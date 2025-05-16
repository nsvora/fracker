import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from requests.exceptions import RequestException


import requests
from requests.exceptions import RequestException  # Explicitly import the exception class
from bs4 import BeautifulSoup
import pandas as pd

# --- Fetch S&P 500 Tickers from Yahoo Finance ---
def get_sp500_tickers():
    """Get the tickers of the S&P 500 companies from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    
    try:
        # Fetch the page using requests
        response = requests.get(url)
        
        # Check if the response was successful
        response.raise_for_status()  # This will raise an error for bad responses (4xx, 5xx)
        
        # Parse the content of the page with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table containing the S&P 500 tickers
        table = soup.find('table', {'class': 'wikitable'})

        if table:
            # Use pandas to parse the table directly
            sp500 = pd.read_html(str(table))[0]

            # Extract the ticker symbols
            tickers = sp500['Symbol'].to_list()
            return tickers
        else:
            print("Error: Could not find the table on the page.")
            return []

    except RequestException as e:
        # Handle any network-related errors (e.g., connection problems)
        print(f"Error fetching data from URL: {e}")
        return []

    except Exception as e:
        # Catch any other exceptions
        print(f"An unexpected error occurred: {e}")
        return []

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
        st.markdown(f"**ROE (Proxy for ROIC) (%)**: {roe_percent}")
        st.markdown(f"**WACC (%)**: {wacc_input}")
        st.info(msg)
    else:
        st.markdown(f"**ROE (Proxy for ROIC) (%)**: {roe_percent}")
        st.markdown(f"**WACC (%)**: {wacc_input}")

# --- Function to display sector data ---
def display_sector_data(sector_name, start_date, end_date):
    tickers = get_sp500_tickers()  # Fetch S&P 500 tickers
    sector_averages = calculate_sector_averages(tickers, start_date, end_date, sector_name)
    
    # Display sector metrics
    st.subheader(f"📊 {sector_name} Sector Metrics")
    st.markdown(f"**P/E Ratio**: {sector_averages['P/E Ratio']}")
    st.markdown(f"**P/B Ratio**: {sector_averages['P/B Ratio']}")
    st.markdown(f"**PEG Ratio**: {sector_averages['PEG Ratio']}")
    st.markdown(f"**EPS**: {sector_averages['EPS']}")
    st.markdown(f"**ROE (Proxy for ROIC)**: {sector_averages['ROE (Proxy for ROIC)']}")

# --- Main Logic ---
st.title("📊 Stock and Sector Tracker with Financial Analysis")

selection_type = st.radio("Select Analysis Type", ("Stock", "Sector"))

range_option = st.selectbox(
    "Select Time Range",
    ["1 Month", "3 Months", "6 Months", "1 Year", "Custom Range"]
)

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

if selection_type == "Stock":
    ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()
    display_stock_data(ticker, start_date, end_date)

elif selection_type == "Sector":
    sector_name = st.selectbox("Select a Sector", ["Technology", "Healthcare", "Financials", "Energy", "Consumer Discretionary"])
    display_sector_data(sector_name, start_date, end_date)

