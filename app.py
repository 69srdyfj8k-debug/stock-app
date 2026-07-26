import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

st.set_page_config(page_title="智能股票分析 Dashboard", layout="wide")

# --- 側邊欄：分頁與時間週期設定 ---
st.sidebar.header("📌 功能選單")
page = st.sidebar.radio("選擇頁面：", ["📊 總覽、新聞與提問助手", "📈 技術走勢圖表"])

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

# --- 收集新聞標題幫手 ---
news_snippets = []
try:
    for item in stock.news[:5]:
        content = item.get('content', item) if isinstance(item, dict) else item
        title = content.get('title')
        provider = content.get('provider', {}).get('displayName') if isinstance(content.get('provider'), dict) else content.get('publisher', 'Yahoo Finance')
        click_url = content.get('canonicalUrl', {}).get('url') or content.get('clickThroughUrl', {}).get('url') or content.get('link')
        if title:
            news_snippets.append({"title": title, "publisher": provider, "url": click_url})
except Exception:
    pass

# --- 休市提示 ---
today = date.today()
is_weekend = today.weekday() in [5, 6]
last_data_date = df.index[-1].date() if not df.empty else None

if is_weekend:
    st.warning("⚠️ **【今日休市提示】** 今天是週末（非交易日），市場暫停交易。以下顯示為最近一個交易日之數據。")
elif last_data_date and last_data_date < today:
    st.info(f"📅 **【工作天休市/假日提示】** 今日 ({today}) 為工作天休市或尚未開市。最新數據結算至：`{last_data_date}`。")

# ==========================================
# 📄 第一頁：總覽、新聞與提問助手
# ==========================================
if page == "📊 總覽、新聞與提問助手":
    st.title(f"📊 {symbol} 股票總覽與智能助理")

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

        # 量化技術面信號
        st.subheader(f"⚡ 量化技術面信號 ({time_frame})")
        score = 0
        reasons = []

        if latest_close > ma20_val > ma50_val:
            score += 2
            reasons.append(f"✅ **多頭排列**：股價站穩 20MA 及 50MA 上方，趨勢偏多。")
        elif latest_close < ma20_val < ma50_val:
            score -= 2
            reasons.append(f"❌ **空頭排列**：股價低於 20MA 及 50MA，趨勢偏空。")
        else:
            reasons.append(f"⚠️ **震盪格局**：價格於均線附近反覆橫盤。")

        if latest_rsi > 70:
            score -= 1
            reasons.append("⚠️ **RSI 超買 (>70)**：技術面有超買回吐風險。")
        elif latest_rsi < 30:
            score += 1
            reasons.append("🎯 **RSI 超賣 (<30)**：市場拋售過度，可能隨時反彈。")

        if score >= 2:
            st.success("🟢 **技術信號：強勢上行**\n\n" + "\n".join([f"- {r}" for r in reasons]))
        elif score <= -2:
            st.error("🔴 **技術信號：弱勢下行**\n\n" + "\n".join([f"- {r}" for r in reasons]))
        else:
            st.info("🟡 **技術信號：中性觀望**\n\n" + "\n".join([f"- {r}" for r in reasons]))

        st.divider()

        # 實時新聞列表
        st.subheader("📰 最新實時新聞與催化劑")
        if news_snippets:
            for item in news_snippets:
                if item["url"]:
                    st.markdown(f"• **[{item['title']}]({item['url']})** — *{item['publisher']}*")
                else:
                    st.markdown(f"• **{item['title']}** — *{item['publisher']}*")
        else:
            st.write("ūk暫無最新新聞數據。")

        st.divider()

        # ==========================================
        # 💬 本地智能提問助手（免 API 聊天框）
        # ==========================================
        st.subheader("💬 股票數據提問助手 (本地智能答題)")
        st.caption("你可以隨便輸入關鍵字提問，例如：`價格`、`支持位`、`RSI`、`止損`、`最高價` 等。")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if user_prompt := st.chat_input("輸入你想查詢的重點（例如：支持位係幾多？）："):
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.write(user_prompt)

            # 根據用戶關鍵字自動生成精準答案
            query_lower = user_prompt.lower()
            if any(k in query_lower for k in ["價格", "幾錢", "現價", "收市"]):
                response = f"📊 **{symbol}** 目前最新收市價係 **${latest_close:.2f}**（變動：{pct_change:+.2f}%）。"
            elif any(k in query_lower for k in ["支持", "20ma", "ma20", "買入"]):
                response = f"🎯 短期 20MA 支持位大約在 **${ma20_val:.2f}**；中期 50MA 支援在 **${ma50_val:.2f}**。"
            elif any(k in query_lower for k in ["止損", "防守", "走"]):
                response = f"🛡️ 建議防守止損位可參考中期 50MA（**${ma50_val:.2f}**）或近期低位（**${low_period:.2f}**）。"
            elif any(k in query_lower for k in ["rsi", "超買", "超賣"]):
                response = f"📉 當前 RSI (14) 指標數值為 **{latest_rsi:.1f}**（>70 為超買，<30 為超賣）。"
            elif any(k in query_lower for k in ["高", "最高"]):
                response = f"📈 在此週期內，最高價曾見 **${high_period:.2f}**（52週高位：${info.get('fiftyTwoWeekHigh', 'N/A')}）。"
            elif any(k in query_lower for k in ["新聞", "消息"]):
                news_titles = "\n".join([f"• {n['title']}" for n in news_snippets[:3]]) if news_snippets else "暫無新聞"
                response = f"📰 最近期的幾條新聞標題如下：\n{news_titles}"
            else:
                response = f"🤖 我係本地智慧助手。根據當前數據：\n- 現價：${latest_close:.2f}\n- 20MA：${ma20_val:.2f}\n- RSI：{latest_rsi:.1f}\n你可以試下問：`現價`、`支持位`、`RSI`、`止損` 或 `新聞`！"

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
