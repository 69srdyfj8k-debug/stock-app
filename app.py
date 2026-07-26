import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

st.set_page_config(page_title="智能股票與市場動態 Dashboard", layout="wide")

# --- 側邊欄：分頁與時間週期設定 ---
st.sidebar.header("📌 功能選單")
page = st.sidebar.radio("選擇頁面：", ["📊 總覽、新聞彙整與提問", "📈 技術走勢圖表"])

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

# --- 收集並將新聞 Group 埋一齊 + 自動生成 Conclusion ---
grouped_news = {
    "💰 業績與財務數據": [],
    "🎯 大行評級與目標價": [],
    "⚖️ 宏觀政策與法規": [],
    "📌 一般市場動態": []
}

news_count = 0
try:
    for item in stock.news[:6]:
        content = item.get('content', item) if isinstance(item, dict) else item
        title = content.get('title')
        provider = content.get('provider', {}).get('displayName') if isinstance(content.get('provider'), dict) else content.get('publisher', 'Yahoo Finance')
        click_url = content.get('canonicalUrl', {}).get('url') or content.get('clickThroughUrl', {}).get('url') or content.get('link')
        
        if title:
            news_count += 1
            t_lower = title.lower()
            if any(k in t_lower for k in ["earnings", "revenue", "profit", "q1", "q2", "q3", "q4", "delivery", "eps", "sales"]):
                grouped_news["💰 業績與財務數據"].append({"title": title, "publisher": provider, "url": click_url})
            elif any(k in t_lower for k in ["upgrade", "downgrade", "target", "buy", "sell", "analyst", "outperform", "overweight"]):
                grouped_news["🎯 大行評級與目標價"].append({"title": title, "publisher": provider, "url": click_url})
            elif any(k in t_lower for k in ["fed", "rate", "inflation", "sec", "lawsuit", "tariff", "court", "ban"]):
                grouped_news["⚖️ 宏觀政策與法規"].append({"title": title, "publisher": provider, "url": click_url})
            else:
                grouped_news["📌 一般市場動態"].append({"title": title, "publisher": provider, "url": click_url})
except Exception:
    pass

