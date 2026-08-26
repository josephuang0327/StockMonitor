import os
import json
import requests

from datetime import datetime, timedelta
from dotenv import load_dotenv


# ==================================================
# 載入 .env
# ==================================================

load_dotenv()


# ==================================================
# Fugle 設定
# ==================================================

API_KEY = os.getenv(
    "FUGLE_API_KEY"
)

BASE_URL = (
    "https://api.fugle.tw/"
    "marketdata/v1.0/stock"
)

HEADERS = {
    "X-API-KEY": API_KEY
}


# ==================================================
# 設定
# ==================================================

HISTORY_30M_BARS = 200

HISTORY_DAILY_DAYS = 19

TIMEFRAME_30M = "30"

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

            history = json.load(f)

        if not isinstance(
            history,
            dict
        ):

            return {}

        return history

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
# 檢查 Fugle API Key
# ==================================================

def check_api_key():

    if not API_KEY:

        print(
            "找不到 FUGLE_API_KEY"
        )

        return False

    return True


# ==================================================
# 取得歷史 K 線
# ==================================================

def fetch_historical_candles(
    stock,
    start_date,
    end_date,
    timeframe
):

    url = (
        f"{BASE_URL}/"
        f"historical/candles/"
        f"{stock}"
    )

    params = {

        "from":
            start_date.strftime(
                "%Y-%m-%d"
            ),

        "to":
            end_date.strftime(
                "%Y-%m-%d"
            ),

        "timeframe":
            timeframe,

        "fields":
            "open,high,low,close,volume,average",

        "sort":
            "asc"
    }

    response = session.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    result = response.json()

    return result.get(
        "data",
        []
    )


# ==================================================
# 歷史 30 分 K
# ==================================================

def fetch_historical_30m(
    stock,
    start_date,
    end_date
):

    return fetch_historical_candles(
        stock,
        start_date,
        end_date,
        TIMEFRAME_30M
    )


# ==================================================
# 歷史日 K
# ==================================================

def fetch_historical_daily(
    stock,
    start_date,
    end_date
):

    return fetch_historical_candles(
        stock,
        start_date,
        end_date,
        "D"
    )


# ==================================================
# 今天盤中 30 分 K
# ==================================================

def fetch_intraday_30m(
    stock
):

    url = (
        f"{BASE_URL}/"
        f"intraday/candles/"
        f"{stock}"
    )

    params = {

        "timeframe":
            TIMEFRAME_30M,

        "sort":
            "asc"
    }

    response = session.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    result = response.json()

    return result.get(
        "data",
        []
    )


# ==================================================
# Fugle 即時報價
#
# 注意：
# 這裡取得的是「即時成交價」
# 不再使用 TWSE 買一 / 賣一
# ==================================================

def fetch_realtime_price(
    stock
):

    url = (
        f"{BASE_URL}/"
        f"intraday/quote/"
        f"{stock}"
    )

    response = session.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()

    result = response.json()

    return result


# ==================================================
# 從即時報價取得成交價
# ==================================================

def get_current_price(
    stock
):

    data = fetch_realtime_price(
        stock
    )

    # --------------------------------------------------
    # Fugle quote 通常會提供 lastPrice
    # --------------------------------------------------

    if "lastPrice" in data:

        return float(
            data["lastPrice"]
        )

    # --------------------------------------------------
    # 如果 API 回傳包在 data 裡
    # --------------------------------------------------

    if (
        isinstance(
            data.get("data"),
            dict
        )
        and
        "lastPrice"
        in data["data"]
    ):

        return float(
            data["data"]["lastPrice"]
        )

    raise ValueError(
        f"{stock} 找不到即時成交價"
    )


# ==================================================
# 整理 K 線
# ==================================================

def normalize_candles(
    candles
):

    result = {}

    for candle in candles:

        try:

            date_time = candle[
                "date"
            ]

            result[date_time] = {

                "date":
                    date_time,

                "open":
                    float(
                        candle["open"]
                    ),

                "high":
                    float(
                        candle["high"]
                    ),

                "low":
                    float(
                        candle["low"]
                    ),

                "close":
                    float(
                        candle["close"]
                    ),

                "volume":
                    float(
                        candle["volume"]
                    )
            }

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            continue

    return result


# ==================================================
# 取得本地最後一根 30 分 K
# ==================================================

def get_last_local_datetime(
    local_data
):

    if not local_data:

        return None

    dates = []

    for candle in local_data:

        try:

            date_time = datetime.fromisoformat(
                candle["date"]
            )

            dates.append(
                date_time
            )

        except Exception:

            continue

    if not dates:

        return None

    return max(dates)


