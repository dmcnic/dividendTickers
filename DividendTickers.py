#!/usr/bin/env python

import datetime
import numpy as np
import csv
import pandas_datareader as pdr


def main(championTickers, champWatch, tickerSource):
    beginDate = datetime.datetime.now() - datetime.timedelta(days = 365)
    # Sort the ending date to today
    endDate = datetime.datetime.now()

    # begin a loop through all of the tickers in dividend champions
    for ticker in championTickers:

        # grab the data from Yahoo!
        try:
            # price = finance.fetch_historical_yahoo(ticker, beginDate, endDate)
            # price = pdr.get_data_yahoo(ticker, beginDate, endDate)
            priceRecord = pdr.DataReader(ticker, 'google', beginDate, endDate)
            priceRecordDF = priceRecord.iloc[::-1]
        except:
            print(ticker + ' failure...')
            break

        # start with the 20-day moving average
        ma20day = np.mean(priceRecordDF.Close[:20])
        counter = 0

        # Need to calculate Bollinger Bands and RSI and 12-day Rate of Change
        # Bollinger Bands are 20-day SMA +/- 20-day standard deviation * 2
        st20day = np.std(priceRecordDF.Close[:20])
        lowerBound = ma20day - 2 * st20day
        upperBound = ma20day + 2 * st20day
        bollPct = (priceRecordDF.Close[0] - lowerBound) / (upperBound - lowerBound) * 100
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

        # ROC calculation is close divided by close twelve trading days ago
        ROC = priceRecordDF.Close[0] / priceRecordDF.Close[12] - 1
        if ROC < -.1:
            counter += 1

        # append the ticker and technical measures to csv file
        if tickerSource == 'DividendChampions':
            with open('ChampionResult.csv', 'a', newline = '') as fileOut:
                champWriter = csv.writer(fileOut)
                champWriter.writerow([ticker, priceRecordDF.Close[0], round(bollPct, 2), round(lowerBound, 2), round(RSI, 1), round(ROC * 100, 1), counter])

            # if counter == 3, add ticker to watchlist
            if counter == 3:
                champWatch[ticker] = "Added to watchlist"
                print("{0} added to Champion watchlist".format(ticker))
            elif ticker in champWatch:
                # with counter less than 3, check to see if RSI < 30
                if RSI < 30:
                    champWatch[ticker] = "Waiting for RSI"
                    print("Champion {0} is waiting for RSI".format(ticker))
                else:
                    # with RSI > 30
                    # if ticker in watchlist and value = "Buy" then remove
                    if ticker in champWatch:
                        if champWatch[ticker] == "Buy":
                            del champWatch[ticker]
                        elif counter == 0:
                            champWatch[ticker] = "Buy"
                            print("Champion {0} is a new buy".format(ticker))
                        else:
                            champWatch[ticker] = "Investigate"
                            print("Champion {0} needs investigation".format(ticker))
        elif tickerSource == 'DailyPaycheck':
            with open('PaycheckResult.csv', 'a', newline = '') as fileOut:
                paycheckWriter = csv.writer(fileOut)
                paycheckWriter.writerow([ticker, priceRecordDF.Close[0], round(bollPct, 2), round(lowerBound, 2), round(RSI, 1), round(ROC * 100, 1), counter])

            # if counter == 3, add ticker to watchlist
            if counter == 3:
                paycheckWatch[ticker] = "Added to watchlist"
                print("{0} added to DailyPaycheck watchlist".format(ticker))
            elif ticker in paycheckWatch:
                # with counter less than 3, check to see if RSI < 30
                if RSI < 30:
                    paycheckWatch[ticker] = "Waiting for RSI"
                    print("DailyPaycheck {0} is waiting for RSI".format(ticker))
                else:
                    # with RSI > 30
                    # if ticker in watchlist and value = "Buy" then remove
                    if ticker in paycheckWatch:
                        if paycheckWatch[ticker] == "Buy":
                            del paycheckWatch[ticker]
                        elif counter == 0:
                            paycheckWatch[ticker] = "Buy"
                            print("DailyPaycheck {)} is a new buy".format(ticker))
                        else:
                            paycheckWatch[ticker] = "Investigate"
                            print("DailyPaycheck {)} needs investigation".format(ticker))

    # write the watchlist
    if tickerSource == 'DividendChampions':
        try:
            with open('ChampionWatchlist.csv', 'w', newline='') as f:
                w = csv.DictWriter(f, fieldnames = ['Ticker', 'Status'])
                w.writeheader()
                for i in champWatch.keys():
                    w.writerow({'Ticker' : i, 'Status' : champWatch[i]})
        except:
            print("Stopping at ticker: {0}".format(ticker))
    elif tickerSource == 'DailyPaycheck':
        try:
            with open('PaycheckWatchlist.csv', 'w', newline = '') as f:
                w = csv.DictWriter(f, fieldnames = ['Ticker', 'Status'])
                w.writeheader()
                for i in paycheckWatch.keys():
                    w.writerow({'Ticker' : i, 'Status' : paycheckWatch[i]})
        except:
            print("Stopping at ticker: {0}".format(ticker))

    return


if __name__ == '__main__':
    # Create an empty list for the ticker symbols
    tickerList = []

    # grab the ticker list
    # tickerPortfolio = sys.argv[1]

    # Read the tickers from the csv file
    with open('DividendChampion.csv', 'r') as tickerFile:
        tickerReader = csv.reader(tickerFile)
        for symbol in tickerReader:
            if symbol != 'FMCB':
                tickerList.extend(symbol)

    # Create the new output file by only printing the headers
    with open('ChampionResult.csv', 'w', newline = '') as fileOut:
        champWriter = csv.writer(fileOut)
        champWriter.writerow(['Ticker', 'Close', 'Boll Pct', 'Lower Bound', 'RSI', 'ROC', 'Count'])

    # load the watchlist
    champWatch = {}
    with open('ChampionWatchlist.csv', 'r') as watchlist:
        reader = csv.DictReader(watchlist)
        for row in reader:
            champWatch[row["Ticker"]] = row["Status"]


    main(tickerList, champWatch, "DividendChampions")

    # create an empty list for the ticker symbols
    tickerList = []

    # read the tickers from the csv file
    with open('DailyPaycheck.csv', 'r') as tickerFile:
        tickerReader = csv.reader(tickerFile)
        for symbol in tickerReader:
            tickerList.extend(symbol)

    # create the new output file by only printing the headers
    with open('PaycheckResult.csv', 'w', newline = '') as fileOut:
        paycheckWriter = csv.writer(fileOut)
        paycheckWriter.writerow(['Ticker', 'Close', 'Boll Pct', 'Lower Bound', 'RSI', 'ROC', 'Count'])

    # load the watchlist
    paycheckWatch = {}
    with open('PaycheckWatchlist.csv', 'r') as watchlist:
        reader = csv.DictReader(watchlist)
        for row in reader:
            paycheckWatch[row["Ticker"]] = row["Status"]

    main(tickerList, paycheckWatch, "DailyPaycheck")
