# region imports
from AlgorithmImports import *
from System.Drawing import Color
# endregion

class AlgoTradingCourse11(QCAlgorithm):
    """ Forex trading with EUR/USD pair - Bollinger bands:
        Expect the price to stay close to the 20-moving average +/- 2*std,
        if price > 2*std + mean: Short EUR/USD,
        if price < -2*std + mean: Long EUR/USD
    """
    def Initialize(self):
        self.SetStartDate(2015, 1, 1)  # Set Start Date
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)  # Set Strategy Cash
        self.pair = self.AddForex("EURUSD", Resolution.Daily, Market.FXCM).Symbol
        # Bollinger bands with 20-day moving average, 2 std
        self.bb = self.BB(self.pair, 20, 2) 

        stockPlot = Chart("Trade Plot")
        stockPlot.AddSeries(Series("Buy", SeriesType.Scatter, "$",
                            Color.Green, ScatterMarkerSymbol.Triangle))
        stockPlot.AddSeries(Series("Sell", SeriesType.Scatter, "$",
                            Color.Red, ScatterMarkerSymbol.Triangle))
        stockPlot.AddSeries(Series("Liquidate", SeriesType.Scatter, "$",
                            Color.Blue, ScatterMarkerSymbol.Triangle))
        
        self.AddChart(stockPlot)

    def OnData(self, data: Slice):
        if not self.bb.IsReady:
            return
        price = data[self.pair].Price

        self.Plot("Trade Plot", "Price", price)
        self.Plot("Trade Plot", "Middle", self.bb.MiddleBand.Current.Value)
        self.Plot("Trade Plot", "Upper", self.bb.UpperBand.Current.Value)
        self.Plot("Trade Plot", "Lower", self.bb.LowerBand.Current.Value)

        if not self.Portfolio.Invested:
            if self.bb.LowerBand.Current.Value > price:
                self.SetHoldings(self.pair, 1)
                self.Plot("Trade Plot", "Buy", price)
            elif self.bb.UpperBand.Current.Value < price:
                self.SetHoldings(self.pair, -1)
                self.Plot("Trade Plot", "Sell", price)
        else:
            if self.Portfolio[self.pair].IsLong:
                if self.bb.MiddleBand.Current.Value < price:
                    self.Liquidate()
                    self.Plot("Trade Plot", "Liquidate", price)
            elif self.bb.MiddleBand.Current.Value > price:
                self.Liquidate()
                self.Plot("Trade Plot", "Liquidate", price)
