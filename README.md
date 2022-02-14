# screener
Hopes to be a programmable screener if it grows up

### Installation
1. `brew install node`. I use v17.3.0
2. `git clone`.
3. `npm install` within cloned repo

### Usage
1. `node index.js -h`
1. Fetch symbols: `node ./index.js -r`
2. Run SuperTrend for a single symbol: `node ./index.js -s BTCUSDT`
   1. or, run SuperTrend for all specified symbols: `node ./index.js -s`
3. `-o` specifies timeframes. The script analyses 4h, 6h, 12h and 1d, by default.
4. `-a` shows the complete analysed time series. Otherwise, by default, the series is trimmed to the latest data points.
5. `-f` filters the series using an already defined predicate, p1.
6. `-p` specifies a predicates. p1, p2 and p3 are the predicates defined in code. Only p1 is implemented. p2 and p3 are just placeholders
7. Specified symbols are in a separate file, `symbol.list`. One symbol per line.

Examples:
- `node ./index.js -s -o 1d -f`: run SuperTrend on all symbols, in 1d, filter it using p1
- `node ./index.js -s BTCUSDT -o 4h -a`: run SuperTrend for BTCUSDT, on 4h and show the entire series. No filtering

### Rationale

- trend === -1 -> downtrend, trend === 1, uptrend.
- p1 predicate is looking for reversal. If previous trend is down and current trend is up (and vice versa), then a buy (sell) signal is produced.
