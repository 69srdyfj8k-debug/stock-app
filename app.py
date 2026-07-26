import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date

st.set_page_config(page_title="智能股票分析與投資決策 Dashboard", layout="wide")

# --- 側邊欄：設定參數 ---
st.sidebar.header("⚙️ 參數設定")
symbol = st.sidebar.text_input("輸入股票代號 (例如: AAPL, 0700.HK, 9988.HK):", value="AAPL")

# 時間週期選擇
time_frame = st.sidebar.selectbox(
    "選擇時間週期 (Timeframe):",
    options=[
        "15 分鐘 (15m)",
        "30 分鐘 (30m)",
        "1 小時 (1h)",
        "1 天 (1d)",
        "1 週 (1wk)",
        "1 個月 (1mo)"
    ]
)

# 映射 yfinance 參數
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

# 1. 自動過濾週末與沒有交易數據的空白 (Cancel 週末空隙)
df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

# --- 2. 頂部「休市 / 假日」提醒 ---
today = date.today()
is_weekend = today.weekday() in [5, 6]  # 5=Saturday, 6=Sunday
last_data_date = df.index[-1].date() if not df.empty else None

if is_weekend:
    st.warning("⚠️ **【今日休市提示】** 今天是週末（非交易日），市場暫停交易。以下顯示為最近一個交易日之收盤數據。")
elif last_data_date and last_data_date < today:
    st.info(f"📅 **【工作天休市/假日提示】** 今日 ({today}) 為工作天休市或尚未開市（例如公眾假期或颱風休市）。最新數據結算至：`{last_data_date}`。")

st.title("📈 智能股票分析與投資決策 Dashboard")

