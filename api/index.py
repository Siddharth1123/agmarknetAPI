from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime, timedelta
from selenium.webdriver.support import expected_conditions as EC

def script(state, commodity, market):
    initial_url = "https://agmarknet.gov.in/SearchCmmMkt.aspx"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')

    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver.get(initial_url)

    # Explicitly remove popup via JavaScript (Reliable method)
    driver.execute_script("""
        var popup = document.querySelector('.popup-onload');
        if (popup) {
            popup.parentNode.removeChild(popup);
        }
        var overlay = document.querySelector('.ui-widget-overlay');
        if (overlay) {
            overlay.parentNode.removeChild(overlay);
        }
    """)
    time.sleep(1)

    # Select Commodity
    dropdown = Select(driver.find_element(By.ID, 'ddlCommodity'))
    dropdown.select_by_visible_text(commodity)

    # Select State
    dropdown = Select(driver.find_element(By.ID, 'ddlState'))
    dropdown.select_by_visible_text(state)

    # Set Date (7 days ago)
    today = datetime.now()
    desired_date = today - timedelta(days=7)
    date_input = driver.find_element(By.ID, "txtDate")
    date_input.clear()
    date_input.send_keys(desired_date.strftime('%d-%b-%Y'))

    # Click Go button clearly (JavaScript click)
    go_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'btnGo')))
    driver.execute_script("arguments[0].click();", go_button)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'ddlMarket'))
    )

    # Select Market
    dropdown = Select(driver.find_element(By.ID, 'ddlMarket'))
    dropdown.select_by_visible_text(market)

    # Click Go button again clearly (JavaScript click)
    go_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'btnGo')))
    driver.execute_script("arguments[0].click();", go_button)

    # Wait for the results clearly
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'cphBody_GridPriceData'))
    )

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    data_list = []
    for row in soup.find_all("tr"):
        data_list.append(row.text.replace("\n", "_").replace("  ", "").split("__"))

    jsonList = []
    for i in data_list[4:len(data_list) - 1]:
        d = {
            "S.No": i[1],
            "City": i[2],
            "Commodity": i[4],
            "Min Prize": i[7],
            "Max Prize": i[8],
            "Model Prize": i[9],
            "Date": i[10]
        }
        jsonList.append(d)

    driver.quit()
    return jsonList



app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def homePage():
    dataSet = {"Page": "Home Page - API Running clearly!", "TimeStamp": time.time()}
    return jsonify(dataSet)

@app.route('/request', methods=['GET'])
def requestPage():
    commodityQuery = request.args.get('commodity')
    stateQuery = request.args.get('state')
    marketQuery = request.args.get('market')

    if not commodityQuery or not stateQuery or not marketQuery:
        return jsonify({"error": "Missing query parameters: commodity, state, market required."})

    try:
        json_data = script(stateQuery, commodityQuery, marketQuery)
        return jsonify(json_data)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run()
