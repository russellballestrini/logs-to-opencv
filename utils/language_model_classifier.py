#!/usr/bin/env python3
"""
Unified Language Model Log Classifier

Combines all log analysis modes using the Hermes language model:
- SPAM/HAM classification
- Detailed security analysis with explanations
- Anomaly detection and reporting
"""

import os
import sys
import glob
import json
import argparse
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from openai import OpenAI

# Initialize OpenAI client for UncloseAI's Hermes model
client = OpenAI(
    base_url="https://hermes.ai.unturf.com/v1",
    api_key="dummy"  # UncloseAI doesn't require a real API key
)

MODEL = "adamo1139/Hermes-3-Llama-3.1-8B-FP8-Dynamic"

# Analysis prompts for different modes
SPAM_HAM_PROMPT = """You are a cybersecurity expert. Analyze the HTTP request and classify as SPAM or HAM.

CRITICAL: These patterns are ALWAYS SPAM regardless of other factors:
1. Scanner tools in User-Agent: masscan, nmap, nikto, sqlmap, dirb, gobuster
2. SQL injection: single quotes in URLs, double dashes, UNION, OR 1=1
3. Path traversal: paths containing aws, config, passwd, env, git
4. Buffer overflow: numeric sequences 10+ digits long
5. Code injection: curly braces with variables, dollar expressions
6. Method mismatches: POST to paths ending with numbers, OPTIONS method

Check the URL path carefully - if it's POST to something/NUMBER, it's SPAM.

HTTP Request Log:
[LOG_CONTENT]

Respond with ONLY one word: SPAM or HAM"""

DETAILED_PROMPT = """You are a cybersecurity expert. Analyze the HTTP request and classify as SPAM or HAM.

CRITICAL: These patterns are ALWAYS SPAM regardless of other factors:
1. Scanner tools in User-Agent: masscan, nmap, nikto, sqlmap, dirb, gobuster
2. SQL injection: single quotes in URLs, double dashes, UNION, OR 1=1
3. Path traversal: paths containing aws, config, passwd, env, git
4. Buffer overflow: numeric sequences 10+ digits long
5. Code injection: curly braces with variables, dollar expressions
6. Method mismatches: POST to paths ending with numbers, OPTIONS method

Check the URL path carefully - if it's POST to something/NUMBER, it's SPAM.

HTTP Request Log:
[LOG_CONTENT]

Format your response as:
EXPLANATION: [Exactly 3 sentences explaining your decision, the specific pattern observed, and potential impact]
CLASSIFICATION: [SPAM or HAM]"""

CONFIDENCE_PROMPT = """You are a cybersecurity expert analyzing HTTP request logs to identify potentially abusive or anomalous traffic patterns.

Analyze the following HTTP request log and classify it as either:
1. NORMAL - Typical, legitimate web traffic
2. SUSPICIOUS - Potentially malicious or abusive traffic

HTTP Request Log:
[LOG_CONTENT]

Provide your classification and a brief explanation (max 2 sentences) for your decision.
Format your response as JSON:
{
    "classification": "NORMAL" or "SUSPICIOUS",
    "confidence": 0.0 to 1.0,
    "reason": "Brief explanation"
}"""


