#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - Firefox Edition
WITH CRASH RECOVERY & FULL CONFIGURATION
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup

# ==================== FULLY CONFIGURABLE SETTINGS ====================
CONFIG = {
    # Basic Settings
    'email': "jiocloud90@gmail.com",  # CHANGE THIS
    'password': "@Sd2007123",  # CHANGE THIS
    
    # Timing Settings
    'base_delay': 2,
    'random_delay': True,
    'min_delay': 1,
    'max_delay': 3,
    
    # Telegram Settings
    'telegram_token': "8225236307:AAF9Y2-CM7TlLDFm2rcTVY6f3SA75j0DFI8",
    'credit_check_interval': 1800,  # 30 minutes
    
    # Crash Recovery Settings
    'max_consecutive_failures': 10,
    'auto_restart_on_crash': True,
    'max_restarts_per_hour': 3,
    'browser_heartbeat_interval': 30,  # seconds
    
    # Memory Optimization Settings
    'enable_memory_optimization': True,
    'max_js_memory_mb': 100,  # Increased for stability
    'enable_disk_cache': True,  # Keep enabled for stability
    'enable_memory_cache': True,  # Keep enabled for stability
    
    # Error Handling Settings
    'send_screenshot_on_error': True,
    'screenshot_cooldown_minutes': 5,
    'refresh_page_after_failures': 5,
    
    # Performance Settings
    'page_load_timeout': 60,  # Increased timeout
    'element_timeout': 30,
}

class FirefoxSymbolGameSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        
        # Enhanced State Management with Crash Recovery
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'last_credits': 'Unknown',
            'monitoring_active': False,
            'is_logged_in': False,
            'consecutive_fails': 0,
            'last_error_screenshot': 0,
            'browser_crashes': 0,
            'last_crash_time': 0,
            'last_heartbeat': 0,
            'restart_count': 0,
            'last_restart_time': 0
        }
        
        self.solver_thread = None
        self.monitoring_thread = None
        self.heartbeat_thread = None
        self.setup_logging()
        self.setup_telegram()
    
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
                    self.send_telegram("🤖 <b>AdShare Solver Started with Crash Recovery!</b>")
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
        """Send screenshot to Telegram with custom caption"""
        if not self.driver or not self.telegram_chat_id:
            return "❌ Browser not running or Telegram not configured"
        
        try:
            screenshot_path = "/tmp/error_screenshot.png"
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
                
            if response.status_code == 200:
                return "✅ Screenshot sent to Telegram!"
            else:
                return f"❌ Screenshot failed: {response.status_code}"
                
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    def is_browser_alive(self):
        """Check if browser is still responsive"""
        try:
            if not self.driver:
                return False
            
            # Try to get current URL - if it works, browser is alive
            self.driver.current_url
            self.state['last_heartbeat'] = time.time()
            return True
            
        except (WebDriverException, Exception) as e:
            self.logger.warning(f"⚠️ Browser heartbeat failed: {e}")
            return False

    def heartbeat_monitor(self):
        """Monitor browser health and auto-restart if crashed"""
        self.logger.info("❤️ Starting browser heartbeat monitor...")
        
        while self.state['is_running']:
            try:
                if not self.is_browser_alive():
                    self.logger.error("🚨 Browser crash detected!")
                    self.state['browser_crashes'] += 1
                    self.state['last_crash_time'] = time.time()
                    
                    if CONFIG['auto_restart_on_crash']:
                        self.auto_restart_browser()
                    else:
                        self.logger.error("❌ Auto-restart disabled, stopping solver")
                        self.stop()
                        break
                
                time.sleep(CONFIG['browser_heartbeat_interval'])
                
            except Exception as e:
                self.logger.error(f"❌ Heartbeat monitor error: {e}")
                time.sleep(10)

    def auto_restart_browser(self):
        """Auto-restart browser after crash"""
        current_time = time.time()
        
        # Check restart limits
        if current_time - self.state['last_restart_time'] < 3600:  # 1 hour
            self.state['restart_count'] += 1
        else:
            self.state['restart_count'] = 1
            self.state['last_restart_time'] = current_time
        
        if self.state['restart_count'] > CONFIG['max_restarts_per_hour']:
            self.logger.error("🚨 Too many restarts, stopping solver")
            self.send_telegram("🚨 <b>Too many browser crashes!</b>\nStopping solver for stability")
            self.stop()
            return False
        
        self.logger.info(f"🔄 Auto-restarting browser ({self.state['restart_count']}/{CONFIG['max_restarts_per_hour']} this hour)")
        self.send_telegram("🔄 <b>Browser crashed - Auto-restarting...</b>")
        
        # Clean up dead browser
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        
        # Start fresh browser
        time.sleep(5)
        return self.setup_firefox()

    def setup_firefox(self):
        """Setup Firefox with STABLE configuration"""
        self.logger.info("🦊 Starting Firefox with STABLE configuration...")
        
        try:
            options = Options()
            
            # BASIC STABLE SETUP
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")  # Critical for containers
            
            # REMOVED PROBLEMATIC FLAGS THAT CAUSE CRASHES:
            # ❌ NO process limits (causes instability)
            # ❌ NO cache disabling (causes performance issues)
            # ❌ NO render disabling (breaks symbols)
            
            if CONFIG['enable_memory_optimization']:
                # ✅ SAFE memory optimizations only
                options.set_preference("javascript.options.mem.max", CONFIG['max_js_memory_mb'] * 1024)  # MB to KB
                options.set_preference("browser.sessionhistory.max_entries", 5)  # Mild reduction
                options.set_preference("media.memory_cache_max_size", 4096)  # 4MB media cache
                options.set_preference("image.mem.max_decoded_image_kb", 2048)  # 2MB image cache
                
                self.logger.info("✅ Safe memory optimizations applied")
            
            # ✅ CRITICAL - KEEP ENABLED FOR STABILITY:
            options.set_preference("permissions.default.image", 2)  # MUST ALLOW IMAGES
            options.set_preference("gfx.webrender.all", True)  # KEEP modern rendering
            options.set_preference("browser.cache.disk.enable", CONFIG['enable_disk_cache'])
            options.set_preference("browser.cache.memory.enable", CONFIG['enable_memory_cache'])
            
            # ✅ PERFORMANCE TWEAKS:
            options.set_preference("network.http.max-connections", 20)
            options.set_preference("browser.sessionstore.interval", 120000)  # 2 minutes
            
            # ✅ TIMEOUT CONFIGURATION:
            options.set_preference("dom.max_script_run_time", 30)
            options.set_preference("dom.max_chrome_script_run_time", 30)
            
            # Create driver with proper timeouts
            service = Service('/usr/local/bin/geckodriver')
            self.driver = webdriver.Firefox(
                service=service, 
                options=options
            )
            
            # Set timeouts
            self.driver.set_page_load_timeout(CONFIG['page_load_timeout'])
            self.driver.implicitly_wait(10)
            
            # Install uBlock Origin
            ublock_path = '/app/ublock.xpi'
            if os.path.exists(ublock_path):
                self.driver.install_addon(ublock_path, temporary=False)
                self.logger.info("✅ uBlock Origin installed!")
            
            # Load cookies if they exist
            self.load_cookies()
            
            self.state['last_heartbeat'] = time.time()
            self.logger.info("✅ Firefox started successfully with stable configuration!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Firefox setup failed: {e}")
            return False

    def save_cookies(self):
        """Save cookies to file for persistent login"""
        try:
            if self.driver and self.state['is_logged_in'] and self.is_browser_alive():
                cookies = self.driver.get_cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f)
                self.logger.info("✅ Cookies saved")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save cookies: {e}")

    def load_cookies(self):
        """Load cookies from file"""
        try:
            if os.path.exists(self.cookies_file) and self.is_browser_alive():
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                # Go to domain first to set cookies
                self.driver.get("https://adsha.re")
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except:
                        continue
                
                self.logger.info("✅ Cookies loaded")
                self.state['is_logged_in'] = True
                return True
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load cookies: {e}")
        
        return False

    def smart_delay(self):
        """Simple delay between actions"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        
        time.sleep(delay)
        return delay

    def handle_consecutive_failures(self):
        """Enhanced error handling with configurable limits"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.warning(f"⚠️ Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        # Check browser health first
        if not self.is_browser_alive():
            self.logger.error("🚨 Browser dead during failure handling!")
            return
        
        # 🚨 LEVEL 1: Send screenshot on first failure
        if current_fails == 1 and CONFIG['send_screenshot_on_error']:
            cooldown_passed = time.time() - self.state['last_error_screenshot'] > CONFIG['screenshot_cooldown_minutes'] * 60
            if cooldown_passed:
                self.logger.info("📸 Sending error screenshot to Telegram...")
                screenshot_result = self.send_screenshot("❌ Game Error - No game solved")
                self.send_telegram(f"⚠️ <b>Game Error Detected</b>\nNo game solved (1/{CONFIG['max_consecutive_failures']} fails)\n{screenshot_result}")
                self.state['last_error_screenshot'] = time.time()
        
        # 🚨 LEVEL 2: Refresh page after configured failures
        elif current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.warning(f"🔄 Too many failures! Refreshing page...")
            self.send_telegram(f"🔄 <b>Refreshing page</b> due to {current_fails}+ consecutive failures")
            
            try:
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                self.logger.info("✅ Page refreshed successfully")
                self.state['consecutive_fails'] = 0  # Reset counter
            except Exception as e:
                self.logger.error(f"❌ Page refresh failed: {e}")
        
        # 🚨 LEVEL 3: Stop at max failures
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error(f"🚨 CRITICAL: {current_fails} consecutive failures! Stopping solver...")
            self.send_telegram(f"🚨 <b>CRITICAL ERROR</b>\n{current_fails} consecutive failures - Stopping solver")
            self.stop()

    def ensure_correct_page(self):
        """Ensure we're on the correct surf page with browser health check"""
        if not self.is_browser_alive():
            self.logger.error("❌ Browser dead during page check")
            return False
            
        try:
            current_url = self.driver.current_url.lower()
            
            if "surf" not in current_url and "adsha.re" in current_url:
                self.logger.info("🔄 Redirecting to surf page...")
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
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

    def check_login_status(self):
        """Check if we're already logged in"""
        if not self.is_browser_alive():
            return False
            
        try:
            current_url = self.driver.current_url.lower()
            
            if "surf" in current_url or "dashboard" in current_url or "account" in current_url:
                self.state['is_logged_in'] = True
                return True
            
            if "login" in current_url:
                self.state['is_logged_in'] = False
                return False
            
            try:
                user_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='user'], [class*='account'], .navbar")
                if user_elements:
                    self.state['is_logged_in'] = True
                    return True
            except:
                pass
            
            return False
            
        except Exception as e:
            self.logger.warning(f"⚠️ Login status check failed: {e}")
            return False

    def force_login(self):
        """Login with configurable email/password"""
        if not self.is_browser_alive():
            self.logger.error("❌ Browser dead during login")
            return False
            
        try:
            self.logger.info("🔐 LOGIN: Attempting login...")
            
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
                self.logger.error("❌ LOGIN: Could not find login form")
                return False
            
            password_field_name = None
            for field in form.find_all('input'):
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                
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
                    email_field.send_keys(CONFIG['email'])  # Use configurable email
                    self.logger.info("✅ LOGIN: Email entered")
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                self.logger.error("❌ LOGIN: Could not find email field")
                return False
            
            self.smart_delay()
            
            # Fill password field
            password_selector = f"input[name='{password_field_name}']"
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, password_selector)
                password_field.clear()
                password_field.send_keys(CONFIG['password'])  # Use configurable password
                self.logger.info("✅ LOGIN: Password entered")
            except:
                self.logger.error(f"❌ LOGIN: Could not find password field with selector: {password_selector}")
                return False
            
            self.smart_delay()
            
            # Click login button
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
                try:
                    form_element = self.driver.find_element(By.CSS_SELECTOR, "form[name='login']")
                    form_element.submit()
                    self.logger.info("✅ LOGIN: Form submitted")
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
                self.logger.info("✅ LOGIN: Successful!")
                self.state['is_logged_in'] = True
                self.save_cookies()
                self.send_telegram("✅ <b>Login Successful!</b>")
                return True
            else:
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

    def navigate_to_adshare(self):
        """Navigate to AdShare with browser health check"""
        if not self.is_browser_alive():
            self.logger.error("❌ Browser dead during navigation")
            return False
            
        self.logger.info("🌐 Navigating to AdShare...")
        
        try:
            self.driver.get("https://adsha.re/surf")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.smart_delay()
            
            if self.check_login_status():
                self.logger.info("✅ Already logged in!")
                return True
            else:
                self.logger.info("🔐 Login required...")
                return self.force_login()
                
        except Exception as e:
            self.logger.error(f"❌ Navigation failed: {e}")
            return False

    # ... (keep all other methods: simple_click, calculate_similarity, compare_symbols, find_best_match, extract_credits, etc.)

    def solve_symbol_game(self):
        """Main game solving logic with browser health checks"""
        if not self.state['is_running']:
            return False
        
        if not self.is_browser_alive():
            self.logger.error("❌ Browser dead during game solving")
            return False
            
        try:
            if not self.ensure_correct_page():
                self.logger.warning("⚠️ Not on correct page, redirecting...")
                if not self.navigate_to_adshare():
                    return False
            
            question_svg = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "svg"))
            )
            
            if not question_svg:
                self.logger.info("⏳ Waiting for game to load...")
                return False
            
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re'], button, .answer-option")
            
            best_match = self.find_best_match(question_svg, links)
            
            if best_match:
                if self.simple_click(best_match['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
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

    def solver_loop(self):
        """Main solving loop with crash recovery"""
        self.logger.info("🎮 Starting solver loop with crash recovery...")
        self.state['status'] = 'running'
        
        # Start heartbeat monitor
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_monitor)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()
        
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("❌ Cannot start - Firefox setup failed")
                self.stop()
                return
        
        if not self.navigate_to_adshare():
            self.logger.warning("⚠️ Navigation issues, but continuing...")
        
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                # Refresh periodically
                if cycle_count % 30 == 0 and cycle_count > 0:
                    if self.is_browser_alive():
                        self.driver.refresh()
                        self.logger.info("🔁 Page refreshed")
                        time.sleep(5)
                
                # Try to solve game
                game_solved = self.solve_symbol_game()
                
                if game_solved:
                    time.sleep(3)
                else:
                    time.sleep(5)
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"❌ Loop error: {e}")
                time.sleep(10)
        
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("🚨 Too many failures, stopping...")
            self.stop()

    def start(self):
        """Start the solver with proper cleanup"""
        if self.state['is_running']:
            return "❌ Solver is already running"
        
        # Force cleanup of any previous session
        self.force_cleanup()
        
        self.state['is_running'] = True
        self.state['consecutive_fails'] = 0
        self.state['last_error_screenshot'] = 0
        self.state['browser_crashes'] = 0
        self.state['restart_count'] = 0
        
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        if not self.state['monitoring_active']:
            self.monitoring_thread = threading.Thread(target=self.monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
        
        self.logger.info("🚀 Solver started with crash recovery!")
        config_summary = f"""
📋 <b>Configuration Summary</b>
🦊 Memory Optimization: {'✅' if CONFIG['enable_memory_optimization'] else '❌'}
🔄 Auto-Restart: {'✅' if CONFIG['auto_restart_on_crash'] else '❌'}
📸 Error Screenshots: {'✅' if CONFIG['send_screenshot_on_error'] else '❌'}
❤️ Heartbeat: Every {CONFIG['browser_heartbeat_interval']}s
        """
        self.send_telegram("🚀 <b>Solver Started with Crash Recovery!</b>" + config_summary)
        return "✅ Solver started successfully!"

    def force_cleanup(self):
        """Force cleanup any previous browser sessions"""
        self.logger.info("🧹 Force cleaning up previous sessions...")
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except:
            pass
        
        # Kill any orphaned geckodriver processes
        try:
            subprocess.run(['pkill', '-f', 'geckodriver'], timeout=10)
        except:
            pass

    def stop(self):
        """Stop the solver with proper cleanup"""
        self.state['is_running'] = False
        self.state['monitoring_active'] = False
        self.state['status'] = 'stopped'
        
        # Save cookies if browser is alive
        if self.is_browser_alive():
            self.save_cookies()
        
        # Force cleanup
        self.force_cleanup()
        
        self.logger.info("🛑 Solver stopped with cleanup")
        self.send_telegram("🛑 <b>Solver Stopped with Cleanup!</b>")
        return "✅ Solver stopped successfully!"

    def status(self):
        """Get status with crash recovery info"""
        return f"""
📊 <b>Status Report</b>
⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}
🔄 Status: {self.state['status']}
🎯 Games Solved: {self.state['total_solved']}
💰 Last Credits: {self.state['last_credits']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Consecutive Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
🚨 Browser Crashes: {self.state['browser_crashes']}
❤️ Last Heartbeat: {time.strftime('%H:%M:%S', time.localtime(self.state['last_heartbeat']))}
        """

    def monitoring_loop(self):
        """Background credit monitoring"""
        self.logger.info("📊 Starting credit monitoring...")
        self.state['monitoring_active'] = True
        
        while self.state['monitoring_active']:
            try:
                if self.state['is_running'] and self.is_browser_alive():
                    self.send_credit_report()
                
                for _ in range(CONFIG['credit_check_interval']):
                    if not self.state['monitoring_active']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                time.sleep(60)
        
        self.logger.info("📊 Credit monitoring stopped")

    def send_credit_report(self):
        """Send credit report to Telegram"""
        if not self.is_browser_alive():
            self.state['last_credits'] = "BROWSER_DEAD"
        else:
            credits = self.extract_credits()
            self.state['last_credits'] = credits
        
        message = f"""
💰 <b>Credit Report</b>
⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}
💎 {self.state['last_credits']}
🎯 Games Solved: {self.state['total_solved']}
🔄 Status: {self.state['status']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Consecutive Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
🚨 Browser Crashes: {self.state['browser_crashes']}
        """
        
        self.send_telegram(message)
        self.logger.info(f"📊 Credit report: {self.state['last_credits']}")

# Telegram Bot (keep the same)
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
            response = f"""
🤖 <b>AdShare Solver Commands</b>

/start - Start solver
/stop - Stop solver  
/status - Check status
/credits - Get credits
/screenshot - Get real-time screenshot
/help - Show help

💡 <b>Crash Recovery Features:</b>
❤️ Heartbeat: Every {CONFIG['browser_heartbeat_interval']}s
🔄 Auto-restart: {CONFIG['max_restarts_per_hour']}x/hour
📸 Error screenshots: {'✅' if CONFIG['send_screenshot_on_error'] else '❌'}
🛑 Stop after: {CONFIG['max_consecutive_failures']} failures
            """
        
        if response:
            self.solver.send_telegram(response)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.logger.info("🤖 AdShare Solver with Crash Recovery started!")
    bot.handle_updates()
