#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - CREDIT GOAL EDITION
DAILY TARGET SYSTEM + IST TIMING + ALL EXISTING FEATURES
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
import asyncio
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
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

class CreditGoalSolver:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        
        # State Management
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'last_credits': 'Unknown',
            'monitoring_active': False,
            'is_logged_in': False,
            'consecutive_fails': 0,
            'last_error_screenshot': 0,
            'browser_restarts': 0,
            'last_browser_health_check': 0,
            
            # Credit Goal System
            'daily_target': 0,
            'credits_earned_today': 0,
            'daily_start_time': self.get_daily_reset_time(),
            'is_paused': False,
            'session_history': [],
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
                    self.send_telegram("🤖 <b>AdShare CREDIT GOAL Solver Started!</b>")
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

    # ==================== IST TIME MANAGEMENT ====================
    def get_ist_time(self):
        """Get current IST time (UTC+5:30)"""
        utc_now = datetime.utcnow()
        ist_offset = timedelta(hours=5, minutes=30)
        return utc_now + ist_offset

    def get_daily_reset_time(self):
        """Get today's reset time (5:30 AM IST)"""
        ist_now = self.get_ist_time()
        reset_time = ist_now.replace(hour=5, minute=30, second=0, microsecond=0)
        
        # If current time is after 5:30 AM, reset is tomorrow
        if ist_now >= reset_time:
            reset_time += timedelta(days=1)
            
        return reset_time

    def check_daily_reset(self):
        """Check if daily reset has occurred"""
        ist_now = self.get_ist_time()
        reset_time = self.state['daily_start_time']
        
        if ist_now >= reset_time:
            self.logger.info("🎯 DAILY RESET - Starting new day!")
            self.state['credits_earned_today'] = 0
            self.state['daily_start_time'] = self.get_daily_reset_time()
            self.state['session_history'] = []
            
            if self.state['daily_target'] > 0:
                self.send_telegram(
                    f"🔄 <b>New Day Started!</b>\n"
                    f"🎯 Target: {self.state['daily_target']} credits\n"
                    f"⏰ Reset: {self.state['daily_start_time'].strftime('%I:%M %p IST')}"
                )
            return True
        return False

    def get_time_until_reset(self):
        """Get time remaining until daily reset"""
        ist_now = self.get_ist_time()
        reset_time = self.state['daily_start_time']
        time_left = reset_time - ist_now
        
        hours = int(time_left.total_seconds() // 3600)
        minutes = int((time_left.total_seconds() % 3600) // 60)
        return hours, minutes

    # ==================== CREDIT GOAL SYSTEM ====================
    def set_daily_target(self, target_credits):
        """Set daily credit target"""
        self.state['daily_target'] = target_credits
        self.check_daily_reset()  # Ensure we're tracking current day
        
        credits_per_hour = 240  # 4 credits/minute × 60 minutes
        hours_needed = target_credits / credits_per_hour
        
        ist_now = self.get_ist_time()
        reset_hours, reset_minutes = self.get_time_until_reset()
        
        response = (
            f"🎯 <b>DAILY TARGET SET</b>\n"
            f"💎 Goal: {target_credits} credits\n"
            f"⏰ Estimated: {hours_needed:.1f} hours\n"
            f"📊 Progress: {self.state['credits_earned_today']}/{target_credits}\n"
            f"🕒 Reset in: {reset_hours}h {reset_minutes}m\n"
            f"🌅 Reset at: 5:30 AM IST"
        )
        
        return response

    def update_credits_earned(self, credits_earned=4):
        """Update earned credits and check if target reached"""
        self.check_daily_reset()  # Check for daily reset
        
        self.state['credits_earned_today'] += credits_earned
        
        # Record session activity
        session_record = {
            'timestamp': self.get_ist_time().strftime('%H:%M IST'),
            'credits': credits_earned,
            'total_earned': self.state['credits_earned_today']
        }
        self.state['session_history'].append(session_record)
        
        # Keep only last 10 sessions
        if len(self.state['session_history']) > 10:
            self.state['session_history'] = self.state['session_history'][-10:]
        
        # Check if target reached
        if (self.state['daily_target'] > 0 and 
            self.state['credits_earned_today'] >= self.state['daily_target']):
            
            self.logger.info(f"🎉 DAILY TARGET REACHED! {self.state['credits_earned_today']}/{self.state['daily_target']}")
            self.send_telegram(
                f"🎉 <b>DAILY TARGET ACHIEVED!</b>\n"
                f"💎 Earned: {self.state['credits_earned_today']} credits\n"
                f"🎯 Target: {self.state['daily_target']} credits\n"
                f"⏰ Time: {self.get_ist_time().strftime('%I:%M %p IST')}\n"
                f"🛑 Auto-pausing until tomorrow..."
            )
            
            self.state['is_paused'] = True
            return True
        
        return False

    def get_progress_status(self):
        """Get detailed progress status"""
        self.check_daily_reset()  # Ensure current day tracking
        
        target = self.state['daily_target']
        earned = self.state['credits_earned_today']
        progress_percent = (earned / target * 100) if target > 0 else 0
        
        reset_hours, reset_minutes = self.get_time_until_reset()
        
        status = (
            f"📊 <b>DAILY PROGRESS</b>\n"
            f"💎 Earned: {earned} / {target} credits\n"
            f"📈 Progress: {progress_percent:.1f}%\n"
            f"⏰ Reset in: {reset_hours}h {reset_minutes}m\n"
            f"🌅 Reset at: 5:30 AM IST\n"
            f"🔄 Status: {'PAUSED' if self.state['is_paused'] else 'ACTIVE'}"
        )
        
        # Add recent session activity
        if self.state['session_history']:
            status += "\n\n<b>Recent Activity:</b>"
            for session in self.state['session_history'][-3:]:
                status += f"\n{session['timestamp']}: +{session['credits']} credits"
        
        return status

    # ==================== EXISTING FEATURES (PRESERVED) ====================
    async def send_screenshot(self, caption="🖥️ Screenshot"):
        """Send screenshot to Telegram"""
        if not self.page or not self.telegram_chat_id:
            return "❌ Browser not running or Telegram not configured"
        
        try:
            screenshot_path = "/tmp/screenshot.png"
            await self.page.screenshot(path=screenshot_path)
            
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendPhoto"
            
            with open(screenshot_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.telegram_chat_id,
                    'caption': f'{caption} - {self.get_ist_time().strftime("%H:%M IST")}'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
            return "✅ Screenshot sent!" if response.status_code == 200 else f"❌ Failed: {response.status_code}"
                
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    async def setup_playwright(self):
        """Setup Playwright with memory optimization"""
        self.logger.info("Setting up Playwright...")
        
        try:
            if self.playwright:
                await self.playwright.stop()
            
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.firefox.launch(
                headless=True,
                args=[
                    '--headless',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )
            
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
            )
            
            self.page = await context.new_page()
            
            self.page.set_default_timeout(30000)
            self.page.set_default_navigation_timeout(45000)
            
            self.state['browser_restarts'] += 1
            self.logger.info("Playwright started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Playwright setup failed: {e}")
            return False

    def is_browser_alive(self):
        """Check if browser is alive"""
        try:
            if not self.page or not self.browser:
                return False
            
            if self.page.is_closed() or not self.browser.is_connected():
                return False
            
            self.state['last_browser_health_check'] = time.time()
            return True
            
        except Exception:
            return False

    async def restart_browser(self):
        """Restart browser and recover session"""
        self.logger.info("🔄 Restarting browser...")
        
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            if await self.setup_playwright():
                if os.path.exists(self.cookies_file):
                    await self.load_cookies()
                    self.logger.info("Session recovered after restart")
                
                await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
                self.logger.info("Browser restart completed successfully!")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    async def smart_delay_async(self, min_delay=None, max_delay=None):
        """Async version of smart delay"""
        if min_delay is None:
            min_delay = CONFIG['min_delay']
        if max_delay is None:
            max_delay = CONFIG['max_delay']
        
        if CONFIG['random_delay']:
            delay = random.uniform(min_delay, max_delay)
        else:
            delay = CONFIG['base_delay']
        
        await asyncio.sleep(delay)
        return delay

    # ==================== ANTI-BOT FEATURES (PRESERVED) ====================
    async def human_like_click(self, element):
        """Human-like click with anti-bot timing"""
        try:
            pre_click_delay = random.uniform(1.0, 2.0)
            await asyncio.sleep(pre_click_delay)
            
            await element.hover()
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            await element.click()
            
            self.logger.info(f"Human-like click with {pre_click_delay:.1f}s delay")
            return True
            
        except Exception as e:
            self.logger.error(f"Human-like click failed: {e}")
            return False

    async def randomized_solving_flow(self):
        """Randomized solving pattern with anti-bot timing"""
        if random.random() < 0.1:
            extra_delay = random.uniform(1.0, 2.0)
            self.logger.info(f"Slower response simulation: +{extra_delay:.1f}s")
            await asyncio.sleep(extra_delay)
        
        return await self.solve_symbol_game()

    # ==================== ULTIMATE LOGIN (PRESERVED) ====================
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
                self.send_telegram("✅ <b>ULTIMATE LOGIN SUCCESSFUL!</b>")
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

    async def save_cookies(self):
        """Save cookies to file"""
        try:
            if self.page and self.state['is_logged_in']:
                cookies = await self.page.context.cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f)
                self.logger.info("Cookies saved")
        except Exception as e:
            self.logger.warning(f"Could not save cookies: {e}")

    async def load_cookies(self):
        """Load cookies from file"""
        try:
            if os.path.exists(self.cookies_file) and self.page:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                await self.page.context.clear_cookies()
                await self.page.context.add_cookies(cookies)
                
                self.logger.info("Cookies loaded - session reused")
                return True
        except Exception as e:
            self.logger.warning(f"Could not load cookies: {e}")
        
        return False

    # ==================== GAME SOLVING (PRESERVED) ====================
    async def ensure_correct_page(self):
        """Ensure we're on the correct surf page"""
        if not self.is_browser_alive():
            self.logger.error("Browser dead during page check")
            return False
            
        try:
            current_url = self.page.url.lower()
            
            if "login" in current_url:
                self.logger.info("Auto-login: redirected to login")
                return await self.ultimate_login()
            
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

    async def solve_symbol_game(self):
        """Main game solving logic with credit tracking"""
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
                    
                    # Track credits earned (4 credits per game)
                    target_reached = self.update_credits_earned(4)
                    
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

    # ==================== ERROR HANDLING (PRESERVED) ====================
    def handle_consecutive_failures(self):
        """Handle consecutive failures"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.info(f"Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        if not self.is_browser_alive():
            return
        
        if current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.info("Refreshing page...")
            self.send_telegram(f"🔄 <b>Refreshing page</b> - {current_fails} failures")
            
            try:
                asyncio.create_task(self.page.reload())
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures! Stopping...")
            self.send_telegram("🚨 <b>CRITICAL ERROR</b>\nToo many failures - Stopping")
            self.stop()

    # ==================== MONITORING COMMANDS ====================
    async def extract_credits(self):
        """Extract credit balance"""
        if not self.is_browser_alive():
            return "BROWSER_DEAD"
        
        try:
            await self.page.reload()
            await asyncio.sleep(5)
            page_source = await self.page.content()
            
            credit_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*Credits',
                r'Credits.*?(\d{1,3}(?:,\d{3})*)',
                r'>\s*(\d[\d,]*)\s*Credits<',
            ]
            
            for pattern in credit_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    return f"{matches[0]} Credits"
            
            return "CREDITS_NOT_FOUND"
            
        except Exception as e:
            return f"ERROR: {str(e)}"

    def get_detailed_status(self):
        """Get detailed status including credit goals"""
        self.check_daily_reset()
        
        status = f"""
📊 <b>DETAILED STATUS</b>
⏰ Current Time: {self.get_ist_time().strftime('%I:%M %p IST')}
🔄 Solver Status: {self.state['status']}
🎯 Daily Target: {self.state['daily_target']} credits
💎 Earned Today: {self.state['credits_earned_today']} credits
📈 Progress: {(self.state['credits_earned_today']/self.state['daily_target']*100) if self.state['daily_target'] > 0 else 0:.1f}%
🎮 Games Solved: {self.state['total_solved']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
🖥️ Browser Health: {'✅' if self.is_browser_alive() else '❌'}
🔄 Browser Restarts: {self.state['browser_restarts']}
⏸️ Paused: {'✅' if self.state['is_paused'] else '❌'}
        """
        return status

    # ==================== MAIN SOLVER LOOP ====================
    async def solver_loop(self):
        """Main solving loop with credit goal tracking"""
        self.logger.info("Starting solver loop...")
        self.state['status'] = 'running'
        
        # Check daily reset at start
        self.check_daily_reset()
        
        if not await self.setup_playwright():
            self.logger.error("Cannot start - Playwright setup failed")
            self.stop()
            return
        
        if not await self.ultimate_login():
            self.logger.error("Cannot start - Login failed")
            self.stop()
            return
        
        consecutive_fails = 0
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                # Check if paused (target reached or manual pause)
                if self.state['is_paused']:
                    self.logger.info("Solver is paused, waiting...")
                    await asyncio.sleep(60)
                    continue
                
                # Check daily reset periodically
                if cycle_count % 10 == 0:
                    self.check_daily_reset()
                
                # Browser health check
                if cycle_count % 5 == 0 and not self.is_browser_alive():
                    self.logger.warning("Browser health check failed, restarting...")
                    if not await self.restart_browser():
                        self.logger.error("Browser restart failed, stopping...")
                        self.stop()
                        break
                
                if not self.is_browser_alive():
                    self.logger.error("Browser dead, stopping solver")
                    self.stop()
                    break
                
                # Refresh every 15 minutes
                if cycle_count % 30 == 0 and cycle_count > 0:
                    await self.page.reload()
                    self.logger.info("Page refreshed")
                    await asyncio.sleep(5)
                
                # Memory cleanup every 20 games
                if cycle_count % 20 == 0:
                    gc.collect()
                
                # Solve game with anti-bot timing
                game_solved = await self.randomized_solving_flow()
                
                if game_solved:
                    consecutive_fails = 0
                else:
                    consecutive_fails += 1
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                consecutive_fails += 1
                await asyncio.sleep(10)
        
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
        self.state['is_paused'] = False
        
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
        
        self.logger.info("CREDIT GOAL solver started successfully!")
        
        status_msg = "🚀 <b>CREDIT GOAL Solver Started!</b>"
        if self.state['daily_target'] > 0:
            status_msg += f"\n🎯 Target: {self.state['daily_target']} credits"
            status_msg += f"\n💎 Earned: {self.state['credits_earned_today']} credits"
        
        self.send_telegram(status_msg)
        return "✅ CREDIT GOAL solver started successfully!"

    def stop(self):
        """Stop the solver"""
        self.state['is_running'] = False
        self.state['monitoring_active'] = False
        self.state['status'] = 'stopped'
        
        async def close_playwright():
            try:
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
            except Exception as e:
                self.logger.warning(f"Playwright close warning: {e}")
        
        def run_cleanup():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(close_playwright())
                loop.close()
            except Exception as e:
                self.logger.warning(f"Cleanup warning: {e}")
        
        cleanup_thread = threading.Thread(target=run_cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        self.logger.info("CREDIT GOAL solver stopped")
        self.send_telegram("🛑 <b>CREDIT GOAL Solver Stopped!</b>")
        return "✅ CREDIT GOAL solver stopped successfully!"

    def status(self):
        """Get status"""
        return self.get_detailed_status()

# Telegram Bot
class TelegramBot:
    def __init__(self):
        self.solver = CreditGoalSolver()
        self.logger = logging.getLogger(__name__)
    
    def handle_updates(self):
        """Handle Telegram updates"""
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
        elif text.startswith('/target'):
            try:
                target = int(text.split()[1])
                if target > 0:
                    response = self.solver.set_daily_target(target)
                else:
                    response = "❌ Target must be greater than 0"
            except (IndexError, ValueError):
                response = "❌ Usage: /target 2000"
        elif text.startswith('/credits'):
            async def get_credits():
                return await self.solver.extract_credits()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                credits = loop.run_until_complete(get_credits())
                loop.close()
                response = f"💰 <b>Current Balance:</b> {credits}"
            except Exception as e:
                response = f"❌ Error getting credits: {e}"
        elif text.startswith('/screenshot'):
            async def take_screenshot():
                return await self.solver.send_screenshot("📸 Real-time Screenshot")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                screenshot_result = loop.run_until_complete(take_screenshot())
                loop.close()
                response = screenshot_result
            except Exception as e:
                response = f"❌ Screenshot error: {e}"
        elif text.startswith('/pause'):
            self.solver.state['is_paused'] = True
            response = "⏸️ <b>Solver Paused</b>\nUse /resume to continue"
        elif text.startswith('/resume'):
            self.solver.state['is_paused'] = False
            response = "▶️ <b>Solver Resumed</b>"
        elif text.startswith('/progress'):
            response = self.solver.get_progress_status()
        elif text.startswith('/help'):
            response = """
🤖 <b>AdShare CREDIT GOAL Solver Commands</b>

/start - Start solver
/stop - Stop solver  
/status - Detailed status
/target 2000 - Set daily credit goal
/progress - Credit progress
/credits - Check current balance
/screenshot - Real-time screenshot
/pause - Pause solver
/resume - Resume solver
/help - Show help

💡 <b>CREDIT GOAL FEATURES</b>
🎯 Set daily credit targets
⏰ IST timezone (5:30 AM reset)
📊 Progress tracking
🛡️ All anti-bot features
🔐 Ultimate login system
🚀 Auto-stop at target
            """
        
        if response:
            self.solver.send_telegram(response)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.logger.info("AdShare CREDIT GOAL Solver started!")
    bot.handle_updates()
