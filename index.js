import fs, { constants } from "fs";
import { readFile, writeFile, access } from "fs/promises";
import fsEextra from "fs-extra";
import fetch from "node-fetch";
import { Command } from "commander/esm.mjs";
import promptly from "promptly";
import chalk from "chalk";
import Indicators from "technicalindicators";
import { exit } from "process";
import { spawn } from "child_process";

let SYMBOLS = [];
// put one ticker per line in symbol.list
// example:
// BTCUSDT
// ETHUSDT
// ... and so on
1646697599999;
// -----------------------------------------------------
// HACK these and you are ready to go
// timeframes and number of bars for seeding
const RESOLUTIONS = [
  { interval: "1w", seedPeriod: 999 },
  { interval: "3d", seedPeriod: 999 },
  { interval: "1d", seedPeriod: 999 },
  { interval: "12h", seedPeriod: 999 },
  { interval: "6h", seedPeriod: 999 },
  { interval: "4h", seedPeriod: 999 },
  { interval: "1h", seedPeriod: 999 },
];
// Seconds in a given timeframe
// Used to calculate the update diff
const I2SECS = {
  "1h": 3600,
  "4h": 14400,
  "6h": 21600,
  "12h": 43200,
  "1d": 86400,
  "3d": 259200,
  "1w": 604800,
};
// TODO: maybe pass trim as an func argument?
// Number of bars we are intereted in, per timeframe
// Used *only* in output
const GETLASTPERIODS = {
  "1w": 5,
  "3d": 5,
  "1d": 5,
  "12h": 8,
  "6h": 12,
  "4h": 14,
  "1h": 14,
};
// End HACK
// -----------------------------------------------------
const SYMBOL_FILENAME = "symbol.list";
const DATA_PATH = "./symbols";

//
//
//
async function fetchData(symbol, interval, limit, startTime) {
  const standardOpts = { symbol, interval, limit };
  const opts = startTime ? { ...standardOpts, startTime } : standardOpts;
  const response = await fetch(
    "https://api.binance.com/api/v3/klines?" + new URLSearchParams(opts)
  );

  return await response.json();
}

//
//
//
async function writeJsonFile(data, flag, filename) {
  try {
    let writeData;
    if (flag === "a") {
      const oldJsonData = await readJsonFile(filename);
      const oldData = JSON.parse(oldJsonData);
      oldData.splice(oldData.length - 1); // always remove the current candle cause it's not complete
      writeData = oldData.concat(data);
    } else writeData = data;

    await writeFile(`${DATA_PATH}/${filename}`, JSON.stringify(writeData), {
      flag: "w",
    });
  } catch (err) {
    console.error(`writeJsonFile() :: Error writing ${DATA_PATH}/${filename}`);
    throw err;
  }
}

async function readJsonFile(filename) {
  try {
    const data = await readFile(`${DATA_PATH}/${filename}`);
    return data;
  } catch (err) {
    console.error(`readJsonFile() :: Error reading ${DATA_PATH}/${filename}`);
    throw err;
  }
}

//
//
//
function hasDuplicateSymbols(symbols = SYMBOLS) {
  const duplicates = symbols.filter(
    (item, index) => index !== symbols.indexOf(item)
  );

  return duplicates.length !== 0;
}

//
// Integrity functions
//

//
// Current implementation: just returns how many candles are missing.
// The caller has to take this into account
// method = 'offset' | 'ignore' | 'fill'
function handleMissingCandles(symbol, resol, candles, method = "offset") {
  const step = I2SECS[resol.interval] * 1000;
  let missingCount = 0;

  for (let i = 0; i < candles.length - 1; i++) {
    if (candles[i][0] + step !== candles[i + 1][0]) {
      missingCount += (candles[i + 1][0] - candles[i][0]) / step - 1;
      console.log(`handleMissingCandles() :: missing ${missingCount} candles`);
    }
  }

  return missingCount;
}

//
//
//
function examineJson(symbol, resol, candles, infile = true) {
  const sourceLog = infile
    ? `${symbol}_${resol.interval}.json`
    : `${symbol} ${resol.interval}`;
  let isOK = true;
  const diff = I2SECS[resol.interval] * 1000;

  for (let i = 0; i < candles.length - 1; i++) {
    if (candles[i][0] === candles[i + 1][0]) {
      console.log(
        `examineJson() :: ${sourceLog}: Duplicate timestamp ${
          candles[i + 1][0]
        }`
      );

      // Better exit here. Duplicate timestamps mean that the offsetting fix
      // has somehow gone wrong.
      // isOK = false;
      exit(4);
    } else if (candles[i][0] + diff !== candles[i + 1][0]) {
      const one = candles[i][0];
      const two = candles[i + 1][0];
      console.log(
        `examineJson() :: ${sourceLog}: Incorrect diff: ${new Date(
          one
        ).toLocaleString()} (${one}) -- ${new Date(
          two
        ).toLocaleString()} (${two}) `
      );

      isOK = false;

      // exit(4);
    }
  }

  return isOK;
}

