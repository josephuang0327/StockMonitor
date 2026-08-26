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

API_KEY = os.getenv("FUGLE_API_KEY")

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

HISTORY_30M_BARS = 500
TIMEFRAME = "30"

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

    if not os.path.exists(HISTORY_FILE):
        return {}

    try:
        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            history = json.load(f)

        if not isinstance(history, dict):
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
# 取得歷史 30 分 K
# ==================================================

def fetch_historical_30m(
    stock,
    start_date,
    end_date
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
            TIMEFRAME,

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
# 取得今天盤中 30 分 K
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
            TIMEFRAME,

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
# 整理 Fugle 30 分 K
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
# 取得本地最後一根30分K時間
# ==================================================

def get_last_local_datetime(
    local_data
):

    if not local_data:
        return None

    try:

        dates = []

        for candle in local_data:

            if "date" not in candle:
                continue

            date_time = datetime.fromisoformat(
                candle["date"]
            )

            dates.append(
                date_time
            )

        if not dates:
            return None

        return max(dates)

    except Exception:

        return None


# ==================================================
# 更新單一股票30分K
# ==================================================

def update_stock_30m(
    stock,
    history
):

    stock_key = str(stock)

    # --------------------------------------------------
    # 確保30m結構存在
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 建立本地資料索引
    # --------------------------------------------------

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
            - timedelta(days=120)
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
        # 如果本地資料不足設定的根數
        # 就重新抓較長的歷史資料補足
        # ==================================================

        if len(existing) < HISTORY_30M_BARS:

            print(
                f"{stock} 本地只有 "
                f"{len(existing)} 根，"
                f"需要補到 {HISTORY_30M_BARS} 根"
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
        # 本地已經有足夠資料
        # 但可能有幾天沒開
        # 所以仍然檢查最後日期之後是否有新的歷史K
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
    # 今天盤中資料
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

    # --------------------------------------------------
    # 合併今天盤中資料
    #
    # 如果同一根K已經存在，
    # Fugle最新資料會覆蓋舊資料
    # --------------------------------------------------

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

    if len(all_data) > HISTORY_30M_BARS:

        final_data = all_data[
            -HISTORY_30M_BARS:
        ]

    else:

        final_data = all_data

    # ==================================================
    # 寫回 history
    # ==================================================

    history[
        "30m"
    ][
        stock_key
    ] = final_data

    # ==================================================
    # 顯示結果
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
# 更新全部股票30分K
# ==================================================

def update_all_30m(
    Stocks
):

    # ==================================================
    # 檢查 API Key
    # ==================================================

    if not API_KEY:

        print(
            "找不到 FUGLE_API_KEY，"
            "無法取得30分K"
        )

        return {}

    # ==================================================
    # 讀取原本 history.json
    #
    # 原本的TWSE日K會完整保留
    # ==================================================

    history = load_history()

    # ==================================================
    # 更新所有股票
    # ==================================================

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

    # ==================================================
    # 儲存
    # ==================================================

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
# 測試
# ==================================================

if __name__ == "__main__":

    Stocks = [
        2330
    ]

    update_all_30m(
        Stocks
    )