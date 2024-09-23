import argparse
import requests
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
    logging.info(f"URL: {result['url']}, Status: {result['status_code']}, "
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
    global active_threads, requests_last_second
    with tqdm(total=test_duration, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]') as pbar:
        while threads_running:
            elapsed_time = time.time() - start_time
            progress = elapsed_time / test_duration
            pbar.n = int(progress * test_duration)
            pbar.set_postfix({
                'Active Threads': active_threads,
                'Requests/s': requests_last_second,
                'Upload': f"{net_speed()[0]:.2f}KB/s",
                'Download': f"{net_speed()[1]:.2f}KB/s"
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

# 执行请求
def perform_requests(urls, headers_list, request_interval):
    global active_threads, requests_last_second
    with lock:
        active_threads += 1
    try:
        while threads_running:
            url = random.choice(urls)
            headers = random.choice(headers_list)
            start_time = datetime.now()
            
            # 生成乱码数据并发送请求
            garbled_text = generate_garbled_text(160)
            response = requests.post(url, headers=headers, data=garbled_text, verify=False)

            # 请求完成，记录时间和数据大小
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            data_size = len(response.content)
                
            with lock:
                result = {
                    "timestamp": start_time,
                    "url": url,
                    "response_time": elapsed_time,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "data_size": data_size
                }
                results.append(result)
                requests_last_second += 1
                log_request_details(result)

            time.sleep(request_interval)
    finally:
        with lock:
            active_threads -= 1

# 结果分析并可视化
def analyze_results(urls):
    url_stats = {url: {"times_requested": 0, "response_times": [], "data_sizes": [], "failures": 0} for url in urls}
    for result in results:
        stats = url_stats[result["url"]]
        stats["times_requested"] += 1
        stats["response_times"].append(result["response_time"])
        stats["data_sizes"].append(result["data_size"])
        if not result["success"]:
            stats["failures"] += 1

    plt.figure(figsize=(len(urls), 8), dpi=800)

    plt.subplot(1, 3, 1)
    plt.bar(range(len(urls)), [stats['failures'] for stats in url_stats.values()], tick_label=list(url_stats.keys()))
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.ylabel('Failures')
    plt.title('Failures by URL')

    plt.subplot(1, 3, 2)
    plt.bar(range(len(urls)), [np.mean(stats['data_sizes']) for stats in url_stats.values()], tick_label=list(url_stats.keys()))
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.ylabel('Average Data Size (bytes)')
    plt.title('Average Data Size by URL')

    plt.subplot(1, 3, 3)
    plt.bar(range(len(urls)), [np.mean(stats['response_times']) for stats in url_stats.values()], tick_label=list(url_stats.keys()))
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.ylabel('Average Response Time (s)')
    plt.title('Average Response Time by URL')

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    plt.savefig(f"{now}.jpg")
    plt.tight_layout()
    plt.show()

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

    args = parser.parse_args()

    global threads_running, active_threads, requests_last_second, results
    global thread_count, test_duration, request_interval, lock

    # 检查域名是否可访问（若未跳过）
    domain_accessible = False
    if not args.skip_check:
        domain_accessible = check_domain_accessibility(args.domain, args.tolerance)
        if domain_accessible:
            print(f"域名 {args.domain} 检查成功，可以访问。")
        else:
            print(f"域名 {args.domain} 检查失败，无法访问。")
    else:
        print(f"跳过域名检查。")

    # 加载 User-Agent 列表
    headers_list = [{"User-Agent": ua} for ua in load_user_agents(args.ua_file)]

    # 获取子域名和 URL
    subdomains = get_subdomains(args.domain)
    all_urls = {"https://" + args.domain} | {"https://" + sub for sub in subdomains}

    print(f"Valid URLs found: {len(all_urls)}")
    urls = list(all_urls)

    # 共享资源初始化
    threads_running = True
    lock = threading.Lock()
    results = []
    requests_last_second = 0
    active_threads = 0

    start_time = time.time()

    # 启动进度条和 Dashboard 线程
    progress_thread = threading.Thread(target=update_progress, args=(start_time, args.duration))
    progress_thread.start()

    # 启动压力测试线程
    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=perform_requests, args=(urls, headers_list, args.interval))
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