//
//
//
async function checkSymbolsIntegrity(
  symbols = SYMBOLS,
  resolutions = RESOLUTIONS,
  shouldThrow = false
) {
  console.log(
    `checkSymbolsIntegrity() :: Checking integrity for everything...`
  );

  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;
        const { interval } = resol;

        let data, candles;
        try {
          data = await readJsonFile(`${symbol}_${interval}.json`);
          candles = JSON.parse(data);
        } catch (err) {
          console.log(
            `checkSymbolsIntegrity() :: error reading ${DATA_PATH}/${symbol}_${interval}.json`,
            err
          );
          throw err;
        }

        // console.log(`Checking integrity for ${symbol}_${resol.interval}...`);
        const isOK = examineJson(symbol, resol, candles, true);

        if (!isOK) console.log("\n");
        if (!isOK && shouldThrow) throw "error";
      }, undefined);
    })
  );
}

//
// rebuilds checkpoints.json for defined SYMBOLS
//
async function rebuildCheckpointsForSymbols(symbols, resolutions) {
  const checkpoints = [];
  // https://advancedweb.hu/how-to-use-async-functions-with-array-foreach-in-javascript/
  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;
        const { interval } = resol;

        let data;
        try {
          data = await readJsonFile(`${symbol}_${interval}.json`);
          const checkpoint = Object.values(JSON.parse(data)).at(-1)[6];
          checkpoints.push({
            symbol,
            interval,
            checkpoint,
          });
        } catch (err) {
          console.log(
            `rebuildCheckpoints() :: cannot find ${DATA_PATH}/${symbol}_${interval}.json, Dropping checkpoint from checkpoints.json`,
            err
          );
        }
      }, undefined);
    })
  );

  // write ticker close datetime
  console.log(
    "rebuildCheckpointsForSymbols() :: Found following checkpoints\n",
    checkpoints
  );
  writeJsonFile(checkpoints, "w", "checkpoints.json");

  return checkpoints;
}
//
// END Integrity functions
//

//
// fetch all symbols
//
async function fetchSymbols(symbols, resolutions) {
  let checkpoints = [];
  try {
    const checkpointsJson = await readJsonFile(`checkpoints.json`);
    checkpoints = JSON.parse(checkpointsJson);
  } catch (err) {
    console.log("fetchSymbols() :: Cannot find checkpoints file", err);
  }
  let nextCheckpoints = [];

  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;

        const { interval, seedPeriod } = resol;

        let { checkpoint } = checkpoints.find((obj) => {
          return obj.symbol === symbol && obj.interval === interval;
        }) || { checkpoint: -1 };

        const symbolFname = `${symbol}_${interval}.json`;
        let fetchedData;
        let didSeed = false;

        console.log(`Checkpoint for ${symbol}, ${interval} = ${checkpoint}`);

        if (checkpoint === -1) {
          try {
            await access(`${DATA_PATH}/${symbolFname}`, constants.F_OK);
            const json = await readJsonFile(symbolFname);
            checkpoint = Object.values(JSON.parse(json)).at(-1)[6];
            console.log(
              `fetchSymbols() :: ${symbolFname} exists, getting last checkpoint from there.\n*** Please rerun to fetch latest data. ***\n`
            );
          } catch (err) {
            console.log(`fetchSymbols() :: Seeding ${symbol}, ${interval} ...`);
            fetchedData = await fetchData(symbol, interval, seedPeriod);
            if (fetchedData.msg) {
              console.log(
                `fetchSymbols() :: Can't find symbol ${symbol}. ${fetchedData.msg}`
              );
              return false;
            }
            checkpoint = `${Object.values(fetchedData).at(-1)[6]}`;
            didSeed = true;
          }
        } else {
          const nowUTC = Date.parse(new Date());
          let diff;

          // checkpoint is close datetime. Binance API sets current bar's
          // close datetime in the future. So:
          // -TF_seconds < nowUTC - checkpoint: current bar update
          // nowUTC - checpoint >= 0 previous bar + 1
          const needUpdate =
            (diff = (nowUTC - checkpoint) / 1000) > -I2SECS[interval];
          if (needUpdate) {
            const count =
              diff < 0 ? 1 : 1 + Math.floor(diff / I2SECS[interval]) + 1;

            fetchedData = await fetchData(symbol, interval, count);
            console.log(
              `fetchSymbols() :: ${symbol} ${interval}: Fetched ${count} candles...`
            );
          }
        }

        if (fetchedData) {
          writeJsonFile(fetchedData, didSeed ? "w" : "a", symbolFname);
          checkpoint = `${Object.values(fetchedData).at(-1)[6]}`;
        }

        nextCheckpoints.push({
          symbol,
          interval,
          checkpoint,
        });
      }, undefined);
    })
  );

  if (nextCheckpoints.length !== 0) {
    console.log(
      `fetchSymbols() :: Writing next checkpoints, ${nextCheckpoints.length} symbol checkpoints`
    );
    writeJsonFile(nextCheckpoints, "w", "checkpoints.json");
  }
}

