import os
import json
import time
import requests

from datetime import datetime, timedelta
from dotenv import load_dotenv
from fugle_marketdata import WebSocketClient


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

TIMEFRAME = "30"


HISTORY_FILE = os.path.join(

    os.path.dirname(
        os.path.abspath(__file__)
    ),

    "history.json"

)


# ==================================================
# HTTP Session
# ==================================================

session = requests.Session()


# ==================================================
# WebSocket
# ==================================================

websocket_client = None

websocket_stock = None

websocket_stocks = []

realtime_prices = {}

websocket_started = False


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

def save_history(
    history
):

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
# 取得歷史30分K
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
# 取得今天盤中30分K
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
# 舊版即時價格 HTTP API
#
# main.py 已不再使用
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
# 整理30分K
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


            result[
                date_time
            ] = {

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
# 取得本地最後一根30分K
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


            date_time = (
                datetime.fromisoformat(
                    candle["date"]
                )
            )


            if date_time.tzinfo is not None:

                date_time = (
                    date_time.replace(
                        tzinfo=None
                    )
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


    if "30m" not in history:

        history["30m"] = {}


    if not isinstance(
        history["30m"],
        dict
    ):

        history["30m"] = {}


    if stock_key not in history["30m"]:

        history["30m"][
            stock_key
        ] = []


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
    # 建立本地資料索引
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


    # ==================================================
    # 第一次沒有資料
    # ==================================================

    if last_local_datetime is None:

        print(
            f"{stock} 沒有本地30分K，"
            f"開始建立資料"
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


        for date_time, candle in (
            historical_data.items()
        ):

            existing[
                date_time
            ] = candle


    # ==================================================
    # 已有本地資料
    # ==================================================

    else:

        end_date = (
            today
            - timedelta(days=1)
        )


        # ==================================================
        # 本地不足200根
        # ==================================================

        if len(existing) < HISTORY_30M_BARS:

            start_date = (
                today
                - timedelta(days=70)
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


            for date_time, candle in (
                historical_data.items()
            ):

                existing[
                    date_time
                ] = candle


        # ==================================================
        # 本地已有足夠資料
        # ==================================================

        else:

            start_date = (
                last_local_datetime.date()
            )


            if start_date <= end_date:

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


                for date_time, candle in (
                    historical_data.items()
                ):

                    existing[
                        date_time
                    ] = candle


    # ==================================================
    # 今天盤中30分K
    # ==================================================

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


    # ==================================================
    # 合併今天資料
    #
    # 注意：
    # 啟動時仍會把今天盤中K放進本地，
    # 但後續 update_completed_30m()
    # 只會正式保留「已完成」的K。
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

    if len(all_data) > HISTORY_30M_BARS:

        final_data = all_data[
            -HISTORY_30M_BARS:
        ]

    else:

        final_data = all_data


    # ==================================================
    # 寫回
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

        f"{stock} 30分K: "
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

            f"{stock} 範圍: "
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

    if not API_KEY:

        print(
            "找不到 FUGLE_API_KEY，"
            "無法取得30分K"
        )

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
            "30分K history 已更新"
        )

    else:

        print(
            "30分K history 更新失敗"
        )


    return history


# ==================================================
# 盤中更新「已完成」30分K
#
# 只有 main.py 跨過30分鐘時呼叫
# ==================================================

def update_completed_30m(
    Stocks,
    history
):

    if not API_KEY:

        print(
            "找不到 FUGLE_API_KEY，"
            "無法更新30分K"
        )

        return history


    if "30m" not in history:

        history["30m"] = {}


    # ==================================================
    # 目前時間
    # ==================================================

    now = datetime.now()


    current_30m = now.replace(

        minute=(
            now.minute // 30
        ) * 30,

        second=0,

        microsecond=0

    )


    for stock in Stocks:

        stock_key = str(stock)


        try:

            # ==================================================
            # 取得今天目前30分K
            # ==================================================

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


            if not intraday_data:

                print(
                    f"{stock} 今天沒有30分K資料"
                )

                continue


            # ==================================================
            # 確保本地結構
            # ==================================================

            if stock_key not in history["30m"]:

                history["30m"][
                    stock_key
                ] = []


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
            # 建立索引
            # ==================================================

            existing = {}


            for candle in local_data:

                try:

                    existing[
                        candle["date"]
                    ] = candle


                except (

                    KeyError,
                    TypeError

                ):

                    continue


            # ==================================================
            # 找出「已完成」30分K
            #
            # 例如現在：
            #
            # 11:05
            #
            # current_30m = 11:00
            #
            # 10:30 < 11:00
            # => 10:30這根已完成
            #
            # 11:00 < 11:00
            # => False
            # => 11:00這根仍在形成
            # ==================================================

            completed_data = {}


            for date_time, candle in (
                intraday_data.items()
            ):

                try:

                    candle_datetime = (
                        datetime.fromisoformat(
                            date_time
                        )
                    )


                    if (
                        candle_datetime.tzinfo
                        is not None
                    ):

                        candle_datetime = (
                            candle_datetime.replace(
                                tzinfo=None
                            )
                        )


                except Exception:

                    continue


                if (
                    candle_datetime
                    < current_30m
                ):

                    completed_data[
                        date_time
                    ] = candle


            # ==================================================
            # 只把已完成K寫入本地
            # ==================================================

            added_count = 0


            for date_time, candle in (
                completed_data.items()
            ):

                if date_time not in existing:

                    added_count += 1


                # --------------------------------------------------
                # 即使已存在也更新
                #
                # 避免 Fugle 資料後續修正時，
                # 本地資料還停留在舊值
                # --------------------------------------------------

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
            # 再次保護：
            #
            # 這裡只留下「已完成」30分K
            #
            # 防止舊版 history.json 裡
            # 還存在正在形成中的K
            # ==================================================

            completed_local_data = []


            for candle in all_data:

                try:

                    candle_datetime = (
                        datetime.fromisoformat(
                            candle["date"]
                        )
                    )


                    if (
                        candle_datetime.tzinfo
                        is not None
                    ):

                        candle_datetime = (
                            candle_datetime.replace(
                                tzinfo=None
                            )
                        )


                    if (
                        candle_datetime
                        < current_30m
                    ):

                        completed_local_data.append(
                            candle
                        )


                except Exception:

                    continue


            # ==================================================
            # 保留最近200根
            # ==================================================

            if (
                len(
                    completed_local_data
                )
                >
                HISTORY_30M_BARS
            ):

                final_data = (
                    completed_local_data[
                        -HISTORY_30M_BARS:
                    ]
                )

            else:

                final_data = (
                    completed_local_data
                )


            # ==================================================
            # 寫回
            # ==================================================

            history[
                "30m"
            ][
                stock_key
            ] = final_data


            # ==================================================
            # 顯示
            # ==================================================

            if added_count > 0:

                print(

                    f"{stock} 新增 "
                    f"{added_count} 根完成30分K"

                )

            else:

                print(

                    f"{stock} 沒有新的完成30分K"

                )


        except Exception as e:

            print(

                f"{stock} "
                f"完成30分K更新失敗:",
                e

            )


    # ==================================================
    # 儲存
    # ==================================================

    if save_history(
        history
    ):

        print(
            "30分K history 已更新"
        )

    else:

        print(
            "30分K history 更新失敗"
        )


    return history


# ==================================================
# 取得歷史日K
# ==================================================

def fetch_historical_daily(
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
            "D",

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
# 更新單一股票歷史日K
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


    for item in history[stock_key]:

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
    # 最近70天
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
        f"取得 {stock} 歷史日K..."
    )


    candles = fetch_historical_daily(

        stock,

        start_date,

        end_date

    )


    # ==================================================
    # 加入資料
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
    # 保留19個交易日
    # ==================================================

    final_data = all_data[
        -HISTORY_DAILY_DAYS:
    ]


    # ==================================================
    # 寫回
    # ==================================================

    history[stock_key] = [

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

    if not API_KEY:

        print(
            "找不到 FUGLE_API_KEY，"
            "無法取得日K"
        )

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
            "日K history 已更新"
        )

    else:

        print(
            "日K history 更新失敗"
        )


    return history


# ==================================================
# WebSocket Connect
# ==================================================

def _handle_websocket_connect():

    print(
        "行情連接成功"
    )


# ==================================================
# WebSocket Disconnect
# ==================================================

def _handle_websocket_disconnect(
    code,
    message
):

    # --------------------------------------------------
    # 這裡只顯示斷線資訊
    #
    # 不在 callback 裡重新連線
    # 避免產生多重 WebSocket connection
    # --------------------------------------------------

    print(

        f"行情連接斷線: "
        f"{code}, {message}"

    )


# ==================================================
# WebSocket Error
# ==================================================

def _handle_websocket_error(
    error
):

    print(
        "行情錯誤:",
        error
    )


# ==================================================
# WebSocket Message
# ==================================================

def _handle_websocket_message(
    message
):

    try:

        msg = json.loads(
            message
        )


        event = msg.get(
            "event"
        )


        # ==================================================
        # pong
        # ==================================================

        if event == "pong":

            return


        # ==================================================
        # heartbeat
        # ==================================================

        if event == "heartbeat":

            return


        # ==================================================
        # subscribed
        # ==================================================

        if event == "subscribed":

            print(
                "WebSocket 訂閱成功"
            )

            return


        # ==================================================
        # unsubscribed
        # ==================================================

        if event == "unsubscribed":

            return


        # ==================================================
        # trades
        # ==================================================

        if (

            event == "data"

            and

            msg.get("channel")
            == "trades"

        ):

            data = msg.get(

                "data",

                {}

            )


            symbol = str(

                data.get(
                    "symbol"
                )

            )


            price = data.get(
                "price"
            )


            # --------------------------------------------------
            # 防止試撮資料被當成正常成交價
            # --------------------------------------------------

            if data.get(
                "isTrial"
            ):

                return


            if (

                symbol

                and

                price is not None

            ):

                try:

                    realtime_prices[
                        symbol
                    ] = float(
                        price
                    )


                except (

                    TypeError,
                    ValueError

                ):

                    pass


    except Exception as e:

        print(

            "WebSocket "
            "資料解析失敗:",
            e

        )


# ==================================================
# 啟動 WebSocket
# ==================================================

def start_websocket(
    Stocks
):

    global websocket_client
    global websocket_stock
    global websocket_stocks
    global websocket_started


    if not API_KEY:

        print(
            "找不到 FUGLE_API_KEY，"
            "無法啟動 WebSocket"
        )

        return False


    # ==================================================
    # 如果已經啟動
    # 不重複建立 connection
    # ==================================================

    if websocket_started:

        print(
            "WebSocket 已經啟動，"
            "不重複建立連線"
        )

        return True


    # ==================================================
    # 清理上一個可能殘留的 client
    # ==================================================

    if (

        websocket_client is not None

        or

        websocket_stock is not None

    ):

        try:

            _force_close_websocket()

        except Exception:

            pass


    websocket_stocks = [

        str(stock)

        for stock in Stocks

    ]


    realtime_prices.clear()


    # ==================================================
    # 建立新的 WebSocket Client
    # ==================================================

    websocket_client = WebSocketClient(

        api_key=API_KEY

    )


    websocket_stock = (
        websocket_client.stock
    )


    # ==================================================
    # Callback
    # ==================================================

    websocket_stock.on(

        "connect",

        _handle_websocket_connect

    )


    websocket_stock.on(

        "message",

        _handle_websocket_message

    )


    websocket_stock.on(

        "disconnect",

        _handle_websocket_disconnect

    )


    websocket_stock.on(

        "error",

        _handle_websocket_error

    )


    # ==================================================
    # 建立連線
    # ==================================================

    try:

        websocket_stock.connect()


        # ==================================================
        # 訂閱 trades
        #
        # Fugle 官方 Python SDK 支援
        # channel + symbol / symbols 的訂閱方式
        # ==================================================

        websocket_stock.subscribe({

            "channel":
                "trades",

            "symbols":
                websocket_stocks

        })


        websocket_started = True


        print(
            "Fugle WebSocket 已啟動"
        )


        print(

            "監控股票:",

            ", ".join(
                websocket_stocks
            )

        )


        return True


    except Exception as e:

        print(

            "Fugle WebSocket "
            "啟動失敗:",
            e

        )


        try:

            _force_close_websocket()

        except Exception:

            pass


        return False


# ==================================================
# 取得目前所有股票即時價格
# ==================================================

def get_realtime_prices():

    return realtime_prices.copy()


# ==================================================
# 取得單一股票即時價格
# ==================================================

def get_realtime_price(
    stock
):

    stock_key = str(
        stock
    )


    return realtime_prices.get(
        stock_key
    )


# ==================================================
# 強制關閉 WebSocket
#
# 不同版本 SDK 的底層 close 方法名稱
# 可能不同，因此做多層安全處理。
# ==================================================

def _force_close_websocket():

    global websocket_client
    global websocket_stock
    global websocket_stocks
    global websocket_started


    # ==================================================
    # 先取消訂閱
    # ==================================================

    if websocket_stock is not None:

        try:

            if websocket_stocks:

                websocket_stock.unsubscribe({

                    "channel":
                        "trades",

                    "symbols":
                        websocket_stocks

                })

                print(
                    "取消訂閱指令已送出"
                )


        except Exception as e:

            print(
                "取消訂閱失敗:",
                e
            )


    # ==================================================
    # 嘗試關閉 stock connection
    #
    # SDK 版本不同時可能提供不同方法，
    # 所以依序安全嘗試。
    # ==================================================

    closed = False


    if websocket_stock is not None:

        for method_name in (

            "disconnect",

            "close",

            "stop"

        ):

            try:

                method = getattr(

                    websocket_stock,

                    method_name,

                    None

                )


                if callable(method):

                    method()

                    closed = True

                    print(
                        f"WebSocket 已執行 "
                        f"{method_name}()"
                    )

                    break


            except Exception as e:

                print(

                    f"WebSocket "
                    f"{method_name}() 失敗:",
                    e

                )


    # ==================================================
    # 如果 stock 沒有關閉方法
    # 再嘗試 client
    # ==================================================

    if (

        not closed

        and

        websocket_client is not None

    ):

        for method_name in (

            "disconnect",

            "close",

            "stop"

        ):

            try:

                method = getattr(

                    websocket_client,

                    method_name,

                    None

                )


                if callable(method):

                    method()

                    closed = True

                    print(
                        f"WebSocket Client 已執行 "
                        f"{method_name}()"
                    )

                    break


            except Exception as e:

                print(

                    f"WebSocket Client "
                    f"{method_name}() 失敗:",
                    e

                )


    # ==================================================
    # 清理 Python 端狀態
    # ==================================================

    websocket_started = False

    websocket_stocks = []

    realtime_prices.clear()

    websocket_stock = None

    websocket_client = None


# ==================================================
# 停止 WebSocket
# ==================================================

def stop_websocket():

    global websocket_started


    # --------------------------------------------------
    # 即使狀態顯示 False，
    # 也檢查 client / stock 是否還存在。
    # --------------------------------------------------

    if (

        not websocket_started

        and

        websocket_stock is None

        and

        websocket_client is None

    ):

        return


    print(
        "正在取消 WebSocket 訂閱..."
    )


    try:

        _force_close_websocket()


    except Exception as e:

        print(

            "停止 WebSocket "
            "失敗:",
            e

        )


# ==================================================
# 測試
# ==================================================

if __name__ == "__main__":

    Stocks = [

        "2303",
        "2317",
        "2330"

    ]


    print(
        "========================================"
    )


    print(
        "Fugle WebSocket 多股票測試"
    )


    print(

        "股票:",

        ", ".join(Stocks)

    )


    print(
        "========================================"
    )


    try:

        if not start_websocket(
            Stocks
        ):

            raise RuntimeError(
                "WebSocket 啟動失敗"
            )


        print(
            "\n開始接收資料..."
        )


        print(
            "按 Ctrl+C 停止\n"
        )


        while True:

            time.sleep(1)


            prices = (
                get_realtime_prices()
            )


            for stock in Stocks:

                price = prices.get(
                    stock
                )


                if price is not None:

                    print(

                        f"{stock} | "
                        f"Price: {price}"

                    )


    except KeyboardInterrupt:

        print(
            "\n\n收到 Ctrl+C"
        )


        stop_websocket()


        print(
            "正在結束 Python..."
        )


        raise SystemExit(0)


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