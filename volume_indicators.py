import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'portfolio':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))    
sys.path.insert(1, os.path.join(cur_path, 'lib', 'python3.7', 'site-packages'))


from _connections import db_connection
from datetime import datetime
from progress_bar import progress
import numpy as np
from rh_psql import pg_query, pg_insert
import pandas as pd

PSQL = db_connection('psql')
#for script in create_tables['sd_day_20']:    
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;") 
    
def det_cur_adl(psql):
#    psql = PSQL
    script = "select max(adl_day_id) from portfolio.adl_day" 
    _cur = pg_query(psql.client, script)
    _nxt_ids = _cur.values[0][0] + 1

    script = "select rh_id, max(date) from portfolio.adl_day group by rh_id"
    _cur_comp = pg_query(PSQL.client, script)
    _comp_cur = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)


def det_cur_chaikin(psql):
#    psql = PSQL
    script = "select max(day_chaikin_id) from portfolio.day_chaikin" 
    _cur = pg_query(psql.client, script)
    _nxt_ids = _cur.values[0][0] + 1

    script = "select rh_id, max(date) from portfolio.day_chaikin group by rh_id"
    _cur_comp = pg_query(PSQL.client, script)
    _comp_cur = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)
    
    
def det_cur_obv(psql):
#    psql = PSQL
    script = "select max(obv_14_roc_id) from portfolio.obv_14_roc" 
    _cur = pg_query(psql.client, script)
    _nxt_ids = _cur.values[0][0] + 1

    script = "select rh_id, max(date) from portfolio.obv_14_roc group by rh_id"
    _cur_comp = pg_query(PSQL.client, script)
    _comp_cur = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)
    
    
def adl(comp_idx, comp_name_conv):
#    comp_idx, comp_name_conv = COMP_IDX, COMP_NAME_CONV
    cur_date = pg_query(PSQL.client, "SELECT max(date) FROM portfolio.adl_day;")[0].values[0]
    nxt_id, comp_cur = det_cur_adl(PSQL)
    total_stocks = len(comp_idx)
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        if rh_id in comp_cur.keys() and cur_date <= np.datetime64(comp_cur[rh_id]):
            continue
        
        comp_data = pg_query(PSQL.client, "SELECT date, close_price, high_price, low_price, volume FROM portfolio.day_prices where rh_id = '%s';" % (rh_id))
        comp_data.rename(columns = {0:'date', 1:'close_price', 2: 'high_price', 3: 'low_price', 4:'volume'}, inplace = True)
        comp_data.sort_values('date', ascending = True, inplace = True)     
        
        comp_data['mfm'] = ((comp_data['close_price'] - comp_data['low_price']) - (comp_data['high_price'] - comp_data['low_price'])) / (comp_data['high_price'] - comp_data['low_price'])
        
        comp_data['mfv'] = comp_data['mfm'] * comp_data['volume']
        comp_data.dropna(inplace = True)
        
        adl = []
        for mfv in comp_data['mfv'].values:
            if len(adl) == 0:
                adl.append(mfv)
            else:
                adl.append(mfv + adl[-1])
        comp_data['adl'] = adl
        
        for date, adl in comp_data[['date', 'adl']].values:
            if rh_id in comp_cur.keys() and date <= np.datetime64(comp_cur[rh_id]):
                continue
            if adl != adl:
                continue
            if adl == np.inf or adl == -np.inf:
                continue
            script = "INSERT INTO portfolio.adl_day(adl_day_id, rh_id, date, adl) VALUES (%i, '%s', '%s', %.4f);" % (nxt_id, rh_id, datetime.strptime(str(date).split('.')[0], '%Y-%m-%d %H:%M:%S'), adl)
            pg_insert(PSQL.client, script)
            nxt_id += 1
            comp_cur[rh_id] = date
        

def calc_ema(x, per, col):
#    x, per, col = comp_data, 3, 'adl'
    weighting_mult = 2/(per+1)
    emas = []
    dates = []
    
    emas.append(x.iloc[:per][col].mean())
    dates.append(x.iloc[per]['date'])
    x = x.iloc[per+1:]
    for nxt_val, nxt_date in x[[col, 'date']].values:
        emas.append((nxt_val - emas[-1]) * weighting_mult + emas[-1])
        dates.append(nxt_date)
    
    output = pd.DataFrame([dates, emas]).T
    output.rename(columns = {0:'date', 1:'%s_%s_ema' % (col, per)}, inplace = True)
    return(output)
    

