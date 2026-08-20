import streamlit as st
import yfinance as yf
from datetime import date
import pandas as pd

st.set_page_config(
    page_title="Stock Analysis System / 股票分析系統",
    page_icon="📈",
    layout="wide"
)

# 📱 強制覆蓋手機 Touch Icon
icon_url = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4c8.png"
st.markdown('''
    <head>
        <link rel="apple-touch-icon" sizes="180x180" href="''' + icon_url + '''">
        <link rel="icon" type="image/png" sizes="32x32" href="''' + icon_url + '''">
    </head> 
    ''', unsafe_allow_html=True)

# ==========================================
# 🌐 語言字典 (Language Dictionary)
# ==========================================
translations = {
    "繁體中文": {
        "p1_title": "💡 估值與持股診斷",
        "p2_title": "📰 實時市場新聞",
        "settings_header": "⚙️ 參數設定",
        "symbol_label": "股票代號:",
        "margin_label": "期望安全邊際 (Margin of Safety %):",
        "margin_caption": "💡 說明：預留嘅折讓幅度，用嚟降低估值出錯嘅買入風險。",
        "timeframe_label": "⏱️ 時間週期",
        "weekend_warn": "⚠️ **【今日休市提示】** 今天是週末（非交易日），市場暫停交易。以下顯示為最近一個交易日之數據。",
        "holiday_info": "📅 **【工作天休市/假日提示】** 今日 ({today}) 為工作天休市或尚未開市。最新數據結算至：`{last_date}`。",
        "guide_title": "💡 **【小白指南】不同時間週期 (Timeframe) 的 AI 建議不一樣，該怎麼看？**",
        "guide_content": """
        * 🎯 **核心原則**：**「大週期 (1d) 定方向，小週期 (15m/30m) 找買點」**。
        * 🧭 **步驟 1（看大方向）**：先切換至 **`1 天 (1d)`**。如果 1d 顯示 **🟢 偏多**，代表中長期大趨勢健康。
        * ⏱️ **步驟 2（找精準入場點）**：再切換至 **`15 分鐘 (15m)`**。若短線拉回至 20MA 支持位，即為最佳逢低建倉時機。
        * ⚠️ **避坑提醒**：若 **`1 天 (1d)`** 顯示 **🔴 觀望/空頭**，即使 15m 出現買入訊號，也多為短線反彈！
        """,
        "overview_title": "📊 {} 股票總覽",
        "sector": "板塊 Sector:",
        "market_cap": "市值 Market Cap:",
        "pe": "市盈率 P/E:",
        "rating": "大行評級:",
        "target": "目標價",
        "latest_price": "最新價格",
        "ma20_support": "20MA (短期支持)",
        "ma50_support": "50MA (中期支持)",
        "rsi_val": "RSI (14)",
        "decision_title": "💡 入手決策與估值分析",
        "fair_val": "估算合理價 (Fair Value):",
        "max_buy": "建議買入價上限 (Max Buy Price):",
        "view_buy_reasons": "🔍 觀看詳細分析理由",
        "sell_diag_title": "📊 持股賣出與止賺止蝕診斷",
        "buy_cost_label": "輸入你的買入成本價 ($):",
        "stop_loss_label": "設定個人止蝕百分比 (Stop Loss %):",
        "pnl_label": "現時帳面盈虧",
        "stop_price_label": "建議止蝕觸發價",
        "target_sell_label": "建議獲利目標價",
        "view_sell_reasons": "🔍 賣出診斷分析理由",
        "news_header": "📰 實時新聞 Grouping 與智能市場結語 (Conclusion)",
        "no_news": "暫無最新新聞數據。",
        "assistant_title": "💬 智能 AI 分析助手",
        "chat_placeholder": "輸入你想了解的關鍵字，例如：支持位、RSI、止損、現價 等。",
        "chat_hint": "你可以試下問：`現價`、`支持位`、`止損` 或 `新聞` ！",
        "data_error": "無法抓取數據，請檢查股票代號是否正確，或嘗試換個時間週期（Timeframe）。",
        "cat_earnings": "💰 業績與財務數據",
        "cat_ratings": "🎯 大行評級與目標價",
        "cat_macro": "⚖️ 宏觀政策與法規",
        "cat_general": "📌 一般市場動態"
    },
    "English": {
        "p1_title": "💡 Valuation & Exit",
        "p2_title": "📰 Live News",
        "settings_header": "⚙️ Settings",
        "symbol_label": "Ticker:",
        "margin_label": "Margin of Safety (%):",
        "margin_caption": "💡 Note: Discount buffer to lower risk from valuation errors.",
        "timeframe_label": "⏱️ Timeframe",
        "weekend_warn": "⚠️ **[Market Closed]** Today is a weekend. Displaying data from the latest trading session.",
        "holiday_info": "📅 **[Market Closed/Holiday]** Market is closed today ({today}). Data updated as of: `{last_date}`.",
        "guide_title": "💡 **[Beginner's Guide] How to interpret different Timeframes?**",
        "guide_content": """
        * 🎯 **Core Principle**: **"Use daily (1d) for macro trend, shorter timeframes (15m/30m) for optimal entry."**
        * 🧭 **Step 1 (Trend)**: Check **`1 Day (1d)`**. If 1d shows **🟢 Bullish**, the trend is healthy.
        * ⏱️ **Step 2 (Entry)**: Switch to **`15 Minutes (15m)`**. If short-term price pulls back to 20MA support, it offers a sweet spot.
        * ⚠️ **Risk Alert**: If **`1 Day (1d)`** is **🔴 Bearish/Neutral**, 15m buy signals are often brief bounces!
        """,
        "overview_title": "📊 {} Stock Overview",
        "sector": "Sector:",
        "market_cap": "Market Cap:",
        "pe": "P/E Ratio:",
        "rating": "Analyst Rating:",
        "target": "Target",
        "latest_price": "Latest Price",
        "ma20_support": "20MA (Short Support)",
        "ma50_support": "50MA (Mid Support)",
        "rsi_val": "RSI (14)",
        "decision_title": "💡 Valuation & Buy Decision",
        "fair_val": "Fair Value:",
        "max_buy": "Max Buy Price:",
        "view_buy_reasons": "🔍 View Detailed Buy Analysis",
        "sell_diag_title": "📊 Exit & Position Diagnosis (Stop Loss / Take Profit)",
        "buy_cost_label": "Enter Your Purchase Price ($):",
        "stop_loss_label": "Stop Loss Threshold (%):",
        "pnl_label": "Unrealized P&L",
        "stop_price_label": "Stop Loss Trigger",
        "target_sell_label": "Target Take-Profit Price",
        "view_sell_reasons": "🔍 View Exit Analysis Reasons",
        "news_header": "📰 Live News Grouping & Sentiment Summary",
        "no_news": "No recent news available.",
        "assistant_title": "💬 Smart AI Assistant",
        "chat_placeholder": "Ask key terms like: Support, RSI, Stop Loss, Current Price...",
        "chat_hint": "Try asking: `Price`, `Support`, `Stop Loss`, or `News`!",
        "data_error": "Failed to fetch data. Please check ticker symbol or try changing timeframe.",
        "cat_earnings": "💰 Earnings & Financials",
        "cat_ratings": "🎯 Analyst Ratings & Targets",
        "cat_macro": "⚖️ Macro & Policy",
        "cat_general": "📌 General Market News"
    }
}

