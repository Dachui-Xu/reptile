from datetime import datetime

import pandas as pd
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
import requests
from bs4 import BeautifulSoup
import re
from tqdm import tqdm

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}
# 正则匹配
BOOK = r'^[Bb]'
MUSIC = r'^[Mm][Uu]'
MOVIE = r'^[Mm][Oo]'


class Comment:
    def __init__(self, cookie_str, browser_type='Edge', headless=True):
        # 解析cookie字符串
        self.filename = None
        self.limit = 20
        self.cookie_dict = {}
        for cookie in cookie_str.split('; '):
            key, value = cookie.split('=', 1)  # 分割每个cookie字符串
            self.cookie_dict[key] = value
        self.classification = 'movie'
        self.browser_type = browser_type
        self.headless = headless

    def init_driver(self, browser_type, user_agent, headless=True):
        '''
        初始化浏览器
        :param browser_type: 从Chrome, Edge, Firefox和Safari中选择一个
        :param user_agent: 请求头
        :param headless: 默认不显示浏览器
        :return: 浏览器
        '''
        driver = None
        if browser_type == 'Chrome':
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument(f'user-agent={user_agent}')
            driver = webdriver.Chrome(options=options)

        elif browser_type == 'Edge':
            options = webdriver.EdgeOptions()
            if headless:
                options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument(f'user-agent={user_agent}')
            driver = webdriver.Edge(options=options)

        elif browser_type == 'Firefox':
            options = webdriver.FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            options.set_preference('general.useragent.override', user_agent)
            driver = webdriver.Firefox(options=options)

        elif browser_type == 'Safari':
            if headless:
                print("Safari does not support headless mode.")
            driver = webdriver.Safari()

        else:
            raise ValueError("Unsupported browser")

        return driver

    def getBriefComment(self, classified=None, name=None, link=None):
        '''
        获取评论
        :param classified: 分类，book, movie, music
        :param name: 书名/电影名/音乐名
        :param link: 在使用前两个的前提下，直接给出链接
        '''
        if name is None and link is None:
            print('name or link must be given')
            return
        if name is not None and classified is not None:
            base_link = self.search(name, classified)
            self.getComment(base_link)
        if name is not None and classified is None:
            print('Please provide classified')
            return
        if link is not None:
            self.getComment(link)

    def search(self, name, classified):
        if re.compile(BOOK).match(classified):
            classified = 'book'
            self.limit = 20
        elif re.compile(MOVIE).match(classified):
            classified = 'movie'
            self.limit = 120
        elif re.compile(MUSIC).match(classified):
            classified = 'music'
            self.limit = 20
        else:
            raise ValueError(f"Classified must be one of: {BOOK}, {MUSIC}, {MOVIE}")
        self.classification = classified

        driver = self.init_driver(self.browser_type, headers, self.headless)
        driver.set_window_size(1920, 1080)  # 设置浏览器窗口大小

        # 使用格式化字符串构建完整的URL
        url = f"https://search.douban.com/{classified}/subject_search?search_text={name}"
        self.filename = f"[{classified}]{name}"  # 文件名
        driver.get(url)
        time.sleep(3)

        # 找到包含链接的元素
        wrapper = driver.find_element(By.ID, 'wrapper')
        root = wrapper.find_element(By.ID, 'root')
        get_link = root.find_element(By.CLASS_NAME, 'cover-link').get_attribute('href')
        # 完成操作后关闭浏览器
        driver.quit()
        return get_link

    def getComment(self, base_link):
        print(base_link)
        if self.limit == 120:
            # 短评的基础地址
            sort_comment_link = base_link + 'comments?limit=120&start='
        else:
            sort_comment_link = base_link + 'comments?limit=20&start='
        print(sort_comment_link)
        page = self._commentPages(sort_comment_link, self.limit)
        comment = []  # 评论信息
        for i in tqdm(range(page), desc="处理进度"):
            url = f'{sort_comment_link}{i * self.limit}'
            response = requests.get(url, headers=headers, cookies=self.cookie_dict)
            soup = BeautifulSoup(response.text, 'html.parser')
            all_comments = self._comment_item(soup)  # 获取所有评论
            for comment_item in all_comments:
                vote = self._label_a_or_span(comment_item, 'vote-count').text
                comment_info = self._label_a_or_span(comment_item, 'comment-info')
                comment_time = self._label_a_or_span(comment_info, 'comment-time').text.lstrip()
                user_name = comment_info.find('a').text
                score = 0
                if comment_info.find('span').get('class') is not None:
                    score_list = comment_info.find('span')['class']
                else:
                    score_list = comment_info.find_all('span')[1]['class']
                for item in score_list:
                    # 使用正则表达式找到字符串中的数字部分
                    numbers = re.findall(r'\d+', item)
                    if numbers:
                        number = numbers[0]
                        score = float(number) / 10
                        break
                    else:
                        score = ''
                comment_content = comment_item.find('p', class_='comment-content').find('span').text
                comment.append({"time": comment_time, "user_name": user_name, "vote": vote, "score": score,
                                "comment_content": comment_content})
            # 延时，以避免对服务器造成过大压力
            time.sleep(2)  # 休息两秒钟

        print("开始保存为Excel")
        # 将你的数据转换为pandas DataFrame
        comment_df = pd.DataFrame(comment)
        try:
            if self.filename:
                stored_comment = f'../result/{self.filename}.xlsx'
                # 将DataFrame存储到Excel文件
            else:
                # 获取当前日期和时间
                now = datetime.now()
                formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")  # 格式化日期和时间
                stored_comment = f'../result/{formatted_date}.xlsx'
            comment_df.to_excel(stored_comment, index=False, engine='openpyxl')
            print("文件保存为：", stored_comment)
        except Exception as e:
            print("保存失败，发生错误", e)

    def _commentPages(self, sort_comment_link, limit):

        # 利用request爬取评论
        response = requests.get(sort_comment_link, cookies=self.cookie_dict, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 获取已看评论总数
        active_li = soup.find('li', class_='is-active')
        if active_li:  # 确保active_li不是None
            span = active_li.find('span')
            if span:  # 确保找到了span元素
                count_comments_text = span.text
                numbers = re.findall(r'\d+', count_comments_text)
                if numbers:  # 确保找到了数字
                    count_comments = int(numbers[0])
                    print(
                        f"一共有{count_comments}条评论,豆瓣限制图书最多能获取300条评论，电影能获取600条评论，音乐是500条")
                else:
                    count_comments = 600  # 或者设定为合理的默认值
                    print('没有获得评论数目，默认600条')
            else:
                count_comments = 600  # 或者设定为合理的默认值
                print('没有获得评论数目，默认600条')

        else:
            count_comments = 600  # 或者设定为合理的默认值
            print('没有获得评论数目，默认600条')

        if self.classification == 'movie' and count_comments > 600:
            count_comments = 600
        if self.classification == 'book' and count_comments > 300:
            count_comments = 300
        if self.classification == 'music' and count_comments > 500:
            count_comments = 500
        # 计算评论页数
        if count_comments > limit:
            if count_comments % limit == 0:
                page = count_comments // limit
            else:
                page = count_comments // limit + 1
        else:
            page = 1
        return page

    def _label_a_or_span(self, driver, class_):
        # 尝试找到<a>标签的评论时间
        label = driver.find('span', class_=class_)
        # 如果<a>标签不存在，则尝试找到<span>标签的评论时间
        if not label:
            label = driver.find('a', class_=class_)
        return label

    def _comment_item(self, soup):
        # 初始化一个空列表来收集所有评论项
        all_comment_items = []

        # 首先尝试找到所有 'div' 标签的评论项
        div_comment_items = soup.find_all('div', class_='comment-item')
        if div_comment_items:
            all_comment_items.extend(div_comment_items)

        # 然后尝试找到所有 'li' 标签的评论项
        li_comment_items = soup.find_all('li', class_='comment-item')
        if li_comment_items:
            all_comment_items.extend(li_comment_items)
        return all_comment_items
