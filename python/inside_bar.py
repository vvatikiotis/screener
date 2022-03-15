import pandas as pd
import helpers

OUTPUT_ID = "inside_bar"


def tabulate(series, tf_screened, color):
    headers = {"inside": "Inside Bar"}

    text = ""
    for k, v in tf_screened.items():
        text += f"{k}: {v}" if v == True else ""

    return [
        headers,
        {"inside": f"{text}"},
    ]


# TODO: Need to check if user excludes 1w and 3d in the analysis.
# This should probably be done in main.py
def run_inside_bar(tf_df_dict, timeframes=["1w", "3d"]):
    def inside_bar(df):
        current = df.iloc[-1]
        previous = df.iloc[-2]
        starting = df.iloc[-3]
        is_inside_bar = (
            starting["high"] > previous["high"] and starting["low"] < previous["low"]
        )

        return is_inside_bar

    series_dict = {}
    screened = {}
    for tf in timeframes:
        df = tf_df_dict[tf]
        ib = inside_bar(df)
        series_dict[tf] = [ib]
        screened[tf] = ib

    series = pd.DataFrame(series_dict).tail(1)

    # series MUST be a Dataframe
    # screend MUST be a dict
    return {
        "name": f"Inside Bar - {timeframes}",
        "series": series,
        "screened": screened,
        "output_id": OUTPUT_ID,
    }
