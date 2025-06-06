from typing import Dict

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from api import get_stock_data, groq_chat

# constants
STOCK_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "NVDA", "TSLA", "IBM", "NFLX", "AMD"
]
DEFAULT_SYMBOL = "AAPL"
EXAMPLE_PROMPTS = [
    "How is the stock performing?",
    "Give me an overview of the stock",
    "What is the highest Close rate?",
    "What are the key technical indicators suggesting?",
    "What is the lowest Open rate?",
    "Show me support and resistance levels"
]


def init_session_state() -> None:
    """creating session state variables."""
    session_defaults = {
        'messages': [],
        'current_symbol': DEFAULT_SYMBOL,
        'stock_data': pd.DataFrame(),
        'pending_prompt': None
    }

    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_stock_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Extract key stock metrics from DataFrame."""
    if df.empty:
        return {}

    return {
        'current_price': df['Close'].iloc[-1],
        'open_price': df['Open'].iloc[-1],
        'high_price': df['High'].max(),
        'low_price': df['Low'].min()
    }


def calculate_sma(df, window=20):
    return df['Close'].rolling(window=window).mean()

def calculate_ema(df, window=20):
    return df['Close'].ewm(span=window, adjust=False).mean()

def calculate_rsi(df, window=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df):
    ema12 = calculate_ema(df, window=12)
    ema26 = calculate_ema(df, window=26)
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def create_candlestick_chart(df: pd.DataFrame, symbol: str, indicators=None) -> go.Figure:
    """create plotly candlestick chart from stock data, with optional indicators."""
    fig = go.Figure()

    if not df.empty:
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Candlestick'
        ))
        if indicators:
            if 'SMA' in indicators:
                sma = calculate_sma(df)
                fig.add_trace(go.Scatter(x=df.index, y=sma, mode='lines', name='SMA (20)', line=dict(color='blue')))
            if 'EMA' in indicators:
                ema = calculate_ema(df)
                fig.add_trace(go.Scatter(x=df.index, y=ema, mode='lines', name='EMA (20)', line=dict(color='orange')))
            if 'RSI' in indicators:
                rsi = calculate_rsi(df)
                fig.add_trace(go.Scatter(x=df.index, y=rsi, mode='lines', name='RSI (14)', yaxis='y2', line=dict(color='purple')))
                # Add secondary y-axis for RSI
                fig.update_layout(yaxis2=dict(title='RSI', overlaying='y', side='right', range=[0, 100]))
            if 'MACD' in indicators:
                macd, signal = calculate_macd(df)
                fig.add_trace(go.Scatter(x=df.index, y=macd, mode='lines', name='MACD', line=dict(color='green')))
                fig.add_trace(go.Scatter(x=df.index, y=signal, mode='lines', name='MACD Signal', line=dict(color='red', dash='dot')))

    fig.update_layout(
        title=f"{symbol} Stock Price",
        yaxis_title="Price ($)",
        xaxis_title="Date",
        xaxis_rangeslider_visible=False,
        height=500
    )

    return fig


def display_stock_metrics(metrics: Dict[str, float]) -> None:
    """Display stock metrics in columns."""
    cols = st.columns(4)
    metric_labels = {
        'current_price': "Current Price",
        'open_price': "Open Price",
        'high_price': "High Price",
        'low_price': "Low Price"
    }

    for (metric, label), col in zip(metric_labels.items(), cols):
        value = metrics.get(metric, 'N/A')
        if isinstance(value, (float, int)):
            value = f"${value:.2f}"
        col.metric(label=label, value=value)


def display_chat_messages() -> None:
    """Display chat messages from session history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def display_example_prompts() -> None:
    """Display example prompts."""
    st.write("**Try these example questions:**")
    cols = st.columns(2)
    for idx, prompt in enumerate(EXAMPLE_PROMPTS):
        with cols[idx % 2]:
            if st.button(
                prompt,
                key=f"ex_{idx}",
                use_container_width=True,
                help="Click to use this example question"
            ):
                st.session_state.pending_prompt = prompt


def handle_stock_selection() -> None:
    """Handle stock symbol selection in sidebar and sidebar information is displayed."""
    with st.sidebar:
        st.header("Settings")
        selected_symbols = st.multiselect(
            "Select Stock Symbol(s) for Comparison:",
            options=STOCK_SYMBOLS,
            default=[st.session_state.current_symbol],
            help="Select one or more stocks to compare side by side."
        )
        # If only one symbol is selected, keep it as the current symbol
        if len(selected_symbols) == 1:
            new_symbol = selected_symbols[0]
            if new_symbol != st.session_state.current_symbol:
                st.session_state.current_symbol = new_symbol
                st.session_state.messages = []
                try:
                    st.session_state.stock_data = get_stock_data(
                        st.secrets["stock_api_key"],
                        new_symbol
                    )
                except Exception as e:
                    st.error(f"Failed to load data: {str(e)}")
                st.rerun()
        st.session_state.selected_symbols = selected_symbols
        st.subheader("How to use:")
        st.write("1. Select one or more stock symbols from the list")
        st.write("2. Type a question about the stock in the input box")
        st.write("3. Press Enter to get the answer from the chatbot")
        st.subheader("About:")
        st.write("This app uses Groq's Llama model to analyse stock data.")
        st.write("The chatbot is limited to a maximum of 5 days of data.")
        st.write("API pulls the last 5 months of data.")


