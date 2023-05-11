import re
import json
import numpy as np
import yfinance as yf
import pandas as pd
import pandas_datareader as pdr
import datetime as dt
from bs4 import BeautifulSoup
import requests
from main import ticker, tenYTreasury, beta, marketReturn
from DCF import GetLastClose


def GetBeta(stocks, start, end):
    stockData = pdr.get_data_yahoo(stocks, start=start, end=end)
    stockData = stockData['Close']

    log_returns = np.log(stockData / stockData.shift())
    covMatrix = log_returns.cov()
    var = log_returns['^GSPC'].var()
    beta = covMatrix.loc[ticker, '^GSPC'] / var

    return beta


def GetLastClose(symbol):
    Data = pdr.get_data_yahoo(symbol, dt.datetime.now()-dt.timedelta(days=10), dt.datetime.now())['Close']
    return Data[-1]


def scrape_data():
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}

    url_s = f"https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}"
    res_s = requests.get(url_s, headers=header)
    soup_s = BeautifulSoup(res_s.text, 'html.parser')
    pattern = re.compile(r'\s--\sData\s--\s')
    script_data = soup_s.find('script', text=pattern).contents[0]
    start = script_data.find('context')-2
    json_data = json.loads(script_data[start:-12])
    defaultKeyStatistics = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['defaultKeyStatistics']
    financialData = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']

    url_a = f"https://finance.yahoo.com/quote/{ticker}/analysis?p={ticker}"
    res_a = requests.get(url_a, headers=header)
    soup_a = BeautifulSoup(res_a.text, 'html.parser')
    pattern = re.compile(r'\s--\sData\s--\s')
    script_data = soup_a.find('script', text=pattern).contents[0]
    start = script_data.find('context')-2
    json_data = json.loads(script_data[start:-12])
    analystPrediction = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']

    return defaultKeyStatistics, financialData, analystPrediction


def get_ticker_financials():
    yf_ticker = yf.Ticker(ticker)
    bs = pd.DataFrame(yf_ticker.get_balance_sheet())
    fin = pd.DataFrame(yf_ticker.get_financials())
    cf = pd.DataFrame(yf_ticker.get_cashflow())

    return bs, fin, cf


def get_key_stats(bs, fin, cf, defaultKeyStatistics, financialData, analystPrediction,
                  ebit, incomeBeforeTax, taxExpense, taxRate, DA, CapEx, FCF, NI, FCFtoNI, avg_FCFtoNI, totalRevenue,
                  NImargin, avg_NImargin, avg_TR_est1, avg_TR_est2, low_TR_est1, low_TR_est2, high_TR_est1,
                  high_TR_est2, shortTermDebt, longTermDebt, costOfDebt, sharesOutstanding, equityValue, debtValue,
                  debtWeight, equityWeight, med_taxRate, CAPM, WACC):
    ebit = fin.loc['Ebit', :]
    incomeBeforeTax = fin.loc['Income Before Tax', :]
    taxExpense = fin.loc['Income Tax Expense', :]
    taxRate = taxExpense / incomeBeforeTax
    taxRate = pd.Series(taxRate, name='Tax Rate(%)', index=fin.columns)
    DA = cf.loc['Depreciation', :]
    CapEx = cf.loc['Capital Expenditures', :]
    FCF = ebit * (1 - taxRate) + DA + CapEx
    FCF = pd.Series(FCF, name='Free Cash Flow', index=cf.columns)
    NI = fin.loc['Net Income', :]
    FCFtoNI = FCF / NI
    FCFtoNI = pd.Series(FCFtoNI, name='Free Cash Flow / Net Income', index=cf.columns)
    avg_FCFtoNI = np.mean(FCFtoNI)
    totalRevenue = fin.loc['Total Revenue', :]
    NImargin = NI / totalRevenue
    NImargin = pd.Series(NImargin, name='Net Income Margin', index=cf.columns)
    avg_NImargin = np.mean(NImargin)

    fin = fin.append(taxRate)
    fin = fin.append(FCFtoNI)
    fin = fin.append(NImargin)
    cf = cf.append(FCF)

    avg_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['avg']['raw']
    avg_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['avg']['raw']
    low_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['low']['raw']
    low_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['low']['raw']
    high_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['low']['raw']
    high_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['low']['raw']


    try:
        shortTermDebt = bs.loc['Short Long Term Debt', :]
    except KeyError:
        shortTermDebt = 0
    longTermDebt = bs.loc['Long Term Debt', :]
    costOfDebt = np.abs(fin.loc['Interest Expense', :] / (shortTermDebt + longTermDebt))
    if(np.median(costOfDebt)!=np.median(costOfDebt)):
        costOfDebt = np.mean(costOfDebt)
    else:
        costOfDebt = np.median(costOfDebt)

    sharesOutstanding = defaultKeyStatistics['sharesOutstanding']['raw']
    equityValue = sharesOutstanding * GetLastClose(ticker)
    debtValue = financialData['totalDebt']['raw']

    debtWeight = debtValue / (debtValue+equityValue)
    equityWeight = equityValue / (debtValue+equityValue)

    if(np.median(taxRate)!=np.median(taxRate)):
        med_taxRate = np.mean(taxRate)
    else:
        med_taxRate = np.median(taxRate)

    CAPM = tenYTreasury + beta*(marketReturn - tenYTreasury)
    WACC = debtWeight*costOfDebt*(1-med_taxRate) + equityWeight*CAPM