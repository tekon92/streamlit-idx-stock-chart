import pandas as pd

def calculate_rsi(data, window=14):
    grouped = data.groupby('ticker')
    result = []

    for ticker, group in grouped:
        delta = group['adj_close'].diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0

        average_gain = up.rolling(window=window).mean()
        average_loss = abs(down.rolling(window=window).mean())

        rs = average_gain / average_loss
        rsi = 100 - (100 / (1 + rs))

        group['rsi'] = rsi
        result.append(group)

    return pd.concat(result)


def calculate_macd(data, short_period=12, long_period=26, signal_period=9):
    grouped = data.groupby('ticker')

    result = []

    for ticker, group in grouped:
        group['ema12'] = group['adj_close'].ewm(span=short_period, adjust=False).mean()
        group['ema26'] = group['adj_close'].ewm(span=long_period, adjust=False).mean()
        group['macd'] = group['ema12'] - group['ema26']

        group['signal'] = group['macd'].ewm(span=signal_period, adjust=False).mean()
        result.append(group)

    return pd.concat(result)

def calculate_bollinger_bands(data, window=20, std_dev=2):
    grouped = data.groupby('ticker')
    result = []

    for ticker, group in grouped:
        group['sma'] = group['adj_close'].rolling(window=window, min_periods=1).mean()
        group['std'] = group['adj_close'].rolling(window=window, min_periods=1).std()
        group['upper_band'] = group['sma'] + std_dev * group['std']
        group['lower_band'] = group['sma'] - std_dev * group['std']
        result.append(group)

    return pd.concat(result)

def calculate_stochcastic_oscillator(data, k_period=14, d_period=3):
    grouped = data.groupby('ticker')
    result = []

    for ticker, group in grouped:
        group['lowest_low'] = group['low'].rolling(window=k_period, min_periods=1).min()
        group['highest_low'] = group['high'].rolling(window=k_period, min_periods=1).max()
        group['k_line'] = ((group['adj_close'] - group['lowest_low']) / (group['highest_low']) / (group['highest_low'])) * 100
        group['d_line'] = group['k_line'].rolling(window=d_period, min_periods=1).mean()
        result.append(group)

    return pd.concat(result)