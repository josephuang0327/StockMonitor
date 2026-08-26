import json

from indicators import calculate_ema23


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
# 取得 2330 的 30 分 K
# ==================================================

candles = history[
    "30m"
][
    "2330"
]


# ==================================================
# 取得收盤價
# ==================================================

closes = [

    candle["close"]

    for candle in candles

]


# ==================================================
# 計算 EMA23
# ==================================================
print(
    "前23根 SMA:",
    sum(closes[:23]) / 23
)

print(
    "前200根 SMA:",
    sum(closes[:200]) / 200
)

print(
    "前490根 SMA:",
    sum(closes) / len(closes)
)
ema23 = calculate_ema23(
    closes
)


# ==================================================
# 顯示結果
# ==================================================

print("=" * 40)

print("2330 EMA23 測試")

print("=" * 40)

print(
    f"使用 K 線數量: {len(closes)}"
)

print(
    f"最新30分K: "
    f"{candles[-1]['date'][:16].replace('T', ' ')}"
)

print(
    f"最新30分K Close: "
    f"{closes[-1]:g}"
)

print(
    f"EMA23: "
    f"{ema23:.4f}"
)

print("=" * 40)