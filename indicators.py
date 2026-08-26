import math


# ==================================================
# 計算 MA / BBand / Level
# ==================================================

def calculate_indicators(
    history_prices,
    price
):

    # ==================================================
    # MA5
    # ==================================================

    ma5 = (

        sum(
            history_prices[-4:]
            + [price]
        )

        / 5
    )


    # ==================================================
    # MA10
    # ==================================================

    ma10 = (

        sum(
            history_prices[-9:]
            + [price]
        )

        / 10
    )


    # ==================================================
    # MA20
    # ==================================================

    prices20 = (

        history_prices[-19:]
        + [price]
    )


    ma20 = (

        sum(prices20)
        / 20
    )


    # ==================================================
    # BBand
    # ==================================================

    variance = (

        sum(

            (x - ma20) ** 2

            for x in prices20

        )

        / 20
    )


    std20 = math.sqrt(
        variance
    )


    ub = (
        ma20
        + 2 * std20
    )


    lb = (
        ma20
        - 2 * std20
    )


    # ==================================================
    # Level
    # ==================================================

    level_step_up = (

        (ub - ma20)
        / 10
    )


    level_step_down = (

        (ma20 - lb)
        / 10
    )


    level8 = (

        ma20
        + level_step_up * 8
    )


    level_neg8 = (

        ma20
        - level_step_down * 8
    )


    return {

        "ma5": ma5,

        "ma10": ma10,

        "ma20": ma20,

        "ub": ub,

        "lb": lb,

        "level8": level8,

        "level_neg8": level_neg8
    }

# ==================================================
# EMA23
# ==================================================

def calculate_ema23(
    closes
):

    if len(closes) < 23:
        return None

    alpha = 2 / (23 + 1)

    # 前23根收盤價的 SMA
    ema = sum(
        closes[:23]
    ) / 23

    # 從第24根開始計算 EMA
    for close in closes[23:]:

        ema = (
            close * alpha
            + ema * (1 - alpha)
        )

    return ema

# ==================================================
# 目前價格計算 EMA23
# ==================================================

def calculate_current_ema23(
    completed_closes,
    current_price
):

    if len(completed_closes) < 23:
        return None

    # 先用完整歷史資料計算 EMA
    ema23 = calculate_ema23(
        completed_closes
    )

    if ema23 is None:
        return None

    # EMA23 的 alpha
    alpha = 2 / (23 + 1)

    # 使用目前價格更新 EMA
    current_ema23 = (
        current_price * alpha
        + ema23 * (1 - alpha)
    )

    return current_ema23
# ==================================================
# EMA23 ±2% 濾網
# ==================================================

def calculate_ema_filter(
    ema23
):

    if ema23 is None:
        return None, None

    ema_up = ema23 * 1.02
    ema_dw = ema23 * 0.98

    return ema_up, ema_dw
# ==================================================
# 判斷 Signal
# ==================================================

def check_signals(
    stock,
    name,
    price,
    ma_data,
    status
):

    ma5 = ma_data["ma5"]

    ma10 = ma_data["ma10"]

    ma20 = ma_data["ma20"]

    ub = ma_data["ub"]

    lb = ma_data["lb"]

    level8 = ma_data["level8"]

    level_neg8 = ma_data[
        "level_neg8"
    ]


    # ==================================================
    # MA5
    # ==================================================

    ma5_trigger = False


    if price <= ma5:

        if not status["MA5"]:

            ma5_trigger = True

        status["MA5"] = True

    else:

        status["MA5"] = False


    # ==================================================
    # MA10
    # ==================================================

    ma10_trigger = False


    if price <= ma10:

        if not status["MA10"]:

            ma10_trigger = True

        status["MA10"] = True

    else:

        status["MA10"] = False


    # ==================================================
    # MA20
    # ==================================================

    ma20_trigger = False


    if price <= ma20:

        if not status["MA20"]:

            ma20_trigger = True

        status["MA20"] = True

    else:

        status["MA20"] = False


    # ==================================================
    # LB
    # ==================================================

    lb_trigger = False


    if price <= lb:

        if not status["LB"]:

            lb_trigger = True

        status["LB"] = True

    else:

        status["LB"] = False


    # ==================================================
    # UB
    # ==================================================

    ub_trigger = False


    if price >= ub:

        if not status["UB"]:

            ub_trigger = True

        status["UB"] = True

    else:

        status["UB"] = False


    # ==================================================
    # Level -8
    # ==================================================

    level_neg8_trigger = False


    if price <= level_neg8:

        if not status["LEVEL_NEG8"]:

            level_neg8_trigger = True

        status["LEVEL_NEG8"] = True

    else:

        status["LEVEL_NEG8"] = False


    # ==================================================
    # Level +8
    # ==================================================

    level8_trigger = False


    if price >= level8:

        if not status["LEVEL_8"]:

            level8_trigger = True

        status["LEVEL_8"] = True

    else:

        status["LEVEL_8"] = False


    # ==================================================
    # Signal
    # ==================================================

    signals = []


    # ==================================================
    # MA Signal
    # ==================================================

    if ma20_trigger:

        signals.append(

            f"[🈷️線]  "
            f"{stock} {name} \n"
            f"💲: {price:g} \n"
            f"Ma20: {ma20:.2f}"
        )


    elif ma10_trigger:

        signals.append(

            f"[🔟日]  "
            f"{stock} {name} \n"
            f"💲: {price:g} \n"
            f"Ma10: {ma10:.2f}"
        )


    elif ma5_trigger:

        signals.append(

            f"[5️⃣日]  "
            f"{stock} {name} \n"
            f"💲: {price:g} \n"
            f"Ma5: {ma5:.2f}"
        )


    # ==================================================
    # UB
    # ==================================================

    if ub_trigger:

        signals.append(

            f"[🔼UB]  "
            f"{stock} {name} \n"
            f"💲: {price:g} \n"
            f"UB2.00: {ub:.2f}"
        )


    # ==================================================
    # Level +8
    # ==================================================

    if level8_trigger:

        signals.append(

            f"[位階 8️⃣]  "
            f"{stock} {name} \n"
            f"💲: {price:g} \n"
            f"LvL 8: {level8:.2f}"
        )


    # ==================================================
    # Level -8
    # ==================================================

    if level_neg8_trigger:

        signals.append(

            f"[位階🔻8️⃣]  "
            f"{stock} {name} \n"
            f"💲: {price:g} \n"
            f"LvL -8: {level_neg8:.2f}"
        )


    # ==================================================
    # LB
    # ==================================================

    if lb_trigger:

        signals.append(

            f"[🔽LB]  "
            f"{stock} {name} \n"
            f"💲: {price:g} \n"
            f"LB2.00: {lb:.2f}"
        )


    return signals