def chaikin(comp_idx, comp_name_conv):
#    comp_idx, comp_name_conv = COMP_IDX, COMP_NAME_CONV
    cur_date = pg_query(PSQL.client, "SELECT max(date) FROM portfolio.day_chaikin;")[0].values[0]
    nxt_id, comp_cur = det_cur_chaikin(PSQL)
    total_stocks = len(comp_idx)
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        if rh_id in comp_cur.keys() and cur_date <= np.datetime64(comp_cur[rh_id]):
            continue
        
        comp_data = pg_query(PSQL.client, "SELECT date, adl FROM portfolio.adl_day where rh_id = '%s';" % (rh_id))
        comp_data.rename(columns = {0:'date', 1:'adl'}, inplace = True)
        comp_data.sort_values('date', ascending = True, inplace = True)     
        
        if len(comp_data) < 11:
            continue
        adl_3_ema = calc_ema(comp_data, 3, 'adl')
        adl_10_ema = calc_ema(comp_data, 10, 'adl')
        
        adl_ema = pd.merge(adl_3_ema, adl_10_ema, left_on = 'date', right_on = 'date')

        adl_ema['chaikin'] = adl_ema['adl_3_ema'] - adl_ema['adl_10_ema'] 

        for date, chaikin in adl_ema[['date', 'chaikin']].values:
            if rh_id in comp_cur.keys() and date <= np.datetime64(comp_cur[rh_id]):
                continue
            if chaikin != chaikin:
                continue
            if chaikin == np.inf or chaikin == -np.inf:
                continue
            script = "INSERT INTO portfolio.day_chaikin(day_chaikin_id, rh_id, date, chaikin) VALUES (%i, '%s', '%s', %.4f);" % (nxt_id, rh_id, datetime.strptime(str(date).split('.')[0], '%Y-%m-%d %H:%M:%S'), chaikin)
            pg_insert(PSQL.client, script)
            nxt_id += 1
            comp_cur[rh_id] = date
            
            
def obv_roc(comp_idx, comp_name_conv):
#    comp_idx, comp_name_conv = COMP_IDX, COMP_NAME_CONV
    cur_date = pg_query(PSQL.client, "SELECT max(date) FROM portfolio.adl_day;")[0].values[0]
    nxt_id, comp_cur = det_cur_obv(PSQL)
    total_stocks = len(comp_idx)
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        if rh_id in comp_cur.keys() and cur_date <= np.datetime64(comp_cur[rh_id]):
            continue
        
        comp_data = pg_query(PSQL.client, "SELECT date, close_price, volume FROM portfolio.day_prices where rh_id = '%s';" % (rh_id))
        comp_data.rename(columns = {0:'date', 1:'close_price', 2:'volume'}, inplace = True)
        comp_data.sort_values('date', ascending = True, inplace = True)     
        
        last_close = comp_data.iloc[0]['close_price']
        obvs = [comp_data.iloc[0]['volume']]
        dates = [comp_data.iloc[0]['date']]
        for date, close, volume in comp_data.iloc[1:].values:
            if close > last_close:
                obvs.append(obvs[-1] + volume)
            elif close < last_close:
                obvs.append(obvs[-1] - volume)
            elif close == last_close:
                obvs.append(obvs[-1])
            dates.append(date)
            last_close = close
        obv = pd.DataFrame([dates, obvs]).T
        obv.rename(columns = {0: 'date', 1: 'obv'}, inplace = True)
        
        obv['ra'] = obv['obv'].rolling(window = 14).mean()

        obv['obv_roc'] = (obv['obv'] - obv['ra'].shift()) / obv['ra'].shift()
        obv.dropna(inplace = True)
        
        for date, obv in obv[['date', 'obv_roc']].values:
            if rh_id in comp_cur.keys() and date <= np.datetime64(comp_cur[rh_id]):
                continue
            if obv != obv:
                continue
            if obv == np.inf or obv == -np.inf:
                continue
            script = "INSERT INTO portfolio.obv_14_roc(obv_14_roc_id, rh_id, date, obv_roc) VALUES (%i, '%s', '%s', %.4f);" % (nxt_id, rh_id, datetime.strptime(str(date).split('.')[0], '%Y-%m-%d %H:%M:%S'), obv)
            pg_insert(PSQL.client, script)
            nxt_id += 1
            comp_cur[rh_id] = date        
            
if __name__ == '__main__':
        
    COMP_IDX = [i[0] for i in pg_query(PSQL.client, "SELECT rh_id FROM portfolio.stocks;").values]
    COMP_NAME_CONV = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks')
    COMP_NAME_CONV = {k:v for k,v in COMP_NAME_CONV.values}
#    adl(COMP_IDX, COMP_NAME_CONV)
#    chaikin(COMP_IDX, COMP_NAME_CONV)
    obv_roc(COMP_IDX, COMP_NAME_CONV)