class UnifiedLogClassifier:
    def __init__(self):
        self.client = client
        self.model = MODEL
        self.known_anomalies = [151, 158, 208, 323, 363, 457, 511, 517, 551, 978]
    
    def read_log_file(self, filepath: str) -> Optional[str]:
        """Read and return the contents of a log file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None
    
    def classify_spam_ham(self, log_content: str, filename: str) -> str:
        """Classify a log as SPAM or HAM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert. Respond with only SPAM or HAM."},
                    {"role": "user", "content": SPAM_HAM_PROMPT.replace("[LOG_CONTENT]", log_content)}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().upper()
            return result if result in ["SPAM", "HAM"] else "ERROR"
            
        except Exception as e:
            print(f"API error for {filename}: {e}")
            return "ERROR"
    
    def analyze_detailed(self, log_content: str, filename: str) -> Dict:
        """Provide detailed analysis with 3-sentence explanation."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing web traffic. Always provide exactly 3 sentences of explanation."},
                    {"role": "user", "content": DETAILED_PROMPT.replace("[LOG_CONTENT]", log_content)}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract classification and explanation
            lines = result_text.split('\n')
            classification = "UNKNOWN"
            explanation = ""
            
            for line in lines:
                if line.startswith("EXPLANATION:"):
                    explanation = line.replace("EXPLANATION:", "").strip()
                elif line.startswith("CLASSIFICATION:"):
                    classification = line.replace("CLASSIFICATION:", "").strip()
            
            return {
                "filename": filename,
                "classification": classification,
                "explanation": explanation,
                "raw_response": result_text
            }
            
        except Exception as e:
            return {
                "filename": filename,
                "classification": "ERROR",
                "explanation": f"API error: {str(e)}",
                "raw_response": None
            }
    
    def analyze_with_confidence(self, log_content: str, filename: str) -> Dict:
        """Analyze with confidence score and reason."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert specializing in log analysis."},
                    {"role": "user", "content": CONFIDENCE_PROMPT.replace("[LOG_CONTENT]", log_content)}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                result = json.loads(result_text)
                result['filename'] = filename
                result['raw_response'] = result_text
                return result
            except json.JSONDecodeError:
                return {
                    'filename': filename,
                    'classification': 'ERROR',
                    'confidence': 0.0,
                    'reason': 'Failed to parse model response',
                    'raw_response': result_text
                }
                
        except Exception as e:
            return {
                'filename': filename,
                'classification': 'ERROR',
                'confidence': 0.0,
                'reason': f'API error: {str(e)}',
                'raw_response': None
            }
    
    def batch_classify_spam_ham(self, log_directory: str, limit: Optional[int] = None) -> Dict[str, List[str]]:
        """Batch classify logs as SPAM or HAM."""
        log_pattern = os.path.join(log_directory, "*.log")
        log_files = sorted(glob.glob(log_pattern))
        
        if limit:
            log_files = log_files[:limit]
        
        print(f"Found {len(log_files)} log files to classify")
        
        results = {"SPAM": [], "HAM": [], "ERROR": []}
        
        for i, log_file in enumerate(log_files):
            log_basename = os.path.basename(log_file)
            log_content = self.read_log_file(log_file)
            if log_content:
                classification = self.classify_spam_ham(log_content, log_basename)
                results[classification].append(log_basename)
                print(f"Log {i+1}/{len(log_files)}: {log_basename} -> {classification}")
                
                time.sleep(0.3)  # Rate limiting
        
        print()
        return results
    
    def analyze_anomalies(self, mode: str = "detailed") -> List[Dict]:
        """Analyze known anomalies with specified mode."""
        log_files = []
        
        # Find log files for known anomalies
        for anomaly_num in self.known_anomalies:
            pattern = f"logs/{anomaly_num:06d}_request*.log"
            matches = glob.glob(pattern)
            if matches:
                log_files.extend(matches)
        
        print(f"Found {len(log_files)} anomaly log files to analyze")
        
        results = []
        for i, log_file in enumerate(sorted(log_files)):
            print(f"\rAnalyzing anomaly {i+1}/{len(log_files)}", end='', flush=True)
            
            log_content = self.read_log_file(log_file)
            if log_content:
                if mode == "spam_ham":
                    classification = self.classify_spam_ham(log_content, os.path.basename(log_file))
                    results.append({
                        "filename": os.path.basename(log_file),
                        "classification": classification
                    })
                elif mode == "detailed":
                    result = self.analyze_detailed(log_content, os.path.basename(log_file))
                    results.append(result)
                elif mode == "confidence":
                    result = self.analyze_with_confidence(log_content, os.path.basename(log_file))
                    results.append(result)
                
                time.sleep(0.5 if mode == "spam_ham" else 1.0)
        
        print()
        return results
    
    def check_anomaly_detection(self, spam_ham_results: Dict[str, List[str]]):
        """Check if known anomalies were detected as SPAM."""
        print("\n" + "="*60)
        print("ANOMALY DETECTION CHECK")
        print("="*60)
        
        detected = 0
        missed = []
        
        for anomaly_num in self.known_anomalies:
            pattern = f"{anomaly_num:06d}_request"
            found_as_spam = False
            
            for spam_file in spam_ham_results["SPAM"]:
                if pattern in spam_file:
                    found_as_spam = True
                    break
            
            if found_as_spam:
                detected += 1
                print(f"✓ Request #{anomaly_num}: DETECTED as SPAM")
            else:
                for ham_file in spam_ham_results["HAM"]:
                    if pattern in ham_file:
                        missed.append(anomaly_num)
                        print(f"✗ Request #{anomaly_num}: MISSED (classified as HAM)")
                        break
        
        print(f"\nDetection rate: {detected}/{len(self.known_anomalies)} ({detected/len(self.known_anomalies)*100:.1f}%)")
        
        if missed:
            print(f"Missed anomalies: {missed}")


