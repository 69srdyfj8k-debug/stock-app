import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date
import pandas as pd

# ⚠️ 必須是程式碼中執行的第一個 Streamlit 指令！
st.set_page_config(
    page_title="股票分析系統",  # 瀏覽器 Tab 的標題
    page_icon="📈",             # 👈 喺度改 Icon！可以用 Emoji、圖片網址或本地檔案
    layout="wide"
)

# 📱 強制覆蓋手機 Touch Icon (iOS Apple Touch Icon & PWA Favicon)
# 裡面嘅 URL 可以換做你想要的 PNG 圖檔網址 (建議 180x180 或以上的正方形圖)
icon_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4c8.png"  # 📈 圖片網址

st.markdown(f'''
    <head>
        <link rel="apple-touch-icon" sizes="180x180" href="{icon_url}">
        <link rel="icon" type="image/png" sizes="32x32" href="{icon_url}">
    </head> 
    ''', unsafe_allow_html=True)
    
# --- 側邊欄：分頁與時間週期設定 ---
st.sidebar.header("📌 功能選單")
page = st.sidebar.radio("選擇頁面：", ["📊 總覽、新聞彙整與提問", "📈 技術走勢圖表"])

st.sidebar.divider()
st.sidebar.header("⚙️ 參數設定")

# 統一使用 symbol 變數，並放入側邊欄
symbol = st.sidebar.text_input("輸入股票代號 (如 AAPL, TSLA, 0700.HK):", value="TSLA").upper()
required_margin = st.sidebar.slider("期望安全邊際 (Margin of Safety %):", 5, 40, 20) / 100
st.sidebar.caption("💡 說明：預留嘅折讓幅度，用嚟降低估值出錯嘅買入風險。")

# 📱 手機友善：用橫向可滑動/點擊嘅 Pills 替代傳統 下拉選單 (Dropdown)
time_frame = st.pills(
    "⏱️ 選擇時間週期",
    options=["15m", "30m", "1h", "1d", "1wk", "1mo"],
    default="1d"
)

# 💡 如果你原本程式有用到 selected_config 字典，可以順便對應返：
config_mapping = {
    "15m": {"period": "7d", "interval": "15m"},
    "30m": {"period": "14d", "interval": "30m"},
    "1h":  {"period": "1mo", "interval": "1h"},
    "1d":  {"period": "2y",  "interval": "1d"},
    "1wk": {"period": "5y",  "interval": "1wk"},
    "1mo": {"period": "max", "interval": "1mo"}  # 👈 改做 max，確保足夠數據計 50MA！
}

selected_config = config_mapping.get(time_frame, {"period": "1y", "interval": "1d"})

# --- 抓取數據 ---
stock = yf.Ticker(symbol)
info = stock.info
df = stock.history(period=selected_config["period"], interval=selected_config["interval"])
df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

# --- 計算指標 ---
df['MA20'] = df['Close'].rolling(20).mean()
df['MA50'] = df['Close'].rolling(50).mean()

# 💡 確保 df 抓到數據後，將 Index 轉為 Datetime 格式
if not df.empty:
    df.index = pd.to_datetime(df.index)

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

