# ---[ Integrated Agent System for scraper_fast.py ]---
"""
Comprehensive integration of Learning Agent and Fixer Agent with on-the-fly self-fixing.
This module provides all the agent functionality integrated into your main scraper.

Features:
- Real-time learning from successes and failures
- On-the-fly strategy adaptation
- Comprehensive terminal logging
- Automatic fixer agent monitoring
- Self-healing capabilities
"""

import threading
import time
import json
import os
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import queue

# Import our agents
from learning_agent import LearningAgent
from fixer_agent import FixerAgent

class IntegratedAgentSystem:
    """Fully integrated agent system with on-the-fly self-fixing"""
    
    def __init__(self, knowledge_file="knowledge_base.json", enable_fixer=True):
        self.knowledge_file = knowledge_file
        self.enable_fixer = enable_fixer
        self.running = False
        
        # Initialize agents
        self.learning_agent = LearningAgent(knowledge_file)
        self.fixer_agent = FixerAgent(knowledge_file) if enable_fixer else None
        
        # Threading for concurrent operation
        self.fixer_thread = None
        self.stats_thread = None
        
        # Communication queues
        self.learning_queue = queue.Queue()
        self.fixer_queue = queue.Queue()
        
        # Real-time statistics
        self.live_stats = {
            'start_time': datetime.utcnow(),
            'total_processed': 0,
            'successes': 0,
            'failures': 0,
            'strategy_adaptations': 0,
            'fixer_suggestions': 0,
            'applied_improvements': 0,
            'current_strategy': 'default',
            'last_activity': None
        }
        
        # Strategy adaptation state
        self.adaptation_state = {
            'current_domain': None,
            'failure_count': 0,
            'success_count': 0,
            'last_strategy_change': None,
            'adaptive_mode': True,
            'signature_failures': {},      # Track failures by content signature
            'signature_successes': {},     # Track successes by content signature
            'current_signature': None,     # Current content signature
            'global_success_count': 0,     # Global success tracking
            'global_failure_count': 0,     # Global failure tracking
            'consecutive_failures': 0,     # Consecutive failure count
            'last_success_time': None,     # Last success timestamp
            'enable_ai_captcha': False,    # AI captcha solving flag
            'enhanced_retry': False        # Enhanced retry logic flag
        }
        
        # Terminal logging configuration
        self.logging_config = {
            'show_detailed_logs': True,
            'show_strategy_changes': True,
            'show_fixer_activity': True,
            'show_statistics': True,
            'stats_interval': 30  # seconds
        }
        
        print("🤖 Integrated Agent System initialized")
        if enable_fixer:
            print("🔧 Fixer Agent enabled - monitoring and self-healing active")
        else:
            print("⚠️ Fixer Agent disabled - learning only mode")
    
    def extract_content_signature(self, page_content, url):
        """Extract a signature based on page structure/content for onion mirrors"""
        try:
            if not page_content:
                return "empty"
            
            # Create a signature based on page structure and content patterns
            signature = {
                'has_login_form': 'login' in page_content.lower() or 'username' in page_content.lower() or 'password' in page_content.lower(),
                'has_captcha': 'captcha' in page_content.lower() or 'recaptcha' in page_content.lower() or 'g-recaptcha' in page_content.lower(),
                'has_js_heavy': len(page_content) > 50000,  # Large pages often have heavy JS
                'url_path_depth': len(url.split('/')) - 3,  # How deep the URL path is
                'content_length': len(page_content),
                'form_count': page_content.count('<form'),
                'button_count': page_content.count('<button'),
                'input_count': page_content.count('<input'),
                'div_count': page_content.count('<div'),
                'script_count': page_content.count('<script'),
                'has_onion_domain': '.onion' in url.lower(),
                'has_marketplace_indicators': any(indicator in page_content.lower() for indicator in ['market', 'shop', 'store', 'buy', 'sell', 'product', 'item']),
                'has_forum_indicators': any(indicator in page_content.lower() for indicator in ['forum', 'board', 'thread', 'post', 'topic', 'discussion']),
                'has_blog_indicators': any(indicator in page_content.lower() for indicator in ['blog', 'article', 'post', 'news', 'story']),
                'has_payment_indicators': any(indicator in page_content.lower() for indicator in ['bitcoin', 'btc', 'payment', 'wallet', 'address', 'crypto']),
                'has_error_page': any(indicator in page_content.lower() for indicator in ['error', '404', 'not found', 'forbidden', 'blocked']),
                'has_maintenance': any(indicator in page_content.lower() for indicator in ['maintenance', 'down', 'offline', 'temporarily unavailable'])
            }
            
            # Create a hash of the signature for comparison
            signature_str = str(sorted(signature.items()))
            return hashlib.md5(signature_str.encode()).hexdigest()[:8]
            
        except Exception as e:
            print(f"⚠️ Content signature extraction failed: {e}")
            return "error"
    
    def get_signature_category(self, signature_data):
        """Get category based on content signature"""
        try:
            if signature_data.get('has_marketplace_indicators', False):
                return "marketplace"
            elif signature_data.get('has_forum_indicators', False):
                return "forum"
            elif signature_data.get('has_blog_indicators', False):
                return "blog"
            elif signature_data.get('has_login_form', False):
                return "login_required"
            elif signature_data.get('has_captcha', False):
                return "captcha_protected"
            elif signature_data.get('has_error_page', False):
                return "error_page"
            elif signature_data.get('has_maintenance', False):
                return "maintenance"
            else:
                return "general"
        except Exception as e:
            return "unknown"
    
    def start_system(self):
        """Start the integrated agent system"""
        self.running = True
        
        # Start fixer agent in background if enabled
        if self.enable_fixer and self.fixer_agent:
            self.fixer_thread = threading.Thread(target=self._fixer_monitor_loop)
            self.fixer_thread.daemon = True
            self.fixer_thread.start()
            print("🔧 Fixer Agent started in background")
        
        # Start statistics thread
        self.stats_thread = threading.Thread(target=self._stats_monitor_loop)
        self.stats_thread.daemon = True
        self.stats_thread.start()
        print("📊 Statistics monitor started")
        
        print("🚀 Integrated Agent System running - ready for scraping operations")
        return True
    
    def stop_system(self):
        """Stop the integrated agent system"""
        self.running = False
        
        # Stop fixer agent
        if self.fixer_agent:
            self.fixer_agent.stop_monitoring()
        
        # Wait for threads to finish
        if self.fixer_thread and self.fixer_thread.is_alive():
            self.fixer_thread.join(timeout=5)
        if self.stats_thread and self.stats_thread.is_alive():
            self.stats_thread.join(timeout=5)
        
        # Save final knowledge
        self.learning_agent.save_knowledge_base()
        
        print("🛑 Integrated Agent System stopped")
    
    def _fixer_monitor_loop(self):
        """Background loop for fixer agent monitoring with smart adaptive intervals"""
        last_improvement_time = time.time()
        
        while self.running:
            try:
                # Calculate current success rate for adaptive scheduling
                current_success_rate = self.live_stats['successes'] / max(self.live_stats['total_processed'], 1)
                total_processed = self.live_stats['total_processed']
                
                # Smart adaptive interval based on performance
                if current_success_rate < 0.05 and total_processed > 5:  # Critical: < 5% success rate
                    interval = 120  # 2 minutes - very frequent improvements
                    auto_apply_level = 3  # Apply all improvements
                    status = "🚨 CRITICAL"
                elif current_success_rate < 0.15 and total_processed > 3:  # Struggling: 5-15% success rate
                    interval = 600  # 10 minutes - frequent improvements
                    auto_apply_level = 2  # Apply performance + critical improvements
                    status = "⚠️ STRUGGLING"
                else:  # Healthy: > 15% success rate
                    interval = 1800  # 30 minutes - less frequent improvements
                    auto_apply_level = 1  # Apply critical improvements only
                    status = "✅ HEALTHY"
                
                # Emergency mode: Zero results for extended period
                last_success_time = self.adaptation_state.get('last_success_time')
                if not isinstance(last_success_time, datetime):
                    last_success_time = datetime.utcnow()
                time_since_last_success = (datetime.utcnow() - last_success_time).total_seconds()
                
                consecutive_failures = self.adaptation_state.get('consecutive_failures', 0)
                
                emergency_mode = False
                if (consecutive_failures >= 10 and current_success_rate == 0) or time_since_last_success > 1200:  # 20 minutes without success
                    interval = 60  # 1 minute - emergency improvements
                    auto_apply_level = 3  # Apply everything
                    status = "🆘 EMERGENCY"
                    emergency_mode = True
                
                # Check if it's time for improvement analysis
                time_since_last = time.time() - last_improvement_time
                
                if time_since_last >= interval:
                    # Log adaptive status every few cycles
                    if total_processed % 20 == 0 or emergency_mode or auto_apply_level >= 2:
                        print(f"🧠 Smart Adaptive Improvements: {status}")
                        print(f"   📊 Success Rate: {current_success_rate:.1%} ({self.live_stats['successes']}/{total_processed})")
                        print(f"   ⏱️ Next improvement check: {interval//60} minutes")
                        print(f"   🔧 Auto-apply level: {auto_apply_level}/3")
                    
                    # Run fixer agent analysis
                    self.fixer_agent.analyze_knowledge_base()
                    self.fixer_agent.generate_improvements()
                    
                    # Apply improvements based on adaptive level
                    improvements = self.fixer_agent.improvement_suggestions
                    if improvements:
                        applied = self._apply_improvements_adaptively(improvements, auto_apply_level)
                        if applied > 0:
                            self.live_stats['applied_improvements'] += applied
                            self.live_stats['fixer_suggestions'] += len(improvements)
                            print(f"🔧 Smart adaptive: Auto-applied {applied}/{len(improvements)} improvements (level {auto_apply_level})")
                    
                    last_improvement_time = time.time()
                
                # Sleep for a short period before checking again
                time.sleep(30)  # Check every 30 seconds if it's time for improvements
                
            except Exception as e:
                print(f"⚠️ Smart adaptive fixer monitor error: {e}")
                time.sleep(30)
    
    def _apply_improvements_adaptively(self, improvements, auto_apply_level):
        """Apply improvements based on adaptive level and current performance"""
        applied_count = 0
        
        for improvement in improvements:
            priority = improvement.get('priority', 'medium')
            improvement_type = improvement.get('type', '')
            
            # Determine if we should apply this improvement based on level
            should_apply = False
            
            if auto_apply_level >= 3:  # Emergency/Critical - apply everything
                should_apply = True
            elif auto_apply_level >= 2:  # Struggling - apply high and medium priority
                should_apply = priority in ['high', 'critical'] or improvement_type in ['performance', 'error_handling']
            elif auto_apply_level >= 1:  # Healthy - apply only critical
                should_apply = priority == 'critical' or improvement_type == 'strategy_improvement'
            
            if should_apply:
                try:
                    if self._apply_single_improvement(improvement):
                        applied_count += 1
                        level_indicator = "🆘" if auto_apply_level >= 3 else "⚠️" if auto_apply_level >= 2 else "✅"
                        print(f"{level_indicator} Auto-applied (L{auto_apply_level}): {improvement.get('description', 'Unknown improvement')}")
                except Exception as e:
                    print(f"⚠️ Failed to apply adaptive improvement: {e}")
        
        return applied_count
    
    def _stats_monitor_loop(self):
        """Background loop for statistics and logging"""
        while self.running:
            try:
                # Print periodic statistics
                if self.logging_config['show_statistics']:
                    self._print_live_statistics()
                
                # Wait for next stats update
                time.sleep(self.logging_config['stats_interval'])
                
            except Exception as e:
                print(f"⚠️ Stats monitor error: {e}")
                time.sleep(30)
    
    def _apply_single_improvement(self, improvement):
        """Apply a single improvement"""
        improvement_type = improvement.get('type')
        
        if improvement_type == 'strategy_improvement':
            return self._apply_strategy_improvement(improvement)
        elif improvement_type == 'error_handling':
            return self._apply_error_handling_improvement(improvement)
        elif improvement_type == 'performance':
            return self._apply_performance_improvement(improvement)
        else:
            return False
    
    def _apply_strategy_improvement(self, improvement):
        """Apply strategy-specific improvements"""
        description = improvement.get('description', '')
        
        if 'performing poorly' in description:
            # Switch to a different strategy
            self.adaptation_state['adaptive_mode'] = True
            return True
        elif 'performing well' in description:
            # Promote current strategy
            self.adaptation_state['adaptive_mode'] = False
            return True
        
        return False
    
    def _apply_error_handling_improvement(self, improvement):
        """Apply error handling improvements"""
        description = improvement.get('description', '')
        
        if 'retry logic' in description:
            # Enable enhanced retry
            self.adaptation_state['enhanced_retry'] = True
            return True
        elif 'fallback strategies' in description:
            # Enable fallbacks
            self.adaptation_state['enable_fallbacks'] = True
            return True
        
        return False
    
    def _apply_performance_improvement(self, improvement):
        """Apply performance improvements"""
        description = improvement.get('description', '')
        
        if 'declining success rate' in description:
            # Trigger strategy review
            self.adaptation_state['strategy_review_needed'] = True
            return True
        
        return False
    
    def _print_live_statistics(self):
        """Print live statistics to terminal"""
        try:
            runtime = datetime.utcnow() - self.live_stats['start_time']
            success_rate = (self.live_stats['successes'] / max(self.live_stats['total_processed'], 1)) * 100
            
            print(f"\n📊 Live Agent Statistics ({runtime.total_seconds():.0f}s runtime):")
            print(f"   Processed: {self.live_stats['total_processed']} | "
                  f"Success: {self.live_stats['successes']} | "
                  f"Failure: {self.live_stats['failures']} | "
                  f"Rate: {success_rate:.1f}%")
            print(f"   Strategy Adaptations: {self.live_stats['strategy_adaptations']} | "
                  f"Applied Improvements: {self.live_stats['applied_improvements']}")
            print(f"   Current Strategy: {self.live_stats['current_strategy']} | "
                  f"Adaptive Mode: {'ON' if self.adaptation_state['adaptive_mode'] else 'OFF'}")
            
            if self.live_stats['last_activity']:
                print(f"   Last Activity: {self.live_stats['last_activity']}")
            
        except Exception as e:
            print(f"⚠️ Statistics print error: {e}")
    
    # === MAIN INTERFACE METHODS ===
    
    def get_best_strategy(self, url, content_signatures=None, worker_id="main"):
        """Get the best strategy for a URL with adaptive learning"""
        try:
            # Get base strategy from learning agent
            strategy = self.learning_agent.get_best_strategy(url, content_signatures)
            
            # Apply adaptive modifications based on current state
            if self.adaptation_state['adaptive_mode']:
                strategy = self._adapt_strategy_for_current_state(strategy, url)
            
            self.live_stats['current_strategy'] = strategy
            self.live_stats['last_activity'] = f"Strategy selection for {url}"
            
            if self.logging_config['show_strategy_changes']:
                print(f"🎯 [{worker_id}] Selected strategy {strategy} for {url}")
            
            return strategy
            
        except Exception as e:
            print(f"⚠️ Strategy selection failed: {e}")
            return 1  # Default to basic strategy
    
    def _adapt_strategy_for_current_state(self, base_strategy, url):
        """Adapt strategy based on current system state"""
        try:
            # Check if we're having issues with current domain
            domain = url.split('/')[2] if '//' in url else url
            
            if domain == self.adaptation_state['current_domain']:
                # Same domain - check failure count
                if self.adaptation_state['failure_count'] > 0:  # More responsive: adapt on first failure  # Lowered from 2 to 1 for more responsive adaptation
                    # Switch to more robust strategy
                    if base_strategy < 5:
                        base_strategy += 1
                    print(f"🔄 Adapting strategy due to failures on {domain}")
            
            # Check if enhanced retry is enabled
            if self.adaptation_state.get('enhanced_retry', False):
                # Prefer strategies with better retry handling
                if base_strategy < 4:
                    base_strategy = 4
            
            return base_strategy
            
        except Exception as e:
            print(f"⚠️ Strategy adaptation failed: {e}")
            return base_strategy
    
    def record_success(self, url, strategy_used, worker_id="main", stage="extracted_address", extracted_data=None):
        """Record a successful scraping attempt"""
        try:
            # Update live stats
            self.live_stats['total_processed'] += 1
            self.live_stats['successes'] += 1
            self.live_stats['last_activity'] = f"Success on {url}"
            
            # Update adaptation state with content signature tracking
            domain = url.split('/')[2] if '//' in url else url
            
            # Extract content signature for structure-based adaptation
            content_signature = self.extract_content_signature("", url)  # Empty content for success
            self.adaptation_state['current_signature'] = content_signature
            
            # Track by both domain and content signature
            if domain == self.adaptation_state['current_domain']:
                self.adaptation_state['success_count'] += 1
                self.adaptation_state['failure_count'] = 0  # Reset failure count
            else:
                # New domain
                self.adaptation_state['current_domain'] = domain
                self.adaptation_state['success_count'] = 1
                self.adaptation_state['failure_count'] = 0
            
            # Track by content signature (for onion mirrors)
            if content_signature not in self.adaptation_state['signature_successes']:
                self.adaptation_state['signature_successes'][content_signature] = 0
            self.adaptation_state['signature_successes'][content_signature] += 1
            
            # Update global success tracking
            self.adaptation_state['global_success_count'] += 1
            self.adaptation_state['consecutive_failures'] = 0  # Reset consecutive failures
            self.adaptation_state['last_success_time'] = datetime.utcnow()
            
            # Learn from success
            self.learning_agent.learn_from_success(
                url=url,
                strategy_used=strategy_used,
                worker_id=worker_id,
                stage=stage,
                extracted_data=extracted_data
            )
            
            if self.logging_config['show_detailed_logs']:
                print(f"✅ [{worker_id}] Success recorded: {url} (strategy {strategy_used}, stage {stage})")
            
        except Exception as e:
            print(f"⚠️ Success recording failed: {e}")
    
    def record_failure(self, url, error_type, strategy_used, worker_id="main", stage="extracted_address", page_content=None):
        """Record a failed scraping attempt with adaptive response"""
        try:
            # Update live stats
            self.live_stats['total_processed'] += 1
            self.live_stats['failures'] += 1
            self.live_stats['last_activity'] = f"Failure on {url}"
            
            # Update adaptation state with content signature tracking
            domain = url.split('/')[2] if '//' in url else url
            
            # Extract content signature for structure-based adaptation
            content_signature = self.extract_content_signature(page_content, url)
            self.adaptation_state['current_signature'] = content_signature
            
            # Track by both domain and content signature
            if domain == self.adaptation_state['current_domain']:
                self.adaptation_state['failure_count'] += 1
            else:
                # New domain
                self.adaptation_state['current_domain'] = domain
                self.adaptation_state['failure_count'] = 1
                self.adaptation_state['success_count'] = 0
            
            # Track by content signature (for onion mirrors)
            if content_signature not in self.adaptation_state['signature_failures']:
                self.adaptation_state['signature_failures'][content_signature] = 0
            self.adaptation_state['signature_failures'][content_signature] += 1
            
            # Update global failure tracking
            self.adaptation_state['global_failure_count'] += 1
            self.adaptation_state['consecutive_failures'] += 1
            
            # Learn from failure
            self.learning_agent.learn_from_failure(
                url=url,
                error_type=error_type,
                page_content=page_content or "",
                strategy_attempted=strategy_used,
                worker_id=worker_id,
                stage=stage
            )
            
            # Trigger adaptive response
            self._trigger_adaptive_response(url, error_type, strategy_used, worker_id)
            
            if self.logging_config['show_detailed_logs']:
                print(f"❌ [{worker_id}] Failure recorded: {url} (error: {error_type}, strategy: {strategy_used}, stage: {stage})")
            
        except Exception as e:
            print(f"⚠️ Failure recording failed: {e}")
    
    def _trigger_adaptive_response(self, url, error_type, strategy_used, worker_id):
        """Trigger adaptive response based on failure with enhanced monitoring"""
        try:
            # Check current success rate and trigger adaptation if too low
            current_success_rate = self.live_stats['successes'] / max(self.live_stats['total_processed'], 1)
            if current_success_rate < 0.1 and self.live_stats['total_processed'] > 10:
                print(f"🚨 [{worker_id}] Critical low success rate ({current_success_rate:.1%}) - forcing strategy adaptation")
                # Force strategy change
                new_strategy = (strategy_used % 5) + 1
                self.live_stats['strategy_adaptations'] += 1
                self.live_stats['current_strategy'] = new_strategy
                print(f"🔄 [{worker_id}] Forced strategy change to {new_strategy} due to low success rate")
            
            # Trigger adaptation based on content signatures and global patterns
            # More sophisticated adaptation triggers for onion mirrors
            current_signature = self.adaptation_state.get('current_signature')
            signature_failures = self.adaptation_state['signature_failures'].get(current_signature, 0) if current_signature else 0
            signature_successes = self.adaptation_state['signature_successes'].get(current_signature, 0) if current_signature else 0
            
            should_adapt = (
                self.adaptation_state['failure_count'] >= 1 or  # Domain-specific failures
                signature_failures >= 1 or  # Content signature failures (lowered from 2)
                self.adaptation_state['consecutive_failures'] >= 1 or  # Global consecutive failures (lowered from 2)
                (self.adaptation_state['global_failure_count'] > 3 and  # Lowered from 5
                 self.adaptation_state['global_success_count'] / max(self.adaptation_state['global_failure_count'], 1) < 0.15) or  # Lowered from 0.3
                (signature_failures > 0 and signature_successes == 0) or  # Never succeeded on this signature
                self.adaptation_state['global_success_count'] / max(self.adaptation_state['total_processed'], 1) < 0.1 or  # Very low overall success rate (lowered from 0.2)
                self.live_stats['successes'] / max(self.live_stats['total_processed'], 1) < 0.1  # Current session success rate
            )
            
            if should_adapt:
                # Get alternative strategy
                failure_record = {
                    'url': url,
                    'error_type': error_type,
                    'strategy_used': strategy_used,
                    'timestamp': datetime.utcnow().isoformat(),
                    'url_pattern': {'domain': url.split('/')[2] if '//' in url else url}
                }
                alternative_strategy = self.learning_agent.find_working_strategy_after_failure(failure_record)
                
                if alternative_strategy and alternative_strategy != strategy_used:
                    # More aggressive strategy switching
                    if self.live_stats['successes'] / max(self.live_stats['total_processed'], 1) < 0.15:
                        # If success rate is very low, try a completely different strategy
                        alternative_strategy = (alternative_strategy % 5) + 1  # Cycle through strategies 1-5
                    
                    self.live_stats['strategy_adaptations'] += 1
                    self.live_stats['current_strategy'] = alternative_strategy
                    
                    if self.logging_config['show_strategy_changes']:
                        current_signature = self.adaptation_state.get('current_signature', 'unknown')
                        signature_failures = self.adaptation_state['signature_failures'].get(current_signature, 0)
                        signature_successes = self.adaptation_state['signature_successes'].get(current_signature, 0)
                        
                        print(f"🔄 [{worker_id}] Adapting strategy from {strategy_used} to {alternative_strategy}")
                        print(f"   📊 Content Signature: {current_signature} (failures: {signature_failures}, successes: {signature_successes})")
                        print(f"   🌐 Domain: {self.adaptation_state['current_domain']} (failures: {self.adaptation_state['failure_count']})")
                        print(f"   📈 Global: {self.adaptation_state['global_success_count']}/{self.adaptation_state['global_failure_count']} = {self.adaptation_state['global_success_count']/max(self.adaptation_state['global_failure_count'], 1)*100:.1f}%")
            
            # Check for specific error types that need immediate response
            if 'captcha' in error_type.lower():
                print(f"🤖 [{worker_id}] Captcha detected - enabling AI captcha solver")
                # Enable AI captcha solving for next attempts
                self.adaptation_state['enable_ai_captcha'] = True
            
            elif 'timeout' in error_type.lower():
                print(f"⏱️ [{worker_id}] Timeout detected - enabling enhanced retry logic")
                # Enable enhanced retry logic
                self.adaptation_state['enhanced_retry'] = True
            
            elif 'blocked' in error_type.lower() or 'suspicious' in error_type.lower():
                print(f"🚫 [{worker_id}] Bot detection detected - switching to stealth mode")
                # Switch to stealth strategy
                self.live_stats['current_strategy'] = 2  # AI enhanced (stealth)
                self.live_stats['strategy_adaptations'] += 1
                
        except Exception as e:
            print(f"⚠️ Adaptive response failed: {e}")
    
    def get_system_status(self):
        """Get comprehensive system status"""
        try:
            status = {
                'timestamp': datetime.utcnow().isoformat(),
                'system_running': self.running,
                'live_stats': self.live_stats,
                'adaptation_state': self.adaptation_state,
                'learning_agent_stats': self.learning_agent.get_statistics(),
                'fixer_agent_active': self.fixer_thread.is_alive() if self.fixer_thread else False
            }
            
            if self.fixer_agent:
                status['fixer_agent'] = {
                    'critical_issues': len(self.fixer_agent.critical_failures),
                    'improvements': len(self.fixer_agent.improvement_suggestions),
                    'last_analysis': getattr(self.fixer_agent, 'last_analysis_time', None)
                }
            
            return status
            
        except Exception as e:
            print(f"⚠️ Status generation failed: {e}")
            return {}
    
    def get_fixer_report(self):
        """Get fixer agent report if available"""
        if self.fixer_agent:
            return self.fixer_agent.get_improvement_report()
        return {}

# Global integrated agent system instance
integrated_agents = IntegratedAgentSystem()
