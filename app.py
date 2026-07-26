import streamlit as st
import yfinance as ticker_data  # 或 import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Analysis Dashboard", layout="wide")
st.title("📈 股票分析與 AI 助手 Dashboard")

# --- 側邊欄：輸入股票代號與時間設定 ---
st.sidebar.header("⚙️ 參數設定")
symbol = st.sidebar.text_input("輸入股票代號 (例如: AAPL, 0700.HK, 9988.HK):", value="AAPL")

# 1. 新增時間週期選擇器
time_frame = st.sidebar.selectbox(
    "選擇時間週期 / 頻率 (Timeframe):",
    options=[
        "15 分鐘 (15m)",
        "30 分鐘 (30m)",
        "1 小時 (1h)",
        "1 天 (1d)",
        "1 週 (1wk)",
        "1 個月 (1mo)"
    ]
)

# 映射選單到 yfinance 參數 (Period 與 Interval)
time_map = {
    "15 分鐘 (15m)": {"period": "1mo", "interval": "15m"},
    "30 分鐘 (30m)": {"period": "1mo", "interval": "30m"},
    "1 小時 (1h)":   {"period": "2mo", "interval": "1h"},
    "1 天 (1d)":     {"period": "1y",  "interval": "1d"},
    "1 週 (1wk)":    {"period": "2y",  "interval": "1wk"},
    "1 個月 (1mo)":  {"period": "5y",  "interval": "1mo"}
}

selected_config = time_map[time_frame]

# --- 抓取股票數據 ---
stock = ticker_data.Ticker(symbol)
df = stock.history(period=selected_config["period"], interval=selected_config["interval"])

if not df.empty:
    st.subheader(f"{symbol} 走勢圖 ({time_frame})")
    
    # 繪製 K 線圖 (Candlestick)
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='K線'
    )])
    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, width='stretch')
else:
    st.error("無法抓取數據，請檢查股票代號或該時間週期是否有交易資料。")

# --- 2. 新增 AI / 問題問答區塊 ---
st.divider()  # 改用呢個畫分隔線！
st.subheader("💬 股票 AI 問答 / 筆記助手")

# 初始化對話歷史 (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 顯示舊對話紀錄
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 輸入框
if user_prompt := st.chat_input("輸入關於這隻股票的問題："):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    with st.chat_message("assistant"):
        response = f"🤖 分析中：關於 **{symbol}** 的問題「{user_prompt}」。"
        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
