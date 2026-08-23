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
# 判斷 Signal
# ==================================================

def check_signals(
    stock,
    name,
    buy1,
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


    if buy1 <= ma5:

        if not status["MA5"]:

            ma5_trigger = True

        status["MA5"] = True

    else:

        status["MA5"] = False


    # ==================================================
    # MA10
    # ==================================================

    ma10_trigger = False


    if buy1 <= ma10:

        if not status["MA10"]:

            ma10_trigger = True

        status["MA10"] = True

    else:

        status["MA10"] = False


    # ==================================================
    # MA20
    # ==================================================

    ma20_trigger = False


    if buy1 <= ma20:

        if not status["MA20"]:

            ma20_trigger = True

        status["MA20"] = True

    else:

        status["MA20"] = False


    # ==================================================
    # LB
    # ==================================================

    lb_trigger = False


    if buy1 <= lb:

        if not status["LB"]:

            lb_trigger = True

        status["LB"] = True

    else:

        status["LB"] = False


    # ==================================================
    # UB
    # ==================================================

    ub_trigger = False


    if buy1 >= ub:

        if not status["UB"]:

            ub_trigger = True

        status["UB"] = True

    else:

        status["UB"] = False


    # ==================================================
    # Level -8
    # ==================================================

    level_neg8_trigger = False


    if buy1 <= level_neg8:

        if not status["LEVEL_NEG8"]:

            level_neg8_trigger = True

        status["LEVEL_NEG8"] = True

    else:

        status["LEVEL_NEG8"] = False


    # ==================================================
    # Level +8
    # ==================================================

    level8_trigger = False


    if buy1 >= level8:

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
            f"💲: {buy1:g} \n"
            f"Ma20: {ma20:.2f}"
        )


    elif ma10_trigger:

        signals.append(

            f"[🔟日]  "
            f"{stock} {name} \n"
            f"💲: {buy1:g} \n"
            f"Ma10: {ma10:.2f}"
        )


    elif ma5_trigger:

        signals.append(

            f"[5️⃣日]  "
            f"{stock} {name} \n"
            f"💲: {buy1:g} \n"
            f"Ma5: {ma5:.2f}"
        )


    # ==================================================
    # UB
    # ==================================================

    if ub_trigger:

        signals.append(

            f"[🔼UB]  "
            f"{stock} {name} \n"
            f"💲: {buy1:g} \n"
            f"UB2.00: {ub:.2f}"
        )


    # ==================================================
    # Level +8
    # ==================================================

    if level8_trigger:

        signals.append(

            f"[位階 8️⃣]  "
            f"{stock} {name} \n"
            f"💲: {buy1:g} \n"
            f"LvL 8: {level8:.2f}"
        )


    # ==================================================
    # Level -8
    # ==================================================

    if level_neg8_trigger:

        signals.append(

            f"[位階🔻8️⃣]  "
            f"{stock} {name} \n"
            f"💲: {buy1:g} \n"
            f"LvL -8: {level_neg8:.2f}"
        )


    # ==================================================
    # LB
    # ==================================================

    if lb_trigger:

        signals.append(

            f"[🔽LB]  "
            f"{stock} {name} \n"
            f"💲: {buy1:g} \n"
            f"LB2.00: {lb:.2f}"
        )


    return signals