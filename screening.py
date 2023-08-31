# import pandas as pd

def detect_breakout_stocks(df, lookback_period, threshold):
    """
    Detect breakout stocks based on a given DataFrame, lookback period, and threshold.

    Parameters:
    - df: pandas DataFrame containing stock data
    - lookback_period: number of days to look back for calculating breakout
    - threshold: minimum percentage change to consider a breakout

    Returns:
    - List of ticker symbols that are considered breakout stocks

    Short-Term Trading (Intraday/Day Trading):

    Lookback Period: 5 to 20 days
    Threshold: 1% to 3%
    Medium-Term Trading (Swing Trading):

    Lookback Period: 20 to 50 days
    Threshold: 3% to 5%
    Long-Term Trading (Position Trading/Investing):

    Lookback Period: 50 to 200 days
    Threshold: 5% to 10% or higher
    """
    breakout_stocks = []

    for ticker in df['ticker'].unique():
        ticker_data = df[df['ticker'] == ticker].sort_values(by='date_sk_id', ascending=True)
        ticker_data['high_ma'] = ticker_data['high'].rolling(window=lookback_period).mean()
        ticker_data['low_ma'] = ticker_data['low'].rolling(window=lookback_period).mean()

        last_row = ticker_data.iloc[-1]
        if (last_row['high'] > last_row['high_ma'] * (1 + threshold / 100)) or (last_row['low'] < last_row['low_ma'] * (1 - threshold / 100)):
            breakout_stocks.append(ticker)

    return breakout_stocks


def detect_cup_and_handle(data, cup_lookback, handle_lookback, breakout_threshold):
    cup_and_handle_stocks = []
    for ticker in data['ticker'].unique():
        ticker_data = data[data['ticker'] == ticker]

        if len(ticker_data) < cup_lookback + handle_lookback:
            continue  # Not enough data points for this ticker

        cup_condition = ticker_data['adj_close'].rolling(window=cup_lookback).mean()
        handle_condition = ticker_data['adj_close'].rolling(window=handle_lookback).mean()

        # Check for cup and handle consolidation
        cup_consolidation = cup_condition.iloc[-1] <= cup_condition.iloc[-2]
        handle_consolidation = handle_condition.iloc[-1] <= handle_condition.iloc[-2]

        # Check for breakout
        breakout_condition = ticker_data['adj_close'].iloc[-1] > max(handle_condition) * (1 + breakout_threshold / 100)

        # Calculate average volume during the handle formation
        handle_start_idx = -handle_lookback
        handle_end_idx = -1
        average_handle_volume = ticker_data['volume'][handle_start_idx:handle_end_idx].mean()

        # Check for volume confirmation
        volume_confirmation = ticker_data['volume'].iloc[-1] > average_handle_volume

        # Determine if the pattern is detected

        if cup_consolidation and handle_consolidation and breakout_condition and volume_confirmation:
            cup_and_handle_stocks.append(ticker)

    return cup_and_handle_stocks


def detect_ma_crossover(data, short_window, long_window):
    ma_cross = []

    for ticker in data['ticker'].unique():
        ticker_data = data[data['ticker'] == ticker]

        if len(ticker_data) < long_window:
            continue

        short_ma = ticker_data['adj_close'].rolling(window=short_window).mean()
        long_ma = ticker_data['adj_close'].rolling(window=long_window).mean()


        # check for ma cross
        if short_ma.iloc[-1] > long_ma.iloc[-1] and short_ma.iloc[-2] <= long_ma.iloc[-2]:
            ma_cross.append(ticker)

    
    return ma_cross