import fs, { constants } from 'fs';
import { readFile, writeFile, access } from 'fs/promises';
import fetch from 'node-fetch';
import { Command } from 'commander/esm.mjs';
import chalk from 'chalk';
import Indicators from 'technicalindicators';

// -----------------------------------------------------
// HACK these and you are ready to go
const SYMBOLS = [
  'BTCUSDT',
  'ETHUSDT',
  'SOLUSDT',
  'AVAXUSDT',
  'LUNAUSDT',
  'DOTUSDT',
  'MATICUSDT',
  'ADAUSDT',
  'ATOMUSDT',
  'ONEUSDT',
  'EGLDUSDT',
  'LINKUSDT',
  'FTMUSDT',
  'NEARUSDT',
  'DUSKUSDT',
  'SYSUSDT',
  'ZILUSDT',
];
// timeframes and number of bars for seeding
const RESOLUTIONS = [
  { interval: '1d', seedPeriod: 120 },
  { interval: '12h', seedPeriod: 240 },
  { interval: '6h', seedPeriod: 480 },
  { interval: '4h', seedPeriod: 720 },
];
// Seconds in a given timeframe
// Used to calculate the update diff
const I2SECS = {
  '4h': 14400,
  '6h': 21600,
  '12h': 43200,
  '1d': 86400,
};
// TODO: maybe pass trim as an func argument?
// Number of bars we are intereted in, per timeframe
// Used only in output
const GETLASTPERIODS = {
  '1d': 2,
  '12h': 4,
  '6h': 8,
  '4h': 12,
};
// End HACK
// -----------------------------------------------------

//
// this will run immediately
//
function hasDuplicateSymbols(symbols = SYMBOLS) {
  const duplicates = symbols.filter(
    (item, index) => index !== symbols.indexOf(item)
  );

  return duplicates.length !== 0;
}

async function fetchData(symbol, interval, limit) {
  const response = await fetch(
    'https://api.binance.com/api/v3/klines?' +
      new URLSearchParams({
        symbol,
        interval,
        limit,
      })
  );

  return await response.json();
}

//
//
//
const DATA_PATH = './symbols';
async function writeJsonFile(data, flag, filename) {
  try {
    let writeData;
    if (flag === 'a') {
      const oldJsonData = await readJsonFile(filename);
      const oldData = JSON.parse(oldJsonData);
      writeData = oldData.concat(data);
    } else writeData = data;

    await writeFile(`${DATA_PATH}/${filename}`, JSON.stringify(writeData), {
      flag: 'w',
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
        } catch (err) {
          console.log(
            `rebuildCheckpoints() :: cannot find ${DATA_PATH}/${symbol}_${interval}.json`,
            err
          );
          throw err;
        }

        const checkpoint = Object.values(JSON.parse(data)).at(-1)[6];
        checkpoints.push({
          symbol,
          interval,
          checkpoint,
        });
      }, undefined);
    })
  );

  // write ticker close datetime
  console.log(
    'rebuildCheckpointsForSymbols() :: Found following checkpoints\n',
    checkpoints
  );
  writeJsonFile(checkpoints, 'w', 'checkpoints.json');

  return checkpoints;
}

//
// fetch all symbols
//
async function fetchSymbols(symbols, resolutions) {
  let checkpoints = [];
  try {
    const checkpointsJson = await readJsonFile(`checkpoints.json`);
    checkpoints = JSON.parse(checkpointsJson);
  } catch (err) {
    console.log('fetchSymbols() :: Cannot find checkpoints file', err);
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
            checkpoint = `${Object.values(fetchedData).at(-1)[6]}`;
            didSeed = true;
          }
        } else {
          const nowUTC = Date.parse(new Date());
          let diff;

          // checkpoint is close datetime. Binance API sets current bar's
          // close datetime in the future. So, nowUTC - checkpoint is negative
          const needUpdate = (diff = (nowUTC - checkpoint) / 1000) > 0;

          needUpdate &&
            console.log(`fetchSymbols() :: Updating ${symbol} ${interval} ...`);
          fetchedData = needUpdate
            ? await fetchData(
                symbol,
                interval,
                diff === nowUTC / 1000
                  ? seedPeriod
                  : Math.floor(diff / I2SECS[interval]) + 1
              )
            : undefined;
        }

        if (fetchedData) {
          writeJsonFile(fetchedData, didSeed ? 'w' : 'a', symbolFname);
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
    writeJsonFile(nextCheckpoints, 'w', 'checkpoints.json');
  }
}

//
//
//
function iterate(filterFn) {
  return async function (symbols = SYMBOLS, resolutions = RESOLUTIONS) {
    console.log(`//\n// Start processing ${filterFn.name}\n//`);
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
            return {
              ...(await memo),
              [interval]: filterFn(data).slice(-GETLASTPERIODS[interval]),
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
//
//
function output(results, symbols = SYMBOLS, resolutions = RESOLUTIONS) {
  symbols.forEach((symbol) => {
    console.log(`===== ${symbol} =====`);

    resolutions.forEach((resolution) => {
      const interval = results[symbol][resolution.interval];
      console.log(resolution.interval);
      console.log(
        interval.map(({ openDT, trend }) => ({
          openDT,
          trend,
        }))
      );
    });

    console.log('\n\n');
  });
}

//
//
//
function SuperTrend(atrPeriod = 10, multiplier = 2) {
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

      // console.log({
      //   date: new Date(datetime[idx + atrPeriod]).toLocaleString('en-US'),
      //   bot1,
      //   top1,
      //   trend,
      //   buySignal,
      //   sellSignal,
      // });
      return {
        openDT: new Date(openDT[idx + atrPeriod]).toLocaleString('en-US'),
        closeDT: new Date(closeDT[idx + atrPeriod]).toLocaleString('en-US'),
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
function createDirs() {
  if (!fs.existsSync(DATA_PATH)) {
    fs.mkdirSync(DATA_PATH);
    console.log(`createDirs() :: ${DATA_PATH} dir has been created`);
  }
}

//
//
//
async function main() {
  createDirs();

  if (hasDuplicateSymbols()) {
    console.log('exit code 1: Duplicate symbols');
    process.exit(1);
  }

  const program = new Command();
  program
    .option(
      '-s, --run-supertrend [symbols...]',
      'run supertrend on fetched symbols'
    )
    .option('-f, --fetch-symbols', 'fetch symbols, in code')
    .option(
      '-b, --rebuild-from-symbols',
      'rebuild checkpoints file from symbols data'
    );

  program.parse();

  const options = program.opts();

  if (options.fetchSymbols) fetchSymbols(SYMBOLS, RESOLUTIONS);
  if (options.rebuildFromSymbols)
    rebuildCheckpointsForSymbols(SYMBOLS, RESOLUTIONS);

  if (options.runSupertrend) {
    let results;
    const fnST = SuperTrend();

    // -s only
    if (options.runSupertrend === true) {
      results = await iterate(fnST)();
      output(results);
    } else {
      // -s symbol
      results = await iterate(fnST)(options.runSupertrend);
      output(results, options.runSupertrend);
    }
  }
}

main();
