#!/usr/bin/env python3
"""
Enhanced Content Signature Extraction for Onion Scraper
Provides intelligent content analysis and signature extraction for better address detection.
"""

import re
import json
import time
from datetime import datetime
from collections import Counter
import hashlib
    
class EnhancedContentSignatures:
    def __init__(self):
        self.signatures = {}
        self.content_patterns = {}
        self.extraction_methods = []
        self.success_patterns = {}
        self.failure_patterns = {}
        
        self.setup_content_patterns()
        self.setup_extraction_methods()
        self.setup_signature_analysis()
    
    def setup_content_patterns(self):
        """Enhanced content pattern recognition for better address detection"""
        self.content_patterns = {
            'payment_indicators': [
                # Direct payment terms
                r'\b(payment|pay|deposit|fund|wallet|address|crypto|bitcoin|btc|ethereum|eth|monero|xmr)\b',
                # Action words near addresses
                r'\b(send|transfer|deposit|fund|pay|order|checkout|purchase|buy)\b',
                # UI elements
                r'\b(button|click|proceed|continue|next|submit|confirm)\b',
                # Crypto-specific terms
                r'\b(blockchain|transaction|tx|hash|confirmation|network|fee)\b'
            ],
            'address_context_patterns': [
                # Patterns that often precede addresses
                r'(address|wallet|send\s+to|pay\s+to|deposit\s+to|fund\s+with)',
                r'(bitcoin\s+address|btc\s+address|eth\s+address|wallet\s+address)',
                r'(copy\s+address|address\s+below|payment\s+address|receiving\s+address)',
                # JavaScript patterns
                r'(address["\']?\s*[:=]|wallet["\']?\s*[:=]|crypto["\']?\s*[:=])',
                # QR code patterns
                r'(qr\s+code|scan\s+code|qr\s+address)'
            ],
            'dynamic_content_indicators': [
                # JavaScript loading patterns
                r'(loading|please\s+wait|generating|processing)',
                r'(document\.ready|window\.onload|\$\(function)',
                # AJAX patterns
                r'(ajax|fetch|xhr|xmlhttprequest)',
                # React/Vue patterns
                r'(react|vue|angular|component|state)'
            ],
            'form_patterns': [
                # Form elements that might contain addresses
                r'<input[^>]*(?:address|wallet|crypto|payment)[^>]*>',
                r'<textarea[^>]*(?:address|wallet|crypto|payment)[^>]*>',
                r'<select[^>]*(?:crypto|coin|currency)[^>]*>',
                # Hidden form fields
                r'<input[^>]*type=["\']hidden["\'][^>]*(?:address|wallet)[^>]*>'
            ],
            'error_patterns': [
                # Common error indicators
                r'(error|failed|invalid|expired|timeout|blocked)',
                r'(maintenance|unavailable|down|offline)',
                r'(captcha|verification|human|robot)',
                r'(suspended|banned|disabled|restricted)'
            ]
        }
    
    def setup_extraction_methods(self):
        """Setup multiple extraction methods for comprehensive address detection"""
        self.extraction_methods = [
            {
                'name': 'regex_standard',
                'function': self.extract_with_standard_regex,
                'priority': 1,
                'description': 'Standard regex patterns for crypto addresses'
            },
            {
                'name': 'context_aware',
                'function': self.extract_with_context_awareness,
                'priority': 2,
                'description': 'Context-aware extraction using surrounding text'
            },
            {
                'name': 'html_attributes',
                'function': self.extract_from_html_attributes,
                'priority': 3,
                'description': 'Extract addresses from HTML attributes and data fields'
            },
            {
                'name': 'javascript_variables',
                'function': self.extract_from_javascript,
                'priority': 4,
                'description': 'Extract addresses from JavaScript variables and functions'
            },
            {
                'name': 'base64_encoded',
                'function': self.extract_from_encoded_content,
                'priority': 5,
                'description': 'Extract addresses from base64 and other encoded content'
            },
            {
                'name': 'dynamic_content',
                'function': self.extract_from_dynamic_content,
                'priority': 6,
                'description': 'Extract addresses from dynamically loaded content'
            }
        ]
    
    def setup_signature_analysis(self):
        """Setup signature analysis for pattern recognition"""
        self.signature_patterns = {
            'high_success_indicators': [
                'checkout', 'payment', 'order', 'buy', 'purchase',
                'wallet', 'address', 'deposit', 'fund', 'crypto'
            ],
            'medium_success_indicators': [
                'bitcoin', 'btc', 'ethereum', 'eth', 'monero', 'xmr',
                'transaction', 'transfer', 'send', 'receive'
            ],
            'low_success_indicators': [
                'market', 'shop', 'store', 'vendor', 'seller'
            ],
            'failure_indicators': [
                'error', 'failed', 'maintenance', 'offline', 'down',
                'captcha', 'verification', 'blocked', 'banned'
            ]
        }
    
    def analyze_content(self, html_content, url="", title=""):
        """Comprehensive content analysis with enhanced signature extraction"""
        timestamp = datetime.utcnow().isoformat()
        
        analysis = {
            'url': url,
            'title': title,
            'timestamp': timestamp,
            'content_length': len(html_content),
            'signatures': {},
            'extraction_potential': 'unknown',
            'recommended_methods': [],
            'success_probability': 0.0
        }
        
        # Analyze content patterns
        analysis['signatures'] = self.extract_content_signatures(html_content)
        
        # Determine extraction potential
        analysis['extraction_potential'] = self.assess_extraction_potential(analysis['signatures'])
        
        # Recommend extraction methods
        analysis['recommended_methods'] = self.recommend_extraction_methods(analysis['signatures'])
        
        # Calculate success probability
        analysis['success_probability'] = self.calculate_success_probability(analysis['signatures'])
        
        return analysis
    
    def extract_content_signatures(self, html_content):
        """Extract comprehensive content signatures"""
        signatures = {}
        
        # Count pattern occurrences
        for pattern_type, patterns in self.content_patterns.items():
            signatures[pattern_type] = 0
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                signatures[pattern_type] += len(matches)
        
        # Analyze HTML structure
        signatures['html_structure'] = self.analyze_html_structure(html_content)
        
        # Analyze JavaScript presence
        signatures['javascript_analysis'] = self.analyze_javascript_content(html_content)
        
        # Analyze form elements
        signatures['form_analysis'] = self.analyze_form_elements(html_content)
        
        # Analyze text content
        signatures['text_analysis'] = self.analyze_text_content(html_content)
        
        return signatures
    
    def analyze_html_structure(self, html_content):
        """Analyze HTML structure for signature patterns"""
        structure = {
            'has_forms': len(re.findall(r'<form[^>]*>', html_content, re.IGNORECASE)) > 0,
            'has_inputs': len(re.findall(r'<input[^>]*>', html_content, re.IGNORECASE)),
            'has_buttons': len(re.findall(r'<button[^>]*>', html_content, re.IGNORECASE)),
            'has_scripts': len(re.findall(r'<script[^>]*>', html_content, re.IGNORECASE)),
            'has_iframes': len(re.findall(r'<iframe[^>]*>', html_content, re.IGNORECASE)),
            'has_canvas': len(re.findall(r'<canvas[^>]*>', html_content, re.IGNORECASE)),
            'meta_tags': len(re.findall(r'<meta[^>]*>', html_content, re.IGNORECASE))
        }
        
        return structure
    
    def analyze_javascript_content(self, html_content):
        """Analyze JavaScript content for address patterns"""
        js_analysis = {
            'has_jquery': 'jquery' in html_content.lower(),
            'has_ajax': any(term in html_content.lower() for term in ['ajax', 'xhr', 'fetch']),
            'has_crypto_js': any(term in html_content.lower() for term in ['crypto', 'bitcoin', 'ethereum']),
            'dynamic_loading': any(term in html_content.lower() for term in ['loading', 'spinner', 'please wait']),
            'address_variables': len(re.findall(r'(address|wallet|crypto)\s*[:=]', html_content, re.IGNORECASE))
        }
        
        return js_analysis
    
    def analyze_form_elements(self, html_content):
        """Analyze form elements for payment/address patterns"""
        form_analysis = {
            'payment_forms': len(re.findall(r'<form[^>]*(?:payment|checkout|order)[^>]*>', html_content, re.IGNORECASE)),
            'crypto_inputs': len(re.findall(r'<input[^>]*(?:address|wallet|crypto)[^>]*>', html_content, re.IGNORECASE)),
            'hidden_fields': len(re.findall(r'<input[^>]*type=["\']hidden["\']', html_content, re.IGNORECASE)),
            'submit_buttons': len(re.findall(r'<(?:button|input)[^>]*(?:submit|pay|order|buy)[^>]*>', html_content, re.IGNORECASE))
        }
        
        return form_analysis
    
    def analyze_text_content(self, html_content):
        """Analyze text content for crypto-related terms"""
        # Remove HTML tags for text analysis
        text_content = re.sub(r'<[^>]+>', ' ', html_content)
        text_lower = text_content.lower()
        
        text_analysis = {
            'crypto_mentions': sum(text_lower.count(term) for term in ['bitcoin', 'btc', 'ethereum', 'eth', 'monero', 'xmr']),
            'payment_mentions': sum(text_lower.count(term) for term in ['payment', 'pay', 'order', 'checkout', 'buy']),
            'address_mentions': sum(text_lower.count(term) for term in ['address', 'wallet', 'send', 'receive']),
            'action_words': sum(text_lower.count(term) for term in ['click', 'continue', 'proceed', 'next'])
        }
        
        return text_analysis
    
    def assess_extraction_potential(self, signatures):
        """Assess the potential for successful address extraction"""
        score = 0
        
        # Payment indicators (high weight)
        score += signatures.get('payment_indicators', 0) * 3
        
        # Address context patterns (high weight)
        score += signatures.get('address_context_patterns', 0) * 4
        
        # Form analysis (medium weight)
        form_score = sum(signatures.get('form_analysis', {}).values())
        score += form_score * 2
        
        # JavaScript analysis (medium weight)
        js_score = sum(1 for v in signatures.get('javascript_analysis', {}).values() if v)
        score += js_score * 2
        
        # Text analysis (low weight)
        text_score = sum(signatures.get('text_analysis', {}).values())
        score += text_score * 1
        
        # Determine potential level
        if score >= 20:
            return 'high'
        elif score >= 10:
            return 'medium'
        elif score >= 5:
            return 'low'
        else:
            return 'very_low'
    
    def recommend_extraction_methods(self, signatures):
        """Recommend extraction methods based on content signatures"""
        recommendations = []
        
        # Always try standard regex first
        recommendations.append('regex_standard')
        
        # Recommend based on content patterns
        if signatures.get('address_context_patterns', 0) > 0:
            recommendations.append('context_aware')
        
        if signatures.get('html_structure', {}).get('has_forms', False):
            recommendations.append('html_attributes')
        
        if signatures.get('javascript_analysis', {}).get('has_crypto_js', False):
            recommendations.append('javascript_variables')
        
        if signatures.get('dynamic_content_indicators', 0) > 0:
            recommendations.append('dynamic_content')
        
        # Always try encoded content as last resort
        recommendations.append('base64_encoded')
        
        return recommendations
    
    def calculate_success_probability(self, signatures):
        """Calculate probability of successful address extraction"""
        base_probability = 0.1  # 10% base probability
        
        # Add probability based on positive indicators
        payment_boost = min(signatures.get('payment_indicators', 0) * 0.05, 0.3)
        context_boost = min(signatures.get('address_context_patterns', 0) * 0.08, 0.4)
        form_boost = min(sum(signatures.get('form_analysis', {}).values()) * 0.03, 0.2)
        
        # Subtract probability based on negative indicators
        error_penalty = min(signatures.get('error_patterns', 0) * 0.1, 0.5)
        
        probability = base_probability + payment_boost + context_boost + form_boost - error_penalty
        
        return max(0.0, min(1.0, probability))
    
    # Extraction method implementations
    def extract_with_standard_regex(self, html_content):
        """Standard regex extraction"""
        addresses = []
        patterns = {
            'BTC': r'\b(bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})\b',
            'ETH': r'\b0x[a-fA-F0-9]{40}\b',
            'XMR': r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b',
            'TRON': r'\bT[1-9A-HJ-NP-Za-km-z]{33}\b',
            'SOL': r'\b[1-9A-HJ-NP-Za-km-z]{44}\b'
        }
        
        for chain, pattern in patterns.items():
            matches = re.findall(pattern, html_content)
            for match in matches:
                addresses.append({'chain': chain, 'address': match, 'method': 'regex_standard'})
        
        return addresses
    
    def extract_with_context_awareness(self, html_content):
        """Context-aware extraction using surrounding text"""
        addresses = []
        
        # Look for addresses near payment-related terms
        context_patterns = [
            r'(payment|pay|send|deposit|wallet|address)\s*:?\s*([a-zA-Z0-9]{25,95})',
            r'([a-zA-Z0-9]{25,95})\s*(?:payment|pay|send|deposit|wallet|address)',
            r'(bitcoin|btc|ethereum|eth)\s*:?\s*([a-zA-Z0-9]{25,95})'
        ]
        
        for pattern in context_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                potential_address = match[1] if len(match) > 1 else match[0]
                if self.validate_address_format(potential_address):
                    chain = self.detect_address_chain(potential_address)
                    if chain:
                        addresses.append({'chain': chain, 'address': potential_address, 'method': 'context_aware'})
        
        return addresses
    
    def extract_from_html_attributes(self, html_content):
        """Extract addresses from HTML attributes"""
        addresses = []
        
        # Look for addresses in data attributes, values, etc.
        attribute_patterns = [
            r'data-address=["\']([^"\']+)["\']',
            r'data-wallet=["\']([^"\']+)["\']',
            r'value=["\']([a-zA-Z0-9]{25,95})["\']',
            r'content=["\']([a-zA-Z0-9]{25,95})["\']'
        ]
        
        for pattern in attribute_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if self.validate_address_format(match):
                    chain = self.detect_address_chain(match)
                    if chain:
                        addresses.append({'chain': chain, 'address': match, 'method': 'html_attributes'})
        
        return addresses
    
    def extract_from_javascript(self, html_content):
        """Extract addresses from JavaScript variables and functions"""
        addresses = []
        
        # Look for addresses in JavaScript variables
        js_patterns = [
            r'(address|wallet|crypto)\s*[:=]\s*["\']([a-zA-Z0-9]{25,95})["\']',
            r'var\s+(address|wallet)\s*=\s*["\']([a-zA-Z0-9]{25,95})["\']',
            r'(bitcoin|btc|ethereum|eth)\s*[:=]\s*["\']([a-zA-Z0-9]{25,95})["\']'
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                potential_address = match[1] if len(match) > 1 else match[0]
                if self.validate_address_format(potential_address):
                    chain = self.detect_address_chain(potential_address)
                    if chain:
                        addresses.append({'chain': chain, 'address': potential_address, 'method': 'javascript_variables'})
        
        return addresses
    
    def extract_from_encoded_content(self, html_content):
        """Extract addresses from base64 and other encoded content"""
        addresses = []
        
        # Look for base64 encoded content that might contain addresses
        import base64
        
        base64_pattern = r'([A-Za-z0-9+/]{20,}={0,2})'
        matches = re.findall(base64_pattern, html_content)
        
        for match in matches:
            try:
                decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
                # Recursively search decoded content
                sub_addresses = self.extract_with_standard_regex(decoded)
                for addr in sub_addresses:
                    addr['method'] = 'base64_encoded'
                    addresses.append(addr)
            except:
                continue
        
        return addresses
    
    def extract_from_dynamic_content(self, html_content):
        """Extract addresses from dynamic content indicators"""
        addresses = []
        
        # Look for AJAX endpoints or dynamic loading patterns
        dynamic_patterns = [
            r'url\s*:\s*["\']([^"\']*address[^"\']*)["\']',
            r'endpoint\s*:\s*["\']([^"\']*wallet[^"\']*)["\']',
            r'api\s*:\s*["\']([^"\']*crypto[^"\']*)["\']'
        ]
        
        # This method would need actual dynamic content execution
        # For now, just return empty list as placeholder
        return addresses
    
    def validate_address_format(self, address):
        """Basic validation of address format"""
        if not address or len(address) < 25:
            return False
        
        # Basic character set validation
        if not re.match(r'^[a-zA-Z0-9]+$', address):
            return False
        
        return True
    
    def detect_address_chain(self, address):
        """Detect which blockchain the address belongs to"""
        if address.startswith('bc1') or address.startswith('1') or address.startswith('3'):
            return 'BTC'
        elif address.startswith('0x') and len(address) == 42:
            return 'ETH'
        elif address.startswith('4') and len(address) == 95:
            return 'XMR'
        elif address.startswith('T') and len(address) == 34:
            return 'TRON'
        elif len(address) == 44:
            return 'SOL'
        
        return None
    
    def get_signature_statistics(self):
        """Get signature extraction statistics"""
        return {
            'total_signatures': len(self.signatures),
            'success_patterns': len(self.success_patterns),
            'failure_patterns': len(self.failure_patterns),
            'extraction_methods': len(self.extraction_methods)
        }

# Global instance
enhanced_content_signatures = EnhancedContentSignatures()

def analyze_page_content(html_content, url="", title=""):
    """Main content analysis function"""
    return enhanced_content_signatures.analyze_content(html_content, url, title)

def extract_addresses_comprehensive(html_content):
    """Comprehensive address extraction using all methods"""
    all_addresses = []
    
    for method in enhanced_content_signatures.extraction_methods:
        try:
            addresses = method['function'](html_content)
            all_addresses.extend(addresses)
        except Exception as e:
            print(f"⚠️ Extraction method {method['name']} failed: {e}")
    
    # Remove duplicates while preserving method information
    unique_addresses = []
    seen = set()
    
    for addr in all_addresses:
        key = f"{addr['chain']}:{addr['address']}"
        if key not in seen:
            seen.add(key)
            unique_addresses.append(addr)
    
    return unique_addresses

def get_content_signature_stats():
    """Get content signature statistics"""
    return enhanced_content_signatures.get_signature_statistics()