# --- 休市提示 ---
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

        # --- 2. 核心：入手決策 logic (Decision Engine) ---
        st.subheader("💡 入手決策與估值分析")
        
        buy_signal = "觀望 (Hold / Wait)"
        signal_color = "orange"
        reasons = []
        
        target_mean_price = info.get('targetMeanPrice', None)
        roe = info.get('returnOnEquity', None)
        fcf = info.get('freeCashflow', None)

        if target_mean_price:
            fair_value = target_mean_price
            max_buy_price = fair_value * (1 - required_margin)
            current_price = round(latest_close,2)
            
            # 判定條件 1: 價格折讓
            if current_price <= max_buy_price:
                price_ok = True
                reasons.append(f"✅ 現價 (＄{current_price}) 低於安全買入上限價 (＄{max_buy_price:.2f})，具備 {required_margin*100:.0f}% 以上安全邊際。")
            else:
                price_ok = False
                reasons.append(f"⚠️ 現價 (＄{current_price}) 高於安全買入上限價 (＄{max_buy_price:.2f})，估值尚未充分折讓。")
    
                
            # 判定條件 2: 財務健康
            health_ok = True
            roe_display = f"{roe * 100:.1f}%" if roe is not None else "N/A"
            
            if roe and roe > 0.15:
                reasons.append(f"✅ ROE ({roe_display}) 表現優秀 ( > 15%)，具備高資本回報率/護城河。")
            else:
                health_ok = False
                reasons.append(f"⚠️ ROE ({roe_display}) 偏低，需注意企業獲利能力。")
                
            if fcf and fcf > 0:
                reasons.append("✅ 自由現金流 (FCF) 為正，財務狀況健康。")
            else:
                reasons.append("⚠️ 自由現金流偏弱或為負，營運風險較高。")
                
            # 綜合訊號判定
            if price_ok and health_ok:
                buy_signal = "🟢 考慮入手 (Buy Candidate)"
                signal_color = "green"
            elif price_ok and not health_ok:
                buy_signal = "🟡 估值便宜但基本面一般 (High Risk / Speculative Buy)"
                signal_color = "orange"
            else:
                buy_signal = "🔴 建議觀望 / 暫不入手 (Overvalued / Wait for Dip)"
                signal_color = "red"
                
            st.markdown(f"### 綜合評估訊號： :{signal_color}[**{buy_signal}**]")
            st.write(f"**估算合理價 (Fair Value):** ＄{fair_value:.2f} | **建議最大買入價 (Max Buy Price):** ＄{max_buy_price:.2f}")
            
            with st.expander("🔍 觀看詳細分析理由", expanded=True):
                for reason in reasons:
                    st.markdown(f"- {reason}")
        else:
            st.info("暫無足夠估值數據進行自動買入判定。")

        # ==========================================
        # 📰 新聞分類彙整 + 自動 Conclusion 結語
        # ==========================================
        # 1. 定義每 2 小時 (7200秒) 自動刷新的 Fragment
        @st.fragment(run_every="7200s")
        def render_live_news_section(grouped_news, news_count):
            st.subheader("📰 實時新聞 Grouping 與智能市場結語 (Conclusion)")

            news_conclusion = "市場焦點總結：目前新聞流向以日常動態為主，未見單一極端消息主導市場情緒。"
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
                    news_conclusion = f"市場焦點總結：近期市場集中關注該股嘅大行評級與目標價變動，機構觀點對股價方向具備較大引導作用。"
                elif len(grouped_news["💰 業績與財務數據"]) > 0:
                    news_conclusion = f"市場焦點總結：近期新聞主要圍繞業績與交付數據，財報表現係短期股價波動嘅核心催化劑。"
                elif len(grouped_news["⚖️ 宏觀政策與法規"]) > 0:
                    news_conclusion = f"市場焦點總結：近期受到宏觀政策、利率或法律訴訟等消息影響，投資者需提防系統性風險。"
    
                st.info(news_conclusion)
            else:
                st.write("暫無最新新聞數據。")
    
            st.divider()
        
        # 2. 在原位置呼叫這個 Function（記得傳入你的 grouped_news 同 news_count 變數）
        render_live_news_section(grouped_news, news_count)
        
        # ==========================================
        # 💬 本地智能提問助手（原汁原味小白提示）
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
                    response = f"入市分析：現價 **＄{latest_close:.2f}** 企喺短期 20MA (**＄{ma20_val:.2f}**) 上方，且 RSI 處於 **{latest_rsi:.1f}**。短線技術面偏向正面，但若追高需注意設好防守位。"
                else:
                    response = f"入市分析：現價 **＄{latest_close:.2f}** 目前低於短期 20MA (**＄{ma20_val:.2f}**)，走勢偏弱。建議等股價重新企穩均線或 RSI 跌至超賣區時再考慮部署。"
            elif any(k in q for k in ["現價", "幾錢", "價格", "收市"]):
                response = f"{symbol} 最新收市價為 **＄{latest_close:.2f}**（升跌幅：{pct_change:+.2f}%）。"
            elif any(k in q for k in ["支持", "20ma", "ma20"]):
                response = f"短期支持位參考 20MA（**＄{ma20_val:.2f}**）；中期 50MA 支援在（**＄{ma50_val:.2f}**）。"
            elif any(k in q for k in ["止損", "走", "風險", "沽"]):
                response = f"風險防守位可設在中期 50MA（**＄{ma50_val:.2f}**）或近期低位（**＄{low_period:.2f}**）。"
            elif any(k in q for k in ["rsi", "指標", "超買", "超賣"]):
                response = f"目前 RSI(14) 數值為 **{latest_rsi:.1f}**（>70 為超買，<30 為超賣）。"
            elif any(k in q for k in ["新聞", "消息", "動態", "結語"]):
                response = f"{news_conclusion}"
            else:
                response = f"本地分析摘要：\n- 現價：＄{latest_close:.2f} ({pct_change:+.2f}%)\n- 趨勢指標：20MA = {ma20_val:.2f} | 50MA = {ma50_val:.2f}\n- 動能指標：RSI = {latest_rsi:.1f}  你可以試下問：`現價`、`支持位`、`止損` 或 `新聞` ！"

            with st.chat_message("assistant"):
                st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.error("無法抓取數據。")

