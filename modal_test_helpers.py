import time
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def get_random_suffix(length=5):
    """Generate a random suffix for unique identifiers"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def fill_visible_inputs_anywhere(driver, data_dict=None):
    """
    Fill all visible and enabled <input> fields in the DOM, regardless of form context.
    data_dict: Optional dict mapping field types/names to values (e.g., {'email': ..., 'username': ...})
    """
    random_suffix = get_random_suffix()
    timestamp = int(time.time())
    # Default data if not provided
    default_data = {
        'email': f'user_{timestamp}_{random_suffix}@protonmail.com',
        'username': f'user_{timestamp}_{random_suffix}',
        'name': f'John Doe {random_suffix}',
        'first_name': f'John{random_suffix}',
        'last_name': f'Doe{random_suffix}',
        'password': 'SecurePass123!',
        'phone': '+1-555-123-4567',
        'address': '123 Main Street',
        'city': 'New York',
        'zip': '10001',
    }
    if data_dict:
        default_data.update(data_dict)
    
    inputs = driver.find_elements(By.TAG_NAME, 'input')
    fields_filled = 0
    for inp in inputs:
        try:
            if not inp.is_displayed() or not inp.is_enabled():
                continue
            field_type = inp.get_attribute('type') or 'text'
            field_name = (inp.get_attribute('name') or '').lower()
            field_id = (inp.get_attribute('id') or '').lower()
            field_placeholder = (inp.get_attribute('placeholder') or '').lower()
            field_text = f"{field_name} {field_id} {field_placeholder}".lower()
            value_to_fill = None
            # Priority: email, username, password, name, phone, address, city, zip
            if field_type == 'email' or 'email' in field_text:
                value_to_fill = default_data['email']
            elif field_type == 'password' or 'pass' in field_text:
                value_to_fill = default_data['password']
            elif 'user' in field_text or 'login' in field_text:
                value_to_fill = default_data['username']
            elif 'first' in field_text and 'name' in field_text:
                value_to_fill = default_data['first_name']
            elif 'last' in field_text and 'name' in field_text:
                value_to_fill = default_data['last_name']
            elif 'name' in field_text:
                value_to_fill = default_data['name']
            elif 'phone' in field_text or 'mobile' in field_text:
                value_to_fill = default_data['phone']
            elif 'address' in field_text:
                value_to_fill = default_data['address']
            elif 'city' in field_text:
                value_to_fill = default_data['city']
            elif 'zip' in field_text or 'postal' in field_text:
                value_to_fill = default_data['zip']
            elif field_type == 'text' and not value_to_fill:
                value_to_fill = default_data['username']
            if value_to_fill:
                inp.clear()
                inp.send_keys(value_to_fill)
                print(f"[fill_visible_inputs_anywhere] Filled '{field_name or field_id or field_placeholder or field_type}' with '{value_to_fill}'")
                fields_filled += 1
        except Exception as e:
            print(f"[fill_visible_inputs_anywhere] Could not fill input: {e}")
            continue
    print(f"[fill_visible_inputs_anywhere] Total fields filled: {fields_filled}")
    return fields_filled

def handle_generic_email_modal(driver, context):
    """
    Handle generic email modal by looking for email inputs and submit buttons.
    Returns True if modal was handled, False otherwise.
    """
    try:
        print(f"[handle_generic_email_modal] Starting modal detection for {context}")
        
        # Look for common modal selectors
        modal_selectors = [
            '.modal', '.popup', '.overlay', '.dialog', '[role="dialog"]',
            '.lightbox', '.modal-dialog', '.modal-content'
        ]
        
        for selector in modal_selectors:
            try:
                print(f"[handle_generic_email_modal] Checking selector: {selector}")
                modals = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"[handle_generic_email_modal] Found {len(modals)} elements with selector {selector}")
                
                for i, modal in enumerate(modals):
                    print(f"[handle_generic_email_modal] Checking modal {i+1}/{len(modals)}")
                    if modal.is_displayed():
                        print(f"[handle_generic_email_modal] Modal {i+1} is displayed")
                        
                        # Look for email input in the modal
                        email_inputs = modal.find_elements(By.XPATH, 
                            ".//input[@type='email'] | .//input[contains(@placeholder, 'email')] | .//input[contains(@placeholder, 'mail')]")
                        
                        print(f"[handle_generic_email_modal] Found {len(email_inputs)} email inputs in modal")
                        
                        if email_inputs:
                            email_input = email_inputs[0]
                            print(f"[handle_generic_email_modal] Email input found: {email_input.get_attribute('id')} - {email_input.get_attribute('placeholder')}")
                            
                            # Generate email
                            timestamp = int(time.time())
                            random_suffix = get_random_suffix()
                            email = f'user_{timestamp}_{random_suffix}@protonmail.com'
                            print(f"[handle_generic_email_modal] Generated email: {email}")
                            
                            # Fill email
                            try:
                                email_input.clear()
                                email_input.send_keys(email)
                                print(f"[handle_generic_email_modal] Successfully filled email input")
                                
                                # Verify the email was filled
                                filled_value = email_input.get_attribute("value")
                                print(f"[handle_generic_email_modal] Email input value after filling: {filled_value}")
                                
                            except Exception as e:
                                print(f"[handle_generic_email_modal] Error filling email: {e}")
                                continue
                            
                            # Look for submit button
                            submit_buttons = modal.find_elements(By.XPATH,
                                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')] | " +
                                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')] | " +
                                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')] | " +
                                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')] | " +
                                ".//input[@type='submit'] | .//button[@type='submit']")
                            
                            print(f"[handle_generic_email_modal] Found {len(submit_buttons)} submit buttons")
                            
                            if submit_buttons:
                                submit_button = submit_buttons[0]
                                print(f"[handle_generic_email_modal] Submit button text: {submit_button.text}")
                                submit_button.click()
                                print(f"[handle_generic_email_modal] Filled email and clicked submit in {context}")
                                return True
                            else:
                                # Try pressing Enter on the email input
                                print(f"[handle_generic_email_modal] No submit button found, trying Enter key")
                                email_input.send_keys(Keys.RETURN)
                                print(f"[handle_generic_email_modal] Filled email and pressed Enter in {context}")
                                return True
                    else:
                        print(f"[handle_generic_email_modal] Modal {i+1} is not displayed")
            except Exception as e:
                print(f"[handle_generic_email_modal] Error with selector {selector}: {e}")
                continue
        
        print(f"[handle_generic_email_modal] No modal found, checking for email inputs anywhere on page")
        
        # If no modal found, look for email inputs anywhere on the page
        email_inputs = driver.find_elements(By.XPATH, 
            "//input[@type='email'] | //input[contains(@placeholder, 'email')] | //input[contains(@placeholder, 'mail')]")
        
        print(f"[handle_generic_email_modal] Found {len(email_inputs)} email inputs on page")
        
        if email_inputs:
            email_input = email_inputs[0]
            print(f"[handle_generic_email_modal] Email input found: {email_input.get_attribute('id')} - {email_input.get_attribute('placeholder')}")
            
            if email_input.is_displayed():
                print(f"[handle_generic_email_modal] Email input is displayed")
                
                # Generate email
                timestamp = int(time.time())
                random_suffix = get_random_suffix()
                email = f'user_{timestamp}_{random_suffix}@protonmail.com'
                print(f"[handle_generic_email_modal] Generated email: {email}")
                
                # Fill email
                try:
                    email_input.clear()
                    email_input.send_keys(email)
                    print(f"[handle_generic_email_modal] Successfully filled email input")
                    
                    # Verify the email was filled
                    filled_value = email_input.get_attribute("value")
                    print(f"[handle_generic_email_modal] Email input value after filling: {filled_value}")
                    
                except Exception as e:
                    print(f"[handle_generic_email_modal] Error filling email: {e}")
                    return False
                
                # Look for nearby submit button
                try:
                    parent_form = email_input.find_element(By.XPATH, "./ancestor::form")
                    if parent_form:
                        submit_buttons = parent_form.find_elements(By.XPATH,
                            ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')] | " +
                            ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')] | " +
                            ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')] | " +
                            ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok')] | " +
                            ".//input[@type='submit'] | .//button[@type='submit']")
                        
                        if submit_buttons:
                            submit_button = submit_buttons[0]
                            submit_button.click()
                            print(f"[handle_generic_email_modal] Filled email and clicked submit in form for {context}")
                            return True
                except:
                    pass
                
                # Try pressing Enter
                email_input.send_keys(Keys.RETURN)
                print(f"[handle_generic_email_modal] Filled email and pressed Enter for {context}")
                return True
            else:
                print(f"[handle_generic_email_modal] Email input is not displayed")
        
        print(f"[handle_generic_email_modal] No email inputs found or handled")
        return False
        
    except Exception as e:
        print(f"[handle_generic_email_modal] Error: {e}")
        return False

def try_handle_generic_email_modal_with_retries(driver, worker_id, context):
    """
    Try to handle generic email modal up to 3 times with 2s wait between attempts. Logs each attempt.
    Fallback: fill all visible inputs and try to click a submit/payment button.
    """
    for attempt in range(1, 4):
        print(f"🛠️ [{worker_id}] Attempt {attempt}/3: Checking for generic email modal after {context}...")
        time.sleep(2)
        try:
            if handle_generic_email_modal(driver, context):
                print(f"✅ [{worker_id}] Generic email modal handled after {context} (attempt {attempt}).")
                return True
            else:
                print(f"🛠️ [{worker_id}] No generic email modal found after {context} (attempt {attempt}).")
        except Exception as e:
            print(f"⚠️ [{worker_id}] Error in generic email modal handler after {context} (attempt {attempt}): {e}")
    
    # Fallback: fill all visible inputs and try to click a submit/payment button
    print(f"[fallback] No modal/email handled after retries for {context}. Trying fill_visible_inputs_anywhere...")
    fields_filled = fill_visible_inputs_anywhere(driver)
    if fields_filled > 0:
        print(f"[fallback] Filled {fields_filled} visible input fields. Attempting to click a submit/payment button...")
        buttons = driver.find_elements(By.XPATH, "//button | //input[@type='submit'] | //input[@type='button']")
        for btn in buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    btn_text = (btn.text or btn.get_attribute('value') or '').lower()
                    if any(word in btn_text for word in ['pay', 'submit', 'buy', 'send', 'continue', 'ok', 'download']):
                        btn.click()
                        print(f"[fallback] Clicked button: {btn_text}")
                        return True
            except Exception as e:
                print(f"[fallback] Could not click button: {e}")
                continue
        print(f"[fallback] No suitable button found to click after filling inputs.")
    else:
        print(f"[fallback] No visible input fields were filled.")
    return False 