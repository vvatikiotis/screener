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


def SuperTrend(df, length=10, multiplier=2):
    def filter_supertrend(df, symbol, timeframe):
        # several predicates can be defined
        log = ""

        def predicate1(df):
            last = -1
            one_b4_last = -2
            two_b4_last = -3
            three_b4_last = -4
            direction = lambda pos: df.iloc[pos][
                1
            ]  # 1 = position of direction in the series

            if (
                direction(one_b4_last) == -1
                and direction(last) == 1
                or direction(two_b4_last) == -1
                and direction(one_b4_last) == 1
                and direction(last) == 1
                or direction(three_b4_last) == -1
                and direction(two_b4_last) == 1
                and direction(one_b4_last) == 1
                and direction(last) == 1
            ):
                return "buy"
            if (
                direction(one_b4_last) == 1
                and direction(last) == -1
                or direction(two_b4_last) == 1
                and direction(one_b4_last) == -1
                and direction(last) == -1
                or direction(three_b4_last) == 1
                and direction(two_b4_last) == -1
                and direction(one_b4_last) == -1
                and direction(last) == -1
            ):
                return "sell"

            return False

        if p := predicate1(df):
            log += f"{timeframe}: {p}"

        return log

    ta_series = ta.supertrend(df["high"], df["low"], df["close"], length, multiplier)

    return [ta_series, filter_supertrend]

    #  TODO: Pine supertrend is optimised! Do it!
    #
    # def _supertrend(df):
    #     src = (df["open"] + df["close"]) / 2
    #     atr = ta.atr(df["high"], df["low"], df["close"], length=atr_period, talib=True)

    #     bot = src - multiplier * atr
    #     print(bot)
    #     bot1 = bot.shift(1) if (not bot.shift(1).isnull()) else bot
    #     # bot = max(bot, bot1) if df["close"].shift(1) > bot1 else bot
    #     # //up1 = nz(up[1], up)
    #     # up := close[1] > up1 ? math.max(up, up1) : up

    # return _supertrend


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


def output(df, symbol, timeframe, filterFn=None, filter=True):
    if filter:
        return filterFn(df, symbol, timeframe)


def run(symbol_timeframes):
    [symbol, TFs] = symbol_timeframes
    log = ""
    for timeframe in TFs:
        path = f"../symbols/csv/{symbol}_{timeframe}.csv"
        with open(path, "r") as csvfile:
            csv_dict_reader = csv.DictReader(csvfile, delimiter=",")
            data = list(csv_dict_reader)

        df = prepare_dataframe(data)
        # bang_for_buck(df, symbol, timeframe)
        [supertrend_df, filter_supertrend] = SuperTrend(df)
        next = output(supertrend_df, symbol, timeframe, filterFn=filter_supertrend)
        if next != "":
            if log.startswith(symbol):
                log += f", {next}"
            else:
                log += f"{symbol} {next}"

    return log


def main():
    set_options()

    dir = "../symbols/csv"
    filenames = [f for f in sorted(os.listdir(dir)) if f.endswith(".csv")]
    ticker_tf_group = group(filenames)
    symbol_arr_of_tfs = [[k, v] for k, v in ticker_tf_group.items()]

    # Enable it for many
    pool = Pool(8)
    logs = pool.map(run, symbol_arr_of_tfs)
    pool.close()
    pool.join()
    print(list(filter(lambda l: l != "", logs)))


def set_options():
    pd.set_option("display.max_rows", None)


def group(strings):
    groups = {}
    for s in map(lambda s: s.split(".")[0], strings):
        prefix, remainder = s.split("_")
        groups.setdefault(prefix, []).append(remainder)
    return groups


if __name__ == "__main__":
    main()