# ==========================================
    # 🆕 新增：賣出/持股診斷 (Hold / Sell Checker)
    # ==========================================
    st.subheader("📊 持股賣出與止賺止蝕診斷")

    c1, c2 = st.columns(2)
    with c1:
        buy_cost = st.number_input("輸入你的買入成本價 ($):", min_value=0.0, value=float(current_price * 0.9), step=1.0)
    with c2:
        stop_loss_pct = st.slider("設定個人止蝕百分比 (Stop Loss %):", 5, 30, 10) / 100

    if buy_cost > 0:
        # 計算當前盈虧
        pnl_pct = ((current_price - buy_cost) / buy_cost) * 100
        pnl_color = "green" if pnl_pct >= 0 else "red"
        
        st.markdown(f"**現時帳面盈虧**：:{pnl_color}[**{pnl_pct:+.2f}%**] (成本: ${buy_cost:.2f} ➔ 現價: ${current_price:.2f})")

        # 賣出邏輯判定
        stop_loss_price = buy_cost * (1 - stop_loss_pct)
        target_sell_price = target_mean_price if target_mean_price else buy_cost * 1.2

        st.markdown("---")
        sell_reasons = []

        # 1. 觸及止蝕
        if current_price <= stop_loss_price:
            sell_signal = "🔴 觸及止蝕點 (SELL / Stop Loss)"
            sell_color = "red"
            sell_reasons.append(f"❌ 現價 (${current_price:.2f}) 已跌穿個人止蝕線 (${stop_loss_price:.2f}，-{stop_loss_pct*100:.0f}%)，建議嚴格執行止蝕規避風險。")
        
        # 2. 達到目標獲利價
        elif current_price >= target_sell_price:
            sell_signal = "🟢 達到目標價 (TRIM / Take Profit)"
            sell_color = "green"
            sell_reasons.append(f"🎉 現價 (${current_price:.2f}) 已達目標估值線 (${target_sell_price:.2f})，建議分批獲利減倉鎖定利潤。")

        # 3. 繼續持有
        else:
            sell_signal = "🟡 繼續持有 (HOLD)"
            sell_color = "orange"
            sell_reasons.append(f"✅ 現價於止蝕價 (${stop_loss_price:.2f}) 與目標價 (${target_sell_price:.2f}) 之間，基本面正常，可繼續 Holding。")

        # 顯示診斷結果
        st.markdown(f"### 賣出診斷建議： :{sell_color}[**{sell_signal}**]")
        st.write(f"**建議止蝕觸發價**: ${stop_loss_price:.2f} | **建議獲利目標價**: ${target_sell_price:.2f}")

        with st.expander("🔍 賣出診斷分析理由", expanded=True):
            for sr in sell_reasons:
                st.write(sr)
                    
