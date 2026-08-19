from datetime import date
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Page configuration
st.set_page_config(page_title="Stock Analyzer & Decision Helper", layout="wide")

# ==========================================
# Language Dictionary
# ==========================================
translations = {
    "English": {
        "title": "📈 Stock Analyzer & Decision Helper",
        "search_label": "Enter Stock Ticker (US: AAPL / NVDA, HK: 0005.HK / 9988.HK):",
        "margin_label": "Margin of Safety (%):",
        "current_price": "Current Price",
        "trailing_pe": "Trailing P/E",
        "forward_pe": "Forward P/E",
        "roe": "ROE",
        "tab_buy": "🟢 Buy Decision",
        "tab_sell": "🔴 Exit Diagnosis",
        "tab_chart": "📊 Technicals",
        "decision_header": "💡 Buy Decision & Valuation Analysis",
        "signal_buy": "🟢 Buy Candidate",
        "signal_spec": "🟡 High Risk / Speculative Buy",
        "signal_hold": "🔴 Overvalued / Wait for Dip",
        "fair_val": "Fair Value",
        "max_buy": "Max Buy Price",
        "reason_price_ok": "✅ Current price (${:.2f}) is below the max buy price (${:.2f}), offering a {:.0f}% margin of safety.",
        "reason_price_high": "⚠️ Current price (${:.2f}) is above the max buy price (${:.2f}). Valuation is not sufficiently discounted.",
        "reason_roe_ok": "✅ ROE ({:.1f}%) is strong (> 15%), indicating solid capital return/moat.",
        "reason_roe_weak": "⚠️ ROE ({}) is low; keep an eye on profitability.",
        "reason_fcf_ok": "✅ Free Cash Flow (FCF) is positive; sound financial health.",
        "reason_fcf_weak": "⚠️ Free Cash Flow is weak or negative; higher operational risk.",
        "expander_buy": "🔍 View Detailed Buy Analysis",
        "no_valuation_data": "Insufficient valuation data for automated decision.",
        "sell_header": "📊 Holding & Exit Diagnosis (Stop Loss / Take Profit)",
        "cost_label": "Your Buy Cost ($):",
        "stop_loss_label": "Stop Loss Threshold (%):",
        "pnl_label": "Current P&L",
        "signal_stop": "🔴 SELL / Triggered Stop Loss",
        "signal_target": "🟢 TRIM / Reached Target Price",
        "signal_keep": "🟡 HOLD",
        "target_sell": "Target Sell Price",
        "stop_price": "Stop Loss Price",
        "reason_stop": "❌ Current price (${:.2f}) dropped below stop loss line (${:.2f}, -{:.0f}%). Consider selling to limit risk.",
        "reason_target": "🎉 Current price (${:.2f}) reached target valuation (${:.2f}). Consider taking profits.",
        "reason_keep": "✅ Current price is between stop loss (${:.2f}) and target price (${:.2f}). Fundamentals remain intact; safe to hold.",
        "expander_sell": "🔍 View Exit Analysis Reasons",
        "timeframe_label": "⏱️ Select Timeframe",
        "chart_title": "Candlestick Chart",
        "guide_title": "💡 **Beginner's Guide: How to read different Timeframes?**",
        "guide_content": """
        * 🎯 **Core Principle**: **"Use longer timeframes (1d) for trend direction, shorter timeframes (15m/30m) for entry timing."**
        * 🧭 **Step 1 (Trend)**: Check **`1 Day (1d)`** first. If 1d shows **🟢 Bullish**, the long-term trend is healthy.
        * ⏱️ **Step 2 (Entry)**: Switch to **`15 Minutes (15m)`**. If short-term price pulls back to the 20MA support, it offers an optimal entry point.
        * ⚠️ **Risk Warning**: If **`1 Day (1d)`** shows **🔴 Bearish**, short-term rallies on 15m are often brief bounces!""",
        "weekend_warning": "⚠️ [Market Closed] Today is a weekend. Displaying latest trading day data.",
        "weekend_detail": "💡 **Notice**: The market is currently closed. All stock prices and valuation metrics reflect the latest trading session.",
        "holiday_warning": "📅 [Market Closed] Market is closed or not open today ({today}). Latest data: {last_date}.",
        "holiday_detail": "💡 **Notice**: Market is currently closed for a holiday or pending open. Please check official trading hours.",
        "news_header": "📰 Real-time News Grouping & Market Sentiment Summary",
        "cat_earnings": "💰 Earnings & Financials",
        "cat_ratings": "🎯 Analyst Ratings & Targets",
        "cat_macro": "⚖️ Macro & Policy",
        "cat_general": "📌 General Market News",
        "news_default_summary": "Market Focus Summary: News flow is balanced across general market updates.",
        "news_ratings_summary": "Market Focus Summary: High concentration on institutional analyst ratings and target price revisions.",
        "news_earnings_summary": "Market Focus Summary: Primary focus is on recent earnings performance and delivery metrics.",
        "news_macro_summary": "Market Focus Summary: Affected by macro policies, interest rate outlook, or regulatory news. Beware of systematic risk.",
        "no_news": "No recent news data available.",
        "chat_header": "💬 Local Technical Assistant",
        "chat_placeholder": "Ask key terms like: Support, RSI, Stop Loss, Current Price...",
        "chat_hint": "Ask about: `Price`, `Support`, `Stop Loss`, or `News`!",
        "not_found": "Stock symbol not found. Please check your input."
    },
    "繁體中文": {
        "title": "📈 股票個股分析與買入決策助手",
        "search_label": "輸入股票代號 (美股如 AAPL / NVDA，港股如 0005.HK / 9988.HK):",
        "margin_label": "期望安全邊際 (Margin of Safety %):",
        "current_price": "當前股價",
        "trailing_pe": "Trailing P/E",
        "forward_pe": "Forward P/E",
        "roe": "ROE",
        "tab_buy": "🟢 買入/觀望決策",
        "tab_sell": "🔴 賣出/持股診斷",
        "tab_chart": "📊 技術分析",
        "decision_header": "💡 入手決策與估值分析",
        "signal_buy": "🟢 考慮入手 (Buy Candidate)",
        "signal_spec": "🟡 估值便宜但基本面一般 (High Risk / Speculative Buy)",
        "signal_hold": "🔴 建議觀望 / 暫不入手 (Overvalued / Wait for Dip)",
        "fair_val": "估算合理價 (Fair Value)",
        "max_buy": "建議最大買入價 (Max Buy Price)",
        "reason_price_ok": "✅ 現價 (${:.2f}) 低於安全買入上限價 (${:.2f})，具備 {:.0f}% 以上安全邊際。",
        "reason_price_high": "⚠️ 現價 (${:.2f}) 高於安全買入上限價 (${:.2f})，估值尚未充分折讓。",
        "reason_roe_ok": "✅ ROE ({:.1f}%) 表現優秀 ( > 15%)，具備高資本回報率/護城河。",
        "reason_roe_weak": "⚠️ ROE ({}) 偏低，需注意企業獲利能力。",
        "reason_fcf_ok": "✅ 自由現金流 (FCF) 為正，財務狀況健康。",
        "reason_fcf_weak": "⚠️ 自由現金流偏弱或為負，營運風險較高。",
        "expander_buy": "🔍 觀看詳細分析理由",
        "no_valuation_data": "暫無足夠估值數據進行自動買入判定。",
        "sell_header": "📊 持股賣出與止賺止蝕診斷",
        "cost_label": "輸入你的買入成本價 ($):",
        "stop_loss_label": "設定個人止蝕百分比 (Stop Loss %):",
        "pnl_label": "現時帳面盈虧",
        "signal_stop": "🔴 觸及止蝕點 (SELL / Stop Loss)",
        "signal_target": "🟢 達到目標價 (TRIM / Take Profit)",
        "signal_keep": "🟡 繼續持有 (HOLD)",
        "target_sell": "建議獲利目標價",
        "stop_price": "建議止蝕觸發價",
        "reason_stop": "❌ 現價 (${:.2f}) 已跌穿個人止蝕線 (${:.2f}，-{:.0f}%)，建議嚴格執行止蝕規避風險。",
        "reason_target": "🎉 現價 (${:.2f}) 已達目標估值線 (${:.2f})，建議分批獲利減倉鎖定利潤。",
        "reason_keep": "✅ 現價於止蝕價 (${:.2f}) 與目標價 (${:.2f}) 之間，基本面正常，可繼續 Holding。",
        "expander_sell": "🔍 賣出診斷分析理由",
        "timeframe_label": "⏱️ 選擇時間週期",
        "chart_title": "K 線圖與均線指標",
        "guide_title": "💡 **【小白指南】不同時間週期 (Timeframe) 的 AI 建議不一樣，該怎麼看？**",
        "guide_content": """
        * 🎯 **核心原則**：**「大週期 (1d) 定方向，小週期 (15m/30m) 找買點」**。
        * 🧭 **步驟 1（看大方向）**：先切換至 **`1 天 (1d)`**。如果 1d 顯示 **🟢 偏多**，代表中長期大趨勢健康。
        * ⏱️ **步驟 2（找精準入場點）**：再切換至 **`15 分鐘 (15m)`**。若短線拉回至 20MA 支持位，即為最佳逢低建倉時機。
        * ⚠️ **避坑提醒**：若 **`1 天 (1d)`** 顯示 **🔴 觀望/空頭**，即使 15m 出現買入訊號，也多為短線反彈！""",
        "weekend_warning": "⚠️ 【今日休市提示】 今天是週末（非交易日），市場暫停交易。以下顯示為最近一個交易日之數據。",
        "weekend_detail": "💡 **小白提醒**：目前為非交易時段，當前顯示之股價與估值指標均為最近一個交易日之結算數據。",
        "holiday_warning": "📅 【工作天休市/假日提示】 今日 ({today}) 為工作天休市或尚未開市。最新數據結算至：{last_date}。",
        "holiday_detail": "💡 **小白提醒**：市場現正處於假期休市或數據延遲，請留意最新開盤狀態。",
        "news_header": "📰 實時新聞 Grouping 與智能市場結語 (Conclusion)",
        "cat_earnings": "💰 業績與財務數據",
        "cat_ratings": "🎯 大行評級與目標價",
        "cat_macro": "⚖️ 宏觀政策與法規",
        "cat_general": "📌 一般市場動態",
        "news_default_summary": "市場焦點總結：目前新聞流向以日常動態為主，未見單一極端消息主導市場情緒。",
        "news_ratings_summary": "市場焦點總結：近期市場集中關注該股嘅大行評級與目標價變動，機構觀點對股價方向具備較大引導作用。",
        "news_earnings_summary": "市場焦點總結：近期新聞主要圍繞業績與交付數據，財報表現係短期股價波動嘅核心催化劑。",
        "news_macro_summary": "市場焦點總結：近期受到宏觀政策、利率或法律訴訟等消息影響，投資者需提防系統性風險。",
        "no_news": "暫無最新新聞數據。",
        "chat_header": "💬 本地智能提問助手",
        "chat_placeholder": "輸入你想了解的關鍵字，例如：支持位、RSI、止損、現價 等。",
        "chat_hint": "你可以試下問：`現價`、`支持位`、`止損` 或 `新聞` ！",
        "not_found": "查無此股票代號，請檢查輸入是否正確。"
    }
}

