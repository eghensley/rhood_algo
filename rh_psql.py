import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'portfolio':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))    
sys.path.insert(1, os.path.join(cur_path, 'lib', 'python3.7', 'site-packages'))


import requests
import pandas as pd
from _connections import db_connection, openfigi_key
from pg_tables import create_tables
from datetime import datetime, timedelta
import robin_stocks.helper as helper
import robin_stocks.urls as urls
import time as tm
from progress_bar import progress
import numpy as np

#PSQL = db_connection('psql')
#for script in create_tables['financials']:    
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;")
#for script in create_tables['ind_perf']:    
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;")
#for script in create_tables['dividends']:    
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;")
#for script in stocks:
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;")  
#for script in create_tables['stocks']:
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;")
#for script in create_tables['day_prices']:
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;")
#for script in create_tables['inday_prices']:    
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;")



    
def pg_create_table(cur, table_name):  
#    cur, table_name = _psql, 
    try:
        # Truncate the table first
        for script in create_tables[table_name]:
            cur.execute(script)
            cur.execute("commit;")
        print("Created {}".format(table_name))
        
    except Exception as e:
        print("Error: {}".format(str(e)))
        
        
def pg_query(cur, query):
    cur.execute(query)
    data = pd.DataFrame(cur.fetchall())
    return(data) 
    
    
def pg_insert(cur, script):
    try:
        cur.execute(script)
        cur.execute("commit;")
        
    except Exception as e:
        print("Error: {}".format(str(e)))
        raise(Exception)


def _det_current_stocks(_psql):
#    _psql = PSQL
#    try: 
    _data = pg_query(_psql.client, 'select rh_sym from portfolio.stocks')
    if len(_data) > 0:
        current_ = set(_data[0].values)
    else:
        current_ = set()
    return(current_)


def stock_loop(psql, stock_dict, _cur_stocks):
#    psql, stock_dict, _cur_stocks = PSQL, data_dict['results'], cur_stocks
    print('~~~ New Page ~~~')
    for entry in stock_dict:
        if not entry['tradeable'] or entry['tradability'] != 'tradable':
            print('Not tradable')
            continue
        
        if entry['type'] != 'stock':
            print('Not a stock')
            continue
        
        if entry['symbol'] in _cur_stocks:
            print('Already included')
            continue
        
        rh_sym = entry['symbol']
        b_id = entry['bloomberg_unique']
        rh_id = entry['id']
        name = entry['name'].replace("'", '')
        country = entry['country']    
        daytrade_ratio = float(entry['day_trade_ratio'])
        listed = datetime.strptime(entry['list_date'], '%Y-%m-%d')
        print(rh_sym)
        
        script = "INSERT INTO portfolio.stocks(rh_id, b_id, rh_sym, name, country, daytrade_ratio, listed) VALUES ('%s', '%s', '%s', '%s', '%s', %.3f, '%s');" % (rh_id, b_id, rh_sym, name, country, daytrade_ratio, listed) 
        pg_insert(psql.client, script)
        _cur_stocks.add(entry['symbol'])
        
        rh_sym = None
        b_id = None
        rh_id = None
        name = None
        country = None
        daytrade_ratio = None
        listed = None
        
    return(_cur_stocks)


def add_stock_ids():
    PSQL = db_connection('psql')
    cur_stocks = _det_current_stocks(PSQL)
    url = 'https://api.robinhood.com/instruments/'
    data_dict = requests.get(url).json()
    cur_stocks = stock_loop(PSQL, data_dict['results'], cur_stocks)
    while True:
        url = data_dict['next']
        data_dict = requests.get(url).json()
        cur_stocks = stock_loop(PSQL, data_dict['results'], cur_stocks)
          
        if data_dict['next'] is None:
            break   


def det_cur_day_prices(psql, scope):
#    psql, scope = PSQL, 'day'
#    _data = pg_query(psql.client, 'select %s_price_id, rh_id, date from portfolio.%s_prices' % (scope, scope)) 
    _data = pg_query(psql.client, 'select rh_id, max(date) from portfolio.%s_prices group by rh_id' % (scope)) 
    _nxt = pg_query(psql.client, 'select max(%s_price_id) from portfolio.%s_prices' % (scope, scope))
    if len(_data) > 0:
        _data.rename(columns = {0: 'rh_idx', 1: 'dt'}, inplace = True)
        current_ = {i:j for i,j in pd.DataFrame(_data[['rh_idx', 'dt']].groupby('rh_idx').agg('dt').max()).reset_index().values}
        nxt = _nxt.values[0][0]+1
    else:
        current_ = {}
        nxt = 0
    return(current_, nxt)
    

