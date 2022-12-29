# region imports
from AlgorithmImports import *
# endregion

class AlgoTradingCourse7(QCAlgorithm):
    """ Day Trading Bot reverse overnight gap
        when Last Close < Open: short,
        when Last Close > Open: long,
        Liquidate daily before close
    """
    def Initialize(self):
        self.SetStartDate(2018, 1, 1)  # Set Start Date
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)  # Set Strategy Cash

        self.symbol = self.AddEquity("SPY", Resolution.Minute).Symbol
        self.rollingWindow = RollingWindow[TradeBar](2)
        self.Consolidate(self.symbol, Resolution.Daily, self.CustomBarHandler)

        # call custom method at specific events
        self.Schedule.On(self.DateRules.EveryDay(self.symbol), 
                        self.TimeRules.BeforeMarketClose(self.symbol, 15),
                        self.ExitPositions)

    def OnData(self, data: Slice):
        if not self.rollingWindow.IsReady:
            return
        if not (self.Time.hour == 9 and self.Time.minute == 31):
            return
        
        if data[self.symbol].Open >= 1.01 * self.rollingWindow[0].Close:
            self.SetHoldings(self.symbol, -1)
        elif data[self.symbol].Open <= 0.99 * self.rollingWindow[0].Close:
            self.SetHoldings(self.symbol, 1)

    def CustomBarHandler(self, bar):
        self.rollingWindow.Add(bar)
    
    def ExitPositions(self):
        self.Liquidate(self.symbol)
