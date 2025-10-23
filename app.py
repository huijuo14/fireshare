#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - Firefox Edition
OPTIMIZED VERSION - Original script + Essential Features Only
"""

import os
import time
import random
import logging
import re
import requests
import threading
import base64
import json
import subprocess
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# ==================== CONFIGURATION ====================
CONFIG = {
    'email': "jiocloud90@gmail.com",
    'password': "@Sd2007123",
    'base_delay': 2,
    'random_delay': True,
    'min_delay': 1,
    'max_delay': 3,
    'telegram_token': "8225236307:AAF9Y2-CM7TlLDFm2rcTVY6f3SA75j0DFI8",
    'credit_check_interval': 1800,
    'max_consecutive_failures': 10,
    'refresh_page_after_failures': 5,
    'send_screenshot_on_error': True,
    'screenshot_cooldown_minutes': 5,
}

class FirefoxSymbolGameSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        self.session_file = "/app/session_status.json"
        
        # Enhanced State Management
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'last_credits': 'Unknown',
            'monitoring_active': False,
            'is_logged_in': False,
            'consecutive_fails': 0,
            'last_error_screenshot': 0,
            'session_valid': False
        }
        
        self.solver_thread = None
        self.monitoring_thread = None
        self.setup_logging()
        self.setup_telegram()
        self.load_session_status()
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        """Setup Telegram bot"""
        try:
            self.logger.info("🤖 Setting up Telegram bot...")
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.telegram_chat_id = updates['result'][-1]['message']['chat']['id']
                    self.logger.info(f"✅ Telegram Chat ID: {self.telegram_chat_id}")
                    self.send_telegram("🤖 <b>AdShare Solver Started with Smart Session Management!</b>")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"❌ Telegram setup failed: {e}")
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
            self.logger.error(f"❌ Telegram send failed: {e}")
            return False

    def send_screenshot(self, caption="🖥️ Screenshot"):
        """Send screenshot to Telegram"""
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
                    'caption': f'{caption} - {time.strftime("%Y-%m-%d %H:%M:%S")}'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
            return "✅ Screenshot sent!" if response.status_code == 200 else f"❌ Failed: {response.status_code}"
                
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    # ==================== SESSION MANAGEMENT ====================
    def save_session_status(self):
        """Save session status to file"""
        try:
            session_data = {
                'is_logged_in': self.state['is_logged_in'],
                'session_valid': self.state['session_valid'],
                'last_login': time.time() if self.state['is_logged_in'] else 0,
                'total_solved': self.state['total_solved']
            }
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
            self.logger.info("💾 Session status saved")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save session status: {e}")

    def load_session_status(self):
        """Load session status from file"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                self.state['is_logged_in'] = session_data.get('is_logged_in', False)
                self.state['session_valid'] = session_data.get('session_valid', False)
                self.state['total_solved'] = session_data.get('total_solved', 0)
                self.logger.info("💾 Session status loaded")
                return True
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load session status: {e}")
        return False

    def save_cookies(self):
        """Save cookies to file"""
        try:
            if self.driver and self.state['is_logged_in']:
                cookies = self.driver.get_cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f)
                self.state['session_valid'] = True
                self.save_session_status()
                self.logger.info("🍪 Cookies saved")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save cookies: {e}")

    def load_cookies(self):
        """Load cookies from file - ONLY if session is valid"""
        try:
            if (os.path.exists(self.cookies_file) and 
                self.state['session_valid'] and 
                self.state['is_logged_in']):
                
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                self.driver.get("https://adsha.re")
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        continue
                
                self.logger.info("🍪 Cookies loaded - Session reused")
                return True
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load cookies: {e}")
        
        return False

    def validate_session(self):
        """Check if current session is still valid"""
        try:
            current_url = self.driver.current_url.lower()
            
            # If we're redirected to login page, session is invalid
            if "login" in current_url:
                self.state['is_logged_in'] = False
                self.state['session_valid'] = False
                self.save_session_status()
                self.logger.warning("⚠️ Session invalid - Redirected to login")
                return False
            
            # If we're on surf/dashboard, session is valid
            if "surf" in current_url or "dashboard" in current_url:
                self.state['is_logged_in'] = True
                self.state['session_valid'] = True
                self.save_session_status()
                return True
            
            return False
                
        except Exception as e:
            self.logger.error(f"❌ Session validation failed: {e}")
            return False

    def smart_login_flow(self):
        """Smart login flow with session reuse"""
        self.logger.info("🔐 Starting smart login flow...")
        
        # Step 1: Try to use existing session first
        if self.state['session_valid'] and self.state['is_logged_in']:
            self.logger.info("🔄 Attempting to reuse existing session...")
            if self.load_cookies() and self.validate_session():
                self.logger.info("✅ Session reused successfully!")
                return True
        
        # Step 2: Session invalid, force login
        self.logger.info("🔄 Session invalid or expired, forcing login...")
        if self.force_login():
            self.state['is_logged_in'] = True
            self.state['session_valid'] = True
            self.save_cookies()
            self.save_session_status()
            self.logger.info("✅ New login successful!")
            return True
        else:
            self.state['is_logged_in'] = False
            self.state['session_valid'] = False
            self.save_session_status()
            self.logger.error("❌ Login failed")
            return False

    # ==================== FIREFOX SETUP ====================
    def setup_firefox(self):
        """Setup Firefox with safe memory optimizations"""
        self.logger.info("🦊 Starting Firefox with safe optimizations...")
        
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # SAFE MEMORY OPTIMIZATIONS ONLY
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("content.processLimit", 1)
            options.set_preference("javascript.options.mem.max", 51200)
            options.set_preference("browser.sessionhistory.max_entries", 5)
            
            # KEEP FUNCTIONALITY
            options.set_preference("permissions.default.image", 2)
            options.set_preference("gfx.webrender.all", True)
            options.set_preference("browser.cache.disk.enable", True)
            options.set_preference("browser.cache.memory.enable", True)
            
            service = Service('/usr/local/bin/geckodriver')
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Install uBlock Origin
            ublock_path = '/app/ublock.xpi'
            if os.path.exists(ublock_path):
                self.driver.install_addon(ublock_path, temporary=False)
                self.logger.info("✅ uBlock Origin installed!")
            
            self.logger.info("✅ Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Firefox setup failed: {e}")
            return False

    def smart_delay(self):
        """Simple delay between actions"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        
        time.sleep(delay)
        return delay

    def ensure_correct_page(self):
        """Ensure we're on the correct surf page with auto-login"""
        try:
            current_url = self.driver.current_url.lower()
            
            # If redirected to login page, auto-login
            if "login" in current_url:
                self.logger.info("🔐 Auto-login: Redirected to login page")
                return self.smart_login_flow()
            
            # If not on surf page, navigate there
            if "surf" not in current_url and "adsha.re" in current_url:
                self.logger.info("🔄 Redirecting to surf page...")
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                
                # Check if we got redirected to login
                if "login" in self.driver.current_url.lower():
                    self.logger.info("🔐 Auto-login: Redirected after navigation")
                    return self.smart_login_flow()
                    
                return True
            elif "adsha.re" not in current_url:
                self.logger.info("🌐 Navigating to AdShare...")
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Page navigation error: {e}")
            return False

    # ==================== ORIGINAL LOGIN METHOD ====================
    def force_login(self):
        """ORIGINAL WORKING LOGIN - DO NOT CHANGE"""
        try:
            self.logger.info("🔐 LOGIN: Attempting login with dynamic field detection...")
            
            # Navigate to login page
            login_url = "https://adsha.re/login"
            self.driver.get(login_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.smart_delay()
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the login form
            form = soup.find('form', {'name': 'login'})
            if not form:
                self.logger.error("❌ LOGIN: Could not find login form")
                return False
            
            # Find the dynamic password field name
            password_field_name = None
            for field in form.find_all('input'):
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                
                # Look for password field - dynamic detection logic
                if field_value == 'Password' and field_name != 'mail' and field_name:
                    password_field_name = field_name
                    break
            
            if not password_field_name:
                self.logger.error("❌ LOGIN: Could not detect password field name")
                return False
            
            self.logger.info(f"🔑 LOGIN: Detected password field name: {password_field_name}")
            
            # Fill email field
            email_selectors = [
                "input[name='mail']",
                "input[type='email']",
                "input[placeholder*='email' i]"
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys(CONFIG['email'])
                    self.logger.info("✅ LOGIN: Email entered")
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                self.logger.error("❌ LOGIN: Could not find email field")
                return False
            
            self.smart_delay()
            
            # Fill password field using detected name
            password_selector = f"input[name='{password_field_name}']"
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, password_selector)
                password_field.clear()
                password_field.send_keys(CONFIG['password'])
                self.logger.info("✅ LOGIN: Password entered")
            except:
                self.logger.error(f"❌ LOGIN: Could not find password field with selector: {password_selector}")
                return False
            
            self.smart_delay()
            
            # Find and click login button - ORIGINAL WORKING CODE
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button",
                "input[value*='Login']",
                "input[value*='Sign']"
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn.is_displayed() and login_btn.is_enabled():
                        login_btn.click()
                        self.logger.info("✅ LOGIN: Login button clicked")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                # Fallback: try to submit the form
                try:
                    form_element = self.driver.find_element(By.CSS_SELECTOR, "form[name='login']")
                    form_element.submit()
                    self.logger.info("✅ LOGIN: Form submitted")
                    login_clicked = True
                except:
                    pass
            
            # Wait for login to complete
            self.smart_delay()
            time.sleep(8)
            
            # Check if login successful by navigating to surf page
            self.driver.get("https://adsha.re/surf")
            self.smart_delay()
            
            current_url = self.driver.current_url
            if "surf" in current_url or "dashboard" in current_url:
                self.logger.info("✅ LOGIN: Successful!")
                self.state['is_logged_in'] = True
                self.save_cookies()
                self.send_telegram("✅ <b>Login Successful!</b>")
                return True
            else:
                # Check if we're still on login page
                if "login" in current_url:
                    self.logger.error("❌ LOGIN: Failed - still on login page")
                    return False
                else:
                    self.logger.warning("⚠️ LOGIN: May need manual verification, but continuing...")
                    self.state['is_logged_in'] = True
                    return True
                
        except Exception as e:
            self.logger.error(f"❌ LOGIN: Error - {e}")
            return False

    # ==================== ORIGINAL GAME SOLVING METHODS ====================
    def simple_click(self, element):
        """Simple direct click without mouse movement"""
        try:
            self.smart_delay()
            element.click()
            self.logger.info("✅ Element clicked")
            return True
        except Exception as e:
            self.logger.error(f"❌ Click failed: {e}")
            return False

    def calculate_similarity(self, str1, str2):
        """Calculate string similarity"""
        if len(str1) == 0 or len(str2) == 0:
            return 0.0
        
        common_chars = sum(1 for a, b in zip(str1, str2) if a == b)
        max_len = max(len(str1), len(str2))
        return common_chars / max_len if max_len > 0 else 0.0

    def compare_symbols(self, question_svg, answer_svg):
        """Compare SVG symbols"""
        try:
            question_content = question_svg.get_attribute('innerHTML')
            answer_content = answer_svg.get_attribute('innerHTML')
            
            if not question_content or not answer_content:
                return {'match': False, 'confidence': 0.0, 'exact': False}
            
            def clean_svg(svg_text):
                cleaned = re.sub(r'\s+', ' ', svg_text).strip().lower()
                cleaned = re.sub(r'fill:#[a-f0-9]+', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'stroke:#[a-f0-9]+', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'style="[^"]*"', '', cleaned)
                cleaned = re.sub(r'class="[^"]*"', '', cleaned)
                return cleaned
            
            clean_question = clean_svg(question_content)
            clean_answer = clean_svg(answer_content)
            
            # Exact match
            if clean_question == clean_answer:
                return {'match': True, 'confidence': 1.0, 'exact': True}
            
            # Fuzzy matching
            similarity = self.calculate_similarity(clean_question, clean_answer)
            should_match = similarity >= 0.90
            
            return {'match': should_match, 'confidence': similarity, 'exact': False}
            
        except Exception as e:
            self.logger.warning(f"⚠️ Symbol comparison error: {e}")
            return {'match': False, 'confidence': 0.0, 'exact': False}

    def find_best_match(self, question_svg, links):
        """Find best matching symbol"""
        best_match = None
        highest_confidence = 0
        exact_matches = []
        
        for link in links:
            try:
                answer_svg = link.find_element(By.TAG_NAME, "svg")
                if answer_svg:
                    comparison = self.compare_symbols(question_svg, answer_svg)
                    
                    if comparison['exact'] and comparison['match']:
                        exact_matches.append({
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': True
                        })
                    
                    elif comparison['match'] and comparison['confidence'] > highest_confidence:
                        highest_confidence = comparison['confidence']
                        best_match = {
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': False
                        }
            except:
                continue
        
        if exact_matches:
            return exact_matches[0]
        
        if best_match and best_match['confidence'] >= 0.90:
            return best_match
        
        return None

    def solve_symbol_game(self):
        """Main game solving logic"""
        if not self.state['is_running']:
            return False
        
        try:
            # Ensure we're on the correct page with auto-login
            if not self.ensure_correct_page():
                self.logger.warning("⚠️ Not on correct page, attempting navigation...")
                self.driver.get("https://adsha.re/surf")
                if not self.ensure_correct_page():
                    return False
            
            # Wait for question SVG
            question_svg = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "svg"))
            )
            
            if not question_svg:
                self.logger.info("⏳ Waiting for game to load...")
                return False
            
            # Find answer options
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re'], button, .answer-option")
            
            # Find best match
            best_match = self.find_best_match(question_svg, links)
            
            if best_match:
                if self.simple_click(best_match['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    self.save_session_status()
                    match_type = "EXACT" if best_match['exact'] else "FUZZY"
                    self.logger.info(f"✅ {match_type} Match! Confidence: {best_match['confidence']*100:.1f}% | Total: {self.state['total_solved']}")
                    return True
            else:
                self.logger.info("🔍 No good match found")
                self.handle_consecutive_failures()
                return False
            
        except TimeoutException:
            self.logger.info("⏳ Waiting for game elements...")
            self.handle_consecutive_failures()
            return False
        except Exception as e:
            self.logger.error(f"❌ Solver error: {e}")
            self.handle_consecutive_failures()
            return False

    # ==================== ERROR HANDLING ====================
    def handle_consecutive_failures(self):
        """Handle consecutive failures"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.warning(f"⚠️ Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        # Send screenshot on first failure
        if current_fails == 1 and CONFIG['send_screenshot_on_error']:
            cooldown_passed = time.time() - self.state['last_error_screenshot'] > CONFIG['screenshot_cooldown_minutes'] * 60
            if cooldown_passed:
                self.logger.info("📸 Sending error screenshot to Telegram...")
                screenshot_result = self.send_screenshot("❌ Game Error - No game solved")
                self.send_telegram(f"⚠️ <b>Game Error Detected</b>\nNo game solved (1/{CONFIG['max_consecutive_failures']} fails)\n{screenshot_result}")
                self.state['last_error_screenshot'] = time.time()
        
        # Refresh page after configured failures
        elif current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.warning("🔄 Too many failures! Refreshing page...")
            self.send_telegram(f"🔄 <b>Refreshing page</b> due to {current_fails} consecutive failures")
            
            try:
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                self.logger.info("✅ Page refreshed successfully")
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"❌ Page refresh failed: {e}")
        
        # Stop at max failures
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("🚨 CRITICAL: Too many failures! Stopping solver...")
            self.send_telegram("🚨 <b>CRITICAL ERROR</b>\nToo many failures - Stopping solver")
            self.stop()

    # ==================== CREDIT SYSTEM ====================
    def extract_credits(self):
        """Extract credit balance"""
        if not self.driver:
            return "BROWSER_NOT_RUNNING"
        
        try:
            # Ensure we're on the right page before checking credits
            self.ensure_correct_page()
            
            self.driver.refresh()
            time.sleep(5)
            page_source = self.driver.page_source
            
            credit_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*Credits',
                r'Credits.*?(\d{1,3}(?:,\d{3})*)',
                r'>\s*(\d[\d,]*)\s*Credits<',
            ]
            
            for pattern in credit_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    credits = matches[0]
                    return f"{credits} Credits"
            
            return "CREDITS_NOT_FOUND"
            
        except Exception as e:
            return f"ERROR: {str(e)}"

    def send_credit_report(self):
        """Send credit report to Telegram"""
        credits = self.extract_credits()
        self.state['last_credits'] = credits
        
        message = f"""
💰 <b>Credit Report</b>
⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}
💎 {credits}
🎯 Games Solved: {self.state['total_solved']}
🔄 Status: {self.state['status']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
💾 Session Valid: {'✅' if self.state['session_valid'] else '❌'}
⚠️ Consecutive Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
        """
        
        self.send_telegram(message)
        self.logger.info(f"📊 Credit report: {credits}")

    def monitoring_loop(self):
        """Background credit monitoring"""
        self.logger.info("📊 Starting credit monitoring...")
        self.state['monitoring_active'] = True
        
        while self.state['monitoring_active']:
            try:
                if self.state['is_running']:
                    self.send_credit_report()
                
                for _ in range(CONFIG['credit_check_interval']):
                    if not self.state['monitoring_active']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)
        
        self.logger.info("📊 Credit monitoring stopped")

    # ==================== MAIN SOLVER LOOP ====================
    def solver_loop(self):
        """Main solving loop"""
        self.logger.info("🎮 Starting solver loop...")
        self.state['status'] = 'running'
        
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("❌ Cannot start - Firefox failed")
                self.stop()
                return
        
        # Initial navigation with smart session handling
        self.driver.get("https://adsha.re/surf")
        if not self.ensure_correct_page():
            self.logger.warning("⚠️ Initial navigation issues, but continuing...")
        
        consecutive_fails = 0
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                # Refresh every 15 minutes
                if cycle_count % 30 == 0 and cycle_count > 0:
                    self.driver.refresh()
                    self.logger.info("🔁 Page refreshed")
                    time.sleep(5)
                
                # Try to solve game
                game_solved = self.solve_symbol_game()
                
                if game_solved:
                    consecutive_fails = 0
                    time.sleep(3)  # Success delay
                else:
                    consecutive_fails += 1
                    time.sleep(5)  # Longer delay on fail
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"❌ Loop error: {e}")
                consecutive_fails += 1
                time.sleep(10)
        
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("🚨 Too many failures, stopping...")
            self.stop()

    # ==================== CONTROL METHODS ====================
    def start(self):
        """Start the solver"""
        if self.state['is_running']:
            return "❌ Solver is already running"
        
        self.state['is_running'] = True
        self.state['consecutive_fails'] = 0
        self.state['last_error_screenshot'] = 0
        
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        if not self.state['monitoring_active']:
            self.monitoring_thread = threading.Thread(target=self.monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
        
        self.logger.info("🚀 Solver started with smart session management!")
        self.send_telegram("🚀 <b>Solver Started with Smart Session Management!</b>")
        return "✅ Solver started successfully!"

    def stop(self):
        """Stop the solver"""
        self.state['is_running'] = False
        self.state['monitoring_active'] = False
        self.state['status'] = 'stopped'
        
        # Save cookies before quitting
        self.save_cookies()
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("🛑 Solver stopped")
        self.send_telegram("🛑 <b>Solver Stopped!</b>")
        return "✅ Solver stopped successfully!"

    def status(self):
        """Get enhanced status"""
        return f"""
📊 <b>Status Report</b>
⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}
🔄 Status: {self.state['status']}
🎯 Games Solved: {self.state['total_solved']}
💰 Last Credits: {self.state['last_credits']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
💾 Session Valid: {'✅' if self.state['session_valid'] else '❌'}
⚠️ Consecutive Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
        """

# Telegram Bot
class TelegramBot:
    def __init__(self):
        self.solver = FirefoxSymbolGameSolver()
        self.logger = logging.getLogger(__name__)
    
    def handle_updates(self):
        """Handle Telegram updates"""
        last_update_id = None
        
        self.logger.info("🤖 Starting Telegram bot...")
        
        while True:
            try:
                url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
                params = {'timeout': 30, 'offset': last_update_id}
                response = requests.get(url, params=params, timeout=35)
                
                if response.status_code == 200:
                    updates = response.json()
                    if updates['result']:
                        for update in updates['result']:
                            last_update_id = update['update_id'] + 1
                            self.process_message(update)
                
            except Exception as e:
                self.logger.error(f"❌ Telegram error: {e}")
                time.sleep(5)
    
    def process_message(self, update):
        """Process Telegram message"""
        if 'message' not in update or 'text' not in update['message']:
            return
        
        chat_id = update['message']['chat']['id']
        text = update['message']['text']
        
        if not self.solver.telegram_chat_id:
            self.solver.telegram_chat_id = chat_id
        
        response = ""
        
        if text.startswith('/start'):
            response = self.solver.start()
        elif text.startswith('/stop'):
            response = self.solver.stop()
        elif text.startswith('/status'):
            response = self.solver.status()
        elif text.startswith('/credits'):
            credits = self.solver.extract_credits()
            response = f"💰 <b>Credits:</b> {credits}"
        elif text.startswith('/screenshot'):
            response = self.solver.send_screenshot()
        elif text.startswith('/help'):
            response = """
🤖 <b>AdShare Solver Commands</b>

/start - Start solver (smart session reuse)
/stop - Stop solver (saves session)  
/status - Check status
/credits - Get credits
/screenshot - Get real-time screenshot
/help - Show help

💡 <b>Smart Features:</b>
🔐 Session reuse - No repeated logins
🔄 Auto-login when redirected
📸 Error screenshots
🛑 Smart failure handling
            """
        
        if response:
            self.solver.send_telegram(response)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.logger.info("🤖 AdShare Solver with Smart Session Management started!")
    bot.handle_updates()
