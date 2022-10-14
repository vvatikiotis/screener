from datetime import datetime, timedelta
from sty import bg, fg, rs, ef
from pydash import omit
import pandas_ta as ta
import pandas as pd


OUTPUT_ID = "atr_tr"


def tabulate(series, dict_screened, analysis=None, timeframe=None):
    if timeframe is None:
        timeframe = "1d"
    else:
        timeframe = timeframe[0]

    def datetime_diff(k):
        today = datetime.now()
        if timeframe == "1d":
            return (today - timedelta(days=k - 1)).strftime("%m/%d")

        elif (
            timeframe == "12h"
            or timeframe == "6h"
            or timeframe == "4h"
            or timeframe == "1h"
        ):
            return (today - timedelta(hours=k * int(timeframe[:-1]))).strftime(
                "%m/%d %H:%M"
            )

    #
    def colorize_min_max(element, min_or_max):
        if min_or_max == "max":
            color = bg(0, 255, 0)
        else:
            color = bg(255, 0, 0)

        return (
            str(element[0] + "\n" + element[1] + " / ")
            + color
            + fg.black
            + str(element[2])
            + rs.all
        )

    #
    def colorize_one(element, max_natr, min_natr):
        if float(element[2]) > max_natr:
            color = fg(0, 255, 0)
        elif float(element[2]) < min_natr:
            color = fg(255, 0, 0)
        else:
            color = ""

        return (
            str(element[0] + "\n" + element[1] + " / ")
            + color
            + str(element[2])
            + rs.all
        )

    # create header text
    l = len(series)
    headers = dict([(x, x) for x in range(l, -1, -1)])
    for k, v in headers.items():
        if k == 1:
            headers[k] = "      TR\nATR / NATR Now"
        else:
            headers[k] = datetime_diff(k)

    # colorize
    key_of_max = max(
        omit(dict_screened, 1), key=(lambda k: float(dict_screened[k].split(" ")[2]))
    )
    key_of_min = min(
        omit(dict_screened, 1), key=(lambda k: float(dict_screened[k].split(" ")[2]))
    )

    # colorize all except the current candle.
    # current candle gets special color if > max or < min
    dict_result = {}
    for k, v in dict_screened.items():
        # print(k, idx_of_max, idx_of_min)
        element = v.split(" ")
        if k == 1:
            dict_result[1] = colorize_one(
                element,
                float(dict_screened[key_of_max].split(" ")[2]),
                float(dict_screened[key_of_min].split(" ")[2]),
            )
        elif k == key_of_max:
            dict_result[k] = colorize_min_max(element, "max")
        elif k == key_of_min:
            dict_result[k] = colorize_min_max(element, "min")
        else:
            dict_result[k] = str(element[0] + "\n" + element[1] + " / " + element[2])

    return [headers, dict_result]


#
def run_tr_atr(tf_df_dict, timeframe="1d", from_bar=10, lookback=14):
    """
    Calculates tr, atr and natr for given timeframe, printing from_bar number of
    candles back
    """

    # calculates atr starting from today and keeps the last 10 results
    def tr_atr(df, timeframe, from_bar):
        high = df[timeframe]["high"]
        low = df[timeframe]["low"]
        close = df[timeframe]["close"]

        tr = ta.true_range(high, low, close)
        atr = ta.atr(high, low, close, length=lookback)
        natr = ta.natr(high, low, close, length=lookback)
        results = {}

        for i in range(1, from_bar):
            _tr = round(tr.iloc[-from_bar + i], 3)
            _atr = round(atr.iloc[-from_bar + i], 3)
            _natr = round(natr.iloc[-from_bar + i], 3)
            # results[from_bar - i] = f"{_tr}\n{_atr} / {_natr}"
            results[from_bar - i] = f"{_tr} {_atr} {_natr}"

        return results

    screened = tr_atr(tf_df_dict, timeframe, from_bar)
    series = pd.DataFrame({f"tratr_{timeframe}": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"TR, ATR and NATR now and last {from_bar} values, {timeframe}, lookback {lookback} candles",
        "desc": f"tr_atr: see TR, ATR and NATR values, starting from {from_bar} previous candles.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
