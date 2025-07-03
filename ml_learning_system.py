#!/usr/bin/env python3
"""
ML Learning System for Crypto Address Extraction
Tracks patterns, learns from experience, and adapts extraction strategies
"""

import json
import pickle
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import threading
import os

@dataclass
class SiteFeatures:
    """Features extracted from a site for ML learning"""
    has_cart: bool = False
    has_registration: bool = False
    has_login: bool = False
    has_search: bool = False
    has_categories: bool = False
    page_type: str = "unknown"  # product_listing, forum, market, etc.
    javascript_frameworks: List[str] = None
    has_payment_forms: bool = False
    has_bitcoin_mentions: bool = False
    has_crypto_mentions: bool = False
    has_wallet_mentions: bool = False
    text_length: int = 0
    link_count: int = 0
    form_count: int = 0
    button_count: int = 0
    input_count: int = 0
    
    def __post_init__(self):
        if self.javascript_frameworks is None:
            self.javascript_frameworks = []

@dataclass
class ExtractionAttempt:
    """Record of an extraction attempt"""
    strategy: str
    success: bool
    time_taken: float
    addresses_found: int = 0
    addresses_valid: int = 0
    error_message: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SiteResult:
    """Complete result for a site extraction"""
    site_url: str
    site_hash: str
    site_features: SiteFeatures
    extraction_attempts: List[ExtractionAttempt]
    final_addresses: List[str]
    total_time: float
    success: bool
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MLAddressExtractor:
    """Machine Learning system for adaptive address extraction"""
    
    def __init__(self, model_path: str = "extraction_model.pkl", data_path: str = "extraction_data.json"):
        self.model_path = model_path
        self.data_path = data_path
        self.lock = threading.Lock()
        
        # ML Components
        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.vectorizer = DictVectorizer(sparse=False)
        self.is_trained = False
        
        # Learning Data
        self.site_results: List[SiteResult] = []
        self.strategy_performance: Dict[str, Dict] = defaultdict(lambda: {
            'success_count': 0,
            'total_count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'avg_addresses': 0.0
        })
        
        # Load existing data
        self.load_data()
        
    def extract_site_features(self, driver, url: str) -> SiteFeatures:
        """Extract features from a site for ML learning"""
        try:
            features = SiteFeatures()
            
            # Basic page analysis
            page_source = driver.page_source.lower()
            features.text_length = len(page_source)
            
            # Check for common elements
            features.has_cart = any(term in page_source for term in ['cart', 'shopping cart', 'add to cart'])
            features.has_registration = any(term in page_source for term in ['register', 'sign up', 'create account'])
            features.has_login = any(term in page_source for term in ['login', 'sign in', 'log in'])
            features.has_search = any(term in page_source for term in ['search', 'find'])
            features.has_categories = any(term in page_source for term in ['category', 'categories', 'browse'])
            
            # Check for payment/crypto mentions
            features.has_payment_forms = any(term in page_source for term in ['payment', 'pay', 'checkout'])
            features.has_bitcoin_mentions = 'bitcoin' in page_source or 'btc' in page_source
            features.has_crypto_mentions = any(term in page_source for term in ['crypto', 'cryptocurrency', 'wallet'])
            features.has_wallet_mentions = 'wallet' in page_source
            
            # Count elements
            features.link_count = len(driver.find_elements("tag name", "a"))
            features.form_count = len(driver.find_elements("tag name", "form"))
            features.button_count = len(driver.find_elements("tag name", "button"))
            features.input_count = len(driver.find_elements("tag name", "input"))
            
            # Detect JavaScript frameworks
            js_frameworks = []
            if 'jquery' in page_source:
                js_frameworks.append('jquery')
            if 'react' in page_source or 'reactjs' in page_source:
                js_frameworks.append('react')
            if 'vue' in page_source or 'vuejs' in page_source:
                js_frameworks.append('vue')
            if 'angular' in page_source:
                js_frameworks.append('angular')
            features.javascript_frameworks = js_frameworks
            
            # Determine page type
            if features.has_cart and features.has_payment_forms:
                features.page_type = "ecommerce"
            elif features.has_categories and features.has_search:
                features.page_type = "marketplace"
            elif features.has_registration and features.has_login:
                features.page_type = "forum"
            elif features.has_bitcoin_mentions and features.has_wallet_mentions:
                features.page_type = "crypto_service"
            else:
                features.page_type = "general"
                
            return features
            
        except Exception as e:
            print(f"Error extracting site features: {e}")
            return SiteFeatures()
    
    def classify_site(self, features: SiteFeatures) -> str:
        """Classify site type based on features"""
        if features.has_cart and features.has_payment_forms:
            return "ecommerce"
        elif features.has_categories and features.has_search:
            return "marketplace"
        elif features.has_registration and features.has_login:
            return "forum"
        elif features.has_bitcoin_mentions and features.has_wallet_mentions:
            return "crypto_service"
        else:
            return "general"
    
    def get_best_strategy(self, features: SiteFeatures) -> str:
        """Get the best extraction strategy based on learned patterns"""
        site_type = self.classify_site(features)
        
        # Get performance data for this site type
        type_performance = defaultdict(lambda: {
            'success_count': 0, 
            'total_count': 0, 
            'total_time': 0.0,
            'success_rate': 0.0, 
            'avg_time': float('inf')
        })
        
        for result in self.site_results:
            if self.classify_site(result.site_features) == site_type:
                for attempt in result.extraction_attempts:
                    type_performance[attempt.strategy]['total_count'] += 1
                    type_performance[attempt.strategy]['total_time'] += attempt.time_taken
                    
                    if attempt.success:
                        type_performance[attempt.strategy]['success_count'] += 1
        
        # Calculate success rates and average times
        for strategy, data in type_performance.items():
            if data['total_count'] > 0:
                data['success_rate'] = data['success_count'] / data['total_count']
                data['avg_time'] = data['total_time'] / data['total_count']
        
        # Return strategy with highest success rate (with time as tiebreaker)
        if type_performance:
            best_strategy = max(type_performance.keys(), 
                              key=lambda s: (type_performance[s]['success_rate'], -type_performance[s]['avg_time']))
            return best_strategy
        
        # Default strategies by site type
        default_strategies = {
            "ecommerce": "cart_interaction",
            "marketplace": "product_navigation",
            "forum": "profile_scan",
            "crypto_service": "direct_extraction",
            "general": "enhanced_regex"
        }
        
        return default_strategies.get(site_type, "enhanced_regex")
    
    def record_extraction_attempt(self, strategy: str, success: bool, time_taken: float, 
                                addresses_found: int = 0, addresses_valid: int = 0, 
                                error_message: str = ""):
        """Record an extraction attempt for learning"""
        attempt = ExtractionAttempt(
            strategy=strategy,
            success=success,
            time_taken=time_taken,
            addresses_found=addresses_found,
            addresses_valid=addresses_valid,
            error_message=error_message
        )
        
        with self.lock:
            # Update strategy performance
            self.strategy_performance[strategy]['total_count'] += 1
            self.strategy_performance[strategy]['total_time'] += time_taken
            
            if success:
                self.strategy_performance[strategy]['success_count'] += 1
            
            # Update averages
            total = self.strategy_performance[strategy]['total_count']
            self.strategy_performance[strategy]['avg_time'] = (
                self.strategy_performance[strategy]['total_time'] / total
            )
            self.strategy_performance[strategy]['avg_addresses'] = (
                (self.strategy_performance[strategy]['avg_addresses'] * (total - 1) + addresses_found) / total
            )
    
    def record_site_result(self, url: str, features: SiteFeatures, attempts: List[ExtractionAttempt],
                          final_addresses: List[str], total_time: float, success: bool):
        """Record complete site extraction result"""
        site_hash = hashlib.md5(url.encode()).hexdigest()
        
        result = SiteResult(
            site_url=url,
            site_hash=site_hash,
            site_features=features,
            extraction_attempts=attempts,
            final_addresses=final_addresses,
            total_time=total_time,
            success=success
        )
        
        with self.lock:
            self.site_results.append(result)
            self.save_data()
    
    def train_model(self):
        """Train the ML model on collected data"""
        if len(self.site_results) < 10:
            print("Not enough data to train model (need at least 10 samples)")
            return
        
        # Prepare training data
        X = []  # Features
        y = []  # Labels (success/failure)
        
        for result in self.site_results:
            # Convert site features to dict
            feature_dict = asdict(result.site_features)
            
            # Add strategy performance features
            for attempt in result.extraction_attempts:
                strategy_features = feature_dict.copy()
                strategy_features['strategy'] = attempt.strategy
                strategy_features['strategy_success_rate'] = (
                    self.strategy_performance[attempt.strategy]['success_count'] / 
                    max(self.strategy_performance[attempt.strategy]['total_count'], 1)
                )
                strategy_features['strategy_avg_time'] = self.strategy_performance[attempt.strategy]['avg_time']
                
                X.append(strategy_features)
                y.append(1 if attempt.success else 0)
        
        if len(X) < 20:
            print(f"Not enough strategy attempts to train model (need at least 20, have {len(X)})")
            return
        
        # Vectorize features
        X_vectorized = self.vectorizer.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_vectorized, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model trained successfully!")
        print(f"Accuracy: {accuracy:.3f}")
        print(f"Training samples: {len(X_train)}")
        print(f"Test samples: {len(X_test)}")
        
        self.is_trained = True
        self.save_model()
    
    def predict_success_probability(self, features: SiteFeatures, strategy: str) -> float:
        """Predict probability of success for a strategy on given features"""
        if not self.is_trained:
            return 0.5  # Default probability
        
        # Prepare feature vector
        feature_dict = asdict(features)
        feature_dict['strategy'] = strategy
        feature_dict['strategy_success_rate'] = (
            self.strategy_performance[strategy]['success_count'] / 
            max(self.strategy_performance[strategy]['total_count'], 1)
        )
        feature_dict['strategy_avg_time'] = self.strategy_performance[strategy]['avg_time']
        
        # Vectorize and predict
        try:
            X_vectorized = self.vectorizer.transform([feature_dict])
            probability = self.classifier.predict_proba(X_vectorized)[0][1]  # Probability of success
            return probability
        except Exception as e:
            print(f"Error predicting success probability: {e}")
            return 0.5
    
    def get_strategy_recommendations(self, features: SiteFeatures, top_k: int = 3) -> List[Tuple[str, float]]:
        """Get top-k strategy recommendations with success probabilities"""
        strategies = [
            "enhanced_regex", "cart_interaction", "product_navigation", 
            "profile_scan", "direct_extraction", "javascript_extract",
            "form_interaction", "ajax_wait", "scroll_and_extract"
        ]
        
        recommendations = []
        for strategy in strategies:
            probability = self.predict_success_probability(features, strategy)
            recommendations.append((strategy, probability))
        
        # Sort by probability and return top-k
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:top_k]
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about the learning system"""
        stats = {
            'total_sites_processed': len(self.site_results),
            'total_extraction_attempts': sum(len(r.extraction_attempts) for r in self.site_results),
            'overall_success_rate': 0.0,
            'strategy_performance': dict(self.strategy_performance),
            'model_trained': self.is_trained,
            'site_type_distribution': Counter(),
            'recent_performance': {}
        }
        
        # Calculate overall success rate
        total_attempts = 0
        successful_attempts = 0
        for result in self.site_results:
            for attempt in result.extraction_attempts:
                total_attempts += 1
                if attempt.success:
                    successful_attempts += 1
        
        if total_attempts > 0:
            stats['overall_success_rate'] = successful_attempts / total_attempts
        
        # Site type distribution
        for result in self.site_results:
            site_type = self.classify_site(result.site_features)
            stats['site_type_distribution'][site_type] += 1
        
        # Recent performance (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_attempts = []
        for result in self.site_results:
            if result.timestamp > week_ago:
                recent_attempts.extend(result.extraction_attempts)
        
        if recent_attempts:
            recent_success_rate = sum(1 for a in recent_attempts if a.success) / len(recent_attempts)
            stats['recent_performance'] = {
                'success_rate': recent_success_rate,
                'attempts_count': len(recent_attempts)
            }
        
        return stats
    
    def save_data(self):
        """Save learning data to file"""
        try:
            with open(self.data_path, 'w') as f:
                # Convert dataclasses to dicts for JSON serialization
                data = {
                    'site_results': [asdict(result) for result in self.site_results],
                    'strategy_performance': dict(self.strategy_performance)
                }
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def load_data(self):
        """Load learning data from file"""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                
                # Convert dicts back to dataclasses
                self.site_results = []
                for result_dict in data.get('site_results', []):
                    # Convert timestamp string back to datetime
                    if 'timestamp' in result_dict:
                        result_dict['timestamp'] = datetime.fromisoformat(result_dict['timestamp'])
                    
                    # Convert extraction attempts
                    attempts = []
                    for attempt_dict in result_dict.get('extraction_attempts', []):
                        if 'timestamp' in attempt_dict:
                            attempt_dict['timestamp'] = datetime.fromisoformat(attempt_dict['timestamp'])
                        
                        # Handle migration from total_time to time_taken
                        if 'total_time' in attempt_dict and 'time_taken' not in attempt_dict:
                            attempt_dict['time_taken'] = attempt_dict.pop('total_time')
                        
                        attempts.append(ExtractionAttempt(**attempt_dict))
                    result_dict['extraction_attempts'] = attempts
                    
                    # Convert site features
                    result_dict['site_features'] = SiteFeatures(**result_dict['site_features'])
                    
                    self.site_results.append(SiteResult(**result_dict))
                
                # Load strategy performance
                self.strategy_performance = defaultdict(lambda: {
                    'success_count': 0, 'total_count': 0, 'total_time': 0.0, 'avg_time': 0.0, 'avg_addresses': 0.0
                })
                for strategy, perf in data.get('strategy_performance', {}).items():
                    # Ensure all required keys exist in loaded data
                    if 'total_time' not in perf:
                        perf['total_time'] = 0.0
                    if 'avg_time' not in perf:
                        perf['avg_time'] = 0.0
                    if 'avg_addresses' not in perf:
                        perf['avg_addresses'] = 0.0
                    self.strategy_performance[strategy] = perf
                
                print(f"Loaded {len(self.site_results)} site results and {len(self.strategy_performance)} strategy performances")
        except Exception as e:
            print(f"Error loading learning data: {e}")
    
    def save_model(self):
        """Save trained model to file"""
        try:
            model_data = {
                'classifier': self.classifier,
                'vectorizer': self.vectorizer,
                'is_trained': self.is_trained
            }
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self):
        """Load trained model from file"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.classifier = model_data['classifier']
                self.vectorizer = model_data['vectorizer']
                self.is_trained = model_data['is_trained']
                
                print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")

# Global instance
ml_extractor = MLAddressExtractor()

def get_ml_extractor() -> MLAddressExtractor:
    """Get the global ML extractor instance"""
    return ml_extractor 