# --- 頂部控制欄 ---
lang = st.radio("🌐 語言 / Language", ["繁體中文", "English"], horizontal=True)
t = translations[lang]

# --- 頂部提示 1：小白指南 ---
with st.expander(t["guide_title"], expanded=False):
    st.markdown(t["guide_content"])

# --- 控制參數元件 ---
col_setting1, col_setting2, col_setting3 = st.columns([2, 3, 3])
with col_setting1:
    symbol = st.text_input(t["symbol_label"], value="AAPL").upper().strip()
with col_setting2:
    required_margin = st.slider(t["margin_label"], 5, 40, 20) / 100
with col_setting3:
    time_frame = st.pills(
        t["timeframe_label"],
        options=["15m", "30m", "1h", "1d", "1wk", "1mo"],
        default="1d"
    )

config_mapping = {
    "15m": {"period": "7d", "interval": "15m"},
    "30m": {"period": "14d", "interval": "30m"},
    "1h":  {"period": "1mo", "interval": "1h"},
    "1d":  {"period": "2y",  "interval": "1d"},
    "1wk": {"period": "5y",  "interval": "1wk"},
    "1mo": {"period": "max", "interval": "1mo"}
}

selected_config = config_mapping.get(time_frame, {"period": "2y", "interval": "1d"})

