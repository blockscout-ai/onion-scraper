# ---[ Learning Agent Integration ]---
"""
This file shows how to integrate the Learning Agent with your existing scraper
without affecting any current functionality.

The learning agent can be added incrementally to your scraper_fast.py file.
"""

from learning_agent import learning_agent
import time
import os
import sys
from datetime import datetime

# ---[ Integration Examples ]---

def integrate_learning_into_process_url_fast():
    """
    Example of how to integrate learning into your existing process_url_fast function.
    This shows the minimal changes needed to add learning capabilities.
    """
    
    # Add this import at the top of your scraper_fast.py:
    # from learning_agent import learning_agent
    
    def process_url_fast_with_learning(url, worker_id):
        """Enhanced version of process_url_fast with learning capabilities"""
        driver = None
        results = []
        strategy_used = None
        
        try:
            print(f"🔍 [{worker_id}] Processing: {url}")
            
            # ---[ LEARNING: Get best strategy for this URL ]---
            content_signatures = None  # Will be set after page load
            strategy_used = learning_agent.get_best_strategy(url, content_signatures)
            print(f"🎯 [{worker_id}] Using strategy: {strategy_used}")
            
            # Your existing TOR rotation code...
            # [existing code here]
            
            driver = create_driver()
            print(f"🌐 [{worker_id}] Loading page: {url}")
            driver.get(url)
            time.sleep(SHORT_WAIT)
            
            # ---[ LEARNING: Extract content signatures ]---
            html = driver.page_source
            content_signatures = learning_agent.extract_content_signatures(html)
            
            # Your existing page processing code...
            # [existing code here]
            
            # ---[ LEARNING: Record success ]---
            if results:  # If we found addresses
                learning_agent.learn_from_success(url, strategy_used, worker_id, stage="extracted_address")
                print(f"✅ [{worker_id}] Learning: Strategy {strategy_used} succeeded")
            
            return results
            
        except Exception as e:
            error_type = classify_error_type(str(e))
            
            # ---[ LEARNING: Record failure ]---
            if driver:
                try:
                    page_content = driver.page_source
                except:
                    page_content = ""
            else:
                page_content = ""
            
            learning_agent.learn_from_failure(url, error_type, page_content, strategy_used, worker_id, stage="solved_captcha")
            print(f"❌ [{worker_id}] Learning: Strategy {strategy_used} failed with {error_type}")
            
            # Your existing error handling code...
            # [existing code here]
            
            return []
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

def classify_error_type(error_message, page_content=""):
    """Enhanced error classification with darknet-specific patterns"""
    error_lower = error_message.lower()
    content_lower = page_content.lower()
    
    # Darknet-specific error patterns
    if any(word in error_lower for word in ['captcha', 'verification', 'robot', 'human']):
        return "captcha_required"
    elif any(word in error_lower for word in ['login', 'authentication', 'signin', 'unauthorized']):
        return "login_required"
    elif any(word in error_lower for word in ['registration', 'signup', 'register', 'account']):
        return "registration_required"
    elif any(word in error_lower for word in ['payment', 'checkout', 'order', 'purchase']):
        return "payment_required"
    elif any(word in error_lower for word in ['timeout', 'connection', 'network']):
        return "connection_timeout"
    elif any(word in error_lower for word in ['javascript', 'js', 'script']):
        return "javascript_required"
    elif any(word in error_lower for word in ['form', 'submit', 'validation']):
        return "form_validation_failed"
    elif any(word in error_lower for word in ['blocked', 'banned', 'restricted']):
        return "access_blocked"
    elif any(word in error_lower for word in ['maintenance', 'down', 'unavailable']):
        return "site_unavailable"
    else:
        return "unknown_error"