# ==========================================
# 📈 第二頁 : 技術走勢圖表 (優化操作版)
# ==========================================
elif page == "📈 技術走勢圖表":
    st.title(f"📈 {symbol} 技術走勢圖表")
    st.caption(f"⏱️ 當前時間週期：**{time_frame}** | 💡 提示：你可以用滑鼠在圖表中拉選框進行放大，雙擊圖表重置檢視。")

    if not df.empty:
        # 創建 2 個上下子圖 (上方：K線與均線 / 下方：RSI)
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.04, 
            row_heights=[0.75, 0.25],
            subplot_titles=(f"{symbol} 走勢圖與移動平均線", "RSI (14) 相對強弱指標")
        )

        # 1. 主圖：K 線圖
        fig.add_trace(
            go.Candlestick(
                x=df.index, 
                open=df['Open'], 
                high=df['High'], 
                low=df['Low'], 
                close=df['Close'], 
                name='K線'
            ), 
            row=1, col=1
        )
        
        # 2. 主圖：20MA & 50MA 均線
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='20MA', line=dict(color='orange', width=1.5)), 
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='50MA', line=dict(color='#2962FF', width=1.5)), 
            row=1, col=1
        )

        # 3. 副圖：RSI
        fig.add_trace(
            go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='#9C27B0', width=1.5)), 
            row=2, col=1
        )
        # RSI 30/70 參考線
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.7, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.7, row=2, col=1)

        # --- ⚙️ 圖表佈局與互動優化 ---
        
        # 💡 只有 15m, 30m, 1h, 1d 才啟用 rangebreaks，1mo / 1wk 唔啟用！
        rangebreaks_config = []
        
        if selected_config['interval'] in ['15m', '30m', '1h', '1d']:
            rangebreaks_config.append(dict(bounds=["sat", "mon"])) # 跳過週末
            if 'm' in selected_config['interval'] or 'h' in selected_config['interval']:
                rangebreaks_config.append(dict(bounds=[16, 9.5], pattern="hour")) # 跳過非交易時段
        
        fig.update_xaxes(
            type='date',
            rangebreaks=rangebreaks_config,  # 👈 帶入條件判斷後嘅 config
            gridcolor='rgba(255, 255, 255, 0.1)',
            row=2, col=1
        )
        
        # 上下兩個子圖（K線圖同 RSI）各自自動對齊高度
        fig.update_yaxes(
            gridcolor='rgba(255, 255, 255, 0.1)',
            autorange=True,        # 自動貼合數據高度
            fixedrange=False,       # 允許 Plotly 計算範圍
            row=1, col=1
        )
        
        fig.update_yaxes(
            gridcolor='rgba(255, 255, 255, 0.1)',
            range=[0, 100],        # RSI 固定喺 0-100 之間，避免爆框
            fixedrange=True,       # RSI 副圖鎖定高度
            row=2, col=1
        )

        # 全局風格：設定十字準星 (Crosshair) & 隱藏下方的 RangeSlider (讓版面更大更順手)
        fig.update_layout(
            height=680,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified",  # 將游標訊息統一合併顯示，操作感受大增
            xaxis_rangeslider_visible=False,
            dragmode='pan',  # 👈 停用滑鼠拉框 Zoom 功能
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # 順手渲染圖表 (👈 之前漏咗呢段渲染程式碼)
        st.plotly_chart(
            fig, 
            use_container_width=True,
            config={
                'scrollZoom': False,
                'displayModeBar': True, # 保留工具列
                'modeBarButtonsToRemove': [
                    'zoom2d',     # 👈 移除拉框 Zoom 按鈕
                    'select2d',   # 👈 移除選擇工具
                    'lasso2d'     # 👈 移除套索工具
                ],
                'displaylogo': False  # 隱藏 Plotly logo
            }
        )
        
    else:
        st.error("暫無走勢圖數據。")
