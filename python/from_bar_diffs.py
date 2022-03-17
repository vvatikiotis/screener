import pandas as pd

OUTPUT_ID = "from_bar_diffs"


def tabulate(series, tf_screened, color):
    l = len(series)
    headers = dict([(x, x) for x in range(l, 0, -1)])

    for k, v in tf_screened.items():
        tf_screened[k] = color(v, "red") if v < 0 else color(v, "green")

    return [headers, tf_screened]


def run_from_bar_diffs(tf_df_dict, timeframe="1d", from_bar=10):
    def perc(from_, to_):
        return ((to_ - from_) / from_) * 100

    def from_bar_diffs(df, timeframe, from_bar):
        close = df[timeframe]["close"]
        close_from = close.iloc[-from_bar]
        percs_from = {}
        for i in range(1, from_bar):
            percs_from[from_bar - i] = perc(close_from, close.iloc[-from_bar + i])

        return percs_from

    screened = from_bar_diffs(tf_df_dict, timeframe, from_bar)
    series = pd.DataFrame({"diffs": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"{from_bar} bars, {timeframe} diff",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
