import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Fetch S&P 500 Tickers from Yahoo Finance ---
@st.cache_data
def get_sp500_tickers():
    """Get the tickers of the S&P 500 companies from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500 = pd.read_html(url)[0]
    tickers = sp500['Symbol'].to_list()
    return tickers

# --- Load Stock Data ---
@st.cache_data
def load_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end)
    hist.dropna(inplace=True)
    info = stock.info
    return hist, info

# --- Calculate Sector Averages ---
def calculate_sector_averages(tickers, start, end, selected_sector):
    sector_data = {
        "P/E Ratio": [],
        "P/B Ratio": [],
        "PEG Ratio": [],
        "EPS": [],
        "ROE (Proxy for ROIC)": []
    }

    # Fetch data for each stock in the sector
    for ticker in tickers:
        _, info = load_data(ticker, start, end)
        
        # Check if the stock's sector matches the selected sector
        sector = info.get("sector", "N/A")
        if sector == selected_sector:
            sector_data["P/E Ratio"].append(info.get("trailingPE", None))
            sector_data["P/B Ratio"].append(info.get("priceToBook", None))
            sector_data["PEG Ratio"].append(info.get("pegRatio", None))
            sector_data["EPS"].append(info.get("trailingEps", None))
            sector_data["ROE (Proxy for ROIC)"].append(info.get("returnOnEquity", None))
    
    # Calculate the average of each ratio
    sector_averages = {key: sum(val) / len(val) if val else "N/A" for key, val in sector_data.items()}
    return sector_averages

# --- Function to fetch and display stock data ---
def display_stock_data(ticker, start_date, end_date):
    data, info = load_data(ticker, start_date, end_date)
    
    if data.empty:
        st.error("No data found for this stock. Please check the ticker symbol or time range.")
        return

    # --- Technical Indicators ---
    data['SMA20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['EMA20'] = ta.trend.ema_indicator(data['Close'], window=20)

    # --- Price Chart ---
    st.subheader(f"{ticker} Price Chart ({start_date.date()} to {end_date.date()})")
    fig, ax = plt.subplots()
    ax.plot(data['Close'], label='Close', color='black')
    ax.plot(data['SMA20'], label='SMA 20', color='blue', linestyle='--')
    ax.plot(data['EMA20'], label='EMA 20', color='green', linestyle='--')
    ax.set_title(f"{ticker} Stock Price")
    ax.legend()
    st.pyplot(fig)

    # --- Display Industry and Sector ---
    st.subheader("🛠 Industry and Sector Information")
    industry = info.get("industry", "N/A")
    sector = info.get("sector", "N/A")
    st.markdown(f"**Sector**: {sector}")
    st.markdown(f"**Industry**: {industry}")

    # --- Financial Ratios ---
    st.subheader("📈 Key Financial Ratios")

    # Extract metrics
    pe_ratio = info.get("trailingPE", "N/A")
    eps = info.get("trailingEps", "N/A")
    peg_ratio = info.get("pegRatio", "N/A")
    pb_ratio = info.get("priceToBook", "N/A")
    total_cash = info.get("totalCash", 0)
    total_debt = info.get("totalDebt", 0)
    total_assets = info.get("totalAssets", 0)
    total_equity = info.get("totalStockholderEquity", 0)

    cash_to_debt = round(total_cash / total_debt, 2) if total_debt else "N/A"
    equity_to_asset = round(total_equity / total_assets, 2) if total_assets else "N/A"

    # --- ROE as a proxy for ROIC ---
    roe = info.get("returnOnEquity", "N/A")
    roe_percent = round(roe * 100, 2) if isinstance(roe, (int, float)) else "N/A"

    # --- WACC (User Input) ---
    wacc_input = st.number_input("Enter estimated WACC (%)", min_value=0.0, max_value=100.0, value=8.0, step=0.1)

    # --- Display ratios ---
    st.markdown(f"**P/E Ratio**: {pe_ratio}")
    st.markdown(f"**EPS (Earnings Per Share)**: {eps}")
    st.markdown(f"**PEG Ratio**: {peg_ratio}")
    st.markdown(f"**P/B Ratio**: {pb_ratio}")
    st.markdown(f"**Cash-to-Debt Ratio**: {cash_to_debt}")
    st.markdown(f"**Equity-to-Asset Ratio**: {equity_to_asset}")

    if isinstance(roe_percent, (int, float)) and isinstance(wacc_input, (int, float)):
        if roe_percent > wacc_input:
            highlight = "green"
            msg = "ROE (proxy for ROIC) is greater than WACC — value creating ✅"
        else:
            highlight = "red"
            msg = "ROE (proxy for ROIC) is less than WACC — potential value destruction ⚠️"
        st.markdown(f"

