import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 頁面基本設定
st.set_page_config(page_title="Stock Analyzer & Decision Helper", layout="wide")

st.title("📈 股票個股分析與買入決策助手")

# 1. 股票搜尋輸入
col_search, col_margin = st.columns([2, 1])
with col_search:
    ticker_symbol = st.text_input("輸入股票代號 (美股如 AAPL / NVDA，港股如 0005.HK / 9988.HK):", "AAPL").upper()
with col_margin:
    required_margin = st.slider("期望安全邊際 (Margin of Safety %):", 5, 40, 20) / 100

if ticker_symbol:
    # 抓取即時數據
    stock = yf.Ticker(ticker_symbol)
    info = stock.info

    if 'regularMarketPrice' in info or 'currentPrice' in info:
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        currency = info.get('currency', 'USD')
        pe_ratio = info.get('trailingPE', None)
        forward_pe = info.get('forwardPE', None)
        roe = info.get('returnOnEquity', 0)
        fcf = info.get('freeCashflow', 0)
        target_mean_price = info.get('targetMeanPrice', None)

        # --- 頂部關鍵指標 ---
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("當前股價", f"{current_price} {currency}")
        m2.metric("Trailing P/E", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
        m3.metric("Forward P/E", f"{forward_pe:.2f}" if forward_pe else "N/A")
        m4.metric("ROE", f"{roe * 100:.2f}%" if roe else "N/A")

        # --- 2. 核心：入手決策 logic (Decision Engine) ---
        st.subheader("💡 入手決策與估值分析")

        buy_signal = "觀望 (Hold / Wait)"
        signal_color = "orange"
        reasons = []

        if target_mean_price:
            fair_value = target_mean_price
            max_buy_price = fair_value * (1 - required_margin)

            # 判定條件 1: 價格折讓
            if current_price <= max_buy_price:
                price_ok = True
                reasons.append(f"✅ 現價 (${current_price:.2f}) 低於安全買入上限價 (${max_buy_price:.2f})，具備 {required_margin*100:.0f}% 以上安全邊際。")
            else:
                price_ok = False
                reasons.append(f"⚠️ 現價 (${current_price:.2f}) 高於安全買入上限價 (${max_buy_price:.2f})，估值尚未充分折讓。")

            # 判定條件 2: 財務健康
            health_ok = True
            if roe and roe > 0.15:
                reasons.append(f"✅ ROE ({roe*100:.1f}%) 表現優秀 ( > 15%)，具備高資本回報率/護城河。")
            else:
                health_ok = False
                reasons.append(f"⚠️ ROE ({roe*100:.1f}% if roe else 'N/A') 偏低，需注意企業獲利能力。")

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
                signal_color = "gold"
            else:
                buy_signal = "🔴 建議觀望 / 暫不入手 (Overvalued / Wait for Dip)"
                signal_color = "red"

            st.markdown(f"### 綜合評估訊號： :{signal_color}[**{buy_signal}**]")
            st.write(f"**估算合理價 (Fair Value)**: ${fair_value:.2f} | **建議最大買入價 (Max Buy Price)**: ${max_buy_price:.2f}")

            with st.expander("🔍 觀看詳細分析理由", expanded=True):
                for reason in reasons:
                    st.write(reason)
        else:
            st.info("暫無足夠估值數據進行自動買入判定。")

        # --- 3. 走勢圖表 ---
        st.markdown("---")
        st.subheader("📊 歷史走勢")
        hist = stock.history(period="1y")

        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name="Price"
        )])
        fig.update_layout(title=f"{ticker_symbol} 近一年 K 線圖", xaxis_rangeslider_visible=False, height=450)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("查無此股票代號，請檢查輸入是否正確。")
