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

#for period in [200, 100, 50, 20, 10]:
#    for script in create_tables['ma_day_%s' % (period)]:    
#        PSQL.client.execute(script)
#        PSQL.client.execute("commit;")
#for period in [12, 26]:
#    for script in create_tables['ema_day_%s' % (period)]:    
#        PSQL.client.execute(script)
#        PSQL.client.execute("commit;")   


def calc_mov_avg(comp_data, period):
#    comp_data, period = ibm, 10
    if period not in [200, 100, 50, 20, 10]:
        raise ValueError()
    ma = comp_data['close_price'].rolling(window=period).mean()
    return(ma)


def det_cur_ma(psql):
    _nxt_ids = {}
    _comp_cur = {}
    for period in [200, 100, 50, 20, 10]:
        script = "select max(ma_day_%s_id) from portfolio.ma_day_%s" % (period, period)
        _cur = pg_query(psql.client, script)
        _nxt_ids[period] = _cur.values[0][0] + 1
    
        script = "select rh_id, max(date) from portfolio.ma_day_%s group by rh_id" % (period)
        _cur_comp = pg_query(PSQL.client, script)
        _comp_cur[period] = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)


def det_cur_ema(psql):
#    psql = PSQL
    _nxt_ids = {}
    _comp_cur = {}
    for period in [12, 26]:
        script = "select max(ema_day_%s_id) from portfolio.ema_day_%s" % (period, period)
        _cur = pg_query(psql.client, script)
        _nxt_ids[period] = _cur.values[0][0] + 1
    
        script = "select rh_id, max(date) from portfolio.ema_day_%s group by rh_id" % (period)
        _cur_comp = pg_query(PSQL.client, script)
        _comp_cur[period] = {k:v for k,v in _cur_comp.values}
    return(_nxt_ids, _comp_cur)    


def moving_average(data, comp_idx, comp_name_conv):
    all_next_id, all_comp_cur = det_cur_ma(PSQL)
    total_stocks = len(comp_idx)
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        comp_data = data.loc[data['rh_id'] == rh_id]
        comp_data.sort_values('date', ascending = True)
        date_idx = comp_data['date']
        for period in [200, 100, 50, 20, 10]:
            dma = calc_mov_avg(comp_data, period)
            
            for date, avg_price in zip(date_idx.values, dma.values):
                if rh_id in all_comp_cur[period].keys() and date <= np.datetime64(all_comp_cur[period][rh_id]):
                    continue
                if avg_price != avg_price:
                    continue
                script = "INSERT INTO portfolio.ma_day_%s(ma_day_%s_id, rh_id, date, period, avg_price) VALUES (%i, '%s', '%s', %i, %.2f);" % (period, period, all_next_id[period], rh_id, datetime.strptime(str(date).split('.')[0], '%Y-%m-%dT%H:%M:%S'), period, avg_price)
                pg_insert(PSQL.client, script)
                all_next_id[period] += 1
                all_comp_cur[period][rh_id] = date


def exp_moving_average(data, comp_idx, comp_name_conv):
#    data, comp_idx, comp_name_conv = DATA, COMP_IDX, COMP_NAME_CONV
    
    all_next_id, all_comp_cur = det_cur_ema(PSQL)
    total_stocks = len(comp_idx)
    for stock_num, (rh_id) in enumerate(comp_idx):
        progress(stock_num, total_stocks, status = comp_name_conv[rh_id])
        comp_data = data.loc[data['rh_id'] == rh_id]
        comp_data.sort_values('date', ascending = True)
        for period in [12, 26]:
            weighting_mult = 2/(period+1)
            emas = []
            dates = []
            emas.append(comp_data.iloc[:period]['close_price'].mean())
            dates.append(comp_data.iloc[period]['date'])
            comp_data = comp_data.iloc[period+1:]
            for nxt_val, nxt_date in comp_data[['close_price', 'date']].values:
                emas.append((nxt_val - emas[-1]) * weighting_mult + emas[-1])
                dates.append(nxt_date)
                
            for date, avg_price in zip(dates, emas):
                if rh_id in all_comp_cur[period].keys() and date <= np.datetime64(all_comp_cur[period][rh_id]):
                    continue
                if avg_price != avg_price:
                    continue
                script = "INSERT INTO portfolio.ema_day_%s(ema_day_%s_id, rh_id, date, period, avg_price) VALUES (%i, '%s', '%s', %i, %.2f);" % (period, period, all_next_id[period], rh_id, datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S'), period, avg_price)
                pg_insert(PSQL.client, script)
                all_next_id[period] += 1
                all_comp_cur[period][rh_id] = date


if __name__ == '__main__':
    PSQL = db_connection('psql')
    DATA = pg_query(PSQL.client, "SELECT rh_id, date, close_price FROM portfolio.day_prices;")
    DATA.rename(columns = {0 :'rh_id', 1:'date', 2:'close_price'}, inplace = True)
    COMP_IDX = DATA['rh_id'].drop_duplicates().values
    COMP_NAME_CONV = pg_query(PSQL.client, 'select rh_id, rh_sym from portfolio.stocks')
    COMP_NAME_CONV = {k:v for k,v in COMP_NAME_CONV.values}

    moving_average(DATA, COMP_IDX, COMP_NAME_CONV)
    exp_moving_average(DATA, COMP_IDX, COMP_NAME_CONV)