# ==========================================
# 📄 第一頁：總覽、新聞彙整與提問
# ==========================================
if page == "📊 總覽、新聞彙整與提問":
    st.title(f"📊 {symbol} 股票總覽與智能市場彙整")

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

        if latest_close > ma20_val > ma50_val:
            score += 2
            reasons.append(f"✅ **多頭排列**：現價 (${latest_close:.2f}) 穩居 20MA 及 50MA 上方，短中期趨勢強勢。")
        elif latest_close < ma20_val < ma50_val:
            score -= 2
            reasons.append(f"❌ **空頭排列**：現價 (${latest_close:.2f}) 低於 20MA 及 50MA，短期走勢偏弱。")
        else:
            reasons.append(f"⚠️ **均線糾結**：股價穿梭於均線之間，屬於震盪整理格局。")

        if latest_rsi > 70:
            score -= 1
            reasons.append(f"⚠️ **RSI 超買區 ({latest_rsi:.1f})**：動能過熱，小心短期技術性回吐。")
        elif latest_rsi < 30:
            score += 1
            reasons.append(f"🎯 **RSI 超賣區 ({latest_rsi:.1f})**：拋壓過重，隨時有超跌反彈機會。")
        else:
            reasons.append(f"⚖️ **RSI 中性區 ({latest_rsi:.1f})**：多空交鋒平衡，未見極端情緒。")

        if score >= 2:
            st.success("🟢 **綜合技術評級：強勢看好 (Bullish)**\n\n" + "\n".join([f"- {r}" for r in reasons]))
        elif score <= -2:
            st.error("🔴 **綜合技術評級：弱勢警惕 (Bearish)**\n\n" + "\n".join([f"- {r}" for r in reasons]))
        else:
            st.info("🟡 **綜合技術評級：中性震盪 (Neutral)**\n\n" + "\n".join([f"- {r}" for r in reasons]))

        st.divider()

        # ==========================================
        # 📰 新聞分類彙整 + 自動 Conclusion 結語
        # ==========================================
        st.subheader("📰 實時新聞 Grouping 與智能市場結語 (Conclusion)")

        news_conclusion = "📌 **市場焦點總結**：目前新聞流向以日常動態為主，未見單一極端消息主導市場情緒。"
        if news_count > 0:
            for category, items in grouped_news.items():
                if items:
                    with st.expander(f"{category} ({len(items)} 條)", expanded=True):
                        for item in items:
                            if item["url"]:
                                st.markdown(f"• **[{item['title']}]({item['url']})** — *{item['publisher']}*")
                            else:
                                st.markdown(f"• **{item['title']}** — *{item['publisher']}*")

            st.markdown("")
            
            if len(grouped_news["🎯 大行評級與目標價"]) > 0:
                news_conclusion = f"🎯 **市場焦點總結**：近期市場集中關注該股嘅**大行評級與目標價變動**，機構觀點對股價方向具備較大引導作用。"
            elif len(grouped_news["💰 業績與財務數據"]) > 0:
                news_conclusion = f"💰 **市場焦點總結**：近期新聞主要圍繞**業績與交付數據**，財報表現係短期股價波動嘅核心催化劑。"
            elif len(grouped_news["⚖️ 宏觀政策與法規"]) > 0:
                news_conclusion = f"⚖️ **市場焦點總結**：近期受到**宏觀政策、利率或法律訴訟**等消息影響，投資者需提防系統性風險。"

            st.info(news_conclusion)
        else:
            st.write("暫無最新新聞數據。")

        st.divider()

        # ==========================================
        # 💬 本地智能提問助手（完整保留你原先的小白提示與對話格式）
        # ==========================================
        st.subheader("💬 本地分析摘要")
        st.markdown(f"* **現價**：${latest_close:.2f} ({pct_change:+.2f}%)")
        st.markdown(f"* **趨勢指標**：20MA = {ma20_val:.2f} | 50MA = {ma50_val:.2f}")
        st.markdown(f"* **動能指標**：RSI = {latest_rsi:.1f}  你可以試下問：`現價`、`支持位`、`止損` 或 `新聞` ！")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if user_prompt := st.chat_input("輸入你想了解的關鍵字，例如：支持位、RSI、止損、現價 等。"):
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.write(user_prompt)

            q = user_prompt.lower()
            
            if any(k in q for k in ["入市", "買", "撈底", "睇好", "投資", "上車", "好唔好"]):
                if latest_close > ma20_val:
                    response = f"💡 **入市分析**：現價 **${latest_close:.2f}** 企喺短期 20MA (**${ma20_val:.2f}**) 上方，且 RSI 處於 **{latest_rsi:.1f}**。短線技術面偏向正面，但若追高需注意設好防守位。"
                else:
                    response = f"💡 **入市分析**：現價 **${latest_close:.2f}** 目前低於短期 20MA (**${ma20_val:.2f}**)，走勢偏弱。建議等股價重新企穩均線或 RSI 跌至超賣區時再考慮部署。"
            elif any(k in q for k in ["現價", "幾錢", "價格", "收市"]):
                response = f"📊 **{symbol}** 最新收市價為 **${latest_close:.2f}**（升跌幅：{pct_change:+.2f}%）。"
            elif any(k in q for k in ["支持", "20ma", "ma20"]):
                response = f"🎯 短期支持位參考 20MA（**${ma20_val:.2f}**）；中期 50MA 支援在（**${ma50_val:.2f}**）。"
            elif any(k in q for k in ["止損", "走", "風險", "沽"]):
                response = f"🛡️ 風險防守位可設在中期 50MA（**${ma50_val:.2f}**）或近期低位（**${low_period:.2f}**）。"
            elif any(k in q for k in ["rsi", "指標", "超買", "超賣"]):
                response = f"📉 目前 RSI(14) 數值為 **{latest_rsi:.1f}**（>70 為超買，<30 為超賣）。"
            elif any(k in q for k in ["新聞", "消息", "動態", "結語"]):
                response = f"{news_conclusion}"
            else:
                response = f"🤖 **本地分析摘要**：\n- 現價：${latest_close:.2f} ({pct_change:+.2f}%)\n- 趨勢指標：20MA = {ma20_val:.2f} | 50MA = {ma50_val:.2f}\n- 動能指標：RSI = {latest_rsi:.1f}\n你可以試下問：`現價`、`支持位`、`止損` 或 `新聞` ！"

            with st.chat_message("assistant"):
                st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.error("無法抓取數據。")

# ==========================================
# 📈 第二頁 : 技術走勢圖表
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
