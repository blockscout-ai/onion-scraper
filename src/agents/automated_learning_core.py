#!/usr/bin/env python3
"""
Core Automated Learning System - Immediate Integration Version
This provides the essential automated learning capabilities that can be integrated
into the existing scraper without major changes.
"""

import time
import threading
import json
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional

class AutomatedLearningCore:
    """
    Core automated learning system for immediate integration
    """
    
    def __init__(self):
        self.running = False
        self.learning_thread = None
        
        # Performance tracking
        self.performance_data = {
            'attempts': [],
            'strategy_performance': defaultdict(lambda: {'success': 0, 'total': 0}),
            'domain_performance': defaultdict(lambda: {'success': 0, 'total': 0}),
            'error_counts': Counter(),
            'last_improvement_time': None
        }
        
        # Learning configuration
        self.config = {
            'training_interval': 1800,  # 30 minutes
            'performance_threshold': 0.10,  # 10% success rate
            'consecutive_failure_threshold': 3,
            'enable_auto_adaptation': True,
            'enable_error_learning': True
        }
        
        # Adaptation state
        self.adaptation_state = {
            'current_strategy': '2',  # Default strategy
            'strategy_weights': {'1': 0.2, '2': 0.2, '3': 0.2, '4': 0.2, '5': 0.2},
            'domain_rules': {},
            'error_handlers': {},
            'last_adaptation': None
        }
        
        print("🤖 Automated Learning Core initialized")
        print(f"   📊 Training interval: {self.config['training_interval']}s")
        print(f"   🎯 Performance threshold: {self.config['performance_threshold']:.1%}")
    
    def start_learning(self):
        """Start the automated learning loop"""
        if self.running:
            return
        
        self.running = True
        self.learning_thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.learning_thread.start()
        
        print("🚀 Automated learning started")
    
    def stop_learning(self):
        """Stop the automated learning loop"""
        self.running = False
        if self.learning_thread:
            self.learning_thread.join()
        print("⏹️ Automated learning stopped")
    
    def record_attempt(self, success: bool, strategy: str, domain: str, error_type: str = None, worker_id: str = "main"):
        """Record a scraping attempt for learning"""
        timestamp = datetime.utcnow()
        
        # Record attempt
        attempt = {
            'timestamp': timestamp.isoformat(),
            'success': success,
            'strategy': strategy,
            'domain': domain,
            'error_type': error_type,
            'worker_id': worker_id
        }
        
        self.performance_data['attempts'].append(attempt)
        
        # Keep only recent attempts (last 1000)
        if len(self.performance_data['attempts']) > 1000:
            self.performance_data['attempts'] = self.performance_data['attempts'][-500:]
        
        # Update strategy performance
        self.performance_data['strategy_performance'][strategy]['total'] += 1
        if success:
            self.performance_data['strategy_performance'][strategy]['success'] += 1
        
        # Update domain performance
        self.performance_data['domain_performance'][domain]['total'] += 1
        if success:
            self.performance_data['domain_performance'][domain]['success'] += 1
        
        # Update error counts
        if error_type and not success:
            self.performance_data['error_counts'][error_type] += 1
        
        # Log the attempt
        status = "✅" if success else "❌"
        print(f"{status} [{worker_id}] Recorded attempt: {domain} (strategy {strategy}) - {'Success' if success else f'Failed: {error_type}'}")
    
    def get_best_strategy(self, domain: str) -> str:
        """Get the best strategy for a domain based on learned performance"""
        # Check for domain-specific rules
        if domain in self.adaptation_state['domain_rules']:
            return self.adaptation_state['domain_rules'][domain]['suggested_strategy']
        
        # Check domain performance
        domain_perf = self.performance_data['domain_performance'].get(domain, {})
        if domain_perf.get('total', 0) > 5:
            # Find best strategy for this domain
            best_strategy = None
            best_rate = 0
            
            for strategy, perf in self.performance_data['strategy_performance'].items():
                if perf['total'] > 0:
                    rate = perf['success'] / perf['total']
                    if rate > best_rate:
                        best_rate = rate
                        best_strategy = strategy
            
            if best_strategy and best_rate > 0.2:  # At least 20% success rate
                return best_strategy
        
        # Use weighted strategy selection
        return self._select_weighted_strategy()
    
    def _select_weighted_strategy(self) -> str:
        """Select strategy based on learned weights"""
        import random
        
        strategies = list(self.adaptation_state['strategy_weights'].keys())
        weights = list(self.adaptation_state['strategy_weights'].values())
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight for w in weights]
        else:
            normalized_weights = [1.0 / len(weights)] * len(weights)
        
        return random.choices(strategies, weights=normalized_weights)[0]
    
    def _learning_loop(self):
        """Main learning loop"""
        while self.running:
            try:
                # Check if learning/adaptation is needed
                if self._should_adapt():
                    self._perform_adaptation()
                
                # Sleep until next check
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"⚠️ Learning loop error: {e}")
                time.sleep(60)
    
    def _should_adapt(self) -> bool:
        """Determine if adaptation should be triggered"""
        current_time = time.time()
        last_adaptation = self.adaptation_state.get('last_adaptation', 0)
        
        # Time-based adaptation
        if current_time - last_adaptation > self.config['training_interval']:
            return True
        
        # Performance-based adaptation
        current_success_rate = self._calculate_current_success_rate()
        if current_success_rate < self.config['performance_threshold']:
            return True
        
        # Consecutive failures trigger
        if self._get_consecutive_failures() >= self.config['consecutive_failure_threshold']:
            return True
        
        return False
    
    def _perform_adaptation(self):
        """Perform learning and adaptation"""
        try:
            print("🧠 Performing automated adaptation...")
            
            # 1. Analyze current performance
            analysis = self._analyze_performance()
            
            # 2. Generate improvements
            improvements = self._generate_improvements(analysis)
            
            # 3. Apply improvements
            applied_count = self._apply_improvements(improvements)
            
            # 4. Update adaptation state
            self.adaptation_state['last_adaptation'] = time.time()
            self.performance_data['last_improvement_time'] = datetime.utcnow()
            
            print(f"✅ Adaptation completed - {applied_count} improvements applied")
            
        except Exception as e:
            print(f"❌ Adaptation failed: {e}")
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze current performance"""
        recent_attempts = self.performance_data['attempts'][-100:]  # Last 100 attempts
        
        if not recent_attempts:
            return {'current_success_rate': 0.0, 'insufficient_data': True}
        
        success_count = sum(1 for attempt in recent_attempts if attempt['success'])
        current_success_rate = success_count / len(recent_attempts)
        
        # Analyze strategy performance
        strategy_analysis = {}
        for strategy, perf in self.performance_data['strategy_performance'].items():
            if perf['total'] > 0:
                strategy_analysis[strategy] = {
                    'success_rate': perf['success'] / perf['total'],
                    'total_attempts': perf['total']
                }
        
        # Analyze domain performance
        domain_analysis = {}
        for domain, perf in self.performance_data['domain_performance'].items():
            if perf['total'] > 0:
                domain_analysis[domain] = {
                    'success_rate': perf['success'] / perf['total'],
                    'total_attempts': perf['total']
                }
        
        return {
            'current_success_rate': current_success_rate,
            'strategy_performance': strategy_analysis,
            'domain_performance': domain_analysis,
            'error_patterns': dict(self.performance_data['error_counts']),
            'consecutive_failures': self._get_consecutive_failures()
        }
    
    def _generate_improvements(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvements based on performance analysis"""
        improvements = []
        
        # Strategy improvements
        for strategy, perf in analysis['strategy_performance'].items():
            if perf['success_rate'] < self.config['performance_threshold']:
                improvements.append({
                    'type': 'strategy_optimization',
                    'target': strategy,
                    'current_performance': perf['success_rate'],
                    'action': 'reduce_weight'
                })
        
        # Domain-specific improvements
        for domain, perf in analysis['domain_performance'].items():
            if perf['total_attempts'] > 3 and perf['success_rate'] < 0.1:
                # Find best strategy for this domain
                best_strategy = self._find_best_strategy_for_domain(domain)
                if best_strategy:
                    improvements.append({
                        'type': 'domain_rule',
                        'target': domain,
                        'suggested_strategy': best_strategy,
                        'current_performance': perf['success_rate']
                    })
        
        # Error handling improvements
        for error_type, count in analysis['error_patterns'].items():
            if count > 2:  # More than 2 occurrences
                improvements.append({
                    'type': 'error_handling',
                    'target': error_type,
                    'occurrence_count': count,
                    'action': 'enhance_handling'
                })
        
        return improvements
    
    def _apply_improvements(self, improvements: List[Dict[str, Any]]) -> int:
        """Apply the generated improvements"""
        applied_count = 0
        
        for improvement in improvements:
            try:
                if improvement['type'] == 'strategy_optimization':
                    if self._apply_strategy_optimization(improvement):
                        applied_count += 1
                
                elif improvement['type'] == 'domain_rule':
                    if self._apply_domain_rule(improvement):
                        applied_count += 1
                
                elif improvement['type'] == 'error_handling':
                    if self._apply_error_handling(improvement):
                        applied_count += 1
                
            except Exception as e:
                print(f"Failed to apply improvement {improvement}: {e}")
        
        return applied_count
    
    def _apply_strategy_optimization(self, improvement: Dict[str, Any]) -> bool:
        """Apply strategy optimization"""
        strategy = improvement['target']
        current_performance = improvement['current_performance']
        
        # Reduce weight for poorly performing strategies
        if improvement['action'] == 'reduce_weight':
            current_weight = self.adaptation_state['strategy_weights'].get(strategy, 0.2)
            new_weight = max(current_weight * 0.5, 0.05)  # Reduce by 50%, minimum 5%
            self.adaptation_state['strategy_weights'][strategy] = new_weight
            
            print(f"🔧 Reduced weight for strategy {strategy} (performance: {current_performance:.1%})")
            return True
        
        return False
    
    def _apply_domain_rule(self, improvement: Dict[str, Any]) -> bool:
        """Apply domain-specific rule"""
        domain = improvement['target']
        suggested_strategy = improvement['suggested_strategy']
        
        # Create domain rule
        domain_rule = {
            'suggested_strategy': suggested_strategy,
            'created_at': datetime.utcnow().isoformat(),
            'performance_threshold': 0.1
        }
        
        self.adaptation_state['domain_rules'][domain] = domain_rule
        
        print(f"🔧 Created domain rule for {domain} -> strategy {suggested_strategy}")
        return True
    
    def _apply_error_handling(self, improvement: Dict[str, Any]) -> bool:
        """Apply error handling improvement"""
        error_type = improvement['target']
        count = improvement['occurrence_count']
        
        # Create error handler
        error_handler = {
            'retry_count': 3,
            'timeout_multiplier': 1.5,
            'strategy_switch': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        self.adaptation_state['error_handlers'][error_type] = error_handler
        
        print(f"🔧 Enhanced error handling for {error_type} ({count} occurrences)")
        return True
    
    def _find_best_strategy_for_domain(self, domain: str) -> Optional[str]:
        """Find the best performing strategy for a specific domain"""
        # This would analyze which strategy works best for this domain
        # For now, return the strategy with highest overall success rate
        best_strategy = None
        best_rate = 0
        
        for strategy, perf in self.performance_data['strategy_performance'].items():
            if perf['total'] > 0:
                rate = perf['success'] / perf['total']
                if rate > best_rate:
                    best_rate = rate
                    best_strategy = strategy
        
        return best_strategy if best_rate > 0.2 else None
    
    def _calculate_current_success_rate(self) -> float:
        """Calculate current success rate from recent attempts"""
        recent_attempts = self.performance_data['attempts'][-50:]  # Last 50 attempts
        if not recent_attempts:
            return 0.0
        
        success_count = sum(1 for attempt in recent_attempts if attempt['success'])
        return success_count / len(recent_attempts)
    
    def _get_consecutive_failures(self) -> int:
        """Get number of consecutive failures"""
        recent_attempts = self.performance_data['attempts'][-20:]  # Last 20 attempts
        consecutive_failures = 0
        
        for attempt in reversed(recent_attempts):
            if not attempt['success']:
                consecutive_failures += 1
            else:
                break
        
        return consecutive_failures
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'learning_active': self.running,
            'current_success_rate': self._calculate_current_success_rate(),
            'consecutive_failures': self._get_consecutive_failures(),
            'total_attempts': len(self.performance_data['attempts']),
            'strategy_performance': dict(self.performance_data['strategy_performance']),
            'domain_rules': len(self.adaptation_state['domain_rules']),
            'error_handlers': len(self.adaptation_state['error_handlers']),
            'last_adaptation': self.adaptation_state.get('last_adaptation')
        }
    
    def save_state(self, filename: str = "automated_learning_state.json"):
        """Save learning state to file"""
        try:
            state = {
                'performance_data': self.performance_data,
                'adaptation_state': self.adaptation_state,
                'config': self.config,
                'saved_at': datetime.utcnow().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"💾 Learning state saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save learning state: {e}")
    
    def load_state(self, filename: str = "automated_learning_state.json"):
        """Load learning state from file"""
        try:
            with open(filename, 'r') as f:
                state = json.load(f)
            
            self.performance_data = state.get('performance_data', self.performance_data)
            self.adaptation_state = state.get('adaptation_state', self.adaptation_state)
            self.config.update(state.get('config', {}))
            
            print(f"📂 Learning state loaded from {filename}")
            
        except FileNotFoundError:
            print(f"📂 No existing learning state found, starting fresh")
        except Exception as e:
            print(f"❌ Failed to load learning state: {e}")


# Global instance for easy integration
automated_learning = AutomatedLearningCore()