def det_cur_divs(psql):
#    psql = PSQL
    _data = pg_query(psql.client, 'select rh_id, max(ex_date) from portfolio.dividends group by rh_id')
    _nxt = pg_query(psql.client, 'select max(div_id) from portfolio.dividends')
    if len(_data) > 0:
        _data.rename(columns = {0: 'rh_idx', 1: 'dt'}, inplace = True)
        current_ = {i:j for i,j in pd.DataFrame(_data[['rh_idx', 'dt']].groupby('rh_idx').agg('dt').max()).reset_index().values}
        nxt = _nxt.values[0][0]+1
    else:
        current_ = {}
        nxt = 0
    return(current_, nxt)


def det_cur_perf(psql):
#    psql = PSQL
    _data = pg_query(psql.client, 'select ind_perf_id, date from portfolio.ind_perf')
    if len(_data) > 0:
        _data.rename(columns = {0:'idx', 1: 'dt'}, inplace = True)
        current_ = _data['dt'].values[0]
        nxt = max(_data['idx'].values) + 1
    else:
        current_ = {}
        nxt = 0
    return(current_, nxt)


def det_cur_fin(psql):
#    psql = PSQL
    _data = pg_query(psql.client, 'select rh_id, max(report_date) from portfolio.financials group by rh_id')
    _nxt = pg_query(psql.client, 'select max(financials_id) from portfolio.financials')
    if len(_data) > 0:
        _data.rename(columns = {0: 'rh_idx', 1: 'dt'}, inplace = True)
        current_ = {i:j for i,j in pd.DataFrame(_data[['rh_idx', 'dt']].groupby('rh_idx').agg('dt').max()).reset_index().values}
        nxt = _nxt.values[0][0]+1
    else:
        current_ = {}
        nxt = 0
    return(current_, nxt)
    
    
def inday_prices():
    print(' ~~ Intra Day Prices ~~ ')

    PSQL = db_connection('psql')
    current, next_id = det_cur_day_prices(PSQL, 'inday')
    id_sym = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks')
    total_stocks = len(id_sym)
    for stock_num, (idx, sym) in enumerate(id_sym.values):
        progress(stock_num, total_stocks, status = sym)
        symbols = helper.inputs_to_set(sym)
        url = urls.historicals()
        payload = { 'symbols' : ','.join(symbols),
                    'interval' : '10minute',
                    'span' : 'week',
                    'bounds' : 'regular'}
        data = helper.request_get(url,'results',payload)
        if data == [None]:
            continue
        for day in data[0]['historicals']:  
            beg_date = datetime.strptime(day['begins_at'].replace('Z', '').replace('T', ' '), '%Y-%m-%d %H:%M:%S')
            if idx in current.keys() and beg_date <= current[idx]:
                continue
    
            open_price = float(day['open_price'])
            close_price = float(day['close_price'])
            high_price = float(day['high_price'])
            low_price = float(day['low_price'])
            volume = int(day['volume'])
            script = "INSERT INTO portfolio.inday_prices(inday_price_id, rh_id, date, open_price, close_price, high_price, low_price, volume) VALUES ('%s', '%s', '%s', %.2f, %.2f, %.2f, %.2f, %i);" % (next_id, idx, beg_date, open_price, close_price, high_price, low_price, volume)
            pg_insert(PSQL.client, script)
            next_id += 1  
            open_price = None
            close_price = None
            high_price = None
            low_price = None
            volume = None 
            
            
def day_prices():
    
    print(' ~~ Full Day Prices ~~ ')
    PSQL = db_connection('psql')
    current, next_id = det_cur_day_prices(PSQL, 'day')
    id_sym = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks')
    total_stocks = len(id_sym)
    for stock_num, (idx, sym) in enumerate(id_sym.values):
#        if idx == '1d4d0780-ba27-4adc-ab12-0c3062fdf365':
#            asdfasdf
        progress(stock_num, total_stocks, status = sym)
        symbols = helper.inputs_to_set(sym)
        url = urls.historicals()
        payload = { 'symbols' : ','.join(symbols),
                    'interval' : 'day',
                    'span' : '5year',
                    'bounds' : 'regular'}
        data = helper.request_get(url,'results',payload)
        
        if data == [None]:
            continue
        for day in data[0]['historicals']:
            beg_date = datetime.strptime(day['begins_at'].replace('Z', '').replace('T', ' '), '%Y-%m-%d %H:%M:%S')
            if idx in current.keys() and beg_date <= current[idx]:
                continue
    
            open_price = float(day['open_price'])
            close_price = float(day['close_price'])
            high_price = float(day['high_price'])
            low_price = float(day['low_price'])
            volume = int(day['volume'])
            script = "INSERT INTO portfolio.day_prices(day_price_id, rh_id, date, open_price, close_price, high_price, low_price, volume) VALUES ('%s', '%s', '%s', %.2f, %.2f, %.2f, %.2f, %i);" % (next_id, idx, beg_date, open_price, close_price, high_price, low_price, volume)
            pg_insert(PSQL.client, script)
            next_id += 1  
            open_price = None
            close_price = None
            high_price = None
            low_price = None
            volume = None


