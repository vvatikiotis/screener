import pandas as pd
from termcolor import colored
from datetime import datetime, timedelta

OUTPUT_ID = "prices_diff"


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
        if v <= -1.5:
            tf_screened[k] = colored(v, "red")
        if v > -1.5 and v < 0:
            tf_screened[k] = colored(v, "red", attrs=["dark"])
        if v > 0 and v < 1.5:
            tf_screened[k] = colored(v, "green", attrs=["dark"])
        if v >= 1.5:
            tf_screened[k] = colored(v, "green")

    return [headers, tf_screened]


def run_prices_diff(tf_df_dict, timeframe="1d", last_nth=10):
    def perc(from_, to_):
        return ((to_ - from_) / from_) * 100

    #
    # calclulates diffs from from_bar bar
    def prices_diff(df, timeframe, last_nth):
        close = df[timeframe]["close"]
        # close_from = close.iloc[-last_nth]
        percs_from = {}
        for i in range(1, last_nth):
            percs_from[last_nth - i] = round(
                perc(close.iloc[-last_nth + i - 1], close.iloc[-last_nth + i]), 2
            )

        return percs_from

    screened = prices_diff(tf_df_dict, timeframe, last_nth)
    series = pd.DataFrame({"diffs": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"Prices diffs, last {last_nth} bars, {timeframe}",
        "desc": f"Prices Diffs: from bar to bar, in %. Dim colors are less than 1.5% difference.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
