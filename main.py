import time

from fugle import (
    update_all_daily,
    update_all_30m,
    fetch_realtime_price
)

from line_notify import (
    send_line
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
    2330
]


# ==================================================
# 歷史資料
# ==================================================

print(
    "正在檢查並校正歷史資料..."
)

history = update_all_daily(
    Stocks
)


# ==================================================
# 30分K DATA
# ==================================================

print(
    "\n正在檢查並更新30分K資料..."
)

history_30m = update_all_30m(
    Stocks
)

# 保留原本日K history
# 只把30分K資料加入進來

if "30m" in history_30m:

    history["30m"] = (
        history_30m["30m"]
    )


# ==================================================
# MA DATA
# ==================================================

MA_DATA = {}


for stock in Stocks:

    stock_key = str(stock)

    if stock_key not in history:

        print(
            f"{stock} 沒有歷史資料，"
            f"跳過 MA 計算"
        )

        continue

    if len(
        history[stock_key]
    ) < 19:

        print(
            f"{stock} 歷史資料不足19天，"
            f"跳過 MA 計算"
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
# 開始盤中監控
# ==================================================

while True:

    try:

        if not MA_DATA:

            print(
                "目前沒有可以監控的股票"
            )

            time.sleep(10)

            continue


        # ==================================================
        # 取得 Fugle 即時報價
        # ==================================================

        for stock in MA_DATA:

            stock_key = str(stock)

            try:

                quote = (
                    fetch_realtime_price(
                        stock
                    )
                )

            except Exception as e:

                print(
                    f"{stock} "
                    f"Fugle 即時報價取得失敗:",
                    e
                )

                continue


            # ==================================================
            # 最新成交價
            # ==================================================

            price = quote.get(
                "lastPrice"
            )

            if price is None:

                print(
                    f"{stock} "
                    f"沒有取得最新成交價"
                )

                continue

            price = float(
                price
            )


            # ==================================================
            # 買一 / 賣一
            # ==================================================

            bids = quote.get(
                "bids",
                []
            )

            asks = quote.get(
                "asks",
                []
            )


            if not bids or not asks:

                print(
                    f"{stock} "
                    f"沒有買一或賣一資料"
                )

                continue


            buy1 = float(
                bids[0]["price"]
            )

            sell1 = float(
                asks[0]["price"]
            )


            # ==================================================
            # 計算 MA / BBand / Level
            #
            # 現在價格全部使用 Fugle lastPrice
            # ==================================================

            indicators = calculate_indicators(
                MA_DATA[stock],
                price
            )
            print(
                f"{stock} 指標 | "
                f"Price: {price:.2f} | "
                f"MA5: {indicators['ma5']:.2f} | "
                f"MA10: {indicators['ma10']:.2f} | "
                f"MA20: {indicators['ma20']:.2f} | "
                f"UB: {indicators['ub']:.2f} | "
                f"LB: {indicators['lb']:.2f} | "
                f"Level8: {indicators['level8']:.2f} | "
                f"Level-8: {indicators['level_neg8']:.2f}"
            )

            # ==================================================
            # EMA23
            # ==================================================

            ema23 = None

            ema_up = None

            ema_dw = None


            if (
                "30m" in history
                and stock_key in history["30m"]
            ):

                candles_30m = (
                    history["30m"][stock_key]
                )


                if len(candles_30m) >= 23:

                    closes_30m = [

                        candle["close"]

                        for candle
                        in candles_30m

                    ]


                    # 完全按照 testema.py
                    # 的方式計算 EMA23

                    ema23 = calculate_ema23(
                        closes_30m
                    )


                    # ==================================================
                    # EMA 即時價格更新
                    #
                    # 最後一根已完成30分K的 EMA
                    # 使用目前 Fugle 成交價更新
                    # ==================================================

                    alpha = (
                        2 / (23 + 1)
                    )


                    ema23 = (

                        price * alpha

                        + ema23 * (
                            1 - alpha
                        )
                    )


                    ema_up, ema_dw = (
                        calculate_ema_filter(
                            ema23
                        )
                    )


            # ==================================================
            # Signal
            # ==================================================

            signals = check_signals(
                stock=stock,
                name=quote.get(
                    "name",
                    str(stock)
                ),
                buy1=buy1,
                ma_data=indicators,
                status=MA_STATUS[stock]
            )


            # ==================================================
            # LINE
            # ==================================================

            # for signal in signals:

            #     print(
            #         signal
            #     )

            #     send_line(
            #         signal
            #     )


            # ==================================================
            # 沒有 Signal
            # ==================================================

            if not signals:

                if ema23 is not None:

                    print(

                        f"{stock} "
                        f"{quote.get('name', '')} | "

                        f"Price: {price:g} | "

                        f"Buy: {buy1:g} | "
                        f"Sell: {sell1:g} | "

                        f"EMA23: {ema23:.2f} | "

                        f"EMA_UP: {ema_up:.2f} | "

                        f"EMA_DW: {ema_dw:.2f}"
                    )

                else:

                    print(

                        f"{stock} "
                        f"{quote.get('name', '')} | "

                        f"Price: {price:g} | "

                        f"Buy: {buy1:g} | "
                        f"Sell: {sell1:g}"
                    )


        # ==================================================
        # 抓取時間
        # ==================================================

        print(

            "-------抓取時間",

            time.strftime(
                "%H:%M:%S"
            ),

            "------\n"
        )


    except KeyboardInterrupt:

        print(
            "\n程式已停止"
        )

        break


    except Exception as e:

        print(
            "ERROR:",
            e
        )


    time.sleep(10)