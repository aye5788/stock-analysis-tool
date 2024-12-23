import streamlit as st
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import matplotlib.pyplot as plt

# Alpha Vantage API Key
API_KEY = "CLP9IN76G4S8OUXN"

# Helper function to format large numbers
def format_large_numbers(value):
    try:
        if value >= 1e12:
            return f"{value / 1e12:.2f}T"
        elif value >= 1e9:
            return f"{value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"{value / 1e6:.2f}M"
        elif value >= 1e3:
            return f"{value / 1e3:.2f}K"
        return f"{value:.2f}"
    except:
        return value

# Fetch data from Alpha Vantage
def fetch_data(function, symbol, params=None):
    url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={API_KEY}"
    if params:
        url += f"&{params}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

# Process and calculate metrics
def calculate_metrics(overview, income_statement):
    try:
        metrics = []
        annual_reports = income_statement["annualReports"]

        for i in range(len(annual_reports)):
            year = annual_reports[i]["fiscalDateEnding"][:4]
            revenue = float(annual_reports[i].get("totalRevenue", 0))
            net_income = float(annual_reports[i].get("netIncome", 0))

            # Valuation Metrics
            pe_ratio = float(overview.get("PERatio", 0))
            pb_ratio = float(overview.get("PriceToBookRatio", 0))

            # Profitability Metrics
            roe = float(overview.get("ReturnOnEquityTTM", 0))
            roa = float(overview.get("ReturnOnAssetsTTM", 0))

            # Quality Metrics
            free_cash_flow = float(overview.get("FreeCashflowTTM", 0))
            market_cap = float(overview.get("MarketCapitalization", 0))
            fcf_yield = (free_cash_flow / market_cap) * 100 if market_cap > 0 else None
            debt_to_equity = float(overview.get("DebtToEquity", 0))

            # Growth Metrics
            revenue_growth = None
            net_income_growth = None
            if i < len(annual_reports) - 1:  # Ensure there's a previous year for comparison
                prev_revenue = float(annual_reports[i + 1].get("totalRevenue", 0))
                prev_net_income = float(annual_reports[i + 1].get("netIncome", 0))
                revenue_growth = ((revenue - prev_revenue) / prev_revenue) * 100 if prev_revenue > 0 else None
                net_income_growth = ((net_income - prev_net_income) / prev_net_income) * 100 if prev_net_income > 0 else None

            # Add metrics to the list
            metrics.append({
                "Year": year,
                "Total Revenue": revenue,
                "Net Income": net_income,
                "P/E Ratio": pe_ratio,
                "P/B Ratio": pb_ratio,
                "ROE (%)": roe,
                "ROA (%)": roa,
                "Debt-to-Equity": debt_to_equity,
                "Free Cash Flow Yield (%)": fcf_yield,
                "Revenue Growth (%)": revenue_growth,
                "Net Income Growth (%)": net_income_growth,
            })

        return pd.DataFrame(metrics)
    except Exception as e:
        st.error(f"Error processing metrics: {e}")
        return None

# Fetch and process stock price data
def fetch_stock_prices(symbol, timeframe):
    if timeframe in ["1D", "1W"]:
        interval = "60min"
        params = f"interval={interval}&datatype=json"
        time_series = fetch_data("TIME_SERIES_INTRADAY", symbol, params=params)
        if time_series and f"Time Series ({interval})" in time_series:
            return pd.DataFrame.from_dict(time_series[f"Time Series ({interval})"], orient="index").astype(float)
    else:
        params = "outputsize=full&datatype=json"
        time_series = fetch_data("TIME_SERIES_DAILY_ADJUSTED", symbol, params=params)
        if time_series and "Time Series (Daily)" in time_series:
            return pd.DataFrame.from_dict(time_series["Time Series (Daily)"], orient="index").astype(float)
    return None

# Main Streamlit App
def main():
    st.title("Enhanced Stock Analysis Tool")
    st.sidebar.header("Options")

    # Input for stock ticker
    ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, MSFT):")
    timeframe = st.sidebar.selectbox(
        "Select Timeframe for Metrics", 
        ["1D", "1W", "1Y", "YTD", "5Y", "MAX", "Custom"]
    )

    custom_timeframe = None
    if timeframe == "Custom":
        custom_length = st.sidebar.number_input("Enter Length (e.g., 2):", min_value=1, value=1, step=1)
        custom_unit = st.sidebar.selectbox("Select Unit:", ["Years"])
        custom_timeframe = (custom_length, custom_unit)

    if ticker:
        st.write(f"Fetching data for {ticker}...")
        
        # Fetch overview and income statement
        overview = fetch_data("OVERVIEW", ticker)
        income_statement = fetch_data("INCOME_STATEMENT", ticker)
        
        # Fetch stock prices
        stock_prices = fetch_stock_prices(ticker, timeframe)

        if overview and income_statement:
            # Calculate metrics
            metrics_df = calculate_metrics(overview, income_statement)
            
            if metrics_df is not None:
                # Transpose and display metrics
                metrics_df_transposed = metrics_df.set_index("Year").transpose()
                metrics_df_transposed.index.name = "Metric"
                
                metrics_df_transposed = metrics_df_transposed.applymap(format_large_numbers)

                st.subheader(f"Metrics for {ticker.upper()} ({timeframe})")
                gb = GridOptionsBuilder.from_dataframe(metrics_df_transposed)
                gb.configure_default_column(wrapHeaderText=True, autoHeight=True)
                gb.configure_column("Metric", pinned=True)
                grid_options = gb.build()
                AgGrid(metrics_df_transposed, gridOptions=grid_options, height=400, theme="balham")

                # Year-over-Year Comparison
                st.subheader("Year-over-Year Comparison")
                st.line_chart(metrics_df.set_index("Year")[["Total Revenue", "Net Income"]])

        if stock_prices is not None:
            # Plot stock prices
            st.subheader(f"{ticker.upper()} Stock Chart ({timeframe})")
            stock_prices.index = pd.to_datetime(stock_prices.index)
            stock_prices = stock_prices.sort_index()

            plt.figure(figsize=(10, 5))
            plt.plot(stock_prices.index, stock_prices["4. close"], label="Close Price")
            plt.xlabel("Date")
            plt.ylabel("Close Price")
            plt.title(f"{ticker.upper()} Stock Price")
            plt.legend()
            st.pyplot(plt)
        else:
            st.error("Failed to fetch stock price data.")

if __name__ == "__main__":
    main()

