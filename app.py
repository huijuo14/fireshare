#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - Complete Fixed Edition
Stable browser + working login + all features
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
from datetime import datetime
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
    'max_consecutive_failures': 15,
    'refresh_page_after_failures': 5,
    'leaderboard_check_interval': 1800,
    'safety_margin': 100,
}

class CompleteSymbolSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        
        # Complete State Management
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'is_logged_in': False,
            'consecutive_fails': 0,
            'daily_target': None,
            'auto_compete': True,
            'safety_margin': CONFIG['safety_margin'],
            'leaderboard': [],
            'my_position': None,
            'last_leaderboard_check': 0,
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
                    self.send_telegram("🤖 Complete AdShare Solver Started!")
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
        """Send screenshot to Telegram"""
        if not self.driver or not self.telegram_chat_id:
            return "❌ Browser not running"
        
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
                
            return "✅ Screenshot sent!" if response.status_code == 200 else "❌ Failed"
                
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    def get_ist_time(self):
        """Get current IST time"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime('%I:%M %p IST')

    # ==================== STABLE BROWSER MANAGEMENT ====================
    def is_browser_alive(self):
        """Check if browser is alive"""
        try:
            if not self.driver:
                return False
            self.driver.current_url
            return True
        except Exception:
            return False

    def setup_firefox(self):
        """Setup stable Firefox"""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # Stable settings
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("permissions.default.image", 1)  # Allow images
            
            service = Service('/usr/local/bin/geckodriver', log_path=os.devnull)
            self.driver = webdriver.Firefox(service=service, options=options)
            
            self.logger.info("Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Firefox setup failed: {e}")
            return False

    def restart_browser(self):
        """Restart browser safely"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            time.sleep(3)
            return self.setup_firefox()
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    # ==================== WORKING LOGIN FUNCTION ====================
    def force_login(self):
        """WORKING LOGIN - SIMPLIFIED AND STABLE"""
        try:
            self.logger.info("Starting login process...")
            
            # Navigate to login page
            self.driver.get("https://adsha.re/login")
            time.sleep(5)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Find login form
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            login_form = None
            
            for form in forms:
                if form.get_attribute('name') == 'login' or 'login' in form.get_attribute('outerHTML').lower():
                    login_form = form
                    break
            
            if not login_form:
                self.logger.error("No login form found")
                return False
            
            self.logger.info("Login form found")
            
            # Find email field
            email_field = None
            email_selectors = [
                "input[name='mail']",
                "input[type='email']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']"
            ]
            
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if email_field:
                        break
                except:
                    continue
            
            if not email_field:
                self.logger.error("Email field not found")
                return False
            
            # Find password field  
            password_field = None
            password_selectors = [
                "input[type='password']",
                "input[name*='pass']",
                "input[placeholder*='password']",
                "input[placeholder*='Password']"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field:
                        break
                except:
                    continue
            
            if not password_field:
                self.logger.error("Password field not found")
                return False
            
            # Fill credentials
            email_field.clear()
            email_field.send_keys(CONFIG['email'])
            self.logger.info("Email entered")
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(CONFIG['password'])
            self.logger.info("Password entered")
            time.sleep(1)
            
            # Find and click submit button
            submit_buttons = [
                "button[type='submit']",
                "input[type='submit']",
                "button",
                "input[value*='Login']",
                "input[value*='Sign']"
            ]
            
            for selector in submit_buttons:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        submit_btn.click()
                        self.logger.info("Login button clicked")
                        break
                except:
                    continue
            
            # Wait for login to process
            time.sleep(8)
            
            # Check if login successful
            current_url = self.driver.current_url.lower()
            if "surf" in current_url or "dashboard" in current_url:
                self.logger.info("Login successful!")
                self.state['is_logged_in'] = True
                self.send_telegram("✅ Login Successful!")
                return True
            else:
                # Try navigating to surf page
                self.driver.get("https://adsha.re/surf")
                time.sleep(5)
                
                current_url = self.driver.current_url.lower()
                if "surf" in current_url:
                    self.logger.info("Login successful after navigation!")
                    self.state['is_logged_in'] = True
                    self.send_telegram("✅ Login Successful!")
                    return True
                else:
                    self.logger.error("Login failed - still not on surf page")
                    return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False

    def ensure_logged_in(self):
        """Ensure we are logged in"""
        if not self.is_browser_alive():
            self.logger.error("Browser not alive")
            return False
        
        try:
            # Navigate to surf page
            self.driver.get("https://adsha.re/surf")
            time.sleep(3)
            
            current_url = self.driver.current_url.lower()
            
            if "login" in current_url:
                self.logger.info("Not logged in - attempting login")
                return self.force_login()
            elif "surf" in current_url:
                self.state['is_logged_in'] = True
                return True
            else:
                self.logger.info("Unexpected page - attempting login")
                return self.force_login()
                
        except Exception as e:
            self.logger.error(f"Login check error: {e}")
            return False

    # ==================== GAME SOLVING (ORIGINAL) ====================
    def smart_delay(self):
        """Randomized delay between actions"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        time.sleep(delay)
        return delay

    def simple_click(self, element):
        """Simple direct click"""
        try:
            self.smart_delay()
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
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
            
            if clean_question == clean_answer:
                return {'match': True, 'confidence': 1.0, 'exact': True}
            
            similarity = self.calculate_similarity(clean_question, clean_answer)
            should_match = similarity >= 0.90
            
            return {'match': should_match, 'confidence': similarity, 'exact': False}
            
        except Exception as e:
            self.logger.warning(f"Symbol comparison error: {e}")
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
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead during game solving")
            return False
            
        try:
            # Ensure we're on surf page and logged in
            if not self.ensure_logged_in():
                self.logger.error("Cannot ensure login status")
                return False
            
            # Look for game elements
            try:
                question_svg = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "svg"))
                )
            except TimeoutException:
                self.logger.info("No game found - waiting...")
                return False
            
            # Find answer options
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re'], button, .answer-option")
            
            if not links:
                self.logger.info("No answer options found")
                return False
            
            best_match = self.find_best_match(question_svg, links)
            
            if best_match:
                if self.simple_click(best_match['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    match_type = "EXACT" if best_match['exact'] else "FUZZY"
                    self.logger.info(f"{match_type} Match! Total: {self.state['total_solved']}")
                    return True
            else:
                self.logger.info("No good match found")
                return False
            
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            return False

    # ==================== LEADERBOARD COMPETITION ====================
    def parse_leaderboard(self):
        """Parse top 10 leaderboard"""
        try:
            if not self.is_browser_alive():
                return None
            
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open('https://adsha.re/ten', '_blank')")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            leaderboard = []
            
            user_divs = soup.find_all('div', style=lambda x: x and 'width:250px' in x)
            
            for i, div in enumerate(user_divs[:10]):
                text = div.get_text()
                
                # Extract user ID
                user_match = re.search(r'#(\d+)', text)
                user_id = int(user_match.group(1)) if user_match else None
                
                # Extract total surfed
                surfed_match = re.search(r'Surfed in 3 Days:\s*([\d,]+)', text)
                total_surfed = int(surfed_match.group(1).replace(',', '')) if surfed_match else 0
                
                # Extract today's credits
                today_match = re.search(r'T:\s*(\d+)', text)
                today_credits = int(today_match.group(1)) if today_match else 0
                
                leaderboard.append({
                    'rank': i + 1,
                    'user_id': user_id,
                    'total_surfed': total_surfed,
                    'today_credits': today_credits,
                    'is_me': user_id == 4242
                })
            
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            self.state['last_leaderboard_check'] = time.time()
            self.state['leaderboard'] = leaderboard
            self.state['my_position'] = next((item for item in leaderboard if item['is_me']), None)
            
            return leaderboard
            
        except Exception as e:
            self.logger.error(f"Leaderboard parsing error: {e}")
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None

    def get_competitive_target(self):
        """Calculate competitive target"""
        if not self.state['leaderboard']:
            return None
        
        leader = self.state['leaderboard'][0]
        my_pos = self.state['my_position']
        
        if my_pos and my_pos['rank'] > 1:
            target = leader['today_credits'] + self.state['safety_margin']
            return target
        elif my_pos and my_pos['rank'] == 1:
            if len(self.state['leaderboard']) > 1:
                second_place = self.state['leaderboard'][1]['today_credits']
                target = second_place + self.state['safety_margin']
                return target
        
        return None

    def get_competitive_status(self):
        """Get competitive status display"""
        status_text = f"""
📊 <b>COMPETITIVE STATUS</b>
⏰ {self.get_ist_time()}
🔄 Status: {self.state['status']}
🎮 Games Solved: {self.state['total_solved']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
"""
        
        # Add competition info
        if self.state['auto_compete'] and self.state['leaderboard']:
            target = self.get_competitive_target()
            my_pos = self.state['my_position']
            
            if my_pos and target:
                leader = self.state['leaderboard'][0]
                gap = target - my_pos['today_credits'] if my_pos['today_credits'] < target else 0
                
                status_text += f"""
🎯 <b>Auto Target:</b> {target} credits (+{self.state['safety_margin']} lead)
🥇 <b>Current Position:</b> #{my_pos['rank']} ({my_pos['today_credits']} vs #1: {leader['today_credits']})
📈 <b>To Reach #1:</b> {gap} credits needed
💎 <b>Earned Today:</b> {my_pos['today_credits']} credits
"""
        
        elif self.state['daily_target']:
            status_text += f"🎯 <b>Daily Target:</b> {self.state['daily_target']} sites\n"
        
        # Add leaderboard preview
        if self.state['leaderboard']:
            status_text += f"\n🏆 <b>LEADERBOARD (Top 3):</b>\n"
            for entry in self.state['leaderboard'][:3]:
                marker = " 👈 YOU" if entry['is_me'] else ""
                status_text += f"{entry['rank']}. #{entry['user_id']} - {entry['today_credits']} credits{marker}\n"
        
        return status_text

    def leaderboard_monitor(self):
        """Background leaderboard monitoring"""
        self.logger.info("Starting leaderboard monitoring...")
        
        while self.state['is_running']:
            try:
                if self.state['auto_compete']:
                    leaderboard = self.parse_leaderboard()
                    if leaderboard:
                        target = self.get_competitive_target()
                        if target and target != self.state.get('last_target'):
                            self.state['last_target'] = target
                            self.send_telegram(f"🎯 <b>Auto Target Updated:</b> {target} credits (Beat #{leaderboard[0]['user_id']})")
                
                # Check every 30 minutes
                for _ in range(CONFIG['leaderboard_check_interval']):
                    if not self.state['is_running']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Leaderboard monitoring error: {e}")
                time.sleep(300)

    # ==================== TARGET MANAGEMENT ====================
    def set_daily_target(self, target):
        """Set daily target"""
        try:
            self.state['daily_target'] = int(target)
            self.state['auto_compete'] = False
            self.send_telegram(f"🎯 Daily target set to {target} sites (Manual mode)")
            return True
        except:
            return False

    def clear_daily_target(self):
        """Clear daily target"""
        self.state['daily_target'] = None
        self.state['auto_compete'] = True
        self.send_telegram("🎯 Daily target cleared - Auto-compete mode activated")
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
        self.send_telegram(f"🏆 Auto-compete mode activated{margin_text} - Targeting #1 position")
        return True

    # ==================== ERROR HANDLING ====================
    def handle_consecutive_failures(self):
        """Handle consecutive failures"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.info(f"Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead - restarting...")
            self.restart_browser()
            return
        
        if current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.info("Refreshing page...")
            try:
                self.driver.get("https://adsha.re/surf")
                time.sleep(5)
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures! Stopping...")
            self.stop()

    # ==================== MAIN SOLVER LOOP ====================
    def solver_loop(self):
        """Main solving loop"""
        self.logger.info("Starting solver loop...")
        self.state['status'] = 'running'
        
        # Setup browser
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("Cannot start - Firefox failed")
                self.stop()
                return
        
        # Initial login
        if not self.ensure_logged_in():
            self.logger.error("Initial login failed")
            self.stop()
            return
        
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                # Browser health check
                if not self.is_browser_alive():
                    self.logger.warning("Browser dead - restarting...")
                    if not self.restart_browser():
                        self.logger.error("Browser restart failed")
                        self.stop()
                        break
                    # Re-login after restart
                    if not self.ensure_logged_in():
                        self.logger.error("Re-login after restart failed")
                        self.stop()
                        break
                
                # Memory cleanup
                if cycle_count % 50 == 0:
                    gc.collect()
                
                # Solve game
                game_solved = self.solve_symbol_game()
                
                if game_solved:
                    self.state['consecutive_fails'] = 0
                    time.sleep(10)  # Wait for next game
                else:
                    self.state['consecutive_fails'] += 1
                    time.sleep(5)
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                self.state['consecutive_fails'] += 1
                time.sleep(10)
        
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures, stopping...")
            self.stop()

    # ==================== CONTROL METHODS ====================
    def start(self):
        """Start the solver"""
        if self.state['is_running']:
            return "❌ Solver already running"
        
        self.state['is_running'] = True
        self.state['consecutive_fails'] = 0
        
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        self.monitoring_thread = threading.Thread(target=self.leaderboard_monitor)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("Complete solver started!")
        self.send_telegram("🚀 Complete Solver Started!")
        return "✅ Solver started successfully!"

    def stop(self):
        """Stop the solver"""
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("Solver stopped")
        self.send_telegram("🛑 Solver Stopped!")
        return "✅ Solver stopped successfully!"

    def status(self):
        """Get competitive status"""
        # Refresh leaderboard if stale
        if time.time() - self.state['last_leaderboard_check'] > 1800:
            self.parse_leaderboard()
        
        return self.get_competitive_status()

# Telegram Bot
class TelegramBot:
    def __init__(self):
        self.solver = CompleteSymbolSolver()
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
                    leader_text += f"{entry['rank']}. #{entry['user_id']} - {entry['today_credits']} credits{marker}\n"
                response = leader_text
            else:
                response = "❌ Could not fetch leaderboard"
        elif text.startswith('/login'):
            response = "🔐 Attempting login..." if self.solver.force_login() else "❌ Login failed"
        elif text.startswith('/help'):
            response = """
🤖 <b>Complete AdShare Solver</b>

<b>Basic Commands:</b>
/start - Start solver
/stop - Stop solver  
/status - Competitive status
/screenshot - Get screenshot
/login - Force login

<b>Target Management:</b>
/target 3000 - Set daily target
/target clear - Clear target
/compete - Auto-compete mode
/compete 150 - Compete with +150 margin

<b>Information:</b>
/leaderboard - Show top 10
/help - Show help
            """
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Handle Telegram updates"""
        self.logger.info("Starting Complete Telegram bot...")
        
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
    bot = TelegramBot()
    bot.logger.info("Complete AdShare Solver started!")
    bot.handle_updates()
