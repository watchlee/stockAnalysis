#!/usr/bin/env python
# coding=utf-8
import requests
import pandas as pd
import numpy as np
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup
import re
#res = requests.get("http://isin.twse.com.tw/isin/C_public.jsp?strMode=2")
#requests.mount("file://",LocalFileAdapter())
#res = requests.get("file:///Users/hans/Code/stockAnalysis/Listed.html")


def getList():
    url = "http://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    res = requests.get(url, verify = False)
    soup = BeautifulSoup(res.text, 'html.parser')
     
    table = soup.find("table", {"class" : "h4"})
    c = 0
    index_list = []
    name_list =[]
    for row in table.find_all("tr"):
        data = []
        for col in row.find_all('td'):
            col.attrs = {}
            data.append(col.text.strip().replace('\u3000', ''))
        
        if len(data) == 1:
            pass # title 股票, 上市認購(售)權證, ...
        else:
            stock_id = re.split("[^\d]",data[0])[0]
            index_list.append(stock_id)
            name_list.append(data[0])

    print("Save to twse_stock_id.csv")
    file_name = "twse_stock_id.csv"
    dict = {"StockID" : index_list[1:],"StockName:":name_list[1:]}
    df = pd.DataFrame(data=dict)
    df.to_csv(file_name,index=False, header = True)
    

getList()
