import pandas as pd
from termcolor import colored
from datetime import datetime, timedelta

OUTPUT_ID = "from_bar_diffs"


def tabulate(series, tf_screened):
    l = len(series)
    headers = dict([(x, x) for x in range(l, 0, -1)])
    today = datetime.now()
    for k, v in headers.items():
        if k == 1:
            headers[k] = "Today"
        else:
            headers[k] = (today - timedelta(days=k - 1)).strftime("%m/%d")

    for k, v in tf_screened.items():
        if v <= -3:
            tf_screened[k] = colored(v, "red")
        if v > -3 and v < 0:
            tf_screened[k] = colored(v, "red", attrs=["dark"])
        if v > 0 and v < 3:
            tf_screened[k] = colored(v, "green", attrs=["dark"])
        if v >= 3:
            tf_screened[k] = colored(v, "green")

    return [headers, tf_screened]


def run_from_bar_diffs(tf_df_dict, timeframe="1d", from_bar=10):
    def perc(from_, to_):
        return ((to_ - from_) / from_) * 100

    #
    # calclulates diffs from from_bar bar
    def from_bar_diffs(df, timeframe, from_bar):
        close = df[timeframe]["close"]
        close_from = close.iloc[-from_bar]
        percs_from = {}
        for i in range(1, from_bar):
            percs_from[from_bar - i] = round(
                perc(close_from, close.iloc[-from_bar + i]), 2
            )

        return percs_from

    screened = from_bar_diffs(tf_df_dict, timeframe, from_bar)
    series = pd.DataFrame({"diffs": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"Diffs, up to {from_bar} bars from today, {timeframe}",
        "desc": f"Diffs: up to {from_bar} bars from today, in %. Diff from {from_bar}th bar to day, from {from_bar}th to yesterday, etc.Dim colors are less than 3% difference.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
