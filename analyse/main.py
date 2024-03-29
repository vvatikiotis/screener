#
#  Using this TA lib. Depends on TA-Lib (brew it)
# https://github.com/twopirllc/pandas-ta
#

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
from datetime import datetime

# our own
import helpers
import supertrend
import bftb
import from_bar_diffs
import prices_diff
import tr_atr
import inside_bar
import engulfing_pattern
import historical_vol

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
def run_indicators(
    tf_df_dict, analysis=None, timeframe=None, view_params=None, analysis_params=None
):
    indicator_results = {}
    indicator2 = None

    if timeframe == None:
        if (
            analysis == "supertrend"
            or analysis == "from_diff"
            or analysis == "tr_atr"
            or analysis == "bear_engulf"
            or analysis == "price_diff"
            or analysis == "bull_engulf"
            or analysis == "hist_vol"
        ):
            indicator1 = bftb.run_btfd(tf_df_dict)
        # Inside bar has no meaning in timeframes other that 1w and 3d
        if analysis == "supertrend":
            indicator2 = supertrend.run_supertrend(tf_df_dict)
        # all the other analysis need a tf spec
        if analysis == "from_diff":
            indicator2 = from_bar_diffs.run_from_bar_diffs(
                tf_df_dict, from_bar=view_params
            )
        if analysis == "price_diff":
            indicator2 = prices_diff.run_prices_diff(tf_df_dict, last_nth=view_params)
        if analysis == "bear_engulf":
            indicator2 = engulfing_pattern.run_engulfing_pattern(
                tf_df_dict, type="bear"
            )
        if analysis == "bull_engulf":
            indicator2 = engulfing_pattern.run_engulfing_pattern(
                tf_df_dict, type="bull"
            )
        if analysis == "tr_atr":
            indicator2 = tr_atr.run_tr_atr(
                tf_df_dict, from_bar=view_params, calc_args=analysis_params
            )
        if analysis == "hist_vol":
            indicator2 = historical_vol.run_historical_vol(
                tf_df_dict, from_bar=view_params, calc_args=analysis_params
            )

    else:
        tf = timeframe[0]
        if tf == "1d":
            indicator1 = bftb.run_btfd(tf_df_dict)
            if analysis == "supertrend":
                indicator2 = supertrend.run_supertrend(tf_df_dict)
            if analysis == "bear_engulf":
                indicator2 = engulfing_pattern.run_engulfing_pattern(
                    tf_df_dict, type="bear"
                )
            if analysis == "bull_engulf":
                indicator2 = engulfing_pattern.run_engulfing_pattern(
                    tf_df_dict, type="bull"
                )
            # all the other analysis need a tf spec
            if analysis == "from_diff":
                indicator2 = from_bar_diffs.run_from_bar_diffs(
                    tf_df_dict, from_bar=view_params
                )
            if analysis == "price_diff":
                indicator2 = prices_diff.run_prices_diff(
                    tf_df_dict, last_nth=view_params
                )
            if analysis == "tr_atr":
                indicator2 = tr_atr.run_tr_atr(
                    tf_df_dict, from_bar=view_params, calc_args=analysis_params
                )
            if analysis == "hist_vol":
                indicator2 = historical_vol.run_historical_vol(
                    tf_df_dict, from_bar=view_params, calc_args=analysis_params
                )
        else:
            if analysis == "supertrend":
                indicator1 = supertrend.run_supertrend(tf_df_dict)
            if analysis == "bear_engulf":
                indicator1 = engulfing_pattern.run_engulfing_pattern(
                    tf_df_dict, type="bear"
                )
            if analysis == "bull_engulf":
                indicator1 = engulfing_pattern.run_engulfing_pattern(
                    tf_df_dict, type="bull"
                )
            # all the other analysis need a tf spec
            if analysis == "from_diff":
                indicator1 = from_bar_diffs.run_from_bar_diffs(
                    tf_df_dict, tf, from_bar=view_params
                )
            if analysis == "price_diff":
                indicator1 = prices_diff.run_prices_diff(
                    tf_df_dict, tf, last_nth=view_params
                )
            if analysis == "tr_atr":
                indicator1 = tr_atr.run_tr_atr(
                    tf_df_dict,
                    timeframe=tf,
                    from_bar=view_params,
                    calc_args=analysis_params,
                )
            if analysis == "hist_vol":
                indicator1 = historical_vol.run_historical_vol(
                    tf_df_dict,
                    timeframe=tf,
                    from_bar=view_params,
                    calc_args=analysis_params,
                )

    indicator_results = {"indicator1": indicator1}
    if indicator2 != None:
        indicator_results["indicator2"] = indicator2

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

    # use_analysis, use_timeframe, use_paramter  global vars per process
    results = run_indicators(
        tf_df_dict,
        analysis=use_analysis,
        timeframe=use_timeframe,
        view_params=use_view_params,
        analysis_params=use_analysis_params,
    )

    return {"symbol": {"name": symbol}, **results}


def pool_initializer(analysis, timeframe, view_params, analysis_params):
    global use_analysis
    global use_timeframe
    global use_view_params
    global use_analysis_params

    use_analysis = analysis
    use_timeframe = timeframe
    use_view_params = view_params
    use_analysis_params = analysis_params


