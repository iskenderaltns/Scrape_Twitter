from time import sleep

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC


class TwitterScrape:
    def __init__(self, username, password, key):
        self.username_key = username
        self.password_key = password
        self.key = key
        self.url_login = ''
        self.headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
        self.driver = None
        self.options = None
        self.wait = None
        self.username = None
        self.password = None
        self.search = None
        self.data = []
        self.tweet_ids = set()
        self.last_position = None
        self.scroll = True

    def start_driver(self):
        self.options = ChromeOptions()
        self.options.add_argument("--start-maximized")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = Chrome(options=self.options)

    def stop_driver(self):
        if self.driver:
            self.driver.quit()

    def login(self):
        self.start_driver()
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get("https://twitter.com/login")
        self.username = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="text"]')))
        self.username.send_keys(self.username_key)
        self.username.send_keys(Keys.ENTER)

        self.password = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
        self.password.send_keys(self.password_key)
        self.password.send_keys(Keys.ENTER)

    def search_key_word(self):
        self.login()
        self.search = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-testid="SearchBox_Search_Input"]')))
        self.search.send_keys(self.key)
        self.search.send_keys(Keys.ENTER)

    def running(self):
        self.search_key_word()
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]')))
        self.last_position = self.driver.execute_script("return window.pageYOffset;")
        while self.scroll:
            page_articles = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
            for article in page_articles:
                tweet = self.get_tweet_data(article)
                if tweet:
                    tweet_id = ''.join(tweet)
                    if tweet_id not in self.tweet_ids:
                        self.tweet_ids.add(tweet_id)
                        self.data.append(tweet)

            scroll_attempt = 0
            while True:
                self.driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
                sleep(3)
                current_position = self.driver.execute_script("return window.pageYOffset;")
                if self.last_position == current_position:
                    scroll_attempt += 1

                    if scroll_attempt >= 3:
                        self.scroll = False
                        break
                    else:
                        sleep(2)
                else:
                    self.last_position = current_position
                    break
        self.save_excel()

    @staticmethod
    def get_tweet_data(article):
        user = article.find_element(By.CSS_SELECTOR, 'div[data-testid="User-Name"]').text.split('\n')
        name = user[0]
        username = user[1]
        postdate = article.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
        tweetText = article.find_element(By.XPATH, ".//div[@data-testid='tweetText']").text
        reply_count = article.find_element(By.XPATH, ".//div[@data-testid='reply']").text
        retweet_count = article.find_element(By.XPATH, ".//div[@data-testid='retweet']").text
        like_count = article.find_element(By.XPATH, ".//div[@data-testid='like']").text
        try:
            img_url = article.find_element(By.XPATH, ".//div[@data-testid='tweetPhoto']")
            img = img_url.find_element(By.TAG_NAME, 'img').get_attribute('src')
        except:
            img = ''
        return name, username, postdate, tweetText, reply_count, retweet_count, like_count, img

    def save_excel(self):
        columns = ['from', 'username', 'date', 'tweet', 'reply', 'retweet', 'like', 'img_url']
        data_dict = {column: [k[idx] for k in self.data] for idx, column in enumerate(columns)}

        dataframe = pd.DataFrame(data_dict)
        dataframe.to_excel('Newfile.xlsx')

        self.stop_driver()


TwitterScrape('usurname', 'password', 'key_words').running()