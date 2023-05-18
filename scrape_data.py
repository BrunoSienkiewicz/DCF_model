import re
import json
import numpy as np
import yfinance as yf
import yahooquery as yq
import pandas as pd
from pandas_datareader import data as pdr
import datetime as dt
from bs4 import BeautifulSoup
import requests


# Key Statistics
ebit = 0
incomeBeforeTax = 0
taxExpense = 0
taxRate = 0
DA = 0
CapEx = 0
FCF = 0
NI = 0
FCFtoNI = 0
avg_FCFtoNI = 0
totalRevenue = 0
NImargin = 0
avg_NImargin = 0
avg_TR_est1 = 0
avg_TR_est2 = 0
low_TR_est1 = 0
low_TR_est2 = 0
high_TR_est1 = 0
high_TR_est2 = 0
shortTermDebt = 0
longTermDebt = 0
costOfDebt = 0
sharesOutstanding = 0
equityValue = 0
debtValue = 0
debtWeight = 0 
equityWeight = 0
med_taxRate = 0
CAPM = 0
WACC = 0


def GetBeta(stocks, start, end):
    stockData = pdr.get_data_yahoo(stocks, start=start, end=end)
    stockData = stockData['Close']

    log_returns = np.log(stockData / stockData.shift())
    covMatrix = log_returns.cov()
    var = log_returns['^GSPC'].var()
    beta = covMatrix.loc[stocks[0], '^GSPC'] / var

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


def get_ticker_financials(ticker):
    yf_ticker = yf.Ticker(ticker)
    bs = pd.DataFrame(yf_ticker.get_balance_sheet())
    fin = pd.DataFrame(yf_ticker.get_financials())
    cf = pd.DataFrame(yf_ticker.get_cashflow())

    return bs, fin, cf


def get_ticker_financials_yq(ticker):
    yq_ticker = yq.Ticker(ticker)
    bs = pd.DataFrame(yq_ticker.balance_sheet()).T
    fin = pd.DataFrame(yq_ticker.income_statement()).T
    cf = pd.DataFrame(yq_ticker.cash_flow()).T

    return bs, fin, cf


def get_key_stats(bs, fin, cf, ticker, CAPM):
    global ebit
    global incomeBeforeTax
    global taxExpense
    global taxRate
    global DA
    global CapEx
    global FCF
    global NI
    global FCFtoNI
    global avg_FCFtoNI
    global totalRevenue
    global NImargin
    global avg_NImargin
    global avg_TR_est1
    global avg_TR_est2
    global low_TR_est1
    global low_TR_est2
    global high_TR_est1
    global high_TR_est2
    global shortTermDebt
    global longTermDebt
    global costOfDebt
    global sharesOutstanding
    global equityValue
    global debtValue
    global debtWeight
    global equityWeight
    global med_taxRate
    global WACC

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

    # avg_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['avg']['raw']
    # avg_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['avg']['raw']
    # low_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['low']['raw']
    # low_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['low']['raw']
    # high_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['low']['raw']
    # high_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['low']['raw']

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

    # sharesOutstanding = defaultKeyStatistics['sharesOutstanding']['raw']
    sharesOutstanding = yf.Ticker(ticker).info['sharesOutstanding']
    equityValue = sharesOutstanding * GetLastClose(ticker)
    # debtValue = financialData['totalDebt']['raw']
    debtValue = yf.Ticker(ticker).info['totalDebt']

    debtWeight = debtValue / (debtValue+equityValue)
    equityWeight = equityValue / (debtValue+equityValue)

    if(np.median(taxRate)!=np.median(taxRate)):
        med_taxRate = np.mean(taxRate)
    else:
        med_taxRate = np.median(taxRate)

    WACC = debtWeight*costOfDebt*(1-med_taxRate) + equityWeight*CAPM


def get_key_stats_yq(bs, fin, cf, ticker, CAPM):
    global ebit
    global incomeBeforeTax
    global taxExpense
    global taxRate
    global DA
    global CapEx
    global FCF
    global NI
    global FCFtoNI
    global avg_FCFtoNI
    global totalRevenue
    global NImargin
    global avg_NImargin
    global avg_TR_est1
    global avg_TR_est2
    global low_TR_est1
    global low_TR_est2
    global high_TR_est1
    global high_TR_est2
    global shortTermDebt
    global longTermDebt
    global costOfDebt
    global sharesOutstanding
    global equityValue
    global debtValue
    global debtWeight
    global equityWeight
    global med_taxRate
    global WACC

    years = pd.to_datetime(fin.loc['asOfDate', :].values).year
    bs.reset_index(drop=True)

    ebit = fin.loc['EBIT', :].values
    taxRate = fin.loc['TaxRateForCalcs', :].values
    taxRate = pd.Series(taxRate, name='Tax Rate(%)', index=years)
    DA = cf.loc['DepreciationAndAmortization', :].values
    CapEx = cf.loc['CapitalExpenditure', :].values
    FCF = ebit * (1 - taxRate) + DA + CapEx
    FCF = pd.Series(FCF, name='Free Cash Flow', index=years)
    NI = cf.loc['NetIncome', :].values
    FCFtoNI = FCF / NI
    FCFtoNI = pd.Series(FCFtoNI, name='Free Cash Flow / Net Income', index=years)
    avg_FCFtoNI = np.mean(FCFtoNI)
    totalRevenue = fin.loc['TotalRevenue', :].values
    NImargin = NI / totalRevenue
    NImargin = pd.Series(NImargin, name='Net Income Margin', index=years)
    avg_NImargin = np.mean(NImargin)

    # fin = fin.append(taxRate)
    # fin = fin.append(FCFtoNI)
    # fin = fin.append(NImargin)
    # cf = cf.append(FCF)

    longTermDebt = bs.loc['LongTermDebt', :].values
    shortTermDebt = 0
    debtValue = bs.loc['TotalDebt', :].values
    costOfDebt = np.abs(cf.loc['RepaymentOfDebt', :].values[-4:] / debtValue)
    costOfDebt = np.median(costOfDebt)

    sharesOutstanding = bs.loc['OrdinarySharesNumber', :].values
    equityValue = sharesOutstanding * GetLastClose(ticker)

    debtWeight = debtValue / (debtValue+equityValue)
    equityWeight = equityValue / (debtValue+equityValue)

    med_taxRate = np.median(taxRate)

    WACC = debtWeight*costOfDebt*(1-med_taxRate) + equityWeight*CAPM
