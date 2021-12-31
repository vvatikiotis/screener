import fetch from 'node-fetch';
import Indicators from 'technicalindicators';

const MULTIPLIER = 2;
const PERIOD = 150;
const ATR_PERIOD = 10;
const response = await fetch(
  'https://api.binance.com/api/v3/klines?' +
    new URLSearchParams({
      symbol: 'BTCUSDT',
      interval: '1h',
      limit: PERIOD,
    })
);

const data = await response.json();
// const slicedData = data.slice(ATR_PERIOD - 1, PERIOD);
const src = data.map((pt) => (parseFloat(pt[2]) + parseFloat(pt[3])) / 2);
const highs = data.map((pt) => pt[2]);
const lows = data.map((pt) => pt[3]);
const closes = data.map((pt) => pt[4]);
const ATR = Indicators.atr({
  period: ATR_PERIOD, // SuperTrend param
  high: highs,
  low: lows,
  close: closes,
});

// (H - L) /2
let bot1 = src[ATR_PERIOD] - MULTIPLIER * ATR[0];
let top1 = src[ATR_PERIOD] + MULTIPLIER * ATR[0];
let trend = 1;
let trend1 = 1;
const band = ATR.map((atr, idx) => {
  const closeIdx = ATR_PERIOD + idx;
  const close = closes[closeIdx];

  const bot = src[idx + ATR_PERIOD] - MULTIPLIER * atr;
  bot1 = closes[closeIdx - 1] > bot1 ? Math.max(bot, bot1) : bot;

  const top = src[idx + ATR_PERIOD] + MULTIPLIER * atr;
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
    top1,
    bot1,
    trend,
    buySignal ? 'Buy' : '--',
    sellSignal ? 'Sell' : '--',
  ];
});
const crosses = Indicators.CrossDown.calculate({
  lineA: closes.slice(-(PERIOD - ATR_PERIOD)),
  lineB: band,
});
[...Array(140)].forEach((x, i) => console.log(i, ...band[i]));
// console.log(src.slice(-20), downLine.slice(-20), crosses.slice(-20));