def integrate_learning_agent_with_scraper():
    """Enhanced integration function with AI capabilities"""
    print("🤖 Enhanced Learning Agent Integration")
    print("=" * 50)
    
    # Check AI capabilities
    if learning_agent.AI_ENABLED:
        print("✅ AI capabilities enabled")
        if learning_agent.OPENAI_API_KEY:
            print("   - OpenAI API configured")
        if learning_agent.ANTHROPIC_API_KEY:
            print("   - Anthropic API configured")
    else:
        print("⚠️ AI capabilities disabled - using fallback methods")
    
    # Show available strategies
    print(f"\n📋 Available Strategies:")
    for strategy_id, strategy_name in learning_agent.strategies.items():
        print(f"   {strategy_id}: {strategy_name}")
    
    # Show darknet-specific capabilities
    print(f"\n🌐 Darknet-Specific Features:")
    print(f"   - Darknet pattern detection: {len(learning_agent.darknet_indicators)} categories")
    print(f"   - Form analysis: {len(learning_agent.analyze_forms(''))} field types")
    print(f"   - AI-powered captcha solving: {'Enabled' if learning_agent.AI_ENABLED else 'Disabled'}")
    print(f"   - AI credential generation: {'Enabled' if learning_agent.AI_ENABLED else 'Disabled'}")
    print(f"   - AI form analysis: {'Enabled' if learning_agent.AI_ENABLED else 'Disabled'}")
    
    # Show current knowledge base stats
    stats = learning_agent.get_statistics()
    print(f"\n📊 Current Knowledge Base:")
    print(f"   - Sites processed: {stats.get('total_sites_learned', 0)}")
    print(f"   - Total failures: {stats.get('total_failures_recorded', 0)}")
    print(f"   - Adaptation rules: {stats.get('total_adaptation_rules', 0)}")
    print(f"   - Per-stage success counts: {stats.get('stage_success_counts', {})}")
    print(f"   - Per-stage failure counts: {stats.get('stage_failure_counts', {})}")
    print("\n" + "=" * 50)
    return True

def enhanced_process_url_with_learning(url, worker_id, driver=None, page_content=""):
    """Enhanced URL processing with learning agent integration"""
    try:
        print(f"🧠 [{worker_id}] Enhanced processing with learning agent...")
        
        # Get content signatures for strategy selection
        content_signatures = learning_agent.extract_content_signatures(page_content) if page_content else None
        best_strategy = learning_agent.get_best_strategy(url, content_signatures)
        
        # Skip AI analysis initially - only use when addresses are found
        ai_analysis = {}
        
        # Execute the strategy based on the type
        if best_strategy == 9:  # AI captcha solver
            print(f"🔍 [{worker_id}] Using AI-powered captcha solver")
            # This would integrate with the existing captcha solving logic
            return execute_ai_captcha_strategy(url, worker_id, driver, ai_analysis)
            
        elif best_strategy == 6:  # Darknet registration focus
            print(f"📝 [{worker_id}] Using darknet registration strategy")
            return execute_darknet_registration_strategy(url, worker_id, driver, ai_analysis)
            
        elif best_strategy == 7:  # Darknet login focus
            print(f"🔐 [{worker_id}] Using darknet login strategy")
            return execute_darknet_login_strategy(url, worker_id, driver, ai_analysis)
            
        elif best_strategy == 8:  # Darknet payment focus
            print(f"💳 [{worker_id}] Using darknet payment strategy")
            return execute_darknet_payment_strategy(url, worker_id, driver, ai_analysis)
            
        elif best_strategy == 10:  # Marketplace-specific
            print(f"🏪 [{worker_id}] Using marketplace-specific strategy")
            return execute_marketplace_strategy(url, worker_id, driver, ai_analysis)
            
        else:
            print(f"🤖 [{worker_id}] Using AI-enhanced general strategy")
            return execute_ai_enhanced_strategy(url, worker_id, driver, ai_analysis)
            
    except Exception as e:
        error_type = classify_error_type(str(e), page_content)
        learning_agent.learn_from_failure(url, error_type, page_content, best_strategy, worker_id, stage="solved_captcha")
        print(f"❌ [{worker_id}] Enhanced processing failed: {e}")
        return None

