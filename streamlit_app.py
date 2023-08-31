import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from charting import calculate_bollinger_bands, calculate_macd, calculate_rsi, calculate_stochcastic_oscillator
from screening import detect_breakout_stocks, detect_cup_and_handle, detect_ma_crossover
from datetime import datetime

st.set_page_config(layout="wide")

# col0 = st.columns(1)
col7, col8 = st.columns(2)
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)
col5, col6 = st.columns(2)

# initialize connection
# uses st.cache_resource to only run once
@st.cache_resource
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])

conn = init_connection()

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()
    
rows = run_query("select * from stock_ohlcv where date_sk_id >= 20220101")


df = pd.DataFrame(rows, columns=['date_sk_id', 'ticker', 'adj_close', 'close', 'high', 'low', 'open', 'volume'])

data_types = {
    'date_sk_id': 'int64',  # datetime data type
    'ticker': 'object',          # string data type
    'adj_close': 'float64',      # floating-point data type
    'close': 'float64',
    'high': 'float64',
    'low': 'float64',
    'open': 'float64',
    'volume': 'int64'            # integer data type
}

df = df.astype(data_types)
# Convert date_sk_id to string for displaying
df['date_sk_id'] = df['date_sk_id'].astype(str)

# df.sort_values(by='date_sk_id')

# df['date_sk_id'] = pd.to_datetime(df['date_sk_id']).dt.strftime('%Y-%m-%d')
df['date_sk_id'] = pd.to_datetime(df['date_sk_id'])

# df['date_sk_id'] = df['date_sk_id'].dt.date
df = df.sort_values(by='date_sk_id')


# add another metrics

# add screening
breakout_stocks = detect_breakout_stocks(df, lookback_period=3, threshold=5)
# st.write(breakout_stocks)

#cup and handle
cup_lookback = 30
handle_lookback = 5
breakout_threshold = 2

cup_and_handle = detect_cup_and_handle(df, cup_lookback, handle_lookback, breakout_threshold)
# st.write(cup_and_handle)


# Set moving average window parameters
short_window = 50  # Short-term moving average window
long_window = 100  # Long-term moving average window

# Screen stocks using moving average crossovers
screened_stocks = detect_ma_crossover(df, short_window, long_window)
# st.write(screened_stocks)



# add ma5
df['ma5'] = df.groupby('ticker')['adj_close'].rolling(window=5).mean().reset_index(0,  drop=True)


# debug

###
#add rsi
df_with_rsi = calculate_rsi(df)
# st.write(df_with_rsi)
df = pd.merge(df, df_with_rsi[['date_sk_id', 'ticker', 'rsi']], on=['date_sk_id', 'ticker'])

# add macd
df_with_macd = calculate_macd(df)

# Merge the calculated MACD and Signal values into the original DataFrame
df = pd.merge(df, df_with_macd[['date_sk_id', 'ticker', 'ema12', 'ema26', 'macd', 'signal']],
              on=['date_sk_id', 'ticker'])

# add bollinger band
df_with_bollinger = calculate_bollinger_bands(df)
df = pd.merge(df, df_with_bollinger[['date_sk_id', 'ticker', 'sma', 'std', 'upper_band', 'lower_band']], on=['date_sk_id', 'ticker'])


# add stochcastic oscillator

df_with_stoch = calculate_stochcastic_oscillator(df)
df = pd.merge(df, df_with_stoch[['date_sk_id', 'ticker', 'lowest_low', 'highest_low', 'k_line', 'd_line']], on=['date_sk_id', 'ticker'])


# filtered_df = filtered_df.sort_values(by='date_sk_id')

# with col0:
with col7:
    # create dropwdown
    available_tickers = df['ticker'].unique()
    selected_ticker = st.selectbox('Select Ticker', available_tickers)
    # selected_ticker = df[df['ticker'] == available_ticker]

    # filter the dataframe based on the selected ticker
    
    # default_start_date = max(df['date_sk_id'].min(), min(df['date_sk_id'].max(), datetime.date(2023, 8, 1)))
    start_date = st.date_input('Start Date', min_value=df['date_sk_id'].min(), max_value=df['date_sk_id'].max())
    end_date = st.date_input('End Date', min_value=start_date, max_value=df['date_sk_id'].max(), value=df['date_sk_id'].max())

    # Convert start_date and end_date to datetime64
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