def main():
    set_options()

    CSV_DIR = "../symbols/csv"
    filenames = [f for f in os.listdir(CSV_DIR) if f.endswith(".csv")]
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
        "-t",
        "--timeframe",
        nargs="+",
        help="Run for timeframe or list of timeframes",
    )
    PARSER.add_argument(
        "-ts",
        "--time-series",
        help="Show last ts rows from timeseries instead of TA results",
    )
    PARSER.add_argument(
        "-sort",
        "--sort-series",
        choices=["asc", "desc"],
        help="WIP Sort last column",
    )
    PARSER.add_argument(
        "-u",
        "--use-analysis",
        default="supertrend",
        choices=[
            "supertrend",
            "from_diff",
            "price_diff",
            "tr_atr",
            "bear_engulf",
            "bull_engulf",
            "hist_vol",
        ],
        help="Type of analysis",
    )
    # this has to be view size options
    PARSER.add_argument(
        "-vp",
        "--view-params",
        help="View parameter for from_diff, price_diff, tr_atr and hist_vol analysis",
    )
    PARSER.add_argument(
        "-ap",
        "--analysis-params",
        nargs="+",
        help="Analysis params for tr_atr and hist_vol analysis. -ap param1_value1 param2_value2 etc",
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

    if (
        parsed_arguments.timeframe != None
        and len(parsed_arguments.timeframe) > 1
        and parsed_arguments.use_analysis != "supertrend"
        and parsed_arguments.use_analysis != "bear_engulf"
        and parsed_arguments.use_analysis != "bull_engulf"
    ):
        print(
            f"This analysis supports only 1 timeframe per run. Will use only {parsed_arguments.timeframe[0]}, the rest are ignored"
        )

    view_params = 10
    if parsed_arguments.view_params != None:
        if (
            parsed_arguments.use_analysis != "from_diff"
            and parsed_arguments.use_analysis != "price_diff"
            and parsed_arguments.use_analysis != "tr_atr"
            and parsed_arguments.use_analysis != "hist_vol"
        ):
            print(
                f"Only from_diff, price_diff, tr_atr, hist_vol support -p. Will run {parsed_arguments.use_analysis} with default arguments"
            )
        else:
            view_params = int(parsed_arguments.view_params)

    # Enable it for many
    pool = Pool(
        processes=8,
        initializer=pool_initializer,
        initargs=(
            parsed_arguments.use_analysis,
            parsed_arguments.timeframe,
            view_params,
            parsed_arguments.analysis_params,
        ),
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
    elif module_id == from_bar_diffs.OUTPUT_ID:
        return from_bar_diffs.tabulate
    elif module_id == tr_atr.OUTPUT_ID:
        return tr_atr.tabulate
    elif module_id == prices_diff.OUTPUT_ID:
        return prices_diff.tabulate
    elif module_id == inside_bar.OUTPUT_ID:
        return inside_bar.tabulate
    elif module_id == engulfing_pattern.OUTPUT_ID:
        return engulfing_pattern.tabulate
    elif module_id == historical_vol.OUTPUT_ID:
        return historical_vol.tabulate


#
def output(results, args):
    last_rows_count = args.time_series
    sort = args.sort_series
    analysis = args.use_analysis
    timeframe = args.timeframe

    if last_rows_count == None:
        print_tabular(results, sort, analysis=analysis, timeframe=timeframe)
    elif last_rows_count != None:
        print_series(results, last_rows_count, sort)


#
# [
# {symbol: {name: BTCUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# {symbol: {name: ATOMUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# ]
#
def print_tabular(
    results,
    sort=None,
    analysis=None,
    timeframe=None,
    calculation_options=None,
    last_n=None,
):
    """
    Print results in a tabular format
    """

    headers = []
    table = []
    titles = []
    descs = []

    for i, symbol_dict in enumerate(results):
        symbol = symbol_dict["symbol"]["name"]
        headers.append({"symbol": "Symbol"})
        table.append({"symbol": symbol})
        titles.append([])
        descs.append([])

        for key, value in symbol_dict.items():
            if key.startswith("indicator") == True:
                if i == 0:
                    titles[i].append(f"--------- {value['name']} ---------")
                    descs[i].append(f"----- {value['desc']} -----")
                tabulate_func = get_tabulate_func(value["output_id"])
                [header, dict_] = tabulate_func(
                    symbol_dict[key]["series"],
                    symbol_dict[key]["screened"],
                    analysis,
                    timeframe,
                )
                headers[i] |= header  # |= Update headers[i] dict, in place
                table[i] |= dict_

    print(*titles[0])
    print(tabulate(table, headers=headers[0], tablefmt="fancy_grid", stralign="right"))
    print("\n")
    print(*[f"{x}\n" for x in descs[0]])

    today = datetime.now()
    print(f"--------- {colored(today, 'yellow')} ---------\n")


#
# [
# {symbol: {name: BTCUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# {symbol: {name: ATOMUSDT}, indicator1: { name:'Supertrend', series: {1d: df},  screened: {1d: False, 12h: Buy}}, indicator2:{name:{}, series: {}, screened: {} } },
# ]
#
def print_series(results, last, sort=None):
    """
    Print raw result series
    """

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

    today = datetime.now()
    print(f"--------- {colored(today, 'yellow')} ---------\n")


def set_options():
    pd.set_option("display.max_rows", None)


if __name__ == "__main__":
    main()
