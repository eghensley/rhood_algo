stocks = ['DROP TABLE IF EXISTS portfolio.stocks;',
           
           'CREATE TABLE portfolio.stocks \
            (rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            b_id varchar COLLATE pg_catalog."default" NOT NULL, \
            rh_sym varchar COLLATE pg_catalog."default" NOT NULL, \
            name varchar COLLATE pg_catalog."default" NOT NULL, \
            country varchar COLLATE pg_catalog."default" NOT NULL, \
            daytrade_ratio float NOT NULL, \
            listed timestamp NOT NULL, \
            CONSTRAINT stock_pkey PRIMARY KEY (rh_id), \
            CONSTRAINT b_id_uq UNIQUE (b_id), \
            CONSTRAINT rh_sym_uq UNIQUE (rh_sym)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.rh_symbol_idx;',
            'CREATE INDEX rh_symbol_idx \
            ON portfolio.stocks USING btree \
            (rh_sym COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',

            'DROP INDEX IF EXISTS portfolio.rh_id_idx;',
            'CREATE INDEX rh_id_idx \
            ON portfolio.stocks USING btree \
            (rh_id COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',

            'DROP INDEX IF EXISTS portfolio.b_id_idx;',
            'CREATE INDEX b_id_idx \
            ON portfolio.stocks USING btree \
            (b_id COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',
            ]

day_prices = ['DROP TABLE IF EXISTS portfolio.day_prices;',
           
           'CREATE TABLE portfolio.day_prices \
            (day_price_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            open_price float NOT NULL, \
            close_price float NOT NULL, \
            high_price float NOT NULL, \
            low_price float NOT NULL, \
            volume int NOT NULL, \
            CONSTRAINT day_price_pkey PRIMARY KEY (day_price_id), \
            CONSTRAINT day_price_day_price_uq UNIQUE (rh_id, date), \
            CONSTRAINT day_price_id_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.day_price_idx;',
            'CREATE INDEX day_price_idx \
            ON portfolio.day_prices USING btree \
            (day_price_id) \
            TABLESPACE pg_default;',
            ]

inday_prices = ['DROP TABLE IF EXISTS portfolio.inday_prices;',
           
           'CREATE TABLE portfolio.inday_prices \
            (inday_price_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            open_price float NOT NULL, \
            close_price float NOT NULL, \
            high_price float NOT NULL, \
            low_price float NOT NULL, \
            volume int NOT NULL, \
            CONSTRAINT inday_price_pkey PRIMARY KEY (inday_price_id), \
            CONSTRAINT inday_price_day_price_uq UNIQUE (rh_id, date), \
            CONSTRAINT inday_price_id_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.inday_price_idx;',
            'CREATE INDEX inday_price_idx \
            ON portfolio.inday_prices USING btree \
            (inday_price_id) \
            TABLESPACE pg_default;',
            ]

dividends = ['DROP TABLE IF EXISTS portfolio.dividends;',
           
           'CREATE TABLE portfolio.dividends \
            (div_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            ex_date timestamp NOT NULL, \
            payment_date timestamp NOT NULL, \
            record_date timestamp NOT NULL, \
            declared_date timestamp, \
            amount float NOT NULL, \
            CONSTRAINT div_pkey PRIMARY KEY (div_id), \
            CONSTRAINT div_uq UNIQUE (rh_id, ex_date), \
            CONSTRAINT div_id_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.div_idx;',
            'CREATE INDEX div_idx \
            ON portfolio.dividends USING btree \
            (div_id) \
            TABLESPACE pg_default;',
            ]

ind_perf = ['DROP TABLE IF EXISTS portfolio.ind_perf;',
           
           'CREATE TABLE portfolio.ind_perf \
            (ind_perf_id bigint NOT NULL, \
            date timestamp NOT NULL, \
            communication float NOT NULL, \
            discretionary float NOT NULL, \
            staples float NOT NULL, \
            energy float NOT NULL, \
            financial float NOT NULL, \
            health float NOT NULL, \
            industrial float NOT NULL, \
            it float NOT NULL, \
            material float NOT NULL, \
            realestate float NOT NULL, \
            utilities float NOT NULL, \
            CONSTRAINT ind_perf_uq UNIQUE (date), \
            CONSTRAINT ind_perf_pkey PRIMARY KEY (ind_perf_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ind_perf_idx;',
            'CREATE INDEX ind_perf_idx \
            ON portfolio.ind_perf USING btree \
            (ind_perf_id) \
            TABLESPACE pg_default;',
            ]
 

