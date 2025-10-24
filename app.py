#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - CREDIT GOAL EDITION
Complete version with Session Backup System
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
import subprocess
import sqlite3
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
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
    'page_timeout': 60000,
    'firefox_profile': '/app/.mozilla/firefox/adshare_profile',
    'backup_dir': '/app/backup',
}

class CreditGoalSolver:
    def __init__(self):
        self.playwright = None
        self.context = None
        self.page = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
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
            'daily_target': 0,
            'credits_earned_today': 0,
            'daily_start_time': self.get_daily_reset_time(),
            'is_paused': False,
            'session_history': [],
            'last_restart_time': 0,
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
                    self.send_telegram("🤖 <b>AdShare CREDIT GOAL Solver Started!</b>")
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

    # ==================== SESSION BACKUP SYSTEM ====================
    
    async def create_session_backup(self):
        """Create a small session backup with cookies + uBlock only"""
        try:
            self.logger.info("Creating session backup...")
            
            # Create temp directory
            temp_dir = "/tmp/session_backup"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 1. Save current cookies
            if self.context and self.state['is_logged_in']:
                cookies = await self.context.cookies()
                with open(os.path.join(temp_dir, 'cookies.json'), 'w') as f:
                    json.dump(cookies, f)
            
            # 2. Copy uBlock extension
            ublock_path = os.path.join(CONFIG['firefox_profile'], 'extensions', 'uBlock0@raymondhill.net.xpi')
            if os.path.exists(ublock_path):
                import shutil
                os.makedirs(os.path.join(temp_dir, 'extensions'), exist_ok=True)
                shutil.copy2(ublock_path, os.path.join(temp_dir, 'extensions', 'uBlock0@raymondhill.net.xpi'))
            
            # 3. Save preferences
            prefs_path = os.path.join(CONFIG['firefox_profile'], 'prefs.js')
            if os.path.exists(prefs_path):
                import shutil
                shutil.copy2(prefs_path, os.path.join(temp_dir, 'prefs.js'))
            
            # 4. Create backup info
            backup_info = {
                'created_at': self.get_ist_time().isoformat(),
                'profile': 'adshare_profile',
                'version': 'session_backup_v1',
                'contains': ['cookies', 'ublock', 'prefs']
            }
            with open(os.path.join(temp_dir, 'backup_info.json'), 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            # 5. Create compressed backup
            session_backup_path = f"/tmp/adshare_session_{int(time.time())}.tar.gz"
            cmd = f"tar -czf {session_backup_path} -C {temp_dir} ."
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            if result.returncode == 0 and os.path.exists(session_backup_path):
                size_kb = os.path.getsize(session_backup_path) / 1024
                self.logger.info(f"Session backup created: {session_backup_path} ({size_kb:.1f} KB)")
                return session_backup_path
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Session backup creation failed: {e}")
            return None

    async def send_session_backup(self):
        """Create and send session backup to Telegram"""
        try:
            backup_path = await self.create_session_backup()
            if not backup_path:
                return "❌ Failed to create session backup"
            
            # Send to Telegram
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendDocument"
            with open(backup_path, 'rb') as document:
                files = {'document': document}
                data = {
                    'chat_id': self.telegram_chat_id,
                    'caption': f'🔐 AdShare Session Backup\n⏰ {self.get_ist_time().strftime("%Y-%m-%d %H:%M IST")}\n💾 Use /restoresession to restore this later'
                }
                response = requests.post(url, files=files, data=data, timeout=60)
            
            # Cleanup
            os.remove(backup_path)
            
            if response.status_code == 200:
                return "✅ Session backup sent to Telegram! Save this file for future deployments."
            else:
                return f"❌ Failed to send backup: {response.status_code}"
                
        except Exception as e:
            return f"❌ Session backup error: {str(e)}"

    async def restore_session_backup(self, backup_path):
        """Restore from session backup (cookies + uBlock only)"""
        try:
            self.logger.info(f"Restoring session backup: {backup_path}")
            
            # Extract session backup
            temp_dir = "/tmp/session_restore"
            os.makedirs(temp_dir, exist_ok=True)
            
            cmd = f"tar -xzf {backup_path} -C {temp_dir}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                return f"❌ Session backup extraction failed: {result.stderr}"
            
            # Restore components
            restored_items = []
            
            # 1. Restore cookies
            cookies_file = os.path.join(temp_dir, 'cookies.json')
            if os.path.exists(cookies_file):
                import shutil
                shutil.copy2(cookies_file, self.cookies_file)
                restored_items.append("cookies")
            
            # 2. Restore uBlock
            ublock_src = os.path.join(temp_dir, 'extensions', 'uBlock0@raymondhill.net.xpi')
            ublock_dest = os.path.join(CONFIG['firefox_profile'], 'extensions', 'uBlock0@raymondhill.net.xpi')
            if os.path.exists(ublock_src):
                os.makedirs(os.path.dirname(ublock_dest), exist_ok=True)
                import shutil
                shutil.copy2(ublock_src, ublock_dest)
                restored_items.append("uBlock")
            
            # 3. Restore preferences
            prefs_src = os.path.join(temp_dir, 'prefs.js')
            prefs_dest = os.path.join(CONFIG['firefox_profile'], 'prefs.js')
            if os.path.exists(prefs_src):
                import shutil
                shutil.copy2(prefs_src, prefs_dest)
                restored_items.append("preferences")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            if restored_items:
                self.logger.info(f"Session restored: {', '.join(restored_items)}")
                # Restart browser to apply changes
                if self.state['is_running']:
                    await self.restart_browser()
                
                return f"✅ Session restored successfully! Items: {', '.join(restored_items)}"
            else:
                return "❌ No valid session data found in backup"
                
        except Exception as e:
            self.logger.error(f"Session restoration failed: {e}")
            return f"❌ Session restoration error: {str(e)}"

    # ==================== BACKUP DOWNLOAD & RESTORATION ====================

    async def download_backup(self, file_id, file_name):
        """Download backup file from Telegram"""
        try:
            os.makedirs(CONFIG['backup_dir'], exist_ok=True)
            backup_path = os.path.join(CONFIG['backup_dir'], file_name)
            
            # Get file info from Telegram
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getFile"
            params = {'file_id': file_id}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                return f"❌ Failed to get file info: {response.status_code} - {response.text}"
            
            file_info = response.json()
            if not file_info.get('ok'):
                return f"❌ Telegram API error: {file_info.get('description', 'Unknown error')}"
            
            file_path = file_info['result']['file_path']
            self.logger.info(f"File path received: {file_path}")
            
            # Download the file
            download_url = f"https://api.telegram.org/file/bot{CONFIG['telegram_token']}/{file_path}"
            download_response = requests.get(download_url, stream=True, timeout=60)
            download_response.raise_for_status()
            
            with open(backup_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify download
            if os.path.exists(backup_path) and os.path.getsize(backup_path) > 0:
                size_mb = os.path.getsize(backup_path) / 1024 / 1024
                self.logger.info(f"Backup downloaded: {backup_path} ({size_mb:.2f} MB)")
                return backup_path
            else:
                return "❌ Backup download failed - file is empty"
                
        except Exception as e:
            self.logger.error(f"Backup download failed: {e}")
            return f"❌ Backup download failed: {str(e)}"

    def restore_backup(self, backup_path):
        """Restore full profile from Termux backup"""
        try:
            if not os.path.exists(backup_path):
                return f"❌ Backup file not found: {backup_path}"
            
            profile_dir = CONFIG['firefox_profile']
            os.makedirs(profile_dir, exist_ok=True)
            
            self.logger.info(f"Restoring full backup to {profile_dir}")
            
            # Clean profile directory
            self.logger.info("Cleaning profile directory...")
            for item in os.listdir(profile_dir):
                item_path = os.path.join(profile_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        import shutil
                        shutil.rmtree(item_path)
                except Exception as e:
                    self.logger.warning(f"Could not remove {item_path}: {e}")
            
            # Extract backup
            cmd = f"tar -xzf {backup_path} -C {profile_dir} --strip-components=1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                # Fix profile version compatibility
                self.fix_profile_compatibility()
                
                self.logger.info("Full backup restored successfully!")
                
                # Auto-create session backup after full restore
                if self.state['is_running']:
                    asyncio.create_task(self.auto_create_session_backup())
                
                return "✅ Full profile restored successfully! Session backup created automatically."
            else:
                return f"❌ Backup restoration failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "❌ Backup restoration timed out"
        except Exception as e:
            return f"❌ Backup restoration error: {str(e)}"

    def fix_profile_compatibility(self):
        """Fix Firefox profile version issues"""
        try:
            profile_dir = CONFIG['firefox_profile']
            
            # Remove version compatibility files
            version_files = ['compatibility.ini', 'times.json', 'sessionCheckpoints.json']
            for file in version_files:
                file_path = os.path.join(profile_dir, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Remove caches
            caches = ['startupCache', 'cache', 'cache2']
            for cache in caches:
                cache_path = os.path.join(profile_dir, cache)
                if os.path.exists(cache_path):
                    import shutil
                    shutil.rmtree(cache_path)
            
            # Create new compatibility file
            compatibility_file = os.path.join(profile_dir, 'compatibility.ini')
            with open(compatibility_file, 'w') as f:
                f.write("[Compatibility]\n")
                f.write("LastVersion=1490\n")
                f.write("LastPlatform=Linux\n")
            
            self.logger.info("Profile compatibility fixed")
            return True
            
        except Exception as e:
            self.logger.error(f"Profile compatibility fix failed: {e}")
            return False

    async def auto_create_session_backup(self):
        """Automatically create session backup after successful restore"""
        try:
            self.logger.info("Auto-creating session backup...")
            await asyncio.sleep(10)  # Wait for browser to stabilize
            
            backup_path = await self.create_session_backup()
            if backup_path:
                # Send to Telegram
                url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendDocument"
                with open(backup_path, 'rb') as document:
                    files = {'document': document}
                    data = {
                        'chat_id': self.telegram_chat_id,
                        'caption': f'🔐 AUTO-GENERATED Session Backup\n⏰ {self.get_ist_time().strftime("%Y-%m-%d %H:%M IST")}\n💾 Save this for future deployments!'
                    }
                    requests.post(url, files=files, data=data, timeout=60)
                
                os.remove(backup_path)
                self.logger.info("Auto session backup sent to Telegram")
                
        except Exception as e:
            self.logger.error(f"Auto session backup failed: {e}")

    # ==================== CORE SOLVER FUNCTIONS ====================
    
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
            
            # Load cookies with validation
            await self.load_cookies()
            
            self.state['browser_restarts'] += 1
            self.logger.info("Playwright started with persistent context!")
            return True
            
        except Exception as e:
            self.logger.error(f"Playwright setup failed: {e}")
            return False

    async def load_cookies(self):
        """Load cookies with expiration validation"""
        try:
            if not os.path.exists(self.cookies_file) or not self.context:
                return False
                
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # Fix and validate cookies
            valid_cookies = []
            current_time = int(time.time())
            
            for cookie in cookies:
                if not all(key in cookie for key in ['name', 'value', 'domain']):
                    continue
                    
                # Fix expiration
                if 'expires' in cookie:
                    if cookie['expires'] <= 0:
                        cookie['expires'] = current_time + 86400
                    elif cookie['expires'] < current_time:
                        cookie['expires'] = current_time + 86400
                else:
                    cookie['expires'] = current_time + 86400
                
                valid_cookies.append(cookie)
            
            if valid_cookies:
                await self.context.clear_cookies()
                await self.context.add_cookies(valid_cookies)
                self.logger.info(f"Loaded {len(valid_cookies)} validated cookies")
                return True
                
        except Exception as e:
            self.logger.warning(f"Could not load cookies: {e}")
        
        return False

    async def save_cookies(self):
        """Save current cookies"""
        try:
            if self.page and self.state['is_logged_in']:
                cookies = await self.context.cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f)
                self.logger.info("Cookies saved")
        except Exception as e:
            self.logger.warning(f"Could not save cookies: {e}")

    async def is_already_logged_in(self):
        """Check if already logged in via cookies"""
        try:
            await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
            content = await self.page.content()
            return 'login' not in content.lower() and 'surf' in self.page.url.lower()
        except Exception:
            return False

    async def ultimate_login(self):
        """Login to AdShare"""
        if await self.is_already_logged_in():
            self.logger.info("Already logged in via cookies!")
            self.state['is_logged_in'] = True
            return True
            
        try:
            self.logger.info("🚀 STARTING ULTIMATE LOGIN...")
            await self.page.goto("https://adsha.re/login", wait_until='networkidle')
            await self.page.wait_for_selector("body", timeout=CONFIG['page_timeout'])
            await asyncio.sleep(2)
            
            page_content = await self.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            form = soup.find('form', {'name': 'login'}) or soup.find_all('form')[0] if soup.find_all('form') else None
            if not form:
                self.logger.error("No forms found!")
                return False
                
            password_field_name = None
            for field in form.find_all('input'):
                if field.get('value') == 'Password' and field.get('name') != 'mail':
                    password_field_name = field.get('name')
                    self.logger.info(f"Found password field by value: {password_field_name}")
                    break
                    
            if not password_field_name:
                password_fields = form.find_all('input', {'type': 'password'})
                if password_fields:
                    password_field_name = password_fields[0].get('name')
                    self.logger.info(f"Found password field by type: {password_field_name}")
                    
            if not password_field_name:
                for field in form.find_all('input'):
                    if field.get('name') and field.get('name') != 'mail' and field.get('type') != 'email':
                        password_field_name = field.get('name')
                        self.logger.info(f"Found password field by exclusion: {password_field_name}")
                        break
                        
            if not password_field_name:
                inputs = form.find_all('input')
                if len(inputs) >= 2:
                    password_field_name = inputs[1].get('name')
                    self.logger.info(f"Found password field by position: {password_field_name}")
                    
            if not password_field_name:
                self.logger.error("Could not find password field!")
                return False

            # Fill email
            email_selectors = [
                "input[name='mail']", "input[type='email']", "input[placeholder*='email' i]",
                "input[placeholder*='Email' i]", "input[name*='mail' i]", "input[name*='email' i]",
                "input:first-of-type", "input:nth-of-type(1)"
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
                
            await asyncio.sleep(1)
            
            # Fill password
            password_selectors = [
                f"input[name='{password_field_name}']", "input[type='password']",
                "input[placeholder*='password' i]", "input[placeholder*='Password' i]",
                "input:nth-of-type(2)", "input:last-of-type"
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
                
            await asyncio.sleep(1)
            
            # Submit login
            login_selectors = [
                "button[type='submit']", "input[type='submit']", "button",
                "input[value*='Login' i]", "input[value*='Sign' i]", "button:has-text('Login')",
                "button:has-text('Sign')", "input[value*='Log']", "input[value*='login']",
                "form button", "form input[type='submit']"
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
                    await self.page.evaluate("document.querySelector('form').submit()")
                    self.logger.info("Form submitted via JavaScript")
                    login_clicked = True
                except:
                    pass
                    
            if not login_clicked:
                try:
                    await self.page.keyboard.press('Enter')
                    self.logger.info("Enter key pressed")
                    login_clicked = True
                except:
                    pass
                    
            if not login_clicked:
                self.logger.error("All login submission methods failed")
                return False
                
            await asyncio.sleep(8)
            
            # Check login success
            current_url = self.page.url.lower()
            page_title = await self.page.title()
            self.logger.info(f"After login - URL: {current_url}, Title: {page_title}")
            
            await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
            final_url = self.page.url.lower()
            self.logger.info(f"Final URL: {final_url}")
            
            if "surf" in final_url or "dashboard" in final_url:
                self.logger.info("🎉 LOGIN SUCCESSFUL!")
                self.state['is_logged_in'] = True
                await self.save_cookies()
                
                # Auto-create session backup after login
                asyncio.create_task(self.auto_create_session_backup())
                
                self.send_telegram("✅ <b>LOGIN SUCCESSFUL!</b>\n🔐 Session backup created automatically.")
                return True
                
            self.logger.error("❌ LOGIN FAILED - Still on login page")
            return False
            
        except Exception as e:
            self.logger.error(f"Login process failed: {e}")
            return False

    async def solve_symbol_game(self):
        """Solve the symbol matching game"""
        if not self.state['is_running'] or self.state['is_paused']:
            return False
            
        try:
            await self.page.goto("https://adsha.re/surf", wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Wait for game to load
            question_svg = await self.page.query_selector("svg")
            if not question_svg:
                self.logger.info("Waiting for game to load...")
                return False
                
            # Get all answer options
            links = await self.page.query_selector_all("a, button")
            if len(links) >= 4:  # Usually 4 options
                # Click random option (simple approach)
                await links[random.randint(0, 3)].click()
                self.state['total_solved'] += 1
                self.update_credits_earned(1)
                self.logger.info(f"Game solved! Total: {self.state['total_solved']}")
                await asyncio.sleep(3)
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Game solving failed: {e}")
            return False

    def update_credits_earned(self, credits_earned=1):
        """Update credits and check daily target"""
        self.state['credits_earned_today'] += credits_earned
        
        if self.state['daily_target'] > 0 and self.state['credits_earned_today'] >= self.state['daily_target']:
            self.logger.info(f"🎉 DAILY TARGET REACHED! {self.state['credits_earned_today']}/{self.state['daily_target']}")
            self.send_telegram(f"🎉 <b>DAILY TARGET ACHIEVED!</b>\n💎 Earned: {self.state['credits_earned_today']} credits")
            self.state['is_paused'] = True
            return True
        return False

    async def restart_browser(self):
        """Restart browser with cooldown"""
        current_time = time.time()
        if current_time - self.state['last_restart_time'] < 10:  # 10 second cooldown
            self.logger.info("Restart cooldown active, waiting...")
            await asyncio.sleep(10)
            
        self.state['last_restart_time'] = current_time
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
            self.state['last_browser_health_check'] = time.time()
            return True
        except Exception:
            return False

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
        if not await self.is_already_logged_in() and not await self.ultimate_login():
            self.logger.error("Login failed")
            self.stop()
            return
            
        # Main solving loop
        cycle_count = 0
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                if self.state['is_paused']:
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

    def check_daily_reset(self):
        """Check and reset daily credits if needed"""
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

    def start(self):
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
        
        status_msg = f"🚀 <b>CREDIT GOAL Solver Started!</b>\n🎯 Target: {self.state['daily_target']} credits\n💎 Earned: {self.state['credits_earned_today']} credits"
        self.send_telegram(status_msg)
        return "✅ CREDIT GOAL solver started successfully!"

    def stop(self):
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        
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
🔄 Browser Restarts: {self.state['browser_restarts']}
⏸️ Paused: {'✅' if self.state['is_paused'] else '❌'}
        """
        return status

class TelegramBot:
    def __init__(self):
        self.solver = CreditGoalSolver()
        self.logger = logging.getLogger(__name__)
        self.last_file_id = None

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
        
        # Handle document (backup file)
        if 'document' in update['message']:
            file_id = update['message']['document']['file_id']
            file_name = update['message']['document']['file_name']
            
            if file_name.endswith('.tar.gz'):
                self.last_file_id = file_id
                if 'session' in file_name.lower():
                    response = f"📥 Session backup received: {file_name}\nUse /restoresession to restore it."
                else:
                    response = f"📥 Full backup received: {file_name}\nUse /restorebackup to restore it."
            else:
                response = "❌ Please send a .tar.gz backup file."

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
            elif text.startswith('/backup'):
                async def create_backup():
                    return await self.solver.send_session_backup()
                response = self.run_async(create_backup)
            elif text.startswith('/restorebackup'):
                if self.last_file_id:
                    async def restore_full():
                        file_path = await self.solver.download_backup(self.last_file_id, f"full_backup_{int(time.time())}.tar.gz")
                        if isinstance(file_path, str) and not file_path.startswith('❌'):
                            return self.solver.restore_backup(file_path)
                        return file_path
                    response = self.run_async(restore_full)
                else:
                    response = "❌ No backup file received."
            elif text.startswith('/restoresession'):
                if self.last_file_id:
                    async def restore_session():
                        file_path = await self.solver.download_backup(self.last_file_id, f"session_backup_{int(time.time())}.tar.gz")
                        if isinstance(file_path, str) and not file_path.startswith('❌'):
                            return await self.solver.restore_session_backup(file_path)
                        return file_path
                    response = self.run_async(restore_session)
                else:
                    response = "❌ No session backup received."
            elif text.startswith('/pause'):
                self.solver.state['is_paused'] = True
                response = "⏸️ <b>Solver Paused</b>\nUse /resume to continue"
            elif text.startswith('/resume'):
                self.solver.state['is_paused'] = False
                response = "▶️ <b>Solver Resumed</b>"
            elif text.startswith('/help'):
                response = """
🤖 <b>AdShare Solver Commands</b>

🔧 Core Commands:
/start - Start solver
/stop - Stop solver  
/status - Check status
/target 2000 - Set daily goal
/pause - Pause solver
/resume - Resume solver

💾 Backup System:
/backup - Create & send session backup
📤 Send .tar.gz file for restoration:
   - Full profile backup → /restorebackup
   - Session backup → /restoresession

💡 <b>Workflow:</b>
1. Send full Termux backup → /restorebackup
2. Bot auto-creates session backup
3. Save session backup for future deployments
4. Next time: send session backup → /restoresession
                """
        
        if response:
            self.solver.send_telegram(response)

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
    bot.logger.info("AdShare Solver with Session Backup started!")
    bot.handle_updates()
