# region imports
from AlgorithmImports import *
# endregion

class AlgoTradingCourse8(QCAlgorithm):
    """ Dynamic Universe based on paper: Size Factor - Small Capitalisation Stocks Premium
        - Idea: small stock outperforms large stocks because (1) more liquidity, (2) more room to grow
        - Implementation: 
            - A Coarse filter which filters out the top 200 most liquid stocks out of 3000,
            - Then a fine filter which filters out the top 10 market-cap stocks,
            - Rebalance the universe once a month
    """
    def Initialize(self):
        self.SetStartDate(2019, 1, 1)  # Set Start Date
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)  # Set Strategy Cash

        self.rebalanceTime = datetime.min
        self.activeStocks = set()

        self.AddUniverse(self.CoarseFilter, self.FineFilter)
        self.UniverseSettings.Resolution = Resolution.Hour

        self.portfolioTargets = []

    def CoarseFilter(self, coarse):
        if self.Time <= self.rebalanceTime:
            return self.Universe.Unchanged
        self.rebalanceTime = self.Time + timedelta(30)
        sortedByDollarVolume = sorted(coarse, key = lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in sortedByDollarVolume if x.Price > 10 
                and x.HasFundamentalData][:200]

    def FineFilter(self, fine):
        sortedByPE = sorted(fine, key = lambda x:x.MarketCap)
        return [x.Symbol for x in sortedByPE if x.MarketCap > 0][:10]
    
    def OnSecuritiesChanged(self, changes):
        for x in changes.RemovedSecurities:
            self.Liquidate(x.Symbol)
            self.activeStocks.remove(x.Symbol)
        
        for x in changes.AddedSecurities:
            self.activeStocks.add(x.Symbol)
        
        self.portfolioTargets = [PortfolioTarget(symbol, 1/len(self.activeStocks)) 
                                    for symbol in self.activeStocks]

    def OnData(self, data: Slice):
        if self.portfolioTargets == []:
            return
        for symbol in self.activeStocks:
            if symbol not in data:
                return
        # make sure data for all stocks are added correctly before moving forward
        self.SetHoldings(self.portfolioTargets)
        self.portfolioTargets = []
