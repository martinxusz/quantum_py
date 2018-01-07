#轨道线策略

from jqlib.technical_analysis import *
#导入判空的python自带函数
import numpy as np

def initialize(context):
    enable_profile()
    set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))
    set_option('use_real_price', True)
    g.buy_stock_count = 4
    g.buy_price = {}
    g.maxprofit = {}
    
def handle_data(context, data):
    hour = context.current_dt.hour
    minute = context.current_dt.minute
    if hour == 9 and minute == 30:
        buy_stocks = select_stocks(context,data)
        if len(buy_stocks) > 0:
            adjust_position(context, buy_stocks, data)
            
#    if hour == 14 and minute == 45:
#        buy_stocks = select_stocks(context,data)
#        if len(buy_stocks) == 0:
#            stock_stop_loss(context, data)
        
def filter_paused_and_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused 
    and not current_data[stock].is_st and 'ST' not in current_data[stock].
    name and '*' not in current_data[stock].name and '退' not in current_data[stock].name]
    
def filter_gem_stock(context, stock_list):
    return [stock for stock in stock_list  if stock[0:3] != '300']

def filter_old_stock(context, stock_list):
    tmpList = []
    for stock in stock_list :
        days_public=(context.current_dt.date() - get_security_info(stock).start_date).days
        # 上市未超过1年
        if days_public < 365:
            tmpList.append(stock)
    return tmpList

def filter_expensive_stock(context, stock_list):
    tmpList = []
    for stock in stock_list :
        #print (stock, " day open price :", get_current_data()[stock].day_open)
        if get_current_data()[stock].day_open < 40:
            tmpList.append(stock)
    return tmpList

def filter_by_ENE_stock(context, stock_list):
    tmpList = []        
    if len(stock_list) > 0:
        #返回任意股前5天的数据 主要是取日期使用
        df = attribute_history(stock_list[0], 5, unit='1d')
        tmpList = filter_by_ENE_internal(stock_list, df)
    
    if len(tmpList) == 0:
        print 'result is empty, not stock satisfy the conditions, return empty array'
    
    return tmpList

def filter_by_ENE_internal(stock_list, date_dateframe):
    i = 0;
    #print 'stock size, before:', len(stock_list)
    while i < date_dateframe.index.size - 1 and len(stock_list) > 0:    
        #print 'start to get ENE ,i = ', i, ', date:' , date_dateframe.index[i]
        #up1, low1, ENE1 = ENE(stock_list, date_dateframe.index[i]   ,N=10, M1=11, M2=9)
        #up2, low2, ENE2 = ENE(stock_list, date_dateframe.index[i+1] ,N=10, M1=11, M2=9)
        #print 'end to get ENE ,i = ', i
        initial_size = len(stock_list)
        for stock in stock_list:
    #        print 'start to get ENE ,i = ', i, ', date:' , date_dateframe.index[i]
            up1, low1, ENE1 = ENE([stock], date_dateframe.index[i]   ,N=10, M1=11, M2=9)
            up2, low2, ENE2 = ENE([stock], date_dateframe.index[i+1] ,N=10, M1=11, M2=9)
            
            #如果为nan空值则无需继续判断（比如：新股连续涨停轨道线中值为nan)
            #if isnan(ENE1[stock]) or isnan(ENE2[stock]):
            #if ENE1[stock] == np.nanFalse or ENE2[stock] == np.nanFalse:
            if np.isnan(ENE1[stock]) or np.isnan(ENE2[stock]):
                stock_list.remove(stock)
                continue
            
            #todo:for debug only, need to comment out the line below:
            #log.info('stock:%s, date:%s, ENE1:%s, ENE2:%s',stock, date_dateframe.index[i], ENE1, ENE2)
#            print 'end to get ENE ,i = ', i
#            print 'ENE1[stock]:', ENE1[stock], ',ENE2[stock]:', ENE2[stock] , ', stock', stock
            if ENE1[stock] <= ENE2[stock]:            
#                print 'remove: ENE1[stock] <= ENE2[stock]:', stock
                stock_list.remove(stock)
                continue

            #获得该股票在 date_dateframe.index[i+1] 前一天的数据
            #dfprice = get_price(stock, count = 1, end_date=date_dateframe.index[i], frequency='daily', fields=['low', 'high']) 
            #dfprice2 = get_price(stock, start_date = date_dateframe.index[i+1], end_date=date_dateframe.index[i+1], frequency='daily', fields=['low', 'high'])
            dfprice = attribute_history(stock, 5, unit='1d')
            dfprice2 = attribute_history(stock, 4, unit='1d')

