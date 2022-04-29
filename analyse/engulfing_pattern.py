import pandas as pd
from sty import fg, rs


OUTPUT_ID = "engulfing_pattern"


def tabulate(tf_series, tf_screened, analysis):
    string = "Bearish" if analysis == "bear_engulf" else "Bullish"
    first_str = "bear" if analysis == "bear_engulf" else "bull"
    color = fg(255, 0, 0) if analysis == "bear_engulf" else fg(0, 255, 0)
    headers = {f"{first_str}_engulf": f"{string} Engulfing"}

    dict_ = {}
    for tf, v in tf_screened.items():
        if v == True:
            dict_[tf] = color + string + rs.all
        else:
            dict_[tf] = ""

    return [headers, dict_]


def run_engulfing_pattern(tf_df_dict, type="bear"):
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

    def bullish_engulfing(df):
        current = df.iloc[-1]
        previous = df.iloc[-2]
        b4_previous = df.iloc[-3]
        is_bullish_engulfing = (
            b4_previous["close"] != b4_previous["open"]
            and previous["close"] != previous["open"]
            and b4_previous["open"] > b4_previous["close"]
            and (
                b4_previous["close"] >= previous["open"]
                and b4_previous["open"] <= previous["close"]
            )
        )

        return is_bullish_engulfing

    screened = {}
    for tf in tf_df_dict:
        df = tf_df_dict[tf]
        ib = bearish_engulfing(df) if type == "bear" else bullish_engulfing(df)
        screened[tf] = ib
    series = pd.DataFrame({f"{type}_engulf": screened})

    # series MUST be a Dataframe
    # screened MUST be a dict
    string = "Bearish" if type == "bear" else "Bullish"
    return {
        "name": f"{string} Engulfing Candle Pattern",
        "desc": f"{string} Engulfing: search if the {string} Engulfing Candle pattern appears the previous 2 candles.",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
