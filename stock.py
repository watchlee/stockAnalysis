#!/usr/bin/env python
# coding=utf-8


    
import requests
from io import StringIO
from datetime import datetime
import datetime
import time
from matplotlib import pyplot as plt
import matplotlib as mpl
import pandas as pd
import numpy as np
import json
import yfinance as yf

import matplotlib.pyplot as plt
from matplotlib import ticker as mticker
#from pyti.bollinger_bands import upper_bollinger_band as ubb
#from pyti.bollinger_bands import lower_bollinger_band as lbb
#from pyti.bollinger_bands import percent_b as percent_b
#from pyti.bollinger_bands import bandwidth as bd 
import mplfinance as mpf

from matplotlib import style
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mdates



# 參考 twstock 取得需要的 URL
SESSION_URL = 'http://mis.twse.com.tw/stock/index.jsp'
STOCKINFO_URL = 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_id}&_={time}'

#------------------------------------------------------------------------------------------

import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

def updateStock():
    link = 'https://quality.data.gov.tw/dq_download_json.php?nid=11549&md5_url=bb878d47ffbe7b83bfc1b41d0b24946e'
    #request stock data 
    r = requests.get(link)
    file_name = "stock_id.csv"
    print("Get today's stock from TW")
    data = pd.DataFrame(r.json())
    print("Save to stock_id.csv")
    data.to_csv(file_name,index=False, header = True)
    return file_name

def readStocks(file_name):
    stock_list = pd.read_csv(file_name)
    stock_list.columns = ['證券代號','證券名稱','成交股數','成交金額','開盤價','最高價','最低價','收盤價','漲跌價差','成交筆數']
    return stock_list

def showStocks(stock_list):
    for i in stock_list.index:
        stock_id = stock_list.loc[i,'證券代號']+'.TW'
        stock_name = stock_list.loc[i,'證券名稱']
        print(str(i)+' '+stock_id+' '+stock_name)
        selectStock(stock_id)

def selectStock(stockID):
    data = yf.Ticker(stockID)
    #get all historical_data from this stock code
    historical_data = pd.DataFrame() 
    df = data.history(period="4mo")
    historical_data = pd.concat([historical_data, df])
    time.sleep(0.8)
    stock_file = stockID+".csv"
    historical_data.to_csv(stock_file)
    return stock_file

def getStockData(stock_file):
    #data = pd.read_csv(stock_file, parse_dates=True, index_col='Date')
    data = pd.read_csv(stock_file)
    data.columns=['Date','Open','High','Low','Close','Volume','Divide','Stock split']
    #The volume of showing is incorrect
    data['Volume'] = data['Volume']/1000
    data.index = pd.to_datetime(data['Date'])
    return data


def bollingerBand(stockData,N,rate):
    STD_N = "STD_"+str(N)
    MA_N = "MA_"+str(N)
    #reference 阿水一式 2.1 
    #stockData['Upper'] = ubb(stockData['Close'],N,2.1)
    #stockData['Lower'] = lbb(stockData['Close'],N,2.1)
    #stockData['percentB'] = percent_b(stockData['Close'],N)
    stockData[STD_N] = stockData['Close'].rolling(N).std()
    stockData['Upper'] = stockData[MA_N] + (stockData[STD_N] * rate )
    stockData['Lower'] = stockData[MA_N] - (stockData[STD_N] * rate  )
    stockData['percentB'] = ((stockData['Close']-stockData['Lower']) / (stockData['Upper']-stockData['Lower']))
    stockData['Bbandwidth'] = (stockData['Upper']-stockData['Lower']) / stockData[MA_N]


def exponentialMovingAverage(stockData,N):
    EMA_NAME = "EMA_"+str(N)
    stockData['Close'] = pd.to_numeric(stockData['Close'])
    stockData[EMA_NAME] = stockData['Close'].ewm(span=N).mean()

def MACD(stockData,N,N2,DIF_DAY):
    exponentialMovingAverage(stockData,N)
    exponentialMovingAverage(stockData,N2)
    EMA_N = 'EMA_'+str(N)
    EMA_N2 = 'EMA_'+str(N2)
    stockData['DIF'] = stockData[EMA_N]-stockData[EMA_N2]
    stockData['DEM'] = stockData['DIF'].ewm(span=DIF_DAY).mean()
    stockData['OSC'] = stockData['DIF'] - stockData['DEM']
	

