import fs from 'fs';
import { readFile } from 'fs/promises';
import fetch from 'node-fetch';
import chalk from 'chalk';
import Indicators from 'technicalindicators';

const ATR_PERIOD = 10;
const ATR_MULTIPLIER = 2;

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
  'ONEUSDT',
  'NEARUSDT',
];
const RESOLUTIONS = [
  { interval: '1d', seedPeriod: 60 },
  { interval: '12h', seedPeriod: 120 },
  { interval: '6h', seedPeriod: 240 },
  { interval: '4h', seedPeriod: 360 },
];

function writeData(data, flag, filename) {
  fs.writeFile(`./symbols/${filename}`, JSON.stringify(data), { flag }, (err) =>
    err
      ? console.error('error: ', JSON.stringify(err))
      : console.log(`Complete writing ${filename}`)
  );
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

// Run once in the beginning to seed the tickers
async function seedSymbols(symbols, resolutions) {
  const checkpoints = [];
  // https://advancedweb.hu/how-to-use-async-functions-with-array-foreach-in-javascript/
  await Promise.all(
    symbols.map(async (symbol) => {
      await resolutions.reduce(async (memo, resol) => {
        await memo;

        const { interval, seedPeriod } = resol;
        const data = await fetchData(symbol, interval, seedPeriod);

        // write ticker data
        writeData(data, 'w', `${symbol}_${interval}.json`);

        checkpoints.push({
          symbol,
          interval,
          checkpoint: `${Object.values(data).at(-1)[0]}`,
        });
      }, undefined);
    })
  );

  // write ticker datetime checkpoints
  console.log(checkpoints);
  writeData(
    JSON.stringify(checkpoints).replace(/\\/g, ''),
    'w',
    'checkpoint.json'
  );
}

async function fetchFromCheckpoint(symbols, resolutions) {
  const checkpointsJson = await readFile(`./symbols/checkpoint.json`);
  const checkpoints = JSON.parse(checkpointsJson);
  console.log(checkpoints);
  const nowUTC = Date.parse(new Date());
  const H4 = 14400;
  const H6 = 21600;
  const H12 = 43200;
  const D1 = 86400;
  // await Promise.all(
  //   symbols.map(async (symbol) => {
  //     await resolutions.reduce(async (memo, resol) => {
  //       await memo;

  //       const { interval, seedPeriod } = resol;
  //       const data = await fetchData(symbol, interval, seedPeriod);

  //       // write ticker data
  //       writeData(data, 'w', `${symbol}_${interval}.json`);
  //     }, undefined);
  //   })
  // );
}

async function SuperTrend(
  data,
  atrPeriod = ATR_PERIOD,
  multiplier = ATR_MULTIPLIER
) {
  const datetime = data.map((pt) => pt[6]);
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

    return [
      new Date(datetime[idx + atrPeriod]).toLocaleString('en-US'),
      bot1,
      top1,
      trend,
      buySignal,
      sellSignal,
    ];
  });

  return band;
}

// await seedSymbols(SYMBOLS, RESOLUTIONS);

await fetchFromCheckpoint();
// const H12 = await SuperTrend('BTCUSDT', '12h', 250);

// [...Array(250 - ATR_PERIOD)].forEach((x, i) => {
//   console.log(i, H12[i][0], H12[i][1], H12[i][2], H12[i][3]);
// });
