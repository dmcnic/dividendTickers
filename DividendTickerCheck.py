#!/usr/bin/env python

import csv
from datetime import datetime, timedelta
from pytz import timezone
import pandas_datareader as pdr
import numpy as np


def whenIsNow():
    return datetime.now(tz = timezone('US/Pacific')).strftime('%m/%d/%Y %I:%M:%S %p')


def main():
    # Load the bad tickers
    badTickers = []
    with open('DividendBadTickers.csv', 'r') as badFile:
        tickerReader = csv.reader(badFile)
        for symbol in tickerReader:
            badTickers.extend(symbol)

    # Set the date range
    beginDate = datetime.now() - timedelta(days = 365)
    endDate = datetime.now()

    # Loop through the ticker list
    for eachSymbol in badTickers:
        # Set the flags
        existFlag = True
        bbFlag = True
        rsiFlag = True
        rocFlag = True
        # Check to see if the ticker exists at Google finance
        try:
            priceRecord = pdr.DataReader(eachSymbol, 'google',
                                         beginDate, endDate)
            priceRecordDF = priceRecord.iloc[::-1]
        except:
            print(' {0} ticker failure...'.format(eachSymbol), flush = True)
            existFlag= False
        # Check to see if there are 20 days for the Bollinger Bands
        if existFlag == True:
            if len(priceRecordDF.index) < 21:
                print(' {0} price history too short for Bollinger'.format(eachSymbol),
                      flush = True)
                bbFlag = False
        # Check to see if there is enough data for RSI
        if existFlag == True and bbFlag == True:
            priceChange = (np.diff(priceRecordDF.Close) * -1).tolist()
            if len(priceChange) < 14:
                print(' {0} price history too short for RSI'.format(eachSymbol),
                      flush = True)
                rsiFlag = False
        # Check to see if there is enough data for Rate Of Change
        if existFlag == True and bbFlag == True and rsiFlag == True:
            if len(priceRecordDF.index) < 14:
                print(' {0} price history too short for ROC'.format(eachSymbol),
                      flush = True)
                rocFlag = False
        # Check results of all tests
        if existFlag == True and bbFlag == True and rsiFlag == True and rocFlag == True:
            print(' {0} is a good ticker. Remove from the DividendBadTickers.csv file'.format(eachSymbol),
                  flush = True)
    return


if __name__ == '__main__':
    print('***** Beginning Dividend Ticker Status code at',
          whenIsNow(), ' *****', flush = True)
    main()
    print('***** Ending Dividend Ticker Status code at',
          whenIsNow(), ' *****', flush = True)
