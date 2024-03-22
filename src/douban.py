from moudle import BriefCommentDouban
from moudle.BriefCommentDouban import Comment
import yaml
import argparse


def parse_cookies(cookie_str):
    """将cookie字符串解析为字典"""
    cookies = {}
    for pair in cookie_str.split('; '):  # Cookie通常由"; "分隔
        if '=' in pair:
            key, value = pair.split('=', 1)  # 只分割第一个'='
            cookies[key] = value
    return cookies


def update_yaml(cookies, filepath='doubanConfig.yaml'):
    """更新YAML配置文件中的cookies"""
    with open(filepath, 'r') as file:
        config = yaml.safe_load(file) or {}

    # 更新cookies
    config['cookies'] = cookies

    # 写回文件
    with open(filepath, 'w') as file:
        yaml.safe_dump(config, file, default_flow_style=False)


def initialize():
    # 读取YAML配置文件
    with open('doubanConfig.yaml', 'r') as file:
        config = yaml.safe_load(file)
    # 将cookie键值对组装成字符串
    cookie_str = '; '.join([f'{key}={value}' for key, value in config['cookies'].items()])
    browser_type = config['browser']['browser_type']
    headless = config['browser']['headless']
    comment = Comment(cookie_str, headless=headless, browser_type=browser_type)
    return comment


if __name__ == '__main__':
    # 创建 ArgumentParser 对象
    parser = argparse.ArgumentParser(description='Process some arguments.')
    # 添加 '--link' 命令行参数
    parser.add_argument('--link', type=str, help='Link to process')
    # 添加 '--name' 命令行参数
    parser.add_argument('--name', type=str, help='Name to process')
    # 添加 'class' 命令行参数
    parser.add_argument('--c', type=str, help='Class to process')
    # 更新 'cookie' 命令行参数
    parser.add_argument('--cookie', type=str, help='Cookie to process')
    # 解析命令行参数
    args = parser.parse_args()

    # 使用解析出的参数
    if args.link:
        print(f"Received link: {args.link}")
        comment = initialize()
        comment.getBriefComment(link=args.link)

    if args.name and args.c:
        print(f"Received name: {args.name}")
        comment = initialize()
        comment.getBriefComment(args.c, name=args.name)

    if args.cookie:
        cookies = parse_cookies(args.cookie)
        update_yaml(cookies)
        print("Cookie updated successfully.")
