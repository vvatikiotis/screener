# for custom supertrend implementation
import numpy as np
import pandas as pd
from numpy import nan as npNaN
from pandas_ta.overlap import hl2

# from pandas_ta.volatility import atr
# from pandas_ta.volatility import true_range
from pandas_ta.utils import get_offset, verify_series
from pandas_ta.overlap import ma
from pandas_ta.utils import get_drift, get_offset, verify_series
from pandas_ta.utils import get_drift, get_offset, non_zero_range, verify_series
from pandas import concat


def true_range(high, low, close, talib=None, drift=None, offset=None, **kwargs):
    """Indicator: True Range"""
    # Validate arguments
    high = verify_series(high)
    low = verify_series(low)
    close = verify_series(close)
    drift = get_drift(drift)
    offset = get_offset(offset)
    mode_tal = bool(talib) if isinstance(talib, bool) else True

    # Calculate Result

    high_low_range = non_zero_range(high, low)
    prev_close = close.shift(1)
    ranges = [high_low_range, high - prev_close, low - prev_close]
    true_range = concat(ranges, axis=1)
    true_range = true_range.abs().max(axis=1)
    true_range.iloc[:drift] = npNaN

    # print(high.head(5))
    # print(low.head(5))
    # print(close.head(5))
    # print(true_range.head(5))
    # m = close.size
    # true_range = [0] * m

    # for i in range(1, m):
    #     if np.isnan(high.iloc[i - 1]):
    #         true_range[i] = high.iloc[i] - low.iloc[i]
    #     else:
    #         true_range[i] = max(
    #             high.iloc[i] - low.iloc[i],
    #             abs(high.iloc[i] - close.iloc[i - 1]),
    #             abs(low.iloc[i] - close.iloc[i - 1]),
    #         )

    # Offset
    if offset != 0:
        true_range = true_range.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        true_range.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        true_range.fillna(method=kwargs["fill_method"], inplace=True)

    # df = pd.DataFrame(
    #     {
    #         f"TRUERANGE": true_range,
    #     },
    #     index=close.index,
    # )
    # Name and Categorize it
    true_range.name = f"TRUERANGE_{drift}"
    true_range.category = "volatility"

    # df.name = f"TRUERANGE_{drift}"
    # df.category = "volatility"
    return true_range


def atr(
    high,
    low,
    close,
    length=None,
    mamode=None,
    talib=None,
    drift=None,
    offset=None,
    **kwargs,
):
    """Indicator: Average True Range (ATR)"""
    # Validate arguments
    length = int(length) if length and length > 0 else 14
    mamode = mamode.lower() if mamode and isinstance(mamode, str) else "rma"
    high = verify_series(high, length)
    low = verify_series(low, length)
    close = verify_series(close, length)
    drift = get_drift(drift)
    offset = get_offset(offset)
    mode_tal = bool(talib) if isinstance(talib, bool) else True

    if high is None or low is None or close is None:
        return

    # Calculate Result
    # if Imports["talib"] and mode_tal:
    #     from talib import ATR

    #     atr = ATR(high, low, close, length)
    # else:
    tr = true_range(high=high, low=low, close=close, drift=drift)
    atr = ma(mamode, tr, length=length)

    percentage = kwargs.pop("percent", False)
    if percentage:
        atr *= 100 / close

    # Offset
    if offset != 0:
        atr = atr.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        atr.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        atr.fillna(method=kwargs["fill_method"], inplace=True)

    # Name and Categorize it
    atr.name = f"ATR{mamode[0]}_{length}{'p' if percentage else ''}"
    atr.category = "volatility"

    return [atr, tr]


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
    dir_, trend = [1] * m, [0] * m
    short, long = [npNaN] * m, [npNaN] * m

    hl2_ = hl2(high, low)
    [atr_, tr_] = atr(high, low, close, length)
    matr = multiplier * atr_
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
            f"SUPERTatr{_props}": atr_,
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
