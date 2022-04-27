import pandas_ta as ta
import pandas as pd
from termcolor import colored
from datetime import datetime, timedelta

OUTPUT_ID = "atr_tr"


def tabulate(series, tf_screened):
    l = len(series)
    headers = dict([(x, x) for x in range(l, -1, -1)])
    today = datetime.now()
    for k, v in headers.items():
        if k == 0:
            headers[k] = "TR now"
        elif k == 1:
            headers[k] = "ATR Today (open)"
        else:
            headers[k] = (today - timedelta(days=k - 1)).strftime("%m/%d")

    for k, v in tf_screened.items():
        if v < float(tf_screened[0] - 1):
            tf_screened[k] = colored(v, "red")
        if v > float(tf_screened[0] + 1):
            tf_screened[k] = colored(v, "green")

    return [headers, tf_screened]


def run_tr_atr(tf_df_dict, timeframe="1d", from_bar=10):
    def perc(from_, to_):
        return ((to_ - from_) / from_) * 100

    # calculates atr starting from today and keeps the last 10 results
    def tr_atr(df, timeframe, from_bar):
        high = df[timeframe]["high"]
        low = df[timeframe]["low"]
        close = df[timeframe]["close"]

        tr = ta.true_range(high, low, close)
        atr = ta.atr(high, low, close, length=14)
        tr_atrs = {}

        for i in range(1, from_bar):
            tr_atrs[from_bar - i] = round(
                (atr.iloc[-from_bar + i] / close.iloc[-from_bar + i]) * 100, 2
            )
        tr_atrs[0] = round((tr.iloc[-1] / close.iloc[-1]) * 100, 2)

        return tr_atrs

    screened = tr_atr(tf_df_dict, timeframe, from_bar)
    series = pd.DataFrame({f"tratr_{timeframe}": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"Today % TR and last {from_bar} ATR14 % values, {timeframe}",
        "desc": f"tr_atr: Compare today's TR with the latest ATR value, the previous ATR value, etc. In %. If -1 < diff < 1 color stays the same.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
