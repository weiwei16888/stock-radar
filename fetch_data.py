import requests
import json
from datetime import datetime

def clean_int(val):
    if isinstance(val, (int, float)): return int(val)
    if not val or not isinstance(val, str): return 0
    clean_str = val.replace(",", "").replace(" ", "").strip()
    try: return int(clean_str)
    except ValueError: return 0

def get_twse_stocks(today_twse_str):
    url = f"https://www.twse.com.tw/rwd/zh/fund/T86?response=json&date={today_twse_str}&selectType=ALL"
    headers = {"User-Agent": "Mozilla/5.0"}
    stocks = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        if data.get("stat") == "OK":
            for row in data.get("data", []):
                code, name = row[0].strip(), row[1].strip()
                if len(code) == 4 and code.isdigit():
                    stocks.append({
                        "code": code,
                        "name": name,
                        "market": "上市",
                        "foreign": round(clean_int(row[4]) / 1000),
                        "trust": round(clean_int(row[10]) / 1000)
                    })
    except Exception as e: print(f"TWSE Error: {e}")
    return stocks

def get_tpex_stocks(today_tpex_str):
    url = f"https://www.tpex.org.tw/web/stock/333/333_result.php?l=zh-tw&o=json&se=AL&d={today_tpex_str}"
    headers = {"User-Agent": "Mozilla/5.0"}
    stocks = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        for row in data.get("aaData", []):
            code, name = str(row[0]).strip(), str(row[1]).strip()
            if len(code) == 4 and code.isdigit():
                stocks.append({
                    "code": code,
                    "name": name,
                    "market": "上櫃",
                    "foreign": round(clean_int(row[8]) / 1000),
                    "trust": round(clean_int(row[11]) / 1000)
                })
    except Exception as e: print(f"TPEx Error: {e}")
    return stocks

def process_chip_data():
    now = datetime.now()
    today_twse = now.strftime("%Y%m%d")
    today_tpex = f"{now.year - 1911}/{now.strftime('%m/%d')}"
    
    all_raw = get_twse_stocks(today_twse) + get_tpex_stocks(today_tpex)
    processed = []
    
    for item in all_raw:
        f, t = item["foreign"], item["trust"]
        if f > 0 and t > 0: q = "bothBuy"
        elif f <= 0 and t > 0: q = "trustBuyOnly"
        elif f > 0 and t <= 0: q = "foreignBuyOnly"
        else: q = "bothSell"

        score = min(99, max(10, int(50 + ((f + t) / 50))))
        status = "🔥 主力極度鎖碼 (突破成本區)" if score >= 80 else ("⚡ 法人沿成本線加碼" if score >= 60 else "❄️ 籌碼鬆動 (回測主力成本)")

        processed.append({
            "code": item["code"],
            "name": item["name"],
            "market": item["market"],
            "foreign": f,
            "trust": t,
            "quadrant": q,
            "vip_data": {
                "score": score,
                "status": status
            }
        })

    output = {"update_time": now.strftime("%Y-%m-%d %H:%M:%S"), "total_count": len(processed), "stocks": processed}
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process_chip_data()
