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

#for script in create_tables['rsi_day_14']:    
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;") 


def det_cur_ma(psql):
#    psql = PSQL
    script = "select max(sto_osc_14_id) from portfolio.sto_osc_14" 
    _cur = pg_query(psql.client, script)
    _nxt_ids = _cur.values[0][0] + 1

    script = "select rh_id, max(date) from portfolio.sto_osc_14 group by rh_id"
    _cur_comp = pg_query(PSQL.client, script)
    _comp_cur = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)


def det_cur_cci(psql):
#    psql = PSQL
    script = "select max(cci_day_20_id) from portfolio.cci_day_20" 
    _cur = pg_query(psql.client, script)
    _nxt_ids = _cur.values[0][0] + 1

    script = "select rh_id, max(date) from portfolio.cci_day_20 group by rh_id"
    _cur_comp = pg_query(PSQL.client, script)
    _comp_cur = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)


def det_cur_rsi(psql):
#    psql = PSQL
    script = "select max(rsi_day_14_id) from portfolio.rsi_day_14" 
    _cur = pg_query(psql.client, script)
    _nxt_ids = _cur.values[0][0] + 1

    script = "select rh_id, max(date) from portfolio.rsi_day_14 group by rh_id"
    _cur_comp = pg_query(PSQL.client, script)
    _comp_cur = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)
    
    
def rsi(comp_idx, comp_name_conv):
#    comp_idx, comp_name_conv = COMP_IDX, COMP_NAME_CONV
    
#    nxt_id = 0
    nxt_id, comp_cur = det_cur_rsi(PSQL)
    total_stocks = len(comp_idx)
    cur_date = pg_query(PSQL.client, "SELECT max(date) FROM portfolio.rsi_day_14;")[0].values[0]
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        
        if rh_id in comp_cur.keys() and cur_date <= np.datetime64(comp_cur[rh_id]):
            continue
        
        comp_data = pg_query(PSQL.client, "SELECT date, close_price FROM portfolio.day_prices where rh_id = '%s';" % (rh_id))
        comp_data.rename(columns = {0:'date', 1:'close_price'}, inplace = True)
        comp_data.sort_values('date', ascending = True, inplace = True)       
        comp_data['diff'] = comp_data['close_price'].diff()
        comp_data['gains'] = comp_data['diff'].apply(lambda x: x if x > 0 else 0)
        comp_data['losses'] = comp_data['diff'].apply(lambda x: x if x < 0 else 0)
        comp_data.dropna(inplace = True)
        all_avg_gain = []
        all_avg_loss = []
        dates = []
        all_avg_gain.append(comp_data.iloc[:14]['gains'].mean())
        all_avg_loss.append(comp_data.iloc[:14]['losses'].mean())
        dates.append(comp_data.iloc[14]['date'])
        comp_data = comp_data.iloc[15:]
        for _date, cur_gain, cur_loss in comp_data[['date', 'gains', 'losses']].values:
            dates.append(_date)
            all_avg_gain.append((all_avg_gain[-1]*13 + cur_gain) / 14)
            all_avg_loss.append((all_avg_loss[-1]*13 + cur_loss) / 14)
            
        for date, gain, loss in zip(dates, all_avg_gain, all_avg_loss):
            if gain == 0:
                rsi = 0
            elif loss == 0:
                rsi = 100
            else:
                rsi = 100 - (100/1+(gain/loss))
                
            if rh_id in comp_cur.keys() and comp_cur[rh_id] >= date:
                continue

            script = "INSERT INTO portfolio.rsi_day_14(rsi_day_14_id, rh_id, date, rsi) VALUES (%i, '%s', '%s', %.3f);" % (nxt_id, rh_id, datetime.strptime(str(date).split('.')[0], '%Y-%m-%d %H:%M:%S'), rsi)
            pg_insert(PSQL.client, script)
            nxt_id += 1   
            comp_cur[rh_id] = date            

