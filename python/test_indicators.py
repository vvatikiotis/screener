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


# pine_rma(src, length) =>
# 	alpha = 1/length
# 	sum = 0.0
# 	ta_sma = ta.sma(src, length)
# 	sum := na(sum[1]) ? ta_sma : alpha * src + (1 - alpha) * nz(sum[1])

# pine_atr(length) =>
#     trueRange = na(high[1])? high-low : math.max(math.max(high - low, math.abs(high - close[1])), math.abs(low - close[1]))
#     //true range can be also calculated with ta.tr(true)
#     rma_ = pine_rma(trueRange, length)
#     [rma_, trueRange]


# pandas_ta.true_range
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

    # high_low_range = non_zero_range(high, low)
    # prev_close = close.shift(1)
    # ranges = [high_low_range, high - prev_close, low - prev_close]
    # true_range = concat(ranges, axis=1)
    # true_range = true_range.abs().max(axis=1)
    # true_range.iloc[:drift] = npNaN

    # print(high.head(5))
    # print(low.head(5))
    # print(close.head(5))
    # print(true_range.head(5))
    m = close.size
    tr = [npNaN] * m

    for i in range(1, m):
        if np.isnan(high.iloc[i - 1]):
            tr[i] = high.iloc[i] - low.iloc[i]
        else:
            tr[i] = max(
                high.iloc[i] - low.iloc[i],
                abs(high.iloc[i] - close.iloc[i - 1]),
                abs(low.iloc[i] - close.iloc[i - 1]),
            )
    true_range = pd.Series(tr)
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


# pine_rma(src, length) =>
# 	alpha = 1/length
# 	sum = 0.0
# 	ta_sma = ta.sma(src, length)
# 	sum := na(sum[1]) ? ta_sma : alpha * src + (1 - alpha) * nz(sum[1])
def pine_rma(close, length):
    length = int(length) if length and length > 0 else 10
    alpha = (1.0 / length) if length > 0 else 0.5
    close = verify_series(close, length)

    if close is None:
        return

    ta_sma = ma("sma", close, length=length)

    m = close.size

    sum = [0] * m
    for i in range(1, m):
        nz_prev_sum = 0 if np.isnan(sum[i - 1]) else sum[i - 1]
        sum[i] = (
            ta_sma[i]
            if np.isnan(sum[i - 1])
            else alpha * close[i] + (1 - alpha) * nz_prev_sum
        )

    df = pd.Series(sum)

    df.name = f"RMA_{length}"
    df.category = "overlap"
    # print(ta_sma, close)
    return df


# pandas_ta.rma
def rma(close, length=None, offset=None, **kwargs):
    """Indicator: wildeR's Moving Average (RMA)"""
    # Validate Arguments
    length = int(length) if length and length > 0 else 10
    alpha = (1.0 / length) if length > 0 else 0.5
    close = verify_series(close, length)
    offset = get_offset(offset)

    if close is None:
        return

    # Calculate Result
    rma = close.ewm(alpha=alpha, min_periods=length).mean()

    # Offset
    if offset != 0:
        rma = rma.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        rma.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        rma.fillna(method=kwargs["fill_method"], inplace=True)

    # Name & Category
    rma.name = f"RMA_{length}"
    rma.category = "overlap"

    return rma


# pandas_ta.atr
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
    # atr = ma(mamode, tr, length=length)
    atr = pine_rma(tr, length=length)

    percentage = kwargs.pop("percent", False)
    if percentage:
        atr *= 100 / close

    # Offset
    if offset != 0:
        atr = atr.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        atr.fillna(kwargs["fillna"], inplace=True)
        # if "fill_method" in kwargs:
        atr.fillna(method=kwargs["fill_method"], inplace=True)

    # Name and Categorize it
    atr.name = f"ATR{mamode[0]}_{length}{'p' if percentage else ''}"
    atr.category = "volatility"

    # print(tr.tail(28), atr.tail(28))
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
def kivan_supertrend(
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
        # else:
        #     dir_[i] = dir_[i]

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

    # print("supertrend---", df.dtypes)
    return df