def execute_ai_captcha_strategy(url, worker_id, driver, ai_analysis):
    """Execute AI-powered captcha solving strategy"""
    try:
        print(f"🔍 [{worker_id}] AI Captcha Strategy - Looking for captcha elements...")
        
        if not driver:
            print(f"⚠️ [{worker_id}] No driver provided for captcha strategy")
            return None
        
        # Look for captcha images
        captcha_images = driver.find_elements_by_tag_name('img')
        for img in captcha_images:
            src = img.get_attribute('src') or ''
            alt = img.get_attribute('alt') or ''
            
            if 'captcha' in src.lower() or 'captcha' in alt.lower():
                print(f"🎯 [{worker_id}] Found captcha image, attempting AI solution...")
                
                # Take screenshot of captcha
                captcha_screenshot = img.screenshot_as_png
                from PIL import Image
                import io
                captcha_image = Image.open(io.BytesIO(captcha_screenshot))
                
                # Use AI to solve captcha
                solution = learning_agent.ai_solve_captcha(captcha_image)
                if solution:
                    print(f"✅ [{worker_id}] AI solved captcha: {solution}")
                    
                    # Find captcha input field and fill it
                    captcha_inputs = driver.find_elements_by_xpath(
                        "//input[contains(@name, 'captcha') or contains(@id, 'captcha') or contains(@placeholder, 'captcha')]"
                    )
                    
                    if captcha_inputs:
                        captcha_inputs[0].clear()
                        captcha_inputs[0].send_keys(solution)
                        
                        # Submit the form
                        submit_buttons = driver.find_elements_by_xpath("//button[@type='submit'] | //input[@type='submit']")
                        if submit_buttons:
                            submit_buttons[0].click()
                            print(f"✅ [{worker_id}] Captcha form submitted")
                            learning_agent.learn_from_success(url, strategy_used, worker_id, stage="solved_captcha")
                            return True
        
        print(f"⚠️ [{worker_id}] No captcha found or AI solving failed")
        return False
        
    except Exception as e:
        print(f"❌ [{worker_id}] AI captcha strategy failed: {e}")
        return False

def execute_darknet_registration_strategy(url, worker_id, driver, ai_analysis):
    """Execute darknet registration strategy with AI-generated credentials"""
    try:
        print(f"📝 [{worker_id}] Darknet Registration Strategy...")
        
        if not driver:
            print(f"⚠️ [{worker_id}] No driver provided for registration strategy")
            return None
        
        # Determine site type for credential generation
        site_type = ai_analysis.get('page_type', 'general')
        if 'marketplace' in site_type.lower():
            site_type = 'marketplace'
        elif 'forum' in site_type.lower():
            site_type = 'forum'
        
        # Generate realistic darknet credentials
        credentials = learning_agent.ai_generate_darknet_credentials(site_type)
        print(f"🤖 [{worker_id}] Generated credentials for {site_type} site")
        
        # Find and fill registration form
        forms = driver.find_elements_by_tag_name('form')
        for form in forms:
            form_html = form.get_attribute('outerHTML')
            
            # Use AI to analyze form fields
            if learning_agent.AI_ENABLED:
                field_analysis = learning_agent.ai_analyze_form_fields(form_html)
                print(f"🤖 [{worker_id}] AI form analysis: {len(field_analysis)} field mappings")
            
            # Fill form fields based on analysis or fallback
            inputs = form.find_elements_by_tag_name('input')
            fields_filled = 0
            
            for inp in inputs:
                name = inp.get_attribute('name') or ''
                id_attr = inp.get_attribute('id') or ''
                placeholder = inp.get_attribute('placeholder') or ''
                typ = inp.get_attribute('type') or ''
                
                field_text = f"{name} {id_attr} {placeholder} {typ}".lower()
                
                # Map fields to credentials
                if any(word in field_text for word in ['user', 'login', 'name']) and typ != 'password':
                    inp.clear()
                    inp.send_keys(credentials['username'])
                    fields_filled += 1
                elif any(word in field_text for word in ['email', 'mail']):
                    inp.clear()
                    inp.send_keys(credentials['email'])
                    fields_filled += 1
                elif any(word in field_text for word in ['pass', 'pwd']):
                    inp.clear()
                    inp.send_keys(credentials['password'])
                    fields_filled += 1
                elif any(word in field_text for word in ['btc', 'bitcoin', 'wallet']):
                    inp.clear()
                    inp.send_keys(credentials['btc_address'])
                    fields_filled += 1
                elif any(word in field_text for word in ['pgp', 'key', 'public']):
                    inp.clear()
                    inp.send_keys(credentials['pgp_key'])
                    fields_filled += 1
                elif any(word in field_text for word in ['telegram', 'signal']):
                    inp.clear()
                    inp.send_keys(credentials['telegram'])
                    fields_filled += 1
                elif any(word in field_text for word in ['age', 'birth']):
                    inp.clear()
                    inp.send_keys(credentials['age'])
                    fields_filled += 1
                elif any(word in field_text for word in ['country', 'location']):
                    inp.clear()
                    inp.send_keys(credentials['country'])
                    fields_filled += 1
            
            if fields_filled > 0:
                print(f"✅ [{worker_id}] Filled {fields_filled} registration fields")
                
                # Submit form
                submit_buttons = form.find_elements_by_xpath(".//button[@type='submit'] | .//input[@type='submit']")
                if submit_buttons:
                    submit_buttons[0].click()
                    print(f"✅ [{worker_id}] Registration form submitted")
                    learning_agent.learn_from_success(url, strategy_used, worker_id, stage="registered")
                    return True
        
        print(f"⚠️ [{worker_id}] No registration form found or filled")
        return False
        
    except Exception as e:
        print(f"❌ [{worker_id}] Darknet registration strategy failed: {e}")
        return False