def movingaverage(stockData,N):
    stockData['Close'] = pd.to_numeric(stockData['Close'])
    MA_N = "MA_"+str(N)
    stockData[MA_N] = stockData['Close'].rolling(N).mean()
	
#there is bug in showing np.nan in the graph
def percentB_below(stockData):
    percentB = stockData['percentB']
    price = stockData['Close']
    signal = []
    previous = -1.0
    for date,value in percentB.iteritems():
        if value < 0 and previous >= 0:
            signal.append(price[date]*0.99)
        else:
            signal.append(np.nan)
        previous = value
    return signal 

def cal_U(num):
    if num >= 0:
        return num
    else:
        return 0
def cal_D(num):
    num = -num
    return cal_U(num)


def RSI(stockData,N,days=1):
    #relative strength index RSI
	#RS = EMA(U,n) / EMA(D,n)
	#RSI = (1 - (1/(1+RS)))*100%
    stockData['U'] = stockData['DIF'].apply(cal_U)
    stockData['D'] = stockData['DIF'].apply(cal_D)
    stockData['ema_U'] = stockData['U'].ewm(span=N).mean()
    stockData['ema_D'] = stockData['D'].ewm(span=N).mean()
    stockData['RS'] = stockData['ema_U']/stockData['ema_D']
    stockData['RSI'] = (1 - (1/(1+stockData['RS'])))*100
    #stockData['RSI']=talib.RSI(stockData['Close'])
	


def percentB_above(stockData):
    percentB = stockData['percentB']
    price = stockData['Close']
    signal   = []
    previous = 2
    for date,value in percentB.iteritems():
        if value > 1 and previous <= 1:
            signal.append(price[date]*1.01)
        else:
            signal.append(np.nan)
        previous = value
    return signal 




def showStockData2(stockData,stockName ):
    style.use('ggplot')
    price = stockData['Close']
    price.head()
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    stockData = stockData.reset_index()
    stockData['Date'] = stockData['Date'].apply(lambda d: mdates.date2num(d.to_pydatetime()))
    candlestick = [tuple(x) for x in stockData[['Date','Open','High','Low','Close']].values]
    print(candlestick)
    candlestick_ohlc(ax1, candlestick[-120:], width=0.7,colorup='r',colordown='green',alpha=0.8)
    plt.plot(stockData["MA_20"][-120:],linewidth=1,alpha=0.7,label="MA20")
    plt.legend()
    plt.show()


def showStockData(stockData,stockName):
    #marketcolor
    mc = mpf.make_marketcolors(up="red",down="green",edge="i",wick="i",volume="in",inherit=True)
    #style
    #mpf.available_styles()
    #['binance',
    # 'blueskies',
    # 'brasil',
    # 'charles',
    # 'checkers',
    # 'classic',
    # 'default',
    # 'mike',
    # 'nightclouds',
    # 'sas',
    # 'starsandstripes',
    # 'yahoo']
    s = mpf.make_mpf_style(gridaxis='both',base_mpf_style='blueskies',gridstyle='-.',y_on_right=False,marketcolors=mc)

    # 设置基本参数
    # type:绘制图形的类型，有candle, renko, ohlc, line等
    # 此处选择candle,即K线图
    # mav(moving average):均线类型,此处设置7,30,60日线
    # volume:布尔类型，设置是否显示成交量，默认False
    # title:设置标题
    # y_label_lower:设置成交量图一栏的标题
    # figratio:设置图形纵横比
    # figscale:设置图形尺寸(数值越大图像质量越高)
    symbol=stockName.replace(".csv","")
    kwargs = dict(
	type='candle', 
	mav=(5 ), 
	volume=True, 
	title='\nStock %s ' % (symbol),ylabel='OHLC Candles', 
        ylabel_lower='Trade volume',
        figscale=1.25,
        figratio=(16,5)
        )
	#figratio=(10, 6), 
	#figscale=4)

    #calculate above and below percentB
    #low_signal = percentB_below(stockData)
    #high_signal = percentB_above(stockData)
    #Days = int(Days)
    Days = 60
    apds = [
        mpf.make_addplot( stockData['Lower'][-Days:],color='b',width=0.75 ,ylabel='Lower'),
        mpf.make_addplot( stockData['Upper'][-Days:], color = 'b',width=0.75),
        mpf.make_addplot( stockData['MA_20'][-Days:], color='b' ,width=0.75),
        #mpf.make_addplot( low_signal[-Days:],color='g',markersize=200,marker='^',type='scatter' ),
        #mpf.make_addplot( high_signal[-Days:],color='g',markersize=200,marker='x',type='scatter' ),
        mpf.make_addplot( stockData['Bbandwidth'][-Days:],color='r',panel=3,width=0.75,ylabel="BD"),
        mpf.make_addplot( stockData['percentB'][-Days:],color='r', panel=2,width=0.75,ylabel="%B"),
        #mpf.make_addplot(stockData['RSI'][-Days:], color='g', panel=4, ylabel="RSI")
    ]
    
    #add legend which doesn't available in current mplfinance library
    fig, axes = mpf.plot(stockData[-Days:], **kwargs,style=s,show_nontrading= False,addplot=apds,returnfig=True,update_width_config=dict(candle_linewidth=2))
    #fig, axes = mpf.plot(stockData[-Days:], **kwargs,style=s,show_nontrading= False,addplot=apds,returnfig=True)
    #configure chart legend and title
    #axes[0].legend(['MA_5'],['MA_20'],['Upper'],['Lower'])
    #_, axs = plt.subplots(nrows=2,ncols=2,figsize=(7,5))
    #todo_list:
    #回測系統
    #加入其他技術分析
    #考慮網頁化?
    #2020-10-25
    #優化視窗 鼠標可顯示該位置的價格 數值等等...

    mpf.show()
    
