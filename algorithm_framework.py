# region imports
from AlgorithmImports import *
# endregion

class AlgoTradingCourse14(QCAlgorithm):
    """ Algorithm framework:
        1. Universe selection (new)
        2. Alpha model (new)
        3. Portfolio construction (built-in)
        4. Transaction cost (built-in)
        5. Risk management (built-in)
        6. Execution (built-in)

        e.g., buy and hold quality US stocks: 
            (1) IPO'd 5+ years, 
            (2) invest in different sectors (financial services, real estate, healthcare, utilities, technology)
            (3) consider the factors (rank by PERatio, Margins, ROE) and invest in top 20% of each sector
            Rebalance Quarterly
    """
    def Initialize(self):
        self.SetStartDate(2019, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000) 

        self.month = 0 # help to keep track rebalancing times
        self.num_coarse = 500 # num of stocks in coarse universe selection

        # universe selection
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        # alpha model
        self.AddAlpha(FundamentalFactorAlphaModel())
        # portfolio construction
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel(self.IsRebalanceDue))
        # risk management
        self.SetRiskManagement(NullRiskManagementModel())
        # execution model
        self.SetExecution(ImmediateExecutionModel())
    
    def IsRebalanceDue(self, time):
        # relance quarterly
        if time.month == self.month or time.month not in [1, 4, 7, 10]:
            return None
        
        self.month = time.month
        return time

    def CoarseSelectionFunction(self, coarse):
        if not self.IsRebalanceDue(self.Time):
            return Universe.Unchanged
        
        # ignore stocks with very low price or does not have fundamental data
        selected = sorted([x for x in coarse if x.HasFundamentalData and x.Price > 5],
                            key = lambda x: x.DollarVolume, reverse = True)

        return [x.Symbol for x in selected[:self.num_coarse]]

    def FineSelectionFunction(self, fine):
        sectors = [
            MorningstarSectorCode.FinancialServices,
            MorningstarSectorCode.RealEstate,
            MorningstarSectorCode.Healthcare,
            MorningstarSectorCode.Utilities,
            MorningstarSectorCode.Technology
        ]

        filtered_fine = [x.Symbol for x in fine 
                            if x.SecurityReference.IPODate + timedelta(5 * 365) < self.Time
                            and x.AssetClassification.MorningstarSectorCode in sectors
                            and x.OperationRatios.ROE.Value > 0
                            and x.OperationRatios.NetMargin.Value > 0
                            and x.ValuationRatios.PERatio > 0]
        
        return filtered_fine

class FundamentalFactorAlphaModel(AlphaModel):
    
    def __init__(self):
        self.rebalanceTime = datetime.min
        self.sectors = {} # sectors = {technology: set(AAPL, TSLA, ...), healthcare: set(ABC, ...)}
    
    def Update(self, algorithm, data):
        if algorithm.Time <= self.rebalanceTime:
            return []
        self.rebalanceTime = Expiry.EndOfQuarter(algorithm.Time)
        insights = []

        for sector in self.sectors:
            securities = self.sectors[sector]
            sortedByROE = sorted(securities, key=lambda x: x.Fundamentals.OperationRatios.ROE.Value, reverse=True)
            sortedByPM = sorted(securities, key=lambda x: x.Fundamentals.OperationRatios.NetMargin.Value, reverse=True)
            sortedByPE = sorted(securities, key=lambda x: x.Fundamentals.ValuationRatios.PERatio, reverse=False)

            scores = {}
            for security in securities:
                # lower the better
                score = sum([sortedByROE.index(security), sortedByPM.index(security), sortedByPE.index(security)])
                scores[security] = score
            
            # get #stocks that are top 20%, at least 1
            length = max(int(len(scores) / 5), 1)
            for security in sorted(scores.items(), key=lambda x: x[1], reverse=False)[:length]:
                symbol = security[0].Symbol
                insights.append(Insight.Price(symbol, Expiry.EndOfQuarter, InsightDirection.Up))
        
        return insights

    def OnSecuritiesChanged(self, algorithm, changes):
        for security in changes.RemovedSecurities:
            for sector in self.sectors:
                if security in self.sectors[sector]:
                    self.sectors[sector].remove(security)
        
        for security in changes.AddedSecurities:
            sector = security.Fundamentals.AssetClassification.MorningstarSectorCode
            if security not in self.sectors:
                self.sectors[sector] = set()
            self.sectors[sector].add(security)
