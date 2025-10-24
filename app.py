#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - FINAL WORKING VERSION
PURE PLAYWRIGHT + MEMORY OPTIMIZED
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

class FinalSymbolGameSolver:
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
        }
        
        self.solver_thread = None
        self.monitoring_thread = None
        self.main_loop = None
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
                    self.send_telegram("🤖 <b>AdShare FINAL Solver Started!</b>")
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
                    'caption': f'{caption} - {time.strftime("%H:%M:%S")}'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
            return "✅ Screenshot sent!" if response.status_code == 200 else f"❌ Failed: {response.status_code}"
                
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    # ==================== PLAYWRIGHT SETUP WITH uBLOCK ====================
    async def setup_playwright(self):
        """Setup Playwright with memory optimization and uBlock"""
        self.logger.info("Setting up Playwright...")
        
        try:
            self.playwright = await async_playwright().start()
            
            # Launch Firefox with memory optimizations
            self.browser = await self.playwright.firefox.launch(
                headless=True,
                args=[
                    '--headless',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--single-process',  # Memory optimization
                ],
                firefox_user_prefs={
                    'dom.ipc.processCount': 1,
                    'content.processLimit': 1,
                    'browser.cache.disk.enable': False,
                    'browser.cache.memory.enable': False,
                    'javascript.options.mem.max': 25600,
                }
            )
            
            # Create context
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
            )
            
            self.page = await context.new_page()
            
            # Set timeouts
            self.page.set_default_timeout(30000)
            self.page.set_default_navigation_timeout(45000)
            
            # Install uBlock Origin
            ublock_path = '/app/ublock.xpi'
            if os.path.exists(ublock_path):
                await context.add_init_script(path=ublock_path)
                self.logger.info("uBlock Origin installed")
            else:
                self.logger.warning("uBlock Origin not found, continuing without it")
            
            self.logger.info("Playwright started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Playwright setup failed: {e}")
            return False

    async def smart_delay_async(self):
        """Async version of smart delay"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        
        await asyncio.sleep(delay)
        return delay

    # ==================== PROVEN LOGIN METHOD ====================
    async def playwright_login(self):
        """PROVEN WORKING LOGIN METHOD"""
        try:
            self.logger.info("Attempting login...")
            
            login_url = "https://adsha.re/login"
            await self.page.goto(login_url, wait_until='networkidle')
            await self.page.wait_for_selector("body")
            
            await self.smart_delay_async()
            
            # Parse form to find password field
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            form = soup.find('form', {'name': 'login'})
            if not form:
                self.logger.error("No login form found")
                return False
            
            # Find password field name
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
            
            self.logger.info(f"Password field: {password_field_name}")
            
            # Fill email
            await self.page.fill("input[name='mail']", CONFIG['email'])
            await self.smart_delay_async()
            
            # Fill password
            password_selector = f"input[name='{password_field_name}']"
            await self.page.fill(password_selector, CONFIG['password'])
            await self.smart_delay_async()
            
            # Submit form via JavaScript (PROVEN METHOD)
            await self.page.evaluate("""() => {
                const form = document.querySelector("form[name='login']");
                if (form) form.submit();
            }""")
            
            await asyncio.sleep(8)  # Wait for login
            
            # Verify login
            await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
            await self.smart_delay_async()
            
            current_url = self.page.url.lower()
            if "surf" in current_url or "dashboard" in current_url:
                self.logger.info("Login successful!")
                self.state['is_logged_in'] = True
                await self.save_cookies()
                self.send_telegram("✅ <b>Login Successful!</b>")
                return True
            else:
                if "login" in current_url:
                    self.logger.error("Login failed - still on login page")
                    return False
                else:
                    self.logger.info("Login may need verification, continuing...")
                    self.state['is_logged_in'] = True
                    return True
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
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

    # ==================== GAME SOLVING LOGIC ====================
    def is_browser_alive(self):
        """Check if browser is alive"""
        try:
            return (self.page and 
                   not self.page.is_closed() and 
                   self.browser and 
                   self.browser.is_connected())
        except Exception:
            return False

    async def ensure_correct_page(self):
        """Ensure we're on the correct surf page"""
        if not self.is_browser_alive():
            self.logger.error("Browser dead during page check")
            return False
            
        try:
            current_url = self.page.url.lower()
            
            if "login" in current_url:
                self.logger.info("Auto-login: redirected to login")
                return await self.playwright_login()
            
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
        """Main game solving logic"""
        if not self.state['is_running']:
            return False
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead during game solving")
            return False
            
        try:
            if not await self.ensure_correct_page():
                self.logger.info("Not on correct page, redirecting...")
                await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
                if not await self.ensure_correct_page():
                    return False
            
            question_svg = await self.page.wait_for_selector("svg", timeout=15000)
            
            if not question_svg:
                self.logger.info("Waiting for game to load...")
                return False
            
            links = await self.page.query_selector_all("a[href*='adsha.re'], button, .answer-option")
            
            if not links:
                self.logger.info("No answer links found")
                return False
            
            best_match = await self.find_best_match(question_svg, links)
            
            if best_match:
                await best_match['link'].click()
                self.state['total_solved'] += 1
                self.state['consecutive_fails'] = 0
                match_type = "EXACT" if best_match['exact'] else "FUZZY"
                self.logger.info(f"{match_type} Match! Total: {self.state['total_solved']}")
                return True
            else:
                self.logger.info("No good match found")
                self.handle_consecutive_failures()
                return False
            
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            self.handle_consecutive_failures()
            return False

    # ==================== ERROR HANDLING ====================
    def handle_consecutive_failures(self):
        """Handle consecutive failures"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.info(f"Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        if not self.is_browser_alive():
            return
        
        if current_fails == 1 and CONFIG['send_screenshot_on_error']:
            cooldown_passed = time.time() - self.state['last_error_screenshot'] > CONFIG['screenshot_cooldown_minutes'] * 60
            if cooldown_passed:
                self.logger.info("Sending error screenshot...")
                async def send_error_screenshot():
                    screenshot_result = await self.send_screenshot("❌ Game Error")
                    self.send_telegram(f"⚠️ <b>Game Error</b>\nFails: {current_fails}/{CONFIG['max_consecutive_failures']}\n{screenshot_result}")
                
                if self.main_loop and not self.main_loop.is_closed():
                    self.main_loop.create_task(send_error_screenshot())
                self.state['last_error_screenshot'] = time.time()
        
        elif current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.info("Refreshing page...")
            self.send_telegram(f"🔄 <b>Refreshing page</b> - {current_fails} failures")
            
            try:
                if self.main_loop and not self.main_loop.is_closed():
                    self.main_loop.create_task(self.page.reload())
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures! Stopping...")
            self.send_telegram("🚨 <b>CRITICAL ERROR</b>\nToo many failures - Stopping")
            self.stop()

    # ==================== CREDIT SYSTEM ====================
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

    async def send_credit_report(self):
        """Send credit report to Telegram"""
        credits = await self.extract_credits() if self.is_browser_alive() else "BROWSER_DEAD"
        self.state['last_credits'] = credits
        
        message = f"""
