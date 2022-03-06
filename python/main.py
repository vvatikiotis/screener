import numpy as np
import pandas as pd
import csv
import pandas_ta as ta
import matplotlib.pyplot as plt
import os
import sys
import argparse
from multiprocessing import Pool
from termcolor import colored
from tabulate import tabulate

# for custom supertrend implementation
from numpy import nan as npNaN
from pandas_ta.overlap import hl2
from pandas_ta.volatility import atr
from pandas_ta.utils import get_offset, verify_series

# our own
import helpers


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

    highB4B = bang_4_buck.tail(days_in_year).max()
    lowB4B = bang_4_buck.tail(days_in_year).min()

    result = {
        "symbol": symbol,
        "results": {
            "BtfB": bang_4_buck.tail(1).to_string(index=False),
            "BtfB_High": highB4B,
            "BtfB_Low": lowB4B,
        },
    }

    return result


#
# implemented from default TV supertrend source, from docs.
# Same results as ta.supertrend
def pine_supertrend(
    high, low, close, length=None, multiplier=None, offset=None, **kwargs
):
    """Indicator: Supertrend"""
    # Validate Arguments
    length = int(length) if length and length > 0 else 7
    multiplier = float(multiplier) if multiplier and multiplier > 0 else 3.0
    high = verify_series(high, length)
    low = verify_series(low, length)
    close = verify_series(close, length)
    offset = get_offset(offset)

    if high is None or low is None or close is None:
        return

    # Calculate Results
    m = close.size
    dir_, trend = [-1] * m, [0] * m
    short, upper = [npNaN] * m, [npNaN] * m

    hl2_ = hl2(high, low)
    matr = multiplier * atr(high, low, close, length)
    upperband = hl2_ + matr
    lowerband = hl2_ - matr

    for i in range(1, m):
        prev_lowerband = 0 if np.isnan(lowerband.iloc[i - 1]) else lowerband.iloc[i - 1]
        prev_upperband = 0 if np.isnan(upperband.iloc[i - 1]) else upperband.iloc[i - 1]

        if lowerband.iloc[i] > prev_lowerband or close.iloc[i - 1] < prev_lowerband:
            lowerband.iloc[i] = lowerband.iloc[i]
        else:
            lowerband.iloc[i] = prev_lowerband

        if upperband.iloc[i] < prev_upperband or close.iloc[i - 1] > prev_upperband:
            upperband.iloc[i] = upperband.iloc[i]
        else:
            upperband.iloc[i] = prev_upperband

        prev_trend = trend[i - 1]
        # if i <= length:
        #     dir_[i] = 1
        if prev_trend == prev_upperband:
            dir_[i] = -1 if close.iloc[i] > upperband.iloc[i] else 1
        else:
            dir_[i] = 1 if close.iloc[i] < lowerband.iloc[i] else -1

        if dir_[i] == -1:
            trend[i] = short[i] = lowerband.iloc[i]
        else:
            trend[i] = upper[i] = upperband.iloc[i]

    # Prepare DataFrame to return
    _props = f"_{length}_{multiplier}"
    df = pd.DataFrame(
        {
            f"SUPERT{_props}": trend,
            f"SUPERTd{_props}": dir_,
            f"SUPERTl{_props}": short,
            f"SUPERTs{_props}": upper,
        },
        index=close.index,
    )

    df.name = f"SUPERT{_props}"
    df.category = "overlap"

    # Apply offset if needed
    if offset != 0:
        df = df.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        df.fillna(kwargs["fillna"], inplace=True)

    if "fill_method" in kwargs:
        df.fillna(method=kwargs["fill_method"], inplace=True)

    return df


