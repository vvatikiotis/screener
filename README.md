# screener
Hopes to be a programmable screener if it grows up

### Installation
1. `brew install node`. I use v17.3.0
2. `git clone`.
3. `npm install` within cloned repo

### Usage
1. Fetch symbols: `node ./index.js -f`
2. Run SuperTrend for a single symbol: `node ./index.js -s BTCUSDT`
   1. or, run SuperTrend for all specified symbols: `node ./index.js -s`

- Specified symbols in code.
- trend === -1 -> downtrend, trend === 1, uptrend.