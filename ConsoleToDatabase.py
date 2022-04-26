# Importing packages
import re
from datetime import datetime as dt
import time
import os

import numpy as np
from selenium.common.exceptions import TimeoutException
from sqlalchemy import create_engine
import urllib
# import pyodbc
import pandas as pd
# from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service


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


def console_login(bot_, username, password, pin, wait):
    bot_.get("https://console.zerodha.com")
    WebDriverWait(bot_, wait).until(
        EC.element_to_be_clickable((By.XPATH, '//*[text()="Login with Kite "]'))
    )
    bot_.find_element(By.XPATH, '//*[text()="Login with Kite "]').click()
    WebDriverWait(bot_, wait).until(
        EC.presence_of_element_located((By.ID, 'userid'))
    )

    bot_.find_element(By.ID, 'userid').send_keys(username)
    bot_.find_element(By.ID, 'password').send_keys(password)
    bot_.find_element(By.CLASS_NAME, 'button-orange').click()
    WebDriverWait(bot_, wait).until(
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


def getting_stocks(bot_):
    # Proper stocks Data
    return pd.read_html(bot_.page_source)[0]


def breakup_dividend_data(bot_, i_, wait_):
    # object of ActionChains
    a = ActionChains(bot_)

    t = bot_.find_elements(By.CLASS_NAME, 'textleft')[i_]

    # Getting breakup and dividend details
    a.move_to_element(t).perform()
    bot_.find_elements(By.CLASS_NAME, 'context-menu-button')[i_].click()
    # WebDriverWait(bot_, wait_).until(
    #     EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "breakdown")]'))
    # )
    bot_.find_element(By.XPATH, '//*[contains(text(), "breakdown")]').click()
    delay()
    breakdown = pd.read_html(bot_.page_source)[1]
    bot_.find_element(By.CLASS_NAME, 'close-modal').click()
    delay()
    a.move_to_element(t).perform()
    bot_.find_elements(By.CLASS_NAME, 'context-menu-button')[i_].click()
    WebDriverWait(bot_, wait_).until(
        EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "dividend")]'))
    )
    bot_.find_element(By.XPATH, '//*[contains(text(), "dividend")]').click()
    delay()
    try:
        dividend_ = pd.read_html(bot_.page_source)[1]
    except IndexError:
        dividend_ = pd.DataFrame(columns=['Date', 'Qty', 'Dividend / Share (DPS)', 'Total dividend'])
    bot_.find_element(By.CLASS_NAME, 'close-modal').click()
    return [breakdown, dividend_]


def write_table(df, tbl_name, if_exists='append'):
    quoted = urllib.parse.quote_plus(
        "DRIVER={SQL Server Native Client 11.0};SERVER=VIVOBOOK-PRO;DATABASE=akash;Trusted_Connection=yes;")
    engine = create_engine('mssql+pyodbc:///?odbc_connect={}'.format(quoted))

    df.to_sql(tbl_name, schema='dbo', con=engine, index=False, if_exists=if_exists)


def replace_function(date_with_attributes):
    return date_with_attributes.replace(' ipo', '').replace(' bonus', '')


def sector(bot, name='current'):
    sector_allocation = bot.find_element(By.CLASS_NAME, 'scLabels').text
    sector_name, allocation_percentage = [], []

    for index, _ in enumerate(sector_allocation.split("\n")):
        if index % 2 != 0:
            allocation_percentage.append(_)
        else:
            sector_name.append(_)
    return pd.DataFrame({'sector_name': sector_name, 'allocation_percentage_' + name: allocation_percentage})


def cap(bot, name='current'):
    cap_allocation = bot.find_element(By.ID, 'stock_labels').text
    cap_name, allocation_percentage = [], []

    for i, _ in enumerate(cap_allocation.split("\n")):
        if i % 2 != 0:
            allocation_percentage.append(_)
        else:
            cap_name.append(_)

    return pd.DataFrame({'cap_name': cap_name, 'allocation_percentage_' + name: allocation_percentage}).iloc[:3]


