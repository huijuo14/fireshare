#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - PERFECTED EDITION v4.5
FIXED: Login, Browser stop, All question types working
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
    'max_clicks_per_minute': 60,
    'cooldown_periods': False,
}

class PerfectedShapeSolver:
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
            'no_question_count': 0,
            'consecutive_rounds': 0,
            'wrong_click_count': 0,
            'last_wrong_click_time': 0,
            'daily_target': None,
            'auto_compete': True,
            'safety_margin': CONFIG['safety_margin'],
            'performance_metrics': {
                'games_per_hour': 0,
                'start_time': 0,
                'session_start_time': 0,
                'click_count': 0,
                'last_click_time': 0,
            },
            'browser_stopped': False,  # NEW: Track browser stop state
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
                    self.send_telegram("🤖 PERFECTED Solver v4.5 Started!\n✅ All questions working\n✅ Fixed login\n✅ Proper browser stop")
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

    # ==================== PERFECTED BROWSER MANAGEMENT ====================
    def is_browser_alive(self):
        """Browser health check - FIXED to respect stop state"""
        if self.state['browser_stopped']:
            return False
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
            # Reset browser stopped state when starting
            self.state['browser_stopped'] = False
            
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
        """Browser restart - FIXED to respect stop state"""
        if self.state['browser_stopped']:
            return False
            
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

    # ==================== EXACT WORKING LOGIN FUNCTION ====================
    def force_login(self):
        """EXACT WORKING LOGIN - No changes from working version"""
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
                self.send_telegram("✅ <b>Login Successful!</b>")
                return True
            else:
                self.logger.error(f"Login failed - current state: {page_state}")
                self.send_telegram(f"❌ Login failed - state: {page_state}")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            self.send_telegram(f"❌ Login error: {str(e)}")
            return False

    # ==================== PERFECTED SYMBOL DETECTION ====================
    def find_question_element(self):
        """Find question from entire page - IMPROVED for all types"""
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
                                return parent
                            except:
                                return svg
                    except:
                        continue
            except:
                pass

            # Look for background image questions - RELAXED
            try:
                all_divs = self.driver.find_elements(By.TAG_NAME, 'div')
                for div in all_divs:
                    try:
                        style = div.get_attribute('style') or ''
                        if 'background-image' in style:
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
        """Background image detection - RELAXED"""
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
        """PERFECTED: Classify ALL symbol types accurately"""
        if not element:
            return 'unknown'
        
        try:
            # STEP 1: Check for background image
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
                
                # CIRCLE: Any circle elements
                if 'circle' in content:
                    return 'circle'
                
                # SQUARE: Any rectangle elements
                if 'rect' in content:
                    return 'square'
                
                # DIAMOND: Transform matrix or polygon points
                if 'transform="matrix(0.7071' in content or 'polygon points="50,0 100,50 50,100 0,50"' in content:
                    return 'diamond'
                
                # ARROW DOWN: Downward pointing polygon
                if 'polygon' in content and '50 25' in content and '25 75' in content and '75 75' in content:
                    return 'arrow_down'
                
                # ARROW LEFT: Left pointing polygon
                if 'polygon' in content and '25 50' in content and '75 25' in content and '75 75' in content:
                    return 'arrow_left'
                    
            except NoSuchElementException:
                pass
            
            return 'unknown'
            
        except Exception as e:
            return 'unknown'

    # ==================== PERFECTED MATCHING ALGORITHM ====================
    def find_best_match(self, questionElement, links):
        """PERFECTED: Matching for ALL question types"""
        bestMatch = None
        exactMatches = []
        
        questionType = self.classify_symbol_type(questionElement)
        self.logger.info(f"🔍 Question Type: {questionType}")
        
        # SPECIAL HANDLING FOR CIRCLE TYPES
        if questionType in ['circle', 'background_circle']:
            self.logger.info("🎯 Circle question - PRIORITIZING circle answers")
            
            # Look for ANY background image answers
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
            
            # Look for ANY SVG circles
            for index, link in enumerate(links):
                answerType = self.classify_symbol_type(link)
                if answerType == 'circle':
                    exactMatches.append({
                        'link': link,
                        'confidence': 0.95,
                        'exact': True,
                        'matchType': 'svg_circle',
                        'position': index + 1,
                        'answerType': 'circle'
                    })
            
            if exactMatches:
                self.logger.info(f"✅ Found {len(exactMatches)} circle answer(s)")
                return exactMatches[0]
        
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
                
                # Question is background, answer is SVG of same type
                elif questionType == 'background_circle' and answerType == 'circle':
                    exactMatches.append({
                        'link': link,
                        'confidence': 0.98,
                        'exact': True,
                        'matchType': 'background_to_svg',
                        'position': index + 1,
                        'answerType': answerType
                    })
                
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
        
        # LAST RESORT: If no match found, try first available answer
        if links:
            self.logger.warning("⚠️ No confident match found, trying first answer")
            return {
                'link': links[0],
                'confidence': 0.5,
                'exact': False,
                'matchType': 'fallback',
                'position': 1,
                'answerType': 'unknown'
            }
        
        self.logger.warning(f"❌ No answers found for {questionType} question")
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
            
            # Exact content match
            if questionContent == answerContent:
                return {'match': True, 'confidence': 1.0, 'exact': True}
            
            # Check for similar structure
            question_circles = questionContent.count('<circle')
            answer_circles = answerContent.count('<circle')
            question_rects = questionContent.count('<rect')
            answer_rects = answerContent.count('<rect')
            question_polygons = questionContent.count('<polygon')
            answer_polygons = answerContent.count('<polygon')
            
            # If both have same type of elements, consider it a match
            if (question_circles > 0 and answer_circles > 0) or \
               (question_rects > 0 and answer_rects > 0) or \
               (question_polygons > 0 and answer_polygons > 0):
                return {'match': True, 'confidence': 0.9, 'exact': False}
                
            return {'match': False, 'confidence': 0, 'exact': False}
        except:
            return {'match': False, 'confidence': 0, 'exact': False}

    # ==================== TARGET & COMPETITION FEATURES ====================
    def set_daily_target(self, target):
        """Set daily target"""
        try:
            self.state['daily_target'] = int(target)
            self.state['auto_compete'] = False
            self.send_telegram(f"🎯 <b>Daily target set to {target} sites</b>")
            return True
        except:
            return False

    def clear_daily_target(self):
        """Clear daily target"""
        self.state['daily_target'] = None
        self.state['auto_compete'] = True
        self.send_telegram("🎯 <b>Daily target cleared</b> - Auto-compete mode")
        return True

    def set_auto_compete(self, margin=None):
        """Set auto-compete mode"""
        if margin:
            try:
                self.state['safety_margin'] = int(margin)
            except:
                pass
        
        self.state['auto_compete'] = True
        self.state['daily_target'] = None
        
        margin_text = f" (+{self.state['safety_margin']} margin)" if margin else ""
        self.send_telegram(f"🏆 <b>Auto-compete mode activated</b>{margin_text}")
        return True

    # ==================== SIMPLIFIED DELAY SYSTEM ====================
    def smart_delay(self):
        """Simple delay"""
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

    # ==================== PERFECTED MAIN SOLVER ====================
    def solve_symbol_game(self):
        """Main game solving - FIXED to respect stop state"""
        if not self.state['is_running'] or self.state['browser_stopped']:
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
        """Solving loop - FIXED to respect stop state"""
        self.logger.info("Starting PERFECTED solver v4.5...")
        self.state['status'] = 'running'
        self.state['browser_stopped'] = False  # Reset on start
        
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
        
        while self.state['is_running'] and not self.state['browser_stopped'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
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
        self.state['browser_stopped'] = False  # Reset browser state
        
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        self.logger.info("PERFECTED solver v4.5 started!")
        self.send_telegram("🚀 PERFECTED Solver v4.5 Started!\n✅ All questions working\n✅ Fixed login\n✅ Proper browser stop")
        return "✅ PERFECTED Solver v4.5 started successfully!"

    def stop(self):
        """STOP SOLVER COMPLETELY - FIXED to actually stop browser"""
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        self.state['browser_stopped'] = True  # NEW: Mark browser as stopped
        
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("Browser completely stopped")
            except Exception as e:
                self.logger.error(f"Error stopping browser: {e}")
        
        self.logger.info("PERFECTED solver v4.5 stopped")
        self.send_telegram("🛑 PERFECTED Solver v4.5 Stopped!\nBrowser completely shut down")
        return "✅ PERFECTED Solver v4.5 stopped successfully!"

    def status(self):
        """Status with target info"""
        metrics = self.state['performance_metrics']
        if metrics['start_time'] > 0:
            total_time = time.time() - metrics['start_time']
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            games_per_hour = self.state['total_solved'] / (total_time / 3600) if total_time > 0 else 0
        else:
            hours, minutes, games_per_hour = 0, 0, 0
        
        target_info = ""
        if self.state['daily_target']:
            target_info = f"🎯 Daily Target: {self.state['daily_target']} sites\n"
        elif self.state['auto_compete']:
            target_info = f"🏆 Auto-compete: ON (+{self.state['safety_margin']} margin)\n"
        
        return f"""
🤖 PERFECTED SOLVER v4.5
⏰ Running: {hours}h {minutes}m
🎮 Games Solved: {self.state['total_solved']}
⚡ Games/Hour: {games_per_hour:.1f}
{target_info}🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}
🚨 Wrong Clicks: {self.state['wrong_click_count']}
"""

# ==================== ENHANCED TELEGRAM BOT ====================
class EnhancedTelegramBot:
    def __init__(self):
        self.solver = PerfectedShapeSolver()
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
        """Process message with target features"""
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
        elif text.startswith('/restart'):
            response = "🔄 Restarting browser..." if self.solver.restart_browser() else "❌ Restart failed"
        elif text.startswith('/help'):
            response = """
🤖 PERFECTED SOLVER v4.5
/start - Start solver
/stop - Stop solver (COMPLETE shutdown)  
/status - Show status with target info
/target 3000 - Set daily target
/target clear - Clear target
/compete - Auto-compete mode
/compete 150 - Compete with +150 margin
/restart - Restart browser
/help - Show this help
"""
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Handle updates"""
        self.logger.info("Starting Enhanced Telegram bot...")
        
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
    bot = EnhancedTelegramBot()
    bot.logger.info("PERFECTED AdShare Solver v4.5 - ALL QUESTIONS WORKING!")
    bot.handle_updates()
