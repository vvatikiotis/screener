import numpy as np
import pandas as pd
import csv
import matplotlib.pyplot as plt
import os
import sys
import argparse
from multiprocessing import Pool
from termcolor import colored
from tabulate import tabulate

# our own
import helpers
import supertrend
import bftb


#
#
#
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
# tf_df_dict: {'1d': df1, '12h': df2,...}
#
def run_indicators(tf_df_dict):
    bftb_dict = bftb.run_btfd(tf_df_dict)
    st_dict = supertrend.run_supertrend(tf_df_dict)

    return {"indicator1": st_dict, "indicator2": bftb_dict}


#
# symbol_timeframes_arr: ['BTCUSDT, ['12h', '4h', ...]]
# processes one symbol in all its timeframes
#
def run(symbol_timeframes_arr):
    [symbol, TFs] = symbol_timeframes_arr
    tf_df_dict = {}
    for timeframe in TFs:
        path = f"../symbols/csv/{symbol}_{timeframe}.csv"
        with open(path, "r") as csvfile:
            csv_dict_reader = csv.DictReader(csvfile, delimiter=",")
            data = list(csv_dict_reader)

        df = prepare_dataframe(data)
        tf_df_dict[timeframe] = df

    results = run_indicators(tf_df_dict)

    return {"symbol": {"name": symbol}, **results}


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
    table = []
    headers = {
        "symbol": "Symbol",
        "1w": "1w",
        "3d": "3d",
        "1d": "1d",
        "12h": "12h",
        "6h": "6h",
        "4h": "4h",
        "1h": "1h",
    }
    for i, symbol_dict in enumerate(results):
        series = symbol_dict["indicator1"]["series"]
        dir1d = series["1d"]["SUPERTd_10_2.0"].iloc[-1]
        dir3d = series["3d"]["SUPERTd_10_2.0"].iloc[-1]
        arrow1d = "\u25B2" if dir1d == 1 else "\u25BC"
        arrow3d = "\u25B2" if dir3d == 1 else "\u25BC"
        table.append({"symbol": symbol_dict["symbol"]["name"]})

        screened = symbol_dict["indicator1"]["screened"]
        for tf, v in screened.items():
            if v == False:
                table[i][tf] = helpers.color(arrow3d) if tf == "3d" else ""
            elif v.startswith("Buy") or v.startswith("Sell"):
                table[i][tf] = (
                    helpers.color(arrow3d + " " + v) if tf == "3d" else helpers.color(v)
                )

    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))


#
# [
# {symbol: {name: BTCUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# {symbol: {name: ATOMUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# ]
#
def print_series(results, last):
    for i, symbol_dict in enumerate(results):  # iterate per symbol
        symbol = symbol_dict["symbol"]["name"]
        print(f"\n\n----------------- ", colored(symbol, "green"), " -----------------")

        for k, indicator in symbol_dict.items():  # iterate per indicator
            if k.startswith("indicator") == True:
                indicator_name = indicator["name"]
                indicator_series = indicator["series"]
                print(f"\n------------ {indicator_name} ------------")
                for tf, series in indicator_series.items():
                    print(f"Timeframe: {tf}")
                    print(series.tail(int(last)))


def set_options():
    pd.set_option("display.max_rows", None)


if __name__ == "__main__":
    main()
