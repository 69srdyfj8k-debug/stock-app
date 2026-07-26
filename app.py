import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date

st.set_page_config(page_title="智能股票分析 Dashboard", layout="wide")

# --- 側邊欄：分頁與時間週期設定 ---
st.sidebar.header("📌 功能選單")
page = st.sidebar.radio("選擇頁面：", ["📊 總覽與 AI 決策", "📈 技術走勢圖表"])

st.sidebar.divider()
st.sidebar.header("⚙️ 參數設定")
symbol = st.sidebar.text_input("輸入股票代號 (例如: AAPL, TSLA, 0700.HK):", value="TSLA")

# 全局時間週期選擇器
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
    index=0  # 預設 15m
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

# --- 頂部提示 1：休市提醒 ---
today = date.today()
is_weekend = today.weekday() in [5, 6]
last_data_date = df.index[-1].date() if not df.empty else None

if is_weekend:
    st.warning("⚠️ **【今日休市提示】** 今天是週末（非交易日），市場暫停交易。以下顯示為最近一個交易日之數據。")
elif last_data_date and last_data_date < today:
    st.info(f"📅 **【工作天休市/假日提示】** 今日 ({today}) 為工作天休市或尚未開市。最新數據結算至：`{last_data_date}`。")

# --- 頂部提示 2：Timeframe 指引 ---
with st.expander("💡 **【小白指南】不同時間週期 (Timeframe) 的 AI 建議不一樣，該怎麼看？**", expanded=False):
    st.markdown("""
    * 🎯 **核心原則**：**「大週期 (1d) 定方向，小週期 (15m/30m) 找買點」**。
    * 🧭 **步驟 1（看大方向）**：先切換至 **`1 天 (1d)`**。如果 1d 顯示 **🟢 偏多**，代表中長期大趨勢健康。
    * ⏱️ **步驟 2（找精準入場點）**：再切換至 **`15 分鐘 (15m)`**。若短線拉回至 20MA 支持位，即為最佳逢低建倉時機。
    * ⚠️ **避坑提醒**：若 **`1 天 (1d)`** 顯示 **🔴 觀望/空頭**，即使 15m 出現買入訊號，也多為短線反彈！
    """)

