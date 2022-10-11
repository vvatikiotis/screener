from datetime import datetime, timedelta
import pandas_ta as ta
import pandas as pd

OUTPUT_ID = "atr_tr"


def tabulate(series, tf_screened, analysis=None, timeframe=None):
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

    l = len(series)
    headers = dict([(x, x) for x in range(l, -1, -1)])
    for k, v in headers.items():
        if k == 1:
            headers[k] = "      TR\nATR / NATR Now"
        else:
            headers[k] = datetime_diff(k)

    return [headers, tf_screened]


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
            results[from_bar - i] = f"{_tr}\n{_atr} / {_natr}"

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
