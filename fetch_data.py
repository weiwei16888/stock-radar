import requests
import json
import random

def fetch_all_data():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    stock_dict = {}
    date_str = "最新交易日"

    # 1. 抓取證交所 TWSE (上市) 全股票三大法人買賣超
    try:
        twse_url = "https://www.twse.com.tw/rwd/zh/fund/T86?response=json&selectType=ALL"
        r = requests.get(twse_url, headers=headers, timeout=10).json()
        if r.get('stat') == 'OK':
            date_str = r.get('date', date_str)
            for row in r.get('data', []):
                code = row[0].strip()
                name = row[1].strip()
                
                # 排除 ETF、認購售權證 (只留普通股)
                if len(code) != 4 or not code.isdigit():
                    continue

                foreign = float(row[4].replace(',', '')) if row[4] != '--' else 0
                trust = float(row[10].replace(',', '')) if row[10] != '--' else 0
                dealer = float(row[11].replace(',', '')) if row[11] != '--' else 0

                f_b = round(foreign / 100000000, 2)
                t_b = round(trust / 100000000, 2)
                d_b = round(dealer / 100000000, 2)
                total = round(f_b + t_b + d_b, 2)

                # 預設產業分類
                category = "其他族群"
                if code.startswith('28'): category = "銀行金融"
                elif code.startswith('23') or code.startswith('24'): category = "半導體與電子"
                elif code.startswith('26'): category = "貨櫃與航運"
                elif code.startswith('30') or code.startswith('31'): category = "電子零組件"

                daily_history = [round(random.uniform(-0.8, 1.2), 2) for _ in range(30)]
                daily_history[0] = total

                stock_dict[code] = {
                    "code": code,
                    "name": name,
                    "category": category,
                    "market": "上市",
                    "price": round(random.uniform(20, 600), 1),
                    "change": round(random.uniform(-3, 3), 1),
                    "change_pct": f"{round(random.uniform(-2, 2), 2)}%",
                    "foreign": f_b,
                    "trust": t_b,
                    "dealer": d_b,
                    "total_net": total,
                    "daily_history": daily_history,
                    "kline": [{"o": 100, "c": 102, "h": 105, "l": 98, "v": 10000} for _ in range(30)],
                    "foreign_ratio": f"{round(random.uniform(5, 45), 2)}%",
                    "flow_days": random.randint(1, 8),
                    "flow_type": "流入" if total >= 0 else "流出"
                }
    except Exception as e:
        print("TWSE Error:", e)

    # 2. 抓取櫃買中心 TPEx (上櫃) 全股票三大法人買賣超
    try:
        tpex_url = "https://www.tpex.org.tw/web/stock/333/333_result.php?l=zh-tw&o=json"
        r2 = requests.get(tpex_url, headers=headers, timeout=10).json()
        if r2.get('aaData'):
            for row in r2.get('aaData', []):
                code = str(row[0]).strip()
                name = str(row[1]).strip()

                if len(code) != 4 or not code.isdigit():
                    continue

                foreign = float(str(row[8]).replace(',', '')) if row[8] != '--' else 0
                trust = float(str(row[11]).replace(',', '')) if row[11] != '--' else 0
                dealer = float(str(row[14]).replace(',', '')) if row[14] != '--' else 0

                f_b = round(foreign / 100000000, 2)
                t_b = round(trust / 100000000, 2)
                d_b = round(dealer / 100000000, 2)
                total = round(f_b + t_b + d_b, 2)

                category = "上櫃熱門股"
                if code.startswith('61') or code.startswith('62'): category = "被動與網通"
                elif code.startswith('32') or code.startswith('35'): category = "光電與生技"

                daily_history = [round(random.uniform(-0.8, 1.2), 2) for _ in range(30)]
                daily_history[0] = total

                stock_dict[code] = {
                    "code": code,
                    "name": name,
                    "category": category,
                    "market": "上櫃",
                    "price": round(random.uniform(15, 350), 1),
                    "change": round(random.uniform(-2, 2), 1),
                    "change_pct": f"{round(random.uniform(-2, 2), 2)}%",
                    "foreign": f_b,
                    "trust": t_b,
                    "dealer": d_b,
                    "total_net": total,
                    "daily_history": daily_history,
                    "kline": [{"o": 50, "c": 52, "h": 55, "l": 48, "v": 5000} for _ in range(30)],
                    "foreign_ratio": f"{round(random.uniform(3, 30), 2)}%",
                    "flow_days": random.randint(1, 6),
                    "flow_type": "流入" if total >= 0 else "流出"
                }
    except Exception as e:
        print("TPEx Error:", e)

    output = {
        "update_time": date_str,
        "stocks": stock_dict
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    fetch_all_data()
