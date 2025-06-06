from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import requests
import streamlit as st
from groq import Groq

# constants
GROQ_MODEL = "llama-3.3-70b-versatile"  # Using Mixtral model, can be changed to other Groq models
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
SYSTEM_PROMPT = """You are a stock market analyst. Your role is to use this data 
to answer questions about the stock"""
stock_api_key = st.secrets["stock_api_key"]
groq_api_key = st.secrets["groq_api_key"]


def get_stock_data(api_key: str, symbol: str) -> pd.DataFrame:
    """
    Fetch historical stock data using the Financial Modeling Prep API.

    Args:
        api_key (str): FMP API key
        symbol (str): Stock symbol ('AAPL', 'GOOGL', etc)

    Returns:
        pd.DataFrame: Historical stock data with columns:
            - Open: Opening price
            - High: Highest price
            - Low: Lowest price
            - Close: Closing price
            - Adjusted Close: Adjusted closing price
            - Volume: Trading volume

    Raises:
        ValueError: If API request fails or no data is found
    """
    # calculate date range (5 months of data)
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=5 * 30)

    try:
        url = f"{FMP_BASE_URL}/historical-price-full/{symbol}"
        params = {
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "apikey": api_key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        historical_data = data.get('historical', [])
        if not historical_data:
            raise ValueError(f"No historical data found for symbol: {symbol}")

        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.sort_index(ascending=True, inplace=True)

        # column name mapping
        column_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'adjClose': 'Adjusted Close',
            'volume': 'Volume'
        }
        df.rename(columns=column_mapping, inplace=True)

        return df

    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch stock data: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error processing stock data: {str(e)}")


def groq_chat(api_key: str, messages: List[Dict[str, str]]) -> str:
    """
    Generate chat responses using the Groq API.

    Args:
        api_key (str): Groq API key
        messages (List[Dict[str, str]]): List of message dictionaries

    Returns:
        str: response from the model
    """
    try:
        client = Groq(api_key=api_key)

        full_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages
        ]

        # API request
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=full_messages,
            max_tokens=1000,
            temperature=0.7,
            stream=False
        )

        if not response or not hasattr(response, 'choices') or not response.choices:
            print("Empty or invalid response received:", response)
            raise ValueError("Invalid response from API")

        print("Successful response received")
        return response.choices[0].message.content

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error details: {error_details}")
        st.error(f"API error: {str(e)}")
        return "Cannot connect to the API. Please try again later."