with col8:

    filtered_df = df[(df['date_sk_id'] >= start_date) & (df['date_sk_id'] <= end_date) & (df['ticker'] == selected_ticker)]
    st.write(filtered_df)

with col1:
    fig = px.line(filtered_df, x='date_sk_id', y='close', title=f'Adjusted Close for {selected_ticker}')

    # explicitly set the ticks values and labes on the x-axis
    date_labels = filtered_df['date_sk_id'].dt.strftime('%Y-%m-%d')
    date_ticks = filtered_df['date_sk_id'].dt.strftime('%Y-%m-%d')

    # add ma5


    # add checkbox 
    show_ma5 = st.checkbox('Show MA5')
    if show_ma5:
        # fig.update_traces(visible='legendonly', selector=dict(name='ma5'))
        fig.add_scatter(x=filtered_df['date_sk_id'], y=filtered_df['ma5'], name='ma5')

    fig.update_xaxes(tickvals=date_ticks, ticktext=date_labels, tickangle=45)
    st.plotly_chart(fig)

with col2:
    fig_rsi = px.line(filtered_df, x='date_sk_id', y='rsi', title=f'RSI for {selected_ticker}')
    st.plotly_chart(fig_rsi)

# st.line_chart(filtered_df[['date_sk_id', 'macd', 'signal']])

with col3:
    # Create an interactive chart using Plotly
    figMacd = go.Figure()
    figMacd.add_trace(go.Scatter(x=filtered_df['date_sk_id'], y=filtered_df['macd'], mode='lines', name='MACD'))
    figMacd.add_trace(go.Scatter(x=filtered_df['date_sk_id'], y=filtered_df['signal'], mode='lines', name='Signal'))
    figMacd.update_layout(title=f"MACD and Signal Line for {selected_ticker}",
                    xaxis_title="Date",
                    yaxis_title="Value")
    st.plotly_chart(figMacd)


with col4:
    figBb = go.Figure()

    figBb.add_trace(go.Scatter(x=filtered_df['date_sk_id'], y=filtered_df['adj_close'], mode='lines', name='Close'))
    figBb.add_trace(go.Scatter(x=filtered_df['date_sk_id'], y=filtered_df['upper_band'], mode='lines', name='Upper Band'))
    figBb.add_trace(go.Scatter(x=filtered_df['date_sk_id'], y=filtered_df['lower_band'], mode='lines', name='Lower Band'))
    figBb.add_trace(go.Scatter(x=filtered_df['date_sk_id'], y=filtered_df['sma'], mode='lines', name='SMA'))

    figBb.update_layout(title=f"Bollinger Bands for {selected_ticker}",
                    xaxis_title="Date",
                    yaxis_title="Value")

    st.plotly_chart(figBb)

with col5:
    # Create a candlestick chart with volume bars using Plotly
    figVol = go.Figure(data=[go.Candlestick(x=filtered_df['date_sk_id'],
                    open=filtered_df['open'],
                    high=filtered_df['high'],
                    low=filtered_df['low'],
                    close=filtered_df['adj_close'],
                    increasing_line_color='green', decreasing_line_color='red'),
                        go.Bar(x=filtered_df['date_sk_id'], y=filtered_df['volume'], marker_color='gray')])

    figVol.update_layout(title=f"Candlestick Chart with Volume for {selected_ticker}",
                    xaxis_title="Date",
                    yaxis_title="Value")

    st.plotly_chart(figVol)


with col6:
    # Create an interactive chart using Plotly
    figStoch = go.Figure()

    figStoch.add_trace(go.Scatter(x=filtered_df['date_sk_id'], y=filtered_df['k_line'], mode='lines', name='%K Line'))
    figStoch.add_trace(go.Scatter(x=filtered_df['date_sk_id'], y=filtered_df['d_line'], mode='lines', name='%D Line'))

    figStoch.update_layout(title=f"Stochastic Oscillator Chart for {selected_ticker}",
                    xaxis_title="Date",
                    yaxis_title="Value")

    st.plotly_chart(figStoch)