# --- 安全抓取數據 ---
stock = yf.Ticker(symbol)
info = {}
df = pd.DataFrame()

try:
    info = stock.info or {}
except Exception:
    info = {}

try:
    df = stock.history(period=selected_config["period"], interval=selected_config["interval"])
    if df is not None and not df.empty:
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
except Exception:
    df = pd.DataFrame()

# --- 核心邏輯判斷 ---
if df is None or df.empty or len(df) < 2:
    st.error(t["data_error"])
else:
    # --- 頂部提示 2：休市提示 (抓取數據後於頂部顯示) ---
    df.index = pd.to_datetime(df.index)    
    today = date.today()
    is_weekend = today.weekday() in [5, 6]
    last_data_date = df.index[-1].date()

    if is_weekend:
        st.warning(t["weekend_warn"])
    elif last_data_date < today:
        st.info(t["holiday_info"].format(today=today, last_date=last_data_date))

    # --- 計算技術指標 ---
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    latest_close = float(df['Close'].iloc[-1])
    prev_close = float(df['Close'].iloc[-2])
    price_change = latest_close - prev_close
    pct_change = (price_change / prev_close) * 100
    
    rsi_series = df['RSI'].dropna()
    latest_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0

    ma20_series = df['MA20'].dropna()
    ma20_val = float(ma20_series.iloc[-1]) if not ma20_series.empty else latest_close

    ma50_series = df['MA50'].dropna()
    ma50_val = float(ma50_series.iloc[-1]) if not ma50_series.empty else latest_close

    high_period = float(df['High'].max())
    low_period = float(df['Low'].min())

    # --- 新聞抓取 ---
    grouped_news = {
        t["cat_earnings"]: [],
        t["cat_ratings"]: [],
        t["cat_macro"]: [],
        t["cat_general"]: []
    }
    news_count = 0
    try:
        raw_news = getattr(stock, 'news', []) or []
        for item in raw_news[:6]:
            content = item.get('content', item) if isinstance(item, dict) else item
            title = content.get('title')
            provider = content.get('provider', {}).get('displayName') if isinstance(content.get('provider'), dict) else content.get('publisher', 'Yahoo Finance')
            click_url = content.get('canonicalUrl', {}).get('url') or content.get('clickThroughUrl', {}).get('url') or content.get('link')
            
            if title:
                news_count += 1
                t_lower = title.lower()
                if any(k in t_lower for k in ["earnings", "revenue", "profit", "q1", "q2", "q3", "q4", "delivery", "eps", "sales"]):
                    grouped_news[t要將「**休市提示**」與「**小白指南**」放置在同一個位置（即頂部展開選單上方／下方緊接排列），主要需要調整程式碼的執行順序：

1. **提前定義** `symbol`、`required_margin` 與 `time_frame`，讓 `yfinance` 先順利抓取數據。
2. **提前計算** 交易日與休市狀態，確保能在頁面頂部直接顯示提示。
3. 將「**休市提示**」與「**小白指南**」集中放在頂部控制欄下方。

修改後的完整 Streamlit 程式碼如下：

```python
import streamlit as st
import yfinance as yf
from datetime import date
import pandas as pd

st.set_page_config(
    page_title="Stock Analysis System / 股票分析系統",
    page_icon="📈",
    layout="wide"
)

# 📱 強制覆蓋手機 Touch Icon
icon_url = "[https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4c8.png](https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4c8.png)"
st.markdown('''
    <head>
        <link rel="apple-touch-icon" sizes="180x180" href="''' + icon_url + '''">
        <link rel="icon" type="image/png" sizes="32x32" href="''' + icon_url + '''">
    </head> 
    ''', unsafe_allow_html=True)

# ==========================================
# 🌐 語言字典 (Language Dictionary)
# ==========================================
translations = {
    "繁體中文": {
        "p1_title": "💡 估值與持股診斷",
        "p2_title": "📰 實時市場新聞",
        "settings_header": "⚙️ 參數設定",
        "symbol_label": "股票代號:",
        "margin_label": "期望安全邊際 (Margin of Safety %):",
        "margin_caption": "💡 說明：預留嘅折讓幅度，用嚟降低估值出錯嘅買入風險。",
        "timeframe_label": "⏱️ 時間週期",
        "weekend_warn": "⚠️ **【今日休市提示】** 今天是週末（非交易日），市場暫停交易。以下顯示為最近一個交易日之數據。",
        "holiday_info": "📅 **【工作天休市/假日提示】** 今日 ({today}) 為工作天休市或尚未開市。最新數據結算至：`{last_date}`。",
        "guide_title": "💡 **【小白指南】不同時間週期 (Timeframe) 的 AI 建議不一樣，該怎麼看？**",
        "guide_content": """
        * 🎯 **核心原則**：**「大週期 (1d) 定方向，小週期 (15m/30m) 找買點」**。
        * 🧭 **步驟 1（看大方向）**：先切換至 **`1 天 (1d)`**。如果 1d 顯示 **🟢 偏多**，代表中長期大趨勢健康。
        * ⏱️ **步驟 2（找精準入場點）**：再切換至 **`15 分鐘 (15m)`**。若短線拉回至 20MA 支持位，即為最佳逢低建倉時機。
        * ⚠️ **避坑提醒**：若 **`1 天 (1d)`** 顯示 **🔴 觀望/空頭**，即使 15m 出現買入訊號，也多為短線反彈！
        """,
        "overview_title": "📊 {} 股票總覽",
        "sector": "板塊 Sector:",
        "market_cap": "市值 Market Cap:",
        "pe": "市盈率 P/E:",
        "rating": "大行評級:",
        "target": "目標價",
        "latest_price": "最新價格",
        "ma20_support": "20MA (短期支持)",
        "ma50_support": "50MA (中期支持)",
        "rsi_val": "RSI (14)",
        "decision_title": "💡 入手決策與估值分析",
        "fair_val": "估算合理價 (Fair Value):",
        "max_buy": "建議最大買入價 (Max Buy Price):",
        "view_buy_reasons": "🔍 觀看詳細分析理由",
        "sell_diag_title": "📊 持股賣出與止賺止蝕診斷",
        "buy_cost_label": "輸入你的買入成本價 ($):",
        "stop_loss_label": "設定個人止蝕百分比 (Stop Loss %):",
        "pnl_label": "現時帳面盈虧",
        "stop_price_label": "建議止蝕觸發價",
        "target_sell_label": "建議獲利目標價",
        "view_sell_reasons": "🔍 賣出診斷分析理由",
        "news_header": "📰 實時新聞 Grouping 與智能市場結語 (Conclusion)",
        "no_news": "暫無最新新聞數據。",
        "assistant_title": "💬 智能 AI 分析助手",
        "chat_placeholder": "輸入你想了解的關鍵字，例如：支持位、RSI、止損、現價 等。",
        "chat_hint": "你可以試下問：`現價`、`支持位`、`止損` 或 `新聞` ！",
        "data_error": "無法抓取數據，請檢查股票代號是否正確，或嘗試換個時間週期（Timeframe）。",
        "cat_earnings": "💰 業績與財務數據",
        "cat_ratings": "🎯 大行評級與目標價",
        "cat_macro": "⚖️ 宏觀政策與法規",
        "cat_general": "📌 一般市場動態"
    },
    "English": {
        "p1_title": "💡 Valuation & Exit",
        "p2_title": "📰 Live News",
        "settings_header": "⚙️ Settings",
        "symbol_label": "Ticker:",
        "margin_label": "Margin of Safety (%):",
        "margin_caption": "💡 Note: Discount buffer to lower risk from valuation errors.",
        "timeframe_label": "⏱️ Timeframe",
        "weekend_warn": "⚠️ **[Market Closed]** Today is a weekend. Displaying data from the latest trading session.",
        "holiday_info": "📅 **[Market Closed/Holiday]** Market is closed today ({today}). Data updated as of: `{last_date}`.",
        "guide_title": "💡 **[Beginner's Guide] How to interpret different Timeframes?**",
        "guide_content": """
        * 🎯 **Core Principle**: **"Use daily (1d) for macro trend, shorter timeframes (15m/30m) for optimal entry."**
        * 🧭 **Step 1 (Trend)**: Check **`1 Day (1d)`**. If 1d shows **🟢 Bullish**, the trend is healthy.
        * ⏱️ **Step 2 (Entry)**: Switch to **`15 Minutes (15m)`**. If short-term price pulls back to 20MA support, it offers a sweet spot.
        * ⚠️ **Risk Alert**: If **`1 Day (1d)`** is **🔴 Bearish/Neutral**, 15m buy signals are often brief bounces!
        """,
        "overview_title": "📊 {} Stock Overview",
        "sector": "Sector:",
        "market_cap": "Market Cap:",
        "pe": "P/E Ratio:",
        "rating": "Analyst Rating:",
        "target": "Target",
        "latest_price": "Latest Price",
        "ma20_support": "20MA (Short Support)",
        "ma50_support": "50MA (Mid Support)",
        "rsi_val": "RSI (14)",
        "decision_title": "💡 Valuation & Buy Decision",
        "fair_val": "Fair Value:",
        "max_buy": "Max Buy Price:",
        "view_buy_reasons": "🔍 View Detailed Buy Analysis",
        "sell_diag_title": "📊 Exit & Position Diagnosis (Stop Loss / Take Profit)",
        "buy_cost_label": "Enter Your Purchase Price ($):",
        "stop_loss_label": "Stop Loss Threshold (%):",
        "pnl_label": "Unrealized P&L",
        "stop_price_label": "Stop Loss Trigger",
        "target_sell_label": "Target Take-Profit Price",
        "view_sell_reasons": "🔍 View Exit Analysis Reasons",
        "news_header": "📰 Live News Grouping & Sentiment Summary",
        "no_news": "No recent news available.",
        "assistant_title": "💬 Smart AI Assistant",
        "chat_placeholder": "Ask key terms like: Support, RSI, Stop Loss, Current Price...",
        "chat_hint": "Try asking: `Price`, `Support`, `Stop Loss`, or `News`!",
        "data_error": "Failed to fetch data. Please check ticker symbol or try changing timeframe.",
        "cat_earnings": "💰 Earnings & Financials",
        "cat_ratings": "🎯 Analyst Ratings & Targets",
        "cat_macro": "⚖️ Macro & Policy",
        "cat_general": "📌 General Market News"
    }
}

# --- 1. 頂部語言選擇 ---
lang = st.radio("🌐 語言 / Language", ["繁體中文", "English"], horizontal=True)
t = translations[lang]

# --- 2. 參數輸入設定欄 ---
col_setting1, col_setting2, col_setting3 = st.columns([2, 3, 3])
with col_setting1:
    symbol = st.text_input(t["symbol_label"], value="AAPL").upper().strip()
with col_setting2:
    required_margin = st.slider(t["margin_label"], 5, 40, 20) / 100
with col_setting3:
    time_frame = st.pills(
        t["timeframe_label"],
        options=["15m", "30m", "1h", "1d", "1wk", "1mo"],
        default="1d"
    )

config_mapping = {
    "15m": {"period": "7d", "interval": "15m"},
    "30m": {"period": "14d", "interval": "30m"},
    "1h":  {"period": "1mo", "interval": "1h"},
    "1d":  {"period": "2y",  "interval": "1d"},
    "1wk": {"period": "5y",  "interval": "1wk"},
    "1mo": {"period": "max", "interval": "1mo"}
}

selected_config = config_mapping.get(time_frame, {"period": "2y", "interval": "1d"})

# --- 3. 抓取數據與指標計算 ---
stock = yf.Ticker(symbol)
info = {}
df = pd.DataFrame()

try:
    info = stock.info or {}
except Exception:
    info = {}

try:
    df = stock.history(period=selected_config["period"], interval=selected_config["interval"])
    if df is not None and not df.empty:
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
except Exception:
    df = pd.DataFrame()

# --- 4. 頂部區域：小白指南與休市提示（放在同一位置） ---
with st.expander(t["guide_title"], expanded=False):
    st.markdown(t["guide_content"])

if df is not None and not df.empty and len(df) >= 2:
    df.index = pd.to_datetime(df.index)    
    today = date.today()
    is_weekend = today.weekday() in [5, 6]
    last_data_date = df.index[-1].date()

    if is_weekend:
        st.warning(t["weekend_warn"])
    elif last_data_date < today:
        st.info(t["holiday_info"].format(today=today, last_date=last_data_date))

# --- 5. 核心邏輯與頁面渲染 ---
if df is None or df.empty or len(df) < 2:
    st.error(t["data_error"])
else:
    # 計算技術指標
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    latest_close = float(df['Close'].iloc[-1])
    prev_close = float(df['Close'].iloc[-2])
    price_change = latest_close - prev_close
    pct_change = (price_change / prev_close) * 100
    
    rsi_series = df['RSI'].dropna()
    latest_rsi = float(rsi_series.iloc[-1]) if not rsi_series.empty else 50.0

    ma20_series = df['MA20'].dropna()
    ma20_val = float(ma20_series.iloc[-1]) if not ma20_series.empty else latest_close

    ma50_series = df['MA50'].dropna()
    ma50_val = float(ma50_series.iloc[-1]) if not ma50_series.empty else latest_close

    high_period = float(df['High'].max())
    low_period = float(df['Low'].min())

    # 新聞抓取
    grouped_news = {
        t["cat_earnings"]: [],
        t["cat_ratings"]: [],
        t["cat_macro"]: [],
        t["cat_general"]: []
    }
    news_count = 0
    try:
        raw_news = getattr(stock, 'news', []) or []
        for item in raw_news[:6]:
            content = item.get('content', item) if isinstance(item, dict) else item
            title = content.get('title')
            provider = content.get('provider', {}).get('displayName') if isinstance(content.get('provider'), dict) else content.get('publisher', 'Yahoo Finance')
            click_url = content.get('canonicalUrl', {}).get('url') or content.get('clickThroughUrl', {}).get('url') or content.get('link')
            
            if title:
                news_count += 1
                t_lower = title.lower()
                if any(k in t_lower for k in ["earnings", "revenue", "profit", "q1", "q2", "q3", "q4", "delivery", "eps", "sales"]):
                    grouped_news[t["cat_earnings"]].append({"title": title, "publisher": provider, "url": click_url})
                elif any(k in t_lower for k in ["upgrade", "downgrade", "target", "buy", "sell", "analyst", "outperform", "overweight"]):
                    grouped_news[t["cat_ratings"]].append({"title": title, "publisher": provider, "url": click_url})
                elif any(k in t_lower for k in ["fed", "rate", "inflation", "sec", "lawsuit", "tariff", "court", "ban"]):
                    grouped_news[t["cat_macro"]].append({"title": title, "publisher": provider, "url": click_url})
                else:
                    grouped_news[t["cat_general"]].append({"title": title, "publisher": provider, "url": click_url})
    except Exception:
        pass

    # ==========================================
    # 📊 股票總覽
    # ==========================================
    st.title(t["overview_title"].format(symbol))
    company_name = info.get('longName', symbol)
    sector = info.get('sector', 'N/A')
    market_cap = info.get('marketCap', 0)
    pe_ratio = info.get('trailingPE', 'N/A')
    target_price = info.get('targetMeanPrice', 'N/A')
    recommendation = str(info.get('recommendationKey', 'N/A')).upper()

    st.subheader(f"🏢 {company_name}")
    cap_str = f"${market_cap / 1e9:.2f}B" if isinstance(market_cap, (int, float)) and market_cap > 1e9 else (f"${market_cap / 1e6:.2f}M" if isinstance(market_cap, (int, float)) and market_cap > 0 else "N/A")

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.write(f"**{t['sector']}** {sector}")
    col_b.write(f"**{t['market_cap']}** {cap_str}")
    col_c.write(f"**{t['pe']}** {pe_ratio if isinstance(pe_ratio, str) else f'{pe_ratio:.2f}'}")
    col_d.write(f"**{t['rating']}** {recommendation} ({t['target']}: ${target_price})")

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t["latest_price"], f"${latest_close:.2f}", f"{pct_change:+.2f}%")
    col2.metric(t["ma20_support"], f"${ma20_val:.2f}")
    col3.metric(t["ma50_support"], f"${ma50_val:.2f}")
    col4.metric(t["rsi_val"], f"{latest_rsi:.1f}")

    st.divider()

    # ==========================================
    # 🎯 中間 Tab 選單
    # ==========================================
    tab1, tab2 = st.tabs([t["p1_title"], t["p2_title"]])

    # --- 🥇 Tab 1：💡 估值與持股診斷 ---
    with tab1:
        st.title(f"💡 {symbol} {t['decision_title']}")

        reasons = []
        target_mean_price = info.get('targetMeanPrice')
        eps = info.get('forwardEps') or info.get('trailingEps')
        pe = info.get('forwardPE') or info.get('trailingPE')
        roe = info.get('returnOnEquity')
        fcf = info.get('freeCashflow')

        fair_value = None
        valuation_source = ""

        if target_mean_price and isinstance(target_mean_price, (int, float)) and target_mean_price > 0:
            fair_value = float(target_mean_price)
        elif eps and pe and isinstance(eps, (int, float)) and isinstance(pe, (int, float)) and eps > 0 and pe > 0:
            fair_value = float(eps * pe)
            valuation_source = "預估 EPS × P/E 估值法"
        else:
            fair_value = float((ma20_val + high_period) / 2)
            valuation_source = "技術面綜合基準價 (20MA & 週期高點)"

        max_buy_price = fair_value * (1 - required_margin)
        current_price = round(latest_close, 2)

        if current_price <= max_buy_price:
            price_ok = True
            margin_pct = int(required_margin * 100)
            if lang == "繁體中文":
                reasons.append(f"✅ 現價 (${current_price:.2f}) 低於買入上限價 (${max_buy_price:.2f})，安全邊際達 {margin_pct}%。")
            else:
                reasons.append(f"✅ Price (${current_price:.2f}) is below max buy price (${max_buy_price:.2f}), offering >{margin_pct}% margin of safety.")
        else:
            price_ok = False
            if lang == "繁體中文":
                reasons.append(f"⚠️ 現價 (${current_price:.2f}) 高於買入上限價 (${max_buy_price:.2f})，折讓幅度不足。")
            else:
                reasons.append(f"⚠️ Price (${current_price:.2f}) exceeds max buy price (${max_buy_price:.2f}). Insufficient discount.")

        health_ok = True
        if roe and isinstance(roe, (int, float)):
            roe_display
