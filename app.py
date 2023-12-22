from urllib import request
import streamlit as st
import time
import tempfile as tp
import os
import platform
import requests
import matplotlib.pyplot as plt
from matplotlib import ticker as mticker
from utils import OHLC_DataFrame

global all_chat_id, bot_token, bot_url
proxy = request.getproxies()
if proxy:
    proxy['https'] = proxy['http']
bot_token = ""
bot_url = 'https://api.telegram.org'

def prepare_ma_args(pair='BTCUSDT', type_='sma', time_frame='d1', *periods):
    def is_pair(v:str):
        if (v.isdigit()) or is_type(v) or is_tframe(v):
            return False
        return True

    def is_type(v):
        if v in ['sma', 'wma', 'vwma', 'ema', 'vwap']:
            return True
        return False

    def is_tframe(v):
        if v in ['m1','m3','m5','m15','m30','h1','h4', 'd1', 'd7','1m']:
            return True
        return False

    def argument(pair=pair, type_=type_, time_frame=time_frame, periods=periods):
        l = []
        for item in [pair,type_,time_frame]:
            if item.isdigit():
                l.append(int(item))
        if not is_pair(pair):
            if is_type(pair):
                type_ = pair
            elif is_tframe(pair):
                time_frame = pair
            pair = 'btcusdt'
        if not is_type(type_):
            if is_tframe(type_):
                time_frame = type_
            type_ = 'sma'
        if not is_tframe(time_frame):
            time_frame = 'd1'
        if len(l)==0 and len(periods)==0:
            l = [100]
        for item in periods:
            try:
                l.append(int(item))
            except:
                continue

        return (pair, type_, time_frame, l)

    return argument()

def open_chat_id():
    global all_chat_id, old_chat_id
    if os.path.isfile("all_chat_id.txt"):
        with open("all_chat_id.txt", 'r') as f:
            all_chat_id = f.read().split(' ')
            all_chat_id.remove('')
            old_chat_id = set(all_chat_id)
            all_chat_id = set(all_chat_id)
            print(all_chat_id)
    else:
        old_chat_id = set()
        all_chat_id = set()

def get_candle(pair,limit,period):
    global sub_command
    url = f"https://api.hitbtc.com/api/3/public/candles/{pair}"
    params = {'period':period, 'limit':limit}
    d = []
    msg = ''
    try:
        response = requests.get(url, proxies=proxy, params=params)
        data = response.json()
        if response.status_code == 200:
            if len(data)>0:
                d = data
                msg = "Data has been received Successfully"
            else:
                msg = 'Data is not received!'
        else:
            msg = f"Error code: {data['status']}\nMessage: {data['message']}"
            # print("Error code: ", data["status"])
            # print(data["message"])
    except:
        # print("\nConnection Error.\nReturn Empty List!")
        msg = 'Connection Error.\n Unable to communicate with HitBTC server!\
                \nMaybe you enter wrong pair or pair dose not exist.\
                \nExample of correct pairs: btcusdt \niotabtc \nltcbtc \ntrxeth...'
    return d, msg

def volume(pair = "DOGEUSDT", period='d1', limit=90):
    global t_receive
    d, msg = get_candle(pair,int(limit),period)
    v, v_quote = [], []
    if len(d)>0:
        m0 = f'Pair: {pair} | Exchange: HitBTC\n\n'
        for item in d:
            v.append(float(item['volume']))
            v_quote.append(float(item['volume_quote']))
        m_time = f'[Response Time: {int(time.time())-t_receive} sec]\n\n'
        m1 = f"Average Volume: {int(sum(v)/len(v))}\nAverage V_quote: {int(sum(v_quote)/len(v_quote))}"
        m2 = f"\n\nCurrent Volume: {item['volume'].split('.')[0]}\nCurrent V_quote: {item['volume_quote'].split('.')[0]}"
        msg = ''.join([m_time,m0,m1,m2])
    method = 'sendMessage'
    params = {
        'chat_id':current_received_message['chat']['id'],
        'text': msg,
    }
    send_message(method, params)

