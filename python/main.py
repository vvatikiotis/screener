import numpy as np
import pandas as pd
import csv
import pandas_ta as ta
import matplotlib.pyplot as plt
import datetime

# amount=input(10000, "Amount in trading account")
# alen=input(200, "Lookback ATR Period")
# days=input(defval=365, title="Trading days in a year (for crypto)")

# // BFTB = amount / close * ta.sma(ta.atr(1), alen) / 100 === amount / close * ta.sma(ta.tr(false), alen) / 100
# BFTB = amount / close * ta.sma(ta.tr(false), alen) / 100
# YearHigh = ta.highest(BFTB, days)
# YearLow = ta.lowest(BFTB, days)


def bang_for_buck(df):
    amount = 10000
    days_in_year = 365
    lookback = 200
    bang_4_buck = (
        (amount / df["close"])
        * ta.sma(
            ta.true_range(high=df["high"], low=df["low"], close=df["close"]),
            length=lookback,
        )
        / 100
    )
    print("Bang for the Back: %s" % (bang_4_buck.tail(1).to_string(index=False)))

    highB4B = bang_4_buck.tail(days_in_year).max()
    lowB4B = bang_4_buck.tail(days_in_year).min()
    print("BtfB high: %s" % (highB4B))
    print("BtfB low: %s" % (lowB4B))
    # // BFTB = amount / close * ta.sma(ta.atr(1), alen) / 100 === amount / close * ta.sma(ta.tr(false), alen) / 100
    # YearHigh = ta.highest(BFTB, days)
    # YearLow = ta.lowest(BFTB, days)

    plt.figure()
    # df.plot(x=df["close_time"], y=bang_4_buck)


def prepare_dataframe(data):
    df = pd.DataFrame(data)
    df["open_time"] = pd.to_datetime(arg=df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(arg=df["close_time"], unit="ms")
    df["open"] = df["open"].astype(float)
    df["close"] = df["close"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["volume"] = df["volume"].astype(float)
    df["quote_asset_volume"] = df["quote_asset_volume"].astype(float)
    df["taker_buy_base_asset_volume"] = df["taker_buy_base_asset_volume"].astype(float)
    df["taker_buy_quote_asset_volume"] = df["taker_buy_quote_asset_volume"].astype(
        float
    )
    df["number_of_trades"] = df["number_of_trades"].astype(int)
    return df


def main():
    file = "../symbols/csv/BTCUSDT_1d.csv"
    with open(file, "r") as csvfile:
        csv_dict_reader = csv.DictReader(csvfile, delimiter=",")
        data = list(csv_dict_reader)
    # headers = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume",
    #            "number_of_trades", "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"]
    # dtypes = {
    #     "open_time": str, "open": 'float', "high": float, "low": float, "close": float, "volume": int, "close_time": str, "quote_asset_volume": int, "number_of_trades": int, "taker_buy_base_asset_volume": int, "taker_buy_quote_asset_volume": int, "ignore": int
    # }
    # parse_dates = ['open_time', 'close_time']
    # data = pd.read_csv(file, sep=',', header=None,
    #                    names=headers, dtype=dtypes, parse_dates=parse_dates)
    df = prepare_dataframe(data)
    bang_for_buck(df)


if __name__ == "__main__":
    main()
