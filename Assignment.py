# -*- coding: utf-8 -*-
"""Untitled0.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1TBxH4WAw1nwhCDG7mWGAsgUpBlt8roEL
"""

!pip install baostock

import baostock as bs
import pandas as pd

# login system
lg = bs.login()
# Display login return information
print('login respond error_code:'+lg.error_code)
print('login respond error_msg:'+lg.error_msg)

# Get CSI 500 constituent stocks
rs = bs.query_zz500_stocks('2021-01-01')
print('query_zz500 error_code:'+rs.error_code)
print('query_zz500 error_msg:'+rs.error_msg)

#Print the result set
zz500_stocks = []
while (rs.error_code == '0') & rs.next():
    # Get a record and merge the records together
    zz500_stocks.append(rs.get_row_data())
result = pd.DataFrame(zz500_stocks, columns=rs.fields)
# Output the result set to a csv file
result.to_csv("zz500_stocks.csv", encoding="gbk", index=False)

# Log out of the system
bs.logout()

result

#### login system####
lg = bs.login()
# Display login return information
print('login respond error_code:'+lg.error_code)
print('login respond error_msg:'+lg.error_msg)

#### Obtain historical K-line data of Shanghai and Shenzhen A shares####
# For detailed indicator parameters, please refer to the "Historical Market Indicator Parameters" chapter; the "minute line" parameters are different from the "daily line" parameters. The "minute line" does not contain an index.
# Minute line indicators: date, time, code, open, high, low, close, volume, amount, adjustflag
# Weekly and monthly indicators: date, code, open, high, low, close, volume, amount, adjustflag, turn, pctChg
rs = bs.query_history_k_data_plus("sh.600000",
    "date,time,code,open,high,low,close,volume,amount,adjustflag",
    start_date='2022-04-01', end_date='2022-07-31',
    frequency="30", adjustflag="3")
print('query_history_k_data_plus respond error_code:'+rs.error_code)
print('query_history_k_data_plus respond error_msg:'+rs.error_msg)

#### Print result set####
data_list = []
while (rs.error_code == '0') & rs.next():
    # Get a record and merge the records together
    data_list.append(rs.get_row_data())
result = pd.DataFrame(data_list, columns=rs.fields)

#### Output the result set to a csv file####
result.to_csv("D:\\history_A_stock_k_data.csv", index=False)

#### Log out of the system####
bs.logout()
result

def calculate_of_rsi(result, period=14):
    # Calculate daily price changes
    delta = result['close'].astype(float).diff(1)

    # Calculate gain (positive changes) and loss (negative changes)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate average gain and average loss over the specified period
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    # Calculate relative strength (RS)
    rs = avg_gain / avg_loss

    # Calculate RSI
    rsi = 100 - (100 / (1 + rs))

    return rsi

result['RSI'] = calculate_of_rsi(result)
# RSI readings below 30 indicating oversold conditions
oversold_stock = result.loc[result['RSI'] <30]
# RSI readings above 70 indicating overbought conditions
overbought_stock = result.loc[result['RSI'] >70]
oversold_stock

def calculate_stochastic_oscillator(result, k_period=14, d_period=3):
    # Calculate %K
    result['Lowest_Low'] = result['low'].astype(float).rolling(window=k_period).min()
    result['Highest_High'] = result['high'].astype(float).rolling(window=k_period).max()
    result['%K'] = ((result['close'].astype(float) - result['Lowest_Low'].astype(float)) / (result['Highest_High'] - result['Lowest_Low'])) * 100

    # Calculate %D (3-day simple moving average of %K)
    result['%D'] = result['%K'].rolling(window=d_period).mean()

    return result

result = calculate_stochastic_oscillator(result)
# %K or %D crossing above the overbought threshold (assume 90) indicate overbought_signal
overbought_signal = result.loc[(result['%K'] > 90) | (result['%D'] > 90)]
# %K or %D crossing below the oversold threshold (assume 20) indicate oversold_signal
oversold_signal = result.loc[(result['%K'] < 20) | (result['%D'] < 20)]
oversold_signal

def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    # Calculate Short-term Exponential Moving Average (EMA)
    short_ema = data['close'].ewm(span=short_window, adjust=False).mean()

    # Calculate Long-term Exponential Moving Average (EMA)
    long_ema = data['close'].ewm(span=long_window, adjust=False).mean()

    # Calculate MACD Line
    data['MACD'] = short_ema - long_ema

    # Calculate Signal Line (9-day EMA of MACD)
    data['Signal_Line'] = data['MACD'].ewm(span=signal_window, adjust=False).mean()

    # Calculate MACD Histogram
    data['MACD_Histogram'] = data['MACD'] - data['Signal_Line']

    return data

result = calculate_macd(result)
# extreme positive values in the MACD Histogram will indicate about overBought_signal
overbought_signal = result.nlargest(5, 'MACD_Histogram')
# extreme negative values in the MACD Histogram will indicate about overSold_signal
oversold_signal = result.nsmallest(5, 'MACD_Histogram')
oversold_signal

# 2 Idea which can work on given datasets.
# 1.  trade_when(rank(ts_delta(close,5)) > 0.5, -rank(close - (high+low)/2), -1)
# 2.  trade_when(volume > ts_mean(volume,5), -rank(close - (high+low)/2), -1)

# tradewhen :  trade_when(condition, condition satisfies based idea, condition not satisfies based idea)
# ts_delta(value,x) :  (todays value - value x days before)

# Both idea is based mean_reversion idea:

#   1. Condition : take difference between today close and close price 5 days ago then assign capital based on weight. We will pick top 50% stocks
    #  if condition satisfied, price reversion is likely to happen else we will short the stock.
    # Idea will work :  Mean Reversion ideas are suitable on Large Cap company and momemtum based idea work on mid/small size company.
#   2. Condition : Volume is higer than last 5 days avg volume. Rest implementation is same.