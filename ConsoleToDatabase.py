# Importing packages
import re
# from datetime import datetime as dt
import time
import os

import pandas as pd
# from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

wait = 10


# Creating chrome function
def chrome():
    """This creates a chrome instance using selenium"""
    options = webdriver.ChromeOptions()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--safebrowsing-disable-download-protection")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def delay(time_=3):
    time.sleep(time_)


def console_login(bot_, username, password, pin):
    bot_.get("https://console.zerodha.com")
    WebDriverWait(bot, wait).until(
        EC.element_to_be_clickable((By.XPATH, '//*[text()="Login with Kite "]'))
    )
    bot_.find_element(By.XPATH, '//*[text()="Login with Kite "]').click()
    WebDriverWait(bot, wait).until(
        EC.presence_of_element_located((By.ID, 'userid'))
    )

    bot_.find_element(By.ID, 'userid').send_keys(username)
    bot_.find_element(By.ID, 'password').send_keys(password)
    bot_.find_element(By.CLASS_NAME, 'button-orange').click()
    WebDriverWait(bot, wait).until(
        EC.presence_of_element_located((By.ID, 'pin'))
    )

    bot_.find_element(By.ID, 'pin').send_keys(pin)
    bot_.find_element(By.CLASS_NAME, 'button-orange').click()
    WebDriverWait(bot_, wait).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'portfolio-id'))
    )

    bot_.find_element(By.CLASS_NAME, 'portfolio-id').click()
    bot_.find_element(By.XPATH, '//*[text()="Holdings"]').click()

    WebDriverWait(bot_, wait).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'su-checkbox-label'))
    )

    bot_.find_element(By.CLASS_NAME, 'su-checkbox-label').click()
    return bot_


# Creating chrome instance and login to console and opening Holdings section
bot = console_login(chrome(), os.environ['zerodha_username'], os.environ['zerodha_password'], os.environ['zerodha_pin'])

# Proper stocks Data
portfolio_table = pd.read_html(bot.page_source)[0]

# object of ActionChains
a = ActionChains(bot)

t = bot.find_elements(By.CLASS_NAME, 'textleft')[2]

# Getting breakup and dividend details
a.move_to_element(t).perform()
print(len(bot.find_elements(By.CLASS_NAME, 'flag-container')))
bot.find_elements(By.CLASS_NAME, 'flag-container')[2].click()
bot.find_element(By.XPATH, '//*[contains(text(), "breakdown")]').click()
delay()
breakdown = pd.read_html(bot.page_source)[1]
bot.find_element(By.CLASS_NAME, 'close-modal').click()
delay()
a.move_to_element(t).perform()
bot.find_elements(By.CLASS_NAME, 'flag-container')[2].click()
bot.find_element(By.XPATH, '//*[contains(text(), "dividend")]').click()
delay()
try:
    dividend = pd.read_html(bot.page_source)[1]
    print(dividend)
except IndexError:
    pass
bot.find_element(By.CLASS_NAME, 'close-modal').click()
print(breakdown)

# ****** Getting Current reports ******
# Getting sector wise
sector_allocation = bot.find_element(By.CLASS_NAME, 'scLabels').text
sector_name, allocation_percentage_now = [], []

for i, _ in enumerate(sector_allocation.split("\n")):
    if i % 2 != 0:
        allocation_percentage_now.append(_)
    else:
        sector_name.append(_)

sector_wise_data = pd.DataFrame({'sector_name': sector_name, 'allocation_percentage_now': allocation_percentage_now})

# Getting cap wise 
cap_allocation = bot.find_element(By.ID, 'stock_labels').text
cap_name, allocation_percentage_now = [], []

for i, _ in enumerate(cap_allocation.split("\n")):
    if i % 2 != 0:
        allocation_percentage_now.append(_)
    else:
        cap_name.append(_)

stocks_wise_data = pd.DataFrame({'cap_name': cap_name, 'allocation_percentage_now': allocation_percentage_now})
cap_wise_data = stocks_wise_data.iloc[:3]

# ****** Getting Invested Reports *******
bot.find_elements(By.CLASS_NAME, 'su-radio-label')[1].click()

# Getting sector wise
sector_allocation = bot.find_element(By.CLASS_NAME, 'scLabels').text
sector_name, allocation_percentage_invested = [], []

for i, _ in enumerate(sector_allocation.split("\n")):
    if i % 2 != 0:
        allocation_percentage_invested.append(_)
    else:
        sector_name.append(_)

sector_wise_data_ = pd.DataFrame(
    {'sector_name': sector_name, 'allocation_percentage_invested': allocation_percentage_invested})

# Getting cap wise
cap_allocation = bot.find_element(By.ID, 'stock_labels').text
cap_name, allocation_percentage_invested = [], []

for i, _ in enumerate(cap_allocation.split("\n")):
    if i % 2 != 0:
        allocation_percentage_invested.append(_)
    else:
        cap_name.append(_)

stocks_wise_data = pd.DataFrame(
    {'cap_name': cap_name, 'allocation_percentage_invested': allocation_percentage_invested})
cap_wise_data_ = stocks_wise_data.iloc[:3]

# Merging the current and invested datasets
cap_wise_data = pd.merge(cap_wise_data, cap_wise_data_, on="cap_name")
sector_wise_data = pd.merge(sector_wise_data, sector_wise_data_, on="sector_name")

# Last Updated date
last_update_date = re.findall(r'(\d\d\d\d-\d\d-\d\d)', bot.find_element(By.CLASS_NAME, 'last-updated').text)[0]

# Getting Insights
bot.find_element(By.CLASS_NAME, 'insights').click()
bot.find_element(By.CLASS_NAME, 'su-checkbox-label').click()

iframe = bot.find_element(By.ID, 'insights_frame')

WebDriverWait(bot, 2 * wait).until(
    EC.presence_of_element_located((By.ID, 'insights_frame'))
)

bot.switch_to.frame(iframe)

tickertape_elements = bot.find_elements(By.CLASS_NAME, 'card-title')
Beta = tickertape_elements[0].text.replace("Beta (β): ", "")
PE_ratio = tickertape_elements[1].text.replace("PE Ratio: ", "")
Red_Flags = tickertape_elements[3].text.replace("Redflags: ", "").replace("🚩", "")

# PriceForecast details
overall_price_forecast = tickertape_elements[2].text.replace("Price Forecast: ", "")
bot.find_element(By.CLASS_NAME, 'card-link').click()
portfolio_forecast_table_details = bot.find_element(By.CLASS_NAME, 'insight-container').text
bot.find_element(By.CLASS_NAME, 'nav-arrow-button').click()
delay()
portfolio_forecast_table_details += bot.find_element(By.CLASS_NAME, 'insight-container').text
bot.find_elements(By.CLASS_NAME, 'nav-arrow-button')[1].click()
delay()
portfolio_forecast_table_details += bot.find_element(By.CLASS_NAME, 'insight-container').text
bot.find_elements(By.CLASS_NAME, 'nav-arrow-button')[1].click()
delay()
portfolio_forecast_table_details += bot.find_element(By.CLASS_NAME, 'insight-container').text

regex_pattern_for_getting_forecast = re.compile(r"([A-Z]+) ([0-9.%]+)\n.+?([0-9.%]+).+?([0-9.]+%)")

forecast_list = regex_pattern_for_getting_forecast.findall(portfolio_forecast_table_details)

forecast_dataframe = pd.DataFrame(forecast_list,
                                  columns=['stock_name', 'forecast%', 'expected_return%', 'last3years_cagr%'])