def scanAllTickInList(stock_list):
    flag = determineBlownUp(stockData)
    filter_list = [] 
    pass

def determineBlownUp(stockData):
    price_threshold=10000000
    #stockData['Share']= stockData['Volume']/1000
    avg_volume=0
    blown_up_volume_flag = False
    blown_up_skill_flag = False
    
    blown_up_day = 0
    for days in range(1,5): 
        day = stockData['Date'].iloc[-days]
        High_price = stockData['High'].iloc[-days]
        Low_price = stockData['Low'].iloc[-days]
        Upper = stockData['Upper'].iloc[-days] 
        if ( Upper >= Low_price and Upper <= High_price ):
            blown_up_skill_flag = True
            blown_up_day = days
	
    close_price = 0.0
    trade_volume = 0.0
    if blown_up_skill_flag :
        for days in range(blown_up_day, blown_up_day+6):
            volume = stockData['Volume'].iloc[-days]
            if ( volume <= 0.0 ):
                return False	
            if ( days == 1 ):
                trade_volume = volume 
                close_price = stockData['Close'].iloc[-days]
            else:
                avg_volume = avg_volume + volume
    else:
        return False
        
    avg_volume = avg_volume/5
    diff_volume = trade_volume / avg_volume
    
    total_money = 1000 * trade_volume*close_price
    if ( diff_volume >= 2.0 and ( (total_money) >= price_threshold)):
        print(total_money)
        blown_up_volume_flag = True
    
    if ( blown_up_volume_flag and blown_up_skill_flag):
        return True
    return False 
    pass

def checkEachTicker(stock_list):
    filter_list = []
    for i in stock_list.index:
        stock_id = stock_list.loc[i,'證券代號']+'.TW'
        stock_name = stock_list.loc[i,'證券名稱']
        stockFile = stock_id+'.csv'
        flag = False
        try:
            stockData = getStockData(stockFile)
            movingaverage(stockData,20)
            bollingerBand(stockData,20,2.1)
            
            try:
                flag = determineBlownUp(stockData)
            except:
                pass
        except:
            pass
        if flag:
            filter_list.append(stockFile+" "+stock_name)
			 
    for line in filter_list:
        print(line)	

def run():
    '''
    file_name = updateStock()
    file_name="stock_id.csv"
    stock_list = readStocks(file_name)
    showStocks(stock_list)
	'''
    file_name = "stock_id.csv"
    stock_list = readStocks(file_name)
    checkEachTicker(stock_list)
    '''
    stockID = input("Enter stockID (.TW) for listed company (.TWO) for over-the-counter company :")
    stockFile = selectStock(stockID)
    stockData = getStockData(stockFile)
    #tempData = stockData.copy()
    movingaverage(stockData,20)
    bollingerBand(stockData,20,2.1)
    #exponentialMovingAverage(tempData,10)
    #print(tempData)
    MACD(stockData,12,26,9)
    #RSI(stockData,10)
    #print(stockData)
    determineBlownUp(stockData)
    showStockData(stockData,stockFile)
    #showStockData2(stockData,stockFile)
	'''

if __name__=="__main__":
    run()
