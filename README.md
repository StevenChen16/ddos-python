# Website Stress Testing Tool

This tool performs a stress test on a specified domain by sending multiple requests to it. The tool can retrieve subdomains, dynamically manage threads based on system load, and provide a detailed analysis of response times, failures, and data sizes.

## Features

- Multi-threaded request generation
- Dynamic thread management based on CPU usage
- Visualization of failures, data size, and response times
- Subdomain fetching using `Sublist3r`
- User-Agent rotation from a file
- Progress bar and live dashboard showing active threads and request rate

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo-url
    cd your-repo-url
    ```

2. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Create a `user_agents.txt` file and add User-Agent strings to it (one per line).

## Usage

```bash
python your_script.py --domain example.com --duration 300 --threads 500 --ua-file user_agents.txt
