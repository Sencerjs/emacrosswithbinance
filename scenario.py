import ccxt, config
import pandas as pd
from ta.trend import EMAIndicator
import winsound
from smtplib import SMTP

duration = 1000
freg = 440

symbolName = input("Enter here coin name ")
symbol = str(symbolName) + "/USDT"
leverage = input("Enter Leverage Level ")
timeFrame = input("Enter Time Interval ")
slowEMAValue = input("Enter Slow EMA Value ")
fastEMAValue = input("Enter Fast EMA Value ")
buy_amount = 0

isEqual = False
inPos = False
inLongPos = False
inShortPos = False


## API Connection
exchange = ccxt.binance({

    "apiKey": config.apiKey,
    "secret": config.secretKey,
        "options":{
            "defaultType": "future"
        },  
        "enableRateLimit": True
                        })

while True:
    try:
        balance = exchange.fetch_balance()
        free_balance = exchange.fetch_free_balance()
        positions = balance["info"]["positions"]   
        newSymbol = symbolName+"USDT" 
        current_positions = [position for position in positions if float(position['positionAmt']) != 0 and position['symbol'] == newSymbol]
        position_info = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])


        ## Check Position Situation
        if not position_info.empty and position_info["positionAmt"][len(position_info.index) - 1] != 0:
            inPos = True
        else: 
            inPos = False

        ## Check Long Position
        if inPos and position_info["positionAmt"][len(position_info.index)-1] > 0:
            inLongPos = True
            inShortPos = False

        ## Check Short Position
        if inPos and position_info["positionAmt"][len(position_info.index)-1] < 0:
            inShortPos = True
            inLongPos = False

        ## Bars & DF Creation
        bars = exchange.fetch_ohlcv(symbol, timeframe = timeFrame, since = None, limit = 500)
        df = pd.DataFrame(bars, columns = ["timestamp", "open", "high", "low", "close", "volume"])

        ## EMA Slow 
        slowEMA = EMAIndicator(df["close"], float(slowEMAValue))
        df["Slow EMA"] = slowEMA.ema_indicator()

        ## EMA Fast
        fastEMA = EMAIndicator(df["close"], float(fastEMAValue))
        df["Fast EMA"] = fastEMA.ema_indicator()

        if (df["Fast EMA"][len(df.index)-3] < df["Slow EMA"][len(df.index)-3] and df["Fast EMA"][len(df.index)-2] > df["Slow EMA"][len(df.index)-2]) or (df["Fast EMA"][len(df.index)-3] > df["Slow EMA"][len(df.index)-3] and df["Fast EMA"][len(df.index)-2] < df["Slow EMA"][len(df.index)-2]):
            isEqual = True
        else: 
            isEqual = False


        ## Long Enter
        def longEnter(buy_amount):
            order = exchange.create_market_buy_order(symbol, buy_amount)
            winsound.Beep(freq, duration)
            
        ## Long Exit
        def longExit():
            order = exchange.create_market_sell_order(symbol, float(position_info["positionAmt"][len(position_info.index) - 1]), {"reduceOnly": True})
            winsound.Beep(freq, duration)

        ## Short Enter
        def shortEnter(buy_amount):
            order = exchange.create_market_sell_order(symbol, buy_amount)
            winsound.Beep(freq, duration)
            
        ## Short Exit
        def shortExit():
            order = exchange.create_market_buy_order(symbol, (float(position_info["positionAmt"][len(position_info.index) - 1]) * -1), {"reduceOnly": True})
            winsound.Beep(freq, duration)
        
        # Buy Long Bull
        if isEqual and df["Fast EMA"][len(df.index)-2] > df["Slow EMA"][len(df.index)-2] and inLongPos == False:
            if inShortPos:
                print("Short process is terminating!!!")
                shortExit()

            buy_amount = (((float(free_balance["USDT"]) / 100 ) * 10) * float(leverage)) / float(df["close"][len(df.index) - 1])
            print("Long process is starting!!!")
            
            longEnter(buy_amount)
            mailSubject = symbol
            message = "LONG ENTER\n" + "Total Balance: " + str(balance['total']["USDT"])
            content = f"Subject: {mailSubject}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))

        
        # Sell Short Bear
        if isEqual and df["Fast EMA"][len(df.index)-2] < df["Slow EMA"][len(df.index)-2] and inShortPos == False:
            if inLongPos:
                print("Long process is terminating!!!")
                longExit()
            buy_amount = (((float(free_balance["USDT"]) / 100 ) * 10) * float(leverage)) / float(df["close"][len(df.index) - 1])
            print ("Short process is starting!!!")
            shortEnter(buy_amount)
            mailSubject = symbol
            message = "SHORT ENTER\n" + "Total Balance: " + str(balance['total']["USDT"])
            content = f"Subject: {mailSubject}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
 
        if inPos == False:
            print("Looking for new position!!!")

        if inShortPos:
            print("Waiting in short position")
        if inLongPos:
            print("Waiting in long position")


    except ccxt.BaseError as Error:
            print("Error", Error)
            continue