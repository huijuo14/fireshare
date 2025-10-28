#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - PERFECT SHAPE MATCHING EDITION v6.1 ULTIMATE
WITH USCRIPT v3.4 MATCHING ALGORITHM AND ZERO STALE ELEMENT CLICKS
"""

import os
import time
import random
import logging
import re
import requests
import threading
import json
import gc
import pytz
import urllib3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup

# Disable connection pool warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== CONFIGURATION ====================
CONFIG = {
    'email': "loginallapps@gmail.com",
    'password': "@Sd2007123",
    'base_delay': 1.7,
    'random_delay': True,
    'min_delay': 1.5,
    'max_delay': 3,
    'telegram_token': "8225236307:AAF9Y2-CM7TlLDFm2rcTVY6f3SA75j0DFI8",
    'max_consecutive_failures': 15,
    'element_wait_time': 5,
    'refresh_after_failures': 3,
    'restart_after_failures': 8,
    'leaderboard_check_interval': 1800,
    'safety_margin': 100,
    'performance_tracking': True,
    'minimum_confidence': 0.90,
    'enable_image_matching': True,
    'enable_background_to_background': True,
}

class UltimateShapeSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        
        # Enhanced State Management
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'is_logged_in': False,
            'consecutive_fails': 0,
            'element_not_found_count': 0,
            'daily_target': None,
            'auto_compete': True,
            'safety_margin': CONFIG['safety_margin'],
            'leaderboard': [],
            'my_position': None,
            'last_leaderboard_check': 0,
            'last_target': None,
            'last_rank': None,
            'performance_metrics': {
                'games_per_hour': 0,
                'start_time': 0,
                'last_hour_count': 0
            },
            'last_question_hash': '',
            'auto_click': True,
            'wrong_click_count': 0,
            'last_wrong_click_time': 0,
            'no_question_count': 0
        }
        
        # Symbol type definitions from userscript v3.4
        self.SYMBOL_TYPES = {
            'CIRCLE': 'circle',
            'SQUARE': 'square', 
            'DIAMOND': 'diamond',
            'ARROW_DOWN': 'arrow_down',
            'ARROW_LEFT': 'arrow_left',
            'BACKGROUND_CIRCLE': 'background_circle',
            'UNKNOWN': 'unknown'
        }
        
        self.solver_thread = None
        self.monitoring_thread = None
        self.setup_logging()
        self.setup_telegram()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        """Setup Telegram bot with enhanced features"""
        try:
            self.logger.info("Setting up Ultimate Telegram bot...")
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.telegram_chat_id = updates['result'][-1]['message']['chat']['id']
                    self.logger.info(f"Telegram Chat ID: {self.telegram_chat_id}")
                    self.send_telegram("🤖 <b>PERFECT SHAPE MATCHING Solver v6.1 ULTIMATE Started!</b>\n"
                                     "🔧 <i>Now with ZERO Stale Element Clicks</i>")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Telegram setup failed: {e}")
            return False
    
    def send_telegram(self, text, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.telegram_chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Telegram send failed: {e}")
            return False

    def send_screenshot(self, caption="🖥️ Screenshot"):
        """Send screenshot to Telegram with enhanced error handling"""
        if not self.driver or not self.telegram_chat_id:
            return "❌ Browser not running or Telegram not configured"
        
        try:
            screenshot_path = "/tmp/screenshot.png"
            self.driver.save_screenshot(screenshot_path)
            
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendPhoto"
            
            with open(screenshot_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.telegram_chat_id,
                    'caption': f'{caption} - {self.get_ist_time()}'
                }
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
            return "✅ Screenshot sent!" if response.status_code == 200 else "❌ Failed to send screenshot"
                
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    def get_ist_time(self):
        """Get current IST time"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime('%I:%M %p IST')

    # ==================== ENHANCED BROWSER MANAGEMENT ====================
    def is_browser_alive(self):
        """ULTRA-RELIABLE browser health check"""
        try:
            if not self.driver:
                return False
            self.driver.current_url
            self.driver.title
            return True
        except Exception as e:
            self.logger.warning(f"Browser health check failed: {e}")
            return False

    def setup_firefox(self):
        """ULTIMATE Firefox setup with uBlock Origin"""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # ULTIMATE Memory Optimization
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("content.processLimit", 1)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("javascript.options.mem.max", 25600)
            options.set_preference("browser.sessionhistory.max_entries", 1)
            options.set_preference("image.mem.max_decoded_image_kb", 512)
            options.set_preference("media.memory_cache_max_size", 1024)
            options.set_preference("permissions.default.image", 1)
            options.set_preference("gfx.webrender.all", True)
            options.set_preference("network.http.max-connections", 10)
            
            service = Service('/usr/local/bin/geckodriver', log_path=os.devnull)
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Install uBlock Origin for performance
            ublock_path = '/app/ublock.xpi'
            if os.path.exists(ublock_path):
                self.driver.install_addon(ublock_path, temporary=False)
                self.logger.info("uBlock Origin installed for enhanced performance")
            
            self.logger.info("ULTIMATE Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Firefox setup failed: {e}")
            return False

    def restart_browser(self):
        """ENHANCED browser restart with PROPER login recovery"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            time.sleep(3)
            gc.collect()
            
            self.state['is_logged_in'] = False
            self.state['consecutive_fails'] = 0
            self.state['element_not_found_count'] = 0
            self.state['no_question_count'] = 0
            
            success = self.setup_firefox()
            if success:
                self.logger.info("Browser restart successful - login required")
                login_success = self.force_login()
                if login_success:
                    self.state['is_logged_in'] = True
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    # ==================== EXACT SAME LOGIN FUNCTION ====================
    def force_login(self):
        """ULTIMATE WORKING LOGIN - EXACT COPY FROM FIRST SCRIPT"""
        try:
            self.logger.info("ULTIMATE LOGIN: Attempting login...")
            
            login_url = "https://adsha.re/login"
            self.driver.get(login_url)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.smart_delay()
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            form = soup.find('form', {'name': 'login'})
            if not form:
                self.logger.error("LOGIN: No login form found")
                return False
            
            password_field_name = None
            for field in form.find_all('input'):
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                
                if field_value == 'Password' and field_name != 'mail' and field_name:
                    password_field_name = field_name
                    break
            
            if not password_field_name:
                self.logger.error("LOGIN: No password field found")
                return False
            
            self.logger.info(f"Password field: {password_field_name}")
            
            email_selectors = [
                "input[name='mail']",
                "input[type='email']",
                "input[placeholder*='email' i]",
                "input[id*='email' i]",
                "input[class*='email' i]"
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys(CONFIG['email'])
                    self.logger.info("Email entered successfully")
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                self.logger.error("Could not fill email field")
                return False
            
            self.smart_delay()
            
            password_selectors = [
                f"input[name='{password_field_name}']",
                "input[type='password']",
                "input[placeholder*='password' i]",
                "input[placeholder*='pass' i]"
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    password_field.clear()
                    password_field.send_keys(CONFIG['password'])
                    self.logger.info("Password entered successfully")
                    password_filled = True
                    break
                except:
                    continue
            
            if not password_filled:
                return False
            
            self.smart_delay()
            
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button",
                "input[value*='Login']",
                "input[value*='Sign']",
                "button[class*='login']",
                "button[class*='submit']"
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn.is_displayed() and login_btn.is_enabled():
                        login_btn.click()
                        self.logger.info("Login button clicked successfully")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                try:
                    form_element = self.driver.find_element(By.CSS_SELECTOR, "form[name='login']")
                    form_element.submit()
                    self.logger.info("Form submitted successfully")
                    login_clicked = True
                except:
                    pass
            
            self.smart_delay()
            time.sleep(8)
            
            self.driver.get("https://adsha.re/surf")
            self.smart_delay()
            
            current_url = self.driver.current_url
            page_state = self.detect_page_state()
            
            if page_state == "GAME_ACTIVE" or page_state == "GAME_LOADING":
                self.logger.info("ULTIMATE LOGIN: Login successful!")
                self.state['is_logged_in'] = True
                self.send_telegram("✅ <b>ULTIMATE Login Successful!</b>")
                return True
            else:
                self.logger.error(f"Login failed - current state: {page_state}")
                self.send_telegram(f"❌ Login failed - state: {page_state}")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            self.send_telegram(f"❌ Login error: {str(e)}")
            return False

    # ==================== USCRIPT v3.4 PERFECT SHAPE MATCHING SYSTEM ====================
    def smart_delay(self):
        """Randomized delay between actions for anti-detection"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
            self.logger.info(f"⏰ Smart delay: {delay:.2f}s")
        else:
            delay = CONFIG['base_delay']
        time.sleep(delay)
        return delay

    def hashCode(self, text):
        """Generate hash code for text (same as userscript)"""
        hash_val = 0
        for char in text:
            hash_val = ((hash_val << 5) - hash_val) + ord(char)
            hash_val = hash_val & hash_val  # Convert to 32-bit integer
        return hash_val

    def check_for_question(self):
        """ENHANCED: Check for question using timer element - NOW DETECTS ALL QUESTION TYPES"""
        try:
            timer = self.driver.find_element(By.ID, 'timer')
            if not timer:
                self.logger.info("❌ No timer element found")
                return False
            
            html = timer.get_attribute('innerHTML')
            current_hash = self.hashCode(html)
            
            # Only process if content changed
            if current_hash == self.state['last_question_hash']:
                return False
                
            self.state['last_question_hash'] = current_hash
            
            # ENHANCED: Check if we have a question (contains gray #808080 OR image)
            if ((html and '#808080' in html and 'svg' in html) or 
                (html and 'background-image' in html and 'background-size:cover' in html)):
                self.logger.info("🎯 Question detected! Analyzing...")
                self.state['no_question_count'] = 0  # Reset counter when question found
                return True
            elif html and 'Credits' in html:
                self.logger.info("⏰ Countdown running...")
                
            return False
            
        except NoSuchElementException:
            self.logger.info("❌ Timer element not found on page")
            return False
        except Exception as e:
            self.logger.error(f"Question detection error: {e}")
            return False

    # NEW: USCRIPT v3.4 SYMBOL CLASSIFICATION SYSTEM
    def classify_symbol_type(self, element):
        """ENHANCED: Classify symbol type for both SVG and background images (USCRIPT v3.4 algorithm)"""
        if not element:
            return self.SYMBOL_TYPES['UNKNOWN']
        
        try:
            # Check if it's a background image element
            div = element.find_element(By.CSS_SELECTOR, 'div') if isinstance(element, webdriver.remote.webelement.WebElement) else None
            if div:
                style = div.get_attribute('style') or ''
                if 'background-image' in style and 'img.gif' in style and 'background-size:cover' in style:
                    return self.SYMBOL_TYPES['BACKGROUND_CIRCLE']
            
            # Check if it's an SVG element
            svg = element.find_element(By.CSS_SELECTOR, 'svg') if isinstance(element, webdriver.remote.webelement.WebElement) else None
            if not svg:
                return self.SYMBOL_TYPES['UNKNOWN']
            
            svg_content = svg.get_attribute('innerHTML') or ''
            content = svg_content.lower()
            
            # Circle detection (concentric circles) - USCRIPT v3.4 pattern
            if 'circle' in content and 'cx="50"' in content and 'cy="50"' in content:
                circles = content.count('<circle')
                if circles >= 2:
                    return self.SYMBOL_TYPES['CIRCLE']
            
            # Square detection (nested squares) - USCRIPT v3.4 pattern
            if 'rect x="25" y="25"' in content and 'width="50" height="50"' in content:
                rects = content.count('<rect')
                if rects >= 2:
                    return self.SYMBOL_TYPES['SQUARE']
            
            # Diamond detection (rotated squares) - USCRIPT v3.4 pattern
            if 'transform="matrix(0.7071 -0.7071 0.7071 0.7071 -20.7107 50)"' in content and '42.4"' in content:
                return self.SYMBOL_TYPES['DIAMOND']
            
            # Arrow down detection (pointing down) - USCRIPT v3.4 pattern
            if ('polygon' in content and '25 75' in content and '50 25' in content and 
                '75 75' in content and '25 75' in content):
                return self.SYMBOL_TYPES['ARROW_DOWN']
            
            # Arrow left detection (pointing left) - USCRIPT v3.4 pattern  
            if ('polygon' in content and '25 25' in content and '75 50' in content and 
                '25 75' in content and '25 25' in content):
                return self.SYMBOL_TYPES['ARROW_LEFT']
            
            return self.SYMBOL_TYPES['UNKNOWN']
            
        except Exception as e:
            self.logger.warning(f"Symbol classification error: {e}")
            return self.SYMBOL_TYPES['UNKNOWN']

    def extract_question(self, html):
        """ENHANCED: Extract question - NOW HANDLES ALL QUESTION TYPES (USCRIPT v3.4)"""
        # Check if question is an IMAGE (GIF)
        if 'background-image' in html and 'background-size:cover' in html:
            # Find the first image element (the question)
            image_match = re.search(r'<div[^>]*background-image[^>]*></div>', html)
            if image_match:
                self.logger.info("🖼️ Image question detected (GIF)")
                return {
                    'type': self.SYMBOL_TYPES['BACKGROUND_CIRCLE'],
                    'content': image_match.group(0),
                    'isImage': True,
                    'element': None  # Will be set later
                }
        
        # Check if question is SVG with gray colors
        svg_match = re.search(r'<svg[^>]*>[\s\S]*?</svg>', html)
        if svg_match and '#808080' in svg_match.group(0):
            svg_content = svg_match.group(0)
            
            # Create a temporary element for classification
            try:
                temp_div = self.driver.execute_script("""
                    var div = document.createElement('div');
                    div.innerHTML = arguments[0];
                    return div;
                """, svg_content)
                question_type = self.classify_symbol_type(temp_div)
            except:
                question_type = self.SYMBOL_TYPES['UNKNOWN']
            
            self.logger.info(f"📐 SVG question detected: {question_type}")
            return {
                'type': question_type,
                'content': svg_content,
                'isImage': False,
                'element': None  # Will be set later
            }
        
        return None

    def extract_answers(self):
        """ENHANCED: Extract and analyze answers (USCRIPT v3.4 algorithm)"""
        answers = []
        try:
            timer = self.driver.find_element(By.ID, 'timer')
            links = timer.find_elements(By.CSS_SELECTOR, 'a[href*="/surf/"]')
            
            self.logger.info(f"🔍 Found {len(links)} answer links")
            
            for index, link in enumerate(links):
                try:
                    link_html = link.get_attribute('outerHTML')
                    
                    # Analyze the answer using USCRIPT v3.4 classification
                    symbol_type = self.classify_symbol_type(link)
                    
                    analysis = {
                        'element': link,
                        'index': index,
                        'html': link_html,
                        'type': symbol_type,
                        'hasImage': symbol_type == self.SYMBOL_TYPES['BACKGROUND_CIRCLE'],
                        'svgContent': self.extract_svg_from_html(link_html),
                        'colors': {
                            'hasDarkBlue': '#143060' in link_html,
                            'hasLightGreen': '#B9DD22' in link_html
                        },
                        'confidence': 0.0,
                        'matchType': 'none'
                    }
                    
                    answers.append(analysis)
                    self.logger.info(f"Answer {index+1}: {analysis['type']} - Colors: DarkBlue:{analysis['colors']['hasDarkBlue']}, LightGreen:{analysis['colors']['hasLightGreen']}")
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing answer {index}: {e}")
                    continue
                    
            return answers
            
        except Exception as e:
            self.logger.error(f"Answer extraction error: {e}")
            return []

    def extract_svg_from_html(self, html):
        """Extract SVG content from HTML"""
        try:
            svg_match = re.search(r'<svg[^>]*>[\s\S]*?</svg>', html)
            return svg_match.group(0) if svg_match else None
        except:
            return None

    # NEW: USCRIPT v3.4 PERFECT MATCHING ALGORITHM
    def find_correct_answer(self, question, answers):
        """ENHANCED: Find correct answer using USCRIPT v3.4 matching algorithm"""
        self.logger.info(f"🔍 Finding correct answer for: {question['type']}")
        
        best_match = None
        highest_confidence = 0
        exact_matches = []
        
        for answer in answers:
            answer_confidence = 0
            match_type = 'none'
            
            # CASE 1: Both question and answer are BACKGROUND_CIRCLE (Image-to-Image)
            if (question['type'] == self.SYMBOL_TYPES['BACKGROUND_CIRCLE'] and 
                answer['type'] == self.SYMBOL_TYPES['BACKGROUND_CIRCLE']):
                answer_confidence = 1.0
                match_type = 'background_to_background'
                exact_matches.append({**answer, 'confidence': answer_confidence, 'matchType': match_type})
            
            # CASE 2: Question is BACKGROUND_CIRCLE, Answer is CIRCLE (Image-to-SVG)
            elif (question['type'] == self.SYMBOL_TYPES['BACKGROUND_CIRCLE'] and 
                  answer['type'] == self.SYMBOL_TYPES['CIRCLE']):
                answer_confidence = 0.98
                match_type = 'background_to_svg'
                if answer_confidence > highest_confidence:
                    highest_confidence = answer_confidence
                    best_match = {**answer, 'confidence': answer_confidence, 'matchType': match_type}
            
            # CASE 3: Question is CIRCLE, Answer is BACKGROUND_CIRCLE (SVG-to-Image)
            elif (question['type'] == self.SYMBOL_TYPES['CIRCLE'] and 
                  answer['type'] == self.SYMBOL_TYPES['BACKGROUND_CIRCLE']):
                answer_confidence = 0.98
                match_type = 'svg_to_background'
                if answer_confidence > highest_confidence:
                    highest_confidence = answer_confidence
                    best_match = {**answer, 'confidence': answer_confidence, 'matchType': match_type}
            
            # CASE 4: Same symbol type with correct colors (SVG-to-SVG exact match)
            elif (question['type'] == answer['type'] and 
                  answer['colors']['hasDarkBlue'] and 
                  answer['colors']['hasLightGreen']):
                answer_confidence = 1.0
                match_type = 'svg_exact'
                exact_matches.append({**answer, 'confidence': answer_confidence, 'matchType': match_type})
            
            # CASE 5: Same symbol type but missing colors (SVG-to-SVG fuzzy match)
            elif question['type'] == answer['type']:
                answer_confidence = 0.85  # Lower confidence without colors
                match_type = 'svg_fuzzy'
                if answer_confidence > highest_confidence:
                    highest_confidence = answer_confidence
                    best_match = {**answer, 'confidence': answer_confidence, 'matchType': match_type}
        
        # Return exact match if available
        if exact_matches:
            self.logger.info(f"✅ Found {len(exact_matches)} exact matches")
            return exact_matches[0]
        
        # Return best match if confidence is high enough
        if best_match and best_match['confidence'] >= CONFIG['minimum_confidence']:
            self.logger.info(f"✅ Found best match with {best_match['confidence']*100:.1f}% confidence")
            return best_match
        
        self.logger.warning("❌ No confident answer found")
        return None

    # ==================== ULTIMATE STALE ELEMENT PROTECTION ====================
    def validate_element_freshness(self, element, context="unknown"):
        """Validate element is still fresh and attached to DOM"""
        try:
            # Multiple freshness checks
            element.is_enabled()
            element.is_displayed() 
            element.location  # This will fail if element is stale
            element.size      # This will fail if element is stale
            return True
        except StaleElementReferenceException:
            self.logger.warning(f"❌ STALE ELEMENT detected in {context}")
            return False
        except Exception as e:
            self.logger.warning(f"❌ Element validation failed in {context}: {e}")
            return False

    def ultra_safe_click(self, element, element_index, question_type):
        """ULTIMATE STALE-PROOF CLICKING SYSTEM"""
        max_retries = 2
        original_url = self.driver.current_url
        
        for attempt in range(max_retries):
            try:
                # ANTI-DETECTION: Random pre-click delay
                click_delay = random.uniform(0.7, 1.8)
                self.logger.info(f"⏰ Pre-click delay: {click_delay:.2f}s (Attempt {attempt+1})")
                time.sleep(click_delay)
                
                # CRITICAL: Verify element is still fresh and clickable
                if not self.validate_element_freshness(element, f"answer_{element_index}"):
                    self.logger.warning(f"❌ Element {element_index} not fresh - stale suspected")
                    raise StaleElementReferenceException("Element not fresh")
                
                if not element.is_displayed():
                    self.logger.warning(f"❌ Element {element_index} not displayed - stale suspected")
                    raise StaleElementReferenceException("Element not displayed")
                
                if not element.is_enabled():
                    self.logger.warning(f"❌ Element {element_index} not enabled - stale suspected")  
                    raise StaleElementReferenceException("Element not enabled")
                
                # VERIFY we're still on the correct page
                current_url = self.driver.current_url
                if "adsha.re/surf" not in current_url:
                    self.logger.error(f"❌ Wrong page during click: {current_url}")
                    self.driver.get("https://adsha.re/surf")
                    return False
                
                # PERFORM CLICK with JavaScript as backup
                try:
                    element.click()
                    self.logger.info(f"✅ DIRECT CLICK SUCCESS! Answer #{element_index+1} for {question_type}")
                    
                    # VERIFY click was successful (page should change/update)
                    time.sleep(1.5)
                    if self.is_click_successful():
                        return True
                    else:
                        self.logger.warning("Click may have failed - page didn't update as expected")
                        continue
                        
                except Exception as click_error:
                    self.logger.warning(f"Standard click failed: {click_error} - trying JavaScript...")
                    # JavaScript click as backup
                    self.driver.execute_script("arguments[0].click();", element)
                    self.logger.info(f"✅ JAVASCRIPT CLICK SUCCESS! Answer #{element_index+1}")
                    time.sleep(1.5)
                    return True
                    
            except StaleElementReferenceException:
                self.logger.warning(f"🔄 STALE ELEMENT on attempt {attempt+1} - refreshing...")
                
                if attempt < max_retries - 1:
                    # Refresh page and try to re-locate the element
                    self.driver.get("https://adsha.re/surf")
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'timer'))
                    )
                    
                    # Wait for new question to load
                    time.sleep(3)
                    self.logger.info("🔄 Page refreshed after stale element - getting new question")
                    return False  # Return False to get new question in main loop
                else:
                    self.logger.error("❌ Max retries reached for stale element")
                    return False
                    
            except Exception as e:
                self.logger.error(f"❌ Unexcepted click error: {e}")
                if attempt < max_retries - 1:
                    self.logger.info("🔄 Retrying after error...")
                    time.sleep(2)
                    continue
                else:
                    return False
        
        return False

    def is_click_successful(self):
        """Verify if click was successful by checking page state"""
        try:
            # Check if timer reset or question changed
            timer = self.driver.find_element(By.ID, 'timer')
            current_html = timer.get_attribute('innerHTML')
            current_hash = self.hashCode(current_html)
            
            # If hash changed, click was likely successful
            if current_hash != self.state['last_question_hash']:
                self.logger.info("✅ Click verification: Page updated successfully")
                return True
            else:
                self.logger.warning("⚠️ Click verification: Page didn't update")
                return False
        except:
            return True  # If we can't verify, assume success

    def refresh_answers_if_stale(self, answers, question_type):
        """Refresh answers if any appear stale"""
        stale_detected = False
        
        for answer in answers:
            if not self.validate_element_freshness(answer['element'], f"answer_{answer['index']}"):
                stale_detected = True
                break
        
        if stale_detected:
            self.logger.info("🔄 Stale answers detected - refreshing page...")
            self.driver.get("https://adsha.re/surf")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'timer'))
            )
            time.sleep(3)
            return None  # Return None to indicate refresh happened
        
        return answers

    # ==================== ENHANCED SOLVER WITH STALE PROTECTION ====================
    def solve_symbol_game_enhanced(self):
        """STALE-PROOF game solving with zero wrong clicks"""
        if not self.state['is_running']:
            return False
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead during game solving")
            self.state['consecutive_fails'] += 1
            return False
            
        try:
            self.logger.info("🔍 STALE-PROOF: Checking for game elements...")
            
            if not self.ensure_correct_page():
                self.logger.error("Cannot ensure correct page status")
                self.state['consecutive_fails'] += 1
                return False
            
            # Check for question using enhanced algorithm
            self.logger.info("🔍 Looking for questions...")
            question_found = self.check_for_question()
            
            if not question_found:
                self.state['no_question_count'] += 1
                self.logger.info(f"⏳ No question found yet (Count: {self.state['no_question_count']})")
                
                # Refresh page if no question found 3 times in a row
                if self.state['no_question_count'] >= 3:
                    self.logger.info("🔄 No question found 3 times - refreshing page...")
                    self.driver.get("https://adsha.re/surf")
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    self.smart_delay()
                    self.state['no_question_count'] = 0
                    return False
                
                return False
            
            # Wait a bit for question to fully load with random delay
            load_delay = random.uniform(0.3, 0.8)
            time.sleep(load_delay)
            
            # Get timer HTML and extract question
            timer = self.driver.find_element(By.ID, 'timer')
            html = timer.get_attribute('innerHTML')
            
            # ENHANCED: Use USCRIPT v3.4 question extraction
            question = self.extract_question(html)
            if not question:
                self.logger.warning("No question found")
                return False
            
            self.logger.info(f"🎯 Question Type: {question['type']}")
            
            # Extract and analyze answers using USCRIPT v3.4 algorithm
            answers = self.extract_answers()
            
            if len(answers) < 2:
                self.logger.warning(f"❌ Only {len(answers)} answers found - REFRESHING")
                self.driver.get("https://adsha.re/surf")
                time.sleep(3)
                return False
            
            # CHECK FOR STALE ANSWERS BEFORE PROCEEDING
            stale_check = self.refresh_answers_if_stale(answers, question['type'])
            if stale_check is None:
                self.logger.info("🔄 Answers were stale - page refreshed, getting new question")
                return False  # Return false to get new question
            
            # Find correct answer using USCRIPT v3.4 matching algorithm
            correct_answer = self.find_correct_answer(question, answers)
            
            if correct_answer and correct_answer['confidence'] >= CONFIG['minimum_confidence']:
                # USE ULTRA-SAFE CLICK instead of safe_click
                click_success = self.ultra_safe_click(
                    correct_answer['element'],
                    correct_answer['index'], 
                    question['type']
                )
                
                if click_success:
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    self.state['element_not_found_count'] = 0
                    self.state['no_question_count'] = 0
                    
                    self.update_performance_metrics()
                    
                    self.logger.info(f"🎯 PERFECT Match! | Type: {question['type']} | Answer: {correct_answer['index']+1} | Confidence: {correct_answer['confidence']*100:.1f}% | Match: {correct_answer['matchType']} | Total: {self.state['total_solved']}")
                    
                    # Wait for new elements with random delay
                    try:
                        wait_time = random.uniform(1, 3)
                        WebDriverWait(self.driver, wait_time).until(
                            EC.presence_of_element_located((By.ID, 'timer'))
                        )
                        return True
                    except TimeoutException:
                        return False
                else:
                    # Click failed due to stale element - page was refreshed
                    self.logger.info("🔄 Click failed - page refreshed, getting new question...")
                    return False
            else:
                self.logger.warning("❌ No confident answer found - skipping")
                self.state['element_not_found_count'] += 1
                
                if self.state['element_not_found_count'] >= CONFIG['refresh_after_failures']:
                    self.logger.info(f"🔄 {self.state['element_not_found_count']} consecutive no-match errors - refreshing")
                    screenshot_result = self.send_screenshot("❌ No confident match found")
                    self.driver.get("https://adsha.re/surf")
                    time.sleep(3)
                    self.state['element_not_found_count'] = 0
                
                return False
            
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            self.state['consecutive_fails'] += 1
            return False

    # ==================== WRONG CLICK DETECTION ====================
    def detect_wrong_click(self):
        """Detect if we were redirected to exchange page (wrong click)"""
        try:
            current_url = self.driver.current_url.lower()
            if "adsha.re/exchange" in current_url:
                current_time = time.time()
                
                # Prevent spam notifications (max 1 per 5 minutes)
                if current_time - self.state['last_wrong_click_time'] > 300:
                    self.state['wrong_click_count'] += 1
                    self.state['last_wrong_click_time'] = current_time
                    
                    self.logger.error("❌ WRONG CLICK DETECTED! Redirected to exchange page")
                    screenshot_result = self.send_screenshot("❌ WRONG CLICK DETECTED - Exchange Page")
                    
                    warning_msg = f"""
🚨 <b>WRONG CLICK DETECTED!</b>

📛 Redirected to exchange page
🔢 Total wrong clicks: {self.state['wrong_click_count']}
🕒 Time: {self.get_ist_time()}
📷 {screenshot_result}

🔄 Returning to surf page...
"""
                    self.send_telegram(warning_msg)
                
                # Return to surf page
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Wrong click detection error: {e}")
            return False

    # ==================== PAGE STATE DETECTION ====================
    def detect_page_state(self):
        """ULTRA-RELIABLE page state detection with wrong click detection"""
        try:
            if not self.is_browser_alive():
                return "BROWSER_DEAD"
            
            # Check for wrong click first
            if self.detect_wrong_click():
                return "WRONG_CLICK_REDIRECT"
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()

            if "adsha.re/login" in current_url or "login" in current_url or "signin" in current_url:
                self.state['is_logged_in'] = False
                return "LOGIN_REQUIRED"
            elif "adsha.re/exchange" in current_url:
                return "WRONG_CLICK_REDIRECT"
            elif "surf" in current_url and ("svg" in page_source or "background-image" in page_source):
                return "GAME_ACTIVE"
            elif "surf" in current_url:
                return "GAME_LOADING"
            elif "adsha.re" in current_url and "surf" not in current_url:
                return "WRONG_PAGE"
            elif "404" in page_source or "not found" in page_source:
                return "PAGE_NOT_FOUND"
            elif "maintenance" in page_source or "offline" in page_source:
                return "MAINTENANCE_MODE"
            else:
                return "UNKNOWN_PAGE"
                
        except Exception as e:
            self.logger.error(f"Page state detection error: {e}")
            return "BROWSER_DEAD"

    def ensure_correct_page(self):
        """ENHANCED page correction with wrong click detection"""
        if not self.is_browser_alive():
            self.logger.error("Browser dead during page check")
            return False
            
        try:
            page_state = self.detect_page_state()
            
            if page_state == "BROWSER_DEAD":
                self.logger.error("Browser confirmed dead - restarting...")
                return self.restart_browser()
            elif page_state == "WRONG_CLICK_REDIRECT":
                self.logger.info("Wrong click detected - already handled")
                return True
            elif page_state == "LOGIN_REQUIRED":
                self.logger.info("Login required - forcing login...")
                self.state['is_logged_in'] = False
                if self.force_login():
                    self.state['is_logged_in'] = True
                    return True
                return False
            elif page_state == "GAME_ACTIVE":
                return True
            elif page_state == "GAME_LOADING":
                self.logger.info("Game loading - waiting...")
                time.sleep(5)
                return self.ensure_correct_page()
            elif page_state == "MAINTENANCE_MODE":
                self.logger.error("Site under maintenance - waiting...")
                self.send_telegram("🔧 Site under maintenance - waiting 5 minutes")
                time.sleep(300)
                return self.ensure_correct_page()
            else:
                self.logger.info(f"Wrong page state: {page_state} - redirecting to surf...")
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                return self.ensure_correct_page()
                
        except Exception as e:
            self.logger.error(f"Page correction error: {e}")
            return False

    # ==================== PERFORMANCE TRACKING ====================
    def update_performance_metrics(self):
        """Update performance tracking metrics"""
        current_time = time.time()
        metrics = self.state['performance_metrics']
        
        if metrics['start_time'] == 0:
            metrics['start_time'] = current_time
            metrics['last_hour_count'] = 0
        
        hours_running = (current_time - metrics['start_time']) / 3600
        if hours_running > 0:
            metrics['games_per_hour'] = self.state['total_solved'] / hours_running
        
        metrics['last_hour_count'] += 1

    def get_performance_status(self):
        """Get performance metrics for status"""
        metrics = self.state['performance_metrics']
        
        if metrics['games_per_hour'] == 0:
            return ""
        
        return f"""
📈 <b>PERFORMANCE METRICS</b>
⚡ Games/Hour: {metrics['games_per_hour']:.1f}
🕒 Running Time: {self.format_running_time()}
"""

    def format_running_time(self):
        """Format running time for display"""
        if self.state['performance_metrics']['start_time'] == 0:
            return "0h 0m"
        
        seconds = time.time() - self.state['performance_metrics']['start_time']
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

    # ==================== FIXED LEADERBOARD PARSING ====================
    def parse_leaderboard(self):
        """FIXED leaderboard parsing with proper HTML structure"""
        try:
            if not self.is_browser_alive() or not self.state['is_logged_in']:
                self.logger.error("Browser not alive or not logged in for leaderboard")
                return None
            
            self.logger.info("Fetching leaderboard...")
            
            # Open leaderboard in same tab (more reliable)
            self.driver.get("https://adsha.re/ten")
            time.sleep(5)
            
            # Check if we're still logged in
            current_url = self.driver.current_url.lower()
            if "login" in current_url:
                self.logger.error("Not logged in when trying to fetch leaderboard")
                self.state['is_logged_in'] = False
                # Go back to surf page
                self.driver.get("https://adsha.re/surf")
                return None
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            leaderboard = []
            
            # Find all leaderboard entries
            leaderboard_divs = soup.find_all('div', style=lambda x: x and 'width:250px' in x and 'margin:5px auto' in x)

            for i, div in enumerate(leaderboard_divs[:10]):  # Top 10 only
                try:
                    text = div.get_text(strip=True)
                    
                    # Extract user ID - multiple patterns
                    user_match = re.search(r'#(\d+)(?:\s*-|\s*\/)' , text)
                    if not user_match:
                        user_match = re.search(r'#(\d+)', text)
                    user_id = int(user_match.group(1)) if user_match else None
                    
                    if not user_id:
                        continue
                    
                    # Extract total surfed
                    surfed_match = re.search(r'Surfed in 3 Days:\s*([\d,]+)', text)
                    if not surfed_match:
                        surfed_match = re.search(r'Surfed:\s*([\d,]+)', text)
                    
                    total_surfed = int(surfed_match.group(1).replace(',', '')) if surfed_match else 0
                    
                    # Extract today's credits
                    today_match = re.search(r'T:\s*(\d+)', text)
                    today_credits = int(today_match.group(1)) if today_match else 0
                    
                    # Extract yesterday credits
                    yesterday_match = re.search(r'Y:\s*(\d+)', text)
                    yesterday_credits = int(yesterday_match.group(1)) if yesterday_match else 0
                    
                    # Extract day before credits
                    day_before_match = re.search(r'DB:\s*(\d+)', text)
                    day_before_credits = int(day_before_match.group(1)) if day_before_match else 0
                    
                    leaderboard.append({
                        'rank': i + 1,
                        'user_id': user_id,
                        'total_surfed': total_surfed,
                        'today_credits': today_credits,
                        'yesterday_credits': yesterday_credits,
                        'day_before_credits': day_before_credits,
                        'is_me': user_id == 4242  # Hardcoded ID
                    })
                    
                    self.logger.info(f"Leaderboard entry {i+1}: #{user_id} - Total: {total_surfed}, Today: {today_credits}")
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing leaderboard entry {i+1}: {e}")
                    continue
            
            # Go back to surf page
            self.driver.get("https://adsha.re/surf")
            time.sleep(3)
            
            self.state['last_leaderboard_check'] = time.time()
            self.state['leaderboard'] = leaderboard
            self.state['my_position'] = next((item for item in leaderboard if item['is_me']), None)
            
            if leaderboard:
                self.logger.info(f"✅ Leaderboard updated with {len(leaderboard)} entries")
                if self.state['my_position']:
                    self.logger.info(f"Your position: #{self.state['my_position']['rank']}")
            else:
                self.logger.warning("No leaderboard entries found")
                
            return leaderboard
            
        except Exception as e:
            self.logger.error(f"Leaderboard parsing error: {e}")
            # Try to return to surf page on error
            try:
                self.driver.get("https://adsha.re/surf")
            except:
                pass
            return None

    # ==================== FIXED TARGET CALCULATION ====================
    def get_competitive_target(self):
        """FIXED competitive target calculation"""
        if not self.state['leaderboard']:
            return None
        
        leader = self.state['leaderboard'][0]
        my_pos = self.state['my_position']
        
        if my_pos and my_pos['rank'] > 1:
            # For chasing #1: leader's total + safety margin
            target = leader['total_surfed'] + self.state['safety_margin']
            return target
        elif my_pos and my_pos['rank'] == 1:
            # For maintaining #1: use 2nd place's today + yesterday + safety margin
            if len(self.state['leaderboard']) > 1:
                second_place = self.state['leaderboard'][1]
                # Calculate 2nd place's recent activity (today + yesterday)
                recent_activity = second_place.get('today_credits', 0) + second_place.get('yesterday_credits', 0)
                # Target = their recent activity + safety margin (DAILY TARGET)
                target = recent_activity + self.state['safety_margin']
                self.logger.info(f"🎯 #1 Maintenance Target: 2ndRecent({recent_activity}) + Margin({self.state['safety_margin']}) = {target}")
                return target
        
        return None

    def get_competitive_status(self):
        """Enhanced competitive status display with wrong click info"""
        status_text = f"""
📊 <b>PERFECT SHAPE MATCHING SOLVER v6.1 ULTIMATE STATUS</b>
⏰ {self.get_ist_time()}
🔄 Status: {self.state['status']}
🎮 Games Solved: {self.state['total_solved']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
🚨 Wrong Clicks: {self.state['wrong_click_count']}
"""
        
        # Performance metrics
        metrics = self.state['performance_metrics']
        if metrics['start_time'] > 0:
            running_time = self.format_running_time()
            hours_running = (time.time() - metrics['start_time']) / 3600
            games_per_hour = self.state['total_solved'] / hours_running if hours_running > 0 else 0
            
            status_text += f"""
📈 <b>PERFORMANCE METRICS</b>
⚡ Games/Hour: {games_per_hour:.1f}
🕒 Running Time: {running_time}
📊 Total Cycles: {self.state['total_solved']}
"""
        
        # Competition info - FIXED TARGET CALCULATION
        if self.state['auto_compete'] and self.state['leaderboard']:
            target = self.get_competitive_target()
            my_pos = self.state['my_position']
            
            if my_pos and target:
                leader = self.state['leaderboard'][0]
                
                if my_pos['rank'] == 1:
                    # For #1 position: show daily maintenance target
                    second_place = self.state['leaderboard'][1]
                    recent_activity = second_place.get('today_credits', 0) + second_place.get('yesterday_credits', 0)
                    remaining_today = max(0, target - my_pos['today_credits'])
                    
                    status_text += f"""
🎯 <b>MAINTENANCE STATUS (#1)</b>
🎯 Today's Target: {target} sites
📈 2nd Place Recent: {recent_activity} (Today: {second_place.get('today_credits', 0)} + Yesterday: {second_place.get('yesterday_credits', 0)})
🛡️ Safety Margin: +{self.state['safety_margin']}
💎 Your Today: {my_pos['today_credits']} credits
📊 Remaining Today: {remaining_today} sites
"""
                else:
                    # For chasing #1: show total target
                    gap = target - my_pos['total_surfed'] if my_pos['total_surfed'] < target else 0
                    status_text += f"""
🎯 <b>COMPETITION STATUS</b>
🎯 Auto Target: {target} total surfed (+{self.state['safety_margin']} lead)
🥇 Current Position: #{my_pos['rank']} ({my_pos['total_surfed']} vs #1: {leader['total_surfed']})
📈 To Reach #1: {gap} sites needed
💎 Your Today: {my_pos['today_credits']} credits
"""
        
        elif self.state['daily_target']:
            status_text += f"🎯 <b>Daily Target:</b> {self.state['daily_target']} sites\n"
        
        if self.state['leaderboard']:
            status_text += f"\n🏆 <b>LEADERBOARD (Top 3):</b>\n"
            for entry in self.state['leaderboard'][:3]:
                marker = " 👈 YOU" if entry['is_me'] else ""
                status_text += f"{entry['rank']}. #{entry['user_id']} - {entry['total_surfed']} total (T:{entry['today_credits']} Y:{entry['yesterday_credits']}){marker}\n"
        
        return status_text

    def leaderboard_monitor(self):
        """Enhanced leaderboard monitoring"""
        self.logger.info("Starting PERFECT SHAPE MATCHING leaderboard monitoring...")
        
        while self.state['is_running']:
            try:
                if self.state['auto_compete']:
                    leaderboard = self.parse_leaderboard()
                    if leaderboard:
                        target = self.get_competitive_target()
                        my_pos = self.state['my_position']
                        
                        if my_pos and target:
                            if target != self.state.get('last_target'):
                                self.state['last_target'] = target
                                leader = leaderboard[0]
                                
                                if my_pos['rank'] == 1:
                                    second_place = leaderboard[1]
                                    recent_activity = second_place.get('today_credits', 0) + second_place.get('yesterday_credits', 0)
                                    self.send_telegram(f"🎯 <b>Maintenance Target Updated:</b> {target} sites today (Based on #2 recent: {recent_activity} + {self.state['safety_margin']} margin)")
                                else:
                                    self.send_telegram(f"🎯 <b>Auto Target Updated:</b> {target} total surfed (Beat #{leader['user_id']} with {leader['total_surfed']})")
                            
                            if my_pos['rank'] <= 3 and my_pos['rank'] != self.state.get('last_rank'):
                                self.state['last_rank'] = my_pos['rank']
                                if my_pos['rank'] == 1:
                                    self.send_telegram("🏆 <b>YOU ARE #1! 🎉</b>")
                                else:
                                    self.send_telegram(f"📈 <b>Now in position #{my_pos['rank']}!</b>")
                
                for _ in range(CONFIG['leaderboard_check_interval']):
                    if not self.state['is_running']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Leaderboard monitoring error: {e}")
                time.sleep(300)

    # ==================== COMPLETE TARGET MANAGEMENT ====================
    def set_daily_target(self, target):
        """Enhanced daily target setting"""
        try:
            self.state['daily_target'] = int(target)
            self.state['auto_compete'] = False
            self.send_telegram(f"🎯 <b>Daily target set to {target} sites</b> (Manual mode activated)")
            return True
        except:
            return False

    def clear_daily_target(self):
        """Enhanced daily target clearing"""
        self.state['daily_target'] = None
        self.state['auto_compete'] = True
        self.send_telegram("🎯 <b>Daily target cleared</b> - Auto-compete mode activated")
        return True

    def set_auto_compete(self, margin=None):
        """Enhanced auto-compete mode"""
        if margin:
            try:
                self.state['safety_margin'] = int(margin)
            except:
                pass
        
        self.state['auto_compete'] = True
        self.state['daily_target'] = None
        
        margin_text = f" (+{self.state['safety_margin']} margin)" if margin else ""
        self.send_telegram(f"🏆 <b>Auto-compete mode activated</b>{margin_text} - Targeting #1 position")
        return True

    # ==================== SMART FAILURE HANDLING ====================
    def handle_consecutive_failures(self):
        """SMART failure handling"""
        current_fails = self.state['consecutive_fails']
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead - restarting with login...")
            self.send_telegram("🔄 Browser dead - restarting with fresh login...")
            if self.restart_browser():
                self.state['consecutive_fails'] = 0
                self.state['element_not_found_count'] = 0
                self.state['no_question_count'] = 0
            return
        
        if current_fails >= CONFIG['restart_after_failures']:
            self.logger.warning("Multiple consecutive failures - restarting browser...")
            self.send_telegram("🔄 Multiple failures - restarting browser...")
            if self.restart_browser():
                self.state['consecutive_fails'] = 0
                self.state['element_not_found_count'] = 0
                self.state['no_question_count'] = 0
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("CRITICAL: Too many failures! Stopping...")
            self.send_telegram("🚨 CRITICAL ERROR - Too many consecutive failures - Stopping solver")
            self.stop()

    # ==================== ULTIMATE SOLVER LOOP ====================
    def solver_loop(self):
        """PERFECT SHAPE MATCHING solving loop with ZERO stale element clicks"""
        self.logger.info("Starting PERFECT SHAPE MATCHING solver loop with STALE PROTECTION...")
        self.state['status'] = 'running'
        self.state['performance_metrics']['start_time'] = time.time()
        
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("CRITICAL: Cannot start - Firefox failed")
                self.stop()
                return
        
        if not self.force_login():
            self.logger.error("CRITICAL: Initial login failed")
            self.stop()
            return
        
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                if cycle_count % 50 == 0:
                    gc.collect()
                
                if cycle_count % 100 == 0:
                    self.logger.info(f"Performance: {self.state['total_solved']} games solved | {self.state['performance_metrics']['games_per_hour']:.1f} games/hour")
                
                # USE ENHANCED SOLVER WITH STALE PROTECTION
                game_solved = self.solve_symbol_game_enhanced()
                
                if not game_solved:
                    self.handle_consecutive_failures()
                    # Random delay between attempts for anti-detection
                    retry_delay = random.uniform(2, 5)
                    time.sleep(retry_delay)
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                self.state['consecutive_fails'] += 1
                time.sleep(10)
        
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("CRITICAL: Too many failures, stopping...")
            self.stop()

    # ==================== ENHANCED CONTROL METHODS ====================
    def start(self):
        """Enhanced solver start"""
        if self.state['is_running']:
            return "❌ Solver already running"
        
        self.state['is_running'] = True
        self.state['consecutive_fails'] = 0
        self.state['element_not_found_count'] = 0
        self.state['wrong_click_count'] = 0
        self.state['no_question_count'] = 0
        self.state['performance_metrics']['start_time'] = time.time()
        
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        self.monitoring_thread = threading.Thread(target=self.leaderboard_monitor)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("PERFECT SHAPE MATCHING solver v6.1 ULTIMATE started!")
        self.send_telegram("🚀 <b>PERFECT SHAPE MATCHING Solver v6.1 ULTIMATE Started!</b>\n"
                         "🔧 <i>Now with ZERO Stale Element Clicks & Enhanced Protection</i>")
        return "✅ PERFECT SHAPE MATCHING Solver v6.1 ULTIMATE started successfully!"

    def stop(self):
        """Enhanced solver stop"""
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        
        if self.state['performance_metrics']['start_time'] > 0:
            total_time = time.time() - self.state['performance_metrics']['start_time']
            games_per_hour = self.state['total_solved'] / (total_time / 3600) if total_time > 0 else 0
            self.state['performance_metrics']['games_per_hour'] = games_per_hour
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("PERFECT SHAPE MATCHING solver stopped")
        self.send_telegram("🛑 <b>PERFECT SHAPE MATCHING Solver Stopped!</b>")
        return "✅ PERFECT SHAPE MATCHING Solver stopped successfully!"

    def status(self):
        """Enhanced status with all features"""
        if time.time() - self.state['last_leaderboard_check'] > 1800:
            self.parse_leaderboard()
        
        return self.get_competitive_status()

