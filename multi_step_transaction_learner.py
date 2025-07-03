#!/usr/bin/env python3
"""
Multi-Step Transaction Learning System
Learns from transaction patterns and applies knowledge to similar cases.
"""

import json
import time
import re
from datetime import datetime
from collections import defaultdict
import hashlib

class TransactionPatternLearner:
    def __init__(self):
        self.patterns = {}
        self.success_sequences = []
        self.failure_sequences = []
        self.interaction_templates = {}
        self.site_behaviors = {}
        
        # Load existing patterns
        self.load_learned_patterns()
        
        # Define common transaction flow patterns
        self.setup_base_patterns()
    
    def setup_base_patterns(self):
        """Setup base transaction patterns to recognize"""
        self.base_patterns = {
            'card_marketplace': {
                'triggers': [
                    r'(?i)(buy\s+cards?|purchase\s+cards?|order\s+cards?)',
                    r'(?i)(visa|mastercard|amex)\s*\$?\d+',
                    r'(?i)price\s*\$\d+',
                    r'(?i)(learn\s+more|more\s+info|details)'
                ],
                'flow_steps': [
                    'product_catalog',      # Browse available cards
                    'product_selection',    # Click on specific card/price
                    'details_modal',        # Learn more / details popup
                    'price_confirmation',   # Confirm price selection
                    'form_filling',         # Fill checkout form
                    'payment_address'       # Get crypto payment address
                ],
                'success_indicators': [
                    'checkout', 'payment', 'address', 'bitcoin', 'total', 'order'
                ],
                'interaction_patterns': {
                    'button_clicks': [
                        r'(?i)(buy|purchase|order|select|choose)',
                        r'(?i)(learn\s+more|more\s+info|details)',
                        r'(?i)(continue|proceed|next|confirm)'
                    ],
                    'form_elements': [
                        'name', 'email', 'address', 'phone', 'country'
                    ],
                    'modal_triggers': [
                        'data-toggle="modal"',
                        'data-target',
                        'modal-',
                        'popup'
                    ]
                }
            },
            'service_marketplace': {
                'triggers': [
                    r'(?i)(buy\s+service|purchase\s+service|hire)',
                    r'(?i)(price|cost|fee)\s*\$?\d+',
                    r'(?i)(consultation|service|work)'
                ],
                'flow_steps': [
                    'service_catalog',
                    'service_selection',
                    'requirements_form',
                    'price_quote',
                    'payment_form',
                    'payment_address'
                ],
                'success_indicators': [
                    'quote', 'estimate', 'payment', 'deposit', 'escrow'
                ]
            },
            'digital_goods': {
                'triggers': [
                    r'(?i)(download|digital|software|access)',
                    r'(?i)(license|key|code|account)',
                    r'(?i)(instant|immediate|download)'
                ],
                'flow_steps': [
                    'product_listing',
                    'product_selection',
                    'license_options',
                    'checkout_form',
                    'payment_address'
                ],
                'success_indicators': [
                    'download', 'access', 'license', 'key', 'account'
                ]
            }
        }
    
    def _strip_inline_flags(self, pattern):
        """Remove inline (?i) flags and return cleaned pattern"""
        return pattern.replace('(?i)', '')
    
    def analyze_page_for_patterns(self, html_content, url, title=""):
        """Analyze page content to identify transaction patterns"""
        analysis = {
            'url': url,
            'title': title,
            'timestamp': datetime.utcnow().isoformat(),
            'detected_patterns': [],
            'flow_step': 'unknown',
            'interaction_opportunities': [],
            'learning_data': {}
        }
        
        # Detect pattern types
        for pattern_name, pattern_data in self.base_patterns.items():
            if self.matches_pattern(html_content, pattern_data['triggers']):
                analysis['detected_patterns'].append(pattern_name)
                
                # Determine current flow step
                flow_step = self.identify_flow_step(html_content, pattern_data)
                if flow_step:
                    analysis['flow_step'] = flow_step
                
                # Find interaction opportunities
                interactions = self.find_interaction_opportunities(html_content, pattern_data)
                analysis['interaction_opportunities'].extend(interactions)
        
        # Extract learning data
        analysis['learning_data'] = self.extract_learning_data(html_content)
        
        return analysis
    
    def matches_pattern(self, html_content, triggers):
        """Check if content matches pattern triggers"""
        content_lower = html_content  # We'll use IGNORECASE regex instead
        
        for trigger in triggers:
            cleaned = self._strip_inline_flags(trigger)
            if re.search(cleaned, content_lower, re.IGNORECASE):
                return True
        return False
    
    def identify_flow_step(self, html_content, pattern_data):
        """Identify which step in the transaction flow we're at"""
        content_lower = html_content  # We'll use IGNORECASE regex
        
        # Check for specific flow step indicators
        flow_indicators = {
            'product_catalog': [
                r'(catalog|products|items|cards|services)',
                r'class=["\"][^"\']*catalog[^"\']*["\"]',
                r'multiple.*price.*options'
            ],
            'product_selection': [
                r'(select|choose|pick).*product',
                r'price.*\$\d+.*buy',
                r'data-toggle=["\']modal["\']'
            ],
            'details_modal': [
                r'modal.*fade.*in',
                r'learn\s+more.*details',
                r'modal-title.*order'
            ],
            'form_filling': [
                r'<form.*action.*checkout',
                r'<form.*action.*payment',
                r'name.*email.*required'
            ],
            'payment_address': [
                r'(bitcoin|btc|ethereum|eth).*address',
                r'send.*payment.*to',
                r'wallet.*address'
            ]
        }
        
        for step, indicators in flow_indicators.items():
            for indicator in indicators:
                cleaned = self._strip_inline_flags(indicator)
                if re.search(cleaned, content_lower, re.IGNORECASE):
                    return step
        
        return 'unknown'
    
    def find_interaction_opportunities(self, html_content, pattern_data):
        """Find specific interaction opportunities on the page"""
        opportunities = []
        
        # Find clickable elements
        button_patterns = pattern_data.get('interaction_patterns', {}).get('button_clicks', [])
        for pattern in button_patterns:
            cleaned = self._strip_inline_flags(pattern)
            buttons = re.findall(r'<(?:button|input)[^>]*(?:value|>)[^<]*' + cleaned + r'[^<]*', html_content, re.IGNORECASE)
            for button in buttons:
                opportunities.append({
                    'type': 'button_click',
                    'element': button,
                    'pattern': pattern,
                    'priority': 'high'
                })
        
        # Find modal triggers
        modal_patterns = pattern_data.get('interaction_patterns', {}).get('modal_triggers', [])
        for pattern in modal_patterns:
            cleaned = self._strip_inline_flags(pattern)
            modals = re.findall(r'<[^>]*' + cleaned + r'[^>]*>', html_content, re.IGNORECASE)
            for modal in modals:
                opportunities.append({
                    'type': 'modal_trigger',
                    'element': modal,
                    'pattern': pattern,
                    'priority': 'high'
                })
        
        # Find forms
        forms = re.findall(r'<form[^>]*action[^>]*>.*?</form>', html_content, re.IGNORECASE | re.DOTALL)
        for form in forms:
            if any(keyword in form.lower() for keyword in ['checkout', 'payment', 'order', 'buy']):
                opportunities.append({
                    'type': 'form_submission',
                    'element': form[:200] + '...' if len(form) > 200 else form,
                    'pattern': 'checkout_form',
                    'priority': 'very_high'
                })
        
        # Find price selection elements
        price_selects = re.findall(r'<select[^>]*>.*?</select>', html_content, re.IGNORECASE | re.DOTALL)
        for select in price_selects:
            if re.search(r'\$\d+', select):
                opportunities.append({
                    'type': 'price_selection',
                    'element': select[:200] + '...' if len(select) > 200 else select,
                    'pattern': 'price_dropdown',
                    'priority': 'high'
                })
        
        return opportunities
    
    def extract_learning_data(self, html_content):
        """Extract data that can be used for learning"""
        learning_data = {
            'form_patterns': [],
            'button_patterns': [],
            'modal_patterns': [],
            'price_patterns': [],
            'navigation_patterns': []
        }
        
        # Extract form patterns
        forms = re.findall(r'<form[^>]*>.*?</form>', html_content, re.IGNORECASE | re.DOTALL)
        for form in forms:
            form_data = {
                'action': re.search(r'action=["\']([^"\']*)["\']', form, re.IGNORECASE),
                'method': re.search(r'method=["\']([^"\']*)["\']', form, re.IGNORECASE),
                'inputs': len(re.findall(r'<input[^>]*>', form, re.IGNORECASE)),
                'has_hidden_fields': 'type="hidden"' in form.lower(),
                'has_required_fields': 'required' in form.lower()
            }
            learning_data['form_patterns'].append(form_data)
        
        # Extract button patterns
        buttons = re.findall(r'<(?:button|input)[^>]*(?:type=["\'](?:button|submit)["\']|>)[^<]*', html_content, re.IGNORECASE)
        for button in buttons:
            button_data = {
                'text': re.search(r'(?:value=["\']([^"\']*)["\']|>([^<]*)<)', button, re.IGNORECASE),
                'classes': re.search(r'class=["\']([^"\']*)["\']', button, re.IGNORECASE),
                'data_attributes': len(re.findall(r'data-[^=]*=', button, re.IGNORECASE))
            }
            learning_data['button_patterns'].append(button_data)
        
        # Extract price patterns
        prices = re.findall(r'\$\d+(?:\.\d{2})?', html_content)
        learning_data['price_patterns'] = list(set(prices))
        
        return learning_data
    
    def learn_from_interaction(self, interaction_sequence, success=True):
        """Learn from a completed interaction sequence"""
        sequence_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'steps': interaction_sequence,
            'success': success,
            'pattern_hash': self.generate_sequence_hash(interaction_sequence)
        }
        
        if success:
            self.success_sequences.append(sequence_data)
            print(f"✅ Learned successful sequence: {len(interaction_sequence)} steps")
        else:
            self.failure_sequences.append(sequence_data)
            print(f"❌ Learned failed sequence: {len(interaction_sequence)} steps")
        
        # Update pattern knowledge
        self.update_pattern_knowledge(sequence_data)
        
        # Save learned patterns
        self.save_learned_patterns()
    
    def generate_sequence_hash(self, sequence):
        """Generate a hash for the interaction sequence"""
        sequence_str = json.dumps(sequence, sort_keys=True)
        return hashlib.md5(sequence_str.encode()).hexdigest()[:8]
    
    def update_pattern_knowledge(self, sequence_data):
        """Update pattern knowledge based on interaction results"""
        pattern_hash = sequence_data['pattern_hash']
        
        if pattern_hash not in self.patterns:
            self.patterns[pattern_hash] = {
                'success_count': 0,
                'failure_count': 0,
                'steps': sequence_data['steps'],
                'success_rate': 0.0,
                'last_used': sequence_data['timestamp']
            }
        
        pattern = self.patterns[pattern_hash]
        
        if sequence_data['success']:
            pattern['success_count'] += 1
        else:
            pattern['failure_count'] += 1
        
        total_attempts = pattern['success_count'] + pattern['failure_count']
        pattern['success_rate'] = pattern['success_count'] / total_attempts
        pattern['last_used'] = sequence_data['timestamp']
    
    def recommend_interaction_sequence(self, page_analysis):
        """Recommend interaction sequence based on learned patterns"""
        recommendations = []
        
        # Check for known successful patterns
        for pattern_hash, pattern_data in self.patterns.items():
            if pattern_data['success_rate'] > 0.5:  # Only recommend patterns with >50% success rate
                recommendations.append({
                    'sequence': pattern_data['steps'],
                    'confidence': pattern_data['success_rate'],
                    'usage_count': pattern_data['success_count'] + pattern_data['failure_count'],
                    'pattern_hash': pattern_hash
                })
        
        # Sort by confidence and usage
        recommendations.sort(key=lambda x: (x['confidence'], x['usage_count']), reverse=True)
        
        # Generate new recommendations based on page analysis
        if page_analysis['detected_patterns']:
            for pattern_name in page_analysis['detected_patterns']:
                if pattern_name in self.base_patterns:
                    base_sequence = self.generate_base_sequence(page_analysis, pattern_name)
                    recommendations.append({
                        'sequence': base_sequence,
                        'confidence': 0.3,  # Lower confidence for untested sequences
                        'usage_count': 0,
                        'pattern_hash': 'new_' + pattern_name
                    })
        
        return recommendations[:3]  # Return top 3 recommendations
    
    def generate_base_sequence(self, page_analysis, pattern_name):
        """Generate a base interaction sequence for a pattern"""
        pattern_data = self.base_patterns[pattern_name]
        flow_step = page_analysis['flow_step']
        
        sequence = []
        
        # Add steps based on current flow position
        if flow_step == 'product_catalog':
            sequence.extend([
                {'action': 'find_product', 'target': 'price_selection'},
                {'action': 'click_button', 'pattern': r'(?i)(buy|select|choose)'},
                {'action': 'wait_for_modal', 'timeout': 5},
                {'action': 'fill_form', 'form_type': 'checkout'},
                {'action': 'submit_form', 'wait_for': 'payment_address'}
            ])
        elif flow_step == 'details_modal':
            sequence.extend([
                {'action': 'select_price_option', 'target': 'highest_value'},
                {'action': 'click_continue', 'pattern': r'(?i)(continue|proceed|next)'},
                {'action': 'fill_form', 'form_type': 'checkout'},
                {'action': 'submit_form', 'wait_for': 'payment_address'}
            ])
        elif flow_step == 'form_filling':
            sequence.extend([
                {'action': 'fill_form', 'form_type': 'checkout'},
                {'action': 'submit_form', 'wait_for': 'payment_address'}
            ])
        
        return sequence
    
    def save_learned_patterns(self):
        """Save learned patterns to file"""
        data = {
            'patterns': self.patterns,
            'success_sequences': self.success_sequences[-50:],  # Keep last 50
            'failure_sequences': self.failure_sequences[-50:],  # Keep last 50
            'last_updated': datetime.utcnow().isoformat()
        }
        
        try:
            with open('learned_transaction_patterns.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save learned patterns: {e}")
    
    def load_learned_patterns(self):
        """Load previously learned patterns"""
        try:
            with open('learned_transaction_patterns.json', 'r') as f:
                data = json.load(f)
                self.patterns = data.get('patterns', {})
                self.success_sequences = data.get('success_sequences', [])
                self.failure_sequences = data.get('failure_sequences', [])
                print(f"📚 Loaded {len(self.patterns)} learned patterns")
        except FileNotFoundError:
            print("📚 No existing learned patterns found, starting fresh")
        except Exception as e:
            print(f"⚠️ Failed to load learned patterns: {e}")
    
    def get_learning_statistics(self):
        """Get statistics about learned patterns"""
        total_patterns = len(self.patterns)
        successful_patterns = sum(1 for p in self.patterns.values() if p['success_rate'] > 0.5)
        total_interactions = len(self.success_sequences) + len(self.failure_sequences)
        
        return {
            'total_patterns': total_patterns,
            'successful_patterns': successful_patterns,
            'success_rate': successful_patterns / total_patterns if total_patterns > 0 else 0,
            'total_interactions': total_interactions,
            'recent_successes': len([s for s in self.success_sequences[-10:]]),
            'recent_failures': len([s for s in self.failure_sequences[-10:]])
        }

# Global instance
transaction_learner = TransactionPatternLearner()

def analyze_transaction_patterns(html_content, url, title=""):
    """Main function to analyze page for transaction patterns"""
    return transaction_learner.analyze_page_for_patterns(html_content, url, title)

def learn_from_transaction(interaction_sequence, success=True):
    """Learn from a completed transaction interaction"""
    return transaction_learner.learn_from_interaction(interaction_sequence, success)

def get_interaction_recommendations(page_analysis):
    """Get recommended interaction sequence for a page"""
    return transaction_learner.recommend_interaction_sequence(page_analysis)

def get_transaction_learning_stats():
    """Get learning system statistics"""
    return transaction_learner.get_learning_statistics() 