financials = ['DROP TABLE IF EXISTS portfolio.financials;',
           
           'CREATE TABLE portfolio.financials \
            (financials_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            report_date timestamp NOT NULL, \
            gross_profit bigint, \
            cost_revenue bigint, \
            operating_revenue bigint, \
            total_revenue bigint, \
            operating_income bigint, \
            net_income bigint, \
            r_d bigint, \
            operating_expense bigint, \
            current_assets bigint, \
            total_assets bigint, \
            total_liabilities bigint, \
            current_cash bigint, \
            current_debt bigint, \
            total_cash bigint, \
            total_debt bigint, \
            shareholder_equity bigint, \
            cash_change bigint, \
            cash_flow bigint, \
            operating_gl bigint, \
            CONSTRAINT financials_uq UNIQUE (report_date, rh_id), \
            CONSTRAINT financials_pkey PRIMARY KEY (financials_id), \
            CONSTRAINT financials_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.financials_idx;',
            'CREATE INDEX financials_idx \
            ON portfolio.financials USING btree \
            (financials_id) \
            TABLESPACE pg_default;',
            ]

#day_ma = ['DROP TABLE IF EXISTS portfolio.day_ma;',
#           
#           'CREATE TABLE portfolio.day_ma \
#            (day_ma_id bigint NOT NULL, \
#            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
#            date timestamp NOT NULL, \
#            period int NOT NULL, \
#            avg_price float NOT NULL, \
#            CONSTRAINT day_ma_uq UNIQUE (date, rh_id, period), \
#            CONSTRAINT day_ma_pkey PRIMARY KEY (day_ma_id), \
#            CONSTRAINT day_ma_fk FOREIGN KEY (rh_id) \
#            REFERENCES portfolio.stocks (rh_id)) \
#            WITH (OIDS = FALSE) \
#            TABLESPACE pg_default;'
#            
#            'DROP INDEX IF EXISTS portfolio.day_ma_idx;',
#            'CREATE INDEX day_ma_idx \
#            ON portfolio.day_ma USING btree \
#            (day_ma_id) \
#            TABLESPACE pg_default;',
#            ]


ma_day_10 = ['DROP TABLE IF EXISTS portfolio.ma_day_10;',
           
           'CREATE TABLE portfolio.ma_day_10 \
            (ma_day_10_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            period int NOT NULL, \
            avg_price float NOT NULL, \
            CONSTRAINT ma_day_10_uq UNIQUE (date, rh_id, period), \
            CONSTRAINT ma_day_10_pkey PRIMARY KEY (ma_day_10_id), \
            CONSTRAINT ma_day_10_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ma_day_10_idx;',
            'CREATE INDEX ma_day_10_idx \
            ON portfolio.ma_day_10 USING btree \
            (ma_day_10_id) \
            TABLESPACE pg_default;',
            ]

ma_day_20 = ['DROP TABLE IF EXISTS portfolio.ma_day_20;',
           
           'CREATE TABLE portfolio.ma_day_20 \
            (ma_day_20_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            period int NOT NULL, \
            avg_price float NOT NULL, \
            CONSTRAINT ma_day_20_uq UNIQUE (date, rh_id, period), \
            CONSTRAINT ma_day_20_pkey PRIMARY KEY (ma_day_20_id), \
            CONSTRAINT ma_day_20_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ma_day_20_idx;',
            'CREATE INDEX ma_day_20_idx \
            ON portfolio.ma_day_20 USING btree \
            (ma_day_20_id) \
            TABLESPACE pg_default;',
            ]

ma_day_50 = ['DROP TABLE IF EXISTS portfolio.ma_day_50;',
           
           'CREATE TABLE portfolio.ma_day_50 \
            (ma_day_50_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            period int NOT NULL, \
            avg_price float NOT NULL, \
            CONSTRAINT ma_day_50_uq UNIQUE (date, rh_id, period), \
            CONSTRAINT ma_day_50_pkey PRIMARY KEY (ma_day_50_id), \
            CONSTRAINT ma_day_50_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ma_day_50_idx;',
            'CREATE INDEX ma_day_50_idx \
            ON portfolio.ma_day_50 USING btree \
            (ma_day_50_id) \
            TABLESPACE pg_default;',
            ]