def main():
    parser = argparse.ArgumentParser(
        description="Unified language model classifier for HTTP request logs"
    )
    parser.add_argument(
        'mode',
        choices=['spam_ham', 'detailed', 'confidence', 'anomalies'],
        help='Analysis mode to use'
    )
    parser.add_argument(
        '-d', '--directory',
        default='logs',
        help='Directory containing log files (default: logs)'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        help='Limit number of logs to analyze'
    )
    parser.add_argument(
        '-s', '--single',
        help='Analyze a single log file'
    )
    parser.add_argument(
        '--check-detection',
        action='store_true',
        help='Check anomaly detection rate (for spam_ham mode)'
    )
    
    args = parser.parse_args()
    
    classifier = UnifiedLogClassifier()
    
    if args.single:
        # Analyze single file
        log_content = classifier.read_log_file(args.single)
        if log_content:
            filename = os.path.basename(args.single)
            
            if args.mode == 'spam_ham':
                result = classifier.classify_spam_ham(log_content, filename)
                print(f"Classification: {result}")
            elif args.mode == 'detailed':
                result = classifier.analyze_detailed(log_content, filename)
                print(f"Classification: {result['classification']}")
                print(f"Explanation: {result['explanation']}")
            elif args.mode == 'confidence':
                result = classifier.analyze_with_confidence(log_content, filename)
                print(json.dumps(result, indent=2))
    
    elif args.mode == 'anomalies':
        # Analyze known anomalies
        results = classifier.analyze_anomalies("detailed")
        
        print("\n" + "="*80)
        print("DETAILED ANOMALY ANALYSIS")
        print("="*80)
        
        for result in results:
            request_num = result['filename'].split('_')[0]
            print(f"\nRequest #{int(request_num)}:")
            print(f"Classification: {result['classification']}")
            print(f"Explanation: {result['explanation']}")
            print("-"*80)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"anomaly_scores/unified_anomaly_analysis_{timestamp}.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")
    
    else:
        # Batch analysis
        if args.mode == 'spam_ham':
            results = classifier.batch_classify_spam_ham(args.directory, args.limit)
            
            # Print summary
            total = len(results["SPAM"]) + len(results["HAM"]) + len(results["ERROR"])
            print(f"\nClassification Results:")
            print(f"SPAM: {len(results['SPAM'])} ({len(results['SPAM'])/total*100:.1f}%)")
            print(f"HAM: {len(results['HAM'])} ({len(results['HAM'])/total*100:.1f}%)")
            print(f"ERROR: {len(results['ERROR'])} ({len(results['ERROR'])/total*100:.1f}%)")
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"anomaly_scores/unified_spam_ham_{timestamp}.json"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\nResults saved to: {output_file}")
            
            # Check anomaly detection if requested
            if args.check_detection:
                classifier.check_anomaly_detection(results)


if __name__ == "__main__":
    main()