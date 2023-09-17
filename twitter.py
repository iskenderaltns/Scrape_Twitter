from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as EC
import pandas as pd
from time import sleep
from selenium.webdriver.chrome.service import Service

class TwitterScrape:
    """
    The TwitterScrape class is used to scrape tweets related to a specific keyword on Twitter.

    Args:
        username (str): Twitter username.
        password (str): Twitter password.
        key (str): The keyword to search for.

    Attributes:
        username_key (str): Twitter username.
        password_key (str): Twitter password.
        key (str): The keyword to search for.
        url_login (str): Twitter login URL.
        headers (dict): HTTP headers for requests.
        driver (selenium.webdriver.Chrome): Selenium WebDriver object.
        options (selenium.webdriver.ChromeOptions): WebDriver options.
        wait (selenium.webdriver.support.ui.WebDriverWait): Selenium wait object.
        username (selenium.webdriver.remote.webelement.WebElement): Username field.
        password (selenium.webdriver.remote.webelement.WebElement): Password field.
        search (selenium.webdriver.remote.webelement.WebElement): Search box.
        data (list): Collected tweet data.
        tweet_ids (set): Unique tweet IDs.
        last_position (int): Page scrolling position.
        scroll (bool): Flag indicating whether scrolling is required.
        current_page_number (int): Current page number.

     Methods:
        running()
        key.csv : data scraped by keyword

    """

    def __init__(self, username, password, key):
        self.service = None
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
        self.current_page_number = 1

    def start_driver(self):
        """
        Starts the WebDriver and configures the necessary options.
        """
        self.service = Service()
        self.options = ChromeOptions()
        self.options.add_argument("--start-maximized")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.driver = Chrome(service = self.service, options=self.options)

    def stop_driver(self):
        """
        Quits the WebDriver.
        """
        if self.driver:
            self.driver.quit()

    def login(self):
        """
        Logs into Twitter.
        """
        self.start_driver()
        sleep(2)
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.get("https://twitter.com/login")
        self.username = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="text"]')))
        self.username.send_keys(self.username_key)
        self.username.send_keys(Keys.ENTER)

        self.password = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="password"]')))
        self.password.send_keys(self.password_key)
        self.password.send_keys(Keys.ENTER)

    def search_key_word(self):
        """
        Searches for the specified keyword on Twitter.
        """
        self.login()
        sleep(4)
        self.search = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-testid="SearchBox_Search_Input"]')))
        self.search.send_keys(self.key)
        self.search.send_keys(Keys.ENTER)
        sleep(4)

    def running(self):
        """
        Initiates the scraping loop to collect tweets.
        """
        self.search_key_word()
        print(self.key)
        current_url = self.driver.current_url
        last_twits_url = current_url + '&f=live'
        self.driver.get(last_twits_url)
        sleep(4)
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]')))
        self.last_position = self.driver.execute_script("return window.pageYOffset;")
        i = 0
        j = 100
        while self.scroll:
            self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]')))
            page_articles = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
            for article in page_articles:
                tweet = self.get_tweet_data(article)
                if tweet:
                    tweet_id = ''.join(tweet)
                    if tweet_id not in self.tweet_ids:
                        self.tweet_ids.add(tweet_id)
                        self.data.append(tweet)
            print(len(self.data))
            sleep(3)
            scroll_attempt = 0
            while True:
                self.driver.execute_script(f"window.scrollTo(0,{(i + 1) * j});")
                sleep(2)
                current_position = self.driver.execute_script("return window.pageYOffset;")
                i += 3
                if len(self.data) > 2000:
                    self.scroll = False
                    break
                if self.last_position == current_position:
                    scroll_attempt += 1
                    j = j - 10

                    if scroll_attempt >= 10:
                        self.scroll = False
                        break
                    else:
                        sleep(2)
                else:
                    self.last_position = current_position
                    break

        self.save_csv()

    @staticmethod
    def get_tweet_data(article):
        """
        Extracts necessary data from a tweet.

        Args:
            article (selenium.webdriver.remote.webelement.WebElement): WebElement representing the tweet.

        Returns:
            tuple: Tuple containing tweet data (from, username, date, tweet, reply, retweet, like, img_url).

        """
        user = article.find_element(By.CSS_SELECTOR, 'div[data-testid="User-Name"]').text.split('\n')
        name = user[0]
        username = user[1]
        try:
            postdate = article.find_element(By.TAG_NAME, 'time').get_attribute('datetime')
        except:
            postdate = ''
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

    def save_csv(self):
        """
        Saves the collected tweet data to a CSV file.
        """
        columns = ['from', 'username', 'date', 'tweet', 'reply', 'retweet', 'like', 'img_url']
        data_dict = {column: [k[idx] for k in self.data] for idx, column in enumerate(columns)}

        dataframe = pd.DataFrame(data_dict)
        dataframe.to_csv(f'{self.key}.csv')

        self.stop_driver()


