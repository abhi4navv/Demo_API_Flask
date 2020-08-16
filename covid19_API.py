import calendar

from flask import Flask, request, make_response

import json

import numpy as np


import pandas as pd
from pandas import ExcelWriter
import requests





app = Flask(__name__)

class Analytics:
    def __init__(self,request):
        self.request = request

    def get_master_data(self):
        url = 'https://api.covid19india.org/data.json'
        json_data = requests.get(url)
        df_main = pd.DataFrame()
        if json_data.status_code == 200 and bool(json_data.content) == True:
            if 'cases_time_series' in json.loads(json_data.content):
                main_data = json.loads(json_data.content)
                df_main = pd.DataFrame(main_data['cases_time_series'])
        df_main.replace({np.nan, 0}, inplace=True)
        month_number_word_json = {v: k for k, v in enumerate(calendar.month_abbr)}
        del month_number_word_json['']
        df_main['date'] = df_main['date'].apply(lambda x: f"2020-0{month_number_word_json[x.split(' ')[1][0:3]]}-{x.split(' ')[0]}" if type(x) == str and len(x.split(' ')) > 1 and len(str(month_number_word_json[x.split(' ')[1][0:3]])) == 1 else f"2020-{month_number_word_json[x.split(' ')[1][0:3]]}-{x.split(' ')[0]}")

        return df_main, json_data

    def get_main_stats(self, df_main_ordered_top15):
        recoveryrate = {}
        dct_data = {}
        try:
            max_index = df_main_ordered_top15[df_main_ordered_top15.date == df_main_ordered_top15.date.max()].index
            recoveryrate['date'] = df_main_ordered_top15.loc[max_index]['date'].values[0]
            recoveryrate['rate'] = round((int(df_main_ordered_top15.loc[max_index]['totalrecovered']) / int(
                df_main_ordered_top15.loc[max_index]['totalconfirmed'])) * 100, 2)

        except:
            recoveryrate = 'N/A'

        df_main_ordered_top15 = df_main_ordered_top15.sort_values(by='date')
        dct = {}
        try:
            dct['dates'] = list(df_main_ordered_top15.date.values)
            dct['case_confirmed'] = list(df_main_ordered_top15.dailyconfirmed.values)
            dct['deaths'] = list(df_main_ordered_top15.dailydeceased.values)
            dct['recovery_rate'] = recoveryrate
            dct_data['main_data'] = dct
        except:
            dct_data = {}

        return dct_data


    def create_dataset(self):
        dct_data_state = {}
        
        df_main_data, json_data = self.get_master_data()
        if df_main_data.empty == False:
            df_main_ordered = df_main_data.sort_values(by='date', ascending=False)
            df_main_ordered_top15 = df_main_ordered[:15]
            dct_data_set = self.get_main_stats(df_main_ordered_top15)
        # State wise dataset

        df_state_wise = pd.DataFrame()
        if json_data.status_code == 200 and bool(json_data.content) == True:
            if 'statewise' in json.loads(json_data.content):
                df_state_wise = json.loads(json_data.content)
                df_state_wise = pd.DataFrame(df_state_wise['statewise'])


        if df_state_wise.empty == False:
            if df_state_wise.shape[0] > 20:
                df_state_wise_top15 = df_state_wise.iloc[:20]

        dct_data_set['State_Name'] = ['Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh', ' Daman and Diu', 'Delhi', 'Dadra and Nagar Haveli', 'Goa', 'Gujarat', 'Himachal Pradesh', 'Haryana', 'Jharkhand', 'Ladakh', 'Karnataka', 'Kerala', 'Lakshadweep', 'Maharashtra', 'Meghalaya', 'Manipur', 'Madhya Pradesh', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Puducherry', 'Rajasthan', 'Sikkim', 'Telangana', 'Tamil Nadu', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Jammu and Kashmir']
        return dct_data_set


@app.route('covid19dataset.herokuapp.com', methods = ['GET','POST'] )
def product_info():
    prd = Analytics(request)
    ret_json = prd.create_dataset()
    return ret_json

if __name__ == '__main__':
    app.run(debug=True)