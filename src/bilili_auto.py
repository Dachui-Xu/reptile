import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import datetime

# 初始化Selenium WebDriver
options = webdriver.EdgeOptions()
options.add_argument('--headless')  # 无头模式，不显示浏览器界面
options.add_argument('--disable-gpu')  # 禁用GPU加速
driver = webdriver.Edge(options=options)

# 访问B站热门视频页面
driver.get('https://www.bilibili.com/v/popular/all')

# 等待页面加载完成
time.sleep(5)  # 根据实际情况调整等待时间

# 加载50个视频
target_count = 50

videos = []
while len(videos) < target_count:
    # 模拟向下滚动页面
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    # 等待内容加载
    time.sleep(3)  # 根据实际情况调整等待时间

    # 解析页面元素，获取视频标题和链接
    videos = driver.find_elements(By.CLASS_NAME, 'video-card')
    print(f"已加载 {len(videos)} 个视频")  # 输出当前加载的视频数量


# 对获取的视频进行处理，只保留目标数量的视频信息
videos = videos[:target_count]
hot_video = []

for video in videos:
    title = video.find_element(By.CLASS_NAME, 'video-card__info')
    title = title.find_element(By.CLASS_NAME, 'video-name').text
    a = video.find_element(By.CLASS_NAME, 'video-card__content')
    link = a.find_element(By.TAG_NAME, 'a').get_attribute('href')
    hot_video.append({'title': title, 'link': link})

for item in hot_video:
    print(item)

hot_video_df = pd.DataFrame(hot_video)
# 获取当前日期和时间
now = datetime.datetime.now()
formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")  # 格式化日期和时间
hot_video_df.to_excel(f'../result/bili_hot_video_{formatted_date}.xlsx', index=False,  engine='openpyxl')

# 关闭WebDriver
driver.quit()