# N
# implemented from Kivan-somthing TV indicator.
# Same results as ta.supertrend
# https://github.com/twopirllc/pandas-ta/issues/420
# There is a warm up period for several indicators (which have a recursive nature).
# During this period results diffr but converge slowly.
def supertrend(high, low, close, length=None, multiplier=None, offset=None, **kwargs):
    """Indicator: Supertrend"""
    # Validate Arguments
    length = int(length) if length and length > 0 else 7
    multiplier = float(multiplier) if multiplier and multiplier > 0 else 3.0
    high = verify_series(high, length)
    low = verify_series(low, length)
    close = verify_series(close, length)
    offset = get_offset(offset)

    if high is None or low is None or close is None:
        return

    # Calculate Results
    m = close.size
    dir_, trend = [-1] * m, [0] * m
    short, long = [npNaN] * m, [npNaN] * m

    hl2_ = hl2(high, low)
    matr = multiplier * atr(high, low, close, length)
    upperband = hl2_ + matr
    lowerband = hl2_ - matr

    for i in range(1, m):
        prev_lowerband = (
            lowerband.iloc[i]
            if np.isnan(lowerband.iloc[i - 1])
            else lowerband.iloc[i - 1]
        )
        prev_upperband = (
            upperband.iloc[i]
            if np.isnan(upperband.iloc[i - 1])
            else upperband.iloc[i - 1]
        )

        lowerband.iloc[i] = (
            max(lowerband.iloc[i], prev_lowerband)
            if close.iloc[i - 1] > prev_lowerband
            else lowerband.iloc[i]
        )

        upperband.iloc[i] = (
            min(upperband.iloc[i], prev_upperband)
            if close.iloc[i - 1] < prev_upperband
            else upperband.iloc[i]
        )

        prev_dir_ = dir_[i - 1]
        dir_[i] = dir_ if np.isnan(prev_dir_) else prev_dir_

        if dir_[i] == -1 and close.iloc[i] > prev_upperband:
            dir_[i] = 1
        elif dir_[i] == 1 and close.iloc[i] < prev_lowerband:
            dir_[i] = -1
        else:
            dir_[i] = dir_[i]

        if dir_[i] == -1:
            trend[i] = short[i] = upperband.iloc[i]
        else:
            trend[i] = long[i] = lowerband.iloc[i]

    # Prepare DataFrame to return
    _props = f"_{length}_{multiplier}"
    df = pd.DataFrame(
        {
            f"SUPERT{_props}": trend,
            f"SUPERTd{_props}": dir_,
            f"SUPERTl{_props}": long,
            f"SUPERTs{_props}": short,
        },
        index=close.index,
    )

    df.name = f"SUPERT{_props}"
    df.category = "overlap"

    # Apply offset if needed
    if offset != 0:
        df = df.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        df.fillna(kwargs["fillna"], inplace=True)

    if "fill_method" in kwargs:
        df.fillna(method=kwargs["fill_method"], inplace=True)

    return df


def SuperTrend(df_dict, length=10, multiplier=2):
    def screen_supertrend(tf_df_dict, symbol):
        # several predicates can be defined
        def predicate1(df):
            last = -1
            one_b4_last = -2
            two_b4_last = -3
            three_b4_last = -4
            direction = lambda pos: df.iloc[pos][
                1
            ]  # 1 = position of direction in the series

            #
            if direction(one_b4_last) == -1 and direction(last) == 1:
                return "Buy (0)"

            if (
                direction(two_b4_last) == -1
                and direction(one_b4_last) == 1
                and direction(last) == 1
            ):
                return "Buy (-1)"

            if (
                direction(three_b4_last) == -1
                and direction(two_b4_last) == 1
                and direction(one_b4_last) == 1
                and direction(last) == 1
            ):
                return "Buy (-2)"

            if direction(one_b4_last) == 1 and direction(last) == -1:
                return "Sell (0)"
            if (
                direction(two_b4_last) == 1
                and direction(one_b4_last) == -1
                and direction(last) == -1
            ):
                return "Sell (-1)"
            if (
                direction(three_b4_last) == 1
                and direction(two_b4_last) == -1
                and direction(one_b4_last) == -1
                and direction(last) == -1
            ):
                return "Sell (-2)"

            return False

        results = {}
        results["symbol"] = symbol
        for tf in tf_df_dict:
            p = predicate1(tf_df_dict[tf])
            results[tf] = p
            # if (
            #     symbol == "BTCUSDT" and tf == "1h"
            # ):  # test only this symbol and timeframe
            # print(tf_df_dict[tf].tail(50))

        return results

    symbol_tfs_dict = {}
    for tf in df_dict:
        df = df_dict[tf]
        # if tf == "4h":  # test only this timeframe
        symbol_tfs_dict[tf] = ta.supertrend(
            df["high"], df["low"], df["close"], length, multiplier
        )

    return [
        symbol_tfs_dict,
        screen_supertrend,
        f"Supertrend length: {length}, multiplier: {multiplier} ",
    ]


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


#
# tf_dfs_dict: { '12h': supertrend_df, '4h': supertrend_df}
#
def parse(tf_df_dict, symbol, parseFn=None, filter=True):
    p = parseFn(tf_df_dict, symbol)
    return p


