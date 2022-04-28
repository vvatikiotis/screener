import pandas as pd
from sty import fg, rs


OUTPUT_ID = "bear_engolf"


def tabulate(tf_series, tf_screened):
    headers = {"bear_engolf": "Bear Engolfing"}

    dict_ = {}
    for tf, v in tf_screened.items():
        if v == True:
            dict_[tf] = fg(255, 0, 0) + "Bear" + rs.all
        else:
            dict_[tf] = ""

    return [headers, dict_]


def run_bear_engolf(tf_df_dict):
    """
    Bearish Engolfing candle detection.
    No need to specify timeframes, since they are passed in tf_df_dict.
    """

    def bearish_engolfing(df):
        current = df.iloc[-1]
        previous = df.iloc[-2]
        b4_previous = df.iloc[-3]
        is_bearish_engolfing = (
            b4_previous["high"] <= previous["high"]
            and b4_previous["low"] >= previous["low"]
        )

        return is_bearish_engolfing

    screened = {}
    for tf in tf_df_dict:
        df = tf_df_dict[tf]
        ib = bearish_engolfing(df)
        screened[tf] = ib
    series = pd.DataFrame({f"bear_engolf": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    return {
        "name": f"Bearish Engolfing Candle Pattern",
        "desc": f"Bearish Engolfing: search if the Bearish Engolfing Candle pattern appears the previous 2 candles.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
