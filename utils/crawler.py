import requests
import time
import random


def crawl():
    base_url = "http://localhost:6543"
    endpoints = ["/", "/hello"]

    # Normal user agent for 99 requests
    normal_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

    # Different user agent for 1 request
    different_user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36"

    # Randomly select which request will have the different user agent
    different_request_num = random.randint(1, 100)

    print(f"Will use different user agent on request #{different_request_num}")

    for i in range(1, 101):
        # 66% chance for home ("/"), 33% chance for hello ("/hello")
        if random.random() < 0.66:
            endpoint = "/"
        else:
            endpoint = "/hello"
        url = base_url + endpoint

        # Use different user agent for the randomly selected request
        if i == different_request_num:
            headers = {"User-Agent": different_user_agent}
            print(
                f"Request #{i}: Using DIFFERENT user agent (Ubuntu/Chrome 95) on {endpoint}"
            )
        else:
            headers = {"User-Agent": normal_user_agent}

        try:
            response = requests.get(url, headers=headers)
            print(f"Request #{i}: {url} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request #{i}: Failed - {e}")

        # Variable delay between requests (50-150ms)
        time.sleep(random.uniform(0.05, 0.15))


if __name__ == "__main__":
    print("Starting crawler v2...")
    print("Make sure the Pyramid app is running on http://localhost:6543")
    print("This version uses more varied user agents")
    time.sleep(2)
    crawl()
    print("Crawler v2 finished!")