#Use the /ref-data/symbols endpoint to find the symbols that we support. 
#id_sym.loc[id_sym[0] == 'c850bc5d-676b-47d3-8f47-d0ce7676ccdf']
def dividends(full_update = False):
    print(' ~~ Dividends ~~ ')

    PSQL = db_connection('psql')
    id_sym = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks')          
    current, next_id = det_cur_divs(PSQL)
    total_stocks = len(id_sym)
    for stock_num, (idx, sym) in enumerate(id_sym.values):
        progress(stock_num, total_stocks, status = sym)

        if not full_update and idx in current.keys():
            continue
        url = 'https://api.iextrading.com/1.0/stock/%s/dividends/5y' % (sym)        
        req = requests.request('GET', url)
        if req.status_code == 404:
            continue
        data = req.json()
        if len(data) == 0:
            continue
        for div in reversed(data):
            ex_date = datetime.strptime(div['exDate'], '%Y-%m-%d')
            if idx in current.keys() and ex_date <= current[idx]:
                continue
            if div['amount'] == '':
                continue
            amount = float(div['amount'])
            if div['paymentDate'] == '':
                continue
            payment_date = datetime.strptime(div['paymentDate'], '%Y-%m-%d')
            record_date = datetime.strptime(div['recordDate'], '%Y-%m-%d')
            if div['declaredDate'] == '':
                declared_date = 'null'
            else:
                declared_date = "'"+str(datetime.strptime(div['declaredDate'], '%Y-%m-%d'))+"'"
            
            script = "INSERT INTO portfolio.dividends(\
                    div_id, rh_id, ex_date, payment_date, record_date, declared_date, amount) \
                    VALUES (%i, '%s', '%s', '%s', '%s', %s, %.2f);" % (next_id, idx, ex_date, payment_date, record_date, declared_date, amount)
            pg_insert(PSQL.client, script)
            next_id += 1
            current[idx] = ex_date
            ex_date = None
            payment_date = None
            record_date = None
            declared_date = None
            amount = None
            
 
def ind_perfs():    
    PSQL = db_connection('psql')  
    current, next_id = det_cur_perf(PSQL)
      
    url = 'https://www.alphavantage.co/query?function=SECTOR&apikey=%s' % openfigi_key
    req = requests.request('GET', url)
    #if req.status_code == 404:
    #    continue
    data = req.json()
    day_perf = data['Rank B: 1 Day Performance']
    date = datetime.strptime(data['Meta Data']['Last Refreshed'].replace(' ET', ''), '%H:%M %p %m/%d/%Y')
    if np.datetime64(date) != current:  
        communication = float(day_perf['Communication Services'].replace('%', ''))
        discretionary = float(day_perf['Consumer Discretionary'].replace('%', ''))
        staples = float(day_perf['Consumer Staples'].replace('%', ''))
        energy = float(day_perf['Energy'].replace('%', ''))
        financial = float(day_perf['Financials'].replace('%', ''))
        health = float(day_perf['Health Care'].replace('%', ''))
        industrial = float(day_perf['Industrials'].replace('%', ''))
        it = float(day_perf['Information Technology'].replace('%', ''))
        material = float(day_perf['Materials'].replace('%', ''))
        realestate = float(day_perf['Real Estate'].replace('%', ''))
        utilities = float(day_perf['Utilities'].replace('%', ''))
        
        script = "INSERT INTO portfolio.ind_perf(\
        	ind_perf_id, date, communication, discretionary, staples, energy, financial, health, industrial, it, material, realestate, utilities)\
        	VALUES (%i, '%s', %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f);" % (next_id, date, communication, discretionary, staples, energy, financial, health, industrial, it, material, realestate, utilities)
        pg_insert(PSQL.client, script)

 