def breakup_dividend_complete(bot, portfolio_table, wait_, last_update_date):
    # Getting breakup and dividend table details
    breakup_details = pd.DataFrame(columns=['Symbol', 'Date', 'Qty.', 'Price', 'Age (days)', 'P&L'])
    dividend_details = pd.DataFrame(columns=['Symbol', 'Date', 'Qty', 'Dividend / Share (DPS)', 'Total dividend'])
    for stock_counter in range(len(portfolio_table)):
        symbol = portfolio_table.iloc[stock_counter]['Symbol']
        try:
            breakup, dividend = breakup_dividend_data(bot, stock_counter, wait_)
            breakup = breakup[np.arange(len(breakup)) % 2 == 0]
            breakup['Symbol'] = symbol
            breakup_details = pd.concat([breakup_details, breakup])
            if len(dividend) != 0:
                dividend['Symbol'] = symbol
                dividend_details = pd.concat([dividend_details, dividend])
        except TimeoutException:
            print(f"Error for {symbol}")
    breakup_details['Date'] = breakup_details['Date'].apply(replace_function)
    breakup_details['source_last_updated'] = last_update_date
    breakup_details['last_update_date'] = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
    dividend_details['source_last_updated'] = last_update_date
    dividend_details['last_update_date'] = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
    write_table(dividend_details, 'dividend', if_exists='replace')
    write_table(breakup_details, 'breakup', if_exists='replace')


def sector_cap_complete(bot, last_update_date):
    sector_wise_data = sector(bot)
    cap_wise_data = cap(bot)
    bot.find_elements(By.CLASS_NAME, 'su-radio-label')[1].click()
    delay()
    sector_wise_data_ = sector(bot, name='invested')
    cap_wise_data_ = cap(bot, name='invested')
    cap_wise_data = pd.merge(cap_wise_data, cap_wise_data_, on="cap_name")
    sector_wise_data = pd.merge(sector_wise_data, sector_wise_data_, on="sector_name")
    cap_wise_data['source_last_updated'] = last_update_date
    cap_wise_data['last_update_date'] = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
    sector_wise_data['source_last_updated'] = last_update_date
    sector_wise_data['last_update_date'] = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
    write_table(cap_wise_data, 'cap_table', if_exists='replace')
    write_table(sector_wise_data, 'sector_table', if_exists='replace')


def insights_extract(bot, wait, last_update_date):
    bot.find_element(By.CLASS_NAME, 'insights').click()
    bot.find_element(By.CLASS_NAME, 'su-checkbox-label').click()
    iframe = bot.find_element(By.ID, 'insights_frame')
    WebDriverWait(bot, 2 * wait).until(
        EC.presence_of_element_located((By.ID, 'insights_frame'))
    )
    bot.switch_to.frame(iframe)
    delay()
    tickertape_elements = bot.find_elements(By.CLASS_NAME, 'card-title')
    beta = tickertape_elements[0].text.replace("Beta (β): ", "")
    pe_ratio = tickertape_elements[1].text.replace("PE Ratio: ", "")
    red_flags = tickertape_elements[3].text.replace("Redflags: ", "").replace("🚩", "")
    overall_price_forecast = tickertape_elements[2].text.replace("Price Forecast: ", "")
    insights = pd.DataFrame(
        {'Beta': beta, 'PE_ratio': pe_ratio, 'overall_price_forecast': overall_price_forecast, 'Red_Flags': red_flags,
         'source_last_updated': last_update_date,
         'last_updated': dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")}, index=[0])
    write_table(insights, 'insights', if_exists='replace')


def forecast_function(bot, last_update_date):
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
    regex_pattern_for_getting_forecast = re.compile(r"([A-Z]+) ([\d.%]+)\n.+?([\d.%]+).+?([\d.]+%)")
    forecast_list = regex_pattern_for_getting_forecast.findall(portfolio_forecast_table_details)
    forecast_dataframe = pd.DataFrame(forecast_list,
                                      columns=['stock_name', 'forecast%', 'expected_return%', 'last3years_cagr%'])
    forecast_dataframe['last_update_date'] = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
    forecast_dataframe['source_last_updated'] = last_update_date
    write_table(forecast_dataframe, 'forecast', if_exists='replace')


def main():
    wait = 10
    wait_ = 2
    # Creating chrome instance and login to console and opening Holdings section
    bot = console_login(chrome(), os.environ['zerodha_username'], os.environ['zerodha_password'],
                        os.environ['zerodha_pin'], wait)
    # Last Updated date
    last_update_date = re.findall(r'(\d\d\d\d-\d\d-\d\d)', bot.find_element(By.CLASS_NAME, 'last-updated').text)[0]
    # Getting portfolio details table
    portfolio_table = getting_stocks(bot)
    portfolio_table['last_update_date'] = dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S")
    portfolio_table['source_last_updated'] = last_update_date
    write_table(portfolio_table.drop('Prev. close', axis=1), 'TargetTable', if_exists='replace')
    breakup_dividend_complete(bot, portfolio_table, wait_, last_update_date)
    # Getting sector and cap wise data
    sector_cap_complete(bot, last_update_date)
    # Getting Insights
    insights_extract(bot, wait, last_update_date)
    # PriceForecast details
    forecast_function(bot, last_update_date)


if __name__ == '__main__':
    main()
