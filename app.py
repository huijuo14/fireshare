#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - PERFECT SHAPE MATCHING EDITION v3.4
COMPLETE FIXED VERSION - NO FEATURES REMOVED
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
            'auto_click': True,
            'wrong_click_count': 0,
            'last_wrong_click_time': 0,
            'no_question_count': 0,
            'last_successful_solve': time.time()
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
                    self.send_telegram("🤖 <b>PERFECT SHAPE MATCHING Solver v3.4 Started!</b>")
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

    # ==================== EXACT SAME LOGIN FUNCTION FROM FIRST WORKING SCRIPT ====================
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
            elif "surf" in current_url and "svg" in page_source:
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

    # ==================== PERFECT SHAPE MATCHING SYSTEM ====================
    def smart_delay(self):
        """Randomized delay between actions for anti-detection"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
            self.logger.info(f"⏰ Smart delay: {delay:.2f}s")
        else:
            delay = CONFIG['base_delay']
        time.sleep(delay)
        return delay

    # ==================== FIXED QUESTION DETECTION - NO HASH CHECKING ====================
    def find_question_element(self):
        """FIXED: Find question element WITHOUT hash-based skipping"""
        try:
            timer = self.driver.find_element(By.ID, 'timer')
            if not timer:
                return None
            
            html = timer.get_attribute('innerHTML')
            
            # Check if this is a question (contains gray #808080 AND svg)
            if html and '#808080' in html and 'svg' in html:
                # Extract the first SVG with gray color (that's the question)
                svg_match = re.search(r'<svg[^>]*>[\s\S]*?</svg>', html)
                if svg_match:
                    svg_content = svg_match.group(0)
                    if '#808080' in svg_content:
                        # Find the parent div containing this SVG
                        svgs = timer.find_elements(By.TAG_NAME, 'svg')
                        for svg in svgs:
                            svg_html = svg.get_attribute('outerHTML')
                            if '#808080' in svg_html:
                                return svg.find_element(By.XPATH, '..')  # Get parent div
                return None
            
            # Also check for background image questions
            divs = timer.find_elements(By.CSS_SELECTOR, 'div[style*="background-image"]')
            for div in divs:
                style = div.get_attribute('style')
                if 'img.gif' in style and 'border-radius:50%' in style:
                    return div
            
            return None
            
        except NoSuchElementException:
            return None
        except Exception as e:
            self.logger.error(f"Question element search error: {e}")
            return None

    def classify_symbol_type(self, element):
        """EXACT USERSCRIPT ALGORITHM: Classify symbol type"""
        if not element:
            return 'unknown'
        
        try:
            # Check if it's a background image element
            div = element.find_element(By.TAG_NAME, 'div') if element.tag_name != 'div' else element
            if div:
                style = div.get_attribute('style') or ''
                if 'background-image' in style and 'img.gif' in style:
                    return 'background_circle'
        except:
            pass
        
        # Check if it's an SVG element
        try:
            svg = element.find_element(By.TAG_NAME, 'svg') if element.tag_name != 'svg' else element
            if not svg:
                return 'unknown'
            
            content = svg.get_attribute('innerHTML').lower()
            
            # Circle detection (concentric circles)
            if 'circle' in content and 'cx="50"' in content and 'cy="50"' in content:
                circles = content.count('<circle')
                if circles >= 2:
                    return 'circle'
            
            # Square detection (nested squares)
            if 'rect x="25" y="25"' in content and 'width="50" height="50"' in content:
                rects = content.count('<rect')
                if rects >= 2:
                    return 'square'
            
            # Diamond detection (rotated squares)
            if 'transform="matrix(0.7071' in content and '42.4"' in content:
                return 'diamond'
            
            # Arrow down detection (pointing down)
            if 'polygon' in content and '25 75' in content and '50 25' in content and '75 75' in content:
                return 'arrow_down'
            
            # Arrow left detection (pointing left)  
            if 'polygon' in content and '25 25' in content and '75 50' in content and '25 75' in content:
                return 'arrow_left'
            
            return 'unknown'
        except:
            return 'unknown'

    def compare_symbols(self, questionElement, answerElement):
        """EXACT USERSCRIPT ALGORITHM: Compare symbols with fuzzy matching"""
        try:
            questionSvg = questionElement.find_element(By.TAG_NAME, 'svg') if questionElement.tag_name != 'svg' else questionElement
            answerSvg = answerElement.find_element(By.TAG_NAME, 'svg') if answerElement.tag_name != 'svg' else answerElement
            
            if not questionSvg or not answerSvg:
                return {'match': False, 'confidence': 0, 'exact': False}
            
            questionContent = questionSvg.get_attribute('innerHTML')
            answerContent = answerSvg.get_attribute('innerHTML')
            
            # Clean content for comparison
            cleanQuestion = re.sub(r'fill:#[A-F0-9]+|stroke:#[A-F0-9]+|style="[^"]*"|class="[^"]*"', '', questionContent, flags=re.IGNORECASE)
            cleanAnswer = re.sub(r'fill:#[A-F0-9]+|stroke:#[A-F0-9]+|style="[^"]*"|class="[^"]*"', '', answerContent, flags=re.IGNORECASE)
            
            # Exact match (preferred)
            if cleanQuestion == cleanAnswer:
                return {'match': True, 'confidence': 1.0, 'exact': True}
            
            # Fuzzy matching for similar symbols
            similarity = self.calculate_similarity(cleanQuestion, cleanAnswer)
            shouldMatch = similarity > 0.90
            
            return {
                'match': shouldMatch,
                'confidence': similarity,
                'exact': False
            }
        except Exception as e:
            return {'match': False, 'confidence': 0, 'exact': False}

    def calculate_similarity(self, str1, str2):
        """Calculate string similarity for fuzzy matching"""
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return 1.0
        
        editDistance = self.get_edit_distance(longer, shorter)
        return (len(longer) - editDistance) / float(len(longer))

    def get_edit_distance(self, a, b):
        """Levenshtein distance for edit distance calculation"""
        if len(a) == 0:
            return len(b)
        if len(b) == 0:
            return len(a)
        
        matrix = []
        for i in range(len(b) + 1):
            matrix.append([i])
        for j in range(len(a) + 1):
            matrix[0].append(j)
        
        for i in range(1, len(b) + 1):
            for j in range(1, len(a) + 1):
                if b[i-1] == a[j-1]:
                    matrix[i].append(matrix[i-1][j-1])
                else:
                    matrix[i].append(min(
                        matrix[i-1][j-1] + 1,
                        matrix[i][j-1] + 1,
                        matrix[i-1][j] + 1
                    ))
        
        return matrix[len(b)][len(a)]

    def is_image_circle_answer(self, element):
        """Check if this is the special case: image answer for circle questions"""
        try:
            div = element.find_element(By.TAG_NAME, 'div')
            style = div.get_attribute('style') or ''
            return ('background-image' in style and 
                    'background-size:cover' in style and
                    'border-radius:50%' in style)
        except:
            return False

    def find_best_match(self, questionElement, links):
        """EXACT USERSCRIPT ALGORITHM: Find the BEST possible match"""
        bestMatch = None
        highestConfidence = 0
        exactMatches = []
        
        questionType = self.classify_symbol_type(questionElement)
        
        try:
            questionSvg = questionElement.find_element(By.TAG_NAME, 'svg')
        except:
            questionSvg = None
        
        for index, link in enumerate(links):
            try:
                answerType = self.classify_symbol_type(link)
                
                try:
                    answerSvg = link.find_element(By.TAG_NAME, 'svg')
                except:
                    answerSvg = None
                
                # CASE 1: Both question and answer are SVGs
                if questionSvg and answerSvg:
                    comparison = self.compare_symbols(questionElement, link)
                    if comparison['exact'] and comparison['match']:
                        exactMatches.append({
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': True,
                            'matchType': 'svg_exact',
                            'index': index
                        })
                    elif comparison['match'] and comparison['confidence'] > highestConfidence:
                        highestConfidence = comparison['confidence']
                        bestMatch = {
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': False,
                            'matchType': 'svg_fuzzy',
                            'index': index
                        }
                
                # CASE 2: Question is SVG, Answer is Background Image
                elif questionSvg and answerType == 'background_circle':
                    if questionType == 'circle':
                        confidence = 0.98
                        if confidence > highestConfidence:
                            highestConfidence = confidence
                            bestMatch = {
                                'link': link,
                                'confidence': confidence,
                                'exact': True,
                                'matchType': 'svg_to_background',
                                'index': index
                            }
                
                # CASE 3: Question is Background Image, Answer is Background Image
                elif questionType == 'background_circle' and answerType == 'background_circle':
                    exactMatches.append({
                        'link': link,
                        'confidence': 1.0,
                        'exact': True,
                        'matchType': 'background_to_background',
                        'index': index
                    })
                
                # CASE 4: Question is Background Image, Answer is SVG
                elif questionType == 'background_circle' and answerSvg:
                    if answerType == 'circle':
                        confidence = 0.98
                        if confidence > highestConfidence:
                            highestConfidence = confidence
                            bestMatch = {
                                'link': link,
                                'confidence': confidence,
                                'exact': True,
                                'matchType': 'background_to_svg',
                                'index': index
                            }
                
            except Exception as e:
                self.logger.error(f"Error analyzing answer {index}: {e}")
                continue
        
        # Return exact match if available
        if exactMatches:
            return exactMatches[0]
        
        # Return best match if confidence is high enough
        if bestMatch and bestMatch['confidence'] >= 0.90:
            return bestMatch
        
        return None

    def safe_click(self, element):
        """SAFE CLICK with stale element protection and anti-detection delay"""
        try:
            # Add random delay before clicking (anti-detection)
            click_delay = random.uniform(0.5, 1.5)
            self.logger.info(f"⏰ Pre-click delay: {click_delay:.2f}s")
            time.sleep(click_delay)
            
            element.click()
            self.logger.info("✅ Click executed successfully!")
            return True
        except StaleElementReferenceException:
            self.logger.info("🔄 Element went stale during click - will retry next cycle")
            return False
        except Exception as e:
            self.logger.error(f"Click error: {e}")
            return False

    def solve_symbol_game(self):
        """PERFECT SHAPE MATCHING: Main game solving WITHOUT hash-based skipping"""
        if not self.state['is_running']:
            return False
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead during game solving")
            self.state['consecutive_fails'] += 1
            return False
            
        try:
            if not self.ensure_correct_page():
                self.logger.error("Cannot ensure correct page status")
                self.state['consecutive_fails'] += 1
                return False
            
            # FIXED: Direct question search WITHOUT hash checking
            questionElement = self.find_question_element()
            
            if not questionElement:
                self.state['no_question_count'] += 1
                
                # Refresh if no question found for too long
                if self.state['no_question_count'] >= 5:
                    self.logger.info("🔄 No question found for 5 attempts - refreshing page...")
                    self.driver.get("https://adsha.re/surf")
                    time.sleep(3)
                    self.state['no_question_count'] = 0
                
                return False
            
            # Reset counter when question is found
            self.state['no_question_count'] = 0
            
            # Wait a bit for question to fully load with random delay
            load_delay = random.uniform(0.3, 0.8)
            time.sleep(load_delay)
            
            questionType = self.classify_symbol_type(questionElement)
            self.logger.info(f"🎯 Question detected! Type: {questionType}")
            
            # Extract and analyze answers
            try:
                timer = self.driver.find_element(By.ID, 'timer')
                links = timer.find_elements(By.CSS_SELECTOR, 'a[href*="/surf/"]')
            except:
                self.logger.warning("❌ Could not find answer links")
                return False
            
            if len(links) < 2:
                self.logger.warning(f"❌ Only {len(links)} answers found - REFRESHING")
                self.driver.get("https://adsha.re/surf")
                time.sleep(3)
                return False
            
            # Find correct answer using userscript algorithm
            correctAnswer = self.find_best_match(questionElement, links)
            
            if correctAnswer:
                # SMART DELAY before clicking (anti-detection)
                self.smart_delay()
                
                # Use safe click with anti-detection
                if self.safe_click(correctAnswer['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    self.state['element_not_found_count'] = 0
                    self.state['last_successful_solve'] = time.time()
                    
                    self.update_performance_metrics()
                    
                    matchType = "EXACT" if correctAnswer['exact'] else "FUZZY"
                    source = correctAnswer['matchType']
                    confidence = correctAnswer['confidence'] * 100
                    
                    self.logger.info(f"✅ {matchType} Match! ({source}) Confidence: {confidence:.1f}% | Total: {self.state['total_solved']}")
                    
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
                    # Click failed due to stale element
                    self.logger.info("Click failed - will retry next cycle")
                    return False
            else:
                self.logger.warning(f"🔍 No high-confidence match found. Question: {questionType}")
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

    # ==================== LEADERBOARD (DISABLED FOR NOW) ====================
    def parse_leaderboard(self):
        """SIMPLIFIED leaderboard - will fix later"""
        try:
            if not self.is_browser_alive() or not self.state['is_logged_in']:
                self.logger.info("Browser not ready for leaderboard")
                return None
            
            self.logger.info("⏳ Leaderboard parsing disabled for now")
            return []
            
        except Exception as e:
            self.logger.info(f"Leaderboard temporarily disabled: {e}")
            return None

    # ==================== TARGET MANAGEMENT ====================
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
                recent_activity = second_place.get('today_credits', 0) + second_place.get('yesterday_credits', 0)
                target = recent_activity + self.state['safety_margin']
                self.logger.info(f"🎯 #1 Maintenance Target: 2ndRecent({recent_activity}) + Margin({self.state['safety_margin']}) = {target}")
                return target
        
        return None

    def get_competitive_status(self):
        """Enhanced competitive status display with wrong click info"""
        status_text = f"""
