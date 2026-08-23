import time

from data_fetch import (
    update_all_history,
    fetch_realtime
)

from line_notify import (
    send_line
)

from indicators import (
    calculate_indicators,
    check_signals
)


# ==================================================
# 股票
# ==================================================

Stocks = [
    2330,
    3653,
    2327
]


# ==================================================
# 歷史資料
# ==================================================

print(
    "正在檢查並校正歷史資料..."
)

history = update_all_history(
    Stocks
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


        data = fetch_realtime(
            list(MA_DATA.keys())
        )


        for stk in data.get(
            "msgArray",
            []
        ):

            stock = int(
                stk["c"]
            )


            if stock not in MA_DATA:

                continue


            # ==================================================
            # 買一 / 賣一
            # ==================================================

            buy1_text = (
                stk["b"]
                .split("_")[0]
            )

            sell1_text = (
                stk["a"]
                .split("_")[0]
            )


            if (

                buy1_text in (
                    "",
                    "-"
                )

                or

                sell1_text in (
                    "",
                    "-"
                )

            ):

                continue


            buy1 = float(
                buy1_text
            )

            sell1 = float(
                sell1_text
            )


            # ==================================================
            # 當下價格
            # ==================================================

            price = (
                buy1 + sell1
            ) / 2


            # ==================================================
            # 計算 MA / BBand / Level
            # ==================================================

            indicators = calculate_indicators(
                MA_DATA[stock],
                price
            )


            # ==================================================
            # Signal
            # ==================================================

            signals = check_signals(
                stock=stock,
                name=stk["n"],
                buy1=buy1,
                ma_data=indicators,
                status=MA_STATUS[stock]
            )


            # ==================================================
            # LINE
            # ==================================================

            for signal in signals:

                print(
                    signal
                )

                send_line(
                    signal
                )


            # ==================================================
            # 沒有 Signal
            # ==================================================

            if not signals:

                print(

                    f"{stk['c']} "
                    f"{stk['n']} | "
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