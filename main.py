import re
import sys
import json
import numpy as np
import yfinance as yf
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
import requests
import plotly.express as px
from plotly.subplots import make_subplots
from io import BytesIO
from scrape_data import *
from DCF import *


# Assumptions
yearsToPredict = 5
marketReturn = 0.1
tenYTreasury = GetLastClose('^TNX')/100
GDP = 0.03

# Global Variables
ticker = ""
path = 'E:\\Python\\DCF_model\Models\\'
endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=365 * yearsToPredict)
stocks = [ticker, '^GSPC']
beta = GetBeta(stocks, startDate, endDate)

columns = [str(i) for i in range(1,yearsToPredict+1)]
columns.append('TV')
basicDCF = pd.DataFrame(data=None, columns=columns)

statsColumns = ['Average Net Income Margin', 'Average Total Revenue Growth','Average FCF Growth', 'WACC', 'Fair Share Price']
Stats = pd.DataFrame(data=None, columns=statsColumns)

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


def save_to_excel(modelList, bs, fin, cf):
    with pd.ExcelWriter(path + "{}.xlsx".format(ticker), engine='xlsxwriter') as writer:
        bs.to_excel(writer, sheet_name="balance_sheet")
        fin.to_excel(writer, sheet_name="income_statement")
        cf.to_excel(writer, sheet_name="cash_flow")
        Stats.to_excel(writer, sheet_name="Sensitivity Analysis")
        for model in modelList:
            model[0].to_excel(writer, sheet_name="{}".format(model[1]))
            chartColumns = [i for i in range(-len(totalRevenue) + 1, yearsToPredict + 1)]
            df1 = pd.DataFrame(data=None, columns=chartColumns)
            df2 = pd.DataFrame(data=None, columns=chartColumns)

            past_TR = totalRevenue.tolist()
            past_NI = NI.tolist()
            past_FCF = FCF.tolist()
            past_FCF.reverse()
            past_NI.reverse()
            past_TR.reverse()
            future_TR = model[0].loc['Total Revenue', :].tolist()
            future_NI = model[0].loc['Net Income', :].tolist()
            future_FCF = model[0].loc['Free Cash Flow', :].tolist()
            future_TR = future_TR[:-1]
            future_NI = future_NI[:-1]
            future_FCF = future_FCF[:-1]
            NI_chart_data = past_NI + future_NI
            TR_chart_data = past_TR + future_TR
            FCF_chart_data = past_FCF + future_FCF
            FCF_chart_data = pd.Series(FCF_chart_data, name='Free Cash Flow', index=df1.columns)
            TR_chart_data = pd.Series(TR_chart_data, name='Total Revenue', index=df1.columns)
            NI_chart_data = pd.Series(NI_chart_data, name='Net Income', index=df1.columns)

            workbook = writer.book
            worksheet = writer.sheets["{}".format(model[1])]

            df1 = df1.append(FCF_chart_data)
            df1 = df1.append(NI_chart_data)
            df2 = df2.append(TR_chart_data)
            df1 = df1.T
            df2 = df2.T
            fig1 = px.bar(df1, barmode='group', color_discrete_sequence=['#006400', '#00BFFF'])
            fig2 = px.bar(df2, barmode='group', color_discrete_sequence=['#B22222'])

            fig2.update_traces(yaxis="y2")
            subfig = make_subplots(specs=[[{"secondary_y": True}]])
            subfig.add_traces(fig1.data + fig2.data)
            subfig.update_layout(bargap=0.30, bargroupgap=0.3)

            image_data = BytesIO(subfig.to_image(format="png"))
            worksheet.insert_image(1, 8, 'plotly.png', {'image_data': image_data})

# with open("ticker.txt") as f:
#     ticker = f.read().splitlines()

# ticker = ticker[0]
# stocks = [ticker, '^GSPC']

# header = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}

# url_s = f"https://finance.yahoo.com/quote/{ticker}/key-statistics?p={ticker}"
# res_s = requests.get(url_s, headers=header)
# soup_s = BeautifulSoup(res_s.text, 'html.parser')
# pattern = re.compile(r'\s--\sData\s--\s')
# script_data = soup_s.find('script', text=pattern).contents[0]
# start = script_data.find('context')-2
# json_data = json.loads(script_data[start:-12])
# defaultKeyStatistics = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['defaultKeyStatistics']
# financialData = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['financialData']

# url_a = f"https://finance.yahoo.com/quote/{ticker}/analysis?p={ticker}"
# res_a = requests.get(url_a, headers=header)
# soup_a = BeautifulSoup(res_a.text, 'html.parser')
# pattern = re.compile(r'\s--\sData\s--\s')
# script_data = soup_a.find('script', text=pattern).contents[0]
# start = script_data.find('context')-2
# json_data = json.loads(script_data[start:-12])
# analystPrediction = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']