if not df.empty:
    # --- 3. 公司基本面資訊 ---
    company_name = info.get('longName', symbol)
    sector = info.get('sector', 'N/A')
    market_cap = info.get('marketCap', 0)
    pe_ratio = info.get('trailingPE', 'N/A')
    week_52_high = info.get('fiftyTwoWeekHigh', 'N/A')
    week_52_low = info.get('fiftyTwoWeekLow', 'N/A')

    st.subheader(f"🏢 {company_name} ({symbol})")
    cap_str = f"${market_cap / 1e9:.2f}B" if market_cap > 1e9 else f"${market_cap / 1e6:.2f}M" if market_cap > 0 else "N/A"
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.write(f"**板塊 Sector:** {sector}")
    col_b.write(f"**市值 Market Cap:** {cap_str}")
    col_c.write(f"**市盈率 P/E Ratio:** {pe_ratio if isinstance(pe_ratio, str) else f'{pe_ratio:.2f}'}")
    col_d.write(f"**52週範圍:** ${week_52_low} - ${week_52_high}")

    st.divider()

    # --- 4. 技術指標計算 ---
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

    # 數據頂部 Metric 卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新價格", f"${latest_close:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
    col2.metric("20MA (短期支持)", f"${ma20_val:.2f}")
    col3.metric("50MA (中期支持)", f"${ma50_val:.2f}")
    col4.metric("RSI (14)", f"{latest_rsi:.1f}")

    # --- 5. ✨【核心重點】AI 操盤手：綜合入場及買賣決策評估 ---
    st.markdown("### 🤖 AI 操盤手：綜合入場及買賣評估")

    # 判定買賣總體建議分數
    score = 0
    reasons = []

    # 1. 均線趨勢評估
    if latest_close > ma20_val > ma50_val:
        score += 2
        reasons.append("✅ **多頭排列**：股價高於 20MA 及 50MA，處於強勢上升通道。")
    elif latest_close < ma20_val < ma50_val:
        score -= 2
        reasons.append("❌ **空頭排列**：股價低於 20MA 及 50MA，短期處於下降趨勢。")
    else:
        reasons.append("⚠️ **震盪格局**：價格在均線附近交錯，趨勢尚未完全明朗。")

    # 2. RSI 強弱評估
    if latest_rsi > 70:
        score -= 1
        reasons.append("⚠️ **RSI 超買 (>70)**：技術面短期過熱，直接追高風險較大，隨時有拉回修正壓力。")
    elif latest_rsi < 30:
        score += 1
        reasons.append("🎯 **RSI 超賣 (<30)**：市場拋售過度，技術面出現極度超賣，可能隨時迎來反彈。")
    else:
        reasons.append("✅ **RSI 中性 (30-70)**：買賣力量相對平衡，無過熱或過冷現象。")

  # --- 5. ✨【核心重點】AI 操盤手：綜合入場及買賣決策評估 ---
    st.markdown("### 🤖 AI 操盤手：綜合入場及買賣評估")

    # 判定買賣總體建議分數
    score = 0
    reasons = []

    # 1. 均線趨勢評估
    if latest_close > ma20_val > ma50_val:
        score += 2
        reasons.append("✅ **多頭排列**：股價高於 20MA 及 50MA，處於強勢上升通道。")
    elif latest_close < ma20_val < ma50_val:
        score -= 2
        reasons.append("❌ **空頭排列**：股價低於 20MA 及 50MA，短期處於下降趨勢。")
    else:
        reasons.append("⚠️ **震盪格局**：價格在均線附近交錯，趨勢尚未完全明朗。")

    # 2. RSI 強弱評估
    if latest_rsi > 70:
        score -= 1
        reasons.append("⚠️ **RSI 超買 (>70)**：技術面短期過熱，直接追高風險較大，隨時有拉回修正壓力。")
    elif latest_rsi < 30:
        score += 1
        reasons.append("🎯 **RSI 超賣 (<30)**：市場拋售過度，技術面出現極度超賣，可能隨時迎來反彈。")
    else:
        reasons.append("✅ **RSI 中性 (30-70)**：買賣力量相對平衡，無過熱或過冷現象。")

    # 組合原因內容
    reasons_text = "\n".join([f"- {r}" for r in reasons])

    # 最終決策輸出 (改為直接呼叫 Streamlit 提示框，避免 with 語法錯誤)
    if score >= 2:
        st.success(
            f"#### 🟢 **建議：【偏多／考慮分批入場】**\n\n"
            f"**操作策略**：目前技術面偏強，若想建倉，建議採用 **分批買入 (Dollar-cost averaging)** 策略。\n\n"
            f"- **建議進場點**：可等待回踩 20MA (`${ma20_val:.2f}`) 附近確認支持時逢低吸納。\n"
            f"- **建議防守/止損位**：若跌破 50MA (`${ma50_val:.2f}`) 宜果斷止損離場。\n\n"
            f"**📊 判定依據與技術細節：**\n{reasons_text}"
        )
    elif score <= -2:
        st.error(
            f"#### 🔴 **建議：【觀望／暫不建議入場】**\n\n"
            f"**操作策略**：目前技術面偏弱，下行風險較高，不建議盲目抄底。\n\n"
            f"- **持股者建議**：若跌破重要均線支持，宜留意減倉避險。\n"
            f"- **新手觀望者**：建議等待股價重回 20MA (`${ma20_val:.2f}`) 上方並站穩後，再尋找右側交易買點。\n\n"
            f"**📊 判定依據與技術細節：**\n{reasons_text}"
        )
    else:
        st.info(
            f"#### 🟡 **建議：【中性觀望／等待突破】**\n\n"
            f"**操作策略**：目前多空力量均衡，市場正在尋找方向。\n\n"
            f"- **觀望重點**：密切留意是否能放量突破上方阻力，或是否跌破下方 20MA (`${ma20_val:.2f}`) 支持。\n\n"
            f"**📊 判定依據與技術細節：**\n{reasons_text}"
        )

# --- 7. 💬 自由提問 AI 助手 ---
st.divider()
st.subheader("💬 股票 AI 提問助手")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_prompt := st.chat_input("想問關於這隻股票的什麼問題？（例如：如果我想止損要設在哪裡？）："):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    with st.chat_message("assistant"):
        response = (
            f"🤖 **AI 助手分析**：關於 **{symbol}** (`{time_frame}`)：\n\n"
            f"- **最新價格**：${latest_close:.2f}\n"
            f"- **關鍵 20MA 支持位**：${ma20_val:.2f}\n"
            f"- **關鍵 50MA 支持位**：${ma50_val:.2f}\n"
            f"- **當前 RSI**：{latest_rsi:.1f}\n\n"
            f"針對你的問題「**{user_prompt}**」：\n"
            f"建議結合上方 **AI 操盤手** 給出的建議，將 20MA (${ma20_val:.2f}) 或 50MA (${ma50_val:.2f}) 當作觀察依據！"
        )
        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
