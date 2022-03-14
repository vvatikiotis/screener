import pandas_ta as ta
import pandas as pd

OUTPUT_ID = "bftb"


def tabulate(series, tf_screened, color):
    headers = {"BftB": "BftB (low - high)"}

    high = "{:.2f}".format(series["BtfB_High"].iloc[-1])
    low = "{:.2f}".format(series["BtfB_Low"].iloc[-1])
    bftb = "{:.2f}".format(series["BtfB"].iloc[-1])

    return [
        headers,
        {"BftB": f"{bftb} ({low} - {high})"},
    ]


def run_btfd(tf_df_dict, amount=10000, lookback=200):
    def bang_for_buck(df, amount, lookback):
        days_in_year = 365
        df_len = len(df)
        lookb = lookback if df_len >= 200 else df_len

        bang_4_buck = (
            (amount / df["close"])
            * ta.sma(
                ta.true_range(high=df["high"], low=df["low"], close=df["close"]),
                length=lookb,
            )
            / 100
        )

        bftb = bang_4_buck.tail(1)
        highB4B = bang_4_buck.tail(days_in_year).max()
        lowB4B = bang_4_buck.tail(days_in_year).min()

        result = pd.DataFrame(
            {
                "BtfB": bftb,
                "BtfB_High": highB4B,
                "BtfB_Low": lowB4B,
            }
        )

        return result

    btfb = bang_for_buck(tf_df_dict["1d"], amount, lookback)

    return {
        "name": f"Bang for the Buck, amount: {amount}, lookback: {lookback}",
        "series": btfb,
        "screened": btfb["BtfB"],
        "output_id": OUTPUT_ID,
    }
