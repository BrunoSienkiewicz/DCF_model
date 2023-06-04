import os
import sys
import json
import numpy as np
import yfinance as yf
import pandas as pd
import datetime as dt
import plotly.express as px
from plotly.subplots import make_subplots
from io import BytesIO
from scrape_data import get_key_stats, get_key_stats_yq, get_ticker_financials, get_ticker_financials_yq,GetBeta, GetLastClose, scrape_data
from DCF import create_sample_models


# Assumptions
yearsToPredict = 5
marketReturn = 0.1
tenYTreasury = 0
GDP = 0.03
CAPM = 0

# Global Variables
ticker = ""
# path = 'E:\\Python\\DCF_model\Models\\'
path = './Models/'
endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=365 * yearsToPredict)
stocks = []
beta = 0

columns = [str(i) for i in range(1,yearsToPredict+1)]
columns.append('TV')
basicDCF = pd.DataFrame(data=None, columns=columns)

statsColumns = ['Average Net Income Margin', 'Average Total Revenue Growth','Average FCF Growth', 'WACC', 'Fair Share Price']
Stats = pd.DataFrame(data=None, columns=statsColumns)

analystPrediction = {}


def save_to_excel(modelList, bs, fin, cf, key_stats, path):
    currentYear = dt.datetime.now().year
    currentQuarter = (dt.datetime.now().month - 1) // 3 + 1

    with pd.ExcelWriter(path + f"{ticker}_{currentYear}_Q{currentQuarter}.xlsx", engine='xlsxwriter') as writer:
        bs.to_excel(writer, sheet_name="balance_sheet")
        fin.to_excel(writer, sheet_name="income_statement")
        cf.to_excel(writer, sheet_name="cash_flow")
        Stats.to_excel(writer, sheet_name="Sensitivity Analysis")
        for model in modelList:
            totalRevenue = key_stats['totalRevenue']
            NI = key_stats['NI']
            FCF = key_stats['FCF']

            model[0].to_excel(writer, sheet_name="{}".format(model[1]))
            chartColumns = [i for i in range(-len(totalRevenue) + 1, yearsToPredict + 1)]
            df1 = pd.DataFrame(data=None, columns=chartColumns)
            df2 = pd.DataFrame(data=None, columns=chartColumns)

            past_TR = totalRevenue
            past_NI = NI
            past_FCF = list(FCF.values())
            if (len(past_FCF) < yearsToPredict + 1):
                past_FCF = [np.nan] + past_FCF
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


def main(args):
    if len(args) != 2:
        print("Usage: python main.py <ticker> <yearsToPredict>")
        sys.exit(1)
    
    global ticker
    global yearsToPredict
    ticker = args[0]
    yearsToPredict = int(args[1])

    yf.pdr_override()

    global analystPrediction
    analystPrediction = scrape_data(ticker)

    global tenYTreasury
    global beta
    global stocks
    global CAPM
    stocks = [ticker, '^GSPC']
    tenYTreasury = GetLastClose('^TNX')/100
    beta = GetBeta(stocks, startDate, endDate)

    CAPM = tenYTreasury + beta * (marketReturn - tenYTreasury)

    bs, fin, cf = get_ticker_financials_yq(ticker)
    get_key_stats_yq(bs, fin, cf, ticker, CAPM, analystPrediction)

    key_stats = {}
    with open(f'./Models/{ticker}_key_stats.json') as json_file:
        key_stats = json.load(json_file)
    
    global Stats
    modelList, Stats = create_sample_models(basicDCF, yearsToPredict, GDP, Stats, key_stats)
    save_to_excel(modelList, bs, fin, cf, key_stats, path)

    os.remove(f'./Models/{ticker}_key_stats.json')


if __name__ == "__main__":
    main(sys.argv[1:])