#            print 'dfprice["low"][0]:', dfprice['low'][0], 'low1[stock]:', low1[stock] , ', stock', stock
            if dfprice['low'][0] >= low1[stock] and i == 0:
#                print 'remove: dfprice["low"][0] >= low1[stock] ,i==0', stock
                stock_list.remove(stock)
                continue

#            print 'dfprice["high"][0]:', dfprice['high'][0], 'dfprice2["high"][0]:', dfprice2['high'][0], ', stock', stock
            if dfprice['high'][0] >= dfprice2['high'][0] and i < 2:
#                print 'remove: dfprice["high"][0] >= dfprice2["high"][0] and i < 2', stock
                stock_list.remove(stock)
                continue


            if dfprice['high'][0] >= dfprice2['high'][0] and i == 3:
#                print 'remove: dfprice["high"][0] >= dfprice2["high"][0] and i == 3', stock
                stock_list.remove(stock)
                continue

#            print 'dfprice["low"][0]:', dfprice['low'][0], 'dfprice2["low"][0]:', dfprice2['low'][0] , ', stock', stock
            if dfprice['low'][0] >= dfprice2['low'][0] and i < 3:
#                print 'remove: dfprice["low"][0] >= dfprice2["low"][0] and i < 3', stock
                stock_list.remove(stock)
                continue

            if i == 3 and dfprice2['high'][0] < ENE2[stock]:
                #print 'remove: dfprice2["high"][0] >= ENE2[stock][0] and i == 3', stock
                log.info('remove: dfprice2["high"][0] >= ENE2[stock][0] and i == 3, %s', stock)
                stock_list.remove(stock)
                continue

#        print 'stock size *** :', len(stock_list) 
        if initial_size == len(stock_list) : 
            i+=1
    #print '######################################stock size, after:', len(stock_list)
    return stock_list

'''
def filter_limit_stock(context, stock_list):
    tmpList = []
    last_prices = history(1, '1m', 'close', security_list=stock_list)
    curr_data = get_current_data()
    for stock in stock_list:
        # 未涨停，也未跌停
        if curr_data[stock].low_limit < last_prices[stock][-1] < curr_data[stock].high_limit:
            tmpList.append(stock)
    return tmpList
'''
def filter_limit_stock(context, data, stock_list):
    tmpList = []
    curr_data = get_current_data()
    for stock in stock_list:
        if data[stock].close == data[stock].high_limit:
            continue
        # 未涨停，也未跌停
        if curr_data[stock].low_limit < data[stock].close < curr_data[stock].high_limit:
            tmpList.append(stock)
    return tmpList

# 取涨停价
def get_high_limit(stock, n=1):
    a_high_limit = attribute_history(stock, count=n, unit='1d', fields='high_limit')['high_limit'][0]
    return a_high_limit
   
# 获取n个单位时间当时的close
def get_close_price(stock, n=1, unit='1d'):
    close_price = attribute_history(stock, count=n, unit=unit, fields=('close'))['close'][0]
    return close_price
    
# 前天涨停
def filter_anteayer_high_limit(stock_list):
    a_stock_list = []
    for stock in stock_list:
        anteayer_close = get_close_price(stock, n=2)
        anteayer_high_limit = get_high_limit(stock, n=2)
        anteayer_volume = attribute_history(stock, count=2, unit='1d', fields='volume')['volume'][-2]
        if anteayer_close != anteayer_high_limit and anteayer_volume > 0:
            a_stock_list.append(stock)
    return a_stock_list

# 昨日涨停股
def filter_preday_high_limit(stock_list):
    df_high_limit = history(count=1, unit='1d', field='high_limit', security_list=stock_list).T
    df_close = history(count=1, unit='1d', field='close', security_list=stock_list).T
    df_high_limit.columns = ['high_limit']
    df_close.columns = ['close']
    df_dict = {'high_limit':df_high_limit['high_limit'], 'close':df_close['close']}
    df_limitup = pd.DataFrame(df_dict)
    df_limitup = df_limitup[df_limitup['high_limit'] != df_limitup['close']]
    a_stock_list = df_limitup.index.tolist()
    return a_stock_list

