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

# our own
import helpers
from indicators import kivan_supertrend


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
    # df["volume"] = df["volume"].astype(float)
    # df["quote_asset_volume"] = df["quote_asset_volume"].astype(float)
    # df["taker_buy_base_asset_volume"] = df["taker_buy_base_asset_volume"].astype(float)
    # df["taker_buy_quote_asset_volume"] = df["taker_buy_quote_asset_volume"].astype(
    #     float
    # )
    # df["number_of_trades"] = df["number_of_trades"].astype(int)

    return df


#
# tf_dfs_dict: { '12h': supertrend_df, '4h': supertrend_df}
#
def screen(tf_df_dict, symbol, screenFn=None, filter=True):
    p = screenFn(tf_df_dict, symbol)
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
    supertrend_output_10_2 = screen(
        symbol_tfs_dict, symbol, screenFn=screen_supertrend_fn
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
        color_and_print(results)
    else:
        print_series(results, last)


#
# [
# [{symbol: BTCUSDT, 1d: False, 12h: Buy}, {1d:timeseries, 12h: timeseries}, "indicator title"],
# [{symbol: ETHUSDT, 1d: False, 12h: Buy}, {1d:timeseries, 12h: timeseries}, "indicator title"],
# ]
#
def color_and_print(results):
    screenResults = list(map(lambda r: r[0], results))

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
            idxs = [i for i, x in enumerate(utterances) if x.startswith("Buy")]
            for i in idxs:
                utterances[i] = green + utterances[i] + reset

        if "\u25B2" in utterances:  # up arrow
            idxs = [i for i, x in enumerate(utterances) if x.startswith("\u25B2")]
            for i in idxs:
                utterances[i] = green + utterances[i] + reset

        if "\u25BC" in utterances:  # down arrow
            idxs = [i for i, x in enumerate(utterances) if x.startswith("\u25BC")]
            for i in idxs:
                utterances[i] = red + utterances[i] + reset

        # join the list back into a string and print
        return " ".join(utterances)

    headers = dict([(x, x) for x in list(screenResults[0].keys())])
    for i, entry in enumerate(screenResults):
        dir1d = results[i][1]["1d"]["SUPERTd_10_2.0"].iloc[-1]
        dir3d = results[i][1]["3d"]["SUPERTd_10_2.0"].iloc[-1]
        arrow1d = "\u25B2" if dir1d == 1 else "\u25BC"
        arrow3d = "\u25B2" if dir3d == 1 else "\u25BC"

        # print_arrow = lambda tf, arg, v: color(arrow1d) if tf == arg else ""
        for tf, v in list(entry.items()):
            if v == False:
                screenResults[i][tf] = color(arrow3d) if tf == "3d" else ""
            elif v.startswith("Buy") or v.startswith("Sell"):
                screenResults[i][tf] = (
                    color(arrow3d + " " + v) if tf == "3d" else color(v)
                )

    print(tabulate(screenResults, headers=headers, tablefmt="fancy_grid"))


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
