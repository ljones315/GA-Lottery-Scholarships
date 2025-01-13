import re
import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def get_data():

    def clean_county_name(name):
        cleaned = re.sub(r'\bcounty\b', '', name, flags=re.IGNORECASE).strip()
        return cleaned.upper()

    def currency_to_float(currency_str):
        if not currency_str:
            return 0.0
        cleaned = re.sub(r'[^0-9.]', '', currency_str)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    # read income data from CSV
    county_income_data = {}
    csv_file_path = 'HDPulse_data_export.csv'
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            raw_county = row['\ufeffCounty']
            county_key = clean_county_name(raw_county)
            county_income_data[county_key] = row['Value (Dollars)']

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    try:
        driver.get("https://www.galottery.com/en-us/benefitting-georgia/county-proceeds.html")
        wait = WebDriverWait(driver, 10)
        select_element = wait.until(EC.presence_of_element_located((By.ID, "selectcounty")))
        dropdown = Select(select_element)

        columns = ['Scholarship Recipients', 'HOPE Money', '', '', 'Lottery Prizes', 'Lottery Sales', '']
        counties_data = {}

        for option in dropdown.options:
            value = option.get_attribute("value")
            text = option.text.strip()
            if value == "" or text.lower().startswith("select a county"):
                continue

            dropdown.select_by_value(value)
            updated_div = wait.until(EC.presence_of_element_located((By.ID, "countryProceedsInfo")))
            elements = updated_div.find_elements(By.CLASS_NAME, "pull-right")

            county_name = text.upper()
            counties_data[county_name] = {}
            curr = counties_data[county_name]
            for i, e in enumerate(elements):
                if i < len(columns) and columns[i]:
                    curr[columns[i]] = e.text

        county_names = []
        ratios = []
        incomes = []

        for county, data in counties_data.items():
            hope_str = data.get('HOPE Money', '0')
            sales_str = data.get('Lottery Sales', '0')
            hope_value = currency_to_float(hope_str)
            sales_value = currency_to_float(sales_str)
            ratio = hope_value / sales_value if sales_value != 0 else 0

            income_str = county_income_data.get(county, "0")
            income_value = currency_to_float(income_str)

            county_names.append(county)
            ratios.append(ratio)
            incomes.append(income_value)

    finally:
        driver.quit()

    data = {
        'County': county_names,
        'Ratio': ratios,
        'Income': incomes
    }
    df = pd.DataFrame(data)
    pd.to_pickle(df, './data')  # save df as a pickle file