📊 <b>PERFECT SHAPE MATCHING SOLVER v3.4 STATUS</b>
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
        
        return status_text

    def leaderboard_monitor(self):
        """Simplified leaderboard monitoring"""
        self.logger.info("Starting leaderboard monitoring...")
        
        while self.state['is_running']:
            try:
                # Just sleep, leaderboard disabled for now
                for _ in range(CONFIG['leaderboard_check_interval']):
                    if not self.state['is_running']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Leaderboard monitoring error: {e}")
                time.sleep(300)

    # ==================== TARGET MANAGEMENT ====================
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
            return
        
        if current_fails >= CONFIG['restart_after_failures']:
            self.logger.warning("Multiple consecutive failures - restarting browser...")
            self.send_telegram("🔄 Multiple failures - restarting browser...")
            if self.restart_browser():
                self.state['consecutive_fails'] = 0
                self.state['element_not_found_count'] = 0
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("CRITICAL: Too many failures! Stopping...")
            self.send_telegram("🚨 CRITICAL ERROR - Too many consecutive failures - Stopping solver")
            self.stop()

    # ==================== ULTIMATE SOLVER LOOP ====================
    def solver_loop(self):
        """PERFECT SHAPE MATCHING solving loop with anti-detection"""
        self.logger.info("Starting PERFECT SHAPE MATCHING solver v3.4...")
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
                
                game_solved = self.solve_symbol_game()
                
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
        
        self.logger.info("PERFECT SHAPE MATCHING solver v3.4 started!")
        self.send_telegram("🚀 <b>PERFECT SHAPE MATCHING Solver v3.4 Started!</b>")
        return "✅ PERFECT SHAPE MATCHING Solver v3.4 started successfully!"

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
        
        self.logger.info("PERFECT SHAPE MATCHING solver v3.4 stopped")
        self.send_telegram("🛑 <b>PERFECT SHAPE MATCHING Solver v3.4 Stopped!</b>")
        return "✅ PERFECT SHAPE MATCHING Solver v3.4 stopped successfully!"

    def status(self):
        """Enhanced status with all features"""
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
            response = "⏳ Leaderboard temporarily disabled - focusing on solving games"
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
🤖 <b>PERFECT SHAPE MATCHING AdShare Solver v3.4</b>

<b>✅ FULLY FIXED VERSION:</b>
✅ NO hash-based question skipping
✅ Direct question element detection
✅ All userscript features included
✅ Background image support
✅ Wrong click detection
✅ Stale element handling

<b>Pattern Detection:</b>
✅ CIRCLES - with image circle detection
✅ ARROW_DOWN - exact points matching  
✅ ARROW_LEFT - exact points matching
✅ ROTATED_SQUARES/DIAMOND - matrix transform
✅ SQUARES - position and size

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
/leaderboard - Temporarily disabled
/performance - Performance metrics
/help - Show this help

<b>FIXES IN v3.4:</b>
✅ Removed timer hash checking
✅ Direct SVG element detection
✅ Better stale element handling
✅ Smarter refresh logic
✅ All features preserved
"""
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Enhanced update handling"""
        self.logger.info("Starting PERFECT SHAPE MATCHING Telegram bot v3.4...")
        
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
    bot.logger.info("PERFECT SHAPE MATCHING AdShare Solver v3.4 - EXACT SAME LOGIC AS USERSCRIPT started!")
    bot.handle_updates()