def execute_darknet_login_strategy(url, worker_id, driver, ai_analysis):
    """Execute darknet login strategy"""
    try:
        print(f"🔐 [{worker_id}] Darknet Login Strategy...")
        
        if not driver:
            print(f"⚠️ [{worker_id}] No driver provided for login strategy")
            return None
        
        # Generate credentials for login
        credentials = learning_agent.ai_generate_darknet_credentials('general')
        
        # Find login forms
        forms = driver.find_elements_by_tag_name('form')
        for form in forms:
            form_html = form.get_attribute('outerHTML').lower()
            
            if any(word in form_html for word in ['login', 'signin', 'access', 'enter']):
                print(f"🎯 [{worker_id}] Found login form")
                
                inputs = form.find_elements_by_tag_name('input')
                fields_filled = 0
                
                for inp in inputs:
                    name = inp.get_attribute('name') or ''
                    typ = inp.get_attribute('type') or ''
                    
                    if 'pass' in name.lower() or typ == 'password':
                        inp.clear()
                        inp.send_keys(credentials['password'])
                        fields_filled += 1
                    elif 'user' in name.lower() or 'email' in name.lower() or typ == 'text':
                        inp.clear()
                        inp.send_keys(credentials['username'])
                        fields_filled += 1
                
                if fields_filled >= 2:
                    print(f"✅ [{worker_id}] Filled {fields_filled} login fields")
                    
                    # Submit form
                    submit_buttons = form.find_elements_by_xpath(".//button[@type='submit'] | .//input[@type='submit']")
                    if submit_buttons:
                        submit_buttons[0].click()
                        print(f"✅ [{worker_id}] Login form submitted")
                        learning_agent.learn_from_success(url, strategy_used, worker_id, stage="logged_in")
                        return True
        
        print(f"⚠️ [{worker_id}] No login form found or filled")
        return False
        
    except Exception as e:
        print(f"❌ [{worker_id}] Darknet login strategy failed: {e}")
        return False

def execute_darknet_payment_strategy(url, worker_id, driver, ai_analysis):
    """Execute darknet payment strategy"""
    try:
        print(f"💳 [{worker_id}] Darknet Payment Strategy...")
        
        if not driver:
            print(f"⚠️ [{worker_id}] No driver provided for payment strategy")
            return None
        
        # Look for payment-related elements
        payment_elements = driver.find_elements_by_xpath(
            "//*[contains(text(), 'bitcoin') or contains(text(), 'btc') or contains(text(), 'payment') or contains(text(), 'checkout')]"
        )
        
        if payment_elements:
            print(f"🎯 [{worker_id}] Found {len(payment_elements)} payment-related elements")
            
            # Click on payment elements to reveal addresses
            for element in payment_elements[:3]:  # Limit to first 3
                try:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"✅ [{worker_id}] Clicked payment element")
                        learning_agent.learn_from_success(url, strategy_used, worker_id, stage="added_to_cart")
                        return True
                except:
                    continue
        
        print(f"⚠️ [{worker_id}] No payment elements found or clickable")
        return False
        
    except Exception as e:
        print(f"❌ [{worker_id}] Darknet payment strategy failed: {e}")
        return False

def execute_marketplace_strategy(url, worker_id, driver, ai_analysis):
    """Execute marketplace-specific strategy"""
    try:
        print(f"🏪 [{worker_id}] Marketplace Strategy...")
        
        if not driver:
            print(f"⚠️ [{worker_id}] No driver provided for marketplace strategy")
            return None
        
        # Look for marketplace-specific elements
        marketplace_elements = driver.find_elements_by_xpath(
            "//*[contains(text(), 'vendor') or contains(text(), 'listing') or contains(text(), 'product') or contains(text(), 'shop')]"
        )
        
        if marketplace_elements:
            print(f"🎯 [{worker_id}] Found {len(marketplace_elements)} marketplace elements")
            
            # Click on marketplace elements
            for element in marketplace_elements[:3]:
                try:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        print(f"✅ [{worker_id}] Clicked marketplace element")
                        learning_agent.learn_from_success(url, strategy_used, worker_id, stage="extracted_address")
                        return True
                except:
                    continue
        
        print(f"⚠️ [{worker_id}] No marketplace elements found or clickable")
        return False
        
    except Exception as e:
        print(f"❌ [{worker_id}] Marketplace strategy failed: {e}")
        return False

