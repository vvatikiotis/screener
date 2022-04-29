import pandas as pd
from datetime import datetime, timedelta
from sty import bg, fg, rs, ef

OUTPUT_ID = "prices_diff"


def tabulate(series, tf_screened, analysis=None):
    l = len(series)
    headers = dict([(x, x) for x in range(l, 0, -1)])
    today = datetime.now()
    timeframe = series.columns.values[0].split("_")[1]
    # if 'h' in timeframe:

    for k, v in headers.items():
        if k == 1:
            headers[k] = "Now"
        else:
            headers[k] = (today - timedelta(days=k - 1)).strftime("%m/%d")

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
    series = pd.DataFrame({f"prices_diffs_{timeframe}": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"Prices diffs, last {last_nth} bars, {timeframe}",
        "desc": f"Prices Diffs: from bar to bar, in %. Ranges: 0-5, 5-15, 15-30, 30+.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
