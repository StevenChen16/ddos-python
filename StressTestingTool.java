import org.apache.commons.cli.*;
import org.apache.http.HttpResponse;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.util.EntityUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;

import java.io.IOException;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class StressTestingTool {
    private static final Logger logger = LogManager.getLogger(StressTestingTool.class);
    private static boolean threadsRunning = true;
    private static int activeThreads = 0;
    private static int requestsLastSecond = 0;
    private static long bytesSent = 0;

    public static void main(String[] args) throws Exception {
        // 创建命令行参数解析器
        Options options = new Options();

        options.addOption("domain", true, "The domain to test.");
        options.addOption("duration", true, "Test duration in seconds.");
        options.addOption("threads", true, "Number of threads.");
        options.addOption("interval", true, "Request interval in seconds.");
        options.addOption("ua-file", true, "Path to User-Agent list file.");
        options.addOption("tolerance", true, "Maximum retries for domain check.");
        options.addOption("skip-check", false, "Skip domain accessibility check.");
        options.addOption("methods", true, "HTTP methods to use (GET, POST, DELETE).");
        options.addOption("garbled-text-len", true, "Length of random garbled text to send in requests.");
        options.addOption("file-count", true, "Number of large files to generate or load.");
        options.addOption("file-size", true, "Size of each file in MB.");
        options.addOption("regenerate-files", false, "Regenerate files instead of caching them.");
        options.addOption("proxy-file", true, "Path to proxy list file.");
        options.addOption("proxy-type", true, "Type of proxies to use (SOCKS4, SOCKS5, HTTP).");
        options.addOption("proxy-threads", true, "Number of threads for validating proxies.");
        options.addOption("max-depth", true, "Maximum depth for crawling links.");
        options.addOption("recursive-link-search", false, "Recursive link search");

        // 解析命令行参数
        CommandLineParser parser = new DefaultParser();
        CommandLine cmd = parser.parse(options, args);

        // 从命令行参数获取值
        String domain = cmd.getOptionValue("domain");
        int threadCount = Integer.parseInt(cmd.getOptionValue("threads", "1000"));
        int testDuration = Integer.parseInt(cmd.getOptionValue("duration", "2400"));
        double requestInterval = Double.parseDouble(cmd.getOptionValue("interval", "0.1"));
        int maxDepth = Integer.parseInt(cmd.getOptionValue("max-depth", "2"));
        String uaFilePath = cmd.getOptionValue("ua-file", "user_agents.txt");

        List<String> headersList = loadUserAgents(uaFilePath);

        // 检查域名可访问性
        if (!cmd.hasOption("skip-check")) {
            checkDomainAccessibility(domain);
        }

        // 获取子域名和 URL
        Set<String> urls = getAllWebsiteLinks("https://" + domain, maxDepth);
        System.out.println("Valid URLs found: " + urls.size());

        // 初始化线程池
        ExecutorService executorService = Executors.newFixedThreadPool(threadCount);

        // 启动测试线程
        for (String url : urls) {
            executorService.execute(() -> performRequests(url, headersList, requestInterval));
        }

        // 等待测试时间结束
        TimeUnit.SECONDS.sleep(testDuration);
        threadsRunning = false;

        // 停止线程池
        executorService.shutdown();
        if (!executorService.awaitTermination(60, TimeUnit.SECONDS)) {
            executorService.shutdownNow();
        }

        // 分析和记录结果
        analyzeResults(urls);
    }

    // 读取 User-Agent 列表
    public static List<String> loadUserAgents(String filename) throws IOException {
        return Files.readAllLines(Paths.get(filename), StandardCharsets.UTF_8);
    }

    // 检查域名是否可访问
    public static void checkDomainAccessibility(String domain) {
        try {
            HttpURLConnection connection = (HttpURLConnection) new URL("https://" + domain).openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(5000);
            connection.setReadTimeout(5000);

            int status = connection.getResponseCode();
            if (status == 200) {
                System.out.println("域名 " + domain + " 可访问");
            } else {
                System.out.println("域名 " + domain + " 访问失败，状态码：" + status);
            }
        } catch (IOException e) {
            logger.error("访问域名时出错: " + e.getMessage());
        }
    }

    // 获取所有链接
    public static Set<String> getAllWebsiteLinks(String url, int depth) {
        Set<String> links = new HashSet<>();
        if (depth <= 0) return links;

        try (CloseableHttpClient httpClient = HttpClients.createDefault()) {
            HttpGet request = new HttpGet(url);
            try (CloseableHttpResponse response = httpClient.execute(request)) {
                String html = EntityUtils.toString(response.getEntity(), StandardCharsets.UTF_8);
                Document doc = Jsoup.parse(html);
                Elements aTags = doc.select("a[href]");

                for (var aTag : aTags) {
                    String link = aTag.attr("abs:href");
                    // 过滤掉 mailto 链接
                    if (link.startsWith("mailto:")) {
                        continue;  // 跳过 mailto 链接
                    }
                    if (isValidURL(link)) {
                        links.add(link);
                    }
                }
            }
        } catch (IOException e) {
            logger.error("获取链接时出错: " + e.getMessage());
        }

        // 递归处理子链接
        Set<String> moreLinks = new HashSet<>();
        for (String link : links) {
            moreLinks.addAll(getAllWebsiteLinks(link, depth - 1));
        }
        links.addAll(moreLinks);

        return links;
    }

    // 验证 URL 是否有效
    public static boolean isValidURL(String url) {
        try {
            new URL(url).toURI();
            return true;
        } catch (URISyntaxException | MalformedURLException e) {
            return false;
        }
    }

    // 执行 HTTP 请求
    public static void performRequests(String url, List<String> headersList, double requestInterval) {
        while (threadsRunning) {
            try (CloseableHttpClient httpClient = HttpClients.createDefault()) {
                HttpGet request = new HttpGet(url);
                String userAgent = headersList.get(new Random().nextInt(headersList.size()));
                request.setHeader("User-Agent", userAgent);

                long startTime = System.currentTimeMillis();
                try (CloseableHttpResponse response = httpClient.execute(request)) {
                    int statusCode = response.getStatusLine().getStatusCode();
                    long elapsedTime = System.currentTimeMillis() - startTime;
                    long dataSize = response.getEntity().getContentLength();
                    
                    logger.info("URL: " + url + ", Status: " + statusCode + ", Time: " + elapsedTime + "ms, Size: " + dataSize + " bytes");

                    synchronized (StressTestingTool.class) {
                        requestsLastSecond++;
                        bytesSent += dataSize;
                    }
                }
            } catch (IOException e) {
                logger.error("请求失败: " + e.getMessage());
            }

            try {
                TimeUnit.MILLISECONDS.sleep((long) (requestInterval * 1000));
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        synchronized (StressTestingTool.class) {
            activeThreads--;
        }
    }

    // 分析和输出结果
    public static void analyzeResults(Set<String> urls) {
        System.out.println("Total requests: " + requestsLastSecond);
        System.out.println("Total data sent: " + bytesSent + " bytes");
    }
}
