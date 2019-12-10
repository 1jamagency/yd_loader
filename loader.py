# -*- coding: utf-8 -*-
import time
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
import requests
from requests.exceptions import ConnectionError
from time import sleep
import json
import os
import sys

path = '/Users/pavelkoryakin/Projects/yd-loader/'

if sys.version_info < (3,):
    def u(x):
        try:
            return x.encode("utf8")
        except UnicodeDecodeError:
            return x
else:
    def u(x):
        if type(x) == type(b''):
            return x.decode('utf8')
        else:
            return x

# --- Input data ---
#  Address of the Reports service for sending JSON requests (case-sensitive)
ReportsURL = 'https://api.direct.yandex.com/json/v5/reports'

# OAuth token of the user that requests will be made on behalf of
token = 'ваш токен'

# Login of the advertising agency client
# Required parameter if requests are made on behalf of an advertising agency
clientLogin = 'ваш логин в Директе'

# --- Preparing the request ---
#  Creating HTTP request headers
headers = {
    # OAuth token. The word Bearer must be used
    "Authorization": "Bearer " + token,
    # Login of the advertising agency client
    "Client-Login": clientLogin,
    # Language for response messages
    "Accept-Language": "en",
    # Mode for report generation
    "processingMode": "auto",
    # Format for monetary values in the report
    # "returnMoneyInMicros": "false",
    # Don't include the row with the report name and date range in the report
    "skipReportHeader": "true",
    # Don't include the row with column names in the report
    # "skipColumnHeader": "true",
    # Don't include the row with the number of statistics rows in the report
    "skipReportSummary": "true"
}

# Set start day
dateS = datetime.strptime("2018-03-01", '%Y-%m-%d')
dateE = dateS + relativedelta(months=+1, days=-1)

# Creating the request message body

while True:

    s = dateS.strftime('%Y-%m-%d') + ' ' + dateE.strftime('%Y-%m-%d')
    print(s)

    now = datetime.now()

    if  now < dateS:
        break

    body = {
        "params": {
            "SelectionCriteria": {
                "DateFrom": dateS.strftime('%Y-%m-%d'),
                "DateTo": dateE.strftime('%Y-%m-%d')
            },
            "FieldNames": [
                "Month",
                "CampaignName",
                "CampaignId",
                "CampaignType",
                "AdGroupName",
                "AdGroupId",
                "AdFormat",
                "AdId",
                "CriterionId",
                "Criterion",
                "CriterionType",
                "Age",
                "Gender",
                "AdNetworkType",
                "Device",
                "MobilePlatform",
                "LocationOfPresenceId",
                "RlAdjustmentId",
                "Placement",
                "Slot",
                "Impressions",
                "Clicks",
                "Cost"
            ],
            "ReportName": u("Test1311"+dateS.strftime('%Y-%m-%d')),
            "Page": {
                "Limit": 4000000
            },
            "ReportType": "CUSTOM_REPORT",
            "DateRangeType": "CUSTOM_DATE",
            "Format": "TSV",
            "IncludeVAT": "YES",
            "IncludeDiscount": "NO"
        }
    }

    body = json.dumps(body, indent=4)

    while True:
        try:
            req = requests.post(ReportsURL, body, headers=headers)
            req.encoding = 'utf-8'  # Принудительная обработка ответа в кодировке UTF-8
            if req.status_code == 400:
                print("Параметры запроса указаны неверно или достигнут лимит отчетов в очереди")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код запроса: {}".format(u(body)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            elif req.status_code == 200:
                print("Отчет создан успешно")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                #print("Содержание отчета: \n{}".format(u(req.text)))
                break
            elif req.status_code == 201:
                print("Отчет успешно поставлен в очередь в режиме офлайн")
                retryIn = int(req.headers.get("retryIn", 60))
                print("Повторная отправка запроса через {} секунд".format('60'))
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                sleep(60)
            elif req.status_code == 202:
                print("Отчет формируется в режиме офлайн")
                retryIn = int(req.headers.get("retryIn", 60))
                print("Повторная отправка запроса через {} секунд".format(retryIn))
                print("RequestId:  {}".format(req.headers.get("RequestId", False)))
                sleep(retryIn)
            elif req.status_code == 500:
                print("При формировании отчета произошла ошибка. Пожалуйста, попробуйте повторить запрос позднее")
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            elif req.status_code == 502:
                print("Время формирования отчета превысило серверное ограничение.")
                print("Пожалуйста, попробуйте изменить параметры запроса - уменьшить период и количество запрашиваемых данных.")
                print("JSON-код запроса: {}".format(body))
                print("RequestId: {}".format(req.headers.get("RequestId", False)))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break
            else:
                print("Произошла непредвиденная ошибка")
                print("RequestId:  {}".format(req.headers.get("RequestId", False)))
                print("JSON-код запроса: {}".format(body))
                print("JSON-код ответа сервера: \n{}".format(u(req.json())))
                break


        # Обработка ошибки, если не удалось соединиться с сервером API Директа
        except ConnectionError:
            # В данном случае мы рекомендуем повторить запрос позднее
            print("Произошла ошибка соединения с сервером API")
            # Принудительный выход из цикла
            break

        # Если возникла какая-либо другая ошибка
        except:
            # В данном случае мы рекомендуем проанализировать действия приложения
            print("Произошла непредвиденная ошибка")
            # Принудительный выход из цикла
            break


    with open((os.path.join(path,dateS.strftime('%Y%m%d')+'-'+dateE.strftime('%Y%m%d')+'.tsv')),'w') as f:
        f.write(req.text)

    dateS = dateS + relativedelta(months=+1)
    dateE = dateS + relativedelta(months=+1, days=-1)