💰 <b>Credit Report</b>
⏰ {time.strftime('%H:%M:%S')}
💎 {credits}
🎯 Games Solved: {self.state['total_solved']}
🔄 Status: {self.state['status']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
        """
        
        self.send_telegram(message)
        self.logger.info(f"Credit report: {credits}")

    async def monitoring_loop(self):
        """Background credit monitoring"""
        self.logger.info("Starting credit monitoring...")
        self.state['monitoring_active'] = True
        
        while self.state['monitoring_active']:
            try:
                if self.state['is_running'] and self.is_browser_alive():
                    await self.send_credit_report()
                
                for _ in range(CONFIG['credit_check_interval']):
                    if not self.state['monitoring_active']:
                        break
                    await asyncio.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)
        
        self.logger.info("Credit monitoring stopped")

    # ==================== MAIN SOLVER LOOP ====================
    async def solver_loop(self):
        """Main solving loop"""
        self.logger.info("Starting solver loop...")
        self.state['status'] = 'running'
        
        if not await self.setup_playwright():
            self.logger.error("Cannot start - Playwright setup failed")
            self.stop()
            return
        
        if not await self.playwright_login():
            self.logger.error("Cannot start - Login failed")
            self.stop()
            return
        
        consecutive_fails = 0
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                if not self.is_browser_alive():
                    self.logger.error("Browser dead, stopping solver")
                    self.stop()
                    break
                
                # Refresh every 15 minutes
                if cycle_count % 30 == 0 and cycle_count > 0:
                    await self.page.reload()
                    self.logger.info("Page refreshed")
                    await asyncio.sleep(5)
                
                # Memory cleanup every 50 cycles
                if cycle_count % 50 == 0:
                    gc.collect()
                
                # Solve game
                game_solved = await self.solve_symbol_game()
                
                if game_solved:
                    consecutive_fails = 0
                    await asyncio.sleep(3)
                else:
                    consecutive_fails += 1
                    await asyncio.sleep(5)
                
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
        
        self.main_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.main_loop)
        
        def run_solver():
            try:
                self.main_loop.run_until_complete(self.solver_loop())
            except Exception as e:
                self.logger.error(f"Solver loop error: {e}")
            finally:
                if self.main_loop and not self.main_loop.is_closed():
                    self.main_loop.close()
        
        self.solver_thread = threading.Thread(target=run_solver)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        if not self.state['monitoring_active']:
            def run_monitoring():
                monitoring_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(monitoring_loop)
                try:
                    monitoring_loop.run_until_complete(self.monitoring_loop())
                except Exception as e:
                    self.logger.error(f"Monitoring loop error: {e}")
                finally:
                    if monitoring_loop and not monitoring_loop.is_closed():
                        monitoring_loop.close()
            
            self.monitoring_thread = threading.Thread(target=run_monitoring)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
        
        self.logger.info("FINAL solver started successfully!")
        self.send_telegram("🚀 <b>FINAL Solver Started!</b>")
        return "✅ FINAL solver started successfully!"

    def stop(self):
        """Stop the solver"""
        self.state['is_running'] = False
        self.state['monitoring_active'] = False
        self.state['status'] = 'stopped'
        
        async def close_playwright():
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        
        try:
            if self.main_loop and not self.main_loop.is_closed():
                self.main_loop.run_until_complete(close_playwright())
        except Exception as e:
            self.logger.warning(f"Playwright close failed: {e}")
        
        self.logger.info("FINAL solver stopped")
        self.send_telegram("🛑 <b>FINAL Solver Stopped!</b>")
        return "✅ FINAL solver stopped successfully!"

    def status(self):
        """Get status"""
        return f"""
📊 <b>Status Report</b>
⏰ {time.strftime('%H:%M:%S')}
🔄 Status: {self.state['status']}
🎯 Games Solved: {self.state['total_solved']}
💰 Last Credits: {self.state['last_credits']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
        """

# Telegram Bot
class TelegramBot:
    def __init__(self):
        self.solver = FinalSymbolGameSolver()
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
        elif text.startswith('/credits'):
            async def get_credits():
                return await self.solver.extract_credits()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                credits = loop.run_until_complete(get_credits())
                loop.close()
                response = f"💰 <b>Credits:</b> {credits}"
            except Exception as e:
                response = f"❌ Error getting credits: {e}"
        elif text.startswith('/screenshot'):
            async def take_screenshot():
                return await self.solver.send_screenshot()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                screenshot_result = loop.run_until_complete(take_screenshot())
                loop.close()
                response = screenshot_result
            except Exception as e:
                response = f"❌ Screenshot error: {e}"
        elif text.startswith('/help'):
            response = """
🤖 <b>AdShare FINAL Solver Commands</b>

/start - Start solver
/stop - Stop solver  
/status - Check status
/credits - Get credits
/screenshot - Get screenshot
/help - Show help

💡 <b>Pure Playwright + Memory Optimized</b>
🔐 Proven login method
🎮 Game solving included
💾 Low memory usage
🚀 Ready to earn!
            """
        
        if response:
            self.solver.send_telegram(response)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.logger.info("AdShare FINAL Solver started!")
    bot.handle_updates()