# Language selector in Sidebar
lang = st.sidebar.radio("🌐 Select Language / 選擇語言", ["English", "繁體中文"])
t = translations[lang]

# Manage ticker state cleanly
if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"

# Single unified sidebar quick fetch
sidebar_input = st.sidebar.text_input("Ticker Quick Fetch", value=st.session_state.ticker).upper()
if sidebar_input and sidebar_input != st.session_state.ticker:
    st.session_state.ticker = sidebar_input

ticker_symbol = st.session_state.ticker

# ------------------------------------------
# 1. TOP OF PAGE: Beginner's Guide Expander
# ------------------------------------------

# Safely perform market holiday/weekend check after stock object is ready
#if ticker_symbol:
 #   stock = yf.Ticker(ticker_symbol)
  #  df = stock.history(period="1y")
    
today = date.today()
is_weekend = today.weekday() in [5, 6]
last_data_date = df.index[-1].date() if not df.empty else None

if is_weekend:
    st.warning(t["weekend_warning"])
elif last_data_date and last_data_date < today:
    st.info(t["holiday_warning"])

with st.expander(t["guide_title"], expanded=False):
        st.markdown(t["guide_content"])

st.markdown("---")

# ------------------------------------------
# 2. MAIN HEADER & SEARCH
# ------------------------------------------
st.title(t["title"])

