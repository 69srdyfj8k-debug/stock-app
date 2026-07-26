import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

st.set_page_config(page_title="智能股票與市場動態 Dashboard", layout="wide")

# --- 側邊欄：分頁與時間週期設定 ---
st.sidebar.header("📌 功能選單")
page = st.sidebar.radio("選擇頁面：", ["📊 總覽、自動分析與提問", "📈 技術走勢圖表"])

st.sidebar.divider()
st.sidebar.header("⚙️ 參數設定")
symbol = st.sidebar.text_input("輸入股票代號 (例如: AAPL, TSLA, 0700.HK):", value="TSLA")

time_frame = st.sidebar.selectbox(
    "選擇分析時間週期 (Timeframe):",
    options=[
        "15 分鐘 (15m)",
        "30 分鐘 (30m)",
        "1 小時 (1h)",
        "1 天 (1d)",
        "1 週 (1wk)",
        "1 個月 (1mo)"
    ],
    index=3  # 預設 1d
)

time_map = {
    "15 分鐘 (15m)": {"period": "1mo", "interval": "15m"},
    "30 分鐘 (30m)": {"period": "1mo", "interval": "30m"},
    "1 小時 (1h)":   {"period": "2mo", "interval": "1h"},
    "1 天 (1d)":     {"period": "1y",  "interval": "1d"},
    "1 週 (1wk)":    {"period": "2y",  "interval": "1wk"},
    "1 個月 (1mo)":  {"period": "5y",  "interval": "1mo"}
}

selected_config = time_map[time_frame]

# --- 抓取數據 ---
stock = yf.Ticker(symbol)
info = stock.info
df = stock.history(period=selected_config["period"], interval=selected_config["interval"])
df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

# --- 計算技術指標 ---
if not df.empty:
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    latest_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    price_change = latest_close - prev_close
    pct_change = (price_change / prev_close) * 100
    latest_rsi = df['RSI'].dropna().iloc[-1] if not df['RSI'].dropna().empty else 50
    ma20_val = df['MA20'].dropna().iloc[-1] if not df['MA20'].dropna().empty else latest_close
    ma50_val = df['MA50'].dropna().iloc[-1] if not df['MA50'].dropna().empty else latest_close
    high_period = df['High'].max()
    low_period = df['Low'].min()

# --- 收集並自動分類新聞 ---
news_snippets = []
try:
    for item in stock.news[:5]:
        content = item.get('content', item) if isinstance(item, dict) else item
        title = content.get('title')
        provider = content.get('provider', {}).get('displayName') if isinstance(content.get('provider'), dict) else content.get('publisher', 'Yahoo Finance')
        click_url = content.get('canonicalUrl', {}).get('url') or content.get('clickThroughUrl', {}).get('url') or content.get('link')
        
        if title:
            # 本地關鍵字自動標籤分類
            t_lower = title.lower()
            tag = "📌 一般動態"
            if any(k in t_lower for k in ["earnings", "revenue", "profit", "q1", "q2", "q3", "q4", "delivery", "eps"]):
                tag = "💰 業績與數據"
            elif any(k in t_lower for k in ["upgrade", "downgrade", "target", "buy", "sell", "analyst"]):
                tag = "🎯 大行評級"
            elif any(k in t_lower for k in ["fed", "rate", "inflation", "sec", "lawsuit", "tariff"]):
                tag = "⚖️ 宏觀與政策"
            
            news_snippets.append({"title": title, "publisher": provider, "url": click_url, "tag": tag})
except Exception:
    pass