def select_stocks(context,data):
    # 选取流通市值小于500亿的500只股票
    q = query(valuation.code, valuation.circulating_market_cap).order_by(
            valuation.circulating_market_cap.asc()).filter(
            valuation.circulating_market_cap <= 500).limit(999)
    df = get_fundamentals(q)
    stock_list = list(df['code'])
    
    # 过滤掉停牌的和ST的
    stock_list = filter_paused_and_st_stock(stock_list)
    # 过滤掉创业板
    stock_list = filter_gem_stock(context, stock_list)
    # 过滤掉上市超过1年的
    #stock_list = filter_old_stock(context, stock_list)
    # 过滤掉现在涨停或者跌停的
    # stock_list = filter_limit_stock(context, stock_list)
    stock_list = filter_limit_stock(context, data, stock_list)
    
    # 前天涨停
    stock_list = filter_anteayer_high_limit(stock_list)
    #昨日涨停股
    stock_list = filter_preday_high_limit(stock_list)

    # 过滤>=40块钱的
    #stock_list = filter_expensive_stock(context, stock_list)
    
    stock_list = filter_by_ENE_stock(context, stock_list)
    # 选取前N只股票放入“目标池”
    stock_list = stock_list[:g.buy_stock_count]  
    return stock_list
def stock_stop_loss(context, data):
    '''
    1.记录最高收益
    2.最高收益<5%，从最高收益下跌4个点，止损。
    3.最高收益5%-10%，从最高收益下跌4个点，止盈。
    4.最高收益10%-20%，从最高收益下跌8个点，止盈。
    5.最高收益>20%，从最高收益下跌10个点，止盈。
    '''
    #log.info(len(context.portfolio.positions.keys()))
    for stock in context.portfolio.positions.keys():
        cur_price = data[stock].close
        #成本价
        hold_price = context.portfolio.positions[stock].avg_cost
        #log.info(g.buy_price, g.maxprofit)
        win = (cur_price - hold_price) / hold_price * 100.0
        #log.info(stock, win)
        
        #收益超25%则出
        if win > 15.0 :
            sellway = 5
            #order_target_value(position.security, 0)
            order_target_value(stock, 0)
            #close_position(position)
            #g.stock_num -= 1
            #g.maxprofit[position.security] = -999
            g.maxprofit[stock] = -999
        if win < -5.0 :
            sellway = 6
            
            position_count = len(context.portfolio.positions)
            #value = context.portfolio.cash / (g.buy_stock_count - position_count)
            #value = context.portfolio.cash / 2
            #print ("value in stop loss" , value)
            print ("context.portfolio.positions[stock].amount", context.portfolio.positions[stock].amount)
            print ("buy", int(context.portfolio.positions[stock].amount * 2))
            order_target_value(stock, int(context.portfolio.positions[stock].amount * 2))
            g.buy_price[stock] = (g.buy_price[stock] + data[stock].close) / 2
            
def clean_positions(context, data):
    # 现持仓的股票，如果不在“目标池”中，且未涨停，就卖出
    if len(context.portfolio.positions)>0:
        last_prices = history(1, '1m', 'close', security_list=context.portfolio.positions.keys())
        for stock in context.portfolio.positions.keys():
                curr_data = get_current_data()
                if last_prices[stock][-1] < curr_data[stock].high_limit:
                    log.info('selling the stock %s', stock)
                    order_target_value(stock, 0)
                else:
                    log.info('not selling it %s, as it reaches high limit, very good!', stock)
                    
def adjust_position(context, buy_stocks, data):
    
#    # 现持仓的股票，如果不在“目标池”中，且未涨停，就卖出
#    if len(context.portfolio.positions)>0:
#        last_prices = history(1, '1m', 'close', security_list=context.portfolio.positions.keys())
#        for stock in context.portfolio.positions.keys():
#            if stock not in buy_stocks:
#                log.info('stock:%s *not* in buy_stocks',stock)
#                curr_data = get_current_data()
#                if last_prices[stock][-1] < curr_data[stock].high_limit:
#                    order_target_value(stock, 0)
#                else:
#                    log.info('not selling it %s', stock)
#            else:
#                log.info('stock:%s in buy_stocks',stock)

    #context.portfolio.returns
    # 依次买入“目标池”中的股票            
    for stock in buy_stocks:
        position_count = len(context.portfolio.positions)
        if g.buy_stock_count > position_count:
            print ("cash:", context.portfolio.cash, " ,remaining: ", (g.buy_stock_count - position_count))
            #value = context.portfolio.cash / (g.buy_stock_count - position_count)
            value = 100
            print ("value" , value)
            if context.portfolio.positions[stock].total_amount == 0:
                #order_target_value(stock, value)
                order(stock, int(100))
                g.buy_price[stock] = data[stock].close
    
    #止损止盈
    stock_stop_loss(context, data)