async function prependSymbolData(symbols = SYMBOLS) {
  const resolutions = [
    //
    // Keep this commented out. Uncomment only when we need more past data.
    //
    // BEWARE: BINANCE data is not always clean. I hand edited some files.
    //
    // 3000 ticks should be enough for any TA we do, even for unstable formulas
    //
    { interval: "1w" },
    { interval: "3d" },
    { interval: "1d" },
    { interval: "12h" },
    { interval: "6h" },
    { interval: "4h" },
    { interval: "1h" },
  ];

  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;

        const { interval } = resol;
        const symbolFname = `${symbol}_${interval}.json`;
        let json;
        let firstSavedDate;

        try {
          await access(`${DATA_PATH}/${symbolFname}`, constants.F_OK);
          json = await readJsonFile(symbolFname);
          firstSavedDate = JSON.parse(json).at(0)[0];
          console.log(
            `prependSymbolData() :: ${symbolFname} exists, getting first date from there.`
          );
        } catch (err) {
          console.log(`prependSymbolData() :: exiting hard...`);
          exit(5);
        }

        // fetch from sometime way back in the past to discover the ticker's
        // very first candle timestamp
        const prefetchJson = await fetchData(
          symbol,
          interval,
          1,
          "1302928000000" // April 16, 2011 7:26:40 AM GMT+03:00 DST
        );
        const introDate = prefetchJson[0][0];
        console.log(
          `prependSymbolData() :: intro date for ${symbol} = ${new Date(
            introDate
          ).toLocaleString()}`
        );

        // we have all Binance data, return
        if (firstSavedDate === introDate) {
          console.log(
            `prependSymbolData() :: we have all data for ${symbol} ${interval}, returning...\n`
          );
          return;
        }

        // haven't finished yet, there is more date to fetch
        const maxLimit = 1000;
        const lhs = firstSavedDate - I2SECS[interval] * 1000 * maxLimit;
        const getBack =
          lhs >= introDate
            ? maxLimit
            : (firstSavedDate - introDate) / 1000 / I2SECS[interval];
        console.log(
          `prependSymbolData() :: ----> Fetching ${symbol}: ${getBack} ${interval},  ...`
        );

        const fetchedData = await fetchData(
          symbol,
          interval,
          getBack,
          firstSavedDate - I2SECS[interval] * 1000 * getBack
        );

        // decide what to do, depending on the fetchedData integrity and length
        if (fetchedData.length === 0) {
          console.log(
            `prependSymbolData() :: fetched data is empty, ${fetchedData.length}, probably rate limiting hit us, try again\n`
          );
        } else if (fetchedData.msg)
          console.log(`prependSymbolData() :: ${fetchedData.msg}\n`);
        else {
          const isOK = examineJson(symbol, resol, fetchedData, false);

          if (!isOK) {
            const count = handleMissingCandles(
              symbol,
              resol,
              fetchedData,
              false
            );
            console.log(
              `prependSymbolData() :: ${symbol} ${interval}: ${count} missing candles in fetched data. Offsetting and prepending...\n`
            );

            fetchedData.splice(-count, count);
          }

          const json2update = JSON.parse(json);
          json2update.unshift(...fetchedData);
          writeJsonFile(json2update, "w", symbolFname);
        }
      }, undefined);
    })
  );
}

