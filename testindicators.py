import json

from data_fetch import fetch_realtime_price
from indicators import calculate_indicators


# ==================================================
# 設定
# ==================================================

STOCK = 2330


# ==================================================
# 讀取 history.json
# ==================================================

with open(
    "history.json",
    "r",
    encoding="utf-8"
) as f:

    history = json.load(f)


# ==================================================
# 取得 2330 歷史日K收盤價
#
# history.json:
#
# "2330": [
#     ["20260803", 2380],
#     ["20260804", 2390],
#     ...
# ]
# ==================================================

daily_data = history[
    str(STOCK)
]


history_prices = [

    float(item[1])

    for item in daily_data

]


# ==================================================
# 取得 Fugle 即時成交價
# ==================================================

quote = fetch_realtime_price(
    STOCK
)


price = float(
    quote["lastPrice"]
)


# ==================================================
# 計算所有指標
#
# calculate_indicators()
# 本身就會把 price 加入：
#
# MA5  = 歷史最後4筆 + price
# MA10 = 歷史最後9筆 + price
# MA20 = 歷史最後19筆 + price
#
# BB = 使用 MA20 的20筆資料
# Level = 根據 MA20 / UB / LB 計算
# ==================================================

ma_data = calculate_indicators(
    history_prices,
    price
)


# ==================================================
# 顯示測試結果
# ==================================================

print("=" * 50)

print(
    f"{STOCK} 台積電 指標測試"
)

print("=" * 50)


# ==================================================
# 基本資料
# ==================================================

print(
    f"歷史日K數量: "
    f"{len(history_prices)}"
)

print(
    f"最新歷史收盤價: "
    f"{history_prices[-1]:g}"
)

print(
    f"Fugle 即時成交價 Price: "
    f"{price:g}"
)


print("-" * 50)


# ==================================================
# MA
# ==================================================

print(
    f"MA5  : "
    f"{ma_data['ma5']:.4f}"
)

print(
    f"MA10 : "
    f"{ma_data['ma10']:.4f}"
)

print(
    f"MA20 : "
    f"{ma_data['ma20']:.4f}"
)


print("-" * 50)


# ==================================================
# BB
# ==================================================

print(
    f"BB Upper 2.00 : "
    f"{ma_data['ub']:.4f}"
)

print(
    f"BB Lower 2.00 : "
    f"{ma_data['lb']:.4f}"
)


print("-" * 50)


# ==================================================
# Level
# ==================================================

print(
    f"Level +8 : "
    f"{ma_data['level8']:.4f}"
)

print(
    f"Level -8 : "
    f"{ma_data['level_neg8']:.4f}"
)


print("=" * 50)