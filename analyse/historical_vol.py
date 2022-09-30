import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sty import bg, fg, rs, ef
import math

OUTPUT_ID = "historical_vol"


def tabulate(series, tf_screened, analysis=None):
    l = len(series)
    headers = dict([(x, x) for x in range(l, 0, -1)])
    today = datetime.now()
    # timeframe = series.columns.values[0].split("_")[1]
    # if 'h' in timeframe:

    for k, v in headers.items():
        if k == 1:
            headers[k] = "CV Now"
        elif k == 2:
            headers[k] = "Now"
        else:
            headers[k] = (today - timedelta(days=k - 1)).strftime("%m/%d")

    # NOTE: maybe we need this
    # for k, v in tf_screened.items():
    #     if v <= 0.0125:
    #         tf_screened[k] = bg(255, 0, 0) + fg.white + str(v) + rs.all
    #     if v <= 0.025 and v > 0.0125:
    #         tf_screened[k] = bg(190, 0, 0) + fg.li_grey + str(v) + rs.all
    #     if v <= 0.03755 and v > 0.025:
    #         tf_screened[k] = fg(255, 0, 0) + str(v) + rs.all
    #     if v > 0.0375 and v < 0.05:
    #         tf_screened[k] = ef.dim + fg(255, 0, 0) + str(v) + rs.all
    #     if v > 0.05 and v < 0.0625:
    #         tf_screened[k] = ef.dim + fg(0, 255, 0) + str(v) + rs.all
    #     if v >= 0.0625 and v < 0.075:
    #         tf_screened[k] = fg(0, 255, 0) + str(v) + rs.all
    #     if v >= 0.075 and v < 0.09:
    #         tf_screened[k] = bg(0, 200, 0) + fg.black + str(v) + rs.all
    #     if v >= 0.09:
    #         tf_screened[k] = bg(0, 255, 0) + fg.black + str(v) + rs.all

    return [headers, tf_screened]


def run_historical_vol(tf_df_dict, rollback=21, timeframe="1d", from_bar=10):
    #
    def calculate_historical_vol(tf_sources_dict):
        """
        We calculate historical vol based on the following
        https://www.youtube.com/watch?v=lcPZcFZXDNA
        """

        series_dict = {}
        df = tf_sources_dict[timeframe]
        df["pct_change"] = np.log1p(df.close.pct_change())
        df_log_pct = df["pct_change"].iloc[1:]

        vol = df_log_pct.rolling(rollback).std().dropna()

        # calculate the mean of only last year
        mean = df["close"].iloc[-rollback:].mean()

        annual = 365  # for crypto only
        per = (
            1
            if (
                timeframe == "1d"
                or timeframe == "12h"
                or timeframe == "6h"
                or timeframe == "4h"
                or timeframe == "1h"
            )
            else 7
        )
        annualised = math.sqrt(annual / per)
        for i in range(1, from_bar):
            # formula from TV vanilla HV indicator
            hist_vol = 100 * vol.iloc[-from_bar + i] * annualised

            # +1 because we want to store CV in the last column
            series_dict[from_bar + 1 - i] = hist_vol

        # This is Coefficiency of Variation
        # https://seekingalpha.com/article/4079870-coefficient-of-variation-better-metric-to-compare-volatility
        series_dict[1] = 100 * vol.iloc[-1] / mean

        return series_dict

    screened = calculate_historical_vol(tf_df_dict)
    series = pd.DataFrame({f"hist_vol_{timeframe}": screened})

    return {
        "name": f"Historical Vol, last {from_bar-1} bars",
        "desc": f"Historical Vol: showing last {from_bar-1} bars, rolling window: {rollback} bars. ",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