#
# symbol_timeframes_arr: ['BTCUSDT, ['12h', '4h', ...]]
# processes one symbol in all its timeframes
#
def run(symbol_timeframes_arr):
    [symbol, TFs] = symbol_timeframes_arr
    process_dict = {}
    for timeframe in TFs:
        path = f"../symbols/csv/{symbol}_{timeframe}.csv"
        with open(path, "r") as csvfile:
            csv_dict_reader = csv.DictReader(csvfile, delimiter=",")
            data = list(csv_dict_reader)

        df = prepare_dataframe(data)
        process_dict[timeframe] = df

    # btfb = bang_for_buck(process_dict["1d"], symbol, "1d")
    # print(btfb)
    [symbol_tfs_dict, screen_supertrend_fn, title] = SuperTrend(process_dict)
    supertrend_output_10_2 = parse(
        symbol_tfs_dict, symbol, parseFn=screen_supertrend_fn
    )

    return [supertrend_output_10_2, symbol_tfs_dict, title]


def main():
    set_options()

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument(
        "-s", "--symbol", nargs="+", help="Run for symbol or list of symbols"
    )
    PARSER.add_argument(
        "-t", "--timeframe", nargs="+", help="Run for timeframe or list of timeframes"
    )
    PARSER.add_argument(
        "-ts",
        "--time-series",
        help="Show last ts rows from timeseries instead of TA results",
    )

    dir = "../symbols/csv"
    filenames = [f for f in os.listdir(dir) if f.endswith(".csv")]
    filenames.sort()  # sort works in-place
    symbol_tfs_dict = helpers.group(filenames)
    for k, v in symbol_tfs_dict.items():
        v.sort(key=helpers.sort_lambda)
        symbol_tfs_dict[k] = v
    symbol_tfs_arr = [[k, v] for k, v in symbol_tfs_dict.items()]

    parsed_arguments = PARSER.parse_args(sys.argv[1:])
    if parsed_arguments.symbol != None:
        symbol_tfs_arr = list(
            filter(lambda s: s[0] in parsed_arguments.symbol, symbol_tfs_arr)
        )
    if parsed_arguments.timeframe != None:
        tfs = parsed_arguments.timeframe
        symbol_tfs_arr = list(
            map(
                lambda s: [s[0], tfs],
                symbol_tfs_arr,
            )
        )

    # Enable it for many
    pool = Pool(8)
    results = pool.map(run, symbol_tfs_arr)
    pool.close()
    pool.join()
    output(results, parsed_arguments.time_series)


#
def output(results, last=10):
    if last == None:
        color_and_print(list(map(lambda r: r[0], results)))
    else:
        print_series(results, last)


#
#
# results = array of dicts
def color_and_print(results):
    def color(t):
        red = "\033[31m"
        green = "\033[32m"
        blue = "\033[34m"
        reset = "\033[39m"
        utterances = t.split()

        if "Sell" in utterances:
            # figure out the list-indices of occurences of "one"
            idxs = [i for i, x in enumerate(utterances) if x.startswith("Sell")]

            # modify the occurences by wrapping them in ANSI sequences
            for i in idxs:
                utterances[i] = red + utterances[i] + reset

        if "Buy" in utterances:
            # figure out the list-indices of occurences of "one"
            idxs = [i for i, x in enumerate(utterances) if x.startswith("Buy")]

            # modify the occurences by wrapping them in ANSI sequences
            for i in idxs:
                utterances[i] = green + utterances[i] + reset

        # join the list back into a string and print
        return " ".join(utterances)

    headers = dict([(x, x) for x in list(results[0].keys())])
    for i, entry in enumerate(results):
        for k, v in list(entry.items()):
            if v == False:
                results[i][k] = ""
            elif v.startswith("Buy") or v.startswith("Sell"):
                results[i][k] = color(v)

    print(tabulate(results, headers=headers, tablefmt="fancy_grid"))


#
# [
# [{symbol: BTCUSDT, 1d: False, 12h: Buy}, {1d:timeseries, 12h: timeseries}, "indicator title"],
# [{symbol: ETHUSDT, 1d: False, 12h: Buy}, {1d:timeseries, 12h: timeseries}, "indicator title"],
# ]
#
def print_series(results, last):
    for i, res in enumerate(results):
        indicator = res[2]
        print(f"\n------------ {indicator} ------------")
        print(f'\n------------ {res[0]["symbol"]} ------------')
        for tf in res[1]:
            print(f"Timeframe: {tf}")
            print(res[1][tf].tail(int(last)))


def set_options():
    pd.set_option("display.max_rows", None)


if __name__ == "__main__":
    main()
