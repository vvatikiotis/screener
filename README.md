# screener
Hopes to be a programmable screener if it grows up

### Installation
1. `brew install node TA-Lib`. I use v17.3.0
2. `git clone`.
3. `npm install` within cloned repo
4. `cd python`
5. `pip3 install -r requirements`



### Fetching data (node script usage)
1. `node index.js -h`
1. Fetch symbols and convert them to csv. `node ./index.js -r -x`. Conversion to csv is necessary for the python screener.
1. Check for integrity of data files, `node ./index.js -c`
2. Convert JSON data files to CSV, `node ./index.js -x`
3. Rebuild checkpoint file, `node ./index.js -b`
4. *NB don't use it lightly, Binance data is not always clean so if you do this you almost certainly will have to clean them, by hand* : Get more past data,`node ./index.js -b`


### TA usage (python script)
1. `cd python`
2. `python main.py`
