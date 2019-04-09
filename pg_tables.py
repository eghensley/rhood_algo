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

    
create_tables = {}
create_tables['stocks'] = stocks
create_tables['day_prices'] = day_prices
create_tables['inday_prices'] = inday_prices
create_tables['dividends'] = dividends
