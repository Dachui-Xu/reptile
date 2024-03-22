import requests
from bs4 import BeautifulSoup
import time
import re
import pandas as pd

# 设置用户代理
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

# 豆瓣图书Top250的基础URL
base_url = 'https://book.douban.com/top250?start='

# 存储图书信息
books = []

# 由于每页显示25本书，豆瓣图书Top250有10页
for i in range(0, 10):
    url = f'{base_url}{i * 25}'
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 解析页面中的图书信息
    for item in soup.find_all('tr', class_='item'):
        # 获取书名
        title = item.find('div', class_='pl2').find('a')['title']
        # 获取作者和价格
        info = item.find('p', class_='pl').text.split('/')
        price = info[-1]
        publisher = info[-2]
        autor = ''.join(info[:-3])
        # 获取评分
        rating = item.find('span', class_='rating_nums').text
        # 获取评价人数
        rating_num_text = item.find('span', class_='pl').text
        rating_num = ''.join(re.findall(r'\d+', rating_num_text))
        # 存储这本书的信息
        books.append({'title': title, 'rating': rating, 'rating_num': rating_num, 'autor': autor, 'publisher': publisher,'price': price})

    # 延时，以避免对服务器造成过大压力
    time.sleep(2)  # 休息两秒钟

# 打印或以其他方式存储爬取的数据
# for book in books:
#     print(book)


# 将你的数据转换为pandas DataFrame
books_df = pd.DataFrame(books)

# 将DataFrame存储到Excel文件
books_df.to_excel('../result/douban_books_top250.xlsx', index=False, engine='openpyxl')
