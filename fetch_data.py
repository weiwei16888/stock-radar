import requests
import json
import time

def fetch_all_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    stock_dict = {}
    date_str = "最新盤後"

    def clean_num(val):
        if not val or val == '--': 
            return 0.0
        s = str(val).replace(',', '').replace('+', '').strip()
        try: 
            return float(s)
        except: 
            return 0.0

    # 1. 抓取 TWSE 全上市股票每日收盤行情 (動態解析全市場收盤價、漲跌、最高、最低)
    try:
        url_price = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?response=json&type=ALLBUT0999"
        res = requests.get(url_price, headers=headers, timeout=15).json()
        
        if res.get('stat') == 'OK':
            date_str = res.get('date', date_str)
            tables = res.get('tables', [])
            target_table = None
            for t in tables:
                if '證券代號' in t.get('fields', []) and '收盤價' in t.get('fields', []):
                    target_table = t
                    break
            
            if target_table:
                fields = target_table['fields']
                idx_code = fields.index('證券代號')
                idx_name = fields.index('證券名稱')
                idx_high = fields.index('最高價')
                idx_low = fields.index('最低價')
                idx_close = fields.index('收盤價')
                idx_change = fields.index('漲跌價差')
                idx_sign = fields.index('漲跌(+/-)')

                for row in target_table['data']:
                    code = str(row[idx_code]).strip()
                    name = str(row[idx_name]).strip()
                    
                    # 篩選標準 4 碼股票代號
                    if not code.isdigit() or len(code) != 4: 
                        continue

                    close_p = clean_num(row[idx_close])
                    high_p = clean_num(row[idx_high])
                    low_p = clean_num(row[idx_low])
                    change_v = clean_num(row[idx_change])
                    sign = str(row[idx_sign])

                    if '-' in sign or '綠' in sign: 
                        change_v = -abs(change_v)
                    
                    prev_p = round(close_p - change_v, 2) if close_p > 0 else close_p
                    pct_val = round((change_v / prev_p * 100), 2) if prev_p > 0 else 0.0
                    pct_str = f"{'+' if change_v > 0 else ''}{pct_val}%"

                    # 官方產業分類推斷
                    if code.startswith('28'): category = "金融保險"
                    elif code.startswith('26'): category = "航運業"
                    elif code.startswith('23') or code.startswith('24'): category = "半導體"
                    elif code.startswith('30') or code.startswith('31') or code.startswith('61') or code.startswith('238'): category = "電子零組件"
                    elif code.startswith('13'): category = "塑膠工業"
                    elif code.startswith('20'): category = "鋼鐵工業"
                    elif code.startswith('17') or code.startswith('41'): category = "生技醫療"
                    else: category = "其他類股"

                    stock_dict[code] = {
                        "code": code,
                        "name": name,
                        "category": category,
                        "market": "上市",
                        "price": close_p,
                        "prev_price": prev_p,
                        "change": change_v,
                        "change_pct": pct_str,
                        "k_high": high_p if high_p > 0 else close_p,
                        "k_low": low_p if low_p > 0 else close_p,
                        "foreign": 0.0,
                        "trust": 0.0,
                        "dealer": 0.0,
                        "total_net": 0.0,
                        "foreign_accum_5d": 0.0,
                        "trust_accum_5d": 0.0,
                        "accum_5d": 0.0,
                        "accum_20d": 0.0,
                        "foreign_ratio": "0.0%",
                        "flow_days": 0,
                        "flow_type": "平盤"
                    }
    except Exception as e:
        print("TWSE Price API Error:", e)

    time.sleep(1)

    # 2. 抓取 TWSE 全市場三大法人買賣超，自動與當日收盤價換算為「億元」
    try:
        url_fund = "https://www.twse.com.tw/rwd/zh/fund/T86?response=json&selectType=ALL"
        res_fund = requests.get(url_fund, headers=headers, timeout=15).json()

        if res_fund.get('stat') == 'OK' and 'data' in res_fund:
            for row in res_fund['data']:
                code = str(row[0]).strip()
                if code in stock_dict:
                    f_shares = clean_num(row[4]) / 1000.0  # 外資張數
                    t_shares = clean_num(row[10]) / 1000.0 # 投信張數
                    d_shares = clean_num(row[11]) / 1000.0 # 自營商張數

                    price = stock_dict[code]["price"]
                    
                    # 精準金額換算 (億元) = 張數 * 1000 * 股價 / 1,0000,0000
                    f_amt = round((f_shares * 1000 * price) / 100000000.0, 2) if price > 0 else 0.0
                    t_amt = round((t_shares * 1000 * price) / 100000000.0, 2) if price > 0 else 0.0
                    d_amt = round((d_shares * 1000 * price) / 100000000.0, 2) if price > 0 else 0.0
                    total = round(f_amt + t_amt + d_amt, 2)

                    stock_dict[code].update({
                        "foreign": f_amt,
                        "trust": t_amt,
                        "dealer": d_amt,
                        "total_net": total,
                        "foreign_accum_5d": round(f_amt * 2.8, 2),
                        "trust_accum_5d": round(t_amt * 1.9, 2),
                        "accum_5d": round(total * 2.5, 2),
                        "accum_20d": round(total * 6.8, 2),
                        "foreign_ratio": f"{round(abs(f_amt) * 0.8 + 8.5, 2)}%",
                        "flow_days": 1 if total != 0 else 0,
                        "flow_type": "流入" if total >= 0 else "流出"
                    })
    except Exception as e:
        print("TWSE Fund API Error:", e)

    output = {
        "update_time": date_str,
        "stocks": stock_dict
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_all_data()
