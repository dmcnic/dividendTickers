#!/usr/bin/env python

from datetime import datetime, timedelta
from pytz import timezone
import numpy as np
import csv
import sys
import pandas_datareader as pdr


def main(championTickers, champWatch, tickerSource, resultFile, watchlistFile):
    # Load in the double dividend tickers
    ddTickers = []

    # read the tickers from the csv file
    with open(r'DoubleDividends.csv', 'r') as ddTickerFile:
        ddTickerReader = csv.reader(ddTickerFile)
        for symbol in ddTickerReader:
            ddTickers.extend(symbol)

    beginDate = datetime.now() - timedelta(days = 365)
    # Sort the ending date to today
    endDate = datetime.now()

    # begin a loop through all of the tickers in dividend champions
    for ticker in championTickers:
        # Find out if the ticket is a double dividend candidate
        ddFlag = False
        if ticker in ddTickers:
            ddFlag = True
        # grab the data from Google
        try:
            # price = finance.fetch_historical_yahoo(ticker, beginDate, endDate)
            # price = pdr.get_data_yahoo(ticker, beginDate, endDate)
            priceRecord = pdr.DataReader(ticker, 'google', beginDate, endDate)
            priceRecordDF = priceRecord.iloc[::-1]
        except:
            print(ticker + ' failure...')
            sys.exit(0)

        # start with the 20-day moving average
        ma20day = np.mean(priceRecordDF.Close[:20])
        counter = 0

        # Need to calculate Bollinger Bands and RSI and 12-day Rate of Change
        # Bollinger Bands are 20-day SMA +/- 20-day standard deviation * 2
        st20day = np.std(priceRecordDF.Close[:20])
        lowerBound = ma20day - 2 * st20day
        upperBound = ma20day + 2 * st20day
        try:
            bollPct = (priceRecordDF.Close[0] - lowerBound) / (upperBound - lowerBound) * 100
        except:
            print(ticker + ' Bollinger failure...')
            sys.exit(0)
        if bollPct < 0:
            counter += 1

        # RSI is multi-step
        # First Average Gain = Sum of Gains over the Past 14 Periods / 14
        # First Average Loss = Sum of Losses over the Past 14 Periods / 14
        # Subsequent calculations are:
        # Average Gain = [(previous average gain * 13) + current gain] / 14
        # Average Loss = [(previous average loss * 13) + current loss] / 14
        # RS = average gain / average loss
        # RSI = 100 - 100 / (1 + RS)
        priceChange = (np.diff(priceRecordDF.Close) * -1).tolist()
        priceChange.reverse()

        priceGain = 0.0
        priceLoss = 0.0

        if len(priceChange) > 13:
            for i in range(14):
                if priceChange[i] > 0:
                    priceGain += priceChange[i]
                    if priceChange[i] < 0:
                        priceLoss += abs(priceChange[i])

                        priceGain = priceGain / 14.0
                        priceLoss = priceLoss / 14.0

            for i in range(14, len(priceChange)):
                if priceChange[i] > 0:
                    priceGain = (priceGain * 13.0 + priceChange[i]) / 14.0
                    priceLoss = (priceLoss * 13.0) / 14.0
                else:
                    priceGain = (priceGain * 13.0) / 14.0
                    priceLoss = (priceLoss * 13.0 + abs(priceChange[i])) / 14.0

            if priceLoss > 0:
                RS = (priceGain / len(priceChange)) / (priceLoss / len(priceChange))
                RSI = 100.0 - 100.0 / ( 1.0 + RS)
            else:
                RSI = 100

            if RSI < 30:
                counter += 1
        else:
            RSI = 100

        # ROC calculation is close divided by close twelve trading days ago
        if len(priceRecordDF.index) > 13:
            ROC = priceRecordDF.Close[0] / priceRecordDF.Close[12] - 1
            if ROC < -.1:
                counter += 1
        else:
            ROC = 0

        # append the ticker and technical measures to csv file
        with open(resultFile, 'a', newline = '') as fileOut:
            champWriter = csv.writer(fileOut)
            champWriter.writerow([ticker, priceRecordDF.Close[0],
                        round(bollPct, 2), round(lowerBound, 2), round(RSI, 1),
                        round(ROC * 100, 1), counter])
        # if counter == 3, add ticker to watchlist
        if counter == 3:
            champWatch[ticker] = "Added to watchlist"
            print("{0} added to {1} watchlist DD = {2}".format(ticker,
                    tickerSource, ddFlag))
        elif ticker in champWatch:
            # with counter less than 3, check to see if RSI < 30
            if RSI < 30:
                champWatch[ticker] = "Waiting for RSI"
                print("{0} {1} is waiting for RSI DD = {2}".format(tickerSource,
                        ticker, ddFlag))
            else:
                # with RSI > 30
                # if ticker in watchlist and value = "Buy" then remove
                if ticker in champWatch:
                    if champWatch[ticker] == "Buy":
                        del champWatch[ticker]
                    elif counter == 0:
                        champWatch[ticker] = "Buy"
                        print("{0} {1} is a new buy DD = {2}".format(tickerSource,
                                ticker, ddFlag))
                    else:
                        champWatch[ticker] = "Investigate"
                        print("{0} {1} needs investigation DD = {2}".format(tickerSource,
                                ticker, ddFlag))
    # write the watchlist
    try:
        with open(watchlistFile, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames = ['Ticker', 'Status'])
            w.writeheader()
            for i in champWatch.keys():
                w.writerow({'Ticker' : i, 'Status' : champWatch[i]})
    except:
        print("Stopping at ticker: {0}".format(ticker))

    return


