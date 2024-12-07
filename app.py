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

# Process and calculate metrics
def calculate_metrics(overview, income_statement):
    try:
        metrics = []
        annual_reports = income_statement["annualReports"]

        # Process each annual report
        for report in annual_reports:
            year = report["fiscalDateEnding"][:4]  # Extract the year
            metrics.append({
                "Year": year,
                "P/E Ratio": overview.get("PERatio", "N/A"),
                "P/B Ratio": overview.get("PriceToBookRatio", "N/A"),
                "Revenue Growth": float(report["totalRevenue"]) if "totalRevenue" in report else "N/A",
                "Net Income": float(report["netIncome"]) if "netIncome" in report else "N/A",
                "Total Revenue": float(report["totalRevenue"]) if "totalRevenue" in report else "N/A",
            })

        # Convert metrics into a DataFrame
        return pd.DataFrame(metrics)
    except Exception as e:
        st.error(f"Error processing metrics: {e}")
        return None

# Main Streamlit App
def main():
    st.title("Enhanced Stock Analysis Tool")
    st.sidebar.header("Options")
    ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, MSFT):")
    
    if ticker:
        st.write(f"Fetching data for {ticker}...")
        overview = fetch_data("OVERVIEW", ticker)
        income_statement = fetch_data("INCOME_STATEMENT", ticker)
        
        if overview and income_statement:
            st.write(f"Calculating metrics for {ticker.upper()}...")
            metrics_df = calculate_metrics(overview, income_statement)
            
            if metrics_df is not None:
                # Dropdown for selecting a timeframe
                timeframes = ["Last 3 Years", "Last 5 Years", "All Time"]
                timeframe = st.sidebar.selectbox("Select Timeframe", timeframes)

                # Filter the DataFrame based on timeframe
                if timeframe == "Last 3 Years":
                    metrics_df = metrics_df.head(3)
                elif timeframe == "Last 5 Years":
                    metrics_df = metrics_df.head(5)
                
                # Display metrics in a table
                st.subheader(f"Metrics for {ticker.upper()} ({timeframe})")
                st.dataframe(metrics_df)
                
                # Add year-over-year comparison
                st.subheader("Year-over-Year Comparison")
                st.write("Below is a comparison of metrics across years:")
                st.line_chart(metrics_df.set_index("Year")[["P/E Ratio", "P/B Ratio", "Revenue Growth"]])
            else:
                st.error("Could not calculate metrics.")
        else:
            st.error("Failed to fetch data from Alpha Vantage.")

if __name__ == "__main__":
    main()
