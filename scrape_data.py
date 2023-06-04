import re
import json
import numpy as np
import yfinance as yf
import yahooquery as yq
import pandas as pd
from pandas_datareader import data as pdr
import datetime as dt
from bs4 import BeautifulSoup
from lxml import etree
import requests


# Key Statistics
ebit = 0
# incomeBeforeTax = 0
# taxExpense = 0
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


def scrape_data(ticker):
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}

    url_a = f"https://finance.yahoo.com/quote/{ticker}/analysis?p={ticker}"
    res_a = requests.get(url_a, headers=header)
    soup_a = BeautifulSoup(res_a.text, 'html.parser')
    dom_a = etree.HTML(str(soup_a))
    analystPrediction = {
        'avg': [dom_a.xpath('//*[@id="Col1-0-AnalystLeafPage-Proxy"]/section/table[2]/tbody/tr[2]/td[4]')[0].text,
                dom_a.xpath('//*[@id="Col1-0-AnalystLeafPage-Proxy"]/section/table[2]/tbody/tr[2]/td[5]')[0].text],
        'low': [dom_a.xpath('//*[@id="Col1-0-AnalystLeafPage-Proxy"]/section/table[2]/tbody/tr[3]/td[4]')[0].text,
                dom_a.xpath('//*[@id="Col1-0-AnalystLeafPage-Proxy"]/section/table[2]/tbody/tr[3]/td[5]')[0].text],
        'high': [dom_a.xpath('//*[@id="Col1-0-AnalystLeafPage-Proxy"]/section/table[2]/tbody/tr[4]/td[4]')[0].text,
                 dom_a.xpath('//*[@id="Col1-0-AnalystLeafPage-Proxy"]/section/table[2]/tbody/tr[4]/td[5]')[0].text]
        }
    
    def transform_to_number(string):
        endings = {
            'K': 1000,
            'M': 1000000,
            'B': 1000000000,
        }

        if string[-1] in endings:
            return float(string[:-1]) * endings[string[-1]]
        else:
            return float(string)
        
    analystPrediction = {k: [transform_to_number(v[0]), transform_to_number(v[1])] for k, v in analystPrediction.items()}

    return analystPrediction


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


def get_key_stats(bs, fin, cf, ticker, CAPM, analystPrediction):
    global ebit
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

    avg_TR_est1 = analystPrediction['avg'][0]
    avg_TR_est2 = analystPrediction['avg'][1]
    low_TR_est1 = analystPrediction['low'][0]
    low_TR_est2 = analystPrediction['low'][1]
    high_TR_est1 = analystPrediction['high'][0]
    high_TR_est2 = analystPrediction['high'][1]

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


def get_key_stats_yq(bs, fin, cf, ticker, CAPM, analystPrediction):
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

    avg_TR_est1 = analystPrediction['avg'][0]
    avg_TR_est2 = analystPrediction['avg'][1]
    low_TR_est1 = analystPrediction['low'][0]
    low_TR_est2 = analystPrediction['low'][1]
    high_TR_est1 = analystPrediction['high'][0]
    high_TR_est2 = analystPrediction['high'][1]

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
    WACC = WACC[-1]

    key_stats = {name: value for name, value in globals().items() 
                if not name.startswith('__') 
                and not value.__class__.__name__ == 'function' 
                and not value.__class__.__name__ == 'module'
                and not value.__class__.__name__ == 'type'
                }
    
    for key, value in key_stats.items():
        if isinstance(value, np.ndarray):
            key_stats[key] = value.tolist()
        elif isinstance(value, pd.Series):
            key_stats[key] = value.to_dict()

    with open(f'./Models/{ticker}_key_stats.json', 'w') as f:
        json.dump(key_stats, f, indent=4)

