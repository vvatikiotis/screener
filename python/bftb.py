import pandas_ta as ta
import pandas as pd


def tabulate(symbol, tf_series_dict, tf_screened_dict, color):
    headers = list(tf_screened_dict.keys())

    return headers


def run_btfd(tf_df_dict, amount=10000, lookback=200):
    def bang_for_buck(df, amount, lookback):
        days_in_year = 365
        l = len(df)
        bang_4_buck = (
            (amount / df["close"])
            * ta.sma(
                ta.true_range(high=df["high"], low=df["low"], close=df["close"]),
                length=lookback,
            )
            / 100
        )

        highB4B = bang_4_buck.tail(days_in_year).max()
        lowB4B = bang_4_buck.tail(days_in_year).min()

        result = pd.DataFrame(
            {
                "BtfB": [bang_4_buck.tail(1).to_string(index=False)],
                "BtfB_High": [highB4B],
                "BtfB_Low": [lowB4B],
            }
        )

        return result

    btfb = bang_for_buck(tf_df_dict["1d"], amount, lookback)

    return {
        "name": f"Bang for the Buck, amount: {amount}, lookback: {lookback}",
        "series": {"1d": btfb},
        "screened": {"1d": btfb["BtfB"]},
    }