def process_prompt(prompt: str) -> None:
    """Common processing for both example prompts and direct input."""
    # add user's message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # display the user's message instantly
    with st.chat_message("user"):
        st.write(prompt)

    # generate and display chatbot response
    with st.chat_message("assistant"):
        with st.spinner("Analysing stock data..."):
            try:
                response = generate_chat_response(prompt)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                st.write(response)
            except Exception as e:
                # logging.error(f"Chat error: {str(e)}")
                st.error("Failed to generate response. Please try again.")

    # rerun to update display
    st.rerun()


def generate_chat_response(prompt: str) -> str:
    """Generate chatbot response using API."""
    stock_name = st.session_state.current_symbol  # stock name pulled for context
    context = f"Stock data for {stock_name}: {st.session_state.stock_data.head(5).to_string()}"
    messages = [{
        "role": "user",
        "content": f"{context}\n\nQuestion: {prompt}"
    }]

    return groq_chat(
        st.secrets["groq_api_key"],
        messages
    )


def handle_chat_input() -> None:
    """Process and display chat messages."""
    # checking for pending prompt from examples
    if st.session_state.pending_prompt:
        prompt = st.session_state.pop('pending_prompt')
        process_prompt(prompt)

    #direct user input
    if prompt := st.chat_input("Ask about the stock..."):
        process_prompt(prompt)


def main():
    """Main application entry point."""
    # page settings
    st.set_page_config(
        page_title="Stock Analysis AI Chatbot",
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="📈"
    )

    # initialise the application state
    init_session_state()

    # page title
    st.title("📈 Stock Analysis AI Chatbot")

    try:
        # gets and cache stock data
        use_example_data = st.sidebar.checkbox("Use Example Stock Data", 
                                               help="Use pre-loaded example data if API limit is reached")

        if use_example_data:
            try:
                df = pd.read_csv('data/stock_data.csv')
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date', ascending=True)
                
                # Display a warning that example data is being used
                st.warning("Using example stock data from local CSV file.")
                st.session_state.stock_data = df
            except Exception as e:
                st.error(f"Error loading example data: {e}")
                return
        else:
            if st.session_state.stock_data.empty:
                try:
                    st.session_state.stock_data = get_stock_data(
                        st.secrets["stock_api_key"],
                        st.session_state.current_symbol
                    )
                except Exception as e:
                    st.error("FMP API limit (250 requests per day) reached")
                    use_example_data = st.sidebar.checkbox("Use Example Stock Data", 
                                                           help="Use pre-loaded example data if API limit is reached")
                    if use_example_data:
                        try:
                            df = pd.read_csv('data/stock_data.csv')
                            df['date'] = pd.to_datetime(df['date'])
                            df = df.sort_values('date', ascending=True)
                            
                            # Display a warning that example data is being used
                            st.warning("Using example stock data from local CSV file.")
                            st.session_state.stock_data = df
                        except Exception as load_error:
                            st.error(f"Error loading example data: {load_error}")
                    return

        # sidebar 
        handle_stock_selection()
        indicator_options = ["SMA", "EMA", "RSI", "MACD"]
        selected_indicators = st.sidebar.multiselect(
            "Technical Indicators:",
            options=indicator_options,
            default=["SMA", "EMA"],
            help="Select technical indicators to display on the chart."
        )
        st.session_state.selected_indicators = selected_indicators

        # display stock data section
        selected_symbols = st.session_state.get('selected_symbols', [st.session_state.current_symbol])
        if len(selected_symbols) > 1:
            st.subheader("Stock Comparison")
            cols = st.columns(len(selected_symbols))
            for idx, symbol in enumerate(selected_symbols):
                with cols[idx]:
                    st.markdown(f"### {symbol}")
                    try:
                        df = get_stock_data(st.secrets["stock_api_key"], symbol)
                        metrics = get_stock_metrics(df)
                        display_stock_metrics(metrics)
                        fig = create_candlestick_chart(df, symbol, indicators=selected_indicators)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error loading data for {symbol}: {e}")
        else:
            if not st.session_state.stock_data.empty:
                metrics = get_stock_metrics(st.session_state.stock_data)
                display_stock_metrics(metrics)
                fig = create_candlestick_chart(
                    st.session_state.stock_data,
                    st.session_state.current_symbol,
                    indicators=selected_indicators
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No stock data available for selected symbol.")

        # here is the chat interface
        st.subheader("Stock Analysis Chat")
        st.write("Limited to the last 5 days of data.")
        display_example_prompts()
        display_chat_messages()
        handle_chat_input()

    except Exception as e:
        # logging.error(f"Application error: {str(e)}")
        st.error("Try again tomorrow or use example data.")

if __name__ == "__main__":
    main()