//
//
//
function runIndicator(indicatorFn, showAll = false) {
  return async function (symbols = SYMBOLS, resolutions = RESOLUTIONS) {
    console.log(`Running  ${indicatorFn.name}\n`);
    const result = await Promise.all(
      symbols.map(async (symbol) => {
        const tfs4symbol = await resolutions.reduce(
          async (memo, resolution) => {
            const { interval } = resolution;
            const json = await readJsonFile(`${symbol}_${interval}.json`);
            const data = JSON.parse(json);

            // ...await memo. Am I using the wrong tool for the job?
            // Async makes dev work time consuming.
            // Python? Amitrader? R? or just sync version?

            // https://stackoverflow.com/questions/41243468/javascript-array-reduce-with-async-await
            const series = indicatorFn(data);
            return {
              ...(await memo),
              [interval]: showAll
                ? series
                : series.slice(-GETLASTPERIODS[interval]),
            };
          },
          {}
        );

        return { [symbol]: tfs4symbol };
      })
    );

    // arr of Obj -> Obj[symbol]={ 4h:[], 1d: [], ...}
    return result.reduce((acc, curr) => {
      const [[key, value], _] = Object.entries(curr);
      acc[key] = value;
      return acc;
    }, {});
  };
}

//
// Generic output function
//
function output({
  results, // results as we get them from our indicator
  filterFn,
  timeframes = RESOLUTIONS.map((r) => r.interval), // used only when no filtering
  symbols = SYMBOLS,
  filter = true,
}) {
  symbols.forEach((symbol) => {
    if (filter) {
      const filtered = filterFn(symbol, results[symbol]);

      if (filtered.signals.length !== 0) {
        console.log(filtered);
        console.log();
      } else console.log(`symbol: ${symbol}: no signal`);
    } else {
      // just print supertrend series
      console.log(`===== ${symbol} =====`);

      // this to print only specified timeframes
      const clone = ((timeframes, symResults) => {
        return timeframes.reduce((acc, tf) => {
          acc[tf] = symResults[tf];

          return acc;
        }, {});
      })(timeframes, results[symbol]);

      console.log(clone);
      console.log();
    }
  });
}

// that's the filterFn argument of output function
// was: default timeframes are 4h and 12h
// current: all timeframes
function filterSupertrend(
  predicateNo = "p1",
  timeframes = RESOLUTIONS.map((r) => r.interval)
) {
  // filter SuperTrend results
  // LONG only filter
  // if latest trend is UP and previous is DOWN -> that's a pivot point.
  // if both (the default) 4h, 12h and 1d timeframes exhibit, this is buy signal
  const predicate1 = (timeframe, series) => {
    const last = -1;
    const OneB4Last = -2;
    const TwoB4Last = -3;
    const ThreeB4Last = -4;

    if (timeframe === "4h") {
      if (series.at(last).trend === 1 && series.at(OneB4Last).trend === -1)
        return "buy";
      if (
        series.at(last).trend === 1 &&
        series.at(OneB4Last).trend === 1 &&
        series.at(TwoB4Last) === -1
      )
        return "buy";
      if (
        series.at(last).trend === 1 &&
        series.at(OneB4Last).trend === 1 &&
        series.at(TwoB4Last) === 1 &&
        series.at(ThreeB4Last) === -1
      )
        return "buy";

      if (series.at(last).trend === -1 && series.at(OneB4Last).trend === 1)
        return "sell";
      if (
        series.at(last).trend === -1 &&
        series.at(OneB4Last).trend === -1 &&
        series.at(TwoB4Last) === 1
      )
        return "sell";
      if (
        series.at(last).trend === -1 &&
        series.at(OneB4Last).trend === -1 &&
        series.at(TwoB4Last) === -1 &&
        series.at(ThreeB4Last) === 1
      )
        return "sell";
    }

    if (timeframe === "12h") {
      if (series.at(last).trend === 1 && series.at(OneB4Last).trend === -1)
        return "buy";
      if (
        series.at(last).trend === 1 &&
        series.at(OneB4Last).trend === 1 &&
        series.at(TwoB4Last).trend === -1
      )
        return "buy";

      if (series.at(last).trend === -1 && series.at(OneB4Last).trend === 1)
        return "sell";
      if (
        series.at(last).trend === -1 &&
        series.at(OneB4Last).trend === -1 &&
        series.at(TwoB4Last).trend === 1
      )
        return "sell";
    }

    if (timeframe === "1d") {
      if (series.at(last).trend === 1 && series.at(OneB4Last).trend === -1)
        return "buy";
      if (
        series.at(last).trend === 1 &&
        series.at(OneB4Last).trend === 1 &&
        series.at(TwoB4Last).trend === -1
      )
        return "buy";

      if (series.at(last).trend === -1 && series.at(OneB4Last).trend === 1)
        return "sell";
      if (
        series.at(last).trend === -1 &&
        series.at(OneB4Last).trend === -1 &&
        series.at(TwoB4Last).trend === 1
      )
        return "sell";
    }

    return false;
  };

  const predicate2 = (timeframe, series) => {
    console.log("---> p2 needs implementation");
    return false;
  };
  const predicate3 = (timeframe, series) => {
    console.log("--->  p3 needs implementation");
    return false;
  };

  const predicateFn =
    predicateNo === "p1"
      ? predicate1
      : predicateNo === "p2"
      ? predicate2
      : predicateNo === "p3"
      ? predicate3
      : (timeframe, series) => {
          console.log("---> this is a noop, Specify p1, p2 or p3 with -p");
        };

  return (symbol, symbolResults) => {
    const signals = timeframes.map((tf) => {
      const series = symbolResults[tf];

      if (predicateFn(tf, series) === "buy") return { [tf]: "buy" };
      else if (predicateFn(tf, series) === "sell") return { [tf]: "sell" };
      else return { [tf]: "" };
    });

    return {
      symbol,
      // signals,
      signals: signals.filter((s) => Object.values(s)[0] !== ""),
    };
  };
}

