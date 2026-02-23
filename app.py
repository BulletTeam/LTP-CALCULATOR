import requests
import pandas as pd
from flask import Flask, render_template, request
import time

app = Flask(__name__)

# Protibar notun session toiri korar jonyo function
def get_nse_session():
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'accept-language': 'en-US,en;q=0.9',
        'accept-encoding': 'gzip, deflate, br'
    }
    session = requests.Session()
    # NSE Home page visit kore cookies collect kora mandatory
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    return session, headers

def get_option_chain(symbol):
    try:
        session, headers = get_nse_session()
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        
        # Data fetch korar agey 1-2 second wait kora bhalo jate block na hoy
        time.sleep(1) 
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    selected_index = request.form.get('index_name', 'NIFTY')
    data = get_option_chain(selected_index)
    
    if not data or 'filtered' not in data:
        return "NSE API Error! Render IP block hoyeche. 2-3 minute por abar Refresh koro."

    underlying_price = data['records']['underlyingValue']
    raw_data = data['filtered']['data']
    
    df = pd.DataFrame([
        {
            'strike': x['strikePrice'],
            'ce_oi': x['CE']['openInterest'] if 'CE' in x else 0,
            'ce_ltp': x['CE']['lastPrice'] if 'CE' in x else 0,
            'pe_oi': x['PE']['openInterest'] if 'PE' in x else 0,
            'pe_ltp': x['PE']['lastPrice'] if 'PE' in x else 0
        } for x in raw_data
    ])

    res_row = df.loc[df['ce_oi'].idxmax()]
    sup_row = df.loc[df['pe_oi'].idxmax()]

    info = {
        'symbol': selected_index,
        'price': underlying_price,
        'res': res_row['strike'],
        'eor': round(res_row['strike'] + res_row['ce_ltp'], 2),
        'sup': sup_row['strike'],
        'eos': round(sup_row['strike'] - sup_row['pe_ltp'], 2)
    }
    return render_template('index.html', info=info)

if __name__ == "__main__":
    app.run()
