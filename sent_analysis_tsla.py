# region imports
from AlgorithmImports import *
from nltk.sentiment import SentimentIntensityAnalyzer
# endregion

class AlgoTradingCourse9(QCAlgorithm):
    """ Trading bot analyse Elon Musk's tweets
        Sentiment analysis on Elon Musk's tweets which mentioned TSLA in some ways,
        If sentiment is positive, we long TSLA; if sentiment is negative, we short TSLA;
        if sentiment is neutral, we don't do anything.  
    """
    def Initialize(self):
        self.SetStartDate(2012, 11, 1)  # Set Start Date
        self.SetEndDate(2017, 1, 1)
        self.SetCash(100000)  # Set Strategy Cash

        self.tsla = self.AddEquity("TSLA", Resolution.Minute).Symbol
        self.musk = self.AddData(MuskTweet, "MUSKTWTS", Resolution.Minute).Symbol

        self.Schedule.On(self.DateRules.EveryDay(self.tsla),
                        self.TimeRules.BeforeMarketClose(self.tsla, 15),
                        self.ExitPositions)

    def OnData(self, data: Slice):
        if self.musk in data:
            score = data[self.musk].Value
            content = data[self.musk].Tweet

            if score > 0.5:
                self.SetHoldings(self.tsla, 1)
            elif score < -0.5:
                self.SetHoldings(self.tsla, -1)

            if abs(score) > 0.5:
                self.Log("Score: " + str(score) + ", Tweet: " + content)    
    
    def ExitPositions(self):
        self.Liquidate()

class MuskTweet(PythonData):
    
    sia = SentimentIntensityAnalyzer()

    def GetSource(self, config, date, isLiveMode):
        # make sure to already set dropbox url to 1
        source = "https://www.dropbox.com/s/ovnsrgg1fou1y0r/MuskTweetsPreProcessed.csv?dl=1"
        return SubscriptionDataSource(source, SubscriptionTransportMedium.RemoteFile)

    def Reader(self, config, line, date, isLiveMode):
        if not (line.strip() and line[0].isdigit()):
            return None
        
        data = line.split(",")
        tweet = MuskTweet()
        tweet.Symbol = config.Symbol
        tweet.Time = datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)
        content = data[1].lower()
        
        try:
            if "tsla" in content or "tesla" in content:
                tweet.Value = self.sia.polarity_scores(content)["compound"]
            else:
                tweet.Value = 0
            
            tweet["Tweet"] = str(content)
        except ValueError:
            return None
        
        return tweet