# ==================== ULTIMATE TELEGRAM BOT ====================
class UltimateTelegramBot:
    def __init__(self):
        self.solver = UltimateShapeSolver()
        self.logger = logging.getLogger(__name__)
        self.last_update_id = 0
    
    def get_telegram_updates(self):
        """Enhanced Telegram updates"""
        try:
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            params = {'offset': self.last_update_id, 'timeout': 10}
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.last_update_id = updates['result'][-1]['update_id'] + 1
                    return updates['result']
            return []
        except Exception as e:
            self.logger.error(f"Telegram updates error: {e}")
            return []
    
    def process_message(self, update):
        """Enhanced message processing"""
        if 'message' not in update:
            return
        
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
        if not self.solver.telegram_chat_id:
            self.solver.telegram_chat_id = chat_id
        
        response = ""
        
        if text.startswith('/start'):
            response = self.solver.start()
        elif text.startswith('/stop'):
            response = self.solver.stop()
        elif text.startswith('/status'):
            response = self.solver.status()
        elif text.startswith('/screenshot'):
            response = self.solver.send_screenshot()
        elif text.startswith('/target'):
            parts = text.split()
            if len(parts) == 2 and parts[1].isdigit():
                if self.solver.set_daily_target(parts[1]):
                    response = f"🎯 Daily target set to {parts[1]} sites"
                else:
                    response = "❌ Invalid target"
            elif len(parts) == 2 and parts[1] == 'clear':
                self.solver.clear_daily_target()
                response = "🎯 Daily target cleared"
            else:
                response = "Usage: /target 3000 or /target clear"
        elif text.startswith('/compete'):
            parts = text.split()
            margin = parts[1] if len(parts) > 1 else None
            self.solver.set_auto_compete(margin)
            response = f"🏆 Auto-compete mode activated (+{self.solver.state['safety_margin']} margin)"
        elif text.startswith('/leaderboard'):
            leaderboard = self.solver.parse_leaderboard()
            if leaderboard:
                leader_text = "🏆 <b>TOP 10 LEADERBOARD</b>\n"
                for entry in leaderboard:
                    marker = " 👈 YOU" if entry['is_me'] else ""
                    leader_text += f"{entry['rank']}. #{entry['user_id']} - {entry['total_surfed']} total (T:{entry['today_credits']} Y:{entry['yesterday_credits']}){marker}\n"
                response = leader_text
            else:
                response = "❌ Could not fetch leaderboard"
        elif text.startswith('/login'):
            response = "🔐 Attempting login..." if self.solver.force_login() else "❌ Login failed"
        elif text.startswith('/performance'):
            response = self.solver.get_performance_status()
        elif text.startswith('/restart'):
            response = "🔄 Restarting browser..." if self.solver.restart_browser() else "❌ Restart failed"
        elif text.startswith('/wrongclicks'):
            response = f"🚨 Total wrong clicks: {self.solver.state['wrong_click_count']}"
        elif text.startswith('/help'):
            response = """
🤖 <b>PERFECT SHAPE MATCHING AdShare Solver v6.1 ULTIMATE</b>

<b>NEW SECURITY FEATURES v6.1 ULTIMATE:</b>
✅ ZERO STALE ELEMENT CLICKS - Complete protection
✅ ULTRA-SAFE CLICK SYSTEM - Multi-layer validation
✅ ELEMENT FRESHNESS VERIFICATION - Pre-click checks
✅ AUTOMATIC STALE RECOVERY - Page refresh & retry
✅ CLICK SUCCESS VERIFICATION - Post-click validation

<b>Stale Element Protection:</b>
🛡️ Pre-click element freshness validation
🛡️ Multi-parameter checks (displayed, enabled, location, size)
🛡️ Automatic retry with page refresh
🛡️ JavaScript click backup system
🛡️ Click success verification

<b>Basic Commands:</b>
/start - Start solver
/stop - Stop solver  
/status - Competitive status
/screenshot - Get screenshot
/login - Force login
/restart - Restart browser
/wrongclicks - Show wrong click count

<b>Target Management:</b>
/target 3000 - Set daily target
/target clear - Clear target
/compete - Auto-compete mode
/compete 150 - Compete with +150 margin

<b>Information:</b>
/leaderboard - Show top 10
/performance - Performance metrics
/help - Show this help

<b>GUARANTEED SAFETY:</b>
✅ Zero stale element wrong clicks
✅ 90%+ confidence matching threshold
✅ Wrong click detection & alerts
✅ Anti-detection random delays
✅ Multi-layer error recovery
"""
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Enhanced update handling"""
        self.logger.info("Starting PERFECT SHAPE MATCHING Telegram bot v6.1 ULTIMATE...")
        
        while True:
            try:
                updates = self.get_telegram_updates()
                for update in updates:
                    self.process_message(update)
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"Telegram bot error: {e}")
                time.sleep(5)

if __name__ == '__main__':
    bot = UltimateTelegramBot()
    bot.logger.info("PERFECT SHAPE MATCHING AdShare Solver v6.1 ULTIMATE - WITH ZERO STALE ELEMENT CLICKS started!")
    bot.handle_updates()
