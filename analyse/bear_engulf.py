import pandas as pd
from sty import fg, rs


OUTPUT_ID = "bear_engulf"


def tabulate(tf_series, tf_screened):
    headers = {"bear_engulf": "Bear Engulfing"}

    dict_ = {}
    for tf, v in tf_screened.items():
        if v == True:
            dict_[tf] = fg(255, 0, 0) + "Bear" + rs.all
        else:
            dict_[tf] = ""

    return [headers, dict_]


def run_bear_engulf(tf_df_dict):
    """
    Bearish Engulfing candle detection.
    No need to specify timeframes, since they are passed in tf_df_dict.
    """

    def bearish_engulfing(df):
        current = df.iloc[-1]
        previous = df.iloc[-2]
        b4_previous = df.iloc[-3]
        is_bearish_engulfing = (
            b4_previous["close"] != b4_previous["open"]
            and previous["close"] != previous["open"]
            and b4_previous["close"] > b4_previous["open"]
            and (
                b4_previous["close"] <= previous["open"]
                and b4_previous["open"] >= previous["close"]
            )
        )

        return is_bearish_engulfing

    # TODO: fix the conditions
    def bullish_engulfing(df):
        current = df.iloc[-1]
        previous = df.iloc[-2]
        b4_previous = df.iloc[-3]
        is_bullish_engulfing = (
            b4_previous["close"] != b4_previous["open"]
            and previous["close"] != previous["open"]
            and b4_previous["close"] > b4_previous["open"]
            and (
                b4_previous["close"] <= previous["open"]
                and b4_previous["open"] >= previous["close"]
            )
        )

        return is_bullish_engulfing

    screened = {}
    for tf in tf_df_dict:
        df = tf_df_dict[tf]
        ib = bearish_engulfing(df)
        screened[tf] = ib
    series = pd.DataFrame({f"bear_engulf": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"Bearish Engulfing Candle Pattern",
        "desc": f"Bearish Engulfing: search if the Bearish Engulfing Candle pattern appears the previous 2 candles.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
