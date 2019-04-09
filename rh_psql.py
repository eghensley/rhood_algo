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
#    psql = PSQL
    _data = pg_query(psql.client, 'select %s_price_id, rh_id, date from portfolio.%s_prices' % (scope, scope)) 
    if len(_data) > 0:
        _data.rename(columns = {0:'idx', 1: 'rh_idx', 2: 'dt'}, inplace = True)
        current_ = {i:j for i,j in pd.DataFrame(_data[['rh_idx', 'dt']].groupby('rh_idx').agg('dt').max()).reset_index().values}
        nxt = max(_data['idx'].values) + 1
    else:
        current_ = {}
        nxt = 0
    return(current_, nxt)
    

def det_cur_divs(psql):
#    psql = PSQL
    _data = pg_query(psql.client, 'select div_id, rh_id, ex_date from portfolio.dividends')
    if len(_data) > 0:
        _data.rename(columns = {0:'idx', 1: 'rh_idx', 2: 'dt'}, inplace = True)
        current_ = {i:j for i,j in pd.DataFrame(_data[['rh_idx', 'dt']].groupby('rh_idx').agg('dt').max()).reset_index().values}
        nxt = max(_data['idx'].values) + 1
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
        progress(stock_num, total_stocks, status = sym)
        symbols = helper.inputs_to_set(sym)
        url = urls.historicals()
        payload = { 'symbols' : ','.join(symbols),
                    'interval' : 'day',
                    'span' : '5year',
                    'bounds' : 'regular'}
        data = helper.request_get(url,'results',payload)
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

           
def floor_dt(dt, delta):
    return dt + (datetime.min - dt) % delta


def update():
#    next_update = floor_dt(datetime.now(), timedelta(minutes=10))
    next_update = floor_dt(datetime.now(), timedelta(days=1))
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
        inday_prices()
        ind_perfs()
#    if next_update.hour >= 9 and next_update.hour <= 
    
    
if __name__ == '__main__':
    while True:
        update()
##    dividends()
    
    




