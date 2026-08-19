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
        "chart_header": "📊 Historical Price Trend",
        "chart_title": "1-Year Candlestick Chart",
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
        "chart_header": "📊 歷史走勢",
        "chart_title": "近一年 K 線圖",
        "not_found": "查無此股票代號，請檢查輸入是否正確。"
    }
}

# Language selector in Sidebar
lang = st.sidebar.radio("🌐 Select Language / 選擇語言", ["English", "繁體中文"])
t = translations[lang]

# Main UI
st.title(t["title"])

col_search, col_margin = st.columns([2, 1])
with col_search:
    ticker_symbol = st.text_input(t["search_label"], "AAPL").upper()
with col_margin:
    required_margin = st.slider(t["margin_label"], 5, 40, 20) / 100

if ticker_symbol:
    stock = yf.Ticker(ticker_symbol)
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
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(t["current_price"], f"{current_price} {currency}")
        m2.metric(t["trailing_pe"], f"{pe_ratio:.2f}" if pe_ratio else "N/A")
        m3.metric(t["forward_pe"], f"{forward_pe:.2f}" if forward_pe else "N/A")
        m4.metric(t["roe"], f"{roe * 100:.2f}%" if roe else "N/A")

        # Buy Decision Engine
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

        # Sell / Exit Diagnosis
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

        # Historical Chart
        st.markdown("---")
        st.subheader(t["chart_header"])
        hist = stock.history(period="1y")

        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name="Price"
        )])
        fig.update_layout(title=f"{ticker_symbol} {t['chart_title']}", xaxis_rangeslider_visible=False, height=450)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error(t["not_found"])
