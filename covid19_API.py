import calendar

from flask import Flask, request, make_response
from flask_cors import CORS, cross_origin

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
        confirmed_data = {'totalconfirmed': '', 'confirmed_max_date': ''}
        detailed_data = {'totalrecovered': '', 'totaldeceased': ''}
        dct_data = {}
        try:
            max_index = df_main_ordered_top15[df_main_ordered_top15.date == df_main_ordered_top15.date.max()].index
            recoveryrate['date'] = df_main_ordered_top15.loc[max_index]['date'].values[0]
            recoveryrate['rate'] = round((int(df_main_ordered_top15.loc[max_index]['totalrecovered']) / int(
                df_main_ordered_top15.loc[max_index]['totalconfirmed'])) * 100, 2)

            confirmed_data['totalconfirmed'] = int(df_main_ordered_top15.loc[max_index]['totalconfirmed'])
            confirmed_data['confirmed_max_date'] = df_main_ordered_top15.loc[max_index]['date'].values[0]
            detailed_data['totalrecovered'] = int(df_main_ordered_top15.loc[max_index]['totalrecovered'])
            detailed_data['totaldeceased'] = int(df_main_ordered_top15.loc[max_index]['totaldeceased'])
            #print(df_main_ordered_top15.loc[max_index])
        except:
            recoveryrate = 'N/A'

        df_main_ordered_top15 = df_main_ordered_top15.sort_values(by='date')
        dct = {}
        try:
            dct['dates'] = list(df_main_ordered_top15.date.values)
            dct['case_confirmed'] = list(df_main_ordered_top15.dailyconfirmed.values)
            dct['deaths'] = list(df_main_ordered_top15.dailydeceased.values)
            dct['recovery_rate'] = recoveryrate
            dct['confirmed_data'] = confirmed_data
            dct['Detailed_data'] = detailed_data
            dct_data['main_data'] = dct


        except:
            dct_data = {}

        return dct_data


    def create_dataset(self):
        state_names = ['Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh', ' Daman and Diu', 'Delhi', 'Dadra and Nagar Haveli', 'Goa', 'Gujarat', 'Himachal Pradesh', 'Haryana', 'Jharkhand', 'Ladakh', 'Karnataka', 'Kerala', 'Lakshadweep', 'Maharashtra', 'Meghalaya', 'Manipur', 'Madhya Pradesh', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Puducherry', 'Rajasthan', 'Sikkim', 'Telangana', 'Tamil Nadu', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Jammu and Kashmir']
        df_main_data, json_data = self.get_master_data()
        state_data = []
        if df_main_data.empty == False:
            df_main_ordered = df_main_data.sort_values(by='date', ascending=False)
            df_main_ordered_top15 = df_main_ordered[:15]
            dct_data_set = self.get_main_stats(df_main_ordered_top15)
        # State wise dataset


        df_state_wise = pd.DataFrame()
        if json_data.status_code == 200 and bool(json_data.content) == True:
            if 'statewise' in json.loads(json_data.content):
                df_state_wise = json.loads(json_data.content)
                #dct_data_set['statewise'] = df_state_wise['statewise']
                for dt in state_names:
                    for states in df_state_wise['statewise']:
                        if dt.lower() == states['state'].lower():
                            states.pop('statecode', None)
                            if 'statenotes' in states:
                                if states['statenotes'] == "":
                                    states.pop('statenotes', None)

                            state_data.append({dt.lower(): states})


                dct_data_set['statewise'] = state_data
                df_state_wise = pd.DataFrame(df_state_wise['statewise'])


        if df_state_wise.empty == False:
            if df_state_wise.shape[0] > 20:
                df_state_wise_top15 = df_state_wise.iloc[:20]

        dct_data_set['State_Name'] = state_names
        return dct_data_set


@app.route('/',  methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def product_info():
    prd = Analytics(request)
    ret_json = prd.create_dataset()
    return ret_json

if __name__ == '__main__':
    CORS(app, support_credentials=True)
    app.run(debug=True)
