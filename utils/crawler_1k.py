import requests
import time
import random


def crawl():
    base_url = "http://localhost:6543"
    endpoints = ["/", "/hello"]

    # Normal user agent for most requests
    normal_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

    # Different user agents for anomalies (about 1% = 10 requests)
    anomaly_user_agents = [
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "curl/7.68.0",
        "Python-urllib/3.8",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.203",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)",
    ]

    # Randomly select which requests will have different user agents
    total_requests = 1000
    anomaly_count = 10  # 1% of 1000
    anomaly_indices = sorted(random.sample(range(1, total_requests + 1), anomaly_count))

    print(f"Starting crawler for {total_requests} requests...")
    print(f"Will use different user agents on requests: {anomaly_indices}")
    print(f"Normal user agent: {normal_user_agent[:50]}...")
    print()

    start_time = time.time()

    for i in range(1, total_requests + 1):
        # 66% chance for home ("/"), 33% chance for hello ("/hello")
        if random.random() < 0.66:
            endpoint = "/"
        else:
            endpoint = "/hello"
        url = base_url + endpoint

        # Use different user agent for selected anomaly requests
        if i in anomaly_indices:
            anomaly_agent = random.choice(anomaly_user_agents)
            headers = {"User-Agent": anomaly_agent}
            print(f"Request #{i}: Using ANOMALY user agent: {anomaly_agent[:60]}...")
        else:
            headers = {"User-Agent": normal_user_agent}

        try:
            response = requests.get(url, headers=headers)
            if i % 100 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                print(
                    f"Request #{i}: {url} - Status: {response.status_code} ({rate:.1f} req/s)"
                )
        except requests.exceptions.RequestException as e:
            print(f"Request #{i}: Failed - {e}")

        # Shorter delay for 1k requests (10-30ms)
        time.sleep(random.uniform(0.01, 0.03))

    elapsed_time = time.time() - start_time
    print(f"\nCrawler finished!")
    print(f"Total requests: {total_requests}")
    print(f"Total time: {elapsed_time:.2f} seconds")
    print(f"Average rate: {total_requests/elapsed_time:.2f} requests/second")
    print(f"Anomaly requests: {anomaly_count}")


if __name__ == "__main__":
    print("Starting 1K crawler...")
    print("Make sure the Pyramid app is running on http://localhost:6543")
    print("This will generate 1000 requests with 10 anomalies (1%)")
    time.sleep(2)
    crawl()
    print("\n1K crawler finished!")
