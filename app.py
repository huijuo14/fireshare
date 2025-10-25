#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - ULTIMATE STABLE EDITION
Fixed version with 4-failure threshold and removed detailed command
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
    'min_delay': 0.7,
    'max_delay': 2.5,
    'telegram_token': "8225236307:AAF9Y2-CM7TlLDFm2rcTVY6f3SA75j0DFI8",
    'max_consecutive_failures': 15,
    'refresh_page_after_failures': 7,
    'browser_restart_after_failures': 10,
    'leaderboard_check_interval': 1800,
    'safety_margin': 100,
    'performance_tracking': True,
}

class UltimateSymbolSolver:
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
            'daily_target': None,
            'auto_compete': True,
            'safety_margin': CONFIG['safety_margin'],
            'leaderboard': [],
            'my_position': None,
            'last_leaderboard_check': 0,
            'performance_metrics': {
                'games_per_hour': 0,
                'success_rate': 0,
                'start_time': 0,
                'last_hour_count': 0
            }
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
                    self.send_telegram("🤖 <b>ULTIMATE AdShare Solver Started!</b>")
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
        """Enhanced browser health check"""
        try:
            if not self.driver:
                return False
            self.driver.current_url  # More reliable check
            return True
        except Exception:
            return False

    def setup_firefox(self):
        """ULTIMATE Firefox setup with all optimizations"""
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
            options.set_preference("permissions.default.image", 1)  # ALLOW IMAGES
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
        """Enhanced browser restart with better cleanup"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            time.sleep(3)  # Longer delay for clean restart
            gc.collect()  # Force garbage collection
            return self.setup_firefox()
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    # ==================== PAGE STATE DETECTION SYSTEM ====================
    def detect_page_state(self):
        """Enhanced page state detection"""
        try:
            if not self.is_browser_alive():
                return "BROWSER_DEAD"
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()

             # ▼▼▼ ADD THIS LINE RIGHT HERE ▼▼▼
            if "adsha.re/login" in current_url:
                return "LOGIN_REQUIRED"
        # ▲▲▲ ADD THIS LINE RIGHT HERE ▲▲▲  
            
            if "login" in current_url or "signin" in current_url:
                return "LOGIN_REQUIRED"
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
            return "DETECTION_ERROR"

    def ensure_correct_page(self):
        """Ensure we're on the correct page with auto-correction"""
        if not self.is_browser_alive():
            self.logger.error("Browser dead during page check")
            return False
            
        try:
            page_state = self.detect_page_state()
            self.logger.info(f"Page state detected: {page_state}")
            
            if page_state == "BROWSER_DEAD":
                return False
            elif page_state == "LOGIN_REQUIRED":
                self.logger.info("Login page detected - handling login...")
                if not self.state['is_logged_in']:
                    return self.force_login()
                return self.state['is_logged_in']
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

    # ==================== ULTIMATE LOGIN SYSTEM ====================
    def force_login(self):
        """ULTIMATE WORKING LOGIN - Enhanced version"""
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
            
            # Enhanced email filling with multiple strategies
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
            
            # Enhanced password filling
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
            
            # Enhanced login button clicking
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
            time.sleep(8)  # Wait for login processing
            
            # Enhanced login verification
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
                if page_state == "LOGIN_REQUIRED":
                    self.logger.error("Login failed - still on login page")
                    self.send_telegram("❌ Login failed - still on login page")
                    return False
                else:
                    self.logger.info("Login may need verification, continuing...")
                    self.state['is_logged_in'] = True
                    return True
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            self.send_telegram(f"❌ Login error: {str(e)}")
            return False

    def ensure_logged_in(self):
        """Enhanced login verification"""
        if not self.is_browser_alive():
            self.logger.error("Browser not alive")
            return False
        
        return self.ensure_correct_page()

    # ==================== ENHANCED GAME SOLVING ====================
    def smart_delay(self):
        """Randomized delay between actions"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        time.sleep(delay)
        return delay

    def simple_click(self, element):
        """Enhanced click with better error handling"""
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
        """Enhanced symbol comparison"""
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
                cleaned = re.sub(r'id="[^"]*"', '', cleaned)
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
        """Enhanced best match finding with fresh elements"""
        best_match = None
        highest_confidence = 0
        exact_matches = []
        
        # Always get fresh elements to avoid stale references
        try:
            question_svg = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "svg"))
            )
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re'], button, .answer-option, [class*='answer'], [class*='option']")
        except:
            return None
        
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
        """Enhanced main game solving logic"""
        if not self.state['is_running']:
            return False
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead during game solving")
            return False
            
        try:
            # Enhanced page verification - only check if we have multiple failures
            if self.state['consecutive_fails'] >= 4:
                if not self.ensure_correct_page():
                    self.logger.error("Cannot ensure correct page status")
                    return False
            
            # Enhanced game detection with multiple strategies
            try:
                question_svg = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "svg"))
                )
            except TimeoutException:
                self.logger.info("No game found - waiting for game...")
                return False
            
            # Enhanced answer option finding
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re'], button, .answer-option, [class*='answer'], [class*='option']")
            
            if not links:
                self.logger.info("No answer options found")
                return False
            
            best_match = self.find_best_match(question_svg, links)
            
            if best_match:
                if self.simple_click(best_match['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    
                    # Update performance metrics
                    self.update_performance_metrics()
                    
                    match_type = "EXACT" if best_match['exact'] else "FUZZY"
                    confidence = best_match['confidence']
                    self.logger.info(f"🎯 {match_type} Match! Confidence: {confidence:.2f} | Total: {self.state['total_solved']}")
                    
                    # Wait for elements to reappear (max 16 seconds)
                    try:
                        WebDriverWait(self.driver, 16).until(
                            EC.presence_of_element_located((By.TAG_NAME, "svg"))
                        )
                        # Elements found! smart_delay will add 1-3s before next click
                        return True
                    except TimeoutException:
                        self.logger.info("Elements didn't appear within 16 seconds")
                        return False
                return True
            else:
                self.logger.info("No good match found")
                return False
            
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            return False

    # ==================== PERFORMANCE TRACKING ====================
    def update_performance_metrics(self):
        """Update performance tracking metrics"""
        if not CONFIG['performance_tracking']:
            return
            
        current_time = time.time()
        metrics = self.state['performance_metrics']
        
        if metrics['start_time'] == 0:
            metrics['start_time'] = current_time
            metrics['last_hour_count'] = 0
        
        # Calculate games per hour
        hours_running = (current_time - metrics['start_time']) / 3600
        if hours_running > 0:
            metrics['games_per_hour'] = self.state['total_solved'] / hours_running
        
        # Update hourly count
        metrics['last_hour_count'] += 1

    def get_performance_status(self):
        """Get performance metrics for status"""
        metrics = self.state['performance_metrics']
        
        if metrics['games_per_hour'] == 0:
            return ""
        
        return f"""
