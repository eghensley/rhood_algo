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

    
#for script in create_tables['obv_14_roc']:    
#    PSQL.client.execute(script)
#    PSQL.client.execute("commit;") 
    
def det_cur_sd(psql):
#    psql = PSQL
    script = "select max(sd_day_20_id) from portfolio.sd_day_20" 
    _cur = pg_query(psql.client, script)
    _nxt_ids = _cur.values[0][0] + 1

    script = "select rh_id, max(date) from portfolio.sd_day_20 group by rh_id"
    _cur_comp = pg_query(PSQL.client, script)
    _comp_cur = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)
    

"""
bollinger bands: middle band = 
    20 sma
    upper band = 20 sma + (20 std x 2)
    lower band = 20 sma - (20 std x 2)
"""

def sd(comp_idx, comp_name_conv):
#    comp_idx, comp_name_conv = COMP_IDX, COMP_NAME_CONV
    cur_date = pg_query(PSQL.client, "SELECT max(date) FROM portfolio.rsi_day_14;")[0].values[0]
    nxt_id, comp_cur = det_cur_sd(PSQL)
    total_stocks = len(comp_idx)
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
        
        comp_data['std'] = comp_data['close_price'].rolling(window = 20).std()
        for date, std in comp_data[['date', 'std']].values:
            if rh_id in comp_cur.keys() and date <= np.datetime64(comp_cur[rh_id]):
                continue
            if std != std:
                continue
            script = "INSERT INTO portfolio.sd_day_20(sd_day_20_id, rh_id, date, sd) VALUES (%i, '%s', '%s', %.3f);" % (nxt_id, rh_id, datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S'), std)
            pg_insert(PSQL.client, script)
            nxt_id += 1
            comp_cur[rh_id] = date
            
if __name__ == '__main__':
    PSQL = db_connection('psql')

    COMP_IDX = [i[0] for i in pg_query(PSQL.client, "SELECT rh_id FROM portfolio.stocks;").values]
    COMP_NAME_CONV = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks')
    COMP_NAME_CONV = {k:v for k,v in COMP_NAME_CONV.values}
    
    sd(COMP_IDX, COMP_NAME_CONV)
                    
                
                