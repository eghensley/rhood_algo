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

#for script in create_tables['sto_osc_14']:    
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


def stoch_osc_k(data, comp_idx, comp_name_conv):
#    data, comp_idx, comp_name_conv = DATA, COMP_IDX, COMP_NAME_CONV
#    all_next_id, all_comp_cur = det_cur_ema(PSQL)
    total_stocks = len(comp_idx)
    nxt_id, comp_cur = det_cur_ma(PSQL)
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        comp_data = data.loc[data['rh_id'] == rh_id]
        comp_data.sort_values('date', ascending = True)
        
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
    DATA = pg_query(PSQL.client, "SELECT rh_id, date, close_price FROM portfolio.day_prices;")
    DATA.rename(columns = {0 :'rh_id', 1:'date', 2:'close_price'}, inplace = True)
    COMP_IDX = DATA['rh_id'].drop_duplicates().values
    COMP_NAME_CONV = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks')
    COMP_NAME_CONV = {k:v for k,v in COMP_NAME_CONV.values}
    stoch_osc_k(DATA, COMP_IDX, COMP_NAME_CONV)


        
        
        
        