#!/usr/bin/env python3
"""
AdShare ULTIMATE Bot - uBlock Origin Focus
✅ Ultimate Login ✅ Game Solving ✅ Anti-Bot ✅ Telegram Control
✅ Daily Reset/Restart ✅ uBlock with Fallbacks
"""

import os
import time
import random
import logging
import re
import requests
import threading
import asyncio
import datetime
import shutil
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
    'max_consecutive_failures': 10,
    'refresh_page_after_failures': 5,
    'send_screenshot_on_error': True,
    'screenshot_cooldown_minutes': 5,
    'daily_target': 3000,
    'reset_time_ist': "05:30",  # 5:30 AM IST
    'restart_time_range': ("06:00", "07:00"),  # Random restart between 6-7 AM
    'ublock_path': "/app/ublock.xpi",  # Path to uBlock Origin from Dockerfile
    'natural_failure_rate': 0.001,  # 0.1% failure rate
    'micro_break_range': (1, 3),
    'short_break_frequency': (30, 50),
    'short_break_duration': (30, 120),
    'meal_break_frequency': (200, 300),
    'meal_break_duration': (900, 1800),
    'long_break_chance': 0.02,
    'long_break_duration': (3600, 10800),
    'night_hours': [22, 23, 0, 1, 2, 3, 4, 5],
    'night_slowdown_factor': 0.4,
}