# ==================================================
# 更新單一股票 30 分 K
# ==================================================

def update_stock_30m(
    stock,
    history
):

    stock_key = str(stock)

    # ==================================================
    # 建立 30m 結構
    # ==================================================

    if "30m" not in history:

        history["30m"] = {}

    if not isinstance(
        history["30m"],
        dict
    ):

        history["30m"] = {}

    if stock_key not in history["30m"]:

        history["30m"][stock_key] = []


    local_data = history[
        "30m"
    ][
        stock_key
    ]


    if not isinstance(
        local_data,
        list
    ):

        local_data = []


    # ==================================================
    # 建立資料索引
    # ==================================================

    existing = {}

    for candle in local_data:

        try:

            date_time = candle[
                "date"
            ]

            existing[
                date_time
            ] = candle

        except (
            KeyError,
            TypeError
        ):

            continue


    last_local_datetime = (
        get_last_local_datetime(
            local_data
        )
    )


    today = datetime.now().date()


    print(
        f"\n========== {stock} =========="
    )


    # ==================================================
    # 第一次沒有資料
    # ==================================================

    if last_local_datetime is None:

        print(
            f"{stock} 沒有本地30分K"
        )

        print(
            f"{stock} 開始取得歷史30分K..."
        )

        start_date = (
            today
            - timedelta(days=70)
        )

        end_date = (
            today
            - timedelta(days=1)
        )

        historical = (
            fetch_historical_30m(
                stock,
                start_date,
                end_date
            )
        )

        historical_data = (
            normalize_candles(
                historical
            )
        )

        print(
            f"{stock} 歷史取得 "
            f"{len(historical_data)} 根"
        )

        for date_time, candle in (
            historical_data.items()
        ):

            existing[
                date_time
            ] = candle


    # ==================================================
    # 已經有本地資料
    # ==================================================

    else:

        print(
            f"{stock} 本地最後30分K: "
            f"{last_local_datetime.strftime('%Y-%m-%d %H:%M')}"
        )

        end_date = (
            today
            - timedelta(days=1)
        )


        # ==================================================
        # 本地不足200根
        # ==================================================

        if len(existing) < HISTORY_30M_BARS:

            print(
                f"{stock} 本地只有 "
                f"{len(existing)} 根，"
                f"需要補到 "
                f"{HISTORY_30M_BARS} 根"
            )

            start_date = (
                today
                - timedelta(days=70)
            )

            print(
                f"{stock} 補抓歷史30分K: "
                f"{start_date} 至 {end_date}"
            )

            historical = (
                fetch_historical_30m(
                    stock,
                    start_date,
                    end_date
                )
            )

            historical_data = (
                normalize_candles(
                    historical
                )
            )

            print(
                f"{stock} 歷史取得 "
                f"{len(historical_data)} 根"
            )

            for date_time, candle in (
                historical_data.items()
            ):

                existing[
                    date_time
                ] = candle


        # ==================================================
        # 已經有200根
        # ==================================================

        else:

            start_date = (
                last_local_datetime.date()
            )

            if start_date <= end_date:

                print(
                    f"{stock} 補抓歷史30分K: "
                    f"{start_date} 至 {end_date}"
                )

                historical = (
                    fetch_historical_30m(
                        stock,
                        start_date,
                        end_date
                    )
                )

                historical_data = (
                    normalize_candles(
                        historical
                    )
                )

                print(
                    f"{stock} 補回 "
                    f"{len(historical_data)} 根"
                )

                for date_time, candle in (
                    historical_data.items()
                ):

                    existing[
                        date_time
                    ] = candle

            else:

                print(
                    f"{stock} 沒有需要補的歷史30分K"
                )


    # ==================================================
    # 今天盤中30分K
    # ==================================================

    print(
        f"取得 {stock} 今天盤中30分K..."
    )

    intraday = (
        fetch_intraday_30m(
            stock
        )
    )

    intraday_data = (
        normalize_candles(
            intraday
        )
    )

    print(
        f"{stock} 今天盤中取得 "
        f"{len(intraday_data)} 根"
    )


    # ==================================================
    # 合併
    # ==================================================

    for date_time, candle in (
        intraday_data.items()
    ):

        existing[
            date_time
        ] = candle


    # ==================================================
    # 排序
    # ==================================================

    all_data = sorted(
        existing.values(),
        key=lambda x: x["date"]
    )


    # ==================================================
    # 保留最近200根
    # ==================================================

    final_data = all_data[
        -HISTORY_30M_BARS:
    ]


    # ==================================================
    # 寫回 history
    # ==================================================

    history[
        "30m"
    ][
        stock_key
    ] = final_data


    # ==================================================
    # 顯示
    # ==================================================

    print(
        f"{stock} 30分K目前共有 "
        f"{len(final_data)} 根"
    )

    if final_data:

        first_date = (
            final_data[0]["date"]
            [:16]
            .replace(
                "T",
                " "
            )
        )

        last_date = (
            final_data[-1]["date"]
            [:16]
            .replace(
                "T",
                " "
            )
        )

        print(
            f"{stock} 30分K範圍: "
            f"{first_date} 至 "
            f"{last_date}"
        )

    return True


