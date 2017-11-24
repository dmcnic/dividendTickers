#!/usr/bin/env python3

import matplotlib
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
# import matplotlib.finance as finance
import sys
import datetime
import pandas_datareader as pdr
# import pandas as pd
# import numpy as np


matplotlib.style.use('seaborn-whitegrid')


def technicalIndicators(ticker):
    # Set the date range
    beginDate = datetime.datetime.now() - datetime.timedelta(days = 365)
    endDate = datetime.datetime.now()
    
    # Attempt to grab the historical data from Yahoo! Finance
    try:
        # price = finance.fetch_historical_yahoo(ticker, beginDate, endDate)
        # price = pdr.get_data_yahoo(ticker, beginDate, endDate)
        priceRecord = pdr.DataReader(ticker, 'google', beginDate, endDate)
    except:
        print('   Ticker failure: ', ticker)
        sys.exit(1)
    
    # Alter the record variable to a panda data frame
    # priceRecord = pd.DataFrame(matplotlib.mlab.csv2rec(price)).sort_index(ascending = False)
    
    # Construct the upper Bollinger band
    priceRecord['Boll_Upper'] = priceRecord['Close'].rolling(center = False, window = 20).mean() + 2 * priceRecord['Close'].rolling(center = False, window = 20, min_periods = 20).std()
    
    # Construct the lower Bollinger band
    priceRecord['Boll_Lower'] = priceRecord['Close'].rolling(center = False, window = 20).mean() - 2 * priceRecord['Close'].rolling(center = False, window = 20, min_periods = 20).std()
    
    # Begin the calculation of the RSI
    # Start by creating the price change
    priceChange = priceRecord['Close'].diff()
    
    # Remove the first row since it is Nan
    priceChange = priceChange[1:]

    # Create the positive gains and the negative gains series
    priceGain, priceLoss = priceChange.copy(), priceChange.copy()
    
    # Reset each new series based on the price change value
    priceGain[priceGain < 0] = 0
    priceLoss[priceLoss > 0] = 0
    
    # Calculate the EWMA
    rollUp = priceGain.ewm(ignore_na = False, adjust = True, min_periods = 14, com = 14).mean()
    rollDown = priceLoss.abs().ewm(ignore_na = False, adjust = True, min_periods = 14, com = 14).mean()
    
    # Calculate the RSI
    relativeStrength = rollUp / rollDown
    relativeStrengthIndex = 100.0 - (100.0 / (1.0 + relativeStrength))
    relativeStrengthIndex[relativeStrengthIndex > 100] = 100
    relativeStrengthIndex[relativeStrengthIndex < 0] = 0
    
    # ROC calculation is close divided by close twelve trading days ago
    priceRecord['ROC'] = priceRecord['Close'].pct_change(periods = 12)
    
    # Construct the text box text to show the latest values
    bollPct = (priceRecord[-1:]['Close'] - priceRecord[-1:]['Boll_Lower']) / (priceRecord[-1:]['Boll_Upper'] - priceRecord[-1:]['Boll_Lower'])
    textBox = 'Ticker: %-5s\nLast values\nPrice %.2f\nBoll Pct %.3f\nROC %.1f\nRSI %.1f'%(ticker,
                                                                            priceRecord[-1:]['Close'],
                                                                            bollPct,
                                                                            priceRecord[-1:]['ROC'] * 100,
                                                                            relativeStrengthIndex[-1:])
    boxProperties = dict(boxstyle = 'round', facecolor = 'wheat', alpha = 0.5)
    
    # Construct three subplots within the figure
    # They should share the same x - axis
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex = True, figsize = (10, 10))
    
    # The first subplot will contain the Bollinger Bands
    ax1.plot(priceRecord.index.values, priceRecord.Close, label = 'Close', color = 'blue')
    ax1.plot(priceRecord.index.values, priceRecord.Boll_Lower, label = 'Lower', color = 'green')
    ax1.plot(priceRecord.index.values, priceRecord.Boll_Upper, label = 'Upper', color = 'red')
    
    # The dates on the x-axis overlap and need to be auto formatted
    fig.autofmt_xdate()
    
    # When moving the mouse, the date needs to be changed from the %b %Y default
    ax1.fmt_xdata = matplotlib.dates.DateFormatter('%b %d')
    
    # The second subplot contains the rate of change line
    ax2.plot(priceRecord.index.values, priceRecord.ROC, label = 'ROC', color = 'black')
    
    # Add a trigger line to show the -10% value
    ax2.axhline(-0.1, linewidth= 2, color = 'red')
    
    # When moving the mouse, the date needs to be changed from the %b %Y default
    ax2.fmt_xdata = matplotlib.dates.DateFormatter('%b %d')
    
    # The third subplot contains the relative strength index line
    ax3.plot(priceRecord.index.values[1:], relativeStrengthIndex, color = 'black')
    
    # When moving the mouse, the date needs to be changed from the %b %Y default
    ax3.fmt_xdata = matplotlib.dates.DateFormatter('%b %d')
    
    # Add a horizontal range between 30 and 70
    ax3.axhspan(30, 70, facecolor = 'yellow', alpha = 0.25)
    
    # Add the textbox to the first subplot
    ax1.text(0.05, 0.95, textBox, transform = ax1.transAxes, fontsize = 14, verticalalignment = 'top', bbox = boxProperties)
    
    # Tighten up the layout so there is less white space on the sides
    fig.tight_layout()
    
    # printPages.savefig()
    # plt.show()
    # printPages.close()
    return

def main():
    if len(sys.argv) == 2:
        # Only one ticker was input
        technicalIndicators(sys.argv[1])
        plt.show()
    else:
        # Create the object to hold the pdf output
        printPages = PdfPages('DividendGraphs.pdf')
        
        # Loop through the tickers 
        for ticker in sys.argv[1:]:
            technicalIndicators(ticker)
            printPages.savefig()
            plt.close()
        
        # Close out the pdf file
        printPages.close()
    return


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(' Usage is DividendGraphs.py followed by a ticker')
        sys.exit(1)
    
    print(' ***** Beginning code execution *****')
    main()
    print(' ***** Ending code execution *****')
    