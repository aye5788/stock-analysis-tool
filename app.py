import streamlit as st
import requests
import pandas as pd

# Alpha Vantage API Key
API_KEY = "CLP9IN76G4S8OUXN"

# Fetch data from Alpha Vantage
def fetch_data(function, symbol):
    url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

# Calculate derived metrics
def calculate_metrics(overview, income_statement, balance_sheet, cash_flow, daily_data):
    metrics = {}
    try:
        # Valuation Metrics
        metrics["P/E Ratio"] = overview.get("PERatio", "N/A")
        metrics["P/B Ratio"] = overview.get("PriceToBookRatio", "N/A")
        metrics["EV/EBITDA"] = overview.get("EVToEBITDA", "N/A")
        
        # Profitability Metrics
        metrics["ROE"] = overview.get("ReturnOnEquityTTM", "N/A")
        metrics["ROA"] = overview.get("ReturnOnAssetsTTM", "N/A")
        
        # Growth Metrics
        annual_reports = income_statement["annualReports"]
        revenue_growth = (float(annual_reports[0]["totalRevenue"]) - float(annual_reports[1]["totalRevenue"])) / float(annual_reports[1]["totalRevenue"])
        metrics["Revenue Growth"] = round(revenue_growth * 100, 2)
        
        earnings_growth = (float(annual_reports[0]["netIncome"]) - float(annual_reports[1]["netIncome"])) / float(annual_reports[1]["netIncome"])
        metrics["Earnings Growth"] = round(earnings_growth * 100, 2)
        
        # Dividend Growth
        metrics["Dividend Growth"] = overview.get("DividendPerShareTTM", "N/A")
        
        # Quality Metrics
        total_liabilities = float(balance_sheet["totalLiabilities"])
        total_equity = float(balance_sheet["totalShareholderEquity"])
        metrics["Debt-to-Equity"] = round(total_liabilities / total_equity, 2)
        
        # Free Cash Flow Yield
        fcf = float(cash_flow["operatingCashflow"]) - float(cash_flow["capitalExpenditures"])
        market_cap = float(overview["MarketCapitalization"])
        metrics["Free Cash Flow Yield"] = round(fcf / market_cap, 4)
        
        # Asset Turnover
        total_assets = float(balance_sheet["totalAssets"])
        metrics["Asset Turnover"] = round(float(annual_reports[0]["totalRevenue"]) / total_assets, 2)
        
        # Momentum Metrics (Last 5 Days Price Change)
        daily_prices = pd.DataFrame.from_dict(daily_data["Time Series (Daily)"], orient="index").astype(float)
        daily_prices["close"] = daily_prices["4. close"]
        momentum = (daily_prices.iloc[0]["close"] - daily_prices.iloc[4]["close"]) / daily_prices.iloc[4]["close"]
        metrics["5-Day Momentum"] = round(momentum * 100, 2)
        
        return metrics
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return None

# Streamlit App
def main():
    st.title("Stock Analysis Tool")
    ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT):")
    
    if ticker:
        st.write("Fetching data...")
        overview = fetch_data("OVERVIEW", ticker)
        income_statement = fetch_data("INCOME_STATEMENT", ticker)
        balance_sheet = fetch_data("BALANCE_SHEET", ticker)
        cash_flow = fetch_data("CASH_FLOW", ticker)
        daily_data = fetch_data("TIME_SERIES_DAILY", ticker)
        
        if overview and income_statement and balance_sheet and cash_flow and daily_data:
            st.write("Calculating metrics...")
            metrics = calculate_metrics(
                overview, 
                income_statement, 
                balance_sheet["annualReports"][0], 
                cash_flow["annualReports"][0], 
                daily_data
            )
            
            if metrics:
                st.subheader(f"Metrics for {ticker.upper()}")
                for metric, value in metrics.items():
                    st.write(f"{metric}: {value}")
            else:
                st.error("Could not calculate metrics.")
        else:
            st.error("Failed to fetch data from Alpha Vantage.")

if __name__ == "__main__":
    main()