# ==========================================
# 📄 第一頁：總覽與 AI 決策
# ==========================================
if page == "📊 總覽與 AI 決策":
    st.title(f"📊 {symbol} 股票總覽與 AI 決策")
    st.caption(f"⏱️ 當前分析時間維度：**{time_frame}**")

    if not df.empty:
        # 基本面
        company_name = info.get('longName', symbol)
        sector = info.get('sector', 'N/A')
        market_cap = info.get('marketCap', 0)
        pe_ratio = info.get('trailingPE', 'N/A')
        week_52_high = info.get('fiftyTwoWeekHigh', 'N/A')
        week_52_low = info.get('fiftyTwoWeekLow', 'N/A')

        st.subheader(f"🏢 {company_name}")
        cap_str = f"${market_cap / 1e9:.2f}B" if market_cap > 1e9 else f"${market_cap / 1e6:.2f}M" if market_cap > 0 else "N/A"
        
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.write(f"**板塊 Sector:** {sector}")
        col_b.write(f"**市值 Market Cap:** {cap_str}")
        col_c.write(f"**市盈率 P/E Ratio:** {pe_ratio if isinstance(pe_ratio, str) else f'{pe_ratio:.2f}'}")
        col_d.write(f"**52週範圍:** ${week_52_low} - ${week_52_high}")

        st.divider()

        # 核心 Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("最新價格", f"${latest_close:.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
        col2.metric("20MA (短期支持)", f"${ma20_val:.2f}")
        col3.metric("50MA (中期支持)", f"${ma50_val:.2f}")
        col4.metric("RSI (14)", f"{latest_rsi:.1f}")

        st.divider()

        # AI 操盤手評估
        st.subheader(f"🤖 AI 操盤手：綜合入場及買賣評估 ({time_frame})")

        score = 0
        reasons = []

        if latest_close > ma20_val > ma50_val:
            score += 2
            reasons.append(f"✅ **多頭排列**：在 `{time_frame}` 維度下，股價高於 20MA 及 50MA，處於上升通道。")
        elif latest_close < ma20_val < ma50_val:
            score -= 2
            reasons.append(f"❌ **空頭排列**：在 `{time_frame}` 維度下，股價低於 20MA 及 50MA，短期處於下降趨勢。")
        else:
            reasons.append(f"⚠️ **震盪格局**：在 `{time_frame}` 維度下，價格在均線附近交錯。")

        if latest_rsi > 70:
            score -= 1
            reasons.append("⚠️ **RSI 超買 (>70)**：技術面過熱，追高風險較大。")
        elif latest_rsi < 30:
            score += 1
            reasons.append("🎯 **RSI 超賣 (<30)**：市場拋售過度，可能隨時迎來反彈。")
        else:
            reasons.append("✅ **RSI 中性 (30-70)**：買賣力量相對平衡。")

        reasons_text = "\n".join([f"- {r}" for r in reasons])

        if score >= 2:
            st.success(f"#### 🟢 **建議：【偏多／考慮分批入場】**\n\n**操作策略 (`{time_frame}`)**：可等待回踩 20MA (`${ma20_val:.2f}`) 附近逢低吸納；防守止損位設為 50MA (`${ma50_val:.2f}`)。\n\n**📊 判定依據：**\n{reasons_text}")
        elif score <= -2:
            st.error(f"#### 🔴 **建議：【觀望／暫不建議入場】**\n\n**操作策略 (`{time_frame}`)**：下行風險較高，建議等待重回 20MA (`${ma20_val:.2f}`) 上方站穩後再考慮。\n\n**📊 判定依據：**\n{reasons_text}")
        else:
            st.info(f"#### 🟡 **建議：【中性觀望／等待突破】**\n\n**操作策略 (`{time_frame}`)**：多空力量均衡，留意是否突破上方阻力或跌破 20MA (`${ma20_val:.2f}`) 支持。\n\n**📊 判定依據：**\n{reasons_text}")

        st.divider()

        # 4. 💬 AI 提問對話框（智能邏輯升級）
        st.subheader("💬 股票 AI 提問助手")
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if user_prompt := st.chat_input("想問這隻股票什麼問題？（例如：止損設在哪？最高可以到多少？）："):
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.write(user_prompt)

            with st.chat_message("assistant"):
                prompt_lower = user_prompt.lower()
                
                # 智能動態回答邏輯
                if "最高" in user_prompt or "目標" in user_prompt or "target" in prompt_lower:
                    response = (
                        f"🤖 **AI 分析【目標價與阻力位】**：\n\n"
                        f"- 在當前 `{time_frame}` 維度下，近期最高點阻力位在 **${high_period:.2f}**。\n"
                        f"- 52 週歷史最高價為 **${week_52_high}**。\n"
                        f"💡 **建議**：若股價向上突破 `${high_period:.2f}`，上方空間才會打開；若接近該位置未突破，宜留意獲利了結。"
                    )
                elif "止損" in user_prompt or "最低" in user_prompt or "stop loss" in prompt_lower:
                    response = (
                        f"🤖 **AI 分析【防守與止損位】**：\n\n"
                        f"- **短期關鍵防守 (20MA)**：**${ma20_val:.2f}**\n"
                        f"- **中期最後止損 (50MA)**：**${ma50_val:.2f}**\n"
                        f"- 在當前 `{time_frame}` 區間最低點為 **${low_period:.2f}**。\n"
                        f"💡 **建議**：若收盤價跌破 `${ma50_val:.2f}`，代表趨勢轉弱，建議嚴格執行止損避險。"
                    )
                elif "timeframe" in prompt_lower or "週期" in user_prompt or "時間" in user_prompt:
                    response = (
                        f"🤖 **AI 分析【Timeframe 選擇指引】**：\n\n"
                        f"- 建議**以 `1天 (1d)` 確定總體趨勢**（看是大升市還是跌市）。\n"
                        f"- 再用 **`15分鐘 (15m)` / `30分鐘 (30m)`** 來抓精準的進場買點。\n"
                        f"- 當前你正在查看 **`{time_frame}`** 維度。"
                    )
                else:
                    response = (
                        f"🤖 **AI 綜合解答**（關於 **{symbol}** 在 `{time_frame}`）：\n\n"
                        f"- **最新價格**：${latest_close:.2f}\n"
                        f"- **20MA 支持**：${ma20_val:.2f} | **50MA 支持**：${ma50_val:.2f}\n"
                        f"- **RSI 強弱度**：{latest_rsi:.1f}\n\n"
                        f"針對你的問題「*{user_prompt}*」：\n"
                        f"目前在 `{time_frame}` 維度下，核心觀察點在於股價能否站穩 20MA (`${ma20_val:.2f}`)。若維持在 20MA 之上則走勢仍偏健康。"
                    )
                
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    else:
        st.error("無法抓取數據，請檢查股票代號。")

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
    else:
        st.error("無法抓取該時間週期的圖表數據。")