def execute_ai_enhanced_strategy(url, worker_id, driver, ai_analysis):
    """Execute general AI-enhanced strategy"""
    try:
        print(f"🤖 [{worker_id}] AI-Enhanced General Strategy...")
        
        if not driver:
            print(f"⚠️ [{worker_id}] No driver provided for AI-enhanced strategy")
            return None
        
        # Use AI analysis to determine best approach
        required_interactions = ai_analysis.get('required_interactions', [])
        
        if 'forms' in str(required_interactions).lower():
            print(f"📝 [{worker_id}] AI detected forms, attempting to fill...")
            return execute_darknet_registration_strategy(url, worker_id, driver, ai_analysis)
        elif 'captcha' in str(required_interactions).lower():
            print(f"🔍 [{worker_id}] AI detected captcha, attempting to solve...")
            return execute_ai_captcha_strategy(url, worker_id, driver, ai_analysis)
        elif 'buttons' in str(required_interactions).lower():
            print(f"🖱️ [{worker_id}] AI detected buttons, attempting to click...")
            return execute_marketplace_strategy(url, worker_id, driver, ai_analysis)
        else:
            print(f"🤷 [{worker_id}] No specific interactions detected, using general approach")
            return execute_marketplace_strategy(url, worker_id, driver, ai_analysis)
        
    except Exception as e:
        print(f"❌ [{worker_id}] AI-enhanced strategy failed: {e}")
        return False

def demonstrate_enhanced_capabilities():
    """Demonstrate the enhanced learning agent capabilities"""
    print("🎯 Enhanced Learning Agent Demonstration")
    print("=" * 50)
    
    # Test URL
    test_url = "http://example.onion"
    test_content = """
    <html>
        <form>
            <input name="username" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <input name="captcha" placeholder="Enter captcha">
            <button type="submit">Login</button>
        </form>
        <div>Bitcoin payment address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa</div>
    </html>
    """
    
    print(f"🔍 Testing URL: {test_url}")
    
    # Extract content signatures
    signatures = learning_agent.extract_content_signatures(test_content)
    print(f"📊 Content signatures: {len(signatures)} features detected")
    
    # AI analysis (if enabled)
    if learning_agent.AI_ENABLED:
        ai_analysis = learning_agent.ai_analyze_page_content(test_content, test_url)
        print(f"🤖 AI analysis: {ai_analysis}")
    else:
        print("⚠️ AI analysis disabled")
    
    # Get best strategy
    best_strategy = learning_agent.get_best_strategy(test_url, signatures)
    print(f"🎯 Best strategy: {learning_agent.strategies.get(best_strategy, 'unknown')}")
    
    # Simulate each stage
    learning_agent.learn_from_success(test_url, best_strategy, "demo_worker", stage="solved_captcha")
    learning_agent.learn_from_success(test_url, best_strategy, "demo_worker", stage="registered")
    learning_agent.learn_from_success(test_url, best_strategy, "demo_worker", stage="logged_in")
    learning_agent.learn_from_success(test_url, best_strategy, "demo_worker", stage="added_to_cart")
    learning_agent.learn_from_success(test_url, best_strategy, "demo_worker", stage="extracted_address")
    
    # Show per-stage stats
    stats = learning_agent.get_statistics()
    print(f"\n📊 Per-stage success counts: {stats.get('stage_success_counts', {})}")
    print(f"📊 Per-stage failure counts: {stats.get('stage_failure_counts', {})}")
    
    print("✅ Enhanced capabilities demonstration completed")

if __name__ == "__main__":
    # Initialize integration
    integrate_learning_agent_with_scraper()
    
    # Demonstrate capabilities
    demonstrate_enhanced_capabilities()
    
    print("\n🚀 Enhanced Learning Agent ready for integration!")
    print("💡 The agent now includes:")
    print("   - AI-powered captcha solving")
    print("   - AI-generated darknet credentials")
    print("   - AI form analysis and filling")
    print("   - Darknet-specific strategy selection")
    print("   - Enhanced pattern recognition")
    print("   - Real-time adaptation based on failures") 