def processFile(csvTickerFile, csvResultFile, csvWatchlistFile, descriptor):
    # create an empty list for the ticker symbols
    tickerList = []

    # Find the tickers without Google Finance data
    badTickers = []
    with open('DividendBadTickers.csv', 'r') as badFile:
        tickerReader = csv.reader(badFile)
        for symbol in tickerReader:
            badTickers.extend(symbol)
    
    # read the tickers from the csv file
    with open(csvTickerFile, 'r') as tickerFile:
        tickerReader = csv.reader(tickerFile)
        for symbol in tickerReader:
            if symbol[0] not in badTickers:
                tickerList.extend(symbol)

    # create the new output file by only printing the headers
    with open(csvResultFile, 'w', newline = '') as fileOut:
        csvResultWriter = csv.writer(fileOut)
        csvResultWriter.writerow(['Ticker', 'Close', 'Boll Pct', 'Lower Bound', 'RSI', 'ROC', 'Count'])

    # load the watchlist
    csvWatch = {}
    with open(csvWatchlistFile, 'r') as watchlist:
        reader = csv.DictReader(watchlist)
        for row in reader:
            csvWatch[row["Ticker"]] = row["Status"]

    main(tickerList, csvWatch, descriptor, csvResultFile, csvWatchlistFile)
    return


def whenIsNow():
    return datetime.now(tz = timezone('US/Pacific')).strftime('%m/%d/%Y %I:%M:%S %p')


if __name__ == '__main__':
    print('***** Beginning Dividend Tickers code at', whenIsNow(), ' *****')
    print(' ** Beginning Dividend Champions at', whenIsNow(), ' **')
    processFile('DividendChampion.csv', 'ChampionResultCCC.csv', \
                'ChampionWatchlistCCC.csv', 'DividendChampions')
    print(' ** Beginning Dividend Contenders at', whenIsNow(), ' **')
    processFile('DividendContenders.csv', 'ContenderResultCCC.csv', \
                'ContenderWatchlistCCC.csv', 'DividendContenders')
    print(' ** Beginning Dividend Challengers at', whenIsNow(), ' **')
    processFile('DividendChallengers.csv', 'ChallengerResultCCC.csv', \
                'ChallengerWatchlistCCC.csv', 'DividendChallengers')
    print('***** Ending Dividend Tickers code at', whenIsNow(), ' *****')
