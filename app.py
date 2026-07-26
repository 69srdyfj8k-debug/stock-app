import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date

st.set_page_config(page_title="股票綜合分析 Dashboard", layout="wide")

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

# --- 抓取股票數據與基本面資料 ---
stock = yf.Ticker(symbol)
info = stock.info
df = stock.history(period=selected_config["period"], interval=selected_config["interval"])

# 1. 剔除週末及沒有交易數據的空白行 (Cancel 週末/空隙)
df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

# --- 2. 頂部「休市 / 非交易日」提示 ---
today = date.today()
is_weekend = today.weekday() in [5, 6]  # 5=Saturday, 6=Sunday

# 檢查最近數據日期
last_data_date = df.index[-1].date() if not df.empty else None

if is_weekend:
    st.warning("⚠️ **【今日休市提示】** 今天是週末（非交易日），市場暫停交易。以下顯示為最近一個交易日之收盤數據。")
elif last_data_date and last_data_date < today:
    # 如果今天是工作天 (Weekdays)，但最新數據留在今天之前，代表今天是工作天假期休市！
    st.info(f"📅 **【工作天休市/假日提示】** 今日 ({today}) 為工作天休市或尚未開市（例如公眾假期或颱風休市）。最新數據結算至：`{last_data_date}`。")

st.title("📈 股票綜合分析與 AI 助手 Dashboard")

if not df.empty:
    # --- 3. 最早期：基本面資訊與 Key Metrics ---
    company_name = info.get('longName', symbol)
    sector = info.get('sector', 'N/A')
    market_cap = info.get('marketCap', 0)
    pe_ratio = info.get('trailingPE', 'N/A')
    week_52_high = info.get('fiftyTwoWeekHigh', 'N/A')
    week_52_low = info.get('fiftyTwoWeekLow', 'N/A')

    st.subheader(f"🏢 {company_name} ({symbol})")
    
    # 格式化市值 (以 B / M 顯示)
    cap_str = f"${market_cap / 1e9:.2f}B" if market_cap > 1e9 else f"${market_cap / 1e6:.2f}M" if market_cap > 0 else "N/A"
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.write(f"**板塊 Sector:** {sector}")
    col_b.write(f"**市值 Market Cap:** {cap_str}")
    col_c.write(f"**市盈率 P/E Ratio:** {pe_ratio if isinstance(pe_ratio, str) else f'{pe_ratio:.2f}'}")
    col_d.write(f"**52週範圍:** ${week_52_low} - ${week_52_high}")

    st.divider()

    # --- 4. 技術指標計算 (MA20, MA50, RSI) ---
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
    latest_rsi = df['RSI'].dropna().iloc[-1] if not df['RSI'].dropna().empty else 0

    # 數據卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("最新價格", f"${latest_close:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
    col2.metric("最高價", f"${df['High'].iloc[-1]:.2f}")
    col3.metric("最低價", f"${df['Low'].iloc[-1]:.2f}")
    col4.metric("RSI (14)", f"{latest_rsi:.1f}")

    # --- 5. 主圖表：K線圖 + MA + RSI（已自動過濾週末/非交易日） ---
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.7, 0.3],
        subplot_titles=(f"{symbol} 走勢圖與均線 ({time_frame})", "RSI 指標")
    )

    # 轉為字串格式可防止 Plotly 在無交易的時間段留下空白 gaps
    x_axis = df.index.strftime('%Y-%m-%d %H:%M') if 'm' in selected_config['interval'] or 'h' in selected_config['interval'] else df.index.strftime('%Y-%m-%d')

    # K線圖
    fig.add_trace(go.Candlestick(
        x=x_axis, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='K線'
    ), row=1, col=1)

    # 均線
    fig.add_trace(go.Scatter(x=x_axis, y=df['MA20'], mode='lines', name='MA20', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=x_axis, y=df['MA50'], mode='lines', name='MA50', line=dict(color='blue', width=1)), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=x_axis, y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple', width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_xaxes(type='category') # 強制分類座標，徹底藏起無交易的空缺日
    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=600)
    
    st.plotly_chart(fig, width='stretch')

   # --- 6. 原始分析訊號解讀 ---
    st.subheader("💡 綜合技術分析解讀")
    
    ma20_val = df['MA20'].iloc[-1]
    ma50_val = df['MA50'].iloc[-1]

    trend_signal = "🟢 <b>多頭排列 (bullish)</b>：股價高於 20MA 及 50MA，短期走勢偏強。" if latest_close > ma20_val > ma50_val else \
                   ("🔴 <b>空頭排列 (bearish)</b>：股價低於 20MA 及 50MA，短期走勢偏弱。" if latest_close < ma20_val < ma50_val else \
                    "🟡 <b>震盪整理 (consolidation)</b>：均線交錯，建議等待明確突破訊號。")

    rsi_signal = "⚠️ <b>RSI > 70 (超買區)</b>：短期技術面過熱，可能面臨拉回修正壓力。" if latest_rsi > 70 else \
                 ("🎯 <b>RSI < 30 (超賣區)</b>：短期拋售過度，可能出現反彈契機。" if latest_rsi < 30 else \
                  "✅ <b>RSI 處於 30-70 中性區</b>：價格波動處於正常範圍。")

    st.markdown(f"- **均線趨勢**：{trend_signal}", unsafe_allow_html=True)
    st.markdown(f"- **RSI 強弱**：{rsi_signal}", unsafe_allow_html=True)