ma_day_100 = ['DROP TABLE IF EXISTS portfolio.ma_day_100;',
           
           'CREATE TABLE portfolio.ma_day_100 \
            (ma_day_100_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            period int NOT NULL, \
            avg_price float NOT NULL, \
            CONSTRAINT ma_day_100_uq UNIQUE (date, rh_id, period), \
            CONSTRAINT ma_day_100_pkey PRIMARY KEY (ma_day_100_id), \
            CONSTRAINT ma_day_100_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ma_day_100_idx;',
            'CREATE INDEX ma_day_100_idx \
            ON portfolio.ma_day_100 USING btree \
            (ma_day_100_id) \
            TABLESPACE pg_default;',
            ]

ma_day_200 = ['DROP TABLE IF EXISTS portfolio.ma_day_200;',
           
           'CREATE TABLE portfolio.ma_day_200 \
            (ma_day_200_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            period int NOT NULL, \
            avg_price float NOT NULL, \
            CONSTRAINT ma_day_200_uq UNIQUE (date, rh_id, period), \
            CONSTRAINT ma_day_200_pkey PRIMARY KEY (ma_day_200_id), \
            CONSTRAINT ma_day_200_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ma_day_200_idx;',
            'CREATE INDEX ma_day_200_idx \
            ON portfolio.ma_day_200 USING btree \
            (ma_day_200_id) \
            TABLESPACE pg_default;',
            ]

ema_day_12 = ['DROP TABLE IF EXISTS portfolio.ema_day_12;',
           
           'CREATE TABLE portfolio.ema_day_12 \
            (ema_day_12_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            period int NOT NULL, \
            avg_price float NOT NULL, \
            CONSTRAINT ema_day_12_uq UNIQUE (date, rh_id, period), \
            CONSTRAINT ema_day_12_pkey PRIMARY KEY (ema_day_12_id), \
            CONSTRAINT ema_day_12_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ema_day_12_idx;',
            'CREATE INDEX ema_day_12_idx \
            ON portfolio.ema_day_12 USING btree \
            (ema_day_12_id) \
            TABLESPACE pg_default;',
            ]

ema_day_26 = ['DROP TABLE IF EXISTS portfolio.ema_day_26;',
           
           'CREATE TABLE portfolio.ema_day_26 \
            (ema_day_26_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            period int NOT NULL, \
            avg_price float NOT NULL, \
            CONSTRAINT ema_day_26_uq UNIQUE (date, rh_id, period), \
            CONSTRAINT ema_day_26_pkey PRIMARY KEY (ema_day_26_id), \
            CONSTRAINT ema_day_26_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ema_day_26_idx;',
            'CREATE INDEX ema_day_26_idx \
            ON portfolio.ema_day_26 USING btree \
            (ema_day_26_id) \
            TABLESPACE pg_default;',
            ]

sto_osc_14 = ['DROP TABLE IF EXISTS portfolio.sto_osc_14;',
           
           'CREATE TABLE portfolio.sto_osc_14 \
            (sto_osc_14_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            k float NOT NULL, \
            CONSTRAINT sto_osc_14_uq UNIQUE (date, rh_id), \
            CONSTRAINT sto_osc_14_pkey PRIMARY KEY (sto_osc_14_id), \
            CONSTRAINT sto_osc_14_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.ema_day_26_idx;',
            'CREATE INDEX sto_osc_14_idx \
            ON portfolio.sto_osc_14 USING btree \
            (sto_osc_14_id) \
            TABLESPACE pg_default;',
            ]

cci_day_20 = ['DROP TABLE IF EXISTS portfolio.cci_day_20;',
           
           'CREATE TABLE portfolio.cci_day_20 \
            (cci_day_20_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            cci float NOT NULL, \
            CONSTRAINT cci_day_20_uq UNIQUE (date, rh_id), \
            CONSTRAINT cci_day_20_pkey PRIMARY KEY (cci_day_20_id), \
            CONSTRAINT cci_day_20_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.cci_day_20_idx;',
            'CREATE INDEX cci_day_20_idx \
            ON portfolio.cci_day_20 USING btree \
            (cci_day_20_id) \
            TABLESPACE pg_default;',
            ]


