import time
import os
from datetime import datetime

from fugle import (
    update_all_daily,
    update_all_30m,
    start_websocket,
    stop_websocket,
    get_realtime_prices,
    update_completed_30m
)

from indicators import (
    calculate_indicators,
    check_signals,
    calculate_ema23,
    calculate_ema_filter
)


# ==================================================
# 股票
# ==================================================

Stocks = [
    2330,
    3653,
    3017,
    3037,
    1815
]


# ==================================================
# 啟動
# ==================================================

print("========================================")
print("程式交易監控系統啟動")
print("股票:", ", ".join(map(str, Stocks)))
print("========================================")


# ==================================================
# 1. 更新歷史日K
# ==================================================

print("\n[1/3] 更新歷史日K...")

history = update_all_daily(
    Stocks
)

print("歷史日K更新完成")


# ==================================================
# 2. 更新30分K
# ==================================================

print("\n[2/3] 更新30分K...")

history_30m = update_all_30m(
    Stocks
)

if "30m" in history_30m:

    history["30m"] = (
        history_30m["30m"]
    )

print("30分K更新完成")


# ==================================================
# MA DATA
# ==================================================

MA_DATA = {}


for stock in Stocks:

    stock_key = str(stock)

    if stock_key not in history:

        print(
            f"{stock} 沒有歷史資料，"
            f"跳過指標計算"
        )

        continue


    if len(
        history[stock_key]
    ) < 19:

        print(
            f"{stock} 歷史資料不足19天，"
            f"跳過指標計算"
        )

        continue


    MA_DATA[stock] = [

        close

        for date, close
        in history[stock_key]

    ]


# ==================================================
# Signal 狀態
# ==================================================

MA_STATUS = {}


for stock in MA_DATA:

    MA_STATUS[stock] = {

        "MA5": False,

        "MA10": False,

        "MA20": False,

        "LB": False,

        "UB": False,

        "LEVEL_NEG8": False,

        "LEVEL_8": False

    }


# ==================================================
# 3. 啟動 WebSocket
# ==================================================

print("\n[3/3] 啟動 Fugle WebSocket...")


if not start_websocket(
    Stocks
):

    print(
        "Fugle WebSocket 啟動失敗"
    )

    raise SystemExit(1)


print("\n========================================")
print("開始即時監控")
print("監控股票:", ", ".join(map(str, Stocks)))
print("按 Ctrl+C 停止")
print("========================================")


# ==================================================
# 即時價格狀態
# ==================================================

last_prices = {}


# ==================================================
# 30分K區間狀態
#
# 用來判斷是否跨過30分鐘
# ==================================================

last_30m_period = None


# ==================================================
# 初始化目前30分鐘區間
# ==================================================

now = datetime.now()

last_30m_period = now.replace(

    minute=(
        now.minute // 30
    ) * 30,

    second=0,

    microsecond=0

)


# ==================================================
# 主迴圈
# ==================================================

