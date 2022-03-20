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
import inside_bar
import from_bar_diffs
import tr_atr

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
def run_indicators(tf_df_dict, type):
    indicator_results = {}
    has1d = "1d" in tf_df_dict
    if type == "supertrend":
        st_dict = supertrend.run_supertrend(tf_df_dict)
        ib_dict = inside_bar.run_inside_bar(tf_df_dict)
    elif type == "diffs" and has1d:
        diffs_dict = from_bar_diffs.run_from_bar_diffs(tf_df_dict)
    elif type == "tr_atr" and has1d:
        tr_atr_dict = tr_atr.run_tr_atr(tf_df_dict)

    if has1d:
        bftb_dict = bftb.run_btfd(tf_df_dict)

    if has1d:
        indicator_results["indicator1"] = bftb_dict
        if type == "supertrend":
            indicator_results["indicator2"] = st_dict
            indicator_results["indicator3"] = ib_dict
        elif type == "diffs":
            indicator_results["indicator2"] = diffs_dict
        elif type == "tr_atr":
            indicator_results["indicator2"] = tr_atr_dict

    else:
        if type == "supertrend":
            indicator_results["indicator1"] = st_dict
            indicator_results["indicator2"] = ib_dict

    return indicator_results


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
            data = list(
                helpers.dict_filter(
                    csv_dict_reader,
                    "open_time",
                    "open",
                    "high",
                    "low",
                    "close",
                    "close_time",
                )
            )

        df = prepare_dataframe(data)
        tf_df_dict[timeframe] = df

    results = run_indicators(tf_df_dict, use_analysis)

    return {"symbol": {"name": symbol}, **results}


def pool_initializer(analysis):
    global use_analysis
    use_analysis = analysis


def main():
    set_options()

    dir = "../symbols/csv"
    filenames = [f for f in os.listdir(dir) if f.endswith(".csv")]
    filenames.sort()  # sort works in-place
    symbol_tfs_dict = helpers.group(filenames)
    for k, v in symbol_tfs_dict.items():
        v.sort(key=helpers.sort_lambda)
        symbol_tfs_dict[k] = v
    symbol_tfs_arr = [[k, v] for k, v in symbol_tfs_dict.items()]

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

    PARSER.add_argument(
        "-u",
        "--use-analysis",
        default="supertrend",
        choices=["supertrend", "diffs", "tr_atr"],
        help="Type of analysis",
    )

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
    pool = Pool(
        processes=8,
        initializer=pool_initializer,
        initargs=(parsed_arguments.use_analysis,),
    )
    results = pool.map(run, symbol_tfs_arr)
    pool.close()
    pool.join()
    output(results, parsed_arguments)


# NOTE: to add an indicator, we MUST spacify an OUTPUT_ID and a tabulate function
# inside the indicator module. The tabulate function MUST return:
# [headers_dict, results_dict]
def get_tabulate_func(module_id):
    if module_id == supertrend.OUTPUT_ID:
        return supertrend.tabulate
    elif module_id == bftb.OUTPUT_ID:
        return bftb.tabulate
    elif module_id == inside_bar.OUTPUT_ID:
        return inside_bar.tabulate
    elif module_id == from_bar_diffs.OUTPUT_ID:
        return from_bar_diffs.tabulate
    elif module_id == tr_atr.OUTPUT_ID:
        return tr_atr.tabulate


#
def output(results, args):
    last_rows_count = args.time_series
    use_analysis = args.use_analysis

    if last_rows_count == None:
        print_tabular(results)
    elif last_rows_count != None:
        print_series(results, last_rows_count)


#
# [
# {symbol: {name: BTCUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# {symbol: {name: ATOMUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# ]
#
def print_tabular(results):
    headers = []
    table = []
    titles = []

    for i, symbol_dict in enumerate(results):
        symbol = symbol_dict["symbol"]["name"]
        headers.append({"symbol": "Symbol"})
        table.append({"symbol": symbol})
        titles.append([])

        for key, value in symbol_dict.items():
            if key.startswith("indicator") == True:
                if i == 0:
                    titles[i].append(f"--------- {value['name']} ---------")
                tabulate_func = get_tabulate_func(value["output_id"])
                [header, dict_] = tabulate_func(
                    symbol_dict[key]["series"],
                    symbol_dict[key]["screened"],
                )
                headers[i] |= header  # |= Update headers[i] dict, in place
                table[i] |= dict_

    print(*titles[0])
    print(tabulate(table, headers=headers[0], tablefmt="fancy_grid"))


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
