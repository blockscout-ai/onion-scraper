#!/usr/bin/env python3
"""
Smart Interaction Executor
Executes multi-step transaction flows using learned patterns.
"""

import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from multi_step_transaction_learner import transaction_learner

class SmartInteractionExecutor:
    def __init__(self, driver):
        self.driver = driver
        self.interaction_log = []
        self.current_sequence = []
        
    def execute_transaction_sequence(self, recommendations, timeout=30):
        """Execute a recommended transaction sequence"""
        if not recommendations:
            return {'success': False, 'reason': 'No recommendations provided'}
        
        best_recommendation = recommendations[0]
        sequence = best_recommendation['sequence']
        
        print(f"🎯 Executing transaction sequence (confidence: {best_recommendation['confidence']:.1%})")
        
        start_time = time.time()
        results = {'success': False, 'steps_completed': 0, 'addresses_found': [], 'interaction_log': []}
        
        try:
            for step_num, step in enumerate(sequence):
                if time.time() - start_time > timeout:
                    results['reason'] = 'Timeout exceeded'
                    break
                
                print(f"📋 Step {step_num + 1}/{len(sequence)}: {step['action']}")
                
                step_result = self.execute_step(step)
                self.interaction_log.append({
                    'step': step_num + 1,
                    'action': step['action'],
                    'result': step_result,
                    'timestamp': time.time()
                })
                
                if step_result['success']:
                    results['steps_completed'] += 1
                    
                    # Check for addresses after each successful step
                    addresses = self.extract_addresses_from_page()
                    if addresses:
                        results['addresses_found'].extend(addresses)
                        print(f"💰 Found {len(addresses)} addresses after step {step_num + 1}")
                else:
                    print(f"❌ Step {step_num + 1} failed: {step_result.get('reason', 'Unknown error')}")
                    results['reason'] = f"Step {step_num + 1} failed: {step_result.get('reason', 'Unknown error')}"
                    break
                
                # Wait between steps
                time.sleep(2)
            
            # Final check for success
            if results['addresses_found']:
                results['success'] = True
                results['reason'] = f"Found {len(results['addresses_found'])} addresses"
            elif results['steps_completed'] == len(sequence):
                # All steps completed but no addresses found
                final_addresses = self.extract_addresses_from_page()
                if final_addresses:
                    results['addresses_found'] = final_addresses
                    results['success'] = True
                    results['reason'] = f"Found {len(final_addresses)} addresses after sequence completion"
        
        except Exception as e:
            results['reason'] = f"Execution error: {str(e)}"
            print(f"❌ Execution error: {e}")
        
        results['interaction_log'] = self.interaction_log
        
        # Learn from this interaction
        self.learn_from_execution(sequence, results['success'])
        
        return results
    
    def execute_step(self, step):
        """Execute a single step in the transaction sequence"""
        action = step['action']
        
        try:
            if action == 'find_product':
                return self.find_and_select_product(step)
            elif action == 'click_button':
                return self.click_button_by_pattern(step)
            elif action == 'wait_for_modal':
                return self.wait_for_modal(step)
            elif action == 'fill_form':
                return self.fill_form_smart(step)
            elif action == 'submit_form':
                return self.submit_form_and_wait(step)
            elif action == 'select_price_option':
                return self.select_price_option(step)
            elif action == 'click_continue':
                return self.click_continue_button(step)
            else:
                return {'success': False, 'reason': f'Unknown action: {action}'}
        
        except Exception as e:
            return {'success': False, 'reason': f'Step execution error: {str(e)}'}
    
    def find_and_select_product(self, step):
        """Find and select a product (like a card with specific price)"""
        try:
            # Look for product cards with prices
            price_elements = self.driver.find_elements(By.XPATH, 
                "//*[contains(text(), '$') and (contains(@class, 'price') or contains(@class, 'cost'))]")
            
            if not price_elements:
                # Broader search for price patterns
                price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
            
            if price_elements:
                # Find the highest priced item (usually gets better results)
                highest_price_element = None
                highest_price = 0
                
                for element in price_elements:
                    price_match = re.search(r'\$(\d+)', element.text)
                    if price_match:
                        price = int(price_match.group(1))
                        if price > highest_price:
                            highest_price = price
                            highest_price_element = element
                
                if highest_price_element:
                    # Find associated buy button
                    parent = highest_price_element
                    for _ in range(5):  # Look up to 5 levels up
                        try:
                            parent = parent.find_element(By.XPATH, "..")
                            buy_buttons = parent.find_elements(By.XPATH, 
                                ".//button[contains(translate(text(), 'BUY', 'buy'), 'buy')] | "
                                ".//input[@type='submit' and contains(translate(@value, 'BUY', 'buy'), 'buy')]")
                            
                            if buy_buttons:
                                self.driver.execute_script("arguments[0].click();", buy_buttons[0])
                                print(f"   -> ✅ Clicked buy button for ${highest_price} item")
                                time.sleep(2)
                                return {'success': True, 'price': highest_price}
                        except:
                            continue
            
            return {'success': False, 'reason': 'No products with buy buttons found'}
        
        except Exception as e:
            return {'success': False, 'reason': f'Product selection error: {str(e)}'}
    
    def click_button_by_pattern(self, step):
        """Click button matching a specific pattern"""
        pattern = step.get('pattern', r'(?i)(buy|purchase|order|select)')
        
        try:
            # Try different button selection strategies
            selectors = [
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy')]",
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'purchase')]",
                f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'order')]",
                f"//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy')]",
                f"//button[@data-toggle='modal']",
                f"//button[contains(@class, 'btn') and contains(text(), '$')]"
            ]
            
            for selector in selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    if buttons:
                        # Click the first visible button
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                self.driver.execute_script("arguments[0].click();", button)
                                print(f"   -> ✅ Clicked button: {button.text[:50]}")
                                time.sleep(2)
                                return {'success': True, 'button_text': button.text}
                except:
                    continue
            
            return {'success': False, 'reason': 'No matching buttons found'}
        
        except Exception as e:
            return {'success': False, 'reason': f'Button click error: {str(e)}'}
    
    def wait_for_modal(self, step):
        """Wait for modal dialog to appear"""
        timeout = step.get('timeout', 5)
        
        try:
            # Wait for modal to appear
            modal_selectors = [
                "//div[contains(@class, 'modal') and contains(@class, 'fade') and contains(@class, 'in')]",
                "//div[contains(@class, 'modal') and @style and contains(@style, 'display: block')]",
                "//div[@id and contains(@id, 'modal')]",
                "//div[contains(@class, 'popup')]"
            ]
            
            for selector in modal_selectors:
                try:
                    modal = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if modal.is_displayed():
                        print(f"   -> ✅ Modal appeared")
                        time.sleep(1)  # Let modal fully load
                        return {'success': True}
                except TimeoutException:
                    continue
            
            # Check if page content changed (might indicate modal or new page)
            time.sleep(timeout)
            return {'success': True, 'reason': 'Assuming content loaded'}
        
        except Exception as e:
            return {'success': False, 'reason': f'Modal wait error: {str(e)}'}
    
    def select_price_option(self, step):
        """Select price option from dropdown or list"""
        target = step.get('target', 'highest_value')
        
        try:
            # Look for select dropdowns with price options
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            
            for select_element in selects:
                options = select_element.find_elements(By.TAG_NAME, "option")
                price_options = []
                
                for option in options:
                    price_match = re.search(r'\$(\d+)', option.text)
                    if price_match:
                        price_options.append((int(price_match.group(1)), option))
                
                if price_options:
                    # Sort by price and select based on target
                    price_options.sort(key=lambda x: x[0], reverse=(target == 'highest_value'))
                    selected_price, selected_option = price_options[0]
                    
                    select = Select(select_element)
                    select.select_by_visible_text(selected_option.text)
                    
                    print(f"   -> ✅ Selected price option: ${selected_price}")
                    time.sleep(1)
                    return {'success': True, 'selected_price': selected_price}
            
            return {'success': False, 'reason': 'No price selection options found'}
        
        except Exception as e:
            return {'success': False, 'reason': f'Price selection error: {str(e)}'}
    
    def fill_form_smart(self, step):
        """Smart form filling with fake data"""
        form_type = step.get('form_type', 'checkout')
        
        try:
            # Find forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            if not forms:
                return {'success': False, 'reason': 'No forms found'}
            
            # Use the most relevant form
            target_form = forms[0]
            for form in forms:
                if any(keyword in form.get_attribute('action').lower() if form.get_attribute('action') else '' 
                      for keyword in ['checkout', 'payment', 'order']):
                    target_form = form
                    break
            
            # Fill form fields
            filled_fields = 0
            inputs = target_form.find_elements(By.TAG_NAME, "input")
            
            fake_data = {
                'name': 'John Smith',
                'email': 'john.smith@protonmail.com',
                'address': '123 Main Street',
                'city': 'New York',
                'zip': '10001',
                'phone': '+1-555-0123',
                'country': 'United States'
            }
            
            for input_field in inputs:
                input_type = input_field.get_attribute('type')
                input_name = input_field.get_attribute('name')
                input_placeholder = input_field.get_attribute('placeholder')
                
                if input_type in ['hidden', 'submit', 'button']:
                    continue
                
                # Determine what to fill based on field characteristics
                value_to_fill = None
                
                if input_name:
                    name_lower = input_name.lower()
                    if 'name' in name_lower:
                        value_to_fill = fake_data['name']
                    elif 'email' in name_lower:
                        value_to_fill = fake_data['email']
                    elif 'address' in name_lower:
                        value_to_fill = fake_data['address']
                    elif 'city' in name_lower:
                        value_to_fill = fake_data['city']
                    elif 'zip' in name_lower or 'postal' in name_lower:
                        value_to_fill = fake_data['zip']
                    elif 'phone' in name_lower:
                        value_to_fill = fake_data['phone']
                    elif 'country' in name_lower:
                        value_to_fill = fake_data['country']
                
                if not value_to_fill and input_placeholder:
                    placeholder_lower = input_placeholder.lower()
                    if 'name' in placeholder_lower:
                        value_to_fill = fake_data['name']
                    elif 'email' in placeholder_lower:
                        value_to_fill = fake_data['email']
                
                if value_to_fill and input_field.is_displayed() and input_field.is_enabled():
                    try:
                        input_field.clear()
                        input_field.send_keys(value_to_fill)
                        filled_fields += 1
                    except:
                        continue
            
            # Fill select dropdowns
            selects = target_form.find_elements(By.TAG_NAME, "select")
            for select_element in selects:
                try:
                    select = Select(select_element)
                    options = select.options
                    if len(options) > 1:  # Skip if only one option
                        # Select first non-empty option
                        for option in options[1:]:
                            if option.text.strip():
                                select.select_by_visible_text(option.text)
                                filled_fields += 1
                                break
                except:
                    continue
            
            if filled_fields > 0:
                print(f"   -> ✅ Filled {filled_fields} form fields")
                return {'success': True, 'fields_filled': filled_fields}
            else:
                return {'success': False, 'reason': 'No fillable fields found'}
        
        except Exception as e:
            return {'success': False, 'reason': f'Form filling error: {str(e)}'}
    
    def submit_form_and_wait(self, step):
        """Submit form and wait for response"""
        wait_for = step.get('wait_for', 'payment_address')
        
        try:
            # Find and submit form
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            if not forms:
                return {'success': False, 'reason': 'No forms to submit'}
            
            # Submit the most relevant form
            target_form = forms[0]
            for form in forms:
                if any(keyword in form.get_attribute('action').lower() if form.get_attribute('action') else '' 
                      for keyword in ['checkout', 'payment', 'order']):
                    target_form = form
                    break
            
            # Try to find submit button first
            submit_buttons = target_form.find_elements(By.XPATH, 
                ".//input[@type='submit'] | .//button[@type='submit'] | .//button[contains(text(), 'Submit')]")
            
            if submit_buttons:
                self.driver.execute_script("arguments[0].click();", submit_buttons[0])
                print(f"   -> ✅ Clicked submit button")
            else:
                # Submit form directly
                target_form.submit()
                print(f"   -> ✅ Submitted form")
            
            # Wait for page to load
            time.sleep(5)
            
            # Check for success indicators
            page_source = self.driver.page_source.lower()
            success_indicators = ['address', 'payment', 'bitcoin', 'wallet', 'total', 'order']
            
            found_indicators = [indicator for indicator in success_indicators if indicator in page_source]
            
            if found_indicators:
                print(f"   -> ✅ Found success indicators: {found_indicators}")
                return {'success': True, 'indicators': found_indicators}
            else:
                return {'success': True, 'reason': 'Form submitted, checking for results'}
        
        except Exception as e:
            return {'success': False, 'reason': f'Form submission error: {str(e)}'}
    
    def click_continue_button(self, step):
        """Click continue/proceed/next button"""
        pattern = step.get('pattern', r'(?i)(continue|proceed|next|confirm)')
        
        try:
            continue_selectors = [
                "//button[contains(translate(text(), 'CONTINUE', 'continue'), 'continue')]",
                "//button[contains(translate(text(), 'PROCEED', 'proceed'), 'proceed')]",
                "//button[contains(translate(text(), 'NEXT', 'next'), 'next')]",
                "//button[contains(translate(text(), 'CONFIRM', 'confirm'), 'confirm')]",
                "//input[@type='submit' and contains(translate(@value, 'CONTINUE', 'continue'), 'continue')]"
            ]
            
            for selector in continue_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            print(f"   -> ✅ Clicked continue button: {button.text}")
                            time.sleep(2)
                            return {'success': True, 'button_text': button.text}
                except:
                    continue
            
            return {'success': False, 'reason': 'No continue buttons found'}
        
        except Exception as e:
            return {'success': False, 'reason': f'Continue button error: {str(e)}'}
    
    def extract_addresses_from_page(self):
        """Extract crypto addresses from current page"""
        addresses = []
        page_source = self.driver.page_source
        
        # Standard address patterns
        patterns = {
            'BTC': r'\b(bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})\b',
            'ETH': r'\b0x[a-fA-F0-9]{40}\b',
            'XMR': r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b',
            'TRON': r'\bT[1-9A-HJ-NP-Za-km-z]{33}\b',
            'SOL': r'\b[1-9A-HJ-NP-Za-km-z]{44}\b'
        }
        
        for chain, pattern in patterns.items():
            matches = re.findall(pattern, page_source)
            for match in matches:
                addresses.append({'chain': chain, 'address': match, 'method': 'smart_interaction'})
        
        return addresses
    
    def learn_from_execution(self, sequence, success):
        """Learn from the execution results"""
        interaction_sequence = []
        
        for log_entry in self.interaction_log:
            interaction_sequence.append({
                'step': log_entry['step'],
                'action': log_entry['action'],
                'success': log_entry['result']['success'],
                'details': log_entry['result']
            })
        
        # Learn from this interaction
        transaction_learner.learn_from_interaction(interaction_sequence, success)

def execute_smart_transaction(driver, html_content, url, title=""):
    """Main function to execute smart transaction flow"""
    from multi_step_transaction_learner import analyze_transaction_patterns, get_interaction_recommendations
    
    # Analyze page for transaction patterns
    page_analysis = analyze_transaction_patterns(html_content, url, title)
    
    if not page_analysis['detected_patterns']:
        return {'success': False, 'reason': 'No transaction patterns detected'}
    
    print(f"🔍 Detected patterns: {page_analysis['detected_patterns']}")
    print(f"📍 Current flow step: {page_analysis['flow_step']}")
    
    # Get interaction recommendations
    recommendations = get_interaction_recommendations(page_analysis)
    
    if not recommendations:
        return {'success': False, 'reason': 'No interaction recommendations available'}
    
    # Execute the transaction sequence
    executor = SmartInteractionExecutor(driver)
    results = executor.execute_transaction_sequence(recommendations)
    
    return results 