def price(pair = "DOGEUSDT", period='d1'):
    global t_receive
    d ,msg = get_candle(pair, 1, period)
    if len(d)>0:
        close = d[0]['close'].replace('.', '\.')
        price = (float(d[0]['open'])+float(d[0]['close'])+float(d[0]['min'])+float(d[0]['max']))/4
        price = str(price).replace('.', '\.')
        msg = f'Pair: {pair} \| Exchange: HitBTC\n\n'
        msg = f"{msg}OHLC4 price: {price}\nCurrent price: {close}\n"
    m_time = f'[Response Time: {int(time.time())-t_receive} sec]\n\n'
    msg = ''.join([m_time, msg])
    method = 'sendMessage'
    params = {
        'chat_id':current_received_message['chat']['id'],
        'text': msg,
        'parse_mode':'MarkdownV2'
    }
    print(msg)
    send_message(method, params)
    print("Message sent")

def is_withdraw_enabled(coin):
    url = f'https://api.hitbtc.com/api/3/public/currency/{coin}'
    with requests.Session() as s:
        resp = s.get(url, proxies=proxy)
        data = resp.json()
        # print(data['networks'])
        payout_enabled = data['networks'][0]['payout_enabled']
        return payout_enabled

def hitbtc_withdraw_enabled(coin='doge'):
    global t_receive
    print("Send request to hitbtc...")
    payout_enabled = is_withdraw_enabled(coin)
    print("Receive hitbtc response.")
    m_time = f'[Response Time: {int(time.time())-t_receive} sec]\n\n'
    msg = f"withdraw for [{coin.upper()}] is enable" if payout_enabled else f"withdraw for [{coin.upper()}] is not enable"
    msg = ''.join([f"{m_time}", msg])
    method = 'sendMessage'
    params = {
        'chat_id':current_received_message['chat']['id'],
        'text': msg,
    }
    print("Sending Message to Telegram")
    send_message(method, params)
    print("Message sent")

def start():
    user = current_received_message['from']['first_name'].replace('.','\.')
    m0 = f"Hi {user}\n"
    m1= 'I am a robot\. My name is HitBTC\_Alert\. Please use the following commands to communicate with me\.'
    m2 = ''
    for item in list_of_command:
        m2 = '\n'.join([m2,item])
    m3 = '\n\nYou can do more things\. 🤩\
        \nUse the following pattrens to get information about other coins and pairs in HitBTC exchange\
        \nExamples: \n/price,btcusdt,m1\n/is\_withdraw\_enabled,iota\n/volume,ethbtc,d7,90\
        \n/ma,btcusdt,wma,d1,55,89\n*ma* is the short of Moving Average\. sma, wma, vma and ema are supported\.'
    msg = ''.join([m0,m1,m2,m3])
    method = 'sendMessage'
    params = {
        'chat_id':current_received_message['chat']['id'],
        'text': msg,
        'parse_mode':'MarkdownV2'
    }
    send_message(method, params)

def send_message(method:str, params:dict, files=None):
    global bot_token, bot_url
    req = '/'.join([bot_url, bot_token, method])
    resp = requests.post(url=req, params=params, proxies=proxy, files=files)
    data = resp.json()
    chat_id = current_received_message['chat']['id']
    if data['ok']:
        print(f"Message has been send to {chat_id}")
    else:
        print('unable to send message', data)