# # Assumptions
# yearsToPredict = 5
# marketReturn = 0.1
# tenYTreasury = GetLastClose('^TNX')/100
# GDP = 0.03

# endDate = dt.datetime.now()
# startDate = endDate - dt.timedelta(days=365 * yearsToPredict)
# beta = GetBeta(stocks, startDate, endDate)

# yf_ticker = yf.Ticker(ticker)
# bs = pd.DataFrame(yf_ticker.get_balance_sheet())
# fin = pd.DataFrame(yf_ticker.get_financials())
# cf = pd.DataFrame(yf_ticker.get_cashflow())

# ebit = fin.loc['Ebit', :]
# incomeBeforeTax = fin.loc['Income Before Tax', :]
# taxExpense = fin.loc['Income Tax Expense', :]
# taxRate = taxExpense / incomeBeforeTax
# taxRate = pd.Series(taxRate, name='Tax Rate(%)', index=fin.columns)
# DA = cf.loc['Depreciation', :]
# CapEx = cf.loc['Capital Expenditures', :]
# FCF = ebit * (1 - taxRate) + DA + CapEx
# FCF = pd.Series(FCF, name='Free Cash Flow', index=cf.columns)
# NI = fin.loc['Net Income', :]
# FCFtoNI = FCF / NI
# FCFtoNI = pd.Series(FCFtoNI, name='Free Cash Flow / Net Income', index=cf.columns)
# avg_FCFtoNI = np.mean(FCFtoNI)
# totalRevenue = fin.loc['Total Revenue', :]
# NImargin = NI / totalRevenue
# NImargin = pd.Series(NImargin, name='Net Income Margin', index=cf.columns)
# avg_NImargin = np.mean(NImargin)

# fin = fin.append(taxRate)
# fin = fin.append(FCFtoNI)
# fin = fin.append(NImargin)
# cf = cf.append(FCF)

# columns = [str(i) for i in range(1,yearsToPredict+1)]
# columns.append('TV')
# basicDCF = pd.DataFrame(data=None, columns=columns)

# avg_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['avg']['raw']
# avg_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['avg']['raw']
# low_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['low']['raw']
# low_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['low']['raw']
# high_TR_est1 = analystPrediction['earningsTrend']['trend'][2]['revenueEstimate']['low']['raw']
# high_TR_est2 = analystPrediction['earningsTrend']['trend'][3]['revenueEstimate']['low']['raw']


# try:
#     shortTermDebt = bs.loc['Short Long Term Debt', :]
# except KeyError:
#     shortTermDebt = 0
# longTermDebt = bs.loc['Long Term Debt', :]
# costOfDebt = np.abs(fin.loc['Interest Expense', :] / (shortTermDebt + longTermDebt))
# if(np.median(costOfDebt)!=np.median(costOfDebt)):
#     costOfDebt = np.mean(costOfDebt)
# else:
#     costOfDebt = np.median(costOfDebt)

# sharesOutstanding = defaultKeyStatistics['sharesOutstanding']['raw']
# equityValue = sharesOutstanding * GetLastClose(ticker)
# debtValue = financialData['totalDebt']['raw']

# debtWeight = debtValue / (debtValue+equityValue)
# equityWeight = equityValue / (debtValue+equityValue)

# if(np.median(taxRate)!=np.median(taxRate)):
#     med_taxRate = np.mean(taxRate)
# else:
#     med_taxRate = np.median(taxRate)

# CAPM = tenYTreasury + beta*(marketReturn - tenYTreasury)
# WACC = debtWeight*costOfDebt*(1-med_taxRate) + equityWeight*CAPM

# statsColumns = ['Average Net Income Margin', 'Average Total Revenue Growth','Average FCF Growth', 'WACC', 'Fair Share Price']
# Stats = pd.DataFrame(data=None, columns=statsColumns)

# modelList = []
# base, Stats = CreateDCFModel('Base', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
#                             yearsToPredict, GDP, Stats, avg_TR_est1, avg_TR_est2, 0)
# modelList.append([base,'Base'])
# semiOptimistic, Stats = CreateDCFModel('Semi Optimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
#                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, 0.05)
# modelList.append([semiOptimistic,'Semi Optimistic'])
# Optimistic, Stats = CreateDCFModel('Optimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
#                                     yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, 0.075)
# modelList.append([Optimistic,'Optimistic'])
# superOptimistic, Stats = CreateDCFModel('Super Optimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
#                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, 0.1)
# modelList.append([superOptimistic,'Super Optimistic'])
# semiPessimistic, Stats = CreateDCFModel('Semi Pessimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
#                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, -0.05)
# modelList.append([semiPessimistic,'Semi Pessimistic'])
# Pessimistic, Stats = CreateDCFModel('Pessimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
#                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, -0.075)
# modelList.append([Pessimistic,'Pessimistic'])

