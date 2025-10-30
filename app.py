#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - PERFECT EDITION v4.4
FIXED: Circle matching, No session rotation, No click reset
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

# ==================== OPTIMIZED CONFIGURATION ====================
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
    # REMOVED: Session rotation and aggressive click limiting
    'max_clicks_per_minute': 60,  # Increased from 20
    'cooldown_periods': False,    # Disabled cooldowns
}

class PerfectShapeSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        
        # SIMPLIFIED State Management
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'is_logged_in': False,
            'consecutive_fails': 0,
            'element_not_found_count': 0,
            'no_question_count': 0,
            'consecutive_rounds': 0,
            'wrong_click_count': 0,
            'last_wrong_click_time': 0,
            'performance_metrics': {
                'games_per_hour': 0,
                'start_time': 0,
                'session_start_time': 0,
                'click_count': 0,
                'last_click_time': 0,
            },
        }
        
        self.solver_thread = None
        self.monitoring_thread = None
        self.setup_logging()
        self.setup_telegram()
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        """Setup Telegram bot"""
        try:
            self.logger.info("Setting up Telegram bot...")
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.telegram_chat_id = updates['result'][-1]['message']['chat']['id']
                    self.logger.info(f"Telegram Chat ID: {self.telegram_chat_id}")
                    self.send_telegram("🤖 PERFECT Solver v4.4 Started!\n✅ Circle matching FIXED\n✅ No session rotation\n✅ No click reset")
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

    # ==================== BROWSER MANAGEMENT ====================
    def is_browser_alive(self):
        """Browser health check"""
        try:
            if not self.driver:
                return False
            self.driver.current_url
            return True
        except:
            return False

    def setup_firefox(self):
        """Firefox setup"""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # Memory optimizations
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("permissions.default.image", 1)
            
            service = Service('/usr/local/bin/geckodriver', log_path=os.devnull)
            self.driver = webdriver.Firefox(service=service, options=options)
            
            self.logger.info("Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Firefox setup failed: {e}")
            return False

    def restart_browser(self):
        """Browser restart"""
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
                login_success = self.force_login()
                if login_success:
                    self.state['is_logged_in'] = True
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    # ==================== PERFECT LOGIN ====================
    def force_login(self):
        """Working login"""
        try:
            self.logger.info("Attempting login...")
            
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
                self.logger.error("No login form found")
                return False
            
            password_field_name = None
            for field in form.find_all('input'):
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                
                if field_value == 'Password' and field_name != 'mail' and field_name:
                    password_field_name = field_name
                    break
            
            if not password_field_name:
                self.logger.error("No password field found")
                return False
            
            # Fill email
            email_selectors = [
                "input[name='mail']",
                "input[type='email']",
                "input[placeholder*='email' i]"
            ]
            
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys(CONFIG['email'])
                    self.logger.info("Email entered")
                    break
                except:
                    continue
            
            self.smart_delay()
            
            # Fill password
            password_selectors = [
                f"input[name='{password_field_name}']",
                "input[type='password']"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    password_field.clear()
                    password_field.send_keys(CONFIG['password'])
                    self.logger.info("Password entered")
                    break
                except:
                    continue
            
            self.smart_delay()
            
            # Click login
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button"
            ]
            
            for selector in login_selectors:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn.is_displayed() and login_btn.is_enabled():
                        login_btn.click()
                        self.logger.info("Login button clicked")
                        break
                except:
                    continue
            
            self.smart_delay()
            time.sleep(8)
            
            self.driver.get("https://adsha.re/surf")
            self.smart_delay()
            
            page_state = self.detect_page_state()
            
            if page_state == "GAME_ACTIVE" or page_state == "GAME_LOADING":
                self.logger.info("Login successful!")
                self.state['is_logged_in'] = True
                self.send_telegram("✅ Login Successful!")
                return True
            else:
                self.logger.error(f"Login failed - state: {page_state}")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False

    # ==================== CRITICAL FIX: PERFECT CIRCLE MATCHING ====================
    def find_question_element(self):
        """Find question from entire page"""
        try:
            # Look for SVG questions
            try:
                svgs = self.driver.find_elements(By.TAG_NAME, 'svg')
                for svg in svgs:
                    try:
                        svg_html = svg.get_attribute('outerHTML')
                        if svg_html and '#808080' in svg_html:
                            try:
                                parent = svg.find_element(By.XPATH, '..')
                                self.logger.info("✅ Found SVG question")
                                return parent
                            except:
                                return svg
                    except:
                        continue
            except:
                pass

            # Look for background image questions - IMPROVED DETECTION
            try:
                all_divs = self.driver.find_elements(By.TAG_NAME, 'div')
                for div in all_divs:
                    try:
                        style = div.get_attribute('style') or ''
                        # RELAXED: Any background image
                        if 'background-image' in style:
                            self.logger.info("✅ Found background image question")
                            return div
                    except:
                        continue
            except:
                pass

            return None
            
        except Exception as e:
            self.logger.error(f"Question search error: {e}")
            return None

    def find_answer_links(self):
        """Find ALL answer links"""
        try:
            links = []
            
            # All adsha.re links
            try:
                adshare_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re']")
                links.extend(adshare_links)
            except:
                pass
            
            # Specific surf links
            try:
                surf_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/surf/']")
                for link in surf_links:
                    if link not in links:
                        links.append(link)
            except:
                pass
            
            self.logger.info(f"📊 Found {len(links)} answer links")
            return links
            
        except Exception as e:
            self.logger.error(f"Answer link search error: {e}")
            return []

    def is_image_circle_answer(self, element):
        """FIXED: Background image detection"""
        try:
            # Check element itself
            element_style = element.get_attribute('style') or ''
            if 'background-image' in element_style:
                return True
            
            # Check child divs
            all_divs = element.find_elements(By.TAG_NAME, 'div')
            for div in all_divs:
                try:
                    style = div.get_attribute('style') or ''
                    if 'background-image' in style:
                        return True
                except:
                    continue
            
            return False
        except:
            return False

    def classify_symbol_type(self, element):
        """EXACT USERSCRIPT LOGIC: Classify symbols"""
        if not element:
            return 'unknown'
        
        try:
            # STEP 1: Check for background image (RELAXED)
            if self.is_image_circle_answer(element):
                return 'background_circle'
            
            # STEP 2: Check SVG content
            try:
                if element.tag_name == 'svg':
                    svg = element
                else:
                    svg = element.find_element(By.TAG_NAME, 'svg')
                
                if not svg:
                    return 'unknown'
                
                content = (svg.get_attribute('innerHTML') or '').lower()
                
                # CIRCLE: Multiple circles - RELAXED MATCHING
                if 'circle' in content:
                    circles = content.count('<circle')
                    if circles >= 1:  # Reduced from 2 to 1
                        return 'circle'
                
                # SQUARE: Nested rectangles
                if 'rect' in content and 'width="50"' in content and 'height="50"' in content:
                    return 'square'
                
                # DIAMOND: Rotated squares
                if 'transform="matrix(0.7071' in content:
                    return 'diamond'
                
                # ARROW DOWN: Specific polygon
                if ('polygon' in content and '25 75' in content and '50 25' in content and 
                    '75 75' in content):
                    return 'arrow_down'
                
                # ARROW LEFT: Specific polygon  
                if ('polygon' in content and '25 25' in content and '75 50' in content and 
                    '25 75' in content):
                    return 'arrow_left'
                    
            except NoSuchElementException:
                pass
            
            return 'unknown'
            
        except Exception as e:
            return 'unknown'

    # ==================== PERFECT MATCHING ALGORITHM ====================
    def find_best_match(self, questionElement, links):
        """FIXED: Perfect matching with priority on ANY circle answers"""
        bestMatch = None
        exactMatches = []
        
        questionType = self.classify_symbol_type(questionElement)
        self.logger.info(f"🔍 Question Type: {questionType}")
        
        # ========== CRITICAL FIX: CIRCLE QUESTION HANDLING ==========
        if questionType == 'circle' or questionType == 'background_circle':
            self.logger.info("🎯 Circle question - PRIORITIZING ANY circle answers")
            
            # STEP 1: Look for ANY background image answers
            for index, link in enumerate(links):
                if self.is_image_circle_answer(link):
                    exactMatches.append({
                        'link': link,
                        'confidence': 1.0,
                        'exact': True,
                        'matchType': 'background_circle',
                        'position': index + 1,
                        'answerType': 'background_circle'
                    })
            
            # STEP 2: Look for ANY SVG circles
            for index, link in enumerate(links):
                answerType = self.classify_symbol_type(link)
                if answerType == 'circle':
                    exactMatches.append({
                        'link': link,
                        'confidence': 0.95,  # High confidence
                        'exact': True,
                        'matchType': 'svg_circle',
                        'position': index + 1,
                        'answerType': 'circle'
                    })
            
            if exactMatches:
                self.logger.info(f"✅ Found {len(exactMatches)} circle answer(s)")
                return exactMatches[0]  # Return first circle match
        # ========== END CRITICAL FIX ==========
        
        # For other symbol types, use traditional matching
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
                
                # Both question and answer are SVGs
                if questionSvg and answerSvg:
                    comparison = self.compare_symbols(questionElement, link)
                    if comparison['exact'] and comparison['match']:
                        exactMatches.append({
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': True,
                            'matchType': 'svg_exact',
                            'position': index + 1,
                            'answerType': answerType
                        })
                    elif comparison['match']:
                        bestMatch = {
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': False,
                            'matchType': 'svg_fuzzy',
                            'position': index + 1,
                            'answerType': answerType
                        }
                
            except Exception as e:
                continue
        
        # Return exact match if available
        if exactMatches:
            match = exactMatches[0]
            self.logger.info(f"🎯 Found EXACT match at position {match['position']}")
            return match
        
        # Return best match
        if bestMatch:
            self.logger.info(f"🎯 Found match at position {bestMatch['position']}")
            return bestMatch
        
        self.logger.warning(f"❌ No match found for {questionType} question")
        return None

    def compare_symbols(self, questionElement, answerElement):
        """Simple symbol comparison"""
        try:
            try:
                questionSvg = questionElement.find_element(By.TAG_NAME, 'svg') if questionElement.tag_name != 'svg' else questionElement
                answerSvg = answerElement.find_element(By.TAG_NAME, 'svg') if answerElement.tag_name != 'svg' else answerElement
            except NoSuchElementException:
                return {'match': False, 'confidence': 0, 'exact': False}
            
            if not questionSvg or not answerSvg:
                return {'match': False, 'confidence': 0, 'exact': False}
            
            questionContent = questionSvg.get_attribute('innerHTML')
            answerContent = answerSvg.get_attribute('innerHTML')
            
            # Simple content comparison
            if questionContent == answerContent:
                return {'match': True, 'confidence': 1.0, 'exact': True}
            
            # Check if they have similar structure
            question_circles = questionContent.count('<circle')
            answer_circles = answerContent.count('<circle')
            
            if question_circles > 0 and answer_circles > 0:
                return {'match': True, 'confidence': 0.9, 'exact': False}
                
            return {'match': False, 'confidence': 0, 'exact': False}
        except:
            return {'match': False, 'confidence': 0, 'exact': False}

    # ==================== SIMPLIFIED DELAY SYSTEM ====================
    def smart_delay(self):
        """Simple delay without behavior tracking"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        
        time.sleep(delay)
        return delay

    def safe_click_with_retry(self, element, max_retries=2):
        """Safe click with retry"""
        for attempt in range(max_retries):
            try:
                click_delay = random.uniform(0.5, 1.5)
                time.sleep(click_delay)
                
                # REMOVED: Click count tracking that was causing issues
                element.click()
                self.logger.info("✅ Click executed successfully!")
                return True
                
            except StaleElementReferenceException:
                if attempt < max_retries - 1:
                    self.logger.info(f"🔄 Element stale, retrying...")
                    time.sleep(1)
                    continue
                else:
                    return False
                    
            except Exception as e:
                self.logger.error(f"Click error: {e}")
                return False
        
        return False

    def detect_page_state(self):
        """Page state detection"""
        try:
            if not self.is_browser_alive():
                return "BROWSER_DEAD"
            
            # Check for wrong click
            current_url = self.driver.current_url.lower()
            if "adsha.re/exchange" in current_url:
                return "WRONG_CLICK_REDIRECT"
            
            if "adsha.re/login" in current_url:
                self.state['is_logged_in'] = False
                return "LOGIN_REQUIRED"
            elif "surf" in current_url:
                return "GAME_ACTIVE"
            else:
                return "UNKNOWN_PAGE"
                
        except Exception as e:
            return "BROWSER_DEAD"

    def ensure_correct_page(self):
        """Ensure we're on the correct page"""
        if not self.is_browser_alive():
            return False
            
        try:
            page_state = self.detect_page_state()
            
            if page_state == "BROWSER_DEAD":
                return self.restart_browser()
            elif page_state == "WRONG_CLICK_REDIRECT":
                self.state['wrong_click_count'] += 1
                self.driver.get("https://adsha.re/surf")
                time.sleep(2)
                return True
            elif page_state == "LOGIN_REQUIRED":
                self.state['is_logged_in'] = False
                if self.force_login():
                    self.state['is_logged_in'] = True
                    return True
                return False
            elif page_state == "GAME_ACTIVE":
                return True
            else:
                self.driver.get("https://adsha.re/surf")
                time.sleep(2)
                return self.ensure_correct_page()
                
        except Exception as e:
            self.logger.error(f"Page correction error: {e}")
            return False

    # ==================== MAIN SOLVER ====================
    def solve_symbol_game(self):
        """Main game solving"""
        if not self.state['is_running']:
            return False
        
        if not self.is_browser_alive():
            self.state['consecutive_fails'] += 1
            return False
            
        try:
            if not self.ensure_correct_page():
                self.state['consecutive_fails'] += 1
                return False
            
            # Find question
            questionElement = self.find_question_element()
            
            if not questionElement:
                self.state['no_question_count'] += 1
                
                if self.state['no_question_count'] >= 8:
                    self.logger.info("🔄 No question found - refreshing page...")
                    self.driver.get("https://adsha.re/surf")
                    time.sleep(3)
                    self.state['no_question_count'] = 0
                
                return False
            
            self.state['no_question_count'] = 0
            
            # Wait for question to load
            time.sleep(random.uniform(0.3, 0.8))
            
            questionType = self.classify_symbol_type(questionElement)
            self.logger.info(f"🎯 Question detected! Type: {questionType}")
            
            # Find answers
            links = self.find_answer_links()
            
            if len(links) < 2:
                self.logger.warning("❌ Not enough answers - REFRESHING")
                self.driver.get("https://adsha.re/surf")
                time.sleep(3)
                return False
            
            self.logger.info(f"📊 Found {len(links)} answer options")
            
            # Find correct answer
            correctAnswer = self.find_best_match(questionElement, links)
            
            if correctAnswer:
                self.logger.info(f"👉 Clicking answer at position {correctAnswer['position']}")
                
                self.smart_delay()
                
                if self.safe_click_with_retry(correctAnswer['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    self.state['element_not_found_count'] = 0
                    
                    matchType = "EXACT" if correctAnswer['exact'] else "FUZZY"
                    self.logger.info(f"✅ {matchType} Match! | Total: {self.state['total_solved']}")
                    
                    # Wait for new elements
                    try:
                        wait_time = random.uniform(1, 3)
                        WebDriverWait(self.driver, wait_time).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        return True
                    except TimeoutException:
                        return False
                else:
                    return False
            else:
                self.logger.warning(f"🔍 No match found. Question: {questionType}")
                self.state['element_not_found_count'] += 1
                
                if self.state['element_not_found_count'] >= CONFIG['refresh_after_failures']:
                    self.logger.info("🔄 Consecutive no-match errors - refreshing")
                    self.driver.get("https://adsha.re/surf")
                    time.sleep(3)
                    self.state['element_not_found_count'] = 0
                
                return False
            
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            self.state['consecutive_fails'] += 1
            return False

    def handle_consecutive_failures(self):
        """Handle failures"""
        current_fails = self.state['consecutive_fails']
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead - restarting...")
            if self.restart_browser():
                self.state['consecutive_fails'] = 0
            return
        
        if current_fails >= CONFIG['restart_after_failures']:
            self.logger.warning("Multiple failures - restarting browser...")
            if self.restart_browser():
                self.state['consecutive_fails'] = 0
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("CRITICAL: Too many failures! Stopping...")
            self.stop()

    def solver_loop(self):
        """Solving loop"""
        self.logger.info("Starting PERFECT solver v4.4...")
        self.state['status'] = 'running'
        
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
                # REMOVED: Garbage collection that was causing issues
                if cycle_count % 100 == 0:
                    hours_running = (time.time() - self.state['performance_metrics']['start_time']) / 3600
                    games_per_hour = self.state['total_solved'] / hours_running if hours_running > 0 else 0
                    self.logger.info(f"Performance: {self.state['total_solved']} games | {games_per_hour:.1f}/hour")
                
                game_solved = self.solve_symbol_game()
                
                if not game_solved:
                    self.handle_consecutive_failures()
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

    def start(self):
        """Start solver"""
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
        
        self.logger.info("PERFECT solver v4.4 started!")
        self.send_telegram("🚀 PERFECT Solver v4.4 Started!\n✅ Circle matching FIXED\n✅ No session rotation\n✅ No click reset")
        return "✅ PERFECT Solver v4.4 started successfully!"

    def stop(self):
        """Stop solver"""
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("PERFECT solver v4.4 stopped")
        self.send_telegram("🛑 PERFECT Solver v4.4 Stopped!")
        return "✅ PERFECT Solver v4.4 stopped successfully!"

    def status(self):
        """Status"""
        metrics = self.state['performance_metrics']
        if metrics['start_time'] > 0:
            total_time = time.time() - metrics['start_time']
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            games_per_hour = self.state['total_solved'] / (total_time / 3600) if total_time > 0 else 0
        else:
            hours, minutes, games_per_hour = 0, 0, 0
        
        return f"""
🤖 PERFECT SOLVER v4.4
⏰ Running: {hours}h {minutes}m
🎮 Games Solved: {self.state['total_solved']}
⚡ Games/Hour: {games_per_hour:.1f}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}
🚨 Wrong Clicks: {self.state['wrong_click_count']}
"""

# ==================== SIMPLE TELEGRAM BOT ====================
class SimpleTelegramBot:
    def __init__(self):
        self.solver = PerfectShapeSolver()
        self.logger = logging.getLogger(__name__)
        self.last_update_id = 0
    
    def get_telegram_updates(self):
        """Get Telegram updates"""
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
        """Process message"""
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
        elif text.startswith('/restart'):
            response = "🔄 Restarting browser..." if self.solver.restart_browser() else "❌ Restart failed"
        elif text.startswith('/help'):
            response = """
🤖 PERFECT SOLVER v4.4
/start - Start solver
/stop - Stop solver  
/status - Show status
/restart - Restart browser
/help - Show this help
"""
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Handle updates"""
        self.logger.info("Starting Simple Telegram bot...")
        
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
    bot = SimpleTelegramBot()
    bot.logger.info("PERFECT AdShare Solver v4.4 - CIRCLE MATCHING FIXED!")
    bot.handle_updates()
