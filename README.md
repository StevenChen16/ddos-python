#### 项目简介

这是一个网站压力测试工具，用于模拟大量并发请求，测试目标网站的承载能力。该工具支持以下功能：

- **子域名抓取**：使用 Sublist3r 获取目标域名的子域名，并将其加入测试。
- **多线程请求**：使用指定的 HTTP 方法对目标网站发送请求，支持 GET、POST、DELETE。
- **代理支持**：可以通过代理发送请求，支持 SOCKS4、SOCKS5 和 HTTP 代理。
- **大文件上传**：支持通过 POST 方法上传大文件，以测试服务器的上传能力。
- **乱码数据发送**：可以发送随机生成的乱码数据，模拟多种数据传输场景。
- **动态线程管理**：根据 CPU 使用情况自动调整线程数量，避免系统过载。

#### 安装步骤

1. 克隆该项目到本地：

```bash
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository
```

2. 安装所需的 Python 库：

```bash
pip install -r requirements.txt
```

3. 创建一个 `user_agents.txt` 文件，填入不同的 User-Agent，每行一个，例如：

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36
```

#### 使用说明

使用该工具时，需要通过命令行参数进行配置：

```bash
python yourscript.py --domain example.com --duration 3600 --threads 100 --interval 0.2 --ua-file user_agents.txt --tolerance 5 --methods GET POST --garbled-text-len 500 --file-count 3 --file-size 100 --regenerate-files --proxy-file proxies.txt --proxy-type SOCKS5
```

#### 参数说明

- `--domain`：要测试的域名，必填项。
- `--duration`：压力测试持续时间，单位为秒，默认值为 2400 秒。
- `--threads`：线程数（即并发请求的数量），默认 1000 个线程。
- `--interval`：每个请求之间的间隔时间，单位为秒，默认 0.1 秒。
- `--ua-file`：存放 User-Agent 列表的文件路径，默认值为 `user_agents.txt`。
- `--tolerance`：检查域名可访问性时的最大重试次数，默认值为 5 次。
- `--skip-check`：跳过域名访问检查，若使用此参数，则不会进行域名可访问性检测。
- `--methods`：HTTP 请求方法列表，支持 GET、POST、DELETE，默认为 `GET`。
- `--garbled-text-len`：生成的乱码文本长度，在 POST 或 DELETE 请求时作为请求体。
- `--file-count`：生成或加载的大文件数量，用于模拟大文件上传。
- `--file-size`：每个文件的大小，单位为 MB，默认值为 100MB。
- `--regenerate-files`：是否重新生成大文件，若不指定此参数，则从缓存加载已生成的文件。
- `--proxy-file`：包含代理列表的文件路径，代理应以 `IP:PORT` 格式列出。
- `--proxy-type`：代理类型，支持 SOCKS4、SOCKS5 和 HTTP，默认为 `SOCKS5`。

#### 示例

##### 基本用法

```bash
python yourscript.py --domain example.com --duration 1200 --threads 500 --ua-file user_agents.txt
```

##### 使用代理

```bash
python yourscript.py --domain example.com --proxy-file proxies.txt --proxy-type HTTP
```

##### 使用大文件上传

```bash
python yourscript.py --domain example.com --file-count 5 --file-size 200 --regenerate-files
```

##### 发送乱码请求

```bash
python yourscript.py --domain example.com --garbled-text-len 1000 --methods POST DELETE
```

#### 注意事项

1. **日志文件**：所有的请求日志将会保存在 `request_logs.log` 文件中，包括每个请求的时间戳、URL、方法、响应时间和数据大小等信息。
2. **安全退出**：在运行过程中，可以使用 `Ctrl + C` 终止程序，程序会捕捉中断信号并安全退出。
3. **代理验证**：若提供了代理列表，程序会并行验证代理的可用性，并仅使用有效的代理进行请求。

#### 贡献

欢迎提交 issue 或者 pull request，以帮助改进该项目。

#### 许可证

该项目遵循 MIT 许可证。