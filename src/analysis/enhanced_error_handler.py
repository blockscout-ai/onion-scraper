#!/usr/bin/env python3
"""
Enhanced Error Handler for Onion Scraper
Provides intelligent error handling with adaptive strategies and improved recovery mechanisms.
"""

import time
import random
import json
from datetime import datetime

class EnhancedErrorHandler:
    def __init__(self):
        self.error_patterns = {}
        self.recovery_strategies = {}
        self.failure_counts = {}
        self.success_rates = {}
        
        # Enhanced retry configuration
        self.max_retries = 5
        self.base_delay = 3.0
        self.delay_multiplier = 2.0
        self.max_delay = 30.0
        
        self.setup_error_patterns()
        self.setup_recovery_strategies()
    
    def setup_error_patterns(self):
        """Enhanced error pattern recognition"""
        self.error_patterns = {
            'no_addresses': {
                'indicators': ['no addresses', 'addresses not found', 'empty result', 'no crypto'],
                'priority': 'high',
                'recovery_action': 'enhanced_extraction'
            },
            'processing_error': {
                'indicators': ['processing failed', 'extraction error', 'parse error', 'invalid html'],
                'priority': 'medium',
                'recovery_action': 'retry_with_backoff'
            },
            'captcha_error': {
                'indicators': ['captcha', 'verification required', 'human verification', 'prove you are human'],
                'priority': 'high',
                'recovery_action': 'ai_captcha_solving'
            },
            'timeout_error': {
                'indicators': ['timeout', 'page load timeout', 'connection timeout', 'request timeout'],
                'priority': 'medium',
                'recovery_action': 'increase_delays'
            },
            'connection_error': {
                'indicators': ['connection refused', 'network error', 'dns error', 'unreachable'],
                'priority': 'medium',
                'recovery_action': 'rotate_tor_identity'
            },
            'blocked_error': {
                'indicators': ['blocked', 'forbidden', 'access denied', 'banned'],
                'priority': 'high',
                'recovery_action': 'change_strategy'
            },
            'javascript_error': {
                'indicators': ['javascript', 'js error', 'script error', 'dynamic content'],
                'priority': 'medium',
                'recovery_action': 'enable_js_execution'
            }
        }
    
    def setup_recovery_strategies(self):
        """Enhanced recovery strategies with better success rates"""
        self.recovery_strategies = {
            'enhanced_extraction': {
                'action': 'switch_to_js_strategy',
                'delay': 3,
                'tor_rotation': True,
                'strategy_change': 4,
                'description': 'Switch to JavaScript-heavy strategy for better extraction'
            },
            'retry_with_backoff': {
                'action': 'exponential_backoff',
                'delay': random.uniform(5, 12),
                'tor_rotation': False,
                'strategy_change': None,
                'description': 'Retry with exponential backoff delay'
            },
            'ai_captcha_solving': {
                'action': 'enable_ai_captcha',
                'delay': 5,
                'tor_rotation': False,
                'strategy_change': 3,
                'description': 'Enable AI-powered captcha solving'
            },
            'increase_delays': {
                'action': 'conservative_timing',
                'delay': random.uniform(8, 15),
                'tor_rotation': True,
                'strategy_change': 2,
                'description': 'Use conservative timing and delays'
            },
            'rotate_tor_identity': {
                'action': 'new_tor_circuit',
                'delay': random.uniform(10, 20),
                'tor_rotation': True,
                'strategy_change': 1,
                'description': 'Get new TOR circuit and retry'
            },
            'change_strategy': {
                'action': 'adaptive_strategy',
                'delay': random.uniform(12, 25),
                'tor_rotation': True,
                'strategy_change': 'adaptive',
                'description': 'Switch to adaptive strategy based on site type'
            },
            'enable_js_execution': {
                'action': 'full_js_rendering',
                'delay': random.uniform(8, 18),
                'tor_rotation': False,
                'strategy_change': 4,
                'description': 'Enable full JavaScript rendering and execution'
            }
        }
    
    def handle_error(self, error_type, url, details="", attempt=1):
        """Enhanced error handling with intelligent recovery"""
        timestamp = datetime.utcnow().isoformat()
        
        # Record failure for analysis
        if error_type not in self.failure_counts:
            self.failure_counts[error_type] = 0
        self.failure_counts[error_type] += 1
        
        # Get recovery strategy
        recovery = self.get_recovery_strategy(error_type, attempt)
        
        print(f"🔧 [{timestamp}] Error Handler: {error_type}")
        print(f"   URL: {url}")
        print(f"   Attempt: {attempt}")
        print(f"   Recovery: {recovery['description']}")
        print(f"   Delay: {recovery['delay']:.1f}s")
        
        # Calculate exponential backoff delay
        delay = min(self.base_delay * (self.delay_multiplier ** (attempt - 1)), self.max_delay)
        actual_delay = max(recovery['delay'], delay)
        
        return {
            'recovery_action': recovery['action'],
            'delay': actual_delay,
            'tor_rotation': recovery['tor_rotation'],
            'strategy_change': recovery['strategy_change'],
            'retry_recommended': attempt < self.max_retries,
            'priority': self.error_patterns.get(error_type, {}).get('priority', 'medium')
        }
    
    def get_recovery_strategy(self, error_type, attempt):
        """Get appropriate recovery strategy based on error type and attempt number"""
        if error_type in self.error_patterns:
            recovery_action = self.error_patterns[error_type]['recovery_action']
            if recovery_action in self.recovery_strategies:
                strategy = self.recovery_strategies[recovery_action].copy()
                
                # Adjust delay based on attempt number
                base_delay = strategy['delay']
                strategy['delay'] = base_delay * (1.5 ** (attempt - 1))
                
                return strategy
        
        # Default recovery strategy
        return {
            'action': 'retry_with_backoff',
            'delay': 5 * attempt,
            'tor_rotation': True,
            'strategy_change': None,
            'description': 'Default retry with backoff'
        }
    
    def classify_error(self, error_message):
        """Classify error based on message content"""
        error_message_lower = error_message.lower()
        
        for error_type, pattern_info in self.error_patterns.items():
            for indicator in pattern_info['indicators']:
                if indicator.lower() in error_message_lower:
                    return error_type
        
        return 'unknown_error'
    
    def should_retry(self, error_type, attempt):
        """Determine if retry is recommended"""
        if attempt >= self.max_retries:
            return False
        
        # High priority errors get more retries
        if error_type in self.error_patterns:
            priority = self.error_patterns[error_type]['priority']
            if priority == 'high':
                return attempt < self.max_retries + 2
            elif priority == 'medium':
                return attempt < self.max_retries
            else:
                return attempt < self.max_retries - 1
        
        return attempt < self.max_retries
    
    def get_statistics(self):
        """Get error handling statistics"""
        total_failures = sum(self.failure_counts.values())
        
        stats = {
            'total_failures': total_failures,
            'failure_breakdown': self.failure_counts.copy(),
            'most_common_errors': sorted(
                self.failure_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
        }
        
        return stats
    
    def reset_statistics(self):
        """Reset error statistics"""
        self.failure_counts = {}
        self.success_rates = {}

# Global instance
enhanced_error_handler = EnhancedErrorHandler()

def handle_scraping_error(error_type, url, details="", attempt=1):
    """Main error handling function"""
    return enhanced_error_handler.handle_error(error_type, url, details, attempt)

def classify_scraping_error(error_message):
    """Classify error type from message"""
    return enhanced_error_handler.classify_error(error_message)

def should_retry_scraping(error_type, attempt):
    """Check if scraping should be retried"""
    return enhanced_error_handler.should_retry(error_type, attempt)

def get_error_statistics():
    """Get current error statistics"""
    return enhanced_error_handler.get_statistics()
