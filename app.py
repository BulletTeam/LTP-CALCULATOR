import requests
import pandas as pd
from flask import Flask, render_template, request

app = Flask(__name__)

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9'
}

def get_option_chain(symbol):
    # Index-er jonno base URL alada hoy (Indices vs Equities)
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    response = session.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    # Default index NIFTY
    selected_index = request.form.get('index_name', 'NIFTY')
    
    try:
        data = get_option_chain(selected_index)
        if not data:
            return "NSE API Error! Please Refresh."

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

        # Calculation: Max OI based Support/Resistance
        res_row = df.loc[df['ce_oi'].idxmax()]
        sup_row = df.loc[df['pe_oi'].idxmax()]

        # Advanced Reversal Points (EOR/EOS)
        eor = res_row['strike'] + res_row['ce_ltp']
        eos = sup_row['strike'] - sup_row['pe_ltp']

        info = {
            'symbol': selected_index,
            'price': underlying_price,
            'res': res_row['strike'],
            'eor': round(eor, 2),
            'sup': sup_row['strike'],
            'eos': round(eos, 2)
        }
        return render_template('index.html', info=info)
    
    except Exception as e:
        return f"System Error: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)
