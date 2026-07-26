import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="股票綜合分析 Dashboard", layout="wide")
st.title("📈 股票綜合分析與 AI 助手 Dashboard")

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
df = stock.history(period=selected_config["period"], interval=selected_config["interval"])

if not df.empty:
    # 計算技術指標：MA20, MA50 與 RSI
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    # 計算 RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # --- 1. 核心數據 Summary 卡片 ---
    latest_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    price_change = latest_close - prev_close
    pct_change = (price_change / prev_close) * 100
    latest_rsi = df['RSI'].dropna().iloc[-1] if not df['RSI'].dropna().empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新價格", f"${latest_close:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
    col2.metric("最高價", f"${df['High'].iloc[-1]:.2f}")
    col3.metric("最低價", f"${df['Low'].iloc[-1]:.2f}")
    col4.metric("RSI (14)", f"{latest_rsi:.1f}")

    st.divider()

    # --- 2. 主圖表：K 線圖 + MA + 成交量 + RSI ---
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.7, 0.3],
        subplot_titles=(f"{symbol} 走勢圖與均線 ({time_frame})", "RSI 指標")
    )

    # K線圖
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='K線'
    ), row=1, col=1)

    # MA 均線
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='MA20', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA50', line=dict(color='blue', width=1)), row=1, col=1)

    # RSI 圖表
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple', width=1.5)), row=2, col=1)
    # RSI 超買/超賣參考線
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=600)
    
    # 這裡採用了最新的 width='stretch' 避開 warning
    st.plotly_chart(fig, width='stretch')

else:
    st.error("無法抓取數據，請檢查股票代號或該時間週期是否有交易資料。")

# --- 3. AI / 問題問答區塊 ---
st.divider()
st.subheader("💬 股票 AI 分析助手")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if user_prompt := st.chat_input("輸入關於這隻股票的問題（例如：這隻股票目前 RSI 偏高嗎？）："):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    with st.chat_message("assistant"):
        # 簡單根據當前數據給予即時數據回應
        rsi_status = "超買 (Overbought)" if latest_rsi > 70 else ("超賣 (Oversold)" if latest_rsi < 30 else "中性")
        response = f"🤖 分析助手報告：關於 **{symbol}** 在 `{time_frame}` 頻率下的現況：\n\n" \
                   f"- **最新價格**：${latest_close:.2f}\n" \
                   f"- **RSI 指標**：{latest_rsi:.1f}（當前狀態：{rsi_status}）\n\n" \
                   f"針對你的問題：「{user_prompt}」，建議配合 20MA 及 50MA 的交叉狀況作綜合判斷。"
        
        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
