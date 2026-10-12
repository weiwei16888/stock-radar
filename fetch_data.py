import requests
import json
import re

def fetch_all_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. 抓取 TWSE 上市每日收盤與三大法人數據
    twse_url = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?response=json"
    twse_bs_url = "https://www.twse.com.tw/rwd/zh/fund/T86?response=json&selectType=ALL"
    
    stock_dict = {}

    try:
        r = requests.get(twse_bs_url, headers=headers).json()
        if r.get('stat') == 'OK':
            date_str = r.get('date', '')
            for row in r.get('data', []):
                code = row[0].strip()
                name = row[1].strip()
                foreign = float(row[4].replace(',', '')) if row[4] != '--' else 0
                trust = float(row[10].replace(',', '')) if row[10] != '--' else 0
                
                stock_dict[code] = {
                    "code": code,
                    "name": name,
                    "market": "上市",
                    "foreign": round(foreign / 100000000, 2),  # 單位：億
                    "trust": round(trust / 100000000, 2),      # 單位：億
                    "total_net": round((foreign + trust) / 100000000, 2)
                }
    except Exception as e:
        print("TWSE Fetch Error:", e)

    # 2. 抓取 TPEx 上櫃三大法人數據
    tpex_bs_url = "https://www.tpex.org.tw/web/stock/33_middle/33_foreign/forstr_result.php?l=zh-tw&t=D"
    try:
        r = requests.get(tpex_bs_url, headers=headers).json()
        if 'aaData' in r:
            for row in r.get('aaData', []):
                code = row[0].strip()
                name = row[1].strip()
                foreign = float(row[8].replace(',', '')) if row[8] != '--' else 0
                trust = float(row[14].replace(',', '')) if row[14] != '--' else 0
                
                stock_dict[code] = {
                    "code": code,
                    "name": name,
                    "market": "上櫃",
                    "foreign": round(foreign / 100000000, 2),
                    "trust": round(trust / 100000000, 2),
                    "total_net": round((foreign + trust) / 100000000, 2)
                }
    except Exception as e:
        print("TPEx Fetch Error:", e)

    output = {
        "update_time": date_str if 'date_str' in locals() else "最新交易日",
        "stocks": stock_dict
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_all_data()