//
//
//
function SuperTrend(atrPeriod = 10, multiplier = 2) {
  console.log(
    `SuperTrend indicator primed: lookback: ${atrPeriod}, ATR multiplier: ${multiplier}`
  );
  return function __supertrend(data) {
    const openDT = data.map((pt) => pt[0]);
    const closeDT = data.map((pt) => pt[6]);
    const src = data.map((pt) => (parseFloat(pt[2]) + parseFloat(pt[3])) / 2);
    const highs = data.map((pt) => pt[2]);
    const lows = data.map((pt) => pt[3]);
    const closes = data.map((pt) => pt[4]);
    const ATR = Indicators.atr({
      period: atrPeriod, // SuperTrend param
      high: highs,
      low: lows,
      close: closes,
    });

    // (H - L) /2
    let bot1 = src[atrPeriod] - multiplier * ATR[0];
    let top1 = src[atrPeriod] + multiplier * ATR[0];
    let trend = 1;
    let trend1 = 1;
    const band = ATR.map((atr, idx) => {
      const closeIdx = atrPeriod + idx;
      const close = closes[closeIdx];

      const bot = src[idx + atrPeriod] - multiplier * atr;
      bot1 = closes[closeIdx - 1] > bot1 ? Math.max(bot, bot1) : bot;

      const top = src[idx + atrPeriod] + multiplier * atr;
      top1 = closes[closeIdx - 1] < top1 ? Math.min(top, top1) : top;

      trend =
        trend === -1 && closes[closeIdx] > top1
          ? 1
          : trend === 1 && closes[closeIdx] < bot1
          ? -1
          : trend;

      const buySignal = trend === 1 && trend1 === -1;
      const sellSignal = trend === -1 && trend1 === 1;
      trend1 = trend;

      return {
        openDT: new Date(openDT[idx + atrPeriod]).toLocaleString("en-US"),
        closeDT: new Date(closeDT[idx + atrPeriod]).toLocaleString("en-US"),
        bottom: bot1,
        top: top1,
        trend,
        buySignal,
        sellSignal,
      };
    });

    return band;
  };
}

//
//
//
function prepFSStruct() {
  if (!fs.existsSync(DATA_PATH)) {
    fs.mkdirSync(DATA_PATH);
    console.log(`prepFSStruct() :: ${DATA_PATH} dir has been created.`);
  }

  if (!fs.existsSync(SYMBOL_FILENAME)) {
    fs.writeFileSync(SYMBOL_FILENAME, "", { encoding: "utf8" });
    console.log(`prepFSStruct() :: ${SYMBOL_FILENAME} file has been created.`);
  }
}

//
//
//
function readSymbols() {
  let list;
  try {
    list = fs.readFileSync(SYMBOL_FILENAME, { encoding: "utf8", flag: "r" });
  } catch (err) {
    console.log(
      `readSymbols() :: Can not find symbols file ${SYMBOL_FILENAME}`,
      err
    );
    exit(2);
  }

  if (list.length === 0) {
    console.log(
      `readSymbols() :: symbol file ${SYMBOL_FILENAME} is empty.\nOne pair, e.g. BTCUSDT, per line`
    );
    exit(3);
  }

  const symbols = list
    .split("\n")
    .filter((s) => s.length !== 0)
    .map((s) => s.trim());

  return symbols;
}

