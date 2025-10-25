#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - ULTIMATE VERSION
With your symbol matching + force login + manual controls
"""

import os
import time
import random
import logging
import re
import requests
import threading
import json
import asyncio
import subprocess
import shutil
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

# ==================== CONFIGURATION ====================
CONFIG = {
    'email': os.getenv('ADSHARE_EMAIL', 'jiocloud90@gmail.com'),
    'password': os.getenv('ADSHARE_PASSWORD', '@Sd2007123'),
    'telegram_token': os.getenv('TELEGRAM_TOKEN', '8225236307:AAF9Y2-CM7TlLDFm2rcTVY6f3SA75j0DFI8'),
    'base_delay': 2,
    'random_delay': True,
    'min_delay': 1,
    'max_delay': 3,
    'max_consecutive_failures': 10,
    'refresh_page_after_failures': 5,
    'page_timeout': 60000,
    'firefox_profile': '/app/.mozilla/firefox/adshare_profile',
    'cookies_file': '/app/cookies.json'
}

class AdShareSolver:
    def __init__(self):
        self.playwright = None
        self.context = None
        self.page = None
        self.telegram_chat_id = None
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'is_logged_in': False,
            'consecutive_fails': 0,
            'browser_restarts': 0,
            'daily_target': 0,
            'credits_earned_today': 0,
            'daily_start_time': self.get_daily_reset_time(),
            'is_paused': False,
            'paused_until': None,
            'session_history': [],
        }
        self.solver_thread = None
        self.setup_logging()
        self.setup_telegram()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        self.logger = logging.getLogger(__name__)

    def setup_telegram(self):
        try:
            self.logger.info("Setting up Telegram bot...")
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.telegram_chat_id = updates['result'][-1]['message']['chat']['id']
                    self.logger.info(f"Telegram Chat ID: {self.telegram_chat_id}")
                    self.send_telegram("🤖 <b>AdShare Solver Started!</b>")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Telegram setup failed: {e}")
            return False

    def send_telegram(self, text, parse_mode='HTML'):
        if not self.telegram_chat_id:
            return False
        try:
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendMessage"
            payload = {'chat_id': self.telegram_chat_id, 'text': text, 'parse_mode': parse_mode}
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Telegram send failed: {e}")
            return False

    # ==================== CORE FUNCTIONS ====================
    
    def get_ist_time(self):
        utc_now = datetime.utcnow()
        ist_offset = timedelta(hours=5, minutes=30)
        return utc_now + ist_offset

    def get_daily_reset_time(self):
        ist_now = self.get_ist_time()
        reset_time = ist_now.replace(hour=5, minute=30, second=0, microsecond=0)
        if ist_now >= reset_time:
            reset_time += timedelta(days=1)
        return reset_time

    def check_daily_reset(self):
        ist_now = self.get_ist_time()
        reset_time = self.state['daily_start_time']
        if ist_now >= reset_time:
            self.logger.info("🎯 DAILY RESET - Starting new day!")
            self.state['credits_earned_today'] = 0
            self.state['daily_start_time'] = self.get_daily_reset_time()
            self.state['session_history'] = []
            return True
        return False

    async def smart_delay_async(self, min_delay=None, max_delay=None):
        min_delay = min_delay or CONFIG['min_delay']
        max_delay = max_delay or CONFIG['max_delay']
        delay = random.uniform(min_delay, max_delay) if CONFIG['random_delay'] else CONFIG['base_delay']
        await asyncio.sleep(delay)
        return delay

    async def setup_playwright(self):
        self.logger.info("Setting up Playwright with persistent Firefox profile...")
        try:
            if self.playwright:
                await self.playwright.stop()
            
            self.playwright = await async_playwright().start()
            self.context = await self.playwright.firefox.launch_persistent_context(
                CONFIG['firefox_profile'],
                headless=True,
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-blink-features=AutomationControlled',
                ],
                timeout=CONFIG['page_timeout'],
            )
            self.page = await self.context.new_page()
            self.page.set_default_timeout(CONFIG['page_timeout'])
            self.page.set_default_navigation_timeout(CONFIG['page_timeout'] + 15000)
            
            # Load cookies if available
            await self.load_cookies()
            
            self.state['browser_restarts'] += 1
            self.logger.info("Playwright started with persistent context!")
            return True
            
        except Exception as e:
            self.logger.error(f"Playwright setup failed: {e}")
            return False

    async def load_cookies(self):
        """Load cookies from file"""
        try:
            if os.path.exists(CONFIG['cookies_file']):
                with open(CONFIG['cookies_file'], 'r') as f:
                    cookies = json.load(f)
                
                await self.context.clear_cookies()
                await self.context.add_cookies(cookies)
                self.logger.info(f"Loaded {len(cookies)} cookies")
                return True
        except Exception as e:
            self.logger.warning(f"Could not load cookies: {e}")
        return False

    async def save_cookies(self):
        """Save current cookies to file"""
        try:
            cookies = await self.context.cookies()
            with open(CONFIG['cookies_file'], 'w') as f:
                json.dump(cookies, f)
            self.logger.info("Cookies saved")
        except Exception as e:
            self.logger.warning(f"Could not save cookies: {e}")

    async def clear_browser_data(self):
        """Clear all browser data"""
        try:
            self.logger.info("Clearing browser data...")
            
            # Clear cookies file
            if os.path.exists(CONFIG['cookies_file']):
                os.remove(CONFIG['cookies_file'])
            
            # Clear browser profile
            if os.path.exists(CONFIG['firefox_profile']):
                shutil.rmtree(CONFIG['firefox_profile'])
                os.makedirs(CONFIG['firefox_profile'])
            
            # Restart browser
            if self.state['is_running']:
                await self.restart_browser()
            
            self.logger.info("Browser data cleared successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear browser data: {e}")
            return False

    async def restart_browser(self):
        """Restart browser"""
        self.logger.info("🔄 Restarting browser...")
        try:
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
                
            if await self.setup_playwright():
                await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
                self.logger.info("Browser restart completed successfully!")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    def is_browser_alive(self):
        """Check if browser is still running"""
        try:
            if not self.context or not self.page or self.page.is_closed() or not self.context.is_connected():
                return False
            return True
        except Exception:
            return False

    # ==================== ULTIMATE LOGIN ====================
    async def ultimate_login(self):
        """ULTIMATE LOGIN WITH ALL FALLBACKS"""
        try:
            self.logger.info("🚀 STARTING ULTIMATE LOGIN...")
            
            login_url = "https://adsha.re/login"
            await self.page.goto(login_url, wait_until='networkidle')
            await self.page.wait_for_selector("body")
            
            await self.smart_delay_async()
            
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            all_forms = soup.find_all('form')
            self.logger.info(f"Found {len(all_forms)} forms")
            
            form = soup.find('form', {'name': 'login'})
            if not form:
                form = all_forms[0] if all_forms else None
            
            if not form:
                self.logger.error("No forms found at all!")
                return False
            
            password_field_name = None
            
            for field in form.find_all('input'):
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                
                if field_value == 'Password' and field_name != 'mail' and field_name:
                    password_field_name = field_name
                    self.logger.info(f"Found password field by value: {password_field_name}")
                    break
            
            if not password_field_name:
                password_fields = form.find_all('input', {'type': 'password'})
                if password_fields:
                    password_field_name = password_fields[0].get('name')
                    self.logger.info(f"Found password field by type: {password_field_name}")
            
            if not password_field_name:
                for field in form.find_all('input'):
                    field_name = field.get('name', '')
                    field_type = field.get('type', '')
                    if field_name and field_name != 'mail' and field_type != 'email':
                        password_field_name = field_name
                        self.logger.info(f"Found password field by exclusion: {password_field_name}")
                        break
            
            if not password_field_name:
                inputs = form.find_all('input')
                if len(inputs) >= 2:
                    password_field_name = inputs[1].get('name')
                    self.logger.info(f"Found password field by position: {password_field_name}")
            
            if not password_field_name:
                self.logger.error("Could not find password field by any method")
                return False
            
            # Fill email
            email_selectors = [
                "input[name='mail']",
                "input[type='email']", 
                "input[placeholder*='email' i]",
                "input[placeholder*='Email' i]",
                "input[name*='mail' i]",
                "input[name*='email' i]",
                "input:first-of-type",
                "input:nth-of-type(1)"
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    if await self.page.is_visible(selector):
                        await self.page.fill(selector, "")
                        await self.page.fill(selector, CONFIG['email'])
                        self.logger.info(f"Email filled with: {selector}")
                        email_filled = True
                        break
                except:
                    continue
            
            if not email_filled:
                self.logger.error("All email filling methods failed")
                return False
            
            await self.smart_delay_async()
            
            # Fill password
            password_selectors = [
                f"input[name='{password_field_name}']",
                "input[type='password']",
                "input[placeholder*='password' i]",
                "input[placeholder*='Password' i]",
                "input:nth-of-type(2)",
                "input:last-of-type"
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    if await self.page.is_visible(selector):
                        await self.page.fill(selector, "")
                        await self.page.fill(selector, CONFIG['password'])
                        self.logger.info(f"Password filled with: {selector}")
                        password_filled = True
                        break
                except:
                    continue
            
            if not password_filled:
                self.logger.error("All password filling methods failed")
                return False
            
            await self.smart_delay_async()
            
            # Submit form
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']", 
                "button",
                "input[value*='Login' i]",
                "input[value*='Sign' i]",
                "button:has-text('Login')",
                "button:has-text('Sign')",
                "input[value*='Log']",
                "input[value*='login']",
                "form button",
                "form input[type='submit']"
            ]
            
            login_clicked = False
            
            for selector in login_selectors:
                try:
                    if await self.page.is_visible(selector):
                        await self.page.click(selector)
                        self.logger.info(f"Login clicked with: {selector}")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                try:
                    await self.page.evaluate("""() => {
                        const form = document.querySelector("form");
                        if (form) form.submit();
                    }""")
                    self.logger.info("Form submitted via JavaScript")
                    login_clicked = True
                except:
                    pass
            
            if not login_clicked:
                try:
                    password_selector = f"input[name='{password_field_name}']"
                    await self.page.click(password_selector)
                    await self.page.keyboard.press('Enter')
                    self.logger.info("Enter key pressed in password field")
                    login_clicked = True
                except:
                    pass
            
            if not login_clicked:
                try:
                    await self.page.click('body')
                    await self.page.keyboard.press('Enter')
                    self.logger.info("Enter key pressed on body")
                    login_clicked = True
                except:
                    pass
            
            if not login_clicked:
                self.logger.error("All login submission methods failed")
                return False
            
            await self.smart_delay_async()
            await asyncio.sleep(8)
            
            current_url = self.page.url.lower()
            page_title = await self.page.title()
            
            self.logger.info(f"After login - URL: {current_url}, Title: {page_title}")
            
            await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
            await self.smart_delay_async()
            
            final_url = self.page.url.lower()
            self.logger.info(f"Final URL: {final_url}")
            
            if "surf" in final_url or "dashboard" in final_url:
                self.logger.info("🎉 LOGIN SUCCESSFUL!")
                self.state['is_logged_in'] = True
                await self.save_cookies()
                self.send_telegram("✅ <b>LOGIN SUCCESSFUL!</b>")
                return True
            elif "login" in final_url:
                self.logger.error("❌ LOGIN FAILED - Still on login page")
                return False
            else:
                self.logger.warning("⚠️ On unexpected page, but might be logged in")
                self.state['is_logged_in'] = True
                return True
                
        except Exception as e:
            self.logger.error(f"❌ ULTIMATE LOGIN ERROR: {e}")
            return False

    async def is_already_logged_in(self):
        """Check if already logged in"""
        try:
            await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
            content = await self.page.content()
            return 'login' not in content.lower() and 'surf' in self.page.url.lower()
        except Exception:
            return False

    # ==================== GAME SOLVING ====================
    async def ensure_correct_page(self):
        """Ensure we're on the correct surf page"""
        if not self.is_browser_alive():
            self.logger.error("Browser dead during page check")
            return False
            
        try:
            current_url = self.page.url.lower()
            
            if "login" in current_url:
                self.logger.info("Auto-login: redirected to login")
                if await self.ultimate_login():
                    return True
                else:
                    self.send_telegram("🔐 <b>LOGIN REQUIRED</b>\nPlease use /forcelogin or send cookies.json")
                    return False
            
            if "surf" not in current_url and "adsha.re" in current_url:
                self.logger.info("Redirecting to surf page...")
                await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
                await self.smart_delay_async()
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Page navigation error: {e}")
            return False

    def calculate_similarity(self, str1, str2):
        """Calculate string similarity"""
        if len(str1) == 0 or len(str2) == 0:
            return 0.0
        
        common_chars = sum(1 for a, b in zip(str1, str2) if a == b)
        max_len = max(len(str1), len(str2))
        return common_chars / max_len if max_len > 0 else 0.0

    async def compare_symbols(self, question_svg, answer_svg):
        """Compare SVG symbols"""
        try:
            question_content = await question_svg.inner_html()
            answer_content = await answer_svg.inner_html()
            
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

    async def find_best_match(self, question_svg, links):
        """Find best matching symbol"""
        best_match = None
        highest_confidence = 0
        exact_matches = []
        
        for link in links:
            try:
                answer_svg = await link.query_selector("svg")
                if answer_svg:
                    comparison = await self.compare_symbols(question_svg, answer_svg)
                    
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

    async def human_like_click(self, locator):
        try:
            await locator.wait_for(state='visible', timeout=CONFIG['page_timeout'])
            await locator.scroll_into_view_if_needed()
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await locator.hover()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await locator.click()
            self.logger.info(f"Human-like click with {random.uniform(0.5, 1.5):.1f}s delay")
            return True
        except Exception as e:
            self.logger.error(f"Human-like click failed: {e}")
            return False

    async def solve_symbol_game(self):
        """Main game solving logic"""
        if not self.state['is_running'] or self.state['is_paused']:
            return False
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead during game solving")
            if await self.restart_browser():
                return await self.solve_symbol_game()
            return False
            
        try:
            if not await self.ensure_correct_page():
                self.logger.info("Not on correct page, redirecting...")
                await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
                if not await self.ensure_correct_page():
                    return False
            
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            question_svg = await self.page.wait_for_selector("svg", timeout=15000)
            
            if not question_svg:
                self.logger.info("Waiting for game to load...")
                return False
            
            think_time = random.uniform(0.5, 1.5)
            await asyncio.sleep(think_time)
            
            links = await self.page.query_selector_all("a[href*='adsha.re'], button, .answer-option")
            
            if not links:
                self.logger.info("No answer links found")
                return False
            
            best_match = await self.find_best_match(question_svg, links)
            
            if best_match:
                if await self.human_like_click(best_match['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    
                    # Track credits earned
                    target_reached = self.update_credits_earned(1)
                    
                    match_type = "EXACT" if best_match['exact'] else "FUZZY"
                    self.logger.info(f"{match_type} Match! Total: {self.state['total_solved']}, Credits: {self.state['credits_earned_today']}")
                    
                    # Stop if target reached
                    if target_reached:
                        self.logger.info("Daily target reached, stopping solver")
                        self.state['is_running'] = False
                        return True
                    
                    await self.smart_delay_async(2.0, 3.0)
                    return True
            
            self.logger.info("No good match found")
            self.handle_consecutive_failures()
            return False
            
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            if "crashed" in str(e).lower() or "closed" in str(e).lower():
                self.logger.info("Attempting browser recovery...")
                if await self.restart_browser():
                    return await self.solve_symbol_game()
            
            self.handle_consecutive_failures()
            return False

    def handle_consecutive_failures(self):
        self.state['consecutive_fails'] += 1
        self.logger.info(f"Consecutive failures: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}")
        
        if self.state['consecutive_fails'] >= CONFIG['refresh_page_after_failures']:
            self.logger.info("Refreshing page...")
            try:
                asyncio.create_task(self.page.reload())
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        elif self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures! Stopping...")
            self.send_telegram("🚨 <b>TOO MANY FAILURES</b>\nStopping solver for safety")
            self.stop()

    def update_credits_earned(self, credits_earned=1):
        """Update credits and check daily target"""
        self.check_daily_reset()
        self.state['credits_earned_today'] += credits_earned
        
        session_record = {
            'timestamp': self.get_ist_time().strftime('%H:%M IST'),
            'credits': credits_earned,
            'total_earned': self.state['credits_earned_today']
        }
        self.state['session_history'].append(session_record)
        if len(self.state['session_history']) > 10:
            self.state['session_history'] = self.state['session_history'][-10:]
            
        if self.state['daily_target'] > 0 and self.state['credits_earned_today'] >= self.state['daily_target']:
            self.logger.info(f"🎉 DAILY TARGET REACHED! {self.state['credits_earned_today']}/{self.state['daily_target']}")
            self.send_telegram(
                f"🎉 <b>DAILY TARGET ACHIEVED!</b>\n"
                f"💎 Earned: {self.state['credits_earned_today']} credits\n"
                f"🎯 Target: {self.state['daily_target']} credits\n"
                f"⏰ Time: {self.get_ist_time().strftime('%I:%M %p IST')}\n"
                f"🛑 Auto-stopping..."
            )
            self.stop()
            return True
        return False

    async def send_screenshot(self):
        """Send real-time screenshot to Telegram"""
        if not self.page or not self.telegram_chat_id:
            return "❌ Browser not running or Telegram not configured"
        try:
            screenshot_path = "/tmp/screenshot.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendPhoto"
            with open(screenshot_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.telegram_chat_id, 'caption': f'🖥️ Screenshot - {self.get_ist_time().strftime("%H:%M IST")}'}
                response = requests.post(url, files=files, data=data, timeout=30)
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return "✅ Screenshot sent!" if response.status_code == 200 else f"❌ Failed: {response.status_code}"
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    async def check_pause_status(self):
        """Check if pause time has expired"""
        if self.state['paused_until']:
            if datetime.now() >= self.state['paused_until']:
                self.state['is_paused'] = False
                self.state['paused_until'] = None
                self.send_telegram("⏰ <b>Pause time over! Resuming...</b>")
                return False
            return True
        return self.state['is_paused']

    # ==================== MAIN SOLVER LOOP ====================
    async def solver_loop(self):
        """Main solver loop"""
        self.logger.info("Starting solver loop...")
        self.state['status'] = 'running'
        
        if not await self.setup_playwright():
            self.logger.error("Playwright setup failed")
            self.stop()
            return
            
        # Check if login needed
        await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
        if not await self.is_already_logged_in():
            self.logger.info("Not logged in, checking for cookies...")
            if not await self.load_cookies():
                self.send_telegram("🔐 <b>NOT LOGGED IN</b>\nUse /forcelogin or send cookies.json file")
                self.stop()
                return
            
        # Main solving loop
        cycle_count = 0
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                # Check pause status
                if await self.check_pause_status():
                    await asyncio.sleep(60)
                    continue
                    
                # Periodic maintenance
                if cycle_count % 10 == 0:
                    self.check_daily_reset()
                    
                if cycle_count % 5 == 0 and not self.is_browser_alive():
                    self.logger.warning("Browser health check failed, restarting...")
                    if not await self.restart_browser():
                        self.logger.error("Browser restart failed, stopping...")
                        self.stop()
                        break
                        
                # Solve game
                if await self.solve_symbol_game():
                    self.state['consecutive_fails'] = 0
                else:
                    self.state['consecutive_fails'] += 1
                    
                cycle_count += 1
                await asyncio.sleep(random.uniform(CONFIG['min_delay'], CONFIG['max_delay']))
                
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                self.state['consecutive_fails'] += 1
                await asyncio.sleep(10)
                
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures, stopping...")
            self.stop()

    # ==================== TELEGRAM COMMANDS ====================
    def start(self):
        if self.state['is_running']:
            return "❌ Solver already running"
            
        self.state['is_running'] = True
        self.state['consecutive_fails'] = 0
        self.state['is_paused'] = False
        self.state['paused_until'] = None
        
        def run_solver():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.solver_loop())
            except Exception as e:
                self.logger.error(f"Solver loop error: {e}")
            finally:
                loop.close()
                
        self.solver_thread = threading.Thread(target=run_solver)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        status_msg = f"🚀 <b>Solver Started!</b>\n🎯 Target: {self.state['daily_target']} credits\n💎 Earned: {self.state['credits_earned_today']} credits"
        self.send_telegram(status_msg)
        return "✅ Solver started successfully!"

    def stop(self):
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        self.state['is_paused'] = False
        self.state['paused_until'] = None
        
        async def close_playwright():
            try:
                if self.context:
                    await self.context.close()
                if self.playwright:
                    await self.playwright.stop()
            except Exception as e:
                self.logger.warning(f"Playwright close warning: {e}")
                
        def run_cleanup():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(close_playwright())
            loop.close()
            
        cleanup_thread = threading.Thread(target=run_cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        self.logger.info("Solver stopped")
        self.send_telegram("🛑 <b>Solver Stopped!</b>")
        return "✅ Solver stopped successfully!"

    def pause(self, minutes=None):
        """Pause the solver"""
        if not self.state['is_running']:
            return "❌ Solver is not running"
            
        self.state['is_paused'] = True
        
        if minutes:
            self.state['paused_until'] = datetime.now() + timedelta(minutes=minutes)
            return f"⏸️ <b>Paused for {minutes} minutes</b>\nAuto-resume at {self.state['paused_until'].strftime('%H:%M IST')}"
        else:
            self.state['paused_until'] = None
            return "⏸️ <b>Paused indefinitely</b>\nUse /resume to continue"

    def resume(self):
        """Resume the solver"""
        if not self.state['is_running']:
            return "❌ Solver is not running"
            
        self.state['is_paused'] = False
        self.state['paused_until'] = None
        return "▶️ <b>Resumed solving!</b>"

    def set_daily_target(self, target_credits):
        self.state['daily_target'] = target_credits
        self.check_daily_reset()
        return f"🎯 <b>DAILY TARGET SET</b>\n💎 Goal: {target_credits} credits\n📊 Progress: {self.state['credits_earned_today']}/{target_credits}"

    def status(self):
        self.check_daily_reset()
        target = self.state['daily_target']
        earned = self.state['credits_earned_today']
        progress_percent = (earned / target * 100) if target > 0 else 0
        
        status = f"""
📊 <b>DETAILED STATUS</b>
⏰ Current Time: {self.get_ist_time().strftime('%I:%M %p IST')}
🔄 Solver Status: {self.state['status']}
🎯 Daily Target: {self.state['daily_target']} credits
💎 Earned Today: {self.state['credits_earned_today']} credits
📈 Progress: {progress_percent:.1f}%
🎮 Games Solved: {self.state['total_solved']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
🖥️ Browser Health: {'✅' if self.is_browser_alive() else '❌'}
⏸️ Paused: {'✅' if self.state['is_paused'] else '❌'}
"""
        if self.state['paused_until']:
            time_left = self.state['paused_until'] - datetime.now()
            minutes_left = int(time_left.total_seconds() / 60)
            status += f"⏰ Resumes in: {minutes_left} minutes"
            
        return status

class TelegramBot:
    def __init__(self):
        self.solver = AdShareSolver()
        self.logger = logging.getLogger(__name__)

    def handle_updates(self):
        last_update_id = None
        self.logger.info("Starting Telegram bot...")
        
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
                self.logger.error(f"Telegram error: {e}")
                time.sleep(5)

    def process_message(self, update):
        if 'message' not in update:
            return
            
        chat_id = update['message']['chat']['id']
        self.solver.telegram_chat_id = chat_id
        response = ""
        
        # Handle document (cookies.json file)
        if 'document' in update['message']:
            file_id = update['message']['document']['file_id']
            file_name = update['message']['document']['file_name']
            
            if file_name == 'cookies.json':
                async def download_cookies():
                    return await self.solver.download_cookies(file_id)
                response = self.run_async(download_cookies)
            else:
                response = "❌ Please send cookies.json file"

        # Handle text commands
        if 'text' in update['message']:
            text = update['message']['text']
            
            if text.startswith('/start'):
                response = self.solver.start()
            elif text.startswith('/stop'):
                response = self.solver.stop()
            elif text.startswith('/status'):
                response = self.solver.status()
            elif text.startswith('/target'):
                try:
                    target = int(text.split()[1])
                    response = self.solver.set_daily_target(target)
                except:
                    response = "❌ Usage: /target 2000"
            elif text.startswith('/screenshot'):
                async def take_screenshot():
                    return await self.solver.send_screenshot()
                response = self.run_async(take_screenshot)
            elif text.startswith('/forcelogin'):
                async def force_login():
                    if await self.solver.ultimate_login():
                        return "✅ Force login successful!"
                    else:
                        return "❌ Force login failed"
                response = self.run_async(force_login)
            elif text.startswith('/pause'):
                try:
                    parts = text.split()
                    if len(parts) > 1:
                        minutes = int(parts[1])
                        response = self.solver.pause(minutes)
                    else:
                        response = self.solver.pause()
                except:
                    response = "❌ Usage: /pause 30 (for 30 minutes) or /pause"
            elif text.startswith('/resume'):
                response = self.solver.resume()
            elif text.startswith('/cleardata'):
                async def clear_data():
                    if await self.solver.clear_browser_data():
                        return "✅ Browser data cleared!"
                    else:
                        return "❌ Failed to clear browser data"
                response = self.run_async(clear_data)
            elif text.startswith('/help'):
                response = """
🤖 <b>AdShare Solver Commands</b>

🔧 Core Commands:
/start - Start solver
/stop - Stop solver  
/status - Check status
/target 2000 - Set daily credit goal

🖥️ Browser Commands:
/screenshot - Real-time screenshot
/forcelogin - Force login with email/password
/cleardata - Clear all browser data

⏸️ Control Commands:
/pause 30 - Pause for 30 minutes
/pause - Pause indefinitely  
/resume - Resume from pause

📁 Setup:
Send cookies.json file to load session
"""
        
        if response:
            self.solver.send_telegram(response)

    async def download_cookies(self, file_id):
        """Download cookies.json file from Telegram"""
        try:
            # Get file info from Telegram
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getFile"
            params = {'file_id': file_id}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return f"❌ Failed to get file info: {response.status_code}"
            
            file_info = response.json()
            if not file_info.get('ok'):
                return f"❌ Telegram API error: {file_info.get('description', 'Unknown error')}"
            
            file_path = file_info['result']['file_path']
            
            # Download the file
            download_url = f"https://api.telegram.org/file/bot{CONFIG['telegram_token']}/{file_path}"
            download_response = requests.get(download_url, timeout=60)
            download_response.raise_for_status()
            
            # Save cookies file
            with open(CONFIG['cookies_file'], 'wb') as f:
                f.write(download_response.content)
            
            self.logger.info("Cookies file downloaded successfully")
            return "✅ Cookies downloaded! Use /start to begin solving."
                
        except Exception as e:
            self.logger.error(f"Cookies download failed: {e}")
            return f"❌ Cookies download failed: {str(e)}"

    def run_async(self, async_func):
        """Run async function in sync context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(async_func())
            loop.close()
            return result
        except Exception as e:
            loop.close()
            return f"❌ Error: {str(e)}"

if __name__ == '__main__':
    bot = TelegramBot()
    bot.logger.info("AdShare Solver started!")
    bot.handle_updates()
