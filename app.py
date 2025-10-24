#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - ULTRA DEBUG Edition
MAXIMUM LOGGING + MULTIPLE LOGIN METHODS + SCREENSHOTS
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

class UltraDebugSymbolGameSolver:
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
        """Setup detailed logging"""
        logging.basicConfig(
            level=logging.DEBUG,  # CHANGED TO DEBUG FOR MAXIMUM INFO
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        """Setup Telegram bot"""
        try:
            self.logger.info("🔧 Setting up Telegram bot...")
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.telegram_chat_id = updates['result'][-1]['message']['chat']['id']
                    self.logger.info(f"📱 Telegram Chat ID: {self.telegram_chat_id}")
                    self.send_telegram("🤖 <b>AdShare ULTRA DEBUG Solver Started!</b>")
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

    async def send_screenshot(self, caption="🖥️ Screenshot"):
        """Send screenshot to Telegram with detailed logging"""
        if not self.page or not self.telegram_chat_id:
            self.logger.error("❌ Cannot take screenshot - browser or telegram not ready")
            return "❌ Browser not running or Telegram not configured"
        
        try:
            screenshot_path = "/tmp/screenshot.png"
            self.logger.debug(f"📸 Taking screenshot: {caption}")
            await self.page.screenshot(path=screenshot_path, full_page=True)
            self.logger.debug("📸 Screenshot taken, sending to Telegram...")
            
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
            
            result = "✅ Screenshot sent!" if response.status_code == 200 else f"❌ Failed: {response.status_code}"
            self.logger.debug(f"📸 Screenshot result: {result}")
            return result
                
        except Exception as e:
            error_msg = f"❌ Screenshot error: {str(e)}"
            self.logger.error(error_msg)
            return error_msg

    # ==================== PLAYWRIGHT SETUP ====================
    async def setup_playwright(self):
        """Setup Playwright with maximum logging"""
        self.logger.info("🔧 Setting up Playwright...")
        
        try:
            self.playwright = await async_playwright().start()
            self.logger.debug("🎭 Playwright started")
            
            # Launch Firefox with detailed logging
            self.browser = await self.playwright.firefox.launch(
                headless=True,
                args=[
                    '--headless',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )
            self.logger.debug("🦊 Firefox browser launched")
            
            # Create context
            context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
            )
            self.logger.debug("📄 Browser context created")
            
            self.page = await context.new_page()
            self.logger.debug("📝 New page created")
            
            # Set timeouts
            self.page.set_default_timeout(45000)
            self.page.set_default_navigation_timeout(60000)
            self.logger.debug("⏰ Timeouts set")
            
            self.logger.info("✅ Playwright started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Playwright setup failed: {e}")
            return False

    async def smart_delay_async(self, reason=""):
        """Async version of smart delay with logging"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        
        self.logger.debug(f"⏳ Delaying {delay:.2f}s: {reason}")
        await asyncio.sleep(delay)
        return delay

    # ==================== ULTRA DEBUG LOGIN METHODS ====================
    async def debug_page_analysis(self, step_name):
        """Analyze current page and log everything"""
        self.logger.debug(f"🔍 {step_name} - Analyzing page...")
        
        try:
            current_url = self.page.url
            page_title = await self.page.title()
            self.logger.debug(f"🌐 URL: {current_url}")
            self.logger.debug(f"📄 Title: {page_title}")
            
            # Count various elements
            forms = await self.page.query_selector_all("form")
            inputs = await self.page.query_selector_all("input")
            buttons = await self.page.query_selector_all("button")
            
            self.logger.debug(f"📝 Forms: {len(forms)}, Inputs: {len(inputs)}, Buttons: {len(buttons)}")
            
            # Log all input fields
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute("type")
                input_name = await input_elem.get_attribute("name")
                input_placeholder = await input_elem.get_attribute("placeholder")
                self.logger.debug(f"  Input {i}: type={input_type}, name={input_name}, placeholder={input_placeholder}")
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Page analysis failed: {e}")
            return False

    async def ultra_debug_login(self):
        """ULTRA DEBUG login with maximum logging and multiple methods"""
        try:
            self.logger.info("🚀 STARTING ULTRA DEBUG LOGIN...")
            await self.send_screenshot("🚀 STARTING LOGIN - Initial Page")
            
            login_url = "https://adsha.re/login"
            self.logger.debug(f"🧭 Navigating to: {login_url}")
            await self.page.goto(login_url, wait_until='networkidle')
            await self.page.wait_for_selector("body")
            
            await self.smart_delay_async("After page load")
            await self.debug_page_analysis("After navigation")
            await self.send_screenshot("📄 Login Page Loaded")
            
            # ==================== STEP 1: FORM ANALYSIS ====================
            self.logger.info("🔍 STEP 1: Analyzing login form...")
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Find ALL forms for debugging
            all_forms = soup.find_all('form')
            self.logger.debug(f"📝 Found {len(all_forms)} forms total")
            
            for i, form in enumerate(all_forms):
                form_name = form.get('name', 'no-name')
                form_action = form.get('action', 'no-action')
                form_method = form.get('method', 'no-method')
                self.logger.debug(f"  Form {i}: name='{form_name}', action='{form_action}', method='{form_method}'")
            
            # Target the specific login form
            form = soup.find('form', {'name': 'login'})
            if not form:
                self.logger.error("❌ No login form found with name='login'")
                await self.send_screenshot("❌ NO LOGIN FORM FOUND")
                return False
            
            self.logger.info("✅ Found login form!")
            
            # ==================== STEP 2: PASSWORD FIELD DISCOVERY ====================
            self.logger.info("🔍 STEP 2: Discovering password field...")
            password_field_name = None
            
            for field in form.find_all('input'):
                field_name = field.get('name', '')
                field_type = field.get('type', '')
                field_value = field.get('value', '')
                field_placeholder = field.get('placeholder', '')
                
                self.logger.debug(f"  Input field: name='{field_name}', type='{field_type}', value='{field_value}', placeholder='{field_placeholder}'")
                
                if field_value == 'Password' and field_name != 'mail' and field_name:
                    password_field_name = field_name
                    self.logger.info(f"🎯 FOUND PASSWORD FIELD: name='{password_field_name}'")
                    break
            
            if not password_field_name:
                self.logger.error("❌ No password field found with value='Password'")
                # Try alternative discovery methods
                password_fields = form.find_all('input', {'type': 'password'})
                if password_fields:
                    password_field_name = password_fields[0].get('name')
                    self.logger.info(f"🎯 Found password field by type: name='{password_field_name}'")
                else:
                    self.logger.error("❌ No password field found by any method")
                    await self.send_screenshot("❌ NO PASSWORD FIELD FOUND")
                    return False
            
            # ==================== STEP 3: FILL EMAIL - MULTIPLE METHODS ====================
            self.logger.info("📧 STEP 3: Filling email...")
            await self.send_screenshot("📧 BEFORE FILLING EMAIL")
            
            email_selectors = [
                "input[name='mail']",
                "input[type='email']", 
                "input[placeholder*='email' i]",
                "input[placeholder*='Email' i]",
                "input[name*='mail' i]",
                "input[name*='email' i]"
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    self.logger.debug(f"  Trying email selector: {selector}")
                    if await self.page.is_visible(selector):
                        self.logger.debug(f"  ✅ Selector visible: {selector}")
                        await self.page.fill(selector, "")
                        await self.page.fill(selector, CONFIG['email'])
                        self.logger.info(f"✅ EMAIL FILLED with selector: {selector}")
                        await self.send_screenshot(f"✅ EMAIL FILLED - {selector}")
                        email_filled = True
                        break
                    else:
                        self.logger.debug(f"  ❌ Selector not visible: {selector}")
                except Exception as e:
                    self.logger.debug(f"  ❌ Email selector failed {selector}: {e}")
            
            if not email_filled:
                self.logger.error("❌ All email filling methods failed")
                await self.send_screenshot("❌ EMAIL FILLING FAILED")
                return False
            
            await self.smart_delay_async("After email fill")
            
            # ==================== STEP 4: FILL PASSWORD - MULTIPLE METHODS ====================
            self.logger.info("🔑 STEP 4: Filling password...")
            await self.send_screenshot("🔑 BEFORE FILLING PASSWORD")
            
            password_selectors = [
                f"input[name='{password_field_name}']",
                "input[type='password']",
                "input[placeholder*='password' i]",
                "input[placeholder*='Password' i]"
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    self.logger.debug(f"  Trying password selector: {selector}")
                    if await self.page.is_visible(selector):
                        self.logger.debug(f"  ✅ Selector visible: {selector}")
                        await self.page.fill(selector, "")
                        await self.page.fill(selector, CONFIG['password'])
                        self.logger.info(f"✅ PASSWORD FILLED with selector: {selector}")
                        await self.send_screenshot(f"✅ PASSWORD FILLED - {selector}")
                        password_filled = True
                        break
                    else:
                        self.logger.debug(f"  ❌ Selector not visible: {selector}")
                except Exception as e:
                    self.logger.debug(f"  ❌ Password selector failed {selector}: {e}")
            
            if not password_filled:
                self.logger.error("❌ All password filling methods failed")
                await self.send_screenshot("❌ PASSWORD FILLING FAILED")
                return False
            
            await self.smart_delay_async("After password fill")
            
            # ==================== STEP 5: CLICK LOGIN - MULTIPLE METHODS ====================
            self.logger.info("🖱️ STEP 5: Clicking login...")
            await self.send_screenshot("🖱️ BEFORE CLICKING LOGIN")
            
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']", 
                "button",
                "input[value*='Login' i]",
                "input[value*='Sign' i]",
                "button:has-text('Login')",
                "button:has-text('Sign')",
                "input[value*='Log']",
                "input[value*='login']"
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    self.logger.debug(f"  Trying login selector: {selector}")
                    if await self.page.is_visible(selector):
                        self.logger.debug(f"  ✅ Selector visible: {selector}")
                        await self.page.click(selector)
                        self.logger.info(f"✅ LOGIN CLICKED with selector: {selector}")
                        await self.send_screenshot(f"✅ LOGIN CLICKED - {selector}")
                        login_clicked = True
                        break
                    else:
                        self.logger.debug(f"  ❌ Selector not visible: {selector}")
                except Exception as e:
                    self.logger.debug(f"  ❌ Login selector failed {selector}: {e}")
            
            # ==================== STEP 6: FORM SUBMISSION FALLBACKS ====================
            if not login_clicked:
                self.logger.warning("⚠️ No login button found, trying form submission...")
                
                # Method 1: JavaScript form submission
                try:
                    self.logger.debug("  Trying JavaScript form submission...")
                    await self.page.evaluate("""() => {
                        const form = document.querySelector("form[name='login']");
                        if (form) {
                            console.log("Submitting form via JS");
                            form.submit();
                            return true;
                        }
                        return false;
                    }""")
                    self.logger.info("✅ Form submitted via JavaScript")
                    await self.send_screenshot("✅ FORM SUBMITTED VIA JAVASCRIPT")
                    login_clicked = True
                except Exception as e:
                    self.logger.debug(f"  ❌ JavaScript submission failed: {e}")
                
                # Method 2: Press Enter in password field
                if not login_clicked:
                    try:
                        self.logger.debug("  Trying Enter key press...")
                        password_selector = f"input[name='{password_field_name}']"
                        await self.page.click(password_selector)
                        await self.page.keyboard.press('Enter')
                        self.logger.info("✅ Enter key pressed in password field")
                        await self.send_screenshot("✅ ENTER KEY PRESSED")
                        login_clicked = True
                    except Exception as e:
                        self.logger.debug(f"  ❌ Enter key press failed: {e}")
            
            if not login_clicked:
                self.logger.error("❌ All login methods failed")
                await self.send_screenshot("❌ ALL LOGIN METHODS FAILED")
                return False
            
            # ==================== STEP 7: WAIT FOR LOGIN RESULT ====================
            self.logger.info("⏳ STEP 7: Waiting for login result...")
            await self.smart_delay_async("Initial wait after login")
            await asyncio.sleep(8)  # Extended wait
            
            await self.send_screenshot("🔄 AFTER LOGIN ATTEMPT")
            await self.debug_page_analysis("After login attempt")
            
            # ==================== STEP 8: VERIFY LOGIN SUCCESS ====================
            self.logger.info("✅ STEP 8: Verifying login...")
            await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
            await self.smart_delay_async("After navigation to surf")
            
            current_url = self.page.url.lower()
            page_title = await self.page.title()
            self.logger.info(f"🌐 Final URL: {current_url}")
            self.logger.info(f"📄 Final Title: {page_title}")
            
            await self.send_screenshot("🎯 FINAL LOGIN RESULT")
            await self.debug_page_analysis("Final verification")
            
            if "surf" in current_url or "dashboard" in current_url:
                self.logger.info("🎉 LOGIN SUCCESSFUL!")
                self.state['is_logged_in'] = True
                await self.save_cookies()
                self.send_telegram("✅ <b>ULTRA DEBUG LOGIN SUCCESSFUL!</b>")
                return True
            else:
                if "login" in current_url:
                    self.logger.error("❌ LOGIN FAILED - Still on login page")
                    await self.send_screenshot("❌ LOGIN FAILED - STILL ON LOGIN PAGE")
                    
                    # Additional debug: check for error messages
                    error_selectors = [".error", ".alert", "[class*='error']", "[class*='alert']"]
                    for selector in error_selectors:
                        errors = await self.page.query_selector_all(selector)
                        if errors:
                            for error in errors:
                                error_text = await error.text_content()
                                self.logger.error(f"❌ Error message: {error_text}")
                    
                    return False
                else:
                    self.logger.warning("⚠️ Unexpected page after login, but might be successful")
                    self.state['is_logged_in'] = True
                    return True
                
        except Exception as e:
            self.logger.error(f"❌ ULTRA DEBUG LOGIN ERROR: {e}")
            await self.send_screenshot("💥 LOGIN CRASHED WITH ERROR")
            return False

    async def save_cookies(self):
        """Save cookies to file"""
        try:
            if self.page and self.state['is_logged_in']:
                cookies = await self.page.context.cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f)
                self.logger.info(f"🍪 Saved {len(cookies)} cookies")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save cookies: {e}")

    # ==================== SIMPLIFIED GAME SOLVING ====================
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
            self.logger.error("❌ Browser dead during page check")
            return False
            
        try:
            current_url = self.page.url.lower()
            
            if "login" in current_url:
                self.logger.info("🔄 Auto-login: redirected to login")
                return await self.ultra_debug_login()
            
            if "surf" not in current_url and "adsha.re" in current_url:
                self.logger.info("🔄 Redirecting to surf page...")
                await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
                await self.smart_delay_async("After navigation to surf")
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Page navigation error: {e}")
            return False

    async def solve_symbol_game(self):
        """Simple game solving for now - focus on login first"""
        if not self.state['is_running']:
            return False
        
        try:
            if not await self.ensure_correct_page():
                return False
            
            self.logger.info("🎮 Attempting to solve symbol game...")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Game solving error: {e}")
            return False

    # ==================== CONTROL METHODS ====================
    def start(self):
        """Start the solver"""
        if self.state['is_running']:
            return "❌ Solver already running"
        
        self.state['is_running'] = True
        
        # Create and set main event loop
        self.main_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.main_loop)
        
        def run_solver():
            try:
                self.main_loop.run_until_complete(self.solver_loop())
            except Exception as e:
                self.logger.error(f"❌ Solver loop error: {e}")
        
        self.solver_thread = threading.Thread(target=run_solver)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        self.logger.info("🚀 ULTRA DEBUG solver started!")
        return "🚀 ULTRA DEBUG solver started successfully!"

    async def solver_loop(self):
        """Main solving loop"""
        self.logger.info("🔄 Starting solver loop...")
        
        if not await self.setup_playwright():
            self.logger.error("❌ Cannot start - Playwright setup failed")
            self.stop()
            return
        
        if not await self.ultra_debug_login():
            self.logger.error("❌ Cannot start - Login failed")
            self.stop()
            return
        
        self.logger.info("🎉 Ready to solve games!")
        # Game solving logic would go here...

    def stop(self):
        """Stop the solver"""
        self.state['is_running'] = False
        self.logger.info("🛑 ULTRA DEBUG solver stopped")

    def status(self):
        """Get status"""
        return f"""
📊 <b>ULTRA DEBUG Status</b>
⏰ {time.strftime('%H:%M:%S')}
🔄 Status: {self.state['status']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
        """

# Telegram Bot
class TelegramBot:
    def __init__(self):
        self.solver = UltraDebugSymbolGameSolver()
        self.logger = logging.getLogger(__name__)
    
    def handle_updates(self):
        """Handle Telegram updates"""
        while True:
            try:
                url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
                response = requests.get(url, timeout=35)
                
                if response.status_code == 200:
                    updates = response.json()
                    if updates['result']:
                        for update in updates['result']:
                            self.process_message(update)
                
                time.sleep(5)
            except Exception as e:
                self.logger.error(f"❌ Telegram error: {e}")
                time.sleep(5)
    
    def process_message(self, update):
        """Process Telegram message"""
        if 'message' not in update or 'text' not in update['message']:
            return
        
        text = update['message']['text']
        
        if not self.solver.telegram_chat_id:
            self.solver.telegram_chat_id = update['message']['chat']['id']
        
        response = ""
        
        if text.startswith('/start'):
            response = self.solver.start()
        elif text.startswith('/stop'):
            response = self.solver.stop()
        elif text.startswith('/status'):
            response = self.solver.status()
        elif text.startswith('/debug_login'):
            async def debug_login():
                return await self.solver.ultra_debug_login()
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(debug_login())
                loop.close()
                response = "✅ Debug login completed!" if result else "❌ Debug login failed!"
            except Exception as e:
                response = f"❌ Debug login error: {e}"
        elif text.startswith('/screenshot'):
            async def take_screenshot():
                return await self.solver.send_screenshot("📸 Manual Screenshot")
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(take_screenshot())
                loop.close()
                response = result
            except Exception as e:
                response = f"❌ Screenshot error: {e}"
        
        if response:
            self.solver.send_telegram(response)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.logger.info("🎯 AdShare ULTRA DEBUG Solver started!")
    bot.handle_updates()