rsi_day_14 = ['DROP TABLE IF EXISTS portfolio.rsi_day_14;',
           
           'CREATE TABLE portfolio.rsi_day_14 \
            (rsi_day_14_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            rsi float NOT NULL, \
            CONSTRAINT rsi_day_14_uq UNIQUE (date, rh_id), \
            CONSTRAINT rsi_day_14_pkey PRIMARY KEY (rsi_day_14_id), \
            CONSTRAINT rsi_day_14_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.rsi_day_14_idx;',
            'CREATE INDEX rsi_day_14_idx \
            ON portfolio.rsi_day_14 USING btree \
            (rsi_day_14_id) \
            TABLESPACE pg_default;',
            ]

sd_day_20 = ['DROP TABLE IF EXISTS portfolio.sd_day_20;',
           
           'CREATE TABLE portfolio.sd_day_20 \
            (sd_day_20_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            sd float NOT NULL, \
            CONSTRAINT sd_day_20_uq UNIQUE (date, rh_id), \
            CONSTRAINT sd_day_20_pkey PRIMARY KEY (sd_day_20_id), \
            CONSTRAINT sd_day_20_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.sd_day_20_idx;',
            'CREATE INDEX sd_day_20_idx \
            ON portfolio.sd_day_20 USING btree \
            (sd_day_20_id) \
            TABLESPACE pg_default;',
            ]


adl_day = ['DROP TABLE IF EXISTS portfolio.adl_day;',
           
           'CREATE TABLE portfolio.adl_day \
            (adl_day_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            adl float NOT NULL, \
            CONSTRAINT adl_day_uq UNIQUE (date, rh_id), \
            CONSTRAINT adl_day_pkey PRIMARY KEY (adl_day_id), \
            CONSTRAINT adl_day_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.adl_day_idx;',
            'CREATE INDEX adl_day_idx \
            ON portfolio.adl_day USING btree \
            (adl_day_id) \
            TABLESPACE pg_default;',
            ]


day_chaikin = ['DROP TABLE IF EXISTS portfolio.day_chaikin;',
           
           'CREATE TABLE portfolio.day_chaikin \
            (day_chaikin_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            chaikin float NOT NULL, \
            CONSTRAINT day_chaikin_uq UNIQUE (date, rh_id), \
            CONSTRAINT day_chaikin_pkey PRIMARY KEY (day_chaikin_id), \
            CONSTRAINT day_chaikin_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.day_chaikin_idx;',
            'CREATE INDEX day_chaikin_idx \
            ON portfolio.day_chaikin USING btree \
            (day_chaikin_id) \
            TABLESPACE pg_default;',
            ]


obv_14_roc = ['DROP TABLE IF EXISTS portfolio.obv_14_roc;',
           
           'CREATE TABLE portfolio.obv_14_roc \
            (obv_14_roc_id bigint NOT NULL, \
            rh_id varchar COLLATE pg_catalog."default" NOT NULL, \
            date timestamp NOT NULL, \
            obv_roc float NOT NULL, \
            CONSTRAINT obv_14_roc_uq UNIQUE (date, rh_id), \
            CONSTRAINT obv_14_roc_pkey PRIMARY KEY (obv_14_roc_id), \
            CONSTRAINT obv_14_roc_fk FOREIGN KEY (rh_id) \
            REFERENCES portfolio.stocks (rh_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS portfolio.obv_14_roc_idx;',
            'CREATE INDEX obv_14_roc_idx \
            ON portfolio.obv_14_roc USING btree \
            (obv_14_roc_id) \
            TABLESPACE pg_default;',
            ]

create_tables = {}
create_tables['stocks'] = stocks
create_tables['day_prices'] = day_prices
create_tables['inday_prices'] = inday_prices
create_tables['dividends'] = dividends
create_tables['ind_perf'] = ind_perf
create_tables['financials'] = financials
#create_tables['day_ma'] = day_ma
create_tables['ma_day_10'] = ma_day_10
create_tables['ma_day_20'] = ma_day_20
create_tables['ma_day_50'] = ma_day_50
create_tables['ma_day_100'] = ma_day_100
create_tables['ma_day_200'] = ma_day_200
create_tables['ema_day_12'] = ema_day_12
create_tables['ema_day_26'] = ema_day_26
create_tables['sto_osc_14'] = sto_osc_14
create_tables['cci_day_20'] = cci_day_20
create_tables['rsi_day_14'] = rsi_day_14
create_tables['sd_day_20'] = sd_day_20
create_tables['adl_day'] = adl_day
create_tables['day_chaikin'] = day_chaikin
create_tables['obv_14_roc'] = obv_14_roc