def cci(comp_idx, comp_name_conv):
#    comp_idx, comp_name_conv = COMP_IDX, COMP_NAME_CONV
    nxt_id, comp_cur = det_cur_cci(PSQL)
    total_stocks = len(comp_idx)
    cur_date = pg_query(PSQL.client, "SELECT max(date) FROM portfolio.cci_day_20;")[0].values[0]
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        
        if rh_id in comp_cur.keys() and cur_date <= np.datetime64(comp_cur[rh_id]):
            continue
        
        comp_ma = pg_query(PSQL.client, "SELECT date, avg_price from portfolio.ma_day_20 where rh_id = '%s'" % (rh_id))
        comp_ma.rename(columns = {0:'date', 1:'ma'}, inplace = True)
        comp_ma.sort_values('date', ascending = True, inplace = True)       
        comp_ma.set_index('date', inplace = True)
        comp_typ_price = pg_query(PSQL.client, "SELECT date, (high_price + low_price + close_price)/3 from portfolio.day_prices where rh_id = '%s'" % (rh_id))
        comp_typ_price.rename(columns = {0:'date', 1:'typical'}, inplace = True)
        comp_typ_price.sort_values('date', ascending = True, inplace = True)       
        comp_typ_price.set_index('date', inplace = True)
        comp_cci = comp_typ_price.join(comp_ma)
        comp_cci['typ_avg'] = comp_cci['typical'].rolling(window = 20).mean()
        comp_cci['abs_dev'] = abs(comp_cci['typical'] - comp_cci['typ_avg'])
        comp_cci['mean_dev'] = comp_cci['abs_dev'].rolling(window = 20).mean()
        comp_cci['cci'] = (comp_cci['typical'] - comp_cci['ma']) / (comp_cci['mean_dev'] * .015)
        comp_cci.dropna(inplace = True)
        comp_cci.reset_index(inplace = True)
        for date, cci in comp_cci[['date', 'cci']].values:
            if rh_id in comp_cur.keys() and comp_cur[rh_id] >= date:
                continue
            if cci != cci or cci == np.inf or cci == -np.inf:
                continue
            script = "INSERT INTO portfolio.cci_day_20(cci_day_20_id, rh_id, date, cci) VALUES (%i, '%s', '%s', %.3f);" % (nxt_id, rh_id, datetime.strptime(str(date).split('.')[0], '%Y-%m-%d %H:%M:%S'), cci)
            pg_insert(PSQL.client, script)
            nxt_id += 1   
            comp_cur[rh_id] = date
            
            
def stoch_osc_k(comp_idx, comp_name_conv):
#    comp_idx, comp_name_conv = COMP_IDX, COMP_NAME_CONV
#    all_next_id, all_comp_cur = det_cur_ema(PSQL)

    cur_date = pg_query(PSQL.client, "SELECT max(date) FROM portfolio.sto_osc_14;")[0].values[0]

    total_stocks = len(comp_idx)
    nxt_id, comp_cur = det_cur_ma(PSQL)
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        
        if rh_id in comp_cur.keys() and cur_date <= np.datetime64(comp_cur[rh_id]):
            continue
        
        
#        if rh_id in comp_cur.keys():
#            missing_days = pg_query(PSQL.client, "SELECT date, close_price FROM portfolio.day_prices where rh_id = '%s' and date > '%s';" % (rh_id, all_comp_cur[period][rh_id]))
#            if len(missing_days) == 0:
#                continue            
#        else:
        comp_data = pg_query(PSQL.client, "SELECT date, close_price FROM portfolio.day_prices where rh_id = '%s';" % (rh_id))
        comp_data.rename(columns = {0:'date', 1:'close_price'}, inplace = True)
        comp_data.sort_values('date', ascending = True, inplace = True)       
        
        per_high = comp_data['close_price'].rolling(window=14).max()
        per_low = comp_data['close_price'].rolling(window=14).min()
        
        for date, current_close, lowest_low, highest_high in zip(comp_data.date.values, comp_data.close_price.values, per_low, per_high.values):    
            if rh_id in comp_cur.keys() and comp_cur[rh_id] >= date:
                continue
            
            k = (current_close - lowest_low)/(highest_high - lowest_low) * 100
            if k != k:
                continue
            script = "INSERT INTO portfolio.sto_osc_14(sto_osc_14_id, rh_id, date, k) VALUES (%i, '%s', '%s', %.2f);" % (nxt_id, rh_id, datetime.strptime(str(date).split('.')[0], '%Y-%m-%dT%H:%M:%S'), k)
            pg_insert(PSQL.client, script)
            nxt_id += 1   
            comp_cur[rh_id] = date
            
        
        
if __name__ == '__main__':
    PSQL = db_connection('psql')
    
    COMP_IDX = [i[0] for i in pg_query(PSQL.client, "SELECT rh_id FROM portfolio.stocks;").values]
    COMP_NAME_CONV = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks')
    COMP_NAME_CONV = {k:v for k,v in COMP_NAME_CONV.values}
    
    cci(COMP_IDX, COMP_NAME_CONV)
    rsi(COMP_IDX, COMP_NAME_CONV)


        
        
        
        