# ==================================================
# 更新全部股票 30 分 K
# ==================================================

def update_all_30m(
    Stocks
):

    if not check_api_key():

        return {}

    history = load_history()

    for stock in Stocks:

        try:

            update_stock_30m(
                stock,
                history
            )

        except Exception as e:

            print(
                f"{stock} "
                f"30分K更新失敗:",
                e
            )

    if save_history(
        history
    ):

        print(
            "\n30分K history 已更新"
        )

    else:

        print(
            "\n30分K history 更新失敗"
        )

    return history


# ==================================================
# 更新單一股票日K
# ==================================================

def update_stock_daily(
    stock,
    history
):

    stock_key = str(stock)

    if stock_key not in history:

        history[stock_key] = []


    # ==================================================
    # 本地資料
    # ==================================================

    existing = {}

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

            existing[
                date
            ] = close

        except Exception:

            continue


    # ==================================================
    # 抓最近70天
    # ==================================================

    today = datetime.now().date()

    start_date = (
        today
        - timedelta(days=70)
    )

    end_date = (
        today
        - timedelta(days=1)
    )


    print(
        f"\n取得 {stock} 歷史日K..."
    )


    candles = (
        fetch_historical_daily(
            stock,
            start_date,
            end_date
        )
    )


    # ==================================================
    # 加入 Fugle 資料
    # ==================================================

    for candle in candles:

        try:

            date = candle[
                "date"
            ]

            close = float(
                candle["close"]
            )

            existing[
                date
            ] = close

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            continue


    # ==================================================
    # 排序
    # ==================================================

    all_data = sorted(
        existing.items()
    )


    # ==================================================
    # 最新19個交易日
    # ==================================================

    final_data = all_data[
        -HISTORY_DAILY_DAYS:
    ]


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
    # 顯示
    # ==================================================

    print(
        f"{stock} 日K目前共有 "
        f"{len(final_data)} 天"
    )

    if final_data:

        print(
            f"{stock} 日K範圍: "
            f"{final_data[0][0]} 至 "
            f"{final_data[-1][0]}"
        )

    return True


# ==================================================
# 更新全部股票日K
# ==================================================

def update_all_daily(
    Stocks
):

    if not check_api_key():

        return {}

    history = load_history()

    for stock in Stocks:

        try:

            update_stock_daily(
                stock,
                history
            )

        except Exception as e:

            print(
                f"{stock} "
                f"日K更新失敗:",
                e
            )

    if save_history(
        history
    ):

        print(
            "\n日K history 已更新"
        )

    else:

        print(
            "\n日K history 更新失敗"
        )

    return history


# ==================================================
# 測試
# ==================================================

if __name__ == "__main__":

    stock = 2330

    print(
        "========================================"
    )

    print(
        "Fugle data_fetch 測試"
    )

    print(
        "========================================"
    )


    # ==================================================
    # 測試即時成交價
    # ==================================================

    try:

        quote = fetch_realtime_price(
            stock
        )

        print(
            "\n--- Fugle 即時報價 ---"
        )

        print(
            quote
        )


        price = get_current_price(
            stock
        )

        print(
            f"\n{stock} "
            f"目前成交價: "
            f"{price:g}"
        )

    except Exception as e:

        print(
            "\n即時報價取得失敗:",
            e
        )


    # ==================================================
    # 測試歷史日K
    # ==================================================

    try:

        start_date = datetime(
            2026,
            7,
            1
        ).date()

        end_date = datetime(
            2026,
            8,
            25
        ).date()


        data = (
            fetch_historical_daily(
                stock,
                start_date,
                end_date
            )
        )


        print(
            "\n--- Fugle 歷史日K ---"
        )

        print(
            f"取得日K: "
            f"{len(data)} 根"
        )


        print(
            "\n前3根:"
        )

        for candle in data[:3]:

            print(
                candle
            )


        print(
            "\n後3根:"
        )

        for candle in data[-3:]:

            print(
                candle
            )

    except Exception as e:

        print(
            "\n歷史日K取得失敗:",
            e
        )