col_search, col_margin = st.columns([2, 1])
with col_search:
    main_input = st.text_input(t["search_label"], value=ticker_symbol).upper()
    if main_input != ticker_symbol:
        st.session_state.ticker = main_input
        st.rerun()

with col_margin:
    required_margin = st.slider(t["margin_label"], 5, 40, 20) / 100

if ticker_symbol:
    stock = yf.Ticker(ticker_symbol)

    try:
        df_check = stock.history(period="5d", interval="1d")
        if not df_check.empty:
            last_data_date = df_check.index[-1].date()
    except Exception:
        pass
    
    info = stock.info
    current_price = info.get('currentPrice') or info.get('regularMarketPrice') or getattr(stock, 'fast_info', {}).get('last_price', None)

    if current_price is not None:
        currency = info.get('currency', 'USD')
        pe_ratio = info.get('trailingPE', None)
        forward_pe = info.get('forwardPE', None)
        roe = info.get('returnOnEquity', 0)
        fcf = info.get('freeCashflow', 0)
        target_mean_price = info.get('targetMeanPrice', None)

        # Key Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t["current_price"], f"{current_price} {currency}")
        m2.metric(t["trailing_pe"], f"{pe_ratio:.2f}" if pe_ratio else "N/A")
        m3.metric(t["forward_pe"], f"{forward_pe:.2f}" if forward_pe else "N/A")
        m4.metric(t["roe"], f"{roe * 100:.2f}%" if roe else "N/A")

        st.markdown("---")

        # ------------------------------------------
        # 3. Decision Tabs
        # ------------------------------------------
        tab_buy, tab_sell, tab_chart = st.tabs([t["tab_buy"], t["tab_sell"], t["tab_chart"]])

        # Tab 1: Buy Decision
        with tab_buy:
            st.subheader(t["decision_header"])
            reasons = []

            if target_mean_price:
                fair_value = target_mean_price
                max_buy_price = fair_value * (1 - required_margin)

                if current_price <= max_buy_price:
                    price_ok = True
                    reasons.append(t["reason_price_ok"].format(current_price, max_buy_price, required_margin * 100))
                else:
                    price_ok = False
                    reasons.append(t["reason_price_high"].format(current_price, max_buy_price))

                health_ok = True
                if roe and roe > 0.15:
                    reasons.append(t["reason_roe_ok"].format(roe * 100))
                else:
                    health_ok = False
                    roe_str = f"{roe*100:.1f}%" if roe else "N/A"
                    reasons.append(t["reason_roe_weak"].format(roe_str))

                if fcf and fcf > 0:
                    reasons.append(t["reason_fcf_ok"])
                else:
                    reasons.append(t["reason_fcf_weak"])

                if price_ok and health_ok:
                    buy_signal = t["signal_buy"]
                    signal_color = "green"
                elif price_ok and not health_ok:
                    buy_signal = t["signal_spec"]
                    signal_color = "gold"
                else:
                    buy_signal = t["signal_hold"]
                    signal_color = "red"

                st.markdown(f"### Signal: :{signal_color}[**{buy_signal}**]")
                st.write(f"**{t['fair_val']}**: ${fair_value:.2f} | **{t['max_buy']}**: ${max_buy_price:.2f}")

                with st.expander(t["expander_buy"], expanded=True):
                    for reason in reasons:
                        st.write(reason)
            else:
                st.info(t["no_valuation_data"])

        # Tab 2: Exit / Sell Diagnosis
        with tab_sell:
            st.subheader(t["sell_header"])

            c1, c2 = st.columns(2)
            with c1:
                buy_cost = st.number_input(t["cost_label"], min_value=0.0, value=float(current_price * 0.9), step=1.0)
            with c2:
                stop_loss_pct = st.slider(t["stop_loss_label"], 5, 30, 10) / 100

            if buy_cost > 0:
                pnl_pct = ((current_price - buy_cost) / buy_cost) * 100
                pnl_color = "green" if pnl_pct >= 0 else "red"
                
                st.markdown(f"**{t['pnl_label']}**：:{pnl_color}[**{pnl_pct:+.2f}%**] (Cost: ${buy_cost:.2f} ➔ Current: ${current_price:.2f})")

                stop_loss_price = buy_cost * (1 - stop_loss_pct)
                target_sell_price = target_mean_price if target_mean_price else buy_cost * 1.2

                st.markdown("---")
                sell_reasons = []

                if current_price <= stop_loss_price:
                    sell_signal = t["signal_stop"]
                    sell_color = "red"
                    sell_reasons.append(t["reason_stop"].format(current_price, stop_loss_price, stop_loss_pct * 100))
                elif current_price >= target_sell_price:
                    sell_signal = t["signal_target"]
                    sell_color = "green"
                    sell_reasons.append(t["reason_target"].format(current_price, target_sell_price))
                else:
                    sell_signal = t["signal_keep"]
                    sell_color = "orange"
                    sell_reasons.append(t["reason_keep"].format(stop_loss_price, target_sell_price))

                st.markdown(f"### Exit Signal: :{sell_color}[**{sell_signal}**]")
                st.write(f"**{t['stop_price']}**: ${stop_loss_price:.2f} | **{t['target_sell']}**: ${target_sell_price:.2f}")

                with st.expander(t["expander_sell"], expanded=True):
                    for sr in sell_reasons:
                        st.write(sr)

        # Tab 3: Technical Chart Only
        with tab_chart:
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

            selected_config = config_mapping.get(time_frame, {"period": "1y", "interval": "1d"})

            df = stock.history(period=selected_config["period"], interval=selected_config["interval"])
            df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

            if not df.empty:
                df.index = pd.to_datetime(df.index)
                df['MA20'] = df['Close'].rolling(window=20).mean()
                df['MA50'] = df['Close'].rolling(window=50).mean()

            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Price"
            )])
            fig.update_layout(title=f"{ticker_symbol} {t['chart_title']} ({time_frame})", xaxis_rangeslider_visible=False, height=450)
            st.plotly_chart(fig, use_container_width=True)

        # ------------------------------------------
        # 4. GLOBAL SECTION (OUTSIDE ALL TABS)
        # ------------------------------------------
        st.markdown("---")

        # News Collection
        grouped_news = {
            t["cat_earnings"]: [],
            t["cat_ratings"]: [],
            t["cat_macro"]: [],
            t["cat_general"]: []
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
                        grouped_news[t["cat_earnings"]].append({"title": title, "publisher": provider, "url": click_url})
                    elif any(k in t_lower for k in ["upgrade", "downgrade", "target", "buy", "sell", "analyst", "outperform", "overweight"]):
                        grouped_news[t["cat_ratings"]].append({"title": title, "publisher": provider, "url": click_url})
                    elif any(k in t_lower for k in ["fed", "rate", "inflation", "sec", "lawsuit", "tariff", "court", "ban"]):
                        grouped_news[t["cat_macro"]].append({"title": title, "publisher": provider, "url": click_url})
                    else:
                        grouped_news[t["cat_general"]].append({"title": title, "publisher": provider, "url": click_url})
        except Exception:
            pass

        # Live News Section Fragment
        @st.fragment(run_every="7200s")
        def render_live_news_section(grouped_news, news_count):
            st.subheader(t["news_header"])

            news_conclusion = t["news_default_summary"]
            if news_count > 0:
                for category, items in grouped_news.items():
                    if items:
                        with st.expander(f"{category} ({len(items)})", expanded=True):
                            for item in items:
                                if item["url"]:
                                    st.markdown(f"• **[{item['title']}]({item['url']})** — *{item['publisher']}*")
                                else:
                                    st.markdown(f"• **{item['title']}** — *{item['publisher']}*")
                
                st.markdown("")
                
                if len(grouped_news[t["cat_ratings"]]) > 0:
                    news_conclusion = t["news_ratings_summary"]
                elif len(grouped_news[t["cat_earnings"]]) > 0:
                    news_conclusion = t["news_earnings_summary"]
                elif len(grouped_news[t["cat_macro"]]) > 0:
                    news_conclusion = t["news_macro_summary"]

                st.info(news_conclusion)
            else:
                st.write(t["no_news"])

            st.divider()
            return news_conclusion

        news_conclusion = render_live_news_section(grouped_news, news_count)

        # Local Interactive Q&A Assistant (Global Section)
        st.subheader(t["chat_header"])
        st.markdown(f"* **{t['current_price']}**: ${current_price:.2f}")
        st.markdown(t["chat_hint"])

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if user_prompt := st.chat_input(t["chat_placeholder"]):
            st.session_state.messages.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.write(user_prompt)

            q = user_prompt.lower()
            
            if any(k in q for k in ["buy", "entry", "bullish", "入市", "買", "撈底", "睇好"]):
                response = f"Entry Check: Current price is **${current_price:.2f}**." if lang == "English" else f"入市分析：現價為 **＄{current_price:.2f}**。"
            elif any(k in q for k in ["price", "current", "現價", "幾錢"]):
                response = f"{ticker_symbol} latest price: **${current_price:.2f}**."
            elif any(k in q for k in ["news", "summary", "新聞", "消息"]):
                response = news_conclusion
            else:
                response = f"Summary: Price=${current_price:.2f}."

            with st.chat_message("assistant"):
                st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    else:
        st.error(t["not_found"])
