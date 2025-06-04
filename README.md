# Stock Analysis AI Chatbot

An interactive Streamlit application that provides AI-powered stock market analysis using real-time data.

## Features

- Real-time stock data visualisation with candlestick charts
- AI-powered analysis of stock performance
- Interactive chat interface for stock-related queries
- Support for multiple popular stock symbols
- Last 5 days of detailed stock metrics
- Technical indicators (SMA, EMA, RSI, MACD) for advanced analysis

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Vraj-38/StockChat
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up your API keys:
   - Add your API keys in `secrets.toml`:
     ```toml
     groq_api_key = "your-groq-api-key"
     stock_api_key = "your-fmp-api-key"
     ```

5. Run the application:
```bash
streamlit run app.py
```
## Usage

1. **Select a Stock Symbol:**
   - In the sidebar, choose one or more stock symbols from the dropdown.
   - If you select multiple symbols, the app will display a side-by-side comparison.

2. **View Stock Data:**
   - The main area shows a candlestick chart and key metrics (current price, open price, high, low).
   - If you selected multiple stocks, each stock's data is displayed in separate columns.

3. **Use Technical Indicators:**
   - In the sidebar, select one or more technical indicators (SMA, EMA, RSI, MACD).
   - The chart will update to overlay the selected indicators.

4. **Chat with the AI:**
   - Type your question in the chat input box or click an example prompt.
   - The AI will analyze the stock data and provide a response.

5. **Example Prompts:**
   - "How is the stock performing?"
   - "Give me an overview of the stock"
   - "What is the highest Close rate?"
   - "What are the key technical indicators suggesting?"
   - "What is the lowest Open rate?"
   - "Show me support and resistance levels"

6. **Fallback Data:**
   - If the API limit is reached, you can use example data by checking "Use Example Stock Data" in the sidebar.

## Troubleshooting

- If you encounter API limit errors, switch to example data.
- Ensure your API keys are correctly set in `secrets.toml`.