def moving_average(pair='BTCUSDT', type_='sma', time_frame='d1', *periods):
    global t_receive
    args = prepare_ma_args(pair,type_,time_frame, *periods)
    d_msg = {
        'sma': f"Simple Moving Average\n\n*Pair*:\t{args[0].upper()}\n*Time Frame*:\t{args[2]}\n",
        'wma': f"Weighted Moving Average\n\n*Pair*:\t{args[0].upper()}\n*Time Frame*:\t{args[2]}\n",
        'vwma': f"Volume Weighted Moving Average\n\n*Pair*:\t{args[0].upper()}\n*Time Frame*:\t{args[2]}\n",
        'vwap': f"Volume Weighted Average Price\n\n*Pair*:\t{args[0].upper()}\n*Time Frame*:\t{args[2]}\n",
        'ema': f"Exponantial Moving Average\n\n*Pair*:\t{args[0].upper()}\n*Time Frame*:\t{args[2]}\n"
    }
    price_msg = ''
    #print(args[0], args[1], args[2], args[3])
    # periods = list(map(int, periods))
    f = tp.TemporaryFile('w+b')
    limit = max(args[3])*2 
    if limit>1000: limit = 1000
    d,msg = get_candle(args[0], limit, args[2])
    m_time = f'[Response Time: {int(time.time())-t_receive} sec]\n\n'
    if len(d)>0:
        close = d[0]['close'].split('.')
        close = ''.join([close[0],'\.',close[1][:6]])
        price_msg = ''.join([price_msg, f"Price: {close}\n"])
        # opens = list(map(lambda data:float(data['open']), d[::-1]))
        timestamp = list(map(lambda data:data['timestamp'], d[::-1]))
        fig,ax = plt.subplots(figsize=(13,6),frameon=False, dpi=100)
        df = OHLC_DataFrame(d[::-1])
        x = range(len(df.price))
        df.candlestick_ochl(ax)
        # p = ax.plot(x, df.price, label='price: OHLC')
        for period in args[3]:
            if len(d)<period:
                continue
            data = df.moving_average(args[1], period)
            mvp = str(data[-1]).split('.')
            mvp = ''.join([mvp[0],'\.',mvp[1][:5]])
            price_msg = ''.join([price_msg, f'{args[1]}{period}: {mvp}\n'])
            if len(data)==len(x[period-1:]):
                ax.plot(x[period-1:], data, label=f"{args[1].upper()}:{period}")
            else:
                x1 = []
                for i in range(period,len(df.price), period):
                    x1.append(x[i])
                if len(x1)<len(data):
                    x1.append(x[-1])
                print(len(x1), len(data))
                ax.plot(x1, data, label=f"{args[1].upper()}:{period}")
        ax.legend()
        # ax.set_xlim(0, len(df.price))
        x_lim = list(map(int,ax.get_xticks()))
        x_lim[-1] = x_lim[-1]-1
        date = []
        # print(x_lim)
        for i in x_lim:
            if i > len(timestamp)-1:
                break
            date.append(timestamp[i].split('T')[0][2:11])
        x_lim = x_lim[:len(date)]
        # print(date)
        # ax.xaxis.set_major_locator(mticker.MaxNLocator(3))
        ax.xaxis.set_major_locator(mticker.FixedLocator(x_lim))
        ax.set_xticklabels(date)
        plt.savefig(f)
        f.seek(0)
        # plt.delaxes(p[0])
        # plt.plot(range(100,10000))
        # plt.show()
        # m_time = f'[Response Time: {int(time.time())-t_receive} sec]\n\n'
        
        msg = ''.join([m_time,d_msg[args[1]], price_msg])
        photo = {'photo':f}
        params = {
            'chat_id':current_received_message['chat']['id'],
            'caption': msg,
            'parse_mode':'MarkdownV2'
        }
        
        method = 'sendPhoto'
        print("before sending moving average photo \n",msg)
        send_message(method,params,photo)
    else:
        method = 'sendMessage'
        params = {
            'chat_id':current_received_message['chat']['id'],
            'text': msg,
            'parse_mode':'MarkdownV2'
        }
        msg = ''.join([m_time, msg])
        print("before sending moving average\n",msg)
        send_message(method, params)
        print(d, msg)

def update_telegram_bot(offset:int=None, allowed_updates:list=None):
    global bot_token, bot_url
    if allowed_updates is None:
        allowed_updates = []
    method = 'getUpdates'
    params = {
        'offset':offset,
        'allowed_updates':allowed_updates
    }
    req = '/'.join([bot_url, bot_token, method])
    resp = requests.get(url=req,params=params, proxies=proxy)
    resp = resp.json()
    print(resp)
    return resp.get('result')

def is_command():
    global current_received_message
    has_entities = current_received_message.get('entities')
    if has_entities:
        return current_received_message['entities'][0]['type']=='bot_command'
    else:
        return False

