# region imports
from AlgorithmImports import *
from collections import deque
# endregion

class AlgoTradingCourse6(QCAlgorithm):
    """ Identify uptrend or downtred using SMA,
        compare current price of `SPY`
        with its 52-week high and low:
            - Uptrend + Near High = Buy
            - Downtrend + Near Low = Sell
    """
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)  # Set Start Date
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)  # Set Strategy Cash
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
        # self.sma = self.SMA(self.spy, 30, Resolution.Daily) # 30 day simple moving average
        # pump histroy data into the indicator first
        # closing_prices = self.History(self.spy, 30, Resolution.Daily)["close"] # last 30 days
        # for time, price in closing_prices.loc[self.spy].items():
        #     self.sma.Update(time, price)

        # alternatively we can create our custom sma indicator
        self.sma = CustomSimpleMovingAverage("CustomSMA", 30)
        self.RegisterIndicator(self.spy, self.sma, Resolution.Daily)
        

    def OnData(self, data: Slice):
        if not self.sma.IsReady:
            return
        # inefficient method because we are requesting similar data again and again
        # more efficient alternative is rolling window or minimum or maximum indicators
        hist = self.History(self.spy, timedelta(365), Resolution.Daily)
        low = min(hist["low"])
        high = max(hist["high"])

        price = self.Securities[self.spy].Price
        if price * 1.05 >= high and self.sma.Current.Value < price:
            if not self.Portfolio[self.spy].IsLong:
                self.SetHoldings(self.spy, 1)
        elif price * 0.95 <= low and self.sma.Current.Value > price:
            if not self.Portfolio[self.spy].IsShort:
                self.SetHoldings(self.spy, -1)
        else:
            self.Liquidate(self.spy)
        

        # Benchmark chart is an existing chart with SPY price on it
        self.Plot("Benchmark", "52w-High", high)
        self.Plot("Benchmark", "52w-Low", low)
        self.Plot("Benchmark", "SMA", self.sma.Current.Value)

class CustomSimpleMovingAverage(PythonIndicator):
    def __init__(self, name, period):
        self.Name = name
        self.Time = datetime.min
        self.Value = 0
        self.queue = deque(maxlen=period) # 30 day period

    def Update(self, input):
        self.queue.appendleft(input.Close) # recent left, old values right
        self.Time = input.EndTime
        count = len(self.queue)
        self.Value = sum(self.queue) / count
        return (count == self.queue.maxlen) # return True if queue IsReady
