# ---[ Fixer Agent Module ]---
"""
The Fixer Agent monitors the main Learning Agent's results, analyzes failures,
and proposes improvements to strategies, parameters, and code.

This creates a 2-agent system where:
- Main Agent: Does scraping, records results, adapts strategies
- Fixer Agent: Monitors, analyzes, and proposes improvements
"""

import os
import sys
import json
import time
import threading
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse
from collections import defaultdict, Counter
from io import BytesIO
from bs4 import BeautifulSoup
import re

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

# Import environment variables
from config.config import load_env_file, OPENAI_API_KEY, ANTHROPIC_API_KEY

# AI imports for intelligent analysis
try:
    from openai import OpenAI
    import anthropic
    AI_ENABLED = True
    print("🤖 AI capabilities enabled for fixer agent")
except ImportError as e:
    print(f"⚠️ AI capabilities disabled for fixer agent: {e}")
    AI_ENABLED = False

# AI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Initialize OpenAI client if key is available
openai_client = None
if AI_ENABLED and OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
if AI_ENABLED and ANTHROPIC_API_KEY:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class FixerAgent:
    """Intelligent agent that analyzes failures and proposes improvements"""
    
    def __init__(self, knowledge_file="knowledge_base.json", fixer_log="fixer_agent.log"):
        """Initialize the fixer agent with knowledge base and monitoring capabilities"""
        self.knowledge_file = knowledge_file
        self.fixer_log = fixer_log
        self.monitoring = False
        self.monitor_thread = None
        
        # Load environment variables
        load_env_file()
        
        # AI configuration
        self.AI_ENABLED = bool(OPENAI_API_KEY or ANTHROPIC_API_KEY)
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
        
        # Initialize AI clients
        if self.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=self.OPENAI_API_KEY)
        if self.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=self.ANTHROPIC_API_KEY)
        
        # Analysis data structures
        self.failure_patterns = {}
        self.success_trends = {}
        self.critical_failures = []
        self.strategy_recommendations = {}
        self.improvement_suggestions = []
        
        # Rate limiting to prevent token limit issues
        self.last_ai_analysis = 0
        self.ai_analysis_cooldown = 300  # 5 minutes between AI analyses
        
        print(f"🔧 Fixer Agent initialized - AI: {'Enabled' if self.AI_ENABLED else 'Disabled'}")
    
    def start_monitoring(self):
        """Start the fixer agent monitoring loop"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.start()
        print("🔧 Fixer Agent started - monitoring for issues...")
    
    def stop_monitoring(self):
        """Stop the fixer agent monitoring loop"""
        self.monitoring = False
        try:
            if hasattr(self, 'monitor_thread') and self.monitor_thread is not None and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
        except Exception as e:
            print(f"⚠️ Fixer monitor thread join error: {e}")
        print("🔧 Fixer Agent stopped")
    
    def analyze_knowledge_base(self):
        """Analyze the main agent's knowledge base for patterns and issues"""
        try:
            if not os.path.exists(self.knowledge_file):
                return
            
            with open(self.knowledge_file, 'r') as f:
                knowledge = json.load(f)
            
            current_time = datetime.utcnow()
            self.last_analysis_time = current_time
            
            # Analyze failure patterns
            self.analyze_failure_patterns(knowledge)
            
            # Analyze success trends
            self.analyze_success_trends(knowledge)
            
            # Identify critical issues
            self.identify_critical_issues(knowledge)
            
            # Analyze strategy performance
            self.analyze_strategy_performance(knowledge)
            
            print(f"🔧 Analysis completed at {current_time}")
            
        except Exception as e:
            print(f"⚠️ Knowledge base analysis failed: {e}")
    
    def analyze_failure_patterns(self, knowledge):
        """Analyze patterns in failures to identify root causes"""
        try:
            failure_patterns = knowledge.get('failure_patterns', {})
            
            # Group failures by domain and stage
            domain_stage_failures = defaultdict(lambda: defaultdict(list))
            error_type_counts = Counter()
            
            for error_type, failures in failure_patterns.items():
                error_type_counts[error_type] = len(failures)
                
                for failure in failures:
                    domain = failure.get('url_pattern', {}).get('domain', 'unknown')
                    stage = failure.get('stage', 'extracted_address')
                    domain_stage_failures[domain][stage].append(failure)
            
            # Identify problematic domains and stages
            problematic_domains = []
            for domain, stage_failures in domain_stage_failures.items():
                total_failures = sum(len(failures) for failures in stage_failures.values())
                if total_failures >= 3:  # Threshold for problematic
                    problematic_domains.append({
                        'domain': domain,
                        'total_failures': total_failures,
                        'stage_breakdown': {stage: len(failures) for stage, failures in stage_failures.items()},
                        'most_common_error': max(error_type_counts.items(), key=lambda x: x[1])[0] if error_type_counts else 'unknown'
                    })
            
            self.failure_patterns = {
                'error_type_counts': dict(error_type_counts),
                'problematic_domains': problematic_domains,
                'domain_stage_failures': dict(domain_stage_failures)
            }
            
        except Exception as e:
            print(f"⚠️ Failure pattern analysis failed: {e}")
    
    def analyze_success_trends(self, knowledge):
        """Analyze success trends to identify improving/declining patterns"""
        try:
            site_patterns = knowledge.get('site_patterns', {})
            strategy_success_rates = knowledge.get('strategy_success_rates', {})
            
            # Analyze recent vs historical success rates
            current_time = datetime.utcnow()
            recent_threshold = current_time - timedelta(hours=24)
            
            recent_successes = 0
            historical_successes = 0
            
            for domain, patterns in site_patterns.items():
                for pattern in patterns:
                    success_time = datetime.fromisoformat(pattern['timestamp'])
                    if success_time > recent_threshold:
                        recent_successes += 1
                    else:
                        historical_successes += 1
            
            # Calculate trend
            if historical_successes > 0:
                trend = (recent_successes - historical_successes) / historical_successes
            else:
                trend = 0
            
            self.success_trends = {
                'recent_successes': recent_successes,
                'historical_successes': historical_successes,
                'trend': trend,
                'trend_direction': 'improving' if trend > 0.1 else 'declining' if trend < -0.1 else 'stable'
            }
            
        except Exception as e:
            print(f"⚠️ Success trend analysis failed: {e}")
    
    def identify_critical_issues(self, knowledge):
        """Identify critical issues that need immediate attention"""
        try:
            critical_issues = []
            
            # Check for high failure rates
            failure_patterns = knowledge.get('failure_patterns', {})
            total_failures = sum(len(failures) for failures in failure_patterns.values())
            
            if total_failures > 10:
                critical_issues.append({
                    'type': 'high_failure_rate',
                    'severity': 'high',
                    'description': f'High failure rate detected: {total_failures} failures',
                    'recommendation': 'Review and improve error handling strategies'
                })
            
            # Check for domain-specific issues
            for domain_info in self.failure_patterns.get('problematic_domains', []):
                if domain_info['total_failures'] > 5:
                    critical_issues.append({
                        'type': 'problematic_domain',
                        'severity': 'medium',
                        'description': f'Domain {domain_info["domain"]} has {domain_info["total_failures"]} failures',
                        'recommendation': f'Implement domain-specific strategy for {domain_info["domain"]}'
                    })
            
            # Check for stage-specific issues
            stage_failures = self.failure_patterns.get('domain_stage_failures', {})
            for domain, stages in stage_failures.items():
                for stage, failures in stages.items():
                    if len(failures) > 3:
                        critical_issues.append({
                            'type': 'stage_failure',
                            'severity': 'medium',
                            'description': f'Stage {stage} failing frequently on {domain}',
                            'recommendation': f'Improve {stage} handling for {domain}'
                        })
            
            self.critical_failures = critical_issues
            
        except Exception as e:
            print(f"⚠️ Critical issue identification failed: {e}")
    
    def analyze_strategy_performance(self, knowledge):
        """Analyze strategy performance and identify improvements"""
        try:
            strategy_success_rates = knowledge.get('strategy_success_rates', {})
            
            strategy_performance = {}
            for domain, strategies in strategy_success_rates.items():
                for strategy, attempts in strategies.items():
                    if attempts:
                        success_count = sum(1 for attempt in attempts if attempt['success'])
                        success_rate = success_count / len(attempts)
                        
                        if strategy not in strategy_performance:
                            strategy_performance[strategy] = []
                        strategy_performance[strategy].append(success_rate)
            
            # Calculate average performance per strategy
            avg_performance = {}
            for strategy, rates in strategy_performance.items():
                avg_performance[strategy] = sum(rates) / len(rates)
            
            self.strategy_recommendations = {
                'avg_performance': avg_performance,
                'best_strategies': sorted(avg_performance.items(), key=lambda x: x[1], reverse=True),
                'worst_strategies': sorted(avg_performance.items(), key=lambda x: x[1])
            }
            
        except Exception as e:
            print(f"⚠️ Strategy performance analysis failed: {e}")
    
    def generate_improvements(self):
        """Generate improvement suggestions based on analysis"""
        try:
            improvements = []
            
            # Generate AI-powered suggestions if available
            if self.AI_ENABLED:
                ai_suggestions = self.generate_ai_improvements()
                if ai_suggestions:  # Check if not None
                    improvements.extend(ai_suggestions)
            
            # Generate rule-based suggestions
            rule_suggestions = self.generate_rule_based_improvements()
            if rule_suggestions:  # Check if not None
                improvements.extend(rule_suggestions)
            
            # Generate strategy improvements
            strategy_improvements = self.generate_strategy_improvements()
            if strategy_improvements:  # Check if not None
                improvements.extend(strategy_improvements)
            
            # Generate code patches
            code_patches = self.generate_code_patches()
            if code_patches:  # Check if not None
                improvements.extend(code_patches)
            
            self.improvement_suggestions = improvements
            
        except Exception as e:
            print(f"⚠️ Improvement generation failed: {e}")
            self.improvement_suggestions = []
    
    def generate_ai_improvements(self):
        """Use AI to generate intelligent improvement suggestions"""
        if not self.AI_ENABLED:
            return []
        
        # Rate limiting to prevent token limit issues
        current_time = time.time()
        if current_time - self.last_ai_analysis < self.ai_analysis_cooldown:
            remaining_time = int(self.ai_analysis_cooldown - (current_time - self.last_ai_analysis))
            print(f"⏳ AI analysis on cooldown - {remaining_time} seconds remaining")
            return []
        
        try:
            # Create a much smaller, summarized analysis for AI
            # Only send key metrics, not the full data
            analysis_summary = {
                'total_failures': sum(self.failure_patterns.get('error_type_counts', {}).values()),
                'most_common_errors': dict(list(self.failure_patterns.get('error_type_counts', {}).items())[:3]),  # Top 3 only
                'success_trend': self.success_trends.get('trend_direction', 'unknown'),
                'critical_issues_count': len(self.critical_failures),
                'problematic_domains_count': len(self.failure_patterns.get('problematic_domains', [])),
                'best_strategy': self.strategy_recommendations.get('best_strategies', [])[:1],  # Top 1 only
                'worst_strategy': self.strategy_recommendations.get('worst_strategies', [])[:1]  # Top 1 only
            }
            
            prompt = f"""
            Analyze this darknet scraping agent's performance summary and suggest improvements:
            
            Performance Summary:
            - Total failures: {analysis_summary['total_failures']}
            - Most common errors: {analysis_summary['most_common_errors']}
            - Success trend: {analysis_summary['success_trend']}
            - Critical issues: {analysis_summary['critical_issues_count']}
            - Problematic domains: {analysis_summary['problematic_domains_count']}
            - Best strategy: {analysis_summary['best_strategy']}
            - Worst strategy: {analysis_summary['worst_strategy']}
            
            Provide 2-3 specific, actionable suggestions for improvements.
            Return as JSON with fields: suggestions (array of improvement objects with type, description, priority, implementation_steps)
            """
            
            if self.OPENAI_API_KEY:
                response = self.openai_client.chat.completions.create(
                    model='gpt-4',
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.3
                )
                ai_response = response.choices[0].message.content
                try:
                    self.last_ai_analysis = current_time  # Update last analysis time
                    return json.loads(ai_response).get('suggestions', [])
                except json.JSONDecodeError:
                    print(f"⚠️ AI returned invalid JSON: {ai_response[:100]}...")
                    return []
            elif self.ANTHROPIC_API_KEY:
                response = self.anthropic_client.messages.create(
                    model='claude-3-sonnet-20240229',
                    max_tokens=400,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_response = response.content[0].text
                try:
                    self.last_ai_analysis = current_time  # Update last analysis time
                    return json.loads(ai_response).get('suggestions', [])
                except json.JSONDecodeError:
                    print(f"⚠️ AI returned invalid JSON: {ai_response[:100]}...")
                    return []
            
        except Exception as e:
            print(f"⚠️ AI improvement generation failed: {e}")
            return []
    
    def generate_rule_based_improvements(self):
        """Generate improvements based on predefined rules"""
        improvements = []
        
        # Check for high failure rates
        if self.failure_patterns.get('error_type_counts', {}):
            most_common_error = max(self.failure_patterns['error_type_counts'].items(), key=lambda x: x[1])[0]
            if self.failure_patterns['error_type_counts'][most_common_error] > 5:
                improvements.append({
                    'type': 'error_handling',
                    'description': f'High rate of {most_common_error} errors',
                    'priority': 'high',
                    'implementation_steps': [
                        f'Review and improve {most_common_error} handling',
                        'Add retry logic with exponential backoff',
                        'Implement fallback strategies'
                    ]
                })
        
        # Check for problematic domains
        for domain_info in self.failure_patterns.get('problematic_domains', []):
            if domain_info['total_failures'] > 3:
                improvements.append({
                    'type': 'domain_specific',
                    'description': f'Domain {domain_info["domain"]} needs special handling',
                    'priority': 'medium',
                    'implementation_steps': [
                        f'Create domain-specific strategy for {domain_info["domain"]}',
                        'Add custom error handling for this domain',
                        'Implement domain-specific retry logic'
                    ]
                })
        
        # Check for declining success trends
        if self.success_trends.get('trend_direction') == 'declining':
            improvements.append({
                'type': 'performance',
                'description': 'Declining success rate detected',
                'priority': 'high',
                'implementation_steps': [
                    'Review recent changes to scraping logic',
                    'Check for site changes or anti-bot measures',
                    'Implement adaptive strategy selection'
                ]
            })
        
        return improvements
    
    def generate_strategy_improvements(self):
        """Generate strategy-specific improvements"""
        improvements = []
        
        strategy_recs = self.strategy_recommendations
        if not strategy_recs:
            return improvements
        
        # Suggest improvements for worst-performing strategies
        worst_strategies = strategy_recs.get('worst_strategies', [])
        for strategy, performance in worst_strategies[:3]:  # Top 3 worst
            if performance < 0.3:  # Less than 30% success rate
                improvements.append({
                    'type': 'strategy_improvement',
                    'description': f'Strategy {strategy} performing poorly ({performance:.1%} success rate)',
                    'priority': 'medium',
                    'implementation_steps': [
                        f'Review and improve strategy {strategy}',
                        'Add fallback strategies',
                        'Implement adaptive strategy selection'
                    ]
                })
        
        # Suggest using best-performing strategies more
        best_strategies = strategy_recs.get('best_strategies', [])
        if best_strategies:
            best_strategy, best_performance = best_strategies[0]
            if best_performance > 0.7:  # More than 70% success rate
                improvements.append({
                    'type': 'strategy_optimization',
                    'description': f'Strategy {best_strategy} performing well ({best_performance:.1%} success rate)',
                    'priority': 'low',
                    'implementation_steps': [
                        f'Increase usage of strategy {best_strategy}',
                        'Use as default strategy for similar sites',
                        'Optimize parameters for this strategy'
                    ]
                })
        
        return improvements
    
    def generate_code_patches(self):
        """Generate specific code patches and improvements"""
        patches = []
        
        # Generate patches based on common failure patterns
        error_patterns = self.failure_patterns.get('error_type_counts', {})
        
        if 'captcha_required' in error_patterns and error_patterns['captcha_required'] > 3:
            patches.append({
                'type': 'code_patch',
                'file': 'scraper_fast.py',
                'description': 'Improve captcha handling',
                'priority': 'high',
                'patch': '''
# Enhanced captcha handling
def enhanced_captcha_solver(driver):
    """Enhanced captcha solving with multiple fallback methods"""
    # Try AI-based solving first
    if AI_ENABLED:
        solution = ai_solve_captcha(driver)
        if solution:
            return solution
    
    # Fallback to OCR
    solution = ocr_solve_captcha(driver)
    if solution:
        return solution
    
    # Fallback to manual solving
    return manual_captcha_solver(driver)
''',
                'implementation_steps': [
                    'Add enhanced_captcha_solver function',
                    'Update captcha handling calls',
                    'Test with known problematic sites'
                ]
            })
        
        if 'timeout' in error_patterns and error_patterns['timeout'] > 3:
            patches.append({
                'type': 'code_patch',
                'file': 'scraper_fast.py',
                'description': 'Improve timeout handling',
                'priority': 'medium',
                'patch': '''
# Enhanced timeout handling
def adaptive_timeout_handler(driver, url, max_retries=3):
    """Handle timeouts with adaptive retry logic"""
    for attempt in range(max_retries):
        try:
            driver.set_page_load_timeout(30 + (attempt * 10))  # Increasing timeout
            driver.get(url)
            return True
        except TimeoutException:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                return False
''',
                'implementation_steps': [
                    'Add adaptive_timeout_handler function',
                    'Update page loading calls',
                    'Test timeout scenarios'
                ]
            })
        
        return patches
    
    def log_analysis_results(self):
        """Log analysis results and improvements"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_results': {
                    'failure_patterns': self.failure_patterns,
                    'success_trends': self.success_trends,
                    'critical_issues': self.critical_failures,
                    'strategy_recommendations': self.strategy_recommendations
                },
                'improvements': self.improvement_suggestions
            }
            
            with open(self.fixer_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Print summary
            print(f"🔧 Analysis Summary:")
            print(f"   - Critical issues: {len(self.critical_failures)}")
            print(f"   - Improvement suggestions: {len(self.improvement_suggestions)}")
            print(f"   - Problematic domains: {len(self.failure_patterns.get('problematic_domains', []))}")
            
        except Exception as e:
            print(f"⚠️ Analysis logging failed: {e}")
    
    def get_improvement_report(self):
        """Get a formatted improvement report"""
        try:
            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'summary': {
                    'critical_issues': len(self.critical_failures),
                    'improvements': len(self.improvement_suggestions),
                    'problematic_domains': len(self.failure_patterns.get('problematic_domains', [])),
                    'success_trend': self.success_trends.get('trend_direction', 'unknown')
                },
                'critical_issues': self.critical_failures,
                'improvements': self.improvement_suggestions,
                'strategy_recommendations': self.strategy_recommendations
            }
            return report
        except Exception as e:
            print(f"⚠️ Report generation failed: {e}")
            return {}

# Global fixer agent instance
fixer_agent = FixerAgent()