📈 <b>PERFORMANCE METRICS</b>
⚡ Games/Hour: {metrics['games_per_hour']:.1f}
🎯 Success Rate: {metrics.get('success_rate', 0):.1f}%
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

    # ==================== ENHANCED LEADERBOARD COMPETITION ====================
    def parse_leaderboard(self):
        """Enhanced leaderboard parsing with multiple strategies"""
        try:
            if not self.is_browser_alive():
                return None
            
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open('https://adsha.re/ten', '_blank')")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            leaderboard = []
            
            # Multiple selector strategies for leaderboard
            user_divs = soup.find_all('div', style=lambda x: x and 'width:250px' in x)
            
            # Alternative strategy if first fails
            if not user_divs:
                user_divs = soup.find_all('div', class_=True)
                user_divs = [div for div in user_divs if '#' in div.get_text()]
            
            for i, div in enumerate(user_divs[:10]):
                try:
                    text = div.get_text()
                    
                    # Enhanced user ID extraction
                    user_match = re.search(r'#(\d+)', text)
                    user_id = int(user_match.group(1)) if user_match else None
                    
                    # Enhanced total surfed extraction
                    surfed_match = re.search(r'Surfed in 3 Days:\s*([\d,]+)', text)
                    total_surfed = int(surfed_match.group(1).replace(',', '')) if surfed_match else 0
                    
                    # Enhanced today's credits extraction
                    today_match = re.search(r'T:\s*(\d+)', text)
                    today_credits = int(today_match.group(1)) if today_match else 0
                    
                    leaderboard.append({
                        'rank': i + 1,
                        'user_id': user_id,
                        'total_surfed': total_surfed,
                        'today_credits': today_credits,
                        'is_me': user_id == 4242  # Your user ID
                    })
                except Exception as e:
                    self.logger.warning(f"Error parsing leaderboard entry: {e}")
                    continue
            
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            self.state['last_leaderboard_check'] = time.time()
            self.state['leaderboard'] = leaderboard
            self.state['my_position'] = next((item for item in leaderboard if item['is_me']), None)
            
            if leaderboard:
                self.logger.info(f"Leaderboard updated - Top: #{leaderboard[0]['user_id']} with {leaderboard[0]['total_surfed']}")
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
        """Enhanced competitive target calculation"""
        if not self.state['leaderboard']:
            return None
        
        leader = self.state['leaderboard'][0]
        my_pos = self.state['my_position']
        
        if my_pos and my_pos['rank'] > 1:
            target = leader['total_surfed'] + self.state['safety_margin']
            return target
        elif my_pos and my_pos['rank'] == 1:
            if len(self.state['leaderboard']) > 1:
                second_place = self.state['leaderboard'][1]['total_surfed']
                target = second_place + self.state['safety_margin']
                return target
        
        return None

    def get_competitive_status(self):
        """Enhanced competitive status display"""
        status_text = f"""
📊 <b>ULTIMATE COMPETITIVE STATUS</b>
⏰ {self.get_ist_time()}
🔄 Status: {self.state['status']}
🎮 Games Solved: {self.state['total_solved']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
"""
        
        # Add performance metrics
        status_text += self.get_performance_status()
        
        # Enhanced competition info
        if self.state['auto_compete'] and self.state['leaderboard']:
            target = self.get_competitive_target()
            my_pos = self.state['my_position']
            
            if my_pos and target:
                leader = self.state['leaderboard'][0]
                gap = target - my_pos['total_surfed'] if my_pos['total_surfed'] < target else 0
                
                status_text += f"""
🎯 <b>Auto Target:</b> {target} total surfed (+{self.state['safety_margin']} lead)
🥇 <b>Current Position:</b> #{my_pos['rank']} ({my_pos['total_surfed']} vs #1: {leader['total_surfed']})
📈 <b>To Reach #1:</b> {gap} sites needed
💎 <b>Today:</b> {my_pos['today_credits']} credits
"""
        
        elif self.state['daily_target']:
            status_text += f"🎯 <b>Daily Target:</b> {self.state['daily_target']} sites\n"
        
        # Enhanced leaderboard preview
        if self.state['leaderboard']:
            status_text += f"\n🏆 <b>LEADERBOARD (Top 3):</b>\n"
            for entry in self.state['leaderboard'][:3]:
                marker = " 👈 YOU" if entry['is_me'] else ""
                status_text += f"{entry['rank']}. #{entry['user_id']} - {entry['total_surfed']} total{marker}\n"
        
        return status_text

    def leaderboard_monitor(self):
        """Enhanced leaderboard monitoring"""
        self.logger.info("Starting ULTIMATE leaderboard monitoring...")
        
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
                                self.send_telegram(f"🎯 <b>Auto Target Updated:</b> {target} total surfed (Beat #{leader['user_id']} with {leader['total_surfed']})")
                            
                            # Enhanced competition alerts
                            if my_pos['rank'] <= 3 and my_pos['rank'] != self.state.get('last_rank'):
                                self.state['last_rank'] = my_pos['rank']
                                if my_pos['rank'] == 1:
                                    self.send_telegram("🏆 <b>YOU ARE #1! 🎉</b>")
                                else:
                                    self.send_telegram(f"📈 <b>Now in position #{my_pos['rank']}!</b>")
                
                # Enhanced monitoring interval
                for _ in range(CONFIG['leaderboard_check_interval']):
                    if not self.state['is_running']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Leaderboard monitoring error: {e}")
                time.sleep(300)  # Wait 5 minutes on error

    # ==================== ENHANCED TARGET MANAGEMENT ====================
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

    # ==================== ULTIMATE ERROR HANDLING ====================
    def handle_consecutive_failures(self):
        """ULTIMATE progressive failure handling - 4 FAILURES BEFORE REDIRECT"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.info(f"Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead - restarting...")
            self.send_telegram("🔄 Browser dead - restarting...")
            self.restart_browser()
            return
        
        # Progressive recovery system - WAIT FOR 4 FAILURES BEFORE REDIRECT
        if current_fails >= 4:  # CHANGED: Wait for 4 failures before redirect
            self.logger.info("4 consecutive failures - redirecting to surf...")
            self.send_telegram(f"🔄 4 consecutive failures - redirecting to surf...")
            
            try:
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                self.state['consecutive_fails'] = 0
                self.send_telegram("✅ Page refresh successful!")
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        
        elif current_fails >= CONFIG['browser_restart_after_failures']:
            self.logger.warning("Multiple failures - restarting browser...")
            self.send_telegram("🔄 Multiple failures detected - restarting browser...")
            self.restart_browser()
            self.state['consecutive_fails'] = 0
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("CRITICAL: Too many failures! Stopping...")
            self.send_telegram("🚨 CRITICAL ERROR - Too many consecutive failures - Stopping solver")
            self.stop()

    # ==================== ULTIMATE SOLVER LOOP ====================
    def solver_loop(self):
        """ULTIMATE solving loop with enhanced features"""
        self.logger.info("Starting ULTIMATE solver loop...")
        self.state['status'] = 'running'
        self.state['performance_metrics']['start_time'] = time.time()
        
        # Enhanced browser setup
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("CRITICAL: Cannot start - Firefox failed")
                self.stop()
                return
        
        # Enhanced initial login
        if not self.ensure_logged_in():
            self.logger.error("CRITICAL: Initial login failed")
            self.stop()
            return
        
        cycle_count = 0
        last_memory_cleanup = time.time()
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                # Enhanced browser health monitoring
                if not self.is_browser_alive():
                    self.logger.warning("Browser dead - restarting...")
                    if not self.restart_browser():
                        self.logger.error("Browser restart failed")
                        self.stop()
                        break
                    # Enhanced re-login after restart
                    if not self.ensure_logged_in():
                        self.logger.error("Re-login after restart failed")
                        self.stop()
                        break
                
                # Enhanced memory management
                if cycle_count % 50 == 0:
                    gc.collect()
                
                # Periodic performance reporting
                if cycle_count % 100 == 0:
                    self.logger.info(f"Performance: {self.state['total_solved']} games solved | {self.state['performance_metrics']['games_per_hour']:.1f} games/hour")
                
                # Solve game
                game_solved = self.solve_symbol_game()
                
                if game_solved:
                    self.state['consecutive_fails'] = 0
                    # Already waited 30 seconds in solve_symbol_game
                else:
                    self.handle_consecutive_failures()
                    time.sleep(5)
                
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
        self.state['performance_metrics']['start_time'] = time.time()
        
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        self.monitoring_thread = threading.Thread(target=self.leaderboard_monitor)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("ULTIMATE solver started!")
        self.send_telegram("🚀 <b>ULTIMATE Solver Started!</b>")
        return "✅ ULTIMATE Solver started successfully!"

    def stop(self):
        """Enhanced solver stop"""
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        
        # Calculate final performance metrics
        if self.state['performance_metrics']['start_time'] > 0:
            total_time = time.time() - self.state['performance_metrics']['start_time']
            games_per_hour = self.state['total_solved'] / (total_time / 3600) if total_time > 0 else 0
            self.state['performance_metrics']['games_per_hour'] = games_per_hour
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("ULTIMATE solver stopped")
        self.send_telegram("🛑 <b>ULTIMATE Solver Stopped!</b>")
        return "✅ ULTIMATE Solver stopped successfully!"

    def status(self):
        """Enhanced status with all features"""
        # Refresh leaderboard if stale
        if time.time() - self.state['last_leaderboard_check'] > 1800:
            self.parse_leaderboard()
        
        return self.get_competitive_status()

# ==================== ULTIMATE TELEGRAM BOT ====================
class UltimateTelegramBot:
    def __init__(self):
        self.solver = UltimateSymbolSolver()
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
        """Enhanced message processing - REMOVED /detailed COMMAND"""
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
                    leader_text += f"{entry['rank']}. #{entry['user_id']} - {entry['total_surfed']} total{marker}\n"
                response = leader_text
            else:
                response = "❌ Could not fetch leaderboard"
        elif text.startswith('/login'):
            response = "🔐 Attempting login..." if self.solver.force_login() else "❌ Login failed"
        elif text.startswith('/performance'):
            response = self.solver.get_performance_status()
        elif text.startswith('/restart'):
            response = "🔄 Restarting browser..." if self.solver.restart_browser() else "❌ Restart failed"
        elif text.startswith('/help'):
            response = """
🤖 <b>ULTIMATE AdShare Solver</b>

<b>Basic Commands:</b>
/start - Start solver
/stop - Stop solver  
/status - Competitive status
/screenshot - Get screenshot
/login - Force login
/restart - Restart browser

<b>Target Management:</b>
/target 3000 - Set daily target
/target clear - Clear target
/compete - Auto-compete mode
/compete 150 - Compete with +150 margin

<b>Information:</b>
/leaderboard - Show top 10
/performance - Performance metrics
/help - Show this help

<b>Features:</b>
✅ Working Login System
✅ Page State Detection  
✅ Progressive Error Recovery
✅ uBlock Origin Integration
✅ Performance Tracking
✅ Enhanced Competition
✅ Memory Optimization
            """
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Enhanced update handling"""
        self.logger.info("Starting ULTIMATE Telegram bot...")
        
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
    bot.logger.info("ULTIMATE AdShare Solver started!")
    bot.handle_updates()
