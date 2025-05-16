import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt

# --- Title ---
st.title("📈 Stock Tracker with Technical Indicators & Fundamentals")

# --- Ticker Input ---
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA)", "AAPL").upper()
start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.date_input("End Date", pd.to_datetime("today"))

# --- Load Stock Data ---
@st.cache_data
def load_data(ticker, start, end):
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end)
    hist.dropna(inplace=True)
    info = stock.info
    return hist, info

data, info = load_data(ticker, start_date, end_date)

if data.empty:
    st.error("No data found. Please check the ticker symbol.")
    st.stop()

# --- Technical Indicators ---
data['SMA20'] = ta.trend.sma_indicator(data['Close'], window=20)
data['EMA20'] = ta.trend.ema_indicator(data['Close'], window=20)
data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
macd = ta.trend.macd_diff(data['Close'])

# --- Price Chart ---
st.subheader(f"{ticker} Price Chart with SMA & EMA")
fig, ax = plt.subplots()
ax.plot(data['Close'], label='Close', color='black')
ax.plot(data['SMA20'], label='SMA 20', color='blue', linestyle='--')
ax.plot(data['EMA20'], label='EMA 20', color='green', linestyle='--')
ax.set_title(f"{ticker} Stock Price")
ax.legend()
st.pyplot(fig)

# --- RSI & MACD ---
st.subheader("RSI (Relative Strength Index)")
st.line_chart(data['RSI'])

st.subheader("MACD")
st.line_chart(macd)

# --- Fundamental Ratios ---
st.subheader("📊 Fundamental Ratios")

peg_ratio = info.get("pegRatio", "N/A")
pb_ratio = info.get("priceToBook", "N/A")
total_cash = info.get("totalCash", 0)
total_liabilities = info.get("totalLiab", 0)
cash_ratio = round(total_cash / total_liabilities, 2) if total_liabilities else "N/A"

fundamentals = {
    "PEG Ratio": peg_ratio,
    "P/B Ratio": pb_ratio,
    "Cash Ratio": cash_ratio,
}

st.table(pd.DataFrame(fundamentals.items(), columns=["Metric", "Value"]))

# --- Raw Data Option ---
if st.checkbox("Show raw price data"):
    st.write(data.tail())