class UltimateAdshareBot:
    def __init__(self):
        self.playwright = None
        self.context = None
        self.page = None
        self.telegram_chat_id = None
        self.profile_dir = "/tmp/firefox_profile"
        self.ublock_method = "none"
        
        self.state = {
            'is_running': False,
            'is_paused': False,
            'total_solved': 0,
            'status': 'stopped',
            'is_logged_in': False,
            'consecutive_fails': 0,
            'last_error_screenshot': 0,
            'credits_earned_today': 0,
            'daily_target': CONFIG['daily_target'],
            'last_reset_date': datetime.date.today().isoformat(),
            'games_solved_today': 0,
            'start_time': time.time(),
            'next_restart_time': self.get_random_restart_time(),
            'browser_retries': 0,
            'max_browser_retries': 3,
        }
        
        self.setup_logging()
        self.setup_telegram()
    
    def get_random_restart_time(self):
        now_ist = datetime.datetime.now() + datetime.timedelta(hours=5, minutes=30)
        today = now_ist.date()
        restart_min, restart_max = CONFIG['restart_time_range']
        min_time = datetime.datetime.strptime(restart_min, "%H:%M").time()
        max_time = datetime.datetime.strptime(restart_max, "%H:%M").time()
        min_minutes = min_time.hour * 60 + min_time.minute
        max_minutes = max_time.hour * 60 + max_time.minute
        random_minutes = random.randint(min_minutes, max_minutes)
        random_hour = random_minutes // 60
        random_minute = random_minutes % 60
        random_time = datetime.datetime.combine(today, datetime.time(random_hour, random_minute))
        if random_time < now_ist:
            random_time += datetime.timedelta(days=1)
        return random_time

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
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
                    self.send_telegram("🤖 <b>AdShare ULTIMATE Bot Started!</b>")
                    return True
            else:
                self.logger.warning(f"Telegram setup failed: {response.status_code}")
            return False
        except Exception as e:
            self.logger.error(f"Telegram setup failed: {e}")
            return False
    
    def send_telegram(self, text, parse_mode='HTML'):
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

    async def send_screenshot(self, caption="🖥️ Screenshot"):
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
                    'caption': f'{caption} - {time.strftime("%H:%M:%S")}'
                }
                response = requests.post(url, files=files, data=data, timeout=30)
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            return "✅ Screenshot sent!" if response.status_code == 200 else f"❌ Failed: {response.status_code}"
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    async def setup_playwright(self):
        self.logger.info("Setting up Playwright with uBlock...")
        try:
            self.playwright = await async_playwright().start()
            profile_dir = self.profile_dir
            os.makedirs(profile_dir, exist_ok=True)
            
            # Primary: Install uBlock via profile
            ublock_xpi_path = CONFIG['ublock_path']
            if os.path.exists(ublock_xpi_path):
                extensions_dir = os.path.join(profile_dir, "extensions")
                os.makedirs(extensions_dir, exist_ok=True)
                ublock_dest = os.path.join(extensions_dir, "uBlock0@raymondhill.net.xpi")
                shutil.copy(ublock_xpi_path, ublock_dest)
                # Create user.js to force-enable extensions
                user_js_path = os.path.join(profile_dir, "user.js")
                with open(user_js_path, 'w') as f:
                    f.write("""
user_pref("extensions.autoDisableScopes", 0);
user_pref("extensions.enabledScopes", 15);
user_pref("xpinstall.signatures.required", false);
                    """)
                self.logger.info("uBlock Origin copied to Firefox profile with user.js")
                self.ublock_method = "primary"
            else:
                self.logger.warning("uBlock Origin .xpi not found, trying fallback...")
            
            # Fallback 1: JavaScript ad-blocker
            if self.ublock_method == "none":
                self.logger.info("Using JavaScript ad-blocker fallback")
                async def block_ads(route, request):
                    ad_domains = ['doubleclick.net', 'googlesyndication.com', 'adservice.google.com', 'adsbygoogle']
                    if any(domain in request.url for domain in ad_domains):
                        await route.abort()
                    else:
                        await route.continue_()
                self.ublock_method = "js_blocker"
            
            # Fallback 2: DOM-based ad hiding
            if self.ublock_method == "none":
                self.logger.info("Using DOM-based ad hiding fallback")
                self.ublock_method = "dom_hiding"
            
            launch_args = ['--headless=new']
            context_options = {
                'viewport': {'width': 1280, 'height': 720},
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
                'java_script_enabled': True,
                'bypass_csp': True
            }
            
            self.context = await self.playwright.firefox.launch_persistent_context(
                user_data_dir=profile_dir,
                headless=True,
                args=launch_args,
                timeout=60000,
                **context_options
            )
            
            self.page = await self.context.new_page()
            self.page.set_default_timeout(20000)
            self.page.set_default_navigation_timeout(60000)
            
            # Apply JS blocker if needed
            if self.ublock_method == "js_blocker":
                await self.page.route("**/*", block_ads)
            
            # Apply DOM hiding if needed
            if self.ublock_method == "dom_hiding":
                await self.page.evaluate("""
                    () => {
                        const adSelectors = [
                            '.adsbygoogle',
                            '.banner',
                            '.video-ads',
                            '.ytp-ad-overlay-container',
                            '[id*="ad-"]',
                            '[class*="ad-"]'
                        ];
                        const observer = new MutationObserver(() => {
                            adSelectors.forEach(selector => {
                                document.querySelectorAll(selector).forEach(el => {
                                    el.style.display = 'none';
                                    el.remove();
                                });
                            });
                        });
                        observer.observe(document.body, { childList: true, subtree: true });
                    }
                """)
            
            self.logger.info(f"Playwright started successfully with uBlock method: {self.ublock_method}")
            return True
        except Exception as e:
            self.logger.error(f"Playwright setup failed: {e}")
            self.ublock_method = "none"
            return False

    async def smart_delay_async(self, min_delay=None, max_delay=None):
        if min_delay is None:
            min_delay = CONFIG['min_delay']
        if max_delay is None:
            max_delay = CONFIG['max_delay']
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
        return delay

    async def take_short_break(self):
        break_duration = random.randint(*CONFIG['short_break_duration'])
        self.logger.info(f"☕ Taking short break: {break_duration}s")
        self.send_telegram(f"☕ <b>Short Break</b>\n⏰ {break_duration} seconds")
        await asyncio.sleep(break_duration)

    async def take_meal_break(self):
        break_duration = random.randint(*CONFIG['meal_break_duration'])
        minutes = break_duration // 60
        self.logger.info(f"🍔 Taking meal break: {minutes}min")
        self.send_telegram(f"🍔 <b>Meal Break</b>\n⏰ {minutes} minutes")
        await asyncio.sleep(break_duration)

    async def take_long_break(self):
        break_duration = random.randint(*CONFIG['long_break_duration'])
        hours = break_duration // 3600
        self.logger.info(f"🌙 Taking long break: {hours}h")
        self.send_telegram(f"🌙 <b>Long Break</b>\n⏰ {hours} hours")
        await asyncio.sleep(break_duration)

    def is_night_time(self):
        now_ist = datetime.datetime.now() + datetime.timedelta(hours=5, minutes=30)
        return now_ist.hour in CONFIG['night_hours']

    def should_restart_now(self):
        now_ist = datetime.datetime.now() + datetime.timedelta(hours=5, minutes=30)
        return now_ist >= self.state['next_restart_time']

    def pause(self):
        if not self.state['is_running']:
            return "❌ Solver is not running"
        if self.state['is_paused']:
            return "⏸️ Solver is already paused"
        self.state['is_paused'] = True
        self.state['status'] = 'paused'
        self.logger.info("Solver paused")
        self.send_telegram("⏸️ <b>Solver Paused</b>")
        return "✅ Solver paused successfully!"

    def resume(self):
        if not self.state['is_running']:
            return "❌ Solver is not running"
        if not self.state['is_paused']:
            return "▶️ Solver is already running"
        self.state['is_paused'] = False
        self.state['status'] = 'running'
        self.logger.info("Solver resumed")
        self.send_telegram("▶️ <b>Solver Resumed</b>")
        return "✅ Solver resumed successfully!"

    async def ultimate_login(self):
        try:
            self.logger.info("🚀 STARTING ULTIMATE LOGIN (12+ METHODS)...")
            await self.page.goto("https://adsha.re/login", wait_until='networkidle', timeout=60000)
            await self.page.wait_for_selector("body", timeout=20000)
            await self.smart_delay_async()
            
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            all_forms = soup.find_all('form')
            self.logger.info(f"Found {len(all_forms)} forms")
            
            form = soup.find('form', {'name': 'login'})
            if not form:
                self.logger.warning("No login form found by name, trying first form")
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
            
            self.logger.info("Filling email (8 methods)...")
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
            
            self.logger.info("Filling password (6 methods)...")
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
            
            self.logger.info("Submitting form (12+ methods)...")
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
                "form input[type='submit']",
                "button[class*='login']",
                "button[class*='submit']"
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
            
            await self.page.goto("https://adsha.re/surf", wait_until='networkidle', timeout=60000)
            await self.smart_delay_async()
            
            final_url = self.page.url.lower()
            self.logger.info(f"Final URL: {final_url}")
            
            if "surf" in final_url or "dashboard" in final_url:
                self.logger.info("🎉 LOGIN SUCCESSFUL!")
                self.state['is_logged_in'] = True
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

    async def check_daily_reset(self):
        try:
            now_ist = datetime.datetime.now() + datetime.timedelta(hours=5, minutes=30)
            current_date = now_ist.date().isoformat()
            if current_date != self.state['last_reset_date']:
                reset_time = datetime.datetime.strptime(CONFIG['reset_time_ist'], "%H:%M").time()
                current_time = now_ist.time()
                if current_time >= reset_time:
                    old_credits = self.state['credits_earned_today']
                    self.state['credits_earned_today'] = 0
                    self.state['games_solved_today'] = 0
                    self.state['last_reset_date'] = current_date
                    self.state['next_restart_time'] = self.get_random_restart_time()
                    self.logger.info(f"💰 Daily reset completed! Previous: {old_credits}, New target: {self.state['daily_target']}")
                    self.send_telegram(f"🌅 <b>Daily Reset Complete!</b>\n🎯 New target: {self.state['daily_target']} credits\n💰 Yesterday: {old_credits} credits")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Reset check error: {e}")
            return False

    def is_browser_alive(self):
        try:
            return self.page and not self.page.is_closed()
        except Exception:
            return False

    async def ensure_correct_page(self):
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
                await self.page.evaluate("window.close()")  # Close any popups
                await self.page.goto("https://adsha.re/surf", wait_until='networkidle', timeout=60000)
                await self.smart_delay_async()
                return True
            await self.page.evaluate("window.close()")  # Close any popups
            return True
        except Exception as e:
            self.logger.error(f"Page navigation error: {e}")
            return False

    def calculate_similarity(self, str1, str2):
        if len(str1) == 0 or len(str2) == 0:
            return 0.0
        common_chars = sum(1 for a, b in zip(str1, str2) if a == b)
        max_len = max(len(str1), len(str2))
        return common_chars / max_len if max_len > 0 else 0.0

    async def compare_symbols(self, question_svg, answer_svg):
        try:
            question_content = await question_svg.inner_html()
            answer_content = await answer_svg.inner_html()
            if not question_content or not answer_content:
                return {'match': False, 'confidence': 0.0, 'exact': False}
            if random.random() < CONFIG['natural_failure_rate']:
                self.logger.info("🤖 0.1% intentional human-like failure")
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
        if not self.state['is_running'] or self.state['is_paused']:
            return False
        if not self.is_browser_alive():
            self.logger.error("Browser dead during game solving")
            return False
        try:
            await self.page.evaluate("window.close()")  # Close any popups
            if not await self.ensure_correct_page():
                self.logger.info("Not on correct page, redirecting...")
                await self.page.goto("https://adsha.re/surf", wait_until='networkidle', timeout=60000)
                if not await self.ensure_correct_page():
                    return False
            question_svg = await self.page.wait_for_selector("svg", timeout=20000)
            if not question_svg:
                self.logger.info("Waiting for game to load...")
                return False
            links = await self.page.query_selector_all("a[href*='adsha.re'], button, .answer-option")
            if not links:
                self.logger.info("No answer links found")
                return False
            best_match = await self.find_best_match(question_svg, links)
            if best_match:
                if random.random() < 0.15:  # 15% chance to hesitate
                    hesitation = random.uniform(0.5, 2.0)
                    await asyncio.sleep(hesitation)
                await best_match['link'].click()
                self.state['total_solved'] += 1
                self.state['credits_earned_today'] += 1
                self.state['games_solved_today'] += 1
                self.state['consecutive_fails'] = 0
                match_type = "EXACT" if best_match['exact'] else "FUZZY"
                self.logger.info(f"{match_type} Match! Total: {self.state['total_solved']}")
                if self.state['credits_earned_today'] >= self.state['daily_target']:
                    self.logger.info(f"🎯 Daily target reached! {self.state['credits_earned_today']}/{self.state['daily_target']}")
                    self.send_telegram(f"🎯 <b>Daily Target Reached!</b>\n💰 {self.state['credits_earned_today']}/{self.state['daily_target']} credits")
                return True
            else:
                self.logger.info("No good match found")
                self.handle_consecutive_failures()
                return False
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            self.handle_consecutive_failures()
            return False

    def handle_consecutive_failures(self):
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        self.logger.info(f"Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        if not self.is_browser_alive():
            return
        if current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.info("Refreshing page...")
            self.send_telegram(f"🔄 <b>Refreshing page</b> - {current_fails} failures")
            try:
                asyncio.create_task(self.page.reload(timeout=60000))
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures! Stopping...")
            self.send_telegram("🚨 <b>CRITICAL ERROR</b>\nToo many failures - Stopping")
            self.stop()

    async def solver_loop(self):
        self.logger.info("Starting solver loop...")
        self.state['status'] = 'running'
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                if not self.is_browser_alive():
                    self.state['browser_retries'] += 1
                    if self.state['browser_retries'] > self.state['max_browser_retries']:
                        self.logger.error("Max browser retries reached, stopping...")
                        self.send_telegram("🚨 <b>CRITICAL ERROR</b>\nMax browser retries reached")
                        self.stop()
                        break
                    self.logger.info(f"Browser dead, retrying ({self.state['browser_retries']}/{self.state['max_browser_retries']})...")
                    await self.cleanup_playwright()
                    if not await self.setup_playwright():
                        self.logger.error("Cannot restart - Playwright setup failed")
                        self.stop()
                        break
                    if not await self.ultimate_login():
                        self.logger.error("Cannot restart - Login failed")
                        self.stop()
                        break
                    self.state['browser_retries'] = 0
                    continue
                
                if self.state['is_paused']:
                    await asyncio.sleep(10)
                    continue
                
                if self.should_restart_now():
                    self.logger.info("🔄 Scheduled restart time reached! Restarting...")
                    self.send_telegram("🔄 <b>Scheduled Restart</b>\n⏰ Restarting bot as scheduled")
                    await self.perform_restart()
                    continue
                
                await self.check_daily_reset()
                
                if self.state['games_solved_today'] > 0:
                    if self.state['games_solved_today'] % random.randint(*CONFIG['short_break_frequency']) == 0:
                        await self.take_short_break()
                    if self.state['games_solved_today'] % random.randint(*CONFIG['meal_break_frequency']) == 0:
                        await self.take_meal_break()
                    if random.random() < CONFIG['long_break_chance']:
                        await self.take_long_break()
                
                if self.is_night_time():
                    night_delay = random.uniform(3, 8) * CONFIG['night_slowdown_factor']
                    await asyncio.sleep(night_delay)
                
                game_solved = await self.solve_symbol_game()
                if game_solved:
                    self.state['games_solved_today'] += 1
                    self.state['consecutive_fails'] = 0
                    await self.smart_delay_async()
                else:
                    self.state['consecutive_fails'] += 1
                    await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                self.state['consecutive_fails'] += 1
                await asyncio.sleep(10)
        
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures, stopping...")
            self.send_telegram("🚨 <b>CRITICAL ERROR</b>\nToo many failures - Stopping")
            self.stop()

    async def perform_restart(self):
        self.logger.info("Performing scheduled restart...")
        current_credits = self.state['credits_earned_today']
        current_target = self.state['daily_target']
        await self.cleanup_playwright()
        self.state['is_running'] = True
        self.state['is_paused'] = False
        self.state['consecutive_fails'] = 0
        self.state['browser_retries'] = 0
        self.state['credits_earned_today'] = current_credits
        self.state['daily_target'] = current_target
        self.state['next_restart_time'] = self.get_random_restart_time()
        await self.solver_loop()

    async def cleanup_playwright(self):
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
            self.page = None
            self.context = None
            self.playwright = None
            self.ublock_method = "none"
            self.logger.info("Playwright cleaned up successfully")
        except Exception as e:
            self.logger.warning(f"Playwright cleanup warning: {e}")

    def start(self):
        if self.state['is_running']:
            return "❌ Solver already running"
        self.state['is_running'] = True
        self.state['is_paused'] = False
        self.state['consecutive_fails'] = 0
        self.state['browser_retries'] = 0
        self.state['start_time'] = time.time()
        self.state['next_restart_time'] = self.get_random_restart_time()
        
        restart_time = self.state['next_restart_time'].strftime("%H:%M IST")
        self.logger.info(f"ULTIMATE solver started successfully! Next restart: {restart_time}")
        self.send_telegram(f"🚀 <b>ULTIMATE Solver Started!</b>\n⏰ Next restart: {restart_time}")
        return f"✅ ULTIMATE solver started successfully!\n⏰ Next restart: {restart_time}"

    def stop(self):
        self.state['is_running'] = False
        self.state['is_paused'] = False
        self.state['status'] = 'stopped'
        asyncio.run(self.cleanup_playwright())
        self.logger.info("ULTIMATE solver stopped")
        self.send_telegram("🛑 <b>ULTIMATE Solver Stopped!</b>")
        return "✅ ULTIMATE solver stopped successfully!"

    def status(self):
        now_ist = datetime.datetime.now() + datetime.timedelta(hours=5, minutes=30)
        reset_time = datetime.datetime.strptime(CONFIG['reset_time_ist'], "%H:%M").time()
        next_reset = datetime.datetime.combine(now_ist.date(), reset_time)
        if now_ist.time() > reset_time:
            next_reset += datetime.timedelta(days=1)
        time_until_reset = next_reset - now_ist
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes = remainder // 60
        runtime = time.time() - self.state['start_time']
        hours_running = max(1, runtime / 3600)
        hourly_rate = self.state['games_solved_today'] / hours_running
        next_restart = self.state['next_restart_time'].strftime("%H:%M IST")
        status_icon = "⏸️" if self.state['is_paused'] else "🔄"
        status_text = "paused" if self.state['is_paused'] else self.state['status']
        return f"""
📊 <b>Status Report</b>
⏰ {now_ist.strftime('%H:%M:%S IST')}
{status_icon} Status: {status_text}
🎯 Total Games: {self.state['total_solved']}
💰 Today's Credits: {self.state['credits_earned_today']}/{self.state['daily_target']}
📈 Hourly Rate: {hourly_rate:.1f} games/h
🌅 Next Reset: {next_reset.strftime('%Y-%m-%d %H:%M IST')}
⏳ Time Until Reset: {hours}h {minutes}m
🔄 Next Restart: {next_restart}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
🛡️ uBlock: {self.ublock_method}
        """

class TelegramBot:
    def __init__(self):
        self.solver = UltimateAdshareBot()
        self.logger = logging.getLogger(__name__)
        self.last_update_id = None
    
    def handle_updates(self):
        self.logger.info("Starting Telegram bot...")
        while True:
            try:
                url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
                params = {'timeout': 30}
                if self.last_update_id:
                    params['offset'] = self.last_update_id + 1
                response = requests.get(url, params=params, timeout=35)
                if response.status_code == 200:
                    updates = response.json()
                    if updates['result']:
                        for update in updates['result']:
                            self.last_update_id = update['update_id']
                            self.process_message(update)
                else:
                    self.logger.warning(f"Telegram API error: {response.status_code}")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Telegram error: {e}")
                time.sleep(5)
    
    def process_message(self, update):
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
        elif text.startswith('/pause'):
            response = self.solver.pause()
        elif text.startswith('/resume'):
            response = self.solver.resume()
        elif text.startswith('/status'):
            response = self.solver.status()
        elif text.startswith('/help'):
            response = """
🤖 <b>AdShare ULTIMATE Bot Commands</b>

/start - Start solver
/stop - Stop solver
/pause - Pause solver
/resume - Resume solver
/status - Check status
/screenshot - Take screenshot
/target [number] - Set daily target
/help - Show help

🎯 <b>Features</b>
🔐 12+ login methods
🛡️ uBlock Origin with fallbacks
🎯 Game solving with 99.9% success
📊 24/7 operation
⏰ Breaks (short, meal, long)
🌙 Night slowdown
🔄 Daily reset (5:30 AM IST)
🔄 Random restart (6-7 AM IST)
⏸️ Pause/Resume control
            """
        elif text.startswith('/screenshot'):
            response = asyncio.run(self.solver.send_screenshot())
        elif text.startswith('/target'):
            try:
                target = int(text.split()[1])
                self.solver.state['daily_target'] = target
                response = f"🎯 <b>Daily target set to:</b> {target} credits"
            except:
                response = "❌ Usage: /target 3000"
        if response:
            self.solver.send_telegram(response)

async def main():
    bot = TelegramBot()
    bot.logger.info("AdShare ULTIMATE Bot started!")
    # Run Telegram polling in a separate thread
    telegram_thread = threading.Thread(target=bot.handle_updates, daemon=True)
    telegram_thread.start()
    # Run solver in main thread
    await bot.solver.solver_loop()

if __name__ == '__main__':
    asyncio.run(main())
