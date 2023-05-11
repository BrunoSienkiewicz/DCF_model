import pandas as pd
import datetime as dt


# Assumptions
yearsToPredict = 5
marketReturn = 0.1
tenYTreasury = 0
GDP = 0.03

# Global Variables
ticker = ""
path = 'E:\\Python\\DCF_model\Models\\'
endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=365 * yearsToPredict)
stocks = [ticker, '^GSPC']
beta = 0

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