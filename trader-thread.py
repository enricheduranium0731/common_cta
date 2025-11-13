#!/usr/bin/python
# coding=utf-8
import numpy as np
import pandas as pd
import time
import math
from datetime import datetime, timedelta,timezone
import os
import sys
import threading
import time
import matplotlib.pyplot as plt
from InterCandle import InterCandle
import ccxt
import mplfinance as mpf
import data_eng
import common_eng
import deal_eng
        
dict_symbols={}
dict_period={}
dict_plot={}
dict_comment={}
dict_order={}
    
asset=0.0
sleepTime=60
sharpeBase=0.03
closeRate=0.03
dHoursCloseRate=0.15
iCloseZoom=36
miniWin=0.03
maxHoldinhg=8

work_dir=os.path.dirname(os.path.abspath(__file__))
arr_MaMethod=["MODE_SMA"]

arr_symbols=[]
arr_PeriodTick=["15m"]
arr_PeriodS=["15m","30m","1h","4h","1d"]
arr_PeriodI=[15,30,60,240,1440]
strategyPatten=""
dataFile=""
     
strategyPatten=sys.argv[1]
iPeriod=int(sys.argv[2]) 
dataYear=float(sys.argv[3])  
run_type=sys.argv[4]
db_host=sys.argv[5]
dataFile="products--cta.txt"
dict_Strategy={}

arrPeriod=[iPeriod]
if iPeriod==0:
    arrPeriod=[60,240]
    dict_Strategy["supertrend"]=arrPeriod
    dict_Strategy["superma"]=arrPeriod
    dict_Strategy["trend"]=arrPeriod
    dict_Strategy["bollb"]=arrPeriod
    dict_Strategy["macd"]=arrPeriod
    
if iPeriod==60:
    dict_Strategy["supertrend"]=arrPeriod
    dict_Strategy["trend"]=arrPeriod
    dict_Strategy["stochastic"]=arrPeriod
    dict_Strategy["macd"]=arrPeriod
    dict_Strategy["rsi"]=arrPeriod
    dict_Strategy["bollb"]=arrPeriod
    dict_Strategy["superma"]=arrPeriod
    
if iPeriod==240:
    dict_Strategy["supertrend"]=arrPeriod
    dict_Strategy["trend"]=arrPeriod
    #dict_Strategy["stochastic"]=arrPeriod
    dict_Strategy["macd"]=arrPeriod
    dict_Strategy["rsi"]=arrPeriod
    dict_Strategy["bollb"]=arrPeriod
    dict_Strategy["snnok"]=arrPeriod
    dict_Strategy["superma"]=arrPeriod
    
iRealDataCounts=500
iPosReadyCount=12
iRefContinueCount=3
iContinueCount=60
iContinueCount2=48
iContinueLimit=12
dShadowRate=0.7

iMacdBrokenRefCount=12
iMaReverseCount=9
iMaQuitCount=5
iMaEntryCount=3
iPreMacdCount=0
iPreFixedMacdCount=9
maClosePeriod=15
iPeriodSuperRef=10
iPeriodSuperQuit=9
iPeriodFrom=5
iPeriodTo=10
iPeriodInd=30    
chanCount=5
iRefChanCount=80
iPeriodInd1=iPeriodInd2=30
dictClosePeriod1=dictClosePeriod2={}    

neural_count = 100

MODE_MAIN = 0
MODE_UPPER = 1
MODE_LOWER = 2
MODE_SIGNAL = 3
PRICE_CLOSE = 'Close'
PRICE_OPEN = 'Open'

class traderThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        
    def run(self):  
        if self.name =="gatheringdata":
            dataThread1 = data_eng.dataThread()
            while True:
                dict_symbol=dataThread1.initK(run_type,"all",dataYear)
                common_eng.dict_symbol=dict_symbol
                break
                    
        if self.name =="gatheringtick":
            dataThread1 = data_eng.dataThread()
            while True:
                dict_symbol=dataThread1.initTick(run_type)
                common_eng.dict_symbol=dict_symbol
                time.sleep(5) 
         
        if self.name =="ordering":
            while True:
                self.detecting(run_type)
                time.sleep(5)    
                if run_type=="test":
                    self.report()
                    break

        if self.name =="auto_close":
            while True:
                deal_eng.auto_close() 
                time.sleep(5)
                if run_type=="test":
                    break
                    
    def getDict(self,symbol,period,dict,value):
        obj1=dict.get(symbol,None)
        if obj1==None:
            return value            
        obj2=obj1.get(period,None)
        if obj2==None:
            return value
        
        return  obj2   

    def setDict(self,symbol,period,dict,value):
        obj1={}
        obj1[period]=value
        dict[symbol]=obj1 
                            
    def refArrayInd(self,arr,value):
        ind=-1
        for i in range(1,len(arr)):
            if value==arr[i-1]:
                ind=i-1
                break
        return ind    
                
    def antiMaStrategy(self,symbol,strategy,period,k):
        if (not strategy=="antima"):
            return 0 
            
        commonThread1 = common_eng.commonThread()    
        for method in arr_MaMethod:        
            if commonThread1.get2LineDownId(symbol,period,5,10,k, method)>=k+iMaReverseCount:
                return 1
                
        for method in arr_MaMethod:        
            if commonThread1.get2LineUpId(symbol,period,5,10,k, method)>=k+iMaReverseCount:
                return -1
        return 0

    def supertrendStrategy(self,symbol,strategy,period,k):
        if (not strategy=="supertrend"):
            return 0   
        
        commonThread1 = common_eng.commonThread()    
        for y in range(6,9):
            z=commonThread1.iContinueUpFromBottomByLowId(symbol,iContinueCount2,k,period,y,iRefContinueCount)
            if (z>0) and (z-k<=9):
                return 1            
            
        for y in range(6,9):
            z=commonThread1.iContinueDownFromTopByHighId(symbol,iContinueCount2,k,period,y,iRefContinueCount)
            if (z>0) and (z-k<=9):
                return -1
                
        return 0
        
    def snnStrategy(self,symbol,strategy,period,k):
        if (not strategy=="snnok"):
            return 0    
                    
        for method in arr_MaMethod:
            if deal_eng.isSNNDealOk(symbol,"BUY"):
                return 1  
                
            # if self.isPowerMaUp(symbol,30,60,100,period,arr_MaMethod[0],k,12):
                # return 1     

            # if self.isPowerMaUp(symbol,21,89,144,period,arr_MaMethod[0],k,12):
                # return 1
                
            # if self.isPowerMaUp(symbol,10,20,60,period,arr_MaMethod[0],k,12):
                # return 1  
                
        for method in arr_MaMethod:
            if deal_eng.isSNNDealOk(symbol,"SELL"):
                return -1 
                
            # if self.isPowerMaDown(symbol,30,60,100,period,arr_MaMethod[0],k,12):
                # return -1 

            # if self.isPowerMaDown(symbol,21,89,144,period,arr_MaMethod[0],k,12):
                # return -1 
                
            # if self.isPowerMaDown(symbol,10,20,60,period,arr_MaMethod[0],k,12):
                # return -1  
                
        return 0

    def supermaStrategy(self,symbol,strategy,period,k):
        if (not strategy=="superma"):
            return 0    

        # for method in arr_MaMethod:
            # if self.isSuperMaUp(symbol,10,30,60,period,arr_MaMethod[0],k,12):
                # return 1  
        commonThread1 = common_eng.commonThread()        
        for method in arr_MaMethod:
            if commonThread1.isSuperMaUp(symbol,30,60,100,period,arr_MaMethod[0],k,12):
                return 1  
                
        for method in arr_MaMethod:
            if commonThread1.isSuperMaUp(symbol,21,89,144,period,arr_MaMethod[0],k,12):
                return 1 

        # for method in arr_MaMethod:
            # if self.isSuperMaDown(symbol,10,30,60,period,arr_MaMethod[0],k,12):
                # return -1 
                
        for method in arr_MaMethod:
            if commonThread1.isSuperMaDown(symbol,30,60,100,period,arr_MaMethod[0],k,12):
                return -1 

        for method in arr_MaMethod:
            if commonThread1.isSuperMaDown(symbol,21,89,144,period,arr_MaMethod[0],k,12):
                return -1 
                
        return 0
        
    def trendStrategy(self,symbol,strategy,period,k):
        if (not strategy=="trend"):
            return 0     
            
        commonThread1 = common_eng.commonThread()        
        if commonThread1.isCanDeal(symbol,period,"trend","BUY","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看空策略检查###############"):
            #return 1
            if (not commonThread1.isCanDeal(symbol,period,"trend","SELL","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看空策略检查###############")):
                if commonThread1.getRefHighInd(symbol, iContinueCount, k, period,12)<commonThread1.getRefLowInd(symbol, iContinueCount, k, period,12):
                    return 1
            
        if commonThread1.isCanDeal(symbol,period,"trend","SELL","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看空策略检查###############"):
            #return -1
            if (not commonThread1.isCanDeal(symbol,period,"trend","BUY","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看空策略检查###############")):
                if commonThread1.getRefHighInd(symbol, iContinueCount, k, period,12)>commonThread1.getRefLowInd(symbol, iContinueCount, k, period,12):
                    return -1
                    
        return 0        

    def macdStrategy(self,symbol,strategy,period,k):
        if (not strategy=="macd"):
            return 0   
            
        commonThread1 = common_eng.commonThread() 
        
        y=commonThread1.iMacdUpInd(symbol,period,k)
        if (y>0) and (y-k<12): 
            return 1 

        y=commonThread1.iMacdDownInd(symbol,period,k)
        if (y>0) and (y-k<12):  
            return -1 
                
        return 0
        
    def stochasticStrategy(self,symbol,strategy,period,k):
        if (not strategy=="stochastic"):
            return 0   
        # if  symbol==symbol:
            # return 0
        
        commonThread1 = common_eng.commonThread()
        
        y=commonThread1.iKdjDownInd(symbol,period,k)
        if ((y>0) and ((y-k)<9)):
            return -1
            
        y=commonThread1.iKdjUpInd(symbol,period,k)
        if ((y>0) and ((y-k)<9)):
            return 1
            
        return 0       
        
    def bollbStrategy(self,symbol,strategy,period,xInd):
        if (not strategy=="bollb"):
            return 0  
            
        commonThread1 = common_eng.commonThread()
        
        if (commonThread1.isBandGoUp(symbol,period,xInd)):
            return 1

        if (commonThread1.isTouchedBottomBand(symbol,period,xInd)):
            return 1
                        
        if (commonThread1.isBandGoDown(symbol,period,xInd)):
            return -1
            
        if (commonThread1.isTouchedTopBand(symbol,period,xInd)):
            return -1
                        
        return 0

    def rsiStrategy(self,symbol,strategy,period,xInd):
        if (not strategy=="rsi"):
            return 0  
        
        commonThread1 = common_eng.commonThread()
        ##BUY
        # zCnt1 = zCnt2 = 0

        # y=self.iMacdUpInd(symbol,period,xInd)
        # if (y>0) and (y-xInd<12):
            # zCnt1+=1
            
        # x=self.iKdjUpInd(symbol,period,xInd)        
        # if (x>0) and (x-xInd<9):
            # zCnt2+=1                    

        # z=self.getBandUpInd(symbol,period,xInd)
        # if ((z>0) and ((z-xInd)<9)):
            # zCnt2+=1

        # if (self.iRsiUpInd(symbol, period, xInd ,12,30,40)>0) and (self.iRsiUpInd(symbol, period, xInd ,12,30,40)<xInd+6):
            # return 1
        
        if (commonThread1.isRsiUp(symbol, period, xInd ,9,14,30)):
            return 1
            
        # if (zCnt1>0) and (zCnt2>1):
        
            # return 1
        
        ##SELL        
        zCnt1 = zCnt2 = 0
        # y=self.iMacdDownInd(symbol,period,xInd)
        # if (y>0) and (y-xInd<12):
            # zCnt1+=1
            
        # x=self.iKdjDownInd(symbol,period,xInd)        
        # if (x>0) and (x-xInd<9):
            # zCnt2+=1                    

        # z=self.getBandDownInd(symbol,period,xInd)
        # if ((z>0) and ((z-xInd)<9)):
            # zCnt2+=1

        # if (self.iRsiDownInd(symbol, period, xInd ,12,70,60)>0) and (self.iRsiDownInd(symbol, period, xInd ,12,70,60)<xInd+6):
            # return -1
        
        if (commonThread1.isRsiDown(symbol, period, xInd ,9,14,70)):
            return -1
        
        # if (zCnt1>0) and (zCnt2>1):
            # return -1
            
        return 0
        
        
                       
    def placeOrder(self,symbol,period,dect_type,type,strategyV,ind):   
        global dict_order,dict_plot        
        chanCloseCount=8
        winRate=1.5
        if period>30:
            chanCloseCount=6
        if period>60:
            winRate=2.0
            chanCloseCount=4
            
        orders=dict_order.get(symbol,None)    
        s_type=""
        s_strategy=""
        d_open=self.iClose(symbol,period,ind)
        d_close=0
        d_win=0
        d_lose=0
        tempT=self.iTime(symbol,period,ind)

    
        if strategyV=="antima" or strategyV=="supertrend":
            if type=="BUY":
                d_lose=self.iClose(symbol,period,ind)-self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount
                d_win=self.iClose(symbol,period,ind)+self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount*winRate
            if type=="SELL":
                d_lose=self.iClose(symbol,period,ind)+self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount
                d_win=self.iClose(symbol,period,ind)-self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount*winRate

        if strategyV=="rsi":
            if type=="BUY":
                d_lose=self.iClose(symbol,period,ind)-self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount
                d_win=self.iClose(symbol,period,ind)+self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount*winRate
            if type=="SELL":
                d_lose=self.iClose(symbol,period,ind)+self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount
                d_win=self.iClose(symbol,period,ind)-self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount*winRate
                
        if (True):    
            if type=="BUY":
                d_lose=self.iClose(symbol,period,ind)-self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount
                d_win=self.iClose(symbol,period,ind)+self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount*winRate
            if type=="SELL":
                d_lose=self.iClose(symbol,period,ind)+self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount
                d_win=self.iClose(symbol,period,ind)-self.getAvgSpace(symbol,period,iContinueCount,ind)*chanCloseCount*winRate
        
        if dect_type=="real":
            deal_eng.gen_deal(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
            return
            
        if (not orders==None):
            times=orders.keys()
            if len(times)>0:
                dealed=False
                for time in times:
                    #if True:
                    strategys=orders.get(time,None)                                           
                    s_type=strategys.get("type","")
                    s_strategy=strategys.get("strategy","")                    
                    if (strategys.get("close",0)<=0 and s_type==type and s_strategy==strategyV):
                        dealed=True
                              
                if not dealed:
                    d_open=self.iClose(symbol,period,ind)                
                    strategy={"time":tempT,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":0,"win":d_win,"lose":d_lose}
                    orders[tempT]=strategy
                    dict_order[symbol]=orders
                    
                    if type=="BUY":
                        dict_plot[symbol][period].loc[tempT,'signal']=1.0
                        dict_plot[symbol][period].loc[tempT,'signal_long']=d_open                        
                    if type=="SELL":
                        dict_plot[symbol][period].loc[tempT,'signal']=-1.0
                        dict_plot[symbol][period].loc[tempT,'signal_short']=d_open
                        
                    print("标的:("+symbol+")交易生成:")
                    print(strategy)
                    
        else:
            strategy={"time":tempT,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":0,"win":d_win,"lose":d_lose}
            orders={tempT:strategy}
            dict_order[symbol]=orders
            
            if type=="BUY":
                dict_plot[symbol][period].loc[tempT,'signal']=1.0
                dict_plot[symbol][period].loc[tempT,'signal_long']=d_open
            if type=="SELL":
                dict_plot[symbol][period].loc[tempT,'signal']=-1.0
                dict_plot[symbol][period].loc[tempT,'signal_short']=d_open
            
            print("标的:("+symbol+")交易生成:")
            print(strategy)    
    
    def closeOrder(self,symbol,period,dect_type,type,strategyV,ind):
        global dict_order,asset,dictClosePeriod1,dictClosePeriod2
        
        if dect_type=="real":
            data=deal_eng.get_close_deal(symbol,type,strategyV,period)
            if (len(data)<=0):
                return
                
            s_type=data.iloc[0,2]
            s_strategy=data.iloc[0,3]
            d_open=data.iloc[0,5]
            d_close=data.iloc[0,6]
            
            d_high=self.iHigh(symbol,period,ind)
            d_low=self.iHigh(symbol,period,ind)
            
            d_win=data.iloc[0,7]
            d_lose=data.iloc[0,8]
            
            time=data.iloc[0, 9]#pd.to_datetime(data.iloc[0, 9])            
            
            if (d_close==0 and s_type==type and s_strategy==strategyV):
                closed=False
                d_close=self.iClose(symbol,period,ind) 

                if (strategyV=="superma"):
                    if type=="BUY":
                        d_close=self.iClose(symbol,period,ind)
                        if d_close<=d_open*(1-closeRate):                            
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止损--")
                            print(strategy)  

                        if (d_close>(d_open+self.iAtr(symbol,period,14,ind)*5)):
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止盈++")
                            print(strategy)  
                            
                        if self.iMA(symbol,period,self.getDict(symbol,period,dictClosePeriod1,10),ind,arr_MaMethod[0],PRICE_CLOSE)<self.iMA(symbol,period,self.getDict(symbol,period,dictClosePeriod2,30),ind,arr_MaMethod[0],PRICE_CLOSE):
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            closed=True
                            print("标的:("+symbol+")技术平仓**")
                            print(strategy)  

                        return

                    if type=="SELL":
                        d_close=self.iClose(symbol,period,ind)
                        if d_close>=d_open*(1+closeRate):
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            closed=True
                            print("标的:("+symbol+")止损--")
                            print(strategy) 

                        if (d_close<(d_open-self.iAtr(symbol,period,14,ind)*5)):
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止盈++")
                            print(strategy) 
                            
                        if self.iMA(symbol,period,self.getDict(symbol,period,dictClosePeriod1,10),ind,arr_MaMethod[0],PRICE_CLOSE)>self.iMA(symbol,period,self.getDict(symbol,period,dictClosePeriod2,30),ind,arr_MaMethod[0],PRICE_CLOSE):
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            closed=True
                            print("标的:("+symbol+")技术平仓**")
                            print(strategy)  

                        return
                            
                if (True): #(strategyV=="others"):
                    ind2=period*ind//15
                    xCount=self.getRecentInd(symbol,15,time,period*ind//15)
                    if type=="BUY":                    
                        # if (((d_close-d_open)/d_open)<=miniWin) and (d_open<d_close):
                            # return
                                
                        if self.iHigh(symbol,15,self.getHighInd(symbol,xCount,ind2,15))>d_open*(1+0.02):
                            if (self.iHigh(symbol,15,self.getHighInd(symbol,xCount,ind2,15))-self.iClose(symbol,15,ind2))/(self.iHigh(symbol,15,self.getHighInd(symbol,xCount,ind2,15))-d_open)>=0.3:
                                d_close=self.iClose(symbol,period,ind)
                                strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                closed=True
                                print("标的:("+symbol+")技术平仓**")
                                print(strategy) 
                            else:
                                return
                                
                        # for x in [y for y in arr_PeriodI if (y>=240 and y<1440)]:
                            # xInd=period*ind//x
                            # if (self.iMacdDownInd(symbol,x,xInd)>0) and (self.iMacdDownInd(symbol,x,xInd)<xInd+12):
                                # if  iPreMacdCount>=iPreFixedMacdCount:
                                    # d_close=self.iClose(symbol,period,ind)
                                    # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                    # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                    # closed=True
                                    # print("标的:("+symbol+")技术平仓**")
                                    # print(strategy)
                                
                            # iStochasticLimit=80
                            # if period>=240:
                                # iStochasticLimit=80
                            # if (self.iStochastic(symbol,x,14,3,"SMA","MAIN",period*ind//x)>=iStochasticLimit) and (self.iStochastic(symbol,x,14,3,"SMA","MAIN",period*ind//x)<self.iStochastic(symbol,x,14,3,"SMA","SIGNAL",period*ind//x)):                                            
                                # d_close=self.iClose(symbol,period,ind)
                                # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                # closed=True
                                # print("标的:("+symbol+")技术平仓**")
                                # print(strategy) 

                            # if (self.isBandGoDown(symbol,x,xInd)):
                                # if  iPreMacdCount>=iPreFixedMacdCount:
                                    # d_close=self.iClose(symbol,period,ind)
                                    # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                    # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                    # closed=True
                                    # print("标的:("+symbol+")技术平仓**")
                                    # print(strategy)
                                    
                            # if (self.isTouchedTopBand(symbol,x,xInd)):
                                # if  iPreMacdCount>=iPreFixedMacdCount:
                                    # d_close=self.iClose(symbol,period,ind)
                                    # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                    # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                    # closed=True
                                    # print("标的:("+symbol+")技术平仓**")
                                    # print(strategy) 
                                
                        # for x in [y for y in arr_PeriodI if  (y>=240 and y<1440)]:
                            # xInd=period*ind//x                                                
                            # if commonThread1.isCanDeal(symbol,x,"trend","SELL","trend",xInd,"标的:("+symbol+"),周期:("+str(x)+")分钟"+"趋势看空策略检查###############"):
                                # if (not commonThread1.isCanDeal(symbol,x,"trend","BUY","trend",xInd,"标的:("+symbol+"),周期:("+str(x)+")分钟"+"趋势看空策略检查###############")):
                                    # if self.getRefHighInd(symbol, iContinueCount, xInd, x,12)>self.getRefLowInd(symbol, iContinueCount, xInd, x,12):
                                        # d_close=self.iClose(symbol,period,ind)
                                        # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                        # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                        # closed=True
                                        # print("标的:("+symbol+")技术平仓**")
                                        # print(strategy)                    
                    
                    if type=="SELL":
                        # if (((d_open-d_close)/d_open)<=miniWin) and (d_open>d_close):
                            # return

                        if self.iLow(symbol,15,self.getLowInd(symbol,xCount,ind2,15))<d_open*(1-0.02):
                            if (self.iClose(symbol,15,ind2)-self.iLow(symbol,15,self.getLowInd(symbol,xCount,ind2,15)))/(d_open-self.iLow(symbol,15,self.getLowInd(symbol,xCount,ind2,15)))>=0.3:
                                d_close=self.iClose(symbol,period,ind)
                                strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                closed=True
                                print("标的:("+symbol+")技术平仓**")
                                print(strategy) 
                            else:
                                return
                                
                        # for x in [y for y in arr_PeriodI if (y>=240 and y<1440)]:
                            # xInd=period*ind//x    
                            # if (self.iMacdUpInd(symbol,x,xInd)>0) and (self.iMacdUpInd(symbol,x,xInd)<xInd+12):
                                # if  iPreMacdCount>=iPreFixedMacdCount:
                                    # d_close=self.iClose(symbol,period,ind)
                                    # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                    # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                    # closed=True
                                    # print("标的:("+symbol+")技术平仓**")
                                    # print(strategy)
                                
                            # iStochasticLimit=20
                            # if period>=240:
                                # iStochasticLimit=20        
                            # if (self.iStochastic(symbol,x,14,3,"SMA","MAIN",period*ind//x)<iStochasticLimit) and (self.iStochastic(symbol,x,14,3,"SMA","MAIN",period*ind//x)>self.iStochastic(symbol,x,14,3,"SMA","SIGNAL",period*ind//x)):
                                # d_close=self.iClose(symbol,period,ind)
                                # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                # closed=True
                                # print("标的:("+symbol+")技术平仓**")
                                # print(strategy)                                 

                            # if (self.isBandGoUp(symbol,x,xInd)):
                                # d_close=self.iClose(symbol,period,ind)
                                # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                # closed=True
                                # print("标的:("+symbol+")技术平仓**")
                                # print(strategy)

                            # if (self.isTouchedBottomBand(symbol,x,xInd)):
                                # d_close=self.iClose(symbol,period,ind)
                                # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                # closed=True
                                # print("标的:("+symbol+")技术平仓**")
                                # print(strategy) 
                                
                        # for x in [y for y in arr_PeriodI if (y>=240 and y<1440)]:
                            # xInd=period*ind//x                    
                            # if commonThread1.isCanDeal(symbol,x,"trend","BUY","trend",xInd,"标的:("+symbol+"),周期:("+str(x)+")分钟"+"趋势看空策略检查###############"):
                                # if (not commonThread1.isCanDeal(symbol,x,"trend","SELL","trend",xInd,"标的:("+symbol+"),周期:("+str(x)+")分钟"+"趋势看空策略检查###############")):
                                    # if self.getRefHighInd(symbol, iContinueCount, xInd, x,12)<self.getRefLowInd(symbol, iContinueCount,xInd, x,12):
                                        # d_close=self.iClose(symbol,period,ind)
                                        # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                        # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                                        # closed=True
                                        # print("标的:("+symbol+")技术平仓**")
                                        # print(strategy)
                                                                                                                           
                if (True):
                    if type=="BUY":
                        d_close=self.iClose(symbol,period,ind)
                        if d_close<=d_open*(1-closeRate):                            
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止损--")
                            print(strategy)   
 
                        if (((d_close-d_open)/d_open)>=closeRate*1.5):
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止盈++")
                            print(strategy)  
                        
                        zCnt=3
                        if period<60:
                            zCnt=5                            
                        if period>60:
                            zCnt=2 
                            
                        if (d_close>(d_open+self.iAtr(symbol,60,14,period*ind//60)*5)) and (((d_close-d_open)/d_open)>=miniWin):
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止盈++")
                            print(strategy)                                                

                    if type=="SELL":                            
                        d_close=self.iClose(symbol,period,ind)
                        if d_close>=d_open*(1+closeRate): 
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_lose,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止损--")
                            print(strategy)  

                        if (((d_open-d_close)/d_open)>=closeRate*1.5):
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止盈++")
                            print(strategy) 

                        zCnt=3
                        if period<60:
                            zCnt=5                            
                        if period>60:
                            zCnt=2 
                            
                        if (d_close<(d_open-self.iAtr(symbol,60,14,period*ind//60)*5)) and (((d_open-d_close)/d_open)>=miniWin):
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")止盈++")
                            print(strategy) 
                            
                if strategyV=="antima":
                    if type=="BUY":
                        if self.iClose(symbol,period,ind)<d_lose:
                            d_close=self.iClose(symbol,period,ind)
                            # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                            # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            # print("标的:("+symbol+")止损--")
                            # print(strategy) 

                        if (self.get2LineUpId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount): 
                        #if self.iMA(symbol,period,5,ind,arr_MaMethod[0],PRICE_CLOSE)>=self.iMA(symbol,period,maClosePeriod,ind,arr_MaMethod[0],PRICE_CLOSE):
                            if (((d_close-d_open)/d_open)<=miniWin):
                                return 
                                
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")技术平仓**")
                            print(strategy)    
                            
                    if type=="SELL":
                        if self.iClose(symbol,period,ind)>d_lose:
                            d_close=self.iClose(symbol,period,ind)
                            # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                            # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            # print("标的:("+symbol+")止损--")                                        
                            # print(strategy)    
                        
                        if (self.get2LineDownId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount):
                        #if self.iMA(symbol,period,5,ind,arr_MaMethod[0],PRICE_CLOSE)<=self.iMA(symbol,period,maClosePeriod,ind,arr_MaMethod[0],PRICE_CLOSE):
                            if (((d_open-d_close)/d_open)<=miniWin):
                                return                     
                                
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")技术平仓**")
                            print(strategy)  

                if strategyV=="powerma":
                    if type=="BUY":
                        if self.iClose(symbol,period,ind)<d_lose:
                            d_close=self.iClose(symbol,period,ind)
                            # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                            # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            # print("标的:("+symbol+")止损--")
                            # print(strategy) 

                        if (self.get2LineDownId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount): 
                        #if self.iMA(symbol,period,5,ind,arr_MaMethod[0],PRICE_CLOSE)>=self.iMA(symbol,period,maClosePeriod,ind,arr_MaMethod[0],PRICE_CLOSE):
                            if (((d_close-d_open)/d_open)<=miniWin):
                                return 
                                
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")技术平仓**")
                            print(strategy)    
                            
                    if type=="SELL":
                        if self.iClose(symbol,period,ind)>d_lose:
                            d_close=self.iClose(symbol,period,ind)
                            # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                            # deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            # print("标的:("+symbol+")止损--")                                        
                            # print(strategy)    
                        
                        if (self.get2LineUpId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount):
                        #if self.iMA(symbol,period,5,ind,arr_MaMethod[0],PRICE_CLOSE)<=self.iMA(symbol,period,maClosePeriod,ind,arr_MaMethod[0],PRICE_CLOSE):
                            if (((d_open-d_close)/d_open)<=miniWin):
                                return                     
                                
                            d_close=self.iClose(symbol,period,ind)
                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                            deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                            print("标的:("+symbol+")技术平仓**")
                            print(strategy) 
                            
                if type=="BUY":
                    d_close=self.iClose(symbol,period,ind)
                        
                    if d_close<=d_open*(1-closeRate):
                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                        deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                        closed=True
                        print("标的:("+symbol+")止损--")
                        print(strategy) 
                        
                    # if (((d_close-d_open)/d_open)<=miniWin):
                        # return
                        
                    if (((d_close-d_open)/d_open)>=closeRate*1.5):
                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                        deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                        closed=True
                        print("标的:("+symbol+")止盈++")
                        print(strategy)                                                        

                if type=="SELL":
                    d_close=self.iClose(symbol,period,ind)
                        
                    if d_close>=d_open*(1+closeRate):
                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                        deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                        closed=True
                        print("标的:("+symbol+")止损--")
                        print(strategy)  
                        
                    # if (((d_open-d_close)/d_open)<=miniWin):
                        # return
                        
                    if (((d_open-d_close)/d_open)>=closeRate*1.5):
                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                        deal_eng.close_order(symbol,type,strategyV,period,d_open,d_close,d_win,d_lose)
                        closed=True
                        print("标的:("+symbol+")止盈++")
                        print(strategy)  

            return
                            
        orders=dict_order.get(symbol,None)    
        if (not orders==None):
            times=orders.keys()
            tempT=self.iTime(symbol,period,ind)
            if len(times)>0:            
                for time in times:
                    if time <tempT:                  
                        strategys=orders.get(time,None)
                        if (not strategys==None):
                            s_type=strategys.get("type","")
                            s_strategy=strategys.get("strategy","")
                            d_open=strategys.get("open",0)
                            d_close=strategys.get("close",0)
                            
                            d_high=self.iHigh(symbol,period,ind)
                            d_low=self.iHigh(symbol,period,ind)
                            
                            d_win=strategys.get("win",0)
                            d_lose=strategys.get("lose",0) 
                            
                            if (d_close==0 and s_type==type and s_strategy==strategyV):
                                closed=False

                                if (strategyV=="superma"):
                                    d_close=self.iClose(symbol,period,ind)
                                    if type=="BUY":
                                        if d_close<=d_open*(1-closeRate):
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                            asset +=(d_close-d_open)/d_open
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")止损--")
                                            print(strategy) 
 
                                        if (d_close>(d_open+self.iAtr(symbol,period,14,ind)*5)):
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                            asset +=((d_close-d_open)/d_open)
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            deal_eng.insert_testdata(db_host,symbol,type,strategyV,period,d_open,d_close,d_win,d_lose,time)
                                            print("标的:("+symbol+")止盈++")
                                            print(strategy)   
                                            
                                        if self.iMA(symbol,period,self.getDict(symbol,period,dictClosePeriod1,10),ind,arr_MaMethod[0],PRICE_CLOSE)<self.iMA(symbol,period,self.getDict(symbol,period,dictClosePeriod2,30),ind,arr_MaMethod[0],PRICE_CLOSE):                                            
                                            #if (d_close<self.iMA(symbol,period,30,ind,arr_MaMethod[0],PRICE_CLOSE)):
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                            asset +=((d_close-d_open)/d_open)
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")技术平仓**")
                                            print(strategy)                                                                                        

                                        return

                                    if type=="SELL":
                                        if d_close>=d_open*(1+closeRate):
                                            if (d_close>self.iMA(symbol,period,30,ind,arr_MaMethod[0],PRICE_CLOSE)):                                        
                                                strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                orders[time]=strategy
                                                dict_order[symbol]=orders
                                                dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                asset +=(d_open-d_close)/d_open
                                                dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                closed=True
                                                print("标的:("+symbol+")止损--")
                                                print(strategy)  

                                        if (not closed) and (d_close<(d_open-self.iAtr(symbol,period,14,ind)*5)):
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                            asset +=(d_open-d_close)/d_open
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            deal_eng.insert_testdata(db_host,symbol,type,strategyV,period,d_open,d_close,d_win,d_lose,time)
                                            print("标的:("+symbol+")止盈++")
                                            print(strategy) 
                                            
                                        if self.iMA(symbol,period,self.getDict(symbol,period,dictClosePeriod1,10),ind,arr_MaMethod[0],PRICE_CLOSE)>self.iMA(symbol,period,self.getDict(symbol,period,dictClosePeriod2,30),ind,arr_MaMethod[0],PRICE_CLOSE):
                                            d_close=self.iClose(symbol,period,ind)
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                            asset +=((d_close-d_open)/d_open)
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")技术平仓**")
                                            print(strategy) 

                                        return
                                ##end superma
                                
                                ##common close
                                xCount=self.getRecentInd(symbol,15,time,period*ind//15)
                                ind2=period*ind//15
                                if type=="BUY":
                                    d_close=self.iClose(symbol,period,ind)
                                    # if (((d_close-d_open)/d_open)<=miniWin) and (d_open<d_close):
                                        # return

                                    if self.iHigh(symbol,15,self.getHighInd(symbol,xCount,ind2,15))>d_open*(1+0.02):
                                        if (self.iHigh(symbol,15,self.getHighInd(symbol,xCount,ind2,15))-self.iClose(symbol,15,ind2))/(self.iHigh(symbol,15,self.getHighInd(symbol,xCount,ind2,15))-d_open)>=0.3:
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                            asset +=((d_close-d_open)/d_open)
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")止盈++")
                                            print(strategy)   
                                        else:
                                            return
                                
                                    if (((d_close-d_open)/d_open)>=closeRate*1.5):
                                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                        orders[time]=strategy
                                        dict_order[symbol]=orders
                                        dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                        dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                        asset +=((d_close-d_open)/d_open)
                                        dict_plot[symbol][period].loc[tempT,'asset']=asset
                                        closed=True
                                        print("标的:("+symbol+")止盈++")
                                        print(strategy)   

                                    zCnt=3
                                    if period<60:
                                        zCnt=5                            
                                    if period>60:
                                        zCnt=2 
                            
                                    if (not closed) and (d_close>(d_open+self.iAtr(symbol,60,14,period*ind//60)*5)) and (((d_close-d_open)/d_open)>=miniWin):
                                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                        orders[time]=strategy
                                        dict_order[symbol]=orders
                                        dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                        dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                        asset +=((d_close-d_open)/d_open)
                                        dict_plot[symbol][period].loc[tempT,'asset']=asset
                                        closed=True
                                        print("标的:("+symbol+")止盈++")
                                        print(strategy)   
                                        
                                    if d_close<=d_open*(1-closeRate):
                                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                        orders[time]=strategy
                                        dict_order[symbol]=orders
                                        dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                        dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                        asset +=(d_close-d_open)/d_open
                                        dict_plot[symbol][period].loc[tempT,'asset']=asset
                                        closed=True
                                        print("标的:("+symbol+")止损--")
                                        print(strategy) 

                                if type=="SELL":
                                    d_close=self.iClose(symbol,period,ind)                                    

                                    # if (((d_open-d_close)/d_open)<=miniWin) and (d_open>d_close):
                                        # return

                                    if self.iLow(symbol,15,self.getLowInd(symbol,xCount,ind2,15))<d_open*(1-0.02):
                                        if (self.iClose(symbol,15,ind2)-self.iLow(symbol,15,self.getLowInd(symbol,xCount,ind2,15)))/(d_open-self.iLow(symbol,15,self.getLowInd(symbol,xCount,ind2,15)))>=0.3:
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                            asset +=(d_open-d_close)/d_open
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")止盈++")
                                            print(strategy)  
                                        else:
                                            return
                                
                                    if (((d_open-d_close)/d_open)>=closeRate*1.5):
                                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                        orders[time]=strategy
                                        dict_order[symbol]=orders
                                        dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                        dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                        asset +=(d_open-d_close)/d_open
                                        dict_plot[symbol][period].loc[tempT,'asset']=asset
                                        closed=True
                                        print("标的:("+symbol+")止盈++")
                                        print(strategy)  

                                    zCnt=3
                                    if period<60:
                                        zCnt=5                            
                                    if period>60:
                                        zCnt=2 
                                        
                                    if (not closed) and (d_close<(d_open-self.iAtr(symbol,60,14,period*ind//60)*5)) and (((d_open-d_close)/d_open)>=miniWin):
                                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                        orders[time]=strategy
                                        dict_order[symbol]=orders
                                        dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                        dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                        asset +=(d_open-d_close)/d_open
                                        dict_plot[symbol][period].loc[tempT,'asset']=asset
                                        closed=True
                                        print("标的:("+symbol+")止盈++")
                                        print(strategy) 
                                        
                                    if d_close>=d_open*(1+closeRate):
                                        strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                        orders[time]=strategy
                                        dict_order[symbol]=orders
                                        dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                        dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                        asset +=(d_open-d_close)/d_open
                                        dict_plot[symbol][period].loc[tempT,'asset']=asset
                                        closed=True
                                        print("标的:("+symbol+")止损--")
                                        print(strategy)   
                                
                                ##normal close    
                                if (not closed):
                                    if type=="BUY":
                                        for x in [y for y in arr_PeriodI if (y>=240 and y<1440)]:
                                            xInd=period*ind//x
                                            if (not closed) and (self.iStochastic(symbol,x,14,3,"SMA","MAIN",xInd)>=80) and (self.iStochastic(symbol,x,14,3,"SMA","MAIN",xInd)<self.iStochastic(symbol,x,14,3,"SMA","SIGNAL",xInd)):
                                                d_close=self.iClose(symbol,period,ind)
                                                strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                orders[time]=strategy
                                                dict_order[symbol]=orders
                                                dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                asset +=(d_close-d_open)/d_open
                                                dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                closed=True
                                                print("标的:("+symbol+")技术平仓**")
                                                print(strategy)                                                                                                                       
                                            
                                            if (not closed) and (self.iMacdDownInd(symbol,x,xInd)>0) and (self.iMacdDownInd(symbol,x,xInd)<xInd+12):
                                                if  iPreMacdCount>=iPreFixedMacdCount:
                                                    d_close=self.iClose(symbol,period,ind)
                                                    strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                    orders[time]=strategy
                                                    dict_order[symbol]=orders
                                                    dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                    dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                    asset +=(d_close-d_open)/d_open
                                                    dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                    closed=True
                                                    print("标的:("+symbol+")技术平仓**")
                                                    print(strategy) 

                                            # if (not closed) and (self.isBandGoDown(symbol,x,xInd)):
                                                # d_close=self.iClose(symbol,period,ind)
                                                # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                # orders[time]=strategy
                                                # dict_order[symbol]=orders
                                                # dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                # dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                # asset +=(d_close-d_open)/d_open
                                                # dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                # closed=True
                                                # print("标的:("+symbol+")技术平仓**")
                                                # print(strategy)

                                            if (not closed) and (self.isTouchedTopBand(symbol,x,xInd)):
                                                d_close=self.iClose(symbol,period,ind)
                                                strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                orders[time]=strategy
                                                dict_order[symbol]=orders
                                                dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                asset +=(d_close-d_open)/d_open
                                                dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                closed=True
                                                print("标的:("+symbol+")技术平仓**")
                                                print(strategy)
                                                
                                        # for x in [y for y in arr_PeriodI if (y>=240 and y<1440)]:
                                            # xInd=period*ind//x                                                
                                            # if (not closed) and commonThread1.isCanDeal(symbol,x,"trend","SELL","trend",xInd,"标的:("+symbol+"),周期:("+str(x)+")分钟"+"趋势看空策略检查###############"):
                                                # if (not commonThread1.isCanDeal(symbol,x,"trend","BUY","trend",xInd,"标的:("+symbol+"),周期:("+str(x)+")分钟"+"趋势看空策略检查###############")):
                                                    # if self.getRefHighInd(symbol, iContinueCount, xInd, x,12)>self.getRefLowInd(symbol, iContinueCount, xInd, x,12):
                                                        # d_close=self.iClose(symbol,period,ind)
                                                        # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                        # orders[time]=strategy
                                                        # dict_order[symbol]=orders
                                                        # dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                        # dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                        # asset +=(d_close-d_open)/d_open
                                                        # dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                        # closed=True
                                                        # print("标的:("+symbol+")技术平仓**")
                                                        # print(strategy)                                                     

                                    if type=="SELL":
                                        for x in [y for y in arr_PeriodI if (y>=240 and y<1440)]:
                                            xInd=period*ind//x                                   

                                            if (not closed) and (self.iStochastic(symbol,x,14,3,"SMA","MAIN",xInd)<=20) and (self.iStochastic(symbol,x,14,3,"SMA","MAIN",xInd)>self.iStochastic(symbol,x,14,3,"SMA","SIGNAL",xInd)):
                                                d_close=self.iClose(symbol,period,ind)
                                                strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                orders[time]=strategy
                                                dict_order[symbol]=orders
                                                dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                asset +=(d_open-d_close)/d_open
                                                dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                closed=True
                                                print("标的:("+symbol+")技术平仓**")
                                                print(strategy)        
                                                
                                            if (not closed) and (self.iMacdUpInd(symbol,x,xInd)>0) and (self.iMacdUpInd(symbol,x,xInd)<xInd+12):
                                                if  iPreMacdCount>=iPreFixedMacdCount:
                                                    d_close=self.iClose(symbol,period,ind)
                                                    strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                    orders[time]=strategy
                                                    dict_order[symbol]=orders
                                                    dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                    dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                    asset +=(d_close-d_open)/d_open
                                                    dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                    closed=True
                                                    print("标的:("+symbol+")技术平仓**")
                                                    print(strategy) 
                                                
                                            # if (not closed) and (self.isBandGoUp(symbol,x,xInd)):
                                                # d_close=self.iClose(symbol,period,ind)
                                                # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                # orders[time]=strategy
                                                # dict_order[symbol]=orders
                                                # dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                # dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                # asset +=(d_close-d_open)/d_open
                                                # dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                # closed=True
                                                # print("标的:("+symbol+")技术平仓**")
                                                # print(strategy) 
                                                
                                            if (not closed) and (self.isTouchedBottomBand(symbol,x,xInd)):
                                                d_close=self.iClose(symbol,period,ind)
                                                strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                orders[time]=strategy
                                                dict_order[symbol]=orders
                                                dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                asset +=(d_close-d_open)/d_open
                                                dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                closed=True
                                                print("标的:("+symbol+")技术平仓**")
                                                print(strategy)
                                                    
                                        # for x in [y for y in arr_PeriodI if (y>=240 and y<1440)]:
                                            # xInd=period*ind//x                    
                                            # if (not closed) and commonThread1.isCanDeal(symbol,x,"trend","BUY","trend",xInd,"标的:("+symbol+"),周期:("+str(x)+")分钟"+"趋势看空策略检查###############"):
                                                # if (not commonThread1.isCanDeal(symbol,x,"trend","SELL","trend",xInd,"标的:("+symbol+"),周期:("+str(x)+")分钟"+"趋势看空策略检查###############")):
                                                    # if self.getRefHighInd(symbol, iContinueCount, xInd, x,12)<self.getRefLowInd(symbol, iContinueCount,xInd, x,12):
                                                        # d_close=self.iClose(symbol,period,ind)
                                                        # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":d_close,"win":d_win,"lose":d_lose}
                                                        # orders[time]=strategy
                                                        # dict_order[symbol]=orders
                                                        # dict_plot[symbol][period].loc[tempT,'signal']=0.0                                            
                                                        # dict_plot[symbol][period].loc[tempT,'signal_close']=d_close
                                                        # asset +=(d_close-d_open)/d_open
                                                        # dict_plot[symbol][period].loc[tempT,'asset']=asset
                                                        # closed=True
                                                        # print("标的:("+symbol+")技术平仓**")
                                                        # print(strategy) 
                                                        
                                            
                                if  (not closed) and (strategyV=="antima"):
                                    if type=="BUY":
                                        if self.iClose(symbol,period,ind)<d_lose:
                                            d_close=self.iClose(symbol,period,ind)
                                            # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                                            # orders[time]=strategy
                                            # dict_order[symbol]=orders
                                            # dict_plot[symbol][period].loc[tempT,'signal']=0.0
                                            # dict_plot[symbol][period].loc[tempT,'signal_close']=self.iClose(symbol,period,ind)
                                            # asset +=(self.iClose(symbol,period,ind)-d_open)/d_open
                                            # dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            # closed=True
                                            # print("标的:("+symbol+")止损--")
                                            # print(strategy) 

                                        if (self.get2LineUpId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount): 
                                            if (((d_close-d_open)/d_open)<=miniWin):
                                                return                                    
                                                
                                        if (not closed) and (self.get2LineUpId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount):
                                            d_close=self.iClose(symbol,period,ind)
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=self.iClose(symbol,period,ind)
                                            asset +=(self.iClose(symbol,period,ind)-d_open)/d_open
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")技术平仓**")
                                            print(strategy)    
                                            
                                    if type=="SELL":
                                        if self.iClose(symbol,period,ind)>d_lose:
                                            d_close=self.iClose(symbol,period,ind)
                                            # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                                            # orders[time]=strategy
                                            # dict_order[symbol]=orders
                                            # dict_plot[symbol][period].loc[tempT,'signal']=0.0
                                            # dict_plot[symbol][period].loc[tempT,'signal_close']=self.iClose(symbol,period,ind)
                                            # asset +=(d_open-self.iClose(symbol,period,ind))/d_open
                                            # dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            # closed=True
                                            # print("标的:("+symbol+")止损--")                                        
                                            # print(strategy)    
                                        
                                        if (not closed) and (self.get2LineDownId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount):
                                        #if self.iMA(symbol,period,5,ind,arr_MaMethod[0],PRICE_CLOSE)<=self.iMA(symbol,period,maClosePeriod,ind,arr_MaMethod[0],PRICE_CLOSE):
                                            if (((d_open-d_close)/d_open)<=miniWin):
                                                return 
                                                
                                            d_close=self.iClose(symbol,period,ind)
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=self.iClose(symbol,period,ind)
                                            asset +=(d_open-self.iClose(symbol,period,ind))/d_open
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")技术平仓**")
                                            print(strategy)                                                                            

                                if  (not closed) and (strategyV=="powerma"):
                                    if type=="BUY":
                                        if self.iClose(symbol,period,ind)<d_lose:
                                            d_close=self.iClose(symbol,period,ind)
                                            # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                                            # orders[time]=strategy
                                            # dict_order[symbol]=orders
                                            # dict_plot[symbol][period].loc[tempT,'signal']=0.0
                                            # dict_plot[symbol][period].loc[tempT,'signal_close']=self.iClose(symbol,period,ind)
                                            # asset +=(self.iClose(symbol,period,ind)-d_open)/d_open
                                            # dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            # closed=True
                                            # print("标的:("+symbol+")止损--")
                                            # print(strategy)                                                                          
                                                
                                        if (not closed) and (self.get2LineDownId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount):
                                            if (((d_close-d_open)/d_open)<=miniWin):
                                                return
                                                
                                            d_close=self.iClose(symbol,period,ind)
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=self.iClose(symbol,period,ind)
                                            asset +=(self.iClose(symbol,period,ind)-d_open)/d_open
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")技术平仓**")
                                            print(strategy)    
                                            
                                    if type=="SELL":
                                        if self.iClose(symbol,period,ind)>d_lose:
                                            d_close=self.iClose(symbol,period,ind)
                                            # strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                                            # orders[time]=strategy
                                            # dict_order[symbol]=orders
                                            # dict_plot[symbol][period].loc[tempT,'signal']=0.0
                                            # dict_plot[symbol][period].loc[tempT,'signal_close']=self.iClose(symbol,period,ind)
                                            # asset +=(d_open-self.iClose(symbol,period,ind))/d_open
                                            # dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            # closed=True
                                            # print("标的:("+symbol+")止损--")                                        
                                            # print(strategy)    
                                        
                                        if (not closed) and (self.get2LineUpId(symbol,period,5,10,ind, arr_MaMethod[0])>=ind+iMaQuitCount):
                                            if (((d_open-d_close)/d_open)<=miniWin):
                                                return 
                                                
                                            d_close=self.iClose(symbol,period,ind)
                                            strategy={"time":time,"k":ind,"period":period,"type":type,"strategy":strategyV,"open":d_open,"close":self.iClose(symbol,period,ind),"win":d_win,"lose":d_lose}
                                            orders[time]=strategy
                                            dict_order[symbol]=orders
                                            dict_plot[symbol][period].loc[tempT,'signal']=0.0
                                            dict_plot[symbol][period].loc[tempT,'signal_close']=self.iClose(symbol,period,ind)
                                            asset +=(d_open-self.iClose(symbol,period,ind))/d_open
                                            dict_plot[symbol][period].loc[tempT,'asset']=asset
                                            closed=True
                                            print("标的:("+symbol+")技术平仓**")
                                            print(strategy)
                                                                                                                     

    def calculate_sharpe_ratio(self,portfolio_returns, risk_free_rate):
        """
        计算夏普率        
        :param portfolio_returns: numpy.array，投资组合的回报率数组
        :param risk_free_rate: float，无风险利率
        :return: float，夏普率
        """
        
        # 计算投资组合的平均回报率
        mean_return = np.mean(portfolio_returns)
        
        # 计算投资组合回报率的标准差
        std_dev = np.std(portfolio_returns)
        
        # 计算夏普率
        sharpe_ratio = (mean_return - risk_free_rate) / std_dev
        
        return sharpe_ratio    

    def draw_asset(self,symbol,period):
        plot1=dict_plot.get(symbol,None)
        if plot1==None:
            return      
            
        plot_data=plot1.get(period,None)
        plot_data=plot_data.iloc[::-1]    
        x_axis_data = list(plot_data.index)
        y_axis_data = plot_data['asset'].to_numpy()
        x_data=[]
        y_data=[]
        
        for i in range(1,len(y_axis_data)):
            if not (y_axis_data[i]==None):
                y_data.append(y_axis_data[i]*100)
                x_data.append(x_axis_data[i])
                
        #plt.plot(x_axis_data, y_axis_data, 'b*--', alpha=0.5, linewidth=1, label='acc')#'bo-'表示蓝色实线，数据点实心原点标注
        plt.plot(x_data, y_data, 'rs--', alpha=0.5, linewidth=1, label='Asset')
        plt.legend()  #显示上面的label
        plt.xlabel('time') #x_label
        plt.ylabel('number')#y_label

        plt.show()
    
    def draw_plot(self,symbol,period):    
        plot1=dict_plot.get(symbol,None)
        if plot1==None:
            return      
            
        plot_data=plot1.get(period,None)
        plot_data=plot_data.iloc[::-1]
        my_color = mpf.make_marketcolors(up='g',
                                         down='r',
                                         edge='inherit',
                                         wick='inherit',
                                         volume='inherit')
                                         
        my_style = mpf.make_mpf_style(marketcolors=my_color,
                                          figcolor='(0.82, 0.83, 0.85)',
                                          gridcolor='(0.82, 0.83, 0.85)')                                          
        
        range=300
        start=int(dataYear*365*1440/period)+int((1440/period)*100)-range            
        candle = InterCandle(plot_data,my_style,symbol,start,range)
        candle.idx_start =start 
        candle.idx_range = range
        candle.refresh_plot(start, range)
    
    def report(self):
        #**********************#   
        #**********************#  
        
        print("###############交易分析###############")
        
        global strategyPatten        
        prouct_trd_dict={}
        total_trd_dict={}
        dict_profile={}

        for symbol in dict_order:
            trade_times=0
            win_times=0
            lose_times=0
            profile=0
            orders=dict_order.get(symbol,None)
            detail={}
            maxLose=0.0
            maxWin=0.0
            sharpe_arr={}  
            
            for time in orders: 
                strategy=orders.get(time,None)
                k=strategy.get("k",0)
                period=strategy.get("period",0)
                s_type=strategy.get("type","")
                s_strategy=strategy.get("strategy","")
                d_open=strategy.get("open",0)
                d_close=strategy.get("close",0)
                d_win=strategy.get("win",0)
                d_lose=strategy.get("lose",0)                
                tmpDate=(pd.to_datetime(time.strip(), format="ISO8601")).strftime("%Y-%m")  
                
                if d_close>0:
                    trade_times=trade_times+1
                    if s_type=="BUY":
                        tmp=d_close-d_open                        
                        if tmp>0:
                            win_times=win_times+1
                            if (d_close-d_open)/d_open>maxWin:
                                maxWin=(d_close-d_open)/d_open                             
                        else:
                            lose_times=lose_times+1
                            if (d_open-d_close)/d_open>maxLose:
                                maxLose=(d_open-d_close)/d_open
                                
                    if s_type=="SELL":
                        tmp=d_open-d_close
                        if tmp>0:
                            win_times=win_times+1                        
                            if (d_open-d_close)/d_open>maxWin:
                                maxWin=(d_open-d_close)/d_open                                                        
                        else:
                            lose_times=lose_times+1
                            if (d_close-d_open)/d_open>maxLose:
                                maxLose=(d_close-d_open)/d_open
                                
                    sharpevalue=sharpe_arr.get(tmpDate,0)+tmp/d_open
                    sharpe_arr[tmpDate]=sharpevalue
                    
                    profile=profile+tmp/d_open
                    x=k*period//1440
                    y=dict_profile.get(x,0)+tmp/d_open
                    dict_profile[x]=y
                        
            portfolio_returns =list(sharpe_arr.values())
            risk_free_rate = sharpeBase / 12
            sharpe_ratio = self.calculate_sharpe_ratio(portfolio_returns, risk_free_rate) 
            
            detail["交易天数:"]=int(dataYear*365)
            detail["交易次数:"]=trade_times        
            detail["止盈次数:"]=win_times
            detail["止损次数:"]=lose_times
            detail["夏普率:"]=sharpe_ratio
            detail["最大盈利(100%):"]=maxWin*100
            detail["最大回撤(100%):"]=maxLose*100
            detail["盈利点数(100%):"]=profile*100
            prouct_trd_dict[symbol]=detail    
            
            print("标的:("+symbol+")交易汇总:")
            print(detail)                                                                            
       
        trade_days=0    
        trade_times=0
        win_times=0
        lose_times=0
        profile=0
        traders=prouct_trd_dict.keys() 
        
        for obj in traders: 
            detail=prouct_trd_dict.get(obj,None)
            trade_days=detail["交易天数:"]
            trade_times=detail["交易次数:"]+trade_times
            win_times=detail["止盈次数:"]+win_times
            lose_times=detail["止损次数:"]+lose_times
            profile=detail["盈利点数(100%):"]+profile
        
        strategyPatten=strategyPatten.replace("supertrend","缠背驰策略")        
        strategyPatten=strategyPatten.replace("stochastic","随机策略")
        strategyPatten=strategyPatten.replace("trend","趋势策略")
        strategyPatten=strategyPatten.replace("rsi","混合策略")
        strategyPatten=strategyPatten.replace("antima","反向均线策略") 
        
        summary={}    
        summary["全部交易标的:"]=str(list(dict_order.keys()))
        summary["交易策略:"]=strategyPatten
        summary["交易天数:"]=int(dataYear*365)
        summary["交易次数:"]=trade_times        
        summary["止盈次数:"]=win_times
        summary["止损次数:"]=lose_times
        summary["盈利点数(100%):"]=profile  
        
        print("")
        print("全部交易汇总:")
        print(summary)

        arr_strategy=[]
        if strategyPatten=="all":
            for key in dict_Strategy:
                arr_strategy.append(key)
        else:
            arr_strategy.append(strategyPatten)
            
        for strategy in arr_strategy:
            arr_Deal_PeriodI=dict_Strategy[strategy]
            for period in arr_Deal_PeriodI:
                for symbol in arr_symbols:                    
                    self.draw_asset(symbol,period)
                    self.draw_plot(symbol,period) 
                
        os.system("pause")   

    def detecting(self,dect_type):
        global asset,dictClosePeriod1,dictClosePeriod2,iPeriodInd1,iPeriodInd2
        if (dect_type=="test"):
            print("###############策略检查开始###############")            
            print(strategyPatten)
        
        if  deal_eng.isClosed():
            return
            
        arr_strategy=[]
        if strategyPatten=="all":
            for key in dict_Strategy:
                arr_strategy.append(key)
        else:
            arr_strategy.append(strategyPatten)
            
        for strategy in arr_strategy:
            arr_Deal_PeriodI=dict_Strategy[strategy]
            for symbol in arr_symbols:
                for x in arr_Deal_PeriodI:
                    refKDataAmount=int(dataYear*365*1440/x)+int((1440/x)*100)
                    refStart=int((1440/x+10)*100)
                    #print(refKDataAmount)
                    ind =refStart
                    if (dect_type=="real"):
                        refKDataAmount=iRealDataCounts
                        ind =iRealDataCounts
                        
                    period=x
                    upMA=0
                    upChan=0
                    downMA=0
                    downChan=0                
                    asset=0.0                
                    while ind<=refKDataAmount:
                        k=refKDataAmount-ind                      
                        if dect_type=="real":
                            k=0

                        self.closeOrder(symbol,x,dect_type,"BUY","antima",k)                        
                        self.closeOrder(symbol,x,dect_type,"BUY","supertrend",k)
                        self.closeOrder(symbol,x,dect_type,"BUY","macd",k)     
                        self.closeOrder(symbol,x,dect_type,"BUY","stochastic",k)
                        self.closeOrder(symbol,x,dect_type,"BUY","rsi",k)
                        self.closeOrder(symbol,x,dect_type,"BUY","bollb",k)                        
                        self.closeOrder(symbol,x,dect_type,"BUY","snnok",k)
                        self.closeOrder(symbol,x,dect_type,"BUY","superma",k)                                       
                        self.closeOrder(symbol,x,dect_type,"BUY","trend",k)                                                       

                        self.closeOrder(symbol,x,dect_type,"SELL","antima",k)                     
                        self.closeOrder(symbol,x,dect_type,"SELL","supertrend",k) 
                        self.closeOrder(symbol,x,dect_type,"SELL","stochastic",k) 
                        self.closeOrder(symbol,x,dect_type,"SELL","rsi",k)
                        self.closeOrder(symbol,x,dect_type,"SELL","bollb",k)                        
                        self.closeOrder(symbol,x,dect_type,"SELL","snnok",k) 
                        self.closeOrder(symbol,x,dect_type,"SELL","superma",k)                     
                        self.closeOrder(symbol,x,dect_type,"SELL","macd",k)                
                        self.closeOrder(symbol,x,dect_type,"SELL","trend",k)                

                        ##buy 
                        commonThread1 = common_eng.commonThread()
                        if self.antiMaStrategy(symbol,strategy,period,k)>0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","antima",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","antima",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","antima",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看多策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"BUY","antima",k)
                                        
                        if self.supertrendStrategy(symbol,strategy,period,k)>0:                        
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","supertrend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","supertrend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","supertrend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"BUY","supertrend",k)              

                        if self.macdStrategy(symbol,strategy,period,k)>0:                        
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","macd",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","macd",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","macd",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"BUY","macd",k) 
 
                        if self.stochasticStrategy(symbol,strategy,period,k)>0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","stochastic",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","stochastic",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","stochastic",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看多策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"BUY","stochastic",k)
                                 
                        if self.rsiStrategy(symbol,strategy,period,k)>0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","rsi",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"超级均线看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","rsi",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","rsi",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"超级均线看多策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"BUY","rsi",k)

                        if self.bollbStrategy(symbol,strategy,period,k)>0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","bollb",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"超级均线看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","bollb",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","bollb",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"超级均线看多策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"BUY","bollb",k)
                                       
                        if self.snnStrategy(symbol,strategy,period,k)>0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","snnok",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","snnok",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","snnok",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看多策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"BUY","snnok",k)

                        if self.supermaStrategy(symbol,strategy,period,k)>0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","superma",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","superma",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","superma",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看多策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"BUY","superma",k)
                                        self.setDict(symbol,period,dictClosePeriod1,iPeriodInd1)
                                        self.setDict(symbol,period,dictClosePeriod2,iPeriodInd2)                                        
                                    
                        if self.trendStrategy(symbol,strategy,period,k)>0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"BUY","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看多策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","SELL","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","BUY","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看多策略检查###############"):
                                        iClosePeriod=iPeriodInd
                                        self.placeOrder(symbol,period,dect_type,"BUY","trend",k)

                        ##sell
                        if self.antiMaStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","antima",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","antima",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","antima",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","antima",k)
                                        
                        if self.supertrendStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","supertrend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"顶部缠绕背驰看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","supertrend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","supertrend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"顶部缠绕背驰看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","supertrend",k)

                        if self.macdStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","macd",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"顶部缠绕背驰看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","macd",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","macd",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"顶部缠绕背驰看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","macd",k)

                        if self.stochasticStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","stochastic",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","stochastic",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","stochastic",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","stochastic",k)
                                        
                        if self.rsiStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","rsi",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"超级均线看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","rsi",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","rsi",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"超级均线看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","rsi",k)

                        if self.bollbStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","bollb",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"超级均线看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","bollb",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","bollb",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"超级均线看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","bollb",k)
                                        
                        if self.snnStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","snnok",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","snnok",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","snnok",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","snnok",k)

                        if self.supermaStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","superma",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","superma",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","superma",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"反向均线看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","superma",k)
                                        self.setDict(symbol,period,dictClosePeriod1,iPeriodInd1)
                                        self.setDict(symbol,period,dictClosePeriod2,iPeriodInd2)
                                        
                        if self.trendStrategy(symbol,strategy,period,k)<0:
                            if commonThread1.isCanDeal(symbol,period,dect_type,"SELL","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看空策略检查###############"):
                                if not commonThread1.isCanDeal(symbol,period,"trend","BUY","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"底部缠绕背驰看多策略检查###############"):
                                    if True: #if commonThread1.isCanDeal("BTCUSDT",period,"extra","SELL","trend",k,"标的:("+symbol+"),周期:("+str(period)+")分钟"+"趋势看空策略检查###############"):
                                        self.placeOrder(symbol,period,dect_type,"SELL","trend",k)
                                                        
                        ind =ind+1
                        if dect_type=="real":
                            break
            
if __name__ == "__main__":        
    #********************************************#    
    #********************************************#  
    #********************************************#        
    print("###############交易线程开始###############")     
    if run_type=="test":    
        thread1 = traderThread(1, "gatheringdata")
        thread1.start()
        time.sleep(sleepTime*5)
        
    if run_type=="real":         
        thread2 = traderThread(2, "gatheringtick")
        thread2.start()
        time.sleep(sleepTime*5)    

    thread3 = traderThread(3, "ordering")
    thread3.start()    