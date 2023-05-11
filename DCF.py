import re
import json
import numpy as np
import yfinance as yf
import pandas as pd
import pandas_datareader as pdr
import datetime as dt
from bs4 import BeautifulSoup
import requests
import plotly.express as px
from plotly.subplots import make_subplots
from io import BytesIO
from main import totalRevenue, basicDCF


def CreateDCFModel(sheetName, avg_NImargin, avg_FCFtoNI, sharesOutstanding,
                   WACC, yearsToPredict, GDP, Stats, TR_est1, TR_est2, multi):
    avg_NImargin = avg_NImargin + np.abs(avg_NImargin)*multi

    YOY_TR_growth = []

    for i in range(0, 3):
        growth = totalRevenue[2 - i] / totalRevenue[3 - i]
        YOY_TR_growth.append(growth)

    YOY_TR_growth.append(TR_est1 / totalRevenue[0])
    YOY_TR_growth.append(TR_est2 / TR_est1)
    avg_YOY_TR_growth = np.mean(YOY_TR_growth)
    avg_YOY_TR_growth = avg_YOY_TR_growth + np.abs(avg_YOY_TR_growth)*multi
    proj_TR = []
    proj_TR.append(TR_est1)
    proj_TR.append(TR_est2)

    columns = [str(i) for i in range(1, yearsToPredict + 1)]
    columns.append('TV')
    DCFmodel = pd.DataFrame(data=None, columns=columns)

    for i in range(0, yearsToPredict - 2):
        proj_TR.append(proj_TR[-1] * avg_YOY_TR_growth)

    proj_NI = [num * avg_NImargin for num in proj_TR]
    proj_FCF = [num * avg_FCFtoNI for num in proj_NI]

    avg_FCF_growth = []
    for i in range(1, yearsToPredict):
        avg_FCF_growth.append((proj_FCF[i]/proj_FCF[i-1])-1)
    avg_FCF_growth = np.mean(avg_FCF_growth)

    terminalValue = (proj_FCF[-1] * (1 + GDP)) / (WACC - GDP)
    proj_FCF.append(terminalValue)
    proj_TR.append(0)
    proj_NI.append(0)

    discountFactor = []
    for i in range(1, yearsToPredict + 1):
        discountFactor.append((1 + WACC) ** i)
    discountFactor.append((1 + WACC) ** yearsToPredict)
    discountFactor = pd.Series(discountFactor, name='Discount Factor', index=DCFmodel.columns)

    presentValueOfFCF = [proj_FCF[i] / discountFactor[i] for i in range(0, yearsToPredict)]
    presentValueOfTV = terminalValue / discountFactor[-1]
    presentValueOfFCF.append(presentValueOfTV)
    presentValueOfFCF = pd.Series(presentValueOfFCF, name='Present Value of Free Cash Flow', index=basicDCF.columns)
    proj_FCF = np.array(proj_FCF)
    proj_NI = np.array(proj_NI)
    proj_FCF = pd.Series(proj_FCF, name='Free Cash Flow', index=DCFmodel.columns)
    proj_TR = pd.Series(proj_TR, name='Total Revenue', index=DCFmodel.columns)
    proj_NI = pd.Series(proj_NI, name='Net Income', index=DCFmodel.columns)

    DCFmodel = DCFmodel.append(proj_TR)
    DCFmodel = DCFmodel.append(proj_NI)
    DCFmodel = DCFmodel.append(proj_FCF)
    DCFmodel = DCFmodel.append(discountFactor)
    DCFmodel = DCFmodel.append(presentValueOfFCF)

    todayValue = np.sum(presentValueOfFCF)
    fairValue = todayValue / sharesOutstanding

    data = [avg_NImargin, avg_YOY_TR_growth-1,avg_FCF_growth, WACC, fairValue]
    stats = pd.Series(data=data, name=sheetName, index=Stats.columns)
    Stats = Stats.append(stats)

    return DCFmodel, Stats


def create_sample_models(avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC, yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, avg_TR_est1, avg_TR_est2):
    modelList = []
    base, Stats = CreateDCFModel('Base', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
                                yearsToPredict, GDP, Stats, avg_TR_est1, avg_TR_est2, 0)
    modelList.append([base,'Base'])
    semiOptimistic, Stats = CreateDCFModel('Semi Optimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, 0.05)
    modelList.append([semiOptimistic,'Semi Optimistic'])
    Optimistic, Stats = CreateDCFModel('Optimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, 0.075)
    modelList.append([Optimistic,'Optimistic'])
    superOptimistic, Stats = CreateDCFModel('Super Optimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, 0.1)
    modelList.append([superOptimistic,'Super Optimistic'])
    semiPessimistic, Stats = CreateDCFModel('Semi Pessimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, -0.05)
    modelList.append([semiPessimistic,'Semi Pessimistic'])
    Pessimistic, Stats = CreateDCFModel('Pessimistic', avg_NImargin, avg_FCFtoNI, sharesOutstanding, WACC,
                                        yearsToPredict, GDP, Stats, high_TR_est1, high_TR_est2, -0.075)
    modelList.append([Pessimistic,'Pessimistic'])

    twelveRR, Stats = CreateDCFModel('12% Required Return', avg_NImargin, avg_FCFtoNI, sharesOutstanding, 0.12,
                                        yearsToPredict, GDP, Stats, avg_TR_est1, avg_TR_est2, 0)
    modelList.append([twelveRR,'12% Required Return'])
    tenRR, Stats = CreateDCFModel('10% Required Return', avg_NImargin, avg_FCFtoNI, sharesOutstanding, 0.1,
                                        yearsToPredict, GDP, Stats, avg_TR_est1, avg_TR_est2, 0)
    modelList.append([tenRR,'10% Required Return'])
    sevenRR, Stats = CreateDCFModel('7.5% Required Return', avg_NImargin, avg_FCFtoNI, sharesOutstanding, 0.075,
                                        yearsToPredict, GDP, Stats, avg_TR_est1, avg_TR_est2, 0)
    modelList.append([sevenRR,'7.5% Required Return'])

    return modelList, Stats