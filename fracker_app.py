import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- Predefined Stock Tickers for Industries ---
industry_stocks = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "AMD"],
    "Healthcare": ["JNJ", "PFE", "MRK", "ABT", "GSK"],
    "Financials": ["JPM", "WFC", "GS", "C", "BAC"],
    "Energy": ["XOM", "CVX", "COP", "BP", "TOT"],
    "Consumer Discretionary": ["AMZN", "TSLA", "DIS", "MCD", "NKE"]
}

# --- Title ---
st.title("📊 Stock Tracker with Industry and Technical Analysis")

# --- Selection for Stock or Industry ---
selection_type = st.radio("Select Analysis Type", ("Stock", "Industry"))

# --- Time Range Selection ---
range_option = st.selectbox(
    "Select Time Range",
    ["1 Month", "3 Months", "6 Months", "1 Year", "Custom Range"]
)

# --- Date Calculation ---
today = datetime.today()
if range_option == "1 Month":
    start_date = today - timedelta(days=30)
    end_date = today
elif range_option == "3 Months":
    start_date = today - timedelta(days=90)
    end_date = today
elif range_option == "6 Months":
    start_date = today - timedelta(days=180)
    end_date = today
elif range_option == "1 Year":
    start_date = today - timedelta(days=365)
    end_date = today
else:
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime(today))

# --- Load Stock Data ---
@st.cache_data
def load_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end)
    hist.dropna(inplace=True)
    info = stock.info
    return hist, info

# --- Function to fetch and display stock data ---
def display_stock_data(ticker):
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

    # --- Fetch ROE as a proxy for ROIC ---
    roe = info.get("returnOnEquity", "N/A")
    roe_percent = round(roe * 100, 2) if isinstance(roe, (int, float)) else "N/A"

    # --- WACC is not available in Yahoo Finance, so we keep it as optional user input ---
    wacc_input = st.number_input("Enter estimated WACC (%)", min_value=0.0, max_value=100.0, value=8.0, step=0.1)

    # --- Display ratios ---
    st.markdown("### 📋 Financial Ratios")

    def format_ratio(label, value, highlight=None):
        """Helper to format rows with optional red/green highlight"""
        if highlight == "green":
            return f"✅ **{label}**: <span style='color:green'><b>{value}</b></span>"
        elif highlight == "red":
            return f"⚠️ **{label}**: <span style='color:red'><b>{value}</b></span>"
        else:
            return f"**{label}**: {value}"

    # Display ratios
    st.markdown(format_ratio("P/E Ratio", pe_ratio), unsafe_allow_html=True)
    st.markdown(format_ratio("Earnings Per Share (EPS)", eps), unsafe_allow_html=True)
    st.markdown(format_ratio("PEG Ratio", peg_ratio), unsafe_allow_html=True)
    st.markdown(format_ratio("P/B Ratio", pb_ratio), unsafe_allow_html=True)
    st.markdown(format_ratio("Cash-to-Debt Ratio", cash_to_debt), unsafe_allow_html=True)
    st.markdown(format_ratio("Equity-to-Asset Ratio", equity_to_asset), unsafe_allow_html=True)

    # --- ROE vs WACC Comparison ---
    if isinstance(roe_percent, (int, float)) and isinstance(wacc_input, (int, float)):
        if roe_percent > wacc_input:
            highlight = "green"
            msg = "ROE (proxy for ROIC) is greater than WACC — value creating ✅"
        else:
            highlight = "red"
            msg = "ROE (proxy for ROIC) is less than WACC — potential value destruction ⚠️"
        st.markdown(format_ratio("ROE (Proxy for ROIC) (%)", roe_percent, highlight), unsafe_allow_html=True)
        st.markdown(format_ratio("WACC (%)", wacc_input), unsafe_allow_html=True)
        st.info(msg)
    else:
        st.markdown(format_ratio("ROE (Proxy for ROIC) (%)", roe_percent), unsafe_allow_html=True)
        st.markdown(format_ratio("WACC (%)", wacc_input), unsafe_allow_html=True)

# --- Function to display industry data ---
def display_industry_data(industry_name):
    stocks = industry_stocks.get(industry_name, [])
    
    if not stocks:
        st.error("No stocks found for this industry.")
        return

    # Collect data for each stock in the industry
    industry_data = {
        "P/E Ratio": [],
        "P/B Ratio": [],
        "PEG Ratio": [],
        "EPS": [],
        "ROE (Proxy for ROIC)": []
    }
    
    for ticker in stocks:
        _, info = load_data(ticker, start_date, end_date)

        industry_data["P/E Ratio"].append(info.get("trailingPE", 0))
        industry_data["P/B Ratio"].append(info.get("priceToBook", 0))
        industry_data["PEG Ratio"].append(info.get("pegRatio", 0))
        industry_data["EPS"].append(info.get("trailingEps", 0))
        industry_data["ROE (Proxy for ROIC)"].append(info.get("returnOnEquity", 0))

    # Calculate averages
    avg_pe = sum(industry_data["P/E Ratio"]) / len(industry_data["P/E Ratio"])
    avg_pb = sum(industry_data["P/B Ratio"]) / len(industry_data["P/B Ratio"])
    avg_peg = sum(industry_data["PEG Ratio"]) / len(industry_data["PEG Ratio"])
    avg_eps = sum(industry_data["EPS"]) / len(industry_data["EPS"])
    avg_roe = sum(industry_data["ROE (Proxy for ROIC)"]) / len(industry_data["ROE (Proxy for ROIC)"])

    # Display industry metrics
    st.subheader(f"Industry: {industry_name}")
    st.markdown(f"**Average P/E Ratio**: {avg_pe}")
    st.markdown(f"**Average P/B Ratio**: {avg_pb}")
    st.markdown(f"**Average PEG Ratio**: {avg_peg}")
    st.markdown(f"**Average EPS**: {avg_eps}")
    st.markdown(f"**Average ROE (Proxy for ROIC)**: {avg_roe}%")

# --- Main Logic ---
if selection_type == "Stock":
    # Stock Analysis
    ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, MSFT)", "AAPL").upper()
    if ticker:
        display_stock_data(ticker)
elif selection_type == "Industry":
    # Industry Analysis
    industry = st.selectbox("Select Industry", list(industry_stocks.keys()))
    display_industry_data(industry)

