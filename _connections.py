#mongodb_creds = "mongodb://eric:Hensley86!@207.38.142.196:4646/ncaa_bb?authSource=marine_science"
import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()

while cur_path.split('/')[-1] != 'portfolio':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))    
sys.path.insert(1, os.path.join(cur_path, 'lib', 'python3.7', 'site-packages'))


from sshtunnel import SSHTunnelForwarder
import _config
import psycopg2
import robin_stocks as r
import requests
import robin_stocks.helper as helper
import robin_stocks.urls as urls


def tunnel_config(_port):
    ssh_tunnel_server = SSHTunnelForwarder(
        (_config.SSH_HOST, _config.SSH_PORT),
        ssh_username=_config.SSH_USER,
        ssh_password=_config.SSH_PASS,
        remote_bind_address=('127.0.0.1', _port)
    )
    return(ssh_tunnel_server)
    
class server_null_tunnel:
    
    def __init__(self, _port):
        self.local_bind_port = _port
        
    def start(self):
        ''
    def stop(self):
        ''
    

name_to_port = {'mongo': 27017,
                'psql': 5432}

class db_connection:
    
    def __init__(self, service, collection = 'portfolio'):
        self.service = service
        self.collection = collection
        self.port = name_to_port[service.lower()] 
        if _config.SERVER:
            self.tunnel = server_null_tunnel(self.port)
        else:        
            self.tunnel = tunnel_config(self.port)         
            self.tunnel.start()
        if self.service == 'psql':
            params = {
             'database': _config.DB_USER,
             'user': _config.DB_USER,
             'password': _config.DB_PW,
             'host': 'localhost',
             'port': self.tunnel.local_bind_port
             }
            self.engine = psycopg2.connect(**params)
            self.client = self.engine.cursor()   
    def disconnect(self):
        self.engine.close()
        self.tunnel.stop()
        
    def reset_db_con(self):
        if self.service == 'psql':
            params = {
             'database': _config.DB_USER,
             'user': _config.DB_USER,
             'password': _config.DB_PW,
             'host': 'localhost',
             'port': self.tunnel.local_bind_port
             }
            self.engine = psycopg2.connect(**params)
            self.client = self.engine.cursor()             


from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as soup
import re
import hmac, base64, struct, hashlib, time

def get_dev_token():
    req = Request("https://robinhood.com/login", headers={'User-Agent': 'Mozilla Chrome Safari'})
    webpage = urlopen(req).read()
    urlopen(req).close()
    
    page_soup = soup(webpage, "lxml")
    container = str(page_soup.findAll("script"))
    
    device_token = re.search('clientId: "(.+?)"', container).group(1)
    return(device_token)
    
    

def get_hotp_token(secret, intervals_no):
    key = base64.b32decode(secret, True)
    msg = struct.pack(">Q", intervals_no)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    h = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return h

def get_totp_token(secret):
    return get_hotp_token(secret, intervals_no=int(time.time())//30)


class rs:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,defalte",
        "Accept-Language": "en;q=1",
        "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        "X-Robinhood-API-Version": "1.0.0",
        "Connection": "keep-alive",
        "User-Agent": "Robinhood/823 (iphone; iOS 7.1.2, Scale/2.00)"
        }
        self.auth_code = get_totp_token(_config.rh_qr)
        self.rpw = _config.rhood_pw
        self.run = _config.rhood_user

    def login(self,expiresIn=86400,scope='internal'):
        payload = {
        'client_id': 'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS',
        'expires_in': expiresIn,
        'grant_type': 'password',
        'password': self.rpw ,
        'scope': 'internal',
        'username': self.run,
        'device_token': get_dev_token(),
#        "challenge_type": "sms",
        "mfa_code" : self.auth_code
        }
        try:
            res_login = self.session.post('https://api.robinhood.com/oauth2/token/', data=payload, timeout=15)
            res_login.raise_for_status()
            login_data = res_login.json()
            self.oauth_token = login_data['access_token']
            self.session.headers['Authorization'] = 'Bearer ' + self.oauth_token
            return login_data
        except requests.exceptions.HTTPError:
            raise

    def logout(self):
        self.session.headers['Authorization'] = None

    
    def request_get(self, url,dataType='regular',payload=None):
        """For a given url and payload, makes a get request and returns the data.
    
        :param url: The url to send a get request to.
        :type url: str
        :param dataType: Determines how far to drill down into the data. 'regular' returns the unfiltered data. \
        'results' will return data['results']. 'pagination' will return data['results'] and append it with any \
        data that is in data['next']. 'indexzero' will return data['results'][0].
        :type dataType: Optional[str]
        :param payload: Dictionary of parameters to pass to the url as url/?key1=value1&key2=value2.
        :type payload: Optional[dict]
        :returns: Returns the data from the get request.
    
        """
        try:
            res = self.session.get(url,params=payload)
            res.raise_for_status()
            data = res.json()
        except (requests.exceptions.HTTPError,AttributeError) as message:
            print(message)
            if (dataType == 'results' or dataType == 'pagination'):
                return [None]
            else:
                return None
    
        if (dataType == 'results'):
            try:
                data = data['results']
            except KeyError as message:
                print("{} is not a key in the dictionary".format(message))
                return [None]
        elif (dataType == 'pagination'):
            counter = 2
            nextData = data
            try:
                data = data['results']
            except KeyError as message:
                print("{} is not a key in the dictionary".format(message))
                return [None]
    
            if nextData['next']:
                print('Found Additional pages.')
            while nextData['next']:
                try:
                    res = self.session.get(nextData['next'])
                    res.raise_for_status()
                    nextData = res.json()
                except:
                    print('Additional pages exist but could not be loaded.')
                    return(data)
                print('Loading page '+str(counter)+' ...')
                counter += 1
                for item in nextData['results']:
                    data.append(item)
        elif (dataType == 'indexzero'):
            try:
                data = data['results'][0]
            except KeyError as message:
                print("{} is not a key in the dictionary".format(message))
                return None
            except IndexError as message:
                return None
    
        return data
         
#r.login(_config.rhood_user, _config.rhood_pw)
openfigi_key = 'f95b350b-d561-42ab-9453-485fce321404'
