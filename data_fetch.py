import requests
import time
import json
import os
from datetime import datetime


# ==================================================
# URL
# ==================================================

MIS_URL = (
    "https://mis.twse.com.tw/stock/api/"
    "getStockInfo.jsp"
)

DAY_URL = (
    "https://www.twse.com.tw/"
    "exchangeReport/STOCK_DAY"
)


# ==================================================
# 設定
# ==================================================

HISTORY_DAYS = 19

HISTORY_FILE = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    ),
    "history.json"
)


# ==================================================
# Session
# ==================================================

session = requests.Session()


# ==================================================
# 今天
# ==================================================

def today():

    return datetime.now().strftime(
        "%Y%m%d"
    )


# ==================================================
# 往前一個月
# ==================================================

def month_before(
    year,
    month
):

    month -= 1

    if month == 0:

        month = 12
        year -= 1

    return year, month


# ==================================================
# 讀取 history.json
# ==================================================

def load_history():

    if not os.path.exists(
        HISTORY_FILE
    ):

        return {}

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(
            "讀取 history.json 失敗:",
            e
        )

        return {}


# ==================================================
# 儲存 history.json
# ==================================================

def save_history(history):

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                ensure_ascii=False,
                indent=2
            )

        return True

    except Exception as e:

        print(
            "儲存 history.json 失敗:",
            e
        )

        return False


# ==================================================
# TWSE 歷史資料
# ==================================================

def fetch_month(
    stock,
    year,
    month
):

    date = (
        f"{year}"
        f"{month:02d}"
        "01"
    )

    params = {
        "response": "json",
        "date": date,
        "stockNo": stock
    }

    try:

        response = session.get(
            DAY_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if "data" not in data:

            return []

        result = []


        for row in data["data"]:

            try:

                date_text = (
                    row[0]
                    .replace("/", "")
                    .strip()
                )


                if len(date_text) != 7:

                    continue


                roc_year = int(
                    date_text[:3]
                )


                full_date = (

                    f"{roc_year + 1911}"

                    f"{date_text[3:5]}"

                    f"{date_text[5:7]}"
                )


                if full_date >= today():

                    continue


                close_text = (
                    row[6]
                    .replace(",", "")
                    .strip()
                )


                if close_text in (
                    "",
                    "-"
                ):

                    continue


                close = float(
                    close_text
                )


                result.append(
                    [
                        full_date,
                        close
                    ]
                )


            except Exception:

                continue


        return result


    except Exception as e:

        print(
            f"TWSE ERROR {stock} "
            f"{year}-{month:02d}:",
            e
        )

        return []


# ==================================================
# 更新單一股票歷史資料
# ==================================================

def update_stock_history(
    stock,
    history
):

    stock_key = str(stock)

    unique = {}


    # ==================================================
    # 整理本地資料
    # ==================================================

    if stock_key in history:

        for item in history[
            stock_key
        ]:

            try:

                if len(item) != 2:

                    continue


                date = str(
                    item[0]
                )

                close = float(
                    item[1]
                )

                unique[date] = close

            except Exception:

                continue


    local_data = sorted(
        unique.items()
    )


    # ==================================================
    # 本地只保留19筆
    # ==================================================

    local_data = (
        local_data[-HISTORY_DAYS:]
    )


    # ==================================================
    # 顯示本地日期
    # ==================================================

    if local_data:

        local_end = (
            local_data[-1][0]
        )

        print(
            f"{stock} 本地最新日期: "
            f"{local_data[0][0]} 至 "
            f"{local_data[-1][0]}"
        )

    else:

        local_end = None

        print(
            f"{stock} 本地沒有歷史資料"
        )


    # ==================================================
    # 從當月開始
    # ==================================================

    year = datetime.now().year

    month = datetime.now().month


    # ==================================================
    # 抓當月份
    # ==================================================

    current_data = fetch_month(
        stock,
        year,
        month
    )


    for date, close in current_data:

        unique[date] = close


    all_data = sorted(
        unique.items()
    )


    # ==================================================
    # 不足19天才往前抓
    # ==================================================

    empty_months = 0


    while len(
        all_data
    ) < HISTORY_DAYS:

        year, month = month_before(
            year,
            month
        )


        print(
            f"取得 {stock} "
            f"{year}-{month:02d}..."
        )


        new_data = fetch_month(
            stock,
            year,
            month
        )


        # ==================================================
        # 沒有資料
        # ==================================================

        if not new_data:

            empty_months += 1


            if empty_months >= 2:

                print(
                    f"{stock} "
                    f"連續2個月沒有歷史資料，跳過"
                )

                return False


        else:

            empty_months = 0


            for date, close in new_data:

                unique[date] = close


        all_data = sorted(
            unique.items()
        )


        if len(
            all_data
        ) >= HISTORY_DAYS:

            break


        time.sleep(0.3)


    # ==================================================
    # 最新19筆
    # ==================================================

    final_data = sorted(
        unique.items()
    )[-HISTORY_DAYS:]


    if not final_data:

        return False


    # ==================================================
    # 寫回 history
    # ==================================================

    history[
        stock_key
    ] = [

        [
            date,
            close
        ]

        for date, close
        in final_data
    ]


    # ==================================================
    # 更新後日期
    # ==================================================

    new_start = (
        final_data[0][0]
    )

    new_end = (
        final_data[-1][0]
    )


    if (
        local_end != new_end
        or local_end is None
    ):

        print(
            f"{stock} 更新後最新日期: "
            f"{new_start} 至 {new_end}"
        )


    return True


# ==================================================
# 更新全部股票
# ==================================================

def update_all_history(Stocks):

    history = load_history()


    for stock in Stocks:

        try:

            update_stock_history(
                stock,
                history
            )


            # 每支股票完成後立即儲存

            save_history(
                history
            )


        except Exception as e:

            print(
                f"{stock} 歷史資料處理失敗:",
                e
            )

            continue


    print(
        "\nhistory.json 已更新"
    )


    return history


# ==================================================
# TWSE MIS 即時資料
# ==================================================

def fetch_realtime(Stocks):

    params = {

        "ex_ch": "|".join(

            f"tse_{x}.tw"

            for x in Stocks
        ),

        "json": "1",

        "delay": "0"
    }


    response = session.get(
        MIS_URL,
        params=params,
        timeout=15
    )


    return response.json()