# twelveRR, Stats = CreateDCFModel('12% Required Return', avg_NImargin, avg_FCFtoNI, sharesOutstanding, 0.12,
#                                        yearsToPredict, GDP, Stats, avg_TR_est1, avg_TR_est2, 0)
# modelList.append([twelveRR,'12% Required Return'])
# tenRR, Stats = CreateDCFModel('10% Required Return', avg_NImargin, avg_FCFtoNI, sharesOutstanding, 0.1,
#                                        yearsToPredict, GDP, Stats, avg_TR_est1, avg_TR_est2, 0)
# modelList.append([tenRR,'10% Required Return'])
# sevenRR, Stats = CreateDCFModel('7.5% Required Return', avg_NImargin, avg_FCFtoNI, sharesOutstanding, 0.075,
#                                        yearsToPredict, GDP, Stats, avg_TR_est1, avg_TR_est2, 0)
# modelList.append([sevenRR,'7.5% Required Return'])

# path = 'C:\\Users\\bruno\\Desktop\\python\\DCF_model\Models\\'
# with pd.ExcelWriter(path + "{}.xlsx".format(ticker), engine='xlsxwriter') as writer:
#     bs.to_excel(writer, sheet_name="balance_sheet")
#     fin.to_excel(writer, sheet_name="income_statement")
#     cf.to_excel(writer, sheet_name="cash_flow")
#     Stats.to_excel(writer, sheet_name="Sensitivity Analysis")
#     for model in modelList:
#         model[0].to_excel(writer, sheet_name="{}".format(model[1]))
#         chartColumns = [i for i in range(-len(totalRevenue) + 1, yearsToPredict + 1)]
#         df1 = pd.DataFrame(data=None, columns=chartColumns)
#         df2 = pd.DataFrame(data=None, columns=chartColumns)

#         past_TR = totalRevenue.tolist()
#         past_NI = NI.tolist()
#         past_FCF = FCF.tolist()
#         past_FCF.reverse()
#         past_NI.reverse()
#         past_TR.reverse()
#         future_TR = model[0].loc['Total Revenue', :].tolist()
#         future_NI = model[0].loc['Net Income', :].tolist()
#         future_FCF = model[0].loc['Free Cash Flow', :].tolist()
#         future_TR = future_TR[:-1]
#         future_NI = future_NI[:-1]
#         future_FCF = future_FCF[:-1]
#         NI_chart_data = past_NI + future_NI
#         TR_chart_data = past_TR + future_TR
#         FCF_chart_data = past_FCF + future_FCF
#         FCF_chart_data = pd.Series(FCF_chart_data, name='Free Cash Flow', index=df1.columns)
#         TR_chart_data = pd.Series(TR_chart_data, name='Total Revenue', index=df1.columns)
#         NI_chart_data = pd.Series(NI_chart_data, name='Net Income', index=df1.columns)

#         workbook = writer.book
#         worksheet = writer.sheets["{}".format(model[1])]

#         df1 = df1.append(FCF_chart_data)
#         df1 = df1.append(NI_chart_data)
#         df2 = df2.append(TR_chart_data)
#         df1 = df1.T
#         df2 = df2.T
#         fig1 = px.bar(df1, barmode='group', color_discrete_sequence=['#006400', '#00BFFF'])
#         fig2 = px.bar(df2, barmode='group', color_discrete_sequence=['#B22222'])

#         fig2.update_traces(yaxis="y2")
#         subfig = make_subplots(specs=[[{"secondary_y": True}]])
#         subfig.add_traces(fig1.data + fig2.data)
#         subfig.update_layout(bargap=0.30, bargroupgap=0.3)

#         image_data = BytesIO(subfig.to_image(format="png"))
#         worksheet.insert_image(1, 8, 'plotly.png', {'image_data': image_data})


def main(args):
    if len(args) != 2:
        print("Usage: python DCF.py <ticker> <path>")
        sys.exit(1)
    
    ticker = args[0]
    path = args[1]

    defaultKeyStatistics, financialData, analystPrediction = scrape_data(ticker)

    bs, fin, cf = get_ticker_financials(ticker, path)
    get_key_stats(bs, fin, cf, defaultKeyStatistics, financialData, analystPrediction,
                  ebit, incomeBeforeTax, taxExpense, taxRate, DA, CapEx, FCF, NI, FCFtoNI, avg_FCFtoNI, totalRevenue,
                  NImargin, avg_NImargin, avg_TR_est1, avg_TR_est2, low_TR_est1, low_TR_est2, high_TR_est1,
                  high_TR_est2, shortTermDebt, longTermDebt, costOfDebt, sharesOutstanding, equityValue, debtValue,
                  debtWeight, equityWeight, med_taxRate, CAPM, WACC)
    
    modelList = create_sample_models()
    save_to_excel(modelList, bs, fin, cf, Stats, ticker, path)

    