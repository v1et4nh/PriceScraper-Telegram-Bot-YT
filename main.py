# -*- coding: utf-8 -*-

import requests
import pathlib
import os
from datetime import datetime
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
bot_token = str(os.getenv('TELEGRAM_BOT_TOKEN'))    # Replace with your own bot_token
bot_chatID = str(os.getenv('TELEGRAM_BOT_CHATID'))  # Replace with your own bot_chatID


def telegram_bot_sendtext(bot_message):
    send_text  = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    return response.json()


def telegram_bot_sendphoto(str_picpath):
    send_photo = 'https://api.telegram.org/bot' + bot_token + '/sendPhoto?chat_id=' + bot_chatID
    files = {'photo': open(str_picpath, 'rb')}
    img_stat = requests.post(send_photo, files=files)
    return img_stat


def get_savepath():
    current_path = pathlib.Path(__file__).parent.absolute()
    tmp = os.path.join(current_path, "screenshot")
    now = datetime.now()
    str_now = now.strftime("%Y%m%d_%H%M%S")
    filename = str_now + '.png'
    str_path = os.path.join(tmp, filename)
    return str_path


class Flaschenpost:
    def __init__(self, list_beverage, run_background=True):
        # Initialize browser
        if run_background:
            os.environ['MOZ_HEADLESS'] = '1'  # Run Firefox in the background if True
        self.service_log_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "geckodriver.log")
        self.driver           = webdriver.Firefox(service_log_path=self.service_log_path)
        self.wait             = WebDriverWait(self.driver, 10)

        # Data
        self.zipcode         = os.getenv('ZIPCODE')
        self.zipcode_entered = False
        self.list_beverage   = list_beverage

    def enter_zipcode(self):
        if not self.zipcode_entered:
            zipcode_input = self.wait.until(EC.presence_of_element_located((By.ID, "validZipcode")))
            sleep(1)
            zipcode_input.send_keys(self.zipcode)
            sleep(1)
            self.driver.find_element_by_class_name("fp-button").click()
            sleep(2)
            self.zipcode_entered = True

    def get_current_price(self, name):
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fp_article_price")))
        dict_price = self.driver.find_elements_by_class_name("fp_article_price")
        list_current_price = []
        for price_idx in range(len(dict_price)):
            current_price = dict_price[price_idx].text
            print(name + ': ' + current_price)
            current_price = current_price.replace('€', '').strip()
            current_price = current_price.replace(',', '.').strip()
            list_current_price.append(float(current_price))
        list_current_price.sort()
        return list_current_price[0]

    def get_screenshot(self):
        str_fpath = get_savepath()
        self.driver.save_screenshot(str_fpath)
        return str_fpath

    def run(self):
        for name, url, pricetrigger in self.list_beverage:
            self.driver.get(url)
            self.enter_zipcode()
            try:
                current_price = self.get_current_price(name)
                if current_price <= pricetrigger:
                    screenshot  = self.get_screenshot()
                    str_message = name + ': ' + str(current_price) + '€\n' + url
                    telegram_bot_sendtext(str_message)
                    telegram_bot_sendphoto(screenshot)
            except:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "fp_article_outOfStock")))
                    print(name + ': Out of Stock')
                except TimeoutException as e:
                    telegram_bot_sendtext(str(e) + 'Timeout')
        self.driver.quit()


if __name__ == "__main__":
    # (name, url, pricetrigger)
    list_beverage = [('Volvic', 'https://www.flaschenpost.de/volvic/volvic-naturelle', 5),
                     ('Spezi', 'https://www.flaschenpost.de/paulaner-spezi/paulaner-spezi', 10),
                     ('FritzKola', 'https://www.flaschenpost.de/fritz-kola/fritz-kola', 18)]

    flaschenpost = Flaschenpost(list_beverage=list_beverage, run_background=False)
    flaschenpost.run()

    print('Finished scraping')
