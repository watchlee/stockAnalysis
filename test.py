from matplotlib import pyplot as plt
from matplotlib import style
import pandas as pd
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc
import csv
 
style.use('ggplot')
 
Analysis = "2313.TW.csv"
 
data = pd.read_csv(Analysis, parse_dates=True, index_col='Date')
 
price = data['Close']
price.head()
 
moving_avg = price.rolling(20).mean()
fig = plt.figure()
ax1 = fig.add_subplot(111)
data = data.reset_index()
data['Date'] = data['Date'].apply(lambda d: mdates.date2num(d.to_pydatetime()))
candlestick = [tuple(x) for x in data[['Date','Open','High','Low','Close']].values]
candlestick_ohlc(ax1, candlestick[-120:], width=0.7,colorup='r',colordown='green',alpha=0.8)
plt.plot(moving_avg[-120:],linewidth=1,alpha=0.7,label="MA20")
plt.legend()
plt.show()