# ==========================================
# 📄 第一頁：總覽、自動分析與提問
# ==========================================
if page == "📊 總覽、自動分析與提問":
    st.title(f"📊 {symbol} 股票總覽與本地智慧分析")

    if not df.empty:
        company_name = info.get('longName', symbol)
        sector = info.get('sector', 'N/A')
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 'N/A')
        target_price = info.get('targetMeanPrice', 'N/A')
        recommendation = info.get('recommendationKey', 'N/A').upper()

        st.subheader(f"🏢 {company_name}")
        cap_str = f"${market_cap / 1e9:.2f}B" if market_cap > 1e9 else f"${market_cap / 1e6:.2f}M" if market_cap > 0 else "N/A"
        
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.write(f"**板塊 Sector:** {sector}")
        col_b.write(f"**市值 Market Cap:** {cap_str}")
        col_c.write(f"**市盈率 P/E:** {pe_ratio if isinstance(pe_ratio, str) else f'{pe_ratio:.2f}'}")
        col_d.write(f"**大行評級:** {recommendation} (目標價: ${target_price})")

        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新價格", f"${latest_close:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
        col2.metric("20MA (短期支持)", f"${ma20_val:.2f}")
        col3.metric("50MA (中期支持)", f"${ma50_val:.2f}")
        col4.metric("RSI (14)", f"{latest_rsi:.1f}")

        st.divider()

        # ⚡ 豐富的量化技術面信號與深入解析
        st.subheader(f"⚡ 量化技術面信號與深度評析 ({time_frame})")
        score = 0
        reasons = []

        # 均線分析
        if latest_close > ma20_val > ma50_val:
            score += 2
            reasons.append(f"✅ **多頭排列**：現價 (${latest_close:.2f}) 穩居 20MA 及 50MA 上方，短中期趨勢強勢。")
        elif latest_close < ma20_val < ma50_val:
            score -= 2
            reasons.append(f"❌ **空頭排列**：現價 (${latest_close:.2f}) 低於 20MA 及 50MA，短期走勢偏弱。")
        else:
            reasons.append(f"⚠️ **均線糾結**：股價穿梭於均線之間，屬於震盪整理格局。")

        # RSI 分析
        if latest_rsi > 70:
            score -= 1
            reasons.append(f"⚠️ **RSI 超買區 ({latest_rsi:.1f})**：動能過熱，小心短期技術性回吐。")
        elif latest_rsi < 30:
            score += 1
            reasons.append(f"🎯 **RSI 超賣區 ({latest_rsi:.1f})**：拋壓過重，隨時有超跌反彈機會。")
        else:
            reasons.append(f"⚖️ **RSI 中性區 ({latest_rsi:.1f})**：多空交鋒平衡，未見極端情緒。")

        # 綜合評分顯示
        if score >= 2:
            st.success("🟢 **綜合技術評級：強勢看好 (Bullish)**\n\n" + "\n".join([f"- {r}" for r in reasons]))
        elif score <= -2:
            st.error("🔴 **綜合技術評級：弱勢警惕 (Bearish)**\n\n" + "\n".join([f"- {r}" for r in reasons]))
        else:
            st.info("🟡 **綜合技術評級：中性震盪 (Neutral)**\n\n" + "\n".join([f"- {r}" for r in reasons]))

        st.divider()

        # 📰 智能分類的新聞清單
        st.subheader("📰 最新實時新聞與自動分類解讀")
        if news_snippets:
            st.caption("系統已自動提取並為以下新聞進行屬性標籤：")
            for item in news_snippets:
                badge = f"`{item['tag']}`"
                if item["url"]:
                    st.markdown(f"• {badge} **[{item['title']}]({item['url']})** — *{item['publisher']}*")
                else:
                    st.markdown(f"• {badge} **{item['title']}** — *{item['publisher']}*")
        else:
            st.write("暫無最新新聞數據。")

        st.divider()

        # ==========================================
        # 💬 本地智能提問助手
        # ==========================================
        st.subheader("💬 股票數據提問助手")
        st.caption("輸入你想了解的關鍵字，例如：`支持位`、`RSI`、`止損`、`現價` 等。")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if user_prompt := st.chat_input("隨便問：例如「而家適唔適合撈底？」"):
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.write(user_prompt)

            # 本地智能邏輯回應
            q = user_prompt.lower()
            if any(k in q for k in ["現價", "幾錢", "價格", "收市"]):
                response = f"📊 **{symbol}** 最新收市價為 **${latest_close:.2f}**（升跌幅：{pct_change:+.2f}%）。"
            elif any(k in q for k in ["支持", "20ma", "ma20", "撈底", "買"]):
                response = f"🎯 短期支持位參考 20MA（**${ma20_val:.2f}**）。如果 RSI 處於超賣區（目前 {latest_rsi:.1f}），通常是分批佈局的參考點。"
            elif any(k in q for k in ["止損", "走", "風險", "沽"]):
                response = f"🛡️ 風險防守位可設在中期 50MA（**${ma50_val:.2f}**）或近期低位（**${low_period:.2f}**），跌穿要小心擴大跌幅。"
            elif any(k in q for k in ["rsi", "指標", "超買"]):
                response = f"📉 目前 RSI(14) 數值為 **{latest_rsi:.1f}**。大於70代表過熱，小於30代表超賣。"
            elif any(k in q for k in ["新聞", "消息", "動態"]):
                headlines = "\n".join([f"• [{n['tag']}] {n['title']}" for n in news_snippets[:3]]) if news_snippets else "暫無新聞"
                response = f"📰 最近期市場關心的頭條有：\n{headlines}"
            else:
                response = f"🤖 **本地分析摘要**：\n- 現價：${latest_close:.2f} ({pct_change:+.2f}%)\n- 趨勢指標：20MA=${ma20_val:.2f} | 50MA=${ma50_val:.2f}\n- 動能指標：RSI = {latest_rsi:.1f}\n你可以試下問：`現價`、`支持位`、`止損` 或 `新聞`！"

            with st.chat_message("assistant"):
                st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.error("無法抓取數據。")

# ==========================================
# 📈 第二頁：技術走勢圖表
# ==========================================
elif page == "📈 技術走勢圖表":
    st.title(f"📈 {symbol} 技術走勢圖表")
    st.caption(f"⏱️ 當前時間週期：**{time_frame}**")

    if not df.empty:
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.7, 0.3],
            subplot_titles=(f"{symbol} 走勢圖與均線 ({time_frame})", "RSI 指標")
        )

        x_axis = df.index.strftime('%Y-%m-%d %H:%M') if 'm' in selected_config['interval'] or 'h' in selected_config['interval'] else df.index.strftime('%Y-%m-%d')

        fig.add_trace(go.Candlestick(x=x_axis, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
        fig.add_trace(go.Scatter(x=x_axis, y=df['MA20'], mode='lines', name='20MA', line=dict(color='orange', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=x_axis, y=df['MA50'], mode='lines', name='50MA', line=dict(color='blue', width=1.5)), row=1, col=1)

        fig.add_trace(go.Scatter(x=x_axis, y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple', width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        fig.update_xaxes(type='category')
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=650)
        
        st.plotly_chart(fig, width='stretch')
