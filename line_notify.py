import requests
from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID

# ==================================================
# LINE 設定
# ==================================================


LINE_URL = (
    "https://api.line.me/v2/bot/message/push"
)


# ==================================================
# LINE 通知
# ==================================================

def send_line(message):

    if (
        not LINE_CHANNEL_ACCESS_TOKEN
        or not LINE_USER_ID
    ):
        return

    headers = {
        "Authorization":
            f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",

        "Content-Type":
            "application/json"
    }

    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:

        response = requests.post(
            LINE_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:

            print(
                "LINE ERROR:",
                response.status_code,
                response.text
            )

    except Exception as e:

        print(
            "LINE ERROR:",
            e
        )

text= (
    f"[TEST] "
    f"3244 甲乙丙 \n"
    f"Buy: 123    |    "
    f"Sell: 123 \n"
    f"Lvl: 321"
    )
text1= (
    f"[🈷️線]  "
    f"2330 台積電 \n"
    f"💲: 1223 \n"
    f"LvL 8: 321"
    )
send_line(text)
# send_line(text1)