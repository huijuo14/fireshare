#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - MEMORY OPTIMIZED EDITION
RAM Target: Under 500MB (from 600-700MB)
"""

import os
import time
import random
import logging
import re
import requests
import threading
import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ==================== CONFIGURATION ====================
CONFIG = {
    'email': "jiocloud90@gmail.com",
    'password': "@Sd2007123",
    'base_delay': 2,
    'random_delay': True,
    'min_delay': 1,
    'max_delay': 3,
    'telegram_token': "8225236307:AAF9Y2-CM7TlLDFm2rcTVY6f3SA75j0DFI8",
    'credit_check_interval': 3600,  # 1 hour instead of 30 minutes
    'max_consecutive_failures': 10,
    'refresh_page_after_failures': 5,
    'send_screenshot_on_error': False,  # Disabled to save memory
    'screenshot_cooldown_minutes': 5,
}

class OptimizedSymbolGameSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        self.session_file = "/app/session_status.json"
        
        # Memory-optimized state management
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'last_credits': 'Unknown',
            'is_logged_in': False,
            'consecutive_fails': 0,
            'session_valid': False
        }
        
        self.solver_thread = None
        self.setup_logging()
        self.setup_telegram()
        self.load_session_status()
    
    def setup_logging(self):
        """Memory-optimized logging"""
        logging.basicConfig(
            level=logging.WARNING,  # Reduced from INFO to WARNING
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'  # Shorter format
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
                    self.send_telegram("🤖 AdShare Solver Started - Memory Optimized Edition")
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

    # ==================== MEMORY-OPTIMIZED FIREFOX SETUP ====================
    def setup_firefox(self):
        """ULTRA memory-optimized Firefox setup"""
        self.logger.info("Starting Firefox with ULTRA memory optimizations...")
        
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # 🔥 ULTRA MEMORY OPTIMIZATIONS
            options.set_preference("dom.ipc.processCount", 1)  # Single process
            options.set_preference("content.processLimit", 1)
            options.set_preference("javascript.options.mem.max", 25600)  # 25MB JS heap
            options.set_preference("browser.sessionhistory.max_entries", 2)
            
            # 🚫 DISABLE MEMORY-HUNGRY FEATURES
            options.set_preference("permissions.default.image", 2)  # Block images
            options.set_preference("browser.cache.disk.enable", False)  # No disk cache
            options.set_preference("browser.cache.memory.enable", False)  # No memory cache
            options.set_preference("gfx.webrender.all", False)  # Disable WebRender
            options.set_preference("layers.acceleration.disabled", True)
            
            # 🎯 MINIMAL FUNCTIONALITY
            options.set_preference("dom.disable_beforeunload", True)
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("media.autoplay.default", 5)
            
            # 🧹 MEMORY CLEANUP
            options.set_preference("memory.free_dirty_pages", True)
            options.set_preference("memory.minimize_memory_usage", True)
            
            service = Service('/usr/local/bin/geckodriver')
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # 🚫 REMOVED uBlock Origin (saves ~50MB)
            
            self.logger.info("Firefox started with ULTRA memory savings!")
            return True
            
        except Exception as e:
            self.logger.error(f"Firefox setup failed: {e}")
            return False

    def smart_delay(self):
        """Simple delay between actions"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        
        time.sleep(delay)
        return delay

    # ==================== MEMORY-OPTIMIZED SESSION MANAGEMENT ====================
    def save_session_status(self):
        """Save session status"""
        try:
            session_data = {
                'is_logged_in': self.state['is_logged_in'],
                'session_valid': self.state['session_valid'],
                'last_login': time.time() if self.state['is_logged_in'] else 0,
                'total_solved': self.state['total_solved']
            }
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
        except Exception as e:
            self.logger.warning(f"Could not save session status: {e}")

    def load_session_status(self):
        """Load session status"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                self.state['is_logged_in'] = session_data.get('is_logged_in', False)
                self.state['session_valid'] = session_data.get('session_valid', False)
                self.state['total_solved'] = session_data.get('total_solved', 0)
                return True
        except Exception as e:
            self.logger.warning(f"Could not load session status: {e}")
        return False

    def save_cookies(self):
        """Save cookies"""
        try:
            if self.driver and self.state['is_logged_in']:
                cookies = self.driver.get_cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f)
                self.state['session_valid'] = True
                self.save_session_status()
        except Exception as e:
            self.logger.warning(f"Could not save cookies: {e}")

    def load_cookies(self):
        """Load cookies"""
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
                
                return True
        except Exception as e:
            self.logger.warning(f"Could not load cookies: {e}")
        
        return False

    # ==================== OPTIMIZED LOGIN & NAVIGATION ====================
    def ensure_correct_page(self):
        """Ensure we're on the correct page"""
        try:
            current_url = self.driver.current_url.lower()
            
            if "login" in current_url:
                self.logger.info("Auto-login: Redirected to login page")
                return self.smart_login_flow()
            
            if "surf" not in current_url and "adsha.re" in current_url:
                self.logger.info("Redirecting to surf page...")
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                
                if "login" in self.driver.current_url.lower():
                    self.logger.info("Auto-login: Redirected after navigation")
                    return self.smart_login_flow()
                    
                return True
            elif "adsha.re" not in current_url:
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Page navigation error: {e}")
            return False

    def smart_login_flow(self):
        """Smart login flow"""
        self.logger.info("Starting smart login flow...")
        
        if self.state['session_valid'] and self.state['is_logged_in']:
            self.logger.info("Attempting to reuse existing session...")
            if self.load_cookies() and self.validate_session():
                self.logger.info("Session reused successfully!")
                return True
        
        self.logger.info("Session invalid or expired, forcing login...")
        if self.force_login():
            self.state['is_logged_in'] = True
            self.state['session_valid'] = True
            self.save_cookies()
            self.save_session_status()
            self.logger.info("New login successful!")
            return True
        else:
            self.state['is_logged_in'] = False
            self.state['session_valid'] = False
            self.save_session_status()
            self.logger.error("Login failed")
            return False

    def validate_session(self):
        """Check if session is valid"""
        try:
            current_url = self.driver.current_url.lower()
            
            if "login" in current_url:
                self.state['is_logged_in'] = False
                self.state['session_valid'] = False
                self.save_session_status()
                return False
            
            if "surf" in current_url or "dashboard" in current_url:
                self.state['is_logged_in'] = True
                self.state['session_valid'] = True
                self.save_session_status()
                return True
            
            return False
                
        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            return False

    def force_login(self):
        """Original working login"""
        try:
            self.logger.info("Attempting login...")
            login_url = "https://adsha.re/login"
            self.driver.get(login_url)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.smart_delay()
            
            # Find password field dynamically
            page_source = self.driver.page_source
            password_field_name = None
            
            for line in page_source.split('\n'):
                if 'value="Password"' in line and 'name=' in line:
                    # Extract name from input field
                    name_start = line.find('name="') + 6
                    name_end = line.find('"', name_start)
                    if name_start > 6 and name_end > name_start:
                        field_name = line[name_start:name_end]
                        if field_name != 'mail':
                            password_field_name = field_name
                            break
            
            if not password_field_name:
                self.logger.error("Could not detect password field name")
                return False
            
            # Fill email
            email_selectors = ["input[name='mail']", "input[type='email']"]
            email_filled = False
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys(CONFIG['email'])
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                self.logger.error("Could not find email field")
                return False
            
            self.smart_delay()
            
            # Fill password
            password_selector = f"input[name='{password_field_name}']"
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, password_selector)
                password_field.clear()
                password_field.send_keys(CONFIG['password'])
            except:
                self.logger.error(f"Could not find password field: {password_selector}")
                return False
            
            self.smart_delay()
            
            # Click login button
            login_selectors = ["button[type='submit']", "input[type='submit']", "button"]
            login_clicked = False
            for selector in login_selectors:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn.is_displayed() and login_btn.is_enabled():
                        login_btn.click()
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                try:
                    form = self.driver.find_element(By.CSS_SELECTOR, "form[name='login']")
                    form.submit()
                    login_clicked = True
                except:
                    pass
            
            self.smart_delay()
            time.sleep(8)
            
            # Check login success
            self.driver.get("https://adsha.re/surf")
            self.smart_delay()
            
            current_url = self.driver.current_url
            if "surf" in current_url or "dashboard" in current_url:
                self.logger.info("Login successful!")
                self.state['is_logged_in'] = True
                self.save_cookies()
                self.send_telegram("✅ Login Successful!")
                return True
            else:
                if "login" in current_url:
                    self.logger.error("Login failed - still on login page")
                    return False
                else:
                    self.logger.warning("May need manual verification, but continuing...")
                    self.state['is_logged_in'] = True
                    return True
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False

    # ==================== MEMORY-OPTIMIZED GAME SOLVING ====================
    def simple_click(self, element):
        """Simple click without mouse movement"""
        try:
            self.smart_delay()
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False

    def optimized_symbol_comparison(self, question_svg, answer_svg):
        """Memory-optimized symbol comparison"""
        try:
            # Get limited SVG data
            question_html = question_svg.get_attribute('innerHTML')[:400]
            answer_html = answer_svg.get_attribute('innerHTML')[:400]
            
            if not question_html or not answer_html:
                return {'match': False, 'confidence': 0.0}
            
            # Simple extraction without heavy regex
            def extract_core_data(svg_text):
                paths = []
                viewbox = ""
                
                # Quick viewbox extraction
                if 'viewBox="' in svg_text:
                    start = svg_text.find('viewBox="') + 9
                    end = svg_text.find('"', start)
                    if end > start:
                        viewbox = svg_text[start:end]
                
                # Quick path extraction
                for line in svg_text.split('>'):
                    if ' d="' in line:
                        start = line.find(' d="') + 4
                        end = line.find('"', start)
                        if end > start:
                            path_data = line[start:end]
                            paths.append(path_data[:40])  # Limited size
                
                return f"{viewbox}|{''.join(paths)}"
            
            q_data = extract_core_data(question_html)
            a_data = extract_core_data(answer_html)
            
            # Exact match
            if q_data and a_data and q_data == a_data:
                return {'match': True, 'confidence': 1.0}
            
            # Simple similarity
            if q_data and a_data:
                min_len = min(len(q_data), len(a_data))
                if min_len > 0:
                    matches = sum(1 for i in range(min_len) if q_data[i] == a_data[i])
                    similarity = matches / min_len
                    return {'match': similarity >= 0.88, 'confidence': similarity}
            
            return {'match': False, 'confidence': 0.0}
            
        except Exception as e:
            self.logger.warning(f"Symbol comparison error: {e}")
            return {'match': False, 'confidence': 0.0}

    def find_best_match(self, question_svg, links):
        """Find best matching symbol"""
        best_match = None
        highest_confidence = 0
        
        for link in links:
            try:
                answer_svg = link.find_element(By.TAG_NAME, "svg")
                if answer_svg:
                    comparison = self.optimized_symbol_comparison(question_svg, answer_svg)
                    
                    if comparison['match'] and comparison['confidence'] > highest_confidence:
                        highest_confidence = comparison['confidence']
                        best_match = {
                            'link': link,
                            'confidence': comparison['confidence']
                        }
            except:
                continue
        
        if best_match and best_match['confidence'] >= 0.88:
            return best_match
        
        return None

    def solve_symbol_game(self):
        """Main game solving logic"""
        if not self.state['is_running']:
            return False
        
        try:
            if not self.ensure_correct_page():
                self.driver.get("https://adsha.re/surf")
                if not self.ensure_correct_page():
                    return False
            
            question_svg = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "svg"))
            )
            
            if not question_svg:
                return False
            
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re'], button")
            best_match = self.find_best_match(question_svg, links)
            
            if best_match:
                if self.simple_click(best_match['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    self.save_session_status()
                    self.logger.info(f"Match! Confidence: {best_match['confidence']*100:.1f}% | Total: {self.state['total_solved']}")
                    return True
            else:
                self.logger.info("No good match found")
                self.handle_consecutive_failures()
                return False
            
        except TimeoutException:
            self.logger.info("Waiting for game elements...")
            self.handle_consecutive_failures()
            return False
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            self.handle_consecutive_failures()
            return False

    # ==================== OPTIMIZED ERROR HANDLING ====================
    def handle_consecutive_failures(self):
        """Handle consecutive failures"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.warning(f"Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        if current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.warning("Too many failures! Refreshing page...")
            self.send_telegram(f"Refreshing page due to {current_fails} consecutive failures")
            
            try:
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures! Stopping solver...")
            self.send_telegram("Too many failures - Stopping solver")
            self.stop()

    # ==================== SIMPLIFIED CREDIT SYSTEM ====================
    def extract_credits(self):
        """Extract credit balance"""
        if not self.driver:
            return "BROWSER_NOT_RUNNING"
        
        try:
            self.ensure_correct_page()
            self.driver.refresh()
            time.sleep(3)
            page_source = self.driver.page_source
            
            credit_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*Credits',
                r'Credits.*?(\d{1,3}(?:,\d{3})*)',
            ]
            
            for pattern in credit_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    return f"{matches[0]} Credits"
            
            return "CREDITS_NOT_FOUND"
            
        except Exception as e:
            return f"ERROR: {str(e)}"

    def send_credit_report(self):
        """Send credit report"""
        credits = self.extract_credits()
        self.state['last_credits'] = credits
        
        message = f"""
💰 Credit Report
⏰ {time.strftime('%H:%M:%S')}
💎 {credits}
🎯 Games Solved: {self.state['total_solved']}
🔄 Status: {self.state['status']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
        """
        
        self.send_telegram(message)
        self.logger.info(f"Credit report: {credits}")

    # ==================== MEMORY-OPTIMIZED MAIN LOOP ====================
    def solver_loop(self):
        """Single-thread optimized solver loop"""
        self.logger.info("Starting optimized solver loop...")
        self.state['status'] = 'running'
        
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("Cannot start - Firefox failed")
                self.stop()
                return
        
        self.driver.get("https://adsha.re/surf")
        if not self.ensure_correct_page():
            self.logger.warning("Initial navigation issues, but continuing...")
        
        consecutive_fails = 0
        cycle_count = 0
        last_credit_check = time.time()
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                # Credit check every hour (instead of separate thread)
                current_time = time.time()
                if current_time - last_credit_check > CONFIG['credit_check_interval']:
                    self.send_credit_report()
                    last_credit_check = current_time
                
                # Refresh every 30 minutes
                if cycle_count % 60 == 0 and cycle_count > 0:
                    self.driver.refresh()
                    self.logger.info("Page refreshed")
                    time.sleep(3)
                
                # Try to solve game
                game_solved = self.solve_symbol_game()
                
                if game_solved:
                    consecutive_fails = 0
                    time.sleep(2)  # Reduced delay
                else:
                    consecutive_fails += 1
                    time.sleep(4)  # Reduced delay
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                consecutive_fails += 1
                time.sleep(8)
        
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures, stopping...")
            self.stop()

    # ==================== CONTROL METHODS ====================
    def start(self):
        """Start the solver - SINGLE THREAD EDITION"""
        if self.state['is_running']:
            return "❌ Solver is already running"
        
        self.state['is_running'] = True
        self.state['consecutive_fails'] = 0
        
        # Single thread only - no monitoring thread
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        self.logger.info("Solver started with memory optimizations!")
        self.send_telegram("🚀 Solver Started - Memory Optimized Edition")
        return "✅ Solver started successfully!"

    def stop(self):
        """Stop the solver"""
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        
        self.save_cookies()
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("Solver stopped")
        self.send_telegram("🛑 Solver Stopped")
        return "✅ Solver stopped successfully!"

    def status(self):
        """Get status"""
        return f"""
📊 Status Report
⏰ {time.strftime('%H:%M:%S')}
🔄 Status: {self.state['status']}
🎯 Games Solved: {self.state['total_solved']}
💰 Last Credits: {self.state['last_credits']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Consecutive Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
        """

# Telegram Bot (Simplified)
class TelegramBot:
    def __init__(self):
        self.solver = OptimizedSymbolGameSolver()
    
    def handle_updates(self):
        """Handle Telegram updates"""
        last_update_id = None
        
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
            response = f"💰 Credits: {credits}"
        elif text.startswith('/help'):
            response = """
🤖 Memory Optimized Solver

/start - Start solver
/stop - Stop solver  
/status - Check status
/credits - Get credits
/help - Show help

💡 Memory optimized features:
• Single thread operation
• Minimal Firefox footprint
• Optimized symbol matching
• Reduced logging
            """
        
        if response:
            self.solver.send_telegram(response)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.solver.logger.info("AdShare Solver - Memory Optimized Edition started!")
    bot.handle_updates()