try:

    while True:

        # ==================================================
        # 現在時間
        # ==================================================

        now = datetime.now()


        # ==================================================
        # 計算目前30分鐘區間
        # ==================================================

        current_30m_period = now.replace(

            minute=(
                now.minute // 30
            ) * 30,

            second=0,

            microsecond=0

        )


        # ==================================================
        # 跨過30分鐘
        #
        # 例如：
        #
        # 10:29 -> 10:30
        #
        # 更新剛完成的10:00~10:30
        #
        # 10:59 -> 11:00
        #
        # 更新剛完成的10:30~11:00
        # ==================================================

        if (
            current_30m_period
            > last_30m_period
        ):

            print(
                f"\n[{now.strftime('%H:%M:%S')}] "
                f"30分K完成，正在更新..."
            )


            try:

                history = (
                    update_completed_30m(
                        Stocks,
                        history
                    )
                )


                print(
                    "30分K更新完成"
                )


            except Exception as e:

                print(
                    "30分K更新失敗:",
                    e
                )


            # --------------------------------------------------
            # 更新區間狀態
            # --------------------------------------------------

            last_30m_period = (
                current_30m_period
            )


        # ==================================================
        # 取得 WebSocket 即時價格
        # ==================================================

        prices = get_realtime_prices()


        # ==================================================
        # 檢查所有股票
        # ==================================================

        for stock in MA_DATA:

            stock_key = str(stock)

            price = prices.get(
                stock_key
            )


            if price is None:

                continue


            price = float(
                price
            )


            # ==================================================
            # 價格沒有變化
            # 不重新計算
            # ==================================================

            if (

                stock_key in last_prices

                and

                last_prices[
                    stock_key
                ] == price

            ):

                continue


            # ==================================================
            # 更新最後價格
            # ==================================================

            last_prices[
                stock_key
            ] = price


            # ==================================================
            # 成交時間
            # ==================================================

            receive_time = (
                time.strftime(
                    "%H:%M:%S"
                )
            )


            print(
                f"\n[{receive_time}] "
                f"{stock} | "
                f"Price: {price:g}"
            )


            # ==================================================
            # MA / BBand / Level
            # ==================================================

            indicators = calculate_indicators(

                MA_DATA[stock],

                price

            )


            print(

                f"MA5: "
                f"{indicators['ma5']:.2f} | "

                f"MA10: "
                f"{indicators['ma10']:.2f} | "

                f"MA20: "
                f"{indicators['ma20']:.2f} \n "

                f"UB: "
                f"{indicators['ub']:.2f} | "

                f"LB: "
                f"{indicators['lb']:.2f} | "

                f"Lv8: "
                f"{indicators['level8']:.2f} | "

                f"Lv-8: "
                f"{indicators['level_neg8']:.2f}"

            )


            # ==================================================
            # EMA23
            # ==================================================

            ema23 = None

            ema_up = None

            ema_dw = None


            if (

                "30m" in history

                and

                stock_key
                in history["30m"]

            ):

                candles_30m = (
                    history["30m"][
                        stock_key
                    ]
                )


                if len(
                    candles_30m
                ) >= 23:


                    closes_30m = [

                        candle["close"]

                        for candle
                        in candles_30m

                    ]


                    # --------------------------------------------------
                    # 使用已完成30分K計算 EMA23
                    # --------------------------------------------------

                    ema23 = calculate_ema23(

                        closes_30m

                    )


                    # --------------------------------------------------
                    # 使用目前即時成交價
                    # 更新正在形成中的30分K
                    # --------------------------------------------------

                    alpha = (

                        2 / (23 + 1)

                    )


                    ema23 = (

                        price * alpha

                        +

                        ema23 * (
                            1 - alpha
                        )

                    )


                    ema_up, ema_dw = (
                        calculate_ema_filter(
                            ema23
                        )
                    )


                    print(

                        f"EMA23: "
                        f"{ema23:.2f} | "

                        f"EMA_UP: "
                        f"{ema_up:.2f} | "

                        f"EMA_DW: "
                        f"{ema_dw:.2f}"

                    )


            # ==================================================
            # Signal
            # ==================================================

            signals = check_signals(

                stock=stock,

                name="",

                price=price,

                ma_data=indicators,

                status=MA_STATUS[stock]

            )


            # ==================================================
            # Signal 顯示
            # ==================================================

            for signal in signals:

                print(
                    f"*** SIGNAL *** {signal}\n"
                )


        # ==================================================
        # CPU 讓出
        #
        # 這不是 HTTP request
        # WebSocket 仍然持續接收
        # ==================================================

        time.sleep(0.01)


# ==================================================
# Ctrl+C
# ==================================================

except KeyboardInterrupt:

    print(
        "\n\n收到 Ctrl+C"
    )

    print(
        "正在停止 Fugle WebSocket..."
    )


    try:

        stop_websocket()

    except Exception as e:

        print(
            "停止 WebSocket 失敗:",
            e
        )


    print(
        "程式已停止"
    )

    raise SystemExit(0)


# ==================================================
# 其他錯誤
# ==================================================

except Exception as e:

    print(
        "\n程式發生錯誤:",
        e
    )


    try:

        stop_websocket()

    except Exception:
        pass


    raise SystemExit(1)