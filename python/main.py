import numpy as np
import pandas as pd
import csv
import pandas_ta as ta
import matplotlib.pyplot as plt
import os
from multiprocessing import Pool
from termcolor import colored


def bang_for_buck(df, symbol, timeframe):
    amount = 10000
    days_in_year = 365
    l = len(df)
    lookback = 200 if l >= 200 else l
    bang_4_buck = (
        (amount / df["close"])
        * ta.sma(
            ta.true_range(high=df["high"], low=df["low"], close=df["close"]),
            length=lookback,
        )
        / 100
    )
    log = "%s %s: " % (symbol, timeframe)
    log += (
        "Bang for the Back: "
        + colored(bang_4_buck.tail(1).to_string(index=False), "cyan")
        + ", "
    )

    highB4B = bang_4_buck.tail(days_in_year).max()
    lowB4B = bang_4_buck.tail(days_in_year).min()
    log += "BtfB high: %s, " % (highB4B)
    log += "BtfB low: %s" % (lowB4B)
    print(log)

    return [bang_4_buck, highB4B, lowB4B]


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


def run(filename):
    path = "../symbols/csv/" + filename
    with open(path, "r") as csvfile:
        csv_dict_reader = csv.DictReader(csvfile, delimiter=",")
        data = list(csv_dict_reader)

    df = prepare_dataframe(data)
    [name, _] = filename.split(".")
    [symbol, timeframe] = name.split("_")
    bang_for_buck(df, symbol, timeframe)


def main():
    dir = "../symbols/csv"
    filenames = [f for f in os.listdir(dir) if f.endswith(".csv")]
    pool = Pool(8)

    # process only 1d
    pool.map(run, filter(lambda f: f.split(".")[0].split("_")[1] == "1d", filenames))


if __name__ == "__main__":
    main()