//
//
//
function toCSV() {
  const toCSV = spawn("/bin/bash", ["./tools/json-to-csv.sh"]);

  toCSV.stdout.on("data", (data) => {
    console.log(`${data}`);
  });

  toCSV.stderr.on("data", (data) => {
    console.log(chalk.red(`main() :: stderr: ${data}`));
  });

  toCSV.on("error", (error) => {
    console.log(chalk.red(`main() :: error: ${error.message}`));
  });

  toCSV.on("close", (code) => {
    console.log(
      `main() :: child process (json to csv bash script) exited with code ${code}`
    );
  });
}

//
//
//
function cpDir(source, dest) {
  fsEextra.copy(source, dest, function (err) {
    if (err) {
      console.log("cpDir() :: An error occured while copying the folder.");
      return console.error(err);
    }
    console.log("Copy completed!");
  });
}

//
//
//
function testThings() {
  console.log("testThings() :: This is a dummy test. Write something.");
}

//
//
//
async function main() {
  prepFSStruct();

  // global
  SYMBOLS = readSymbols();

  if (hasDuplicateSymbols(SYMBOLS)) {
    console.log("main() :: exit code 1: Duplicate symbols");
    process.exit(1);
  }

  const program = new Command();
  program

    //
    // for fetching and checking datapoint only.
    //
    .option("-r, --fetch-symbols", "fetch symbols, in code")
    .option("-x, --convert-CSV", "convert files to csv")
    .option(
      "-b, --rebuild-from-symbols",
      "rebuild checkpoints file from symbols data"
    )
    .option("-c --check-integrity", "check symbols timestamp order")
    .option("-e --tEst", "test/dry run things")

    //
    // OBSOLETE, USE PYTHON
    //
    .option(
      "-s, --run-screener [symbols...]",
      "(DEPRECATED, run python). Run supertrend on fetched symbols"
    )
    .option(
      "-o --output-timeframes [timeframes...]",
      "(DEPRECATED, run python). Specify which timeframes to show. Options: 4h, 6h, 12h, 1d, 3d, 1w"
    )
    .option("-a, --show-all", "show all data points, do not trim", false)
    .option(
      "-f, --filter",
      "(DEPRECATED, run python). Filter results (using a predicate), else show the supertrend series",
      false
    )
    .option(
      "-p --predicate [predicate]",
      "(DEPRECATED, run python). Select predicate. Options: p1, p2, p3. Read code",
      "p1"
    );

  program.parse();

  const options = program.opts();

  // fetching, checking and rebuilding
  // will exit if there is an integrity error
  if (options.fetchSymbols) {
    await fetchSymbols(SYMBOLS, RESOLUTIONS);

    try {
      console.log("\n");
      await checkSymbolsIntegrity(SYMBOLS, RESOLUTIONS);
    } catch (e) {
      console.log("\nmain() :: Error with symbol integrity, exiting...");
      exit(4);
    }
  }

  if (options.rebuildFromSymbols) {
    const answer = await promptly.confirm(
      "Sure? Checkpoint file will be recreated:"
    );
    answer && rebuildCheckpointsForSymbols(SYMBOLS, RESOLUTIONS);
  }

  if (options.checkIntegrity) await checkSymbolsIntegrity(SYMBOLS, RESOLUTIONS);

  if (options.convertCSV) {
    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    console.log("\nmain() :: Will convert json to csv... Wait a bit...");
    await delay(5000);

    toCSV();
  }

  if (options.tEst) {
    testThings();

    // leave it here. this shouldn't be exposed casually to the CLI
    prependSymbolData(SYMBOLS);
  }

  //
  // OBSOLETE NOTE, RUN PYTHON
  //
  if (options.runScreener) {
    let results;
    const fnST = SuperTrend();
    const filterFn = filterSupertrend(
      options.predicate,
      options.outputTimeframes
    );

    // -s only, all symbols
    if (options.runScreener === true) {
      results = await runIndicator(fnST, options.showAll)();
      output({
        results,
        filterFn,
        filter: options.filter,
        timeframes: options.outputTimeframes,
      });
    } else {
      // -s symbol
      results = await runIndicator(fnST, options.showAll)(options.runScreener);
      output({
        results,
        filterFn,
        timeframes: options.outputTimeframes,
        symbols: options.runScreener,
        filter: options.filter,
      });
    }
  }
}

main();
