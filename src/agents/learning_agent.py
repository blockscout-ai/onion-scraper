# Learning Agent Module
import os
import hashlib
import threading
import json
import random
import string
import base64

from datetime import datetime, timedelta
from urllib.parse import urlparse
from collections import defaultdict
from io import BytesIO
from bs4 import BeautifulSoup
from config import OPENAI_API_KEY, ANTHROPIC_API_KEY

# ---[ Load Environment Variables ]---
def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment variables before importing other modules
load_env_file()

# AI imports
try:
    from openai import OpenAI
    import anthropic
    AI_ENABLED = True
    print("🤖 AI capabilities enabled for learning agent")
except ImportError as e:
    print(f"⚠️ AI capabilities disabled: {e}")
    AI_ENABLED = False

# Initialize OpenAI client if key is available
openai_client = None
if AI_ENABLED and OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
if AI_ENABLED and ANTHROPIC_API_KEY:
    anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# AI models for different tasks
AI_MODELS = {
    'gpt4': 'gpt-4',
    'gpt4_vision': 'gpt-4o', 
    'gpt35': 'gpt-3.5-turbo',
    'claude': 'claude-3-sonnet-20240229'
}

class LearningAgent:
    """Enhanced learning agent with AI capabilities for darknet interactions"""
    
    def __init__(self, knowledge_file="knowledge_base.json"):
        self.knowledge_file = knowledge_file
        self.site_patterns = {}
        self.failure_patterns = defaultdict(list)
        self.strategy_success_rates = defaultdict(lambda: defaultdict(list))
        self.content_signatures = {}
        self.adaptation_rules = {}
        self.darknet_patterns = {}  # Darknet-specific patterns
        self.captcha_solutions = {}  # Captcha solution history
        self.form_patterns = {}     # Form interaction patterns
        self.lock = threading.Lock()
        
        # Expose AI capabilities
        self.AI_ENABLED = AI_ENABLED
        self.OPENAI_API_KEY = OPENAI_API_KEY
        self.ANTHROPIC_API_KEY = ANTHROPIC_API_KEY
        self.openai_client = openai_client  # Use the global client
        
        # Load existing knowledge
        self.load_knowledge_base()
        
        # Strategy definitions
        self.strategies = {
            1: "basic_scrape",
            2: "ai_enhanced_scrape", 
            3: "visual_captcha_scrape",
            4: "js_interactive_scrape",
            5: "custom_site_scrape",
            6: "darknet_registration_scrape",  # New: Darknet registration focus
            7: "darknet_login_scrape",         # New: Darknet login focus
            8: "darknet_payment_scrape",       # New: Darknet payment focus
            9: "ai_captcha_solver",            # New: AI-powered captcha solving
            10: "darknet_marketplace_scrape"   # New: Marketplace-specific
        }
        
        # Darknet-specific content patterns
        self.darknet_indicators = {
            'marketplace': ['vendor', 'listing', 'product', 'shop', 'store', 'market'],
            'registration': ['signup', 'register', 'join', 'create account', 'new user'],
            'login': ['signin', 'login', 'access', 'enter', 'username', 'password'],
            'payment': ['bitcoin', 'btc', 'eth', 'crypto', 'wallet', 'payment', 'checkout'],
            'captcha': ['captcha', 'verification', 'robot', 'human', 'prove'],
            'security': ['pgp', 'encryption', 'secure', 'private', 'anonymous'],
            'illegal_services': ['hack', 'card', 'drug', 'weapon', 'fake', 'counterfeit']
        }
        
        print("🤖 Learning Agent initialized")
    
    def extract_url_pattern(self, url):
        """Extract pattern from URL for learning"""
        try:
            parsed = urlparse(url)
            # Create a pattern based on URL structure
            path_parts = parsed.path.split('/')
            pattern = {
                'domain': parsed.netloc,
                'path_depth': len(path_parts),
                'has_query': bool(parsed.query),
                'has_fragment': bool(parsed.fragment),
                'path_keywords': [part for part in path_parts if len(part) > 3],
                'is_onion': parsed.netloc.endswith('.onion'),
                'has_market_keywords': any(word in url.lower() for word in ['market', 'shop', 'store', 'vendor']),
                'has_auth_keywords': any(word in url.lower() for word in ['login', 'register', 'signup', 'auth'])
            }
            return pattern
        except Exception as e:
            return {'domain': 'unknown', 'error': str(e)}
    
    def extract_content_signatures(self, html_content):
        """Enhanced content signature extraction for darknet sites"""
        try:
            # Create a hash of the content structure
            content_hash = hashlib.md5(html_content.encode()).hexdigest()[:16]
            
            # Basic content features
            signatures = {
                'hash': content_hash,
                'length': len(html_content),
                'has_forms': 'form' in html_content.lower(),
                'has_captcha': any(word in html_content.lower() for word in ['captcha', 'verification', 'robot']),
                'has_login': any(word in html_content.lower() for word in ['login', 'signin', 'username', 'password']),
                'has_payment': any(word in html_content.lower() for word in ['payment', 'checkout', 'buy', 'order']),
                'has_crypto': any(word in html_content.lower() for word in ['bitcoin', 'btc', 'eth', 'crypto', 'wallet']),
                'js_heavy': html_content.count('script') > 5,
                'dynamic_content': html_content.count('ajax') > 0 or html_content.count('fetch') > 0
            }
            
            # Darknet-specific features
            darknet_features = {}
            for category, keywords in self.darknet_indicators.items():
                darknet_features[f'darknet_{category}'] = any(
                    keyword in html_content.lower() for keyword in keywords
                )
            
            signatures.update(darknet_features)
            
            # Form analysis
            form_analysis = self.analyze_forms(html_content)
            signatures.update(form_analysis)
            
            return signatures
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_forms(self, html_content):
        """Analyze forms for darknet-specific patterns"""
        try:
            form_analysis = {
                'form_count': html_content.count('<form'),
                'input_count': html_content.count('<input'),
                'has_username_field': any(word in html_content.lower() for word in ['name="username"', 'id="username"', 'placeholder="username"']),
                'has_password_field': any(word in html_content.lower() for word in ['type="password"', 'name="password"', 'id="password"']),
                'has_email_field': any(word in html_content.lower() for word in ['type="email"', 'name="email"', 'id="email"']),
                'has_captcha_field': any(word in html_content.lower() for word in ['name="captcha"', 'id="captcha"', 'class="captcha"']),
                'has_pgp_field': any(word in html_content.lower() for word in ['pgp', 'public key', 'encryption']),
                'has_bitcoin_field': any(word in html_content.lower() for word in ['bitcoin', 'btc', 'wallet', 'address']),
                'has_invite_field': any(word in html_content.lower() for word in ['invite', 'referral', 'code']),
                'has_telegram_field': any(word in html_content.lower() for word in ['telegram', 'signal', 'wickr']),
                'has_age_field': any(word in html_content.lower() for word in ['age', 'birth', 'year']),
                'has_country_field': any(word in html_content.lower() for word in ['country', 'location', 'region'])
            }
            return form_analysis
        except Exception as e:
            return {'form_analysis_error': str(e)}
    
    def ai_analyze_page_content(self, html_content, url):
        """Use AI to analyze page content for darknet-specific patterns"""
        if not self.AI_ENABLED:
            return {'page_type': 'unknown', 'content_type': 'unknown'}
        
        # Handle empty or whitespace-only HTML content
        if not html_content or not html_content.strip():
            print("⚠️ Skipping AI analysis: empty HTML content.")
            return {'page_type': 'unknown', 'content_type': 'unknown'}
        
        try:
            # More aggressive content truncation to prevent token limit issues
            # Extract only text content and limit to 2000 characters
            
            # Parse HTML and extract text content only
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content and clean it
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = ' '.join(chunk for chunk in chunks if chunk)
            
            # Truncate to 2000 characters to stay well under token limits
            content_preview = text_content[:2000]
            
            if len(text_content) > 2000:
                print(f"⚠️ Content truncated from {len(text_content)} to 2000 characters for AI analysis")
            
            system_message = "You are a helpful assistant that analyzes provided text content and always returns a JSON object with the fields: page_type, required_interactions, recommended_strategy, darknet_patterns. If you cannot determine a value, use 'unknown'. Do not mention browsing, URLs, or safety limitations."
            user_message = f"Analyze the following text content and return a JSON object with the fields: page_type, required_interactions, recommended_strategy, darknet_patterns. If you cannot determine a value, use 'unknown'. Content: {content_preview}"

            ai_response = None

            if self.OPENAI_API_KEY:
                response = self.openai_client.chat.completions.create(
                    model=AI_MODELS['gpt4'],
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                ai_response = response.choices[0].message.content
            elif self.ANTHROPIC_API_KEY:
                response = anthropic_client.messages.create(
                    model=AI_MODELS['claude'],
                    max_tokens=300,
                    temperature=0.3,
                    messages=[{"role": "user", "content": user_message}]
                )
                ai_response = response.content[0].text
            
            # Safely parse JSON response - ai_response is a string, not a dict
            if ai_response:
                try:
                    return json.loads(ai_response)
                except json.JSONDecodeError:
                    print(f"⚠️ AI returned invalid JSON: {ai_response[:100]}...")
                    return {'page_type': 'unknown', 'content_type': 'unknown'}
            else:
                return {'page_type': 'unknown', 'content_type': 'unknown'}
                
        except Exception as e:
            print(f"⚠️ AI page analysis failed: {e}")
            return {'page_type': 'unknown', 'content_type': 'unknown'}
    
    def ai_solve_captcha(self, captcha_image):
        """Use AI to solve captchas"""
        if not self.AI_ENABLED:
            return None
        
        try:
            # Convert image to base64
            buffered = BytesIO()
            captcha_image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            
            prompt = """
            This is a captcha from a darknet site. Please read the text and return only the captcha code.
            Focus on the text characters, ignore any background noise or decorative elements.
            """
            
            if self.OPENAI_API_KEY:
                response = self.openai_client.chat.completions.create(
                    model=AI_MODELS['gpt4_vision'],
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
                        ]}
                    ],
                    max_tokens=10
                )
                return response.choices[0].message.content.strip()
            elif self.ANTHROPIC_API_KEY:
                response = anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=10,
                    temperature=0.3,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}}
                        ]
                    }]
                )
                return response.content[0].text.strip()
                
        except Exception as e:
            print(f"⚠️ AI captcha solving failed: {e}")
            return None
    
    def ai_generate_darknet_credentials(self, site_type="general"):
        """Use AI to generate realistic darknet credentials"""
        if not self.AI_ENABLED:
            return self.generate_fallback_credentials()
        
        try:
            prompts = {
                "marketplace": "Generate realistic darknet marketplace credentials. Include username, password, email, PGP key, and Bitcoin address. Make it look like a real darknet user.",
                "forum": "Generate realistic darknet forum credentials. Include username, password, email, and any required fields for forum registration.",
                "vendor": "Generate realistic darknet vendor credentials. Include business name, contact info, PGP key, and payment addresses.",
                "general": "Generate realistic darknet site credentials. Include username, password, email, and any common required fields."
            }
            
            prompt = prompts.get(site_type, prompts["general"])
            
            if self.OPENAI_API_KEY:
                response = self.openai_client.chat.completions.create(
                    model=AI_MODELS['gpt35'],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content
                try:
                    return json.loads(ai_response)
                except json.JSONDecodeError:
                    return self.generate_fallback_credentials()
            elif self.ANTHROPIC_API_KEY:
                response = anthropic_client.messages.create(
                    model=AI_MODELS['claude'],
                    max_tokens=200,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_response = response.content[0].text
                try:
                    return json.loads(ai_response)
                except json.JSONDecodeError:
                    return self.generate_fallback_credentials()
                
        except Exception as e:
            print(f"⚠️ AI credential generation failed: {e}")
            return self.generate_fallback_credentials()
    
    def generate_fallback_credentials(self):
        """Fallback credential generation without AI"""
        
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        password = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%^&*', k=14))
        email = username + '@protonmail.com'
        btc_address = '1' + ''.join(random.choices(string.ascii_letters + string.digits, k=33))
        pgp_key = '-----BEGIN PGP PUBLIC KEY BLOCK-----\n' + ''.join(random.choices(string.ascii_letters + string.digits, k=100)) + '\n-----END PGP PUBLIC KEY BLOCK-----'
        
        return {
            'username': username,
            'password': password,
            'email': email,
            'btc_address': btc_address,
            'pgp_key': pgp_key,
            'telegram': '@' + username,
            'age': str(random.randint(18, 45)),
            'country': random.choice(['USA', 'UK', 'Germany', 'Canada', 'Australia'])
        }
    
    def ai_analyze_form_fields(self, form_html):
        """Use AI to analyze form fields and suggest filling strategy"""
        if not self.AI_ENABLED:
            return {}
        
        try:
            # Truncate form HTML to prevent token limit issues
            form_preview = form_html[:1500]  # Reduced from 2000 to 1500
            
            prompt = f"""
            Analyze this darknet form and identify:
            1. What each field is for (username, password, email, etc.)
            2. What type of data should be entered
            3. Any special requirements or patterns
            
            Form HTML: {form_preview}
            
            Return as JSON with field mappings and suggestions.
            """
            
            if self.OPENAI_API_KEY:
                response = self.openai_client.chat.completions.create(
                    model=AI_MODELS['gpt4'],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.3
                )
                ai_response = response.choices[0].message.content
                try:
                    return json.loads(ai_response)
                except json.JSONDecodeError:
                    return {}
            elif self.ANTHROPIC_API_KEY:
                response = anthropic_client.messages.create(
                    model=AI_MODELS['claude'],
                    max_tokens=300,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                ai_response = response.content[0].text
                try:
                    return json.loads(ai_response)
                except json.JSONDecodeError:
                    return {}
                
        except Exception as e:
            print(f"⚠️ AI form analysis failed: {e}")
            return {}
    
    def learn_from_failure(self, url, error_type, page_content, strategy_attempted, worker_id, stage="extracted_address", addresses_found=None):
        """Enhanced failure learning with pattern recognition"""
        try:
            with self.lock:
                # Extract URL pattern
                url_pattern = self.extract_url_pattern(url)
                
                # Extract content signatures
                content_signatures = self.extract_content_signatures(page_content) if page_content else {}
                
                # Create failure record
                failure_record = {
                    'url': url,
                    'url_pattern': url_pattern,
                    'content_signatures': content_signatures,
                    'error_type': error_type,
                    'strategy_attempted': strategy_attempted,
                    'worker_id': worker_id,
                    'stage': stage,
                    'timestamp': datetime.utcnow().isoformat(),
                    'addresses_found': addresses_found or 0
                }
                
                # Store failure pattern
                if error_type not in self.failure_patterns:
                    self.failure_patterns[error_type] = []
                self.failure_patterns[error_type].append(failure_record)
                
                # Update strategy success rate
                domain = url_pattern.get('domain', 'unknown')
                self.update_strategy_success_rate(domain, strategy_attempted, False, stage)
                
                # Generate adaptation rule for repeated failures
                recent_failures = [f for f in self.failure_patterns[error_type] 
                                 if f['url_pattern'].get('domain') == domain and
                                 (datetime.utcnow() - datetime.fromisoformat(f['timestamp'])).total_seconds() < 3600]
                
                if len(recent_failures) >= 2:
                    print(f"🔧 [{worker_id}] Multiple failures detected for {domain} - generating adaptation rule")
                    self.generate_adaptation_rule(url, error_type)
                
                # Save knowledge base
                self.save_knowledge_base()
                
                print(f"📚 [{worker_id}] Learned from failure: {error_type} on {domain} (strategy {strategy_attempted})")
                
        except Exception as e:
            print(f"⚠️ Failure learning error: {e}")
        """Enhanced failure learning with pattern recognition"""
        try:
            with self.lock:
                # Extract URL pattern
                url_pattern = self.extract_url_pattern(url)
                
                # Extract content signatures
                content_signatures = self.extract_content_signatures(page_content) if page_content else {}
                
                # Create failure record
                failure_record = {
                    'url': url,
                    'url_pattern': url_pattern,
                    'content_signatures': content_signatures,
                    'error_type': error_type,
                    'strategy_attempted': strategy_attempted,
                    'worker_id': worker_id,
                    'stage': stage,
                    'timestamp': datetime.utcnow().isoformat(),
                    'addresses_found': addresses_found or 0
                }
                
                # Store failure pattern
                if error_type not in self.failure_patterns:
                    self.failure_patterns[error_type] = []
                self.failure_patterns[error_type].append(failure_record)
                
                # Update strategy success rate
                domain = url_pattern.get('domain', 'unknown')
                self.update_strategy_success_rate(domain, strategy_attempted, False, stage)
                
                # Generate adaptation rule for repeated failures
                recent_failures = [f for f in self.failure_patterns[error_type] 
                                 if f['url_pattern'].get('domain') == domain and
                                 (datetime.utcnow() - datetime.fromisoformat(f['timestamp'])).total_seconds() < 3600]
                
                if len(recent_failures) >= 2:
                    print(f"🔧 [{worker_id}] Multiple failures detected for {domain} - generating adaptation rule")
                    self.generate_adaptation_rule(url, error_type)
                
                # Save knowledge base
                self.save_knowledge_base()
                
                print(f"📚 [{worker_id}] Learned from failure: {error_type} on {domain} (strategy {strategy_attempted})")
                
        except Exception as e:
            print(f"⚠️ Failure learning error: {e}")
        """Enhanced learning from failures with conditional AI analysis - only use AI when addresses are found"""
        try:
            with self.lock:
                domain = urlparse(url).netloc
                url_pattern = self.extract_url_pattern(url)
                
                # Extract content signatures for pattern matching
                content_signatures = self.extract_content_signatures(page_content)
                
                # Only use AI analysis if addresses were found (to save costs)
                ai_analysis = None
                if addresses_found and len(addresses_found) > 0:
                    print(f"🤖 [{worker_id}] Using AI analysis since {len(addresses_found)} addresses were found")
                    # Truncate page content before sending to AI to prevent token limit issues
                    if page_content and len(page_content) > 5000:
                        print(f"⚠️ [{worker_id}] Truncating page content from {len(page_content)} to 5000 characters for AI analysis")
                        page_content = page_content[:5000]
                    ai_analysis = self.ai_analyze_page_content(page_content, url)
                else:
                    print(f"💰 [{worker_id}] Skipping AI analysis - no addresses found (cost optimization)")
                    ai_analysis = {'page_type': 'unknown', 'content_type': 'unknown'}
                
                # Record failure pattern
                failure_record = {
                    'url_pattern': url_pattern,
                    'error_type': error_type,
                    'strategy_attempted': strategy_attempted,
                    'timestamp': datetime.utcnow().isoformat(),
                    'worker_id': worker_id,
                    'is_darknet': domain.endswith('.onion'),
                    'content_signatures': content_signatures,
                    'ai_analysis': ai_analysis,
                    'stage': stage,
                    'addresses_found': addresses_found is not None and len(addresses_found) > 0
                }
                
                if error_type not in self.failure_patterns:
                    self.failure_patterns[error_type] = []
                
                self.failure_patterns[error_type].append(failure_record)
                
                # Update strategy success rates (mark as failed)
                self.update_strategy_success_rate(domain, strategy_attempted, False, stage)
                
                # Generate adaptation rule for this failure
                self.generate_darknet_adaptation_rule(url, error_type, ai_analysis)
                
                print(f"📚 [{worker_id}] Learned from failure: {error_type} for {domain} at stage {stage}")
                
                # Save knowledge periodically
                if len(self.failure_patterns[error_type]) % 5 == 0:
                    self.save_knowledge_base()
                    
        except Exception as e:
            print(f"⚠️ Learning from failure failed: {e}")
    
    def generate_darknet_adaptation_rule(self, url, error_type, ai_analysis):
        """Generate darknet-specific adaptation rules"""
        try:
            domain = urlparse(url).netloc
            
            # Analyze recent failures for this domain
            recent_failures = []
            for failures in self.failure_patterns.values():
                for failure in failures:
                    # Check if failure has required keys
                    if not failure or 'timestamp' not in failure:
                        continue  # Skip invalid failure records
                    
                    if failure.get('url_pattern', {}).get('domain') == domain:
                        try:
                            failure_time = datetime.fromisoformat(failure['timestamp'])
                            if (datetime.utcnow() - failure_time).days < 7:  # Last week
                                recent_failures.append(failure)
                        except (ValueError, TypeError):
                            continue  # Skip invalid timestamps
            
            if recent_failures:
                # Generate adaptation rule with AI analysis
                rule = {
                    'domain': domain,
                    'error_patterns': [f['error_type'] for f in recent_failures],
                    'suggested_strategy': self.suggest_darknet_strategy_for_errors(recent_failures, ai_analysis),
                    'ai_analysis': ai_analysis,
                    'generated_at': datetime.utcnow().isoformat()
                }
                
                self.adaptation_rules[domain] = rule
                print(f"🔧 Generated darknet adaptation rule for {domain}")
                
        except Exception as e:
            print(f"⚠️ Darknet adaptation rule generation failed: {e}")
    
    def suggest_darknet_strategy_for_errors(self, failures, ai_analysis):
        """Suggest darknet-specific strategies based on errors and AI analysis"""
        try:
            error_types = [f['error_type'] for f in failures]
            
            # Handle None ai_analysis with proper fallback
            if ai_analysis is None:
                ai_analysis = {'page_type': 'unknown', 'content_type': 'unknown'}
            
            page_type = ai_analysis.get('page_type', 'unknown')
            content_type = ai_analysis.get('content_type', 'unknown')
            
            # Darknet-specific strategy mapping
            if 'captcha' in str(error_types).lower():
                return 9  # AI captcha solver
            elif 'login' in str(error_types).lower() or 'authentication' in str(error_types).lower():
                return 7  # Darknet login focus
            elif 'registration' in str(error_types).lower() or 'signup' in str(error_types).lower():
                return 6  # Darknet registration focus
            elif 'payment' in str(error_types).lower() or 'checkout' in str(error_types).lower():
                return 8  # Darknet payment focus
            elif 'marketplace' in page_type.lower():
                return 10  # Marketplace-specific
            elif 'timeout' in str(error_types).lower():
                return 4  # JS interactive
            else:
                return 2  # AI enhanced as default
                
        except Exception as e:
            print(f"⚠️ Darknet strategy suggestion failed: {e}")
            return 2
    
    def get_best_strategy(self, url, content_signatures=None):
        """Enhanced strategy selection with darknet-specific logic"""
        try:
            domain = urlparse(url).netloc
            
            # Check if we have learned patterns for this site
            if domain in self.site_patterns:
                # Get the most recent successful strategy - fix timestamp comparison
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=24)  # Last 24 hours
                
                recent_successes = []
                for p in self.site_patterns[domain]:
                    if 'timestamp' in p:
                        try:
                            success_time = datetime.fromisoformat(p['timestamp'])
                            if success_time > cutoff_time:
                                recent_successes.append(p)
                        except (ValueError, TypeError):
                            continue  # Skip invalid timestamps
                
                if recent_successes:
                    best_strategy = max(recent_successes, key=lambda x: x.get('timestamp', ''))
                    print(f"🎯 Using learned strategy {best_strategy['strategy']} for {domain}")
                    return best_strategy['strategy']
            
            # Check strategy success rates
            if domain in self.strategy_success_rates:
                best_strategy = self.get_highest_success_rate_strategy(domain)
                if best_strategy:
                    print(f"📊 Using best success rate strategy {best_strategy} for {domain}")
                    return best_strategy
            
            # Check content signatures for similar patterns
            if content_signatures:
                similar_strategy = self.find_similar_content_strategy(content_signatures)
                if similar_strategy:
                    print(f"🔍 Using similar content strategy {similar_strategy}")
                    return similar_strategy
            
            # Darknet-specific default strategy with cycling
            if domain.endswith('.onion'):
                # Cycle through strategies for onion sites based on recent performance
                current_time = datetime.utcnow()
                recent_failures = 0
                
                # Count recent failures for this domain
                for failures in self.failure_patterns.values():
                    for failure in failures:
                        if (failure.get('url_pattern', {}).get('domain') == domain and 
                            'timestamp' in failure):
                            try:
                                failure_time = datetime.fromisoformat(failure['timestamp'])
                                if (current_time - failure_time).total_seconds() < 3600:  # Last hour
                                    recent_failures += 1
                            except:
                                continue
                
                # Choose strategy based on recent failures
                if recent_failures >= 3:
                    strategy = 4  # JS interactive for problematic sites
                elif recent_failures >= 1:
                    strategy = 3  # Visual captcha for moderate issues
                else:
                    strategy = 2  # AI enhanced for normal sites
                
                print(f"🌐 Using darknet strategy {strategy} for {domain} (recent failures: {recent_failures})")
                return strategy
            else:
                print(f"🤖 Using default AI-enhanced strategy for {domain}")
                return 2
            
        except Exception as e:
            print(f"⚠️ Strategy selection failed: {e}")
            return 2  # Default to AI-enhanced
    
    def get_highest_success_rate_strategy(self, domain):
        """Get strategy with highest success rate for a domain"""
        try:
            if domain not in self.strategy_success_rates:
                return None
            
            best_strategy = None
            best_rate = 0
            
            for strategy, attempts in self.strategy_success_rates[domain].items():
                if not isinstance(attempts, list):
                    continue  # Skip invalid strategy entries
                    
                if attempts:
                    try:
                        success_count = sum(1 for attempt in attempts if isinstance(attempt, dict) and attempt.get('success', False))
                        success_rate = success_count / len(attempts)
                        
                        if success_rate > best_rate:
                            best_rate = success_rate
                            best_strategy = strategy
                    except (TypeError, ZeroDivisionError):
                        continue  # Skip invalid attempts
            
            return best_strategy if best_rate > 0.1 else None  # Lowered threshold: success rate > 10%
            
        except Exception as e:
            print(f"⚠️ Success rate calculation failed: {e}")
            return None
    
    def find_similar_content_strategy(self, content_signatures):
        """Find strategy that worked for similar content"""
        try:
            # Look for similar content patterns in failure records
            for error_type, failures in self.failure_patterns.items():
                for failure in failures:
                    if 'content_signatures' in failure:
                        sig = failure['content_signatures']
                        similarity = self.calculate_content_similarity(content_signatures, sig)
                        
                        if similarity > 0.5:  # Lowered threshold: 50% similarity
                            # Find what strategy worked after this failure
                            return self.find_working_strategy_after_failure(failure)
            
            return None
            
        except Exception as e:
            print(f"⚠️ Similar content strategy search failed: {e}")
            return None
    
    def calculate_content_similarity(self, sig1, sig2):
        """Calculate similarity between content signatures"""
        try:
            if 'error' in sig1 or 'error' in sig2:
                return 0
            
            # Simple similarity calculation
            matching_features = 0
            total_features = 0
            
            for key in sig1:
                if key in sig2 and key != 'hash':
                    if sig1[key] == sig2[key]:
                        matching_features += 1
                    total_features += 1
            
            return matching_features / total_features if total_features > 0 else 0
            
        except Exception:
            return 0
    
    def find_working_strategy_after_failure(self, failure_record):
        """Find what strategy worked after a specific failure"""
        try:
            # Check if failure_record has required keys
            if not failure_record or 'timestamp' not in failure_record:
                print(f"⚠️ Invalid failure record: missing timestamp")
                return None
            
            # Look for successful attempts after this failure
            try:
                failure_time = datetime.fromisoformat(failure_record['timestamp'])
            except (ValueError, TypeError):
                print(f"⚠️ Invalid failure record timestamp format")
                return None
            
            for domain, patterns in self.site_patterns.items():
                for pattern in patterns:
                    if 'timestamp' not in pattern:
                        continue  # Skip patterns without timestamp
                    try:
                        success_time = datetime.fromisoformat(pattern['timestamp'])
                        if success_time > failure_time:
                            return pattern['strategy']
                    except (ValueError, TypeError):
                        continue  # Skip invalid timestamps
            
            return None
            
        except Exception as e:
            print(f"⚠️ Working strategy search failed: {e}")
            return None
    
    def generate_adaptation_rule(self, url, error_type):
        """Generate adaptation rules based on failures"""
        try:
            domain = urlparse(url).netloc
            
            # Analyze recent failures for this domain
            recent_failures = []
            for failures in self.failure_patterns.values():
                for failure in failures:
                    # Check if failure has required keys
                    if not failure or 'timestamp' not in failure:
                        continue  # Skip invalid failure records
                        
                    if failure.get('url_pattern', {}).get('domain') == domain:
                        try:
                            failure_time = datetime.fromisoformat(failure['timestamp'])
                            if (datetime.utcnow() - failure_time).days < 7:  # Last week
                                recent_failures.append(failure)
                        except (ValueError, TypeError):
                            continue  # Skip invalid timestamps
            
            if recent_failures:
                # Generate adaptation rule
                rule = {
                    'domain': domain,
                    'error_patterns': [f['error_type'] for f in recent_failures],
                    'suggested_strategy': self.suggest_strategy_for_errors(recent_failures),
                    'generated_at': datetime.utcnow().isoformat()
                }
                
                self.adaptation_rules[domain] = rule
                print(f"🔧 Generated adaptation rule for {domain}")
                
        except Exception as e:
            print(f"⚠️ Adaptation rule generation failed: {e}")
    
    def suggest_strategy_for_errors(self, failures):
        """Suggest strategy based on error patterns"""
        try:
            error_types = [f['error_type'] for f in failures]
            
            if any('captcha' in error.lower() for error in error_types):
                return 3  # Visual captcha strategy
            elif any('timeout' in error.lower() for error in error_types):
                return 4  # JS interactive strategy
            elif any('login' in error.lower() for error in error_types):
                return 2  # AI enhanced strategy
            else:
                return 5  # Custom site strategy
                
        except Exception as e:
            print(f"⚠️ Strategy suggestion failed: {e}")
            return 2
    
    def save_knowledge_base(self):
        """Save all learned patterns to disk"""
        try:
            # Convert nested defaultdict to regular dict for JSON serialization
            strategy_rates_dict = {}
            for domain, strategies in self.strategy_success_rates.items():
                strategy_rates_dict[domain] = {}
                for strategy, attempts in strategies.items():
                    strategy_rates_dict[domain][strategy] = attempts
            
            knowledge = {
                'site_patterns': self.site_patterns,
                'failure_patterns': dict(self.failure_patterns),
                'strategy_success_rates': strategy_rates_dict,
                'adaptation_rules': self.adaptation_rules,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            with open(self.knowledge_file, 'w') as f:
                json.dump(knowledge, f, indent=2)
            
            print(f"💾 Knowledge base saved: {self.knowledge_file}")
            
        except Exception as e:
            print(f"⚠️ Knowledge base save failed: {e}")
    
    def load_knowledge_base(self):
        """Load learned patterns from disk"""
        try:
            if os.path.exists(self.knowledge_file):
                with open(self.knowledge_file, 'r') as f:
                    knowledge = json.load(f)
                
                self.site_patterns = knowledge.get('site_patterns', {})
                self.failure_patterns = defaultdict(list, knowledge.get('failure_patterns', {}))
                self.strategy_success_rates = defaultdict(lambda: defaultdict(list), 
                                                        knowledge.get('strategy_success_rates', {}))
                self.adaptation_rules = knowledge.get('adaptation_rules', {})
                
                print(f"📚 Knowledge base loaded: {len(self.site_patterns)} site patterns, "
                      f"{sum(len(f) for f in self.failure_patterns.values())} failure patterns")
            else:
                print("📚 No existing knowledge base found, starting fresh")
                
        except Exception as e:
            print(f"⚠️ Knowledge base load failed: {e}")
    
    def get_statistics(self):
        """Get learning statistics, including per-stage analysis"""
        try:
            stats = {
                'total_sites_learned': len(self.site_patterns),
                'total_failures_recorded': sum(len(f) for f in self.failure_patterns.values()),
                'total_adaptation_rules': len(self.adaptation_rules),
                'most_common_errors': self.get_most_common_errors(),
                'best_performing_strategies': self.get_best_performing_strategies(),
                'stage_success_counts': self.get_stage_success_counts(),
                'stage_failure_counts': self.get_stage_failure_counts()
            }
            return stats
        except Exception as e:
            print(f"⚠️ Statistics generation failed: {e}")
            return {}
    
    def get_most_common_errors(self):
        """Get most common error types"""
        try:
            error_counts = {}
            for error_type, failures in self.failure_patterns.items():
                error_counts[error_type] = len(failures)
            
            return sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        except Exception:
            return []
    
    def get_best_performing_strategies(self):
        """Get best performing strategies"""
        try:
            strategy_scores = defaultdict(list)
            
            for domain, strategies in self.strategy_success_rates.items():
                if not isinstance(strategies, dict):
                    continue  # Skip invalid domain entries
                    
                for strategy, attempts in strategies.items():
                    if not isinstance(attempts, list):
                        continue  # Skip invalid strategy entries
                        
                    if attempts:
                        try:
                            success_rate = sum(1 for a in attempts if isinstance(a, dict) and a.get('success', False)) / len(attempts)
                            strategy_scores[strategy].append(success_rate)
                        except (TypeError, ZeroDivisionError):
                            continue  # Skip invalid attempts
            
            # Calculate average success rates
            avg_scores = {}
            for strategy, scores in strategy_scores.items():
                if scores:  # Only calculate if we have valid scores
                    avg_scores[strategy] = sum(scores) / len(scores)
            
            return sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
        except Exception as e:
            print(f"⚠️ Best performing strategies calculation failed: {e}")
            return []
    
    def learn_from_success(self, url, strategy_used, worker_id, stage="extracted_address", extracted_data=None):
        """Enhanced learning from successful scraping attempts with stage tracking and extracted data"""
        try:
            with self.lock:
                domain = urlparse(url).netloc
                
                # Record successful pattern
                if domain not in self.site_patterns:
                    self.site_patterns[domain] = []
                
                success_record = {
                    'strategy': strategy_used,
                    'timestamp': datetime.utcnow().isoformat(),
                    'worker_id': worker_id,
                    'is_darknet': domain.endswith('.onion'),
                    'stage': stage,
                    'extracted_data': extracted_data or {}
                }
                
                self.site_patterns[domain].append(success_record)
                
                # Update strategy success rates (mark as successful)
                self.update_strategy_success_rate(domain, strategy_used, True, stage)
                
                print(f"📚 [{worker_id}] Learned from success: strategy {strategy_used} for {domain} at stage {stage}")
                
                # Save knowledge periodically
                if len(self.site_patterns[domain]) % 5 == 0:
                    self.save_knowledge_base()
                    
        except Exception as e:
            print(f"⚠️ Learning from success failed: {e}")
    
    def update_strategy_success_rate(self, domain, strategy, success, stage="extracted_address"):
        """Update success rates for strategies, per stage"""
        try:
            # Ensure the domain exists in the strategy_success_rates
            if domain not in self.strategy_success_rates:
                self.strategy_success_rates[domain] = defaultdict(list)
            
            # Ensure the strategy exists for this domain
            if strategy not in self.strategy_success_rates[domain]:
                self.strategy_success_rates[domain][strategy] = []
            
            # Record the attempt
            self.strategy_success_rates[domain][strategy].append({
                'success': success,
                'timestamp': datetime.utcnow().isoformat(),
                'stage': stage
            })
            
            # Keep only recent attempts (last 50)
            if len(self.strategy_success_rates[domain][strategy]) > 50:
                self.strategy_success_rates[domain][strategy] = \
                    self.strategy_success_rates[domain][strategy][-50:]
                    
        except Exception as e:
            print(f"⚠️ Strategy success rate update failed: {e}")
    
    def get_stage_success_counts(self):
        """Count successes per stage"""
        from collections import Counter
        stage_counts = Counter()
        for domain, records in self.site_patterns.items():
            for rec in records:
                stage = rec.get('stage', 'extracted_address')
                stage_counts[stage] += 1
        return dict(stage_counts)

    def get_stage_failure_counts(self):
        """Count failures per stage"""
        from collections import Counter
        stage_counts = Counter()
        for error_type, records in self.failure_patterns.items():
            for rec in records:
                stage = rec.get('stage', 'extracted_address')
                stage_counts[stage] += 1
        return dict(stage_counts)

# Global learning agent instance
learning_agent = LearningAgent()
