import pandas_ta as ta
from test_indicators import kivan_supertrend

OUTPUT_ID = "supertrend"

#
def color(t):
    red = "\033[31m"
    green = "\033[32m"
    blue = "\033[34m"
    reset = "\033[39m"
    utterances = t.split()

    if "Sell" in utterances:
        # figure out the list-indices of occurences of "one"
        idxs = [i for i, x in enumerate(utterances) if x.startswith("Sell")]

        # modify the occurences by wrapping them in ANSI sequences
        for i in idxs:
            utterances[i] = red + utterances[i] + reset

    if "Buy" in utterances:
        idxs = [i for i, x in enumerate(utterances) if x.startswith("Buy")]
        for i in idxs:
            utterances[i] = green + utterances[i] + reset

    if "\u25B2" in utterances:  # up arrow
        idxs = [i for i, x in enumerate(utterances) if x.startswith("\u25B2")]
        for i in idxs:
            utterances[i] = green + utterances[i] + reset

    if "\u25BC" in utterances:  # down arrow
        idxs = [i for i, x in enumerate(utterances) if x.startswith("\u25BC")]
        for i in idxs:
            utterances[i] = red + utterances[i] + reset

    # join the list back into a string and print
    return " ".join(utterances)


# this depends on the data structures shape we used to store our source data and results
def tabulate(tf_series_dict, tf_screened_dict):
    headers = dict([(x, x) for x in list(tf_screened_dict.keys())])

    arrow3d = ""
    if "3d" in tf_series_dict:
        headers["3d"] = "direction - 3d"
        # dir1d = tf_series_dict["1d"]["SUPERTd_10_2.0"].iloc[-1]
        dir3d = tf_series_dict["3d"]["SUPERTd_10_2.0"].iloc[-1]
        # arrow1d = "\u25B2" if dir1d == 1 else "\u25BC"
        arrow3d = "\u25B2" if dir3d == 1 else "\u25BC"

    dict_ = {}
    for tf, v in tf_screened_dict.items():
        if v == False:
            dict_[tf] = color(arrow3d) if tf == "3d" else ""
        elif v.startswith("Buy") or v.startswith("Sell"):
            dict_[tf] = color(arrow3d + " -  " + v) if tf == "3d" else color(v)

    return [headers, dict_]


def run_supertrend(tf_df_dict, length=10, multiplier=2):
    #
    def screen_supertrend(tf_df_dict):
        # several predicates can be defined
        def predicate1(df):
            last = -1
            one_b4_last = -2
            two_b4_last = -3
            three_b4_last = -4
            direction = lambda pos: df.iloc[pos][
                1
            ]  # 1 = position of direction in the series

            #
            if direction(one_b4_last) == -1 and direction(last) == 1:
                return "Buy (0)"

            if (
                direction(two_b4_last) == -1
                and direction(one_b4_last) == 1
                and direction(last) == 1
            ):
                return "Buy (-1)"

            if (
                direction(three_b4_last) == -1
                and direction(two_b4_last) == 1
                and direction(one_b4_last) == 1
                and direction(last) == 1
            ):
                return "Buy (-2)"

            if direction(one_b4_last) == 1 and direction(last) == -1:
                return "Sell (0)"
            if (
                direction(two_b4_last) == 1
                and direction(one_b4_last) == -1
                and direction(last) == -1
            ):
                return "Sell (-1)"
            if (
                direction(three_b4_last) == 1
                and direction(two_b4_last) == -1
                and direction(one_b4_last) == -1
                and direction(last) == -1
            ):
                return "Sell (-2)"

            return False

        results = {}
        for tf in tf_df_dict:
            p = predicate1(tf_df_dict[tf])
            results[tf] = p

        return results

    #
    def SuperTrend(tf_sources_dict, length=10, multiplier=2):
        tf_st_series_dict = {}
        for tf in tf_sources_dict:
            df = tf_sources_dict[tf]
            tf_st_series_dict[tf] = ta.supertrend(
                df["high"], df["low"], df["close"], length, multiplier
            )

        return tf_st_series_dict

    series = SuperTrend(tf_df_dict, length, multiplier)
    screened = screen_supertrend(series)

    return {
        "name": f"Supertrend, length: {length}, multiplier: {multiplier} ",
        "desc": f"Supertrend: search for change of direction the last 3 candles.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