def financials():
    PSQL = db_connection('psql')
    current, next_id = det_cur_fin(PSQL)
    id_sym = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks') 
    total_stocks = len(id_sym)
    for stock_num, (idx, sym) in enumerate(id_sym.values):
        progress(stock_num, total_stocks, status = sym)
        
        url = 'https://api.iextrading.com/1.0/stock/%s/financials' % (sym)        
        req = requests.request('GET', url)
        if req.status_code == 404:
            continue
        data = req.json()
        if len(data) == 0:
            continue
        
        for stock in reversed(data['financials']):
            
            report_date = datetime.strptime(stock['reportDate'], '%Y-%m-%d')
            
            if idx in current.keys() and current[idx] >= np.datetime64(report_date):
                continue
            
            if stock['grossProfit'] is None:
                gross_profit = 'null'
            else:
                gross_profit = int(stock['grossProfit'])
                
            if stock['costOfRevenue'] is None:
                cost_revenue = 'null'
            else:
                cost_revenue = int(stock['costOfRevenue'])
    
            if stock['operatingRevenue'] is None:
                operating_revenue = 'null'
            else:
                operating_revenue = int(stock['operatingRevenue'])
    
            if stock['totalRevenue'] is None:
                total_revenue = 'null'
            else:
                total_revenue = int(stock['totalRevenue'])
    
            if stock['operatingIncome'] is None:
                operating_income = 'null'
            else:
                operating_income = int(stock['operatingIncome'])
    
            if stock['netIncome'] is None:
                net_income = 'null'
            else:
                net_income = int(stock['netIncome'])
    
            if stock['researchAndDevelopment'] is None:
                r_d = 'null'
            else:
                r_d = int(stock['researchAndDevelopment'])
    
            if stock['operatingExpense'] is None:
                operating_expense = 'null'
            else:
                operating_expense = int(stock['operatingExpense'])
    
            if stock['currentAssets'] is None:
                current_assets = 'null'
            else:
                current_assets = int(stock['currentAssets'])
    
            if stock['totalAssets'] is None:
                total_assets = 'null'
            else:
                total_assets = int(stock['totalAssets'])
                
            if stock['totalLiabilities'] is None:
                total_liabilities = 'null'
            else:
                total_liabilities = int(stock['totalLiabilities'])
    
            if stock['currentCash'] is None:
                current_cash = 'null'
            else:
                current_cash = int(stock['currentCash'])
    
            if stock['currentDebt'] is None:
                current_debt = 'null'
            else:
                current_debt = int(stock['currentDebt'])
    
            if stock['totalCash'] is None:
                total_cash = 'null'
            else:
                total_cash = int(stock['totalCash'])
    
            if stock['totalDebt'] is None:
                total_debt = 'null'
            else:
                total_debt = int(stock['totalDebt'])
    
            if stock['shareholderEquity'] is None:
                shareholder_equity = 'null'
            else:
                shareholder_equity = int(stock['shareholderEquity'])
    
            if stock['cashChange'] is None:
                cash_change = 'null'
            else:
                cash_change = int(stock['cashChange'])
         
            if stock['cashFlow'] is None:
                cash_flow = 'null'
            else:
                cash_flow = int(stock['cashFlow'])
    
            if stock['operatingGainsLosses'] is None:
                operating_gl = 'null'
            else:
                operating_gl = int(stock['operatingGainsLosses'])
                
    
            script = "INSERT INTO portfolio.financials(\
                	financials_id, rh_id, report_date, gross_profit, cost_revenue, operating_revenue, total_revenue, operating_income, net_income, r_d, operating_expense, current_assets, total_assets, total_liabilities, current_cash, current_debt, total_cash, total_debt, shareholder_equity, cash_change, cash_flow, operating_gl)\
                	VALUES (%i, '%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);" % (next_id, idx, report_date, gross_profit, cost_revenue, operating_revenue, total_revenue, operating_income, net_income, r_d, operating_expense, current_assets, total_assets, total_liabilities, current_cash, current_debt, total_cash, total_debt, shareholder_equity, cash_change, cash_flow, operating_gl)
            pg_insert(PSQL.client, script)
            next_id += 1
            current[idx] = np.datetime64(report_date)
            
            report_date = None
            gross_profit = None
            cost_revenue = None
            operating_revenue = None
            total_revenue = None
            operating_income = None
            net_income = None
            r_d = None
            operating_expense = None
            current_assets = None
            total_assets = None
            total_liabilities = None
            current_cash = None
            current_debt = None
            total_cash = None
            total_debt = None
            shareholder_equity = None
            cash_change = None
            cash_flow = None
            operating_gl = None

          
def floor_dt(dt, delta):
    return dt + (datetime.min - dt) % delta


def update():
    next_update = floor_dt(datetime.now(), timedelta(minutes=10))
#    next_update = floor_dt(datetime.now(), timedelta(days=1))
    dt_until_update = next_update - datetime.now()
    seconds_before_update = dt_until_update.total_seconds()
    tm.sleep(seconds_before_update)
    print('BEGINNING UPDATE')
    if next_update.hour == 0 and next_update.minute == 0:
        day_prices()
        if next_update.day == 1 or next_update.day == 15:
            dividends(full_update = True)
        else:
            dividends()
        ind_perfs()
        financials()
    
    if next_update.hour >= 9 and next_update.hour <= 17:
        inday_prices()
    
if __name__ == '__main__':
#    while True:
#        update()
##    dividends()
        day_prices()
#        dividends()
        ind_perfs()
        financials()
        inday_prices()
