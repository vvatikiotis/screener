from cgi import test
import pandas as pd
from datetime import datetime, timedelta
from sty import bg, fg, rs, ef

OUTPUT_ID = "from_bar_diffs"


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
    headers = dict([(x, x) for x in range(l, 0, -1)])
    for k, v in headers.items():
        if k == 1:
            headers[k] = "Now"
        else:
            headers[k] = datetime_diff(k)

    for k, v in tf_screened.items():
        if v <= -30:
            tf_screened[k] = bg(255, 0, 0) + fg.white + str(v) + rs.all
        if v <= -15 and v > -30:
            tf_screened[k] = bg(190, 0, 0) + fg.li_grey + str(v) + rs.all
        if v <= -5 and v > -15:
            tf_screened[k] = fg(255, 0, 0) + str(v) + rs.all
        if v > -5 and v < 0:
            tf_screened[k] = ef.dim + fg(255, 0, 0) + str(v) + rs.all
        if v > 0 and v < 5:
            tf_screened[k] = ef.dim + fg(0, 255, 0) + str(v) + rs.all
        if v >= 5 and v < 15:
            tf_screened[k] = fg(0, 255, 0) + str(v) + rs.all
        if v >= 15 and v < 30:
            tf_screened[k] = bg(0, 200, 0) + fg.black + str(v) + rs.all
        if v >= 30:
            tf_screened[k] = bg(0, 255, 0) + fg.black + str(v) + rs.all

    return [headers, tf_screened]


def run_from_bar_diffs(tf_df_dict, timeframe="1d", from_bar=10):

    # percentage diff
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
    series = pd.DataFrame({f"from_bar_diffs_{timeframe}": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"Diffs, up to {from_bar} bars from today, {timeframe}",
        "desc": f"Diffs: up to {from_bar} bars from Now, in %. Diff from {from_bar}th bar to today, from {from_bar}th to yesterday, etc. Ranges: 0-5, 5-15, 15-30, 30+. ",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