def run_func():
    commands = current_received_message['text'].split(',')
    main_command = commands[0].replace(' ', '')
    sub_command = []
    if len(commands)>=2:
        for command in commands[1:]:
            sub_command.append(command.replace(' ', ''))

    #print(f"commands: {commands} and sub_command: {sub_command}")
    val = func_dict.get(main_command)
    if val:
        val(*sub_command)
        # message = f"*{current_received_message['from']['first_name']}*\n{func_msg[command](ans)}"
    else:
        msg = ''
        for item in func_dict:
            if '@' not in item:
                if 'start' not in item:
                    msg = '\n'.join([msg,item])
        
        msg = f"This command is not support.\nUse the following commands:\n{msg}"
        method = 'sendMessage'
        params = {
            'chat_id':current_received_message['chat']['id'],
            'text': msg,
        }
        send_message(method,params)
        print("massege sent")

func_dict = {
    '/start':start,
    '/start@HitBTCAlert_bot':start,
    '/is_withdraw_enabled':hitbtc_withdraw_enabled,
    '/is_withdraw_enabled@HitBTCAlert_bot':hitbtc_withdraw_enabled,
    '/is_withdraw_enable':hitbtc_withdraw_enabled,
    '/is_withdraw_enable@HitBTCAlert_bot':hitbtc_withdraw_enabled,
    '/ma':moving_average,
    '/ma@HitBTCAlert_bot':moving_average,
    '/price':price,
    '/price@HitBTCAlert_bot':price,
    '/volume':volume,
    '/volume@HitBTCAlert_bot':volume
}

list_of_command=['/start','/is\_withdraw\_enabled','/price','/volume', '/ma']

def save_chat_id():
    global all_chat_id, old_chat_id
    if all_chat_id != old_chat_id:
        with open('all_chat_id.txt', 'w') as f: 
            m = ''
            for item in all_chat_id:
                m = ' '.join([item, m])
            f.write(m)
            old_chat_id = set(all_chat_id)

def app(n, group_id):
    global current_received_message, all_chat_id, t_receive
    open_chat_id()
    os_info = platform.uname()
    msg = f'New shift started from: \n\nOS: {os_info[0]} \nUser: {os_info[1]}\n'
    # send_message(message=msg, chat_id=group_id)
    data = update_telegram_bot()
    i = 0
    te_idx = 0
    while True:
        try:
            if len(data) == 0:
                #print("No Data To Handle!")
                time.sleep(0.1)
                data = update_telegram_bot()
            else:
                print("Handling Data...")
                offset = data[-1]['update_id']
                for d in data:
                    current_received_message = d.get('message')
                    if current_received_message:
                        t_receive = current_received_message['date']
                        print("difference of sending time from telegram server and receiving time: ", int(time.time())-t_receive)
                        all_chat_id.add(str(current_received_message['chat']['id']))
                        # print("text of message: \t", current_received_message)
                        if is_command():
                            # command = current_received_message['text']
                            run_func()
                            #print("After Excecute of run_func function")
                # print("offset: ", offset)
                data = update_telegram_bot(offset+1)
            if is_withdraw_enabled('doge'):
                for chat_id in all_chat_id:
                    send_message(
                        message="withdraw for [Dogecoin] is enable", 
                        chat_id=int(chat_id)
                    )
            if i > n:
                break
            i += 1
        except TypeError as te:
            i += 1
            te_idx += 1
            print(f"This Error Occure {te_idx} times :\t", te)
            if te_idx>3:
                break
        except:
            print("problem with internet connection")
            print(data)
            save_chat_id()
            break
    msg = f'\nThe shift in the following machine is over: \n\nOS: {os_info[0]} \nUser: {os_info[1]}\n'
    # send_message(message=msg, chat_id=group_id)
    # print(all_chat_id, old_chat_id)
    save_chat_id()

if __name__ == "__main__":
    with st.form("telegram_bot form"):
        bot_token = st.text_input("Enter your bot Token", "XXX-XXXX")
        n = st.number_input("number of iteration", step=1)
        groub_id = st.number_input("default group id ", step=1)
        submit = st.form_submit_button()
        if submit:
            app(n=n, group_id=groub_id)
    # moving_average('iotausdt','vwma','m5','55','200')
