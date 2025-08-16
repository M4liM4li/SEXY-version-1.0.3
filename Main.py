#!/usr/bin/env python3

# =============================|
# Main Program                  |
# =============================|

# Import standard libraries
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sys
import os
import hashlib
from datetime import datetime, timezone
import threading
import time
import webbrowser
import requests
import json
from PIL import Image, ImageTk
import io
import base64
import gc
# Import custom modules
try:
    from Windowscapture import WindowCapture
    from Myclassbot import Classbot
    from Classclick import Click
    # Import the modified keyauth with exception classes
    from keyauth import (
        api, 
        KeyAuthException, 
        KeyAuthLoginException, 
        KeyAuthRegisterException,
        KeyAuthUpgradeException,
        KeyAuthLicenseException,
        KeyAuthHWIDException,
        KeyAuthInitException
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# Set customtkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# =============================|
# Discord Webhook Class         |
# =============================|

class DiscordWebhook:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.session = requests.Session()  # เพิ่ม session pool
        self.session.headers.update({
            'User-Agent': 'Sexy Bot/1.0'
        })

    def send_message(self, message, image_data=None):
        """Send message to Discord webhook with optimized connection"""
        try:
            data = {
                "content": message,
                "username": "Sexy Bot",
                "avatar_url": "https://i.imgur.com/4M34hi2.png"
            }
            files = {}
            if image_data:
                # บีบอัดรูปภาพก่อนส่ง
                compressed_image = self._compress_image(image_data)
                files["file"] = ("screenshot.png", compressed_image, "image/png")
            
            response = self.session.post(
                self.webhook_url,
                data=data,
                files=files,
                timeout=10  # ลดเวลา timeout
            )
            
            return response.status_code == 204
                
        except Exception as e:
            print(f"Discord webhook failed: {e}")
            return False

    def _compress_image(self, image_data, max_size_mb=8):
        """บีบอัดรูปภาพเพื่อลดขนาด"""
        try:
            if len(image_data) <= max_size_mb * 1024 * 1024:
                return image_data
                
            img = Image.open(io.BytesIO(image_data))
            
            # ปรับขนาดรูปถ้าใหญ่เกินไป
            if img.size[0] > 1280 or img.size[1] > 720:
                img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
            
            # บีบอัดด้วย quality ที่เหมาะสม
            output = io.BytesIO()
            img.save(output, format='PNG', optimize=True)
            return output.getvalue()
            
        except Exception as e:
            print(f"Image compression failed: {e}")
            return image_data

    def __del__(self):
        """ปิด session เมื่อ object ถูกทำลาย"""
        if hasattr(self, 'session'):
            self.session.close()

    def send_embed(self, title, description, color=0x00ff00, fields=None, image_data=None):
        """Send embed message to Discord"""
        try:
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "Create By _h4ckler",
                    "icon_url": "https://i.ibb.co/Kpj01gtZ/hackler-httpss-mj-run-OFZTaf-D91-LM-simple-avataranime-3d-rende-3ffcf3e4-8796-4801-a049-704417901bb4.png"
                }
            }
            
            if fields:
                embed["fields"] = fields
            
            data = {
                "embeds": [embed],
                "username": "SA Gaming Bot"
            }
            
            files = {}
            if image_data:
                files["file"] = ("screenshot.png", image_data, "image/png")
                embed["image"] = {"url": "attachment://screenshot.png"}
            
            response = requests.post(
                self.webhook_url,
                data={"payload_json": json.dumps(data)},
                files=files,
                timeout=30
            )
            
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord embed failed: {e}")
            return False

# =============================|
# SA Gaming Bot Class          |
# =============================|

class SAGamingBot:
    def __init__(self, user_data=None, parent_root=None, keyauth_app=None):
        # Initialize basic attributes
        self.parent_root = parent_root
        self.user_data = user_data
        self.keyauth_app = keyauth_app
        self.windowname = 'Sexy - Google Chrome'
        self.running = False
        self.bot_thread = None
        self.target_image = "img/player.png"
        self.target_name = "Player"
        self.total_clicks = 0
        self.start_time = None
        self.is_authorized = self.check_authorization()
        self.config_file = "webhook_config.json"
        self.gc_counter = 0
        self.gc_interval = 100
        
        # Discord webhook settings
        self.last_screenshot_time = 0
        self.screenshot_interval = 5
        
        # Initialize objects
        try:
            self.windows = WindowCapture(self.windowname)
            self.myclick = Click(self.windowname)
            self.hwid = self.myclick.getchromeid()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize: {e}")
            sys.exit(1)
        
        # Check image files
        for img in ["img/player.png", "img/banker.png"]:
            if not os.path.exists(img):
                messagebox.showwarning("Warning", f"Image not found: '{img}'")
        
        # Load webhook configuration
        self.load_webhook_config()
        
        # Setup GUI
        self.setup_gui()
    def cleanup_memory(self):
        """ทำความสะอาด memory เป็นระยะ"""
        import gc
        self.gc_counter += 1
        
        if self.gc_counter >= self.gc_interval:
            gc.collect()
            self.gc_counter = 0
    # =============================|
    # Webhook Configuration        |
    # =============================|

    def load_webhook_config(self):
        """Load webhook configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.webhook_url = config.get('webhook_url', '')
                    
                    if self.webhook_url and ("discord.com/api/webhooks/" in self.webhook_url or 
                                           "discordapp.com/api/webhooks/" in self.webhook_url):
                        self.discord_webhook = DiscordWebhook(self.webhook_url)
                        print(f"✅ Webhook auto-connected: {self.webhook_url[:50]}...")
                        self.send_auto_connection_notification()
                    else:
                        self.discord_webhook = None
                        self.webhook_url = ""
                        print("⚠️ No valid webhook URL found")
            else:
                self.webhook_url = ""
                self.discord_webhook = None
                print("📝 No webhook config file found")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in webhook config: {e}")
            self.webhook_url = ""
            self.discord_webhook = None
            try:
                os.remove(self.config_file)
                print("🗑️ Corrupted config file removed")
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error loading webhook config: {e}")
            self.webhook_url = ""
            self.discord_webhook = None

    def save_webhook_config(self):
        """Optimized config saving with atomic write"""
        try:
            config = {
                'webhook_url': self.webhook_url,
                'last_saved': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Atomic write - เขียนไปยังไฟล์ temp ก่อน
            temp_file = f"{self.config_file}.tmp"
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # ย้ายไฟล์ temp มาเป็นไฟล์จริง (atomic operation)
            import shutil
            shutil.move(temp_file, self.config_file)
            
            print(f"✅ Webhook config saved successfully")
            
        except Exception as e:
            print(f"❌ Error saving webhook config: {e}")
            # ลบไฟล์ temp ถ้ามี
            try:
                if os.path.exists(f"{self.config_file}.tmp"):
                    os.remove(f"{self.config_file}.tmp")
            except:
                pass

    # =============================|
    # Authorization Methods        |
    # =============================|

    def check_authorization(self):
        """Check login and license status"""
        if not self.user_data or not hasattr(self.user_data, 'username') or not self.user_data.username:
            return False
        if not hasattr(self.user_data, 'subscriptions') or not self.user_data.subscriptions:
            return False
        try:
            expiry_timestamp = int(self.user_data.subscriptions[0]['expiry'])
            return datetime.now(timezone.utc).timestamp() < expiry_timestamp
        except (KeyError, ValueError, IndexError):
            return False

    def get_license_status(self):
        """Get license status info"""
        if not self.user_data or not hasattr(self.user_data, 'subscriptions') or not self.user_data.subscriptions:
            return "No License", "#ff4444"
        try:
            expiry_timestamp = int(self.user_data.subscriptions[0]['expiry'])
            current_timestamp = datetime.now(timezone.utc).timestamp()
            expiry_date = datetime.fromtimestamp(expiry_timestamp, timezone.utc).strftime('%d/%m/%Y')
            
            if current_timestamp >= expiry_timestamp:
                return f"Expired: {expiry_date}", "#ff4444"
            
            days_left = int((expiry_timestamp - current_timestamp) / 86400)
            return f"{expiry_date}", "#44ff44" if days_left > 7 else "#ff8800"
        except (KeyError, ValueError, IndexError):
            return "License Error", "#ff4444"

    # =============================|
    # Webhook Dialog Methods       |
    # =============================|

    def setup_discord_webhook(self):
        """Setup Discord webhook dialog"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Discord Webhook Settings")
        dialog.geometry("450x350")
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 150
        dialog.geometry(f'450x350+{x}+{y}')
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, 
                     text="Discord Webhook Settings", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(main_frame, 
                     text="แจ้งเตือนผ่าน Discord + แคปหน้าจอทุก 1 ชม", 
                     font=ctk.CTkFont(size=11), 
                     text_color="#888888").pack(pady=(0, 15))
        
        webhook_label = ctk.CTkLabel(main_frame, text="Discord Webhook URL:")
        webhook_label.pack(anchor="w", padx=20, pady=(5, 0))
        
        webhook_entry = ctk.CTkEntry(main_frame, 
                                    placeholder_text="https://discord.com/api/webhooks/...", 
                                    width=350, height=35)
        webhook_entry.pack(pady=5, padx=20)
        webhook_entry.insert(0, self.webhook_url)
        
        status_label = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=10))
        status_label.pack(pady=5)
        
        save_btn = ctk.CTkButton(main_frame, 
                                text="บันทึก", 
                                command=lambda: self.save_webhook(webhook_entry.get(), status_label, dialog), 
                                width=100, height=30, fg_color="#28a745")
        save_btn.pack(pady=5)
        
        test_btn = ctk.CTkButton(main_frame, 
                                text="ทดสอบ", 
                                command=lambda: self.test_webhook_connection(webhook_entry.get(), status_label), 
                                width=100, height=30, fg_color="#17a2b8")
        test_btn.pack(pady=5)
        
        ctk.CTkButton(main_frame, 
                     text="ปิด", 
                     command=dialog.destroy, 
                     width=100, height=30, fg_color="#6c757d").pack(pady=5)

    def send_auto_connection_notification(self):
        """Send notification when webhook auto-connects"""
        if not self.discord_webhook:
            return
        
        def send_notification_thread():
            try:
                username = self.user_data.username if self.user_data else "Unknown"
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                success = self.discord_webhook.send_embed(
                    title="🔗 Webhook Auto-Connected",
                    description="SEXY Bot webhook connected automatically after login",
                    color=0x00ff00,
                    fields=[
                        {"name": "User", "value": username, "inline": True},
                        {"name": "Status", "value": "✅ Connected", "inline": True},
                        {"name": "Time", "value": current_time, "inline": False}
                    ]
                )
                
                print("✅ Auto-connection notification sent" if success else 
                      "❌ Failed to send auto-connection notification")
                    
            except Exception as e:
                print(f"Auto-connection notification failed: {e}")
        
        threading.Thread(target=send_notification_thread, daemon=True).start()

    def save_webhook(self, webhook_url, status_label, dialog):
        """Save webhook URL with validation"""
        url = webhook_url.strip()
        
        if url:
            if "discord.com/api/webhooks/" in url or "discordapp.com/api/webhooks/" in url:
                if len(url) > 50:
                    self.webhook_url = url
                    self.discord_webhook = DiscordWebhook(url)
                    self.save_webhook_config()
                    
                    if hasattr(self, 'webhook_status_label'):
                        self.webhook_status_label.configure(text="🟢 Connected", text_color="#00ff00")
                    
                    status_label.configure(text="✅ Webhook saved successfully!", text_color="#00ff00")
                    print(f"✅ Webhook configured: {url[:50]}...")
                    self.root.after(1500, dialog.destroy)
                else:
                    status_label.configure(text="❌ Invalid webhook URL (too short)", text_color="#ff4444")
            else:
                status_label.configure(text="❌ Invalid Discord webhook URL format", text_color="#ff4444")
        else:
            self.webhook_url = ""
            self.discord_webhook = None
            self.save_webhook_config()
            
            if hasattr(self, 'webhook_status_label'):
                self.webhook_status_label.configure(text="🔴 Disconnected", text_color="#ff4444")
            
            status_label.configure(text="🗑️ Webhook cleared", text_color="#ffaa00")
            print("🗑️ Webhook configuration cleared")

    def validate_webhook_url(self, url):
        """Validate webhook URL"""
        if not url or not isinstance(url, str):
            return False, "URL is empty or invalid"
        
        url = url.strip()
        
        if not ("discord.com/api/webhooks/" in url or "discordapp.com/api/webhooks/" in url):
            return False, "Not a Discord webhook URL"
        
        if not url.startswith("https://"):
            return False, "URL must use HTTPS"
        
        if len(url) < 50:
            return False, "URL too short"
        
        import re
        pattern = r'https://discord(?:app)?\.com/api/webhooks/\d+/[\w-]+'
        if not re.match(pattern, url):
            return False, "Invalid webhook URL format"
        
        return True, "Valid webhook URL"

    def test_webhook_connection(self, webhook_url, status_label):
        """Test webhook connection"""
        is_valid, error_msg = self.validate_webhook_url(webhook_url)
        if not is_valid:
            status_label.configure(text=f"❌ {error_msg}", text_color="#ff4444")
            return
        
        def test_thread():
            try:
                status_label.configure(text="🔄 Testing webhook...", text_color="#ffaa00")
                test_webhook = DiscordWebhook(webhook_url)
                success = test_webhook.send_embed(
                    title="🧪 Test Message",
                    description="SEXY Bot webhook test successful!",
                    color=0x00ff00,
                    fields=[
                        {"name": "Status", "value": "✅ Connected", "inline": True},
                        {"name": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                        {"name": "User", "value": self.user_data.username if self.user_data else "Unknown", "inline": True}
                    ]
                )
                
                self.root.after(0, lambda: status_label.configure(
                    text="✅ Test successful! Message sent to Discord" if success else 
                         "❌ Test failed - Check webhook URL", 
                    text_color="#00ff00" if success else "#ff4444"
                ))
                    
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg:
                    error_msg = "Webhook not found (404)"
                elif "401" in error_msg:
                    error_msg = "Unauthorized (401)"
                elif "timeout" in error_msg.lower():
                    error_msg = "Connection timeout"
                else:
                    error_msg = f"Error: {error_msg[:50]}"
                    
                self.root.after(0, lambda: status_label.configure(
                    text=f"❌ {error_msg}", 
                    text_color="#ff4444"
                ))
        
        threading.Thread(target=test_thread, daemon=True).start()

    #-------------------------------------------------------------------

    def safe_update_status(self, message, color="#ffffff"):
        """Thread-safe status update"""
        if self.root and hasattr(self, 'status_label'):
            try:
                self.root.after(0, lambda: self.status_label.configure(
                    text=message, text_color=color
                ))
            except:
                pass  # GUI may be destroyed

    def safe_update_clicks(self):
        if self.root and hasattr(self, 'clicks_label'):
            try:
                self.root.after(0, lambda: self.clicks_label.configure(
                    text=f"Clicks: {self.total_clicks}"
                ))
            except:
                pass
    # =============================|
    # Notification Methods         |
    # =============================|

    def send_discord_notification(self, message_type, details=None):
        """Send Discord notification with screenshot"""
        if not self.discord_webhook:
            return
        
        def send_notification_thread():
            try:
                username = self.user_data.username if self.user_data else "Unknown"
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                screenshot_data = self.capture_screenshot()
                
                notification_configs = {
                    "bot_started": {
                        "title": "🟢 Bot Started",
                        "description": "SEXY Bot has been started",
                        "color": 0x00ff00,
                        "fields": [
                            {"name": "User", "value": username, "inline": True},
                            {"name": "Target", "value": self.target_name, "inline": True},
                            {"name": "Time", "value": current_time, "inline": False}
                        ]
                    },
                    "bot_stopped": {
                        "title": "🔴 Bot Stopped",
                        "description": "SEXY Bot has been stopped",
                        "color": 0xff0000,
                        "fields": [
                            {"name": "User", "value": username, "inline": True},
                            {"name": "Runtime", "value": details.get("runtime", "Unknown") if details else "Unknown", "inline": True},
                            {"name": "Total Clicks", "value": str(details.get("clicks", 0) if details else 0), "inline": True},
                            {"name": "Time", "value": current_time, "inline": False}
                        ]
                    },
                    "hourly_report": {
                        "title": "📊 Hourly Report",
                        "description": "SEXY Bot hourly status report",
                        "color": 0x0099ff,
                        "fields": [
                            {"name": "User", "value": username, "inline": True},
                            {"name": "Target", "value": self.target_name, "inline": True},
                            {"name": "Runtime", "value": details.get("runtime", "Unknown") if details else "Unknown", "inline": True},
                            {"name": "Total Clicks", "value": str(details.get("clicks", 0) if details else 0), "inline": True},
                            {"name": "Time", "value": current_time, "inline": False}
                        ]
                    },
                    "error": {
                        "title": "⚠️ Error Occurred",
                        "description": "SEXY Bot encountered an error",
                        "color": 0xff8800,
                        "fields": [
                            {"name": "User", "value": username, "inline": True},
                            {"name": "Error", "value": details.get("error", "Unknown error") if details else "Unknown error", "inline": False},
                            {"name": "Time", "value": current_time, "inline": True}
                        ]
                    },
                    "target_found": {
                        "title": "🎯 Target Found & Clicked",
                        "description": f"Found and clicked {self.target_name}",
                        "color": 0x00ffff,
                        "fields": [
                            {"name": "User", "value": username, "inline": True},
                            {"name": "Target", "value": self.target_name, "inline": True},
                            {"name": "Position", "value": f"{details.get('x', 0)}, {details.get('y', 0)}" if details else "Unknown", "inline": True},
                            {"name": "Total Clicks", "value": str(self.total_clicks), "inline": True},
                            {"name": "Runtime", "value": self.get_runtime_string(), "inline": True},
                            {"name": "Time", "value": current_time, "inline": False}
                        ]
                    }
                }
                
                config = notification_configs.get(message_type)
                if config:
                    success = self.discord_webhook.send_embed(
                        title=config["title"],
                        description=config["description"],
                        color=config["color"],
                        fields=config["fields"],
                        image_data=screenshot_data
                    )
                    if not success:
                        print(f"Failed to send Discord notification: {message_type}")
                    
            except Exception as e:
                print(f"Discord notification failed: {e}")
        
        threading.Thread(target=send_notification_thread, daemon=True).start()

    def capture_screenshot(self):
        """Optimized screenshot capture with caching and compression - Full Screen"""
        try:
            import pyautogui
            import numpy as np
            
            screenshot = pyautogui.screenshot()
            
            if screenshot is None:
                return None
            
            if hasattr(screenshot, 'size'):
                pass
            else:
                screenshot = Image.fromarray(screenshot)
            
            if not hasattr(screenshot, 'size'):
                return None
            
            original_size = screenshot.size
            max_size = (1280, 720)
            
            if original_size[0] > max_size[0] or original_size[1] > max_size[1]:
                ratio = min(max_size[0]/original_size[0], max_size[1]/original_size[1])
                new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
            
            img_byte_arr = io.BytesIO()
            
            if screenshot.size[0] * screenshot.size[1] > 500000:
                screenshot.save(img_byte_arr, format='WEBP', quality=85, method=6)
            else:
                screenshot.save(img_byte_arr, format='PNG', optimize=True, compress_level=6)
            
            return img_byte_arr.getvalue()
            
        except Exception as e:
            print(f"Full screen capture failed: {e}")
            try:
                screenshot = self.windows.screenshot()
                if screenshot is None:
                    return None
                
                if hasattr(screenshot, 'shape'):
                    if len(screenshot.shape) == 3:
                        import cv2
                        screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
                        screenshot = Image.fromarray(screenshot_rgb)
                    else:
                        screenshot = Image.fromarray(screenshot)
                
                if not hasattr(screenshot, 'size'):
                    return None
                
                original_size = screenshot.size
                max_size = (1280, 720)
                
                if original_size[0] > max_size[0] or original_size[1] > max_size[1]:
                    ratio = min(max_size[0]/original_size[0], max_size[1]/original_size[1])
                    new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                    screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
                
                img_byte_arr = io.BytesIO()
                
                if screenshot.size[0] * screenshot.size[1] > 500000:
                    screenshot.save(img_byte_arr, format='WEBP', quality=85, method=6)
                else:
                    screenshot.save(img_byte_arr, format='PNG', optimize=True, compress_level=6)
                
                return img_byte_arr.getvalue()
                
            except Exception as fallback_error:
                print(f"Fallback window capture also failed: {fallback_error}")
                return None


    # =============================|
    # License Extension Methods    |
    # =============================|

    def extend_license(self):
        """Extend license using keyauth upgrade method with proper error handling"""
        if not self.keyauth_app:
            messagebox.showerror("Error", "KeyAuth not available")
            return
            
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Extend License")
        dialog.geometry("350x350")
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 175
        y = (dialog.winfo_screenheight() // 2) - 150
        dialog.geometry(f'350x350+{x}+{y}')
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, 
                     text="ต่ออายุโปรแกรม", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(main_frame, 
                     text="Enter username and license key to extend", 
                     font=ctk.CTkFont(size=11), 
                     text_color="#888888").pack(pady=(0, 15))
        
        username_entry = ctk.CTkEntry(main_frame, 
                                     placeholder_text="Username", 
                                     width=250, height=35)
        username_entry.pack(pady=5)
        
        license_entry = ctk.CTkEntry(main_frame, 
                                    placeholder_text="License Key", 
                                    width=250, height=35)
        license_entry.pack(pady=5)
        
        status_label = ctk.CTkLabel(main_frame, 
                                   text="", 
                                   font=ctk.CTkFont(size=10))
        status_label.pack(pady=5)
        
        def extend_license_action():
            username = username_entry.get().strip()
            license_key = license_entry.get().strip()
            
            if not username or not license_key:
                status_label.configure(text="Please enter both username and license key", 
                                     text_color="#ff4444")
                return
                
            extend_btn.configure(state="disabled", text="Processing...")
            status_label.configure(text="Processing upgrade...", text_color="#ffaa00")
            
            def extend_thread():
                try:
                    self.keyauth_app.upgrade(username, license_key)
                    
                    # อัพเดต user data ถ้ามี
                    if hasattr(self.keyauth_app, 'user_data') and self.keyauth_app.user_data:
                        self.user_data = self.keyauth_app.user_data
                        self.is_authorized = self.check_authorization()
                    
                    self.root.after(0, lambda: status_label.configure(
                        text="License extended successfully!", 
                        text_color="#00ff00"
                    ))
                    
                    self.root.after(0, lambda: messagebox.showinfo("Success", "License extended successfully!\nPlease restart the program."))
                    self.root.after(1000, dialog.destroy)
                    
                except KeyAuthUpgradeException as e:
                    error_msg = str(e)
                    self.root.after(0, lambda: status_label.configure(
                        text=f"Upgrade failed: {error_msg}", 
                        text_color="#ff4444"
                    ))
                    self.root.after(0, lambda: extend_btn.configure(state="normal", text="ตกลง"))
                    
                except KeyAuthLicenseException as e:
                    self.root.after(0, lambda: status_label.configure(
                        text="Invalid License Key", 
                        text_color="#ff4444"
                    ))
                    self.root.after(0, lambda: extend_btn.configure(state="normal", text="ตกลง"))
                    
                except KeyAuthException as e:
                    error_msg = str(e)
                    self.root.after(0, lambda: status_label.configure(
                        text=f"Error: {error_msg}", 
                        text_color="#ff4444"
                    ))
                    self.root.after(0, lambda: extend_btn.configure(state="normal", text="ตกลง"))
                    
                except Exception as e:
                    error_msg = str(e)
                    self.root.after(0, lambda: status_label.configure(
                        text=f"Unexpected error: {error_msg}", 
                        text_color="#ff4444"
                    ))
                    self.root.after(0, lambda: extend_btn.configure(state="normal", text="ตกลง"))
            
            threading.Thread(target=extend_thread, daemon=True).start()
        
        extend_btn = ctk.CTkButton(main_frame, 
                                  text="ตกลง", 
                                  command=extend_license_action, 
                                  width=200, height=35, 
                                  fg_color="#28a745")
        extend_btn.pack(pady=15)
        
        ctk.CTkButton(main_frame, 
                     text="ยกเลิก", 
                     command=dialog.destroy, 
                     width=100, height=30, 
                     fg_color="#6c757d").pack(pady=5)
        
        license_entry.bind('<Return>', lambda e: extend_license_action())
        username_entry.focus()

    def refresh_gui(self):
        """Refresh GUI elements after license extension"""
        username = self.user_data.username if self.user_data and hasattr(self.user_data, 'username') else "Not Logged In"
        username_color = "#00ffff" if self.is_authorized else "#ff4444"
        license_text, license_color = self.get_license_status()
        
        self.root.destroy()
        self.setup_gui()

    # =============================|
    # GUI Setup Methods            |
    # =============================|

    def setup_gui(self):
        """Setup GUI"""
        self.root = ctk.CTk() if not self.parent_root else ctk.CTkToplevel(self.parent_root)
        self.root.title("Sexy Bot - Version Admin")
        self.root.geometry("500x500")
        self.root.resizable(False, False)
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 250
        y = (self.root.winfo_screenheight() // 2) - 250
        self.root.geometry(f'500x500+{x}+{y}')
        
        self.create_widgets()

    def create_widgets(self):
        """Create all widgets"""
        # Header
        header_frame = ctk.CTkFrame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        username = self.user_data.username if self.user_data and hasattr(self.user_data, 'username') else "Not Logged In"
        username_color = "#00ffff" if self.is_authorized else "#ff4444"
        
        ctk.CTkLabel(header_frame, 
                     text=f"User: {username}", 
                     font=ctk.CTkFont(size=12, weight="bold"), 
                     text_color=username_color).pack(side="left", padx=10, pady=5)
        
        license_text, license_color = self.get_license_status()
        ctk.CTkLabel(header_frame, 
                     text=f"หมดอายุ: {license_text}", 
                     font=ctk.CTkFont(size=11), 
                     text_color=license_color).pack(side="right", padx=10, pady=5)
        
        # Webhook status
        webhook_frame = ctk.CTkFrame(self.root)
        webhook_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(webhook_frame, 
                     text="Discord Webhook:", 
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=10, pady=5)
        
        self.webhook_status_label = ctk.CTkLabel(webhook_frame, 
                                               text="🔴 Disconnected" if not self.discord_webhook else "🟢 Connected",
                                               font=ctk.CTkFont(size=11),
                                               text_color="#ff4444" if not self.discord_webhook else "#00ff00")
        self.webhook_status_label.pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(webhook_frame, 
                     text="⚙️ Settings", 
                     command=self.setup_discord_webhook,
                     width=80, height=25, 
                     fg_color="#6c757d").pack(side="right", padx=10, pady=5)
        
        # License extension button
        if self.is_authorized:
            ctk.CTkButton(self.root, 
                         text="🔑 ต่ออายุโปรแกรม", 
                         command=self.extend_license, 
                         width=150, height=30, 
                         fg_color="#ffc107", 
                         text_color="#000000").pack(pady=5)
        
        # Warning for unauthorized
        if not self.is_authorized:
            warning_frame = ctk.CTkFrame(self.root, fg_color="#2d1818")
            warning_frame.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(warning_frame, 
                        text="⚠️ Please Login and Check License", 
                        font=ctk.CTkFont(size=12, weight="bold"), 
                        text_color="#ff4444").pack(pady=5)
            
        # Title
        ctk.CTkLabel(self.root, 
                     text="Sexy Bot", 
                     font=ctk.CTkFont(size=18, weight="bold"), 
                     text_color="#ff008c" if self.is_authorized else "#888888").pack(pady=10)
        
        # Control buttons frame
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=10)
        
        start_stop_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        start_stop_frame.pack(pady=5)
        
        self.btn_start = ctk.CTkButton(start_stop_frame, 
                                      text="▶ เริ่ม", 
                                      command=self.start_bot, 
                                      width=120, height=35, 
                                      fg_color="#28a745" if self.is_authorized else "#666666",
                                      state="normal" if self.is_authorized else "disabled")
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ctk.CTkButton(start_stop_frame, 
                                     text="■ หยุด", 
                                     command=self.stop_bot, 
                                     width=120, height=35, 
                                     fg_color="#dc3545", 
                                     state="disabled")
        self.btn_stop.pack(side="left", padx=5)
        
        toggle_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        toggle_frame.pack(pady=5)
        
        self.btn_toggle = ctk.CTkButton(toggle_frame, 
                                       text="Player", 
                                       command=self.toggle_target, 
                                       width=250, height=35, 
                                       fg_color="#007bff" if self.is_authorized else "#666666",
                                       state="normal" if self.is_authorized else "disabled")
        self.btn_toggle.pack()
        
        # Stats
        stats_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        stats_frame.pack(pady=10)
        
        self.clicks_label = ctk.CTkLabel(stats_frame, 
                                        text="Clicks: 0", 
                                        font=ctk.CTkFont(size=11))
        self.clicks_label.grid(row=0, column=0, padx=20)
        
        self.runtime_label = ctk.CTkLabel(stats_frame, 
                                         text="Runtime: 00:00:00", 
                                         font=ctk.CTkFont(size=11))
        self.runtime_label.grid(row=0, column=1, padx=20)
        
        self.screenshot_timer_label = ctk.CTkLabel(stats_frame, 
                                                 text="Next screenshot: --:--:--", 
                                                 font=ctk.CTkFont(size=10), 
                                                 text_color="#888888")
        self.screenshot_timer_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Status
        status_frame = ctk.CTkFrame(self.root)
        status_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(status_frame, 
                                        text="🕹️ Ready" if self.is_authorized else "🔒 Unauthorized", 
                                        font=ctk.CTkFont(size=11),
                                        text_color="#00ffff" if self.is_authorized else "#ff4444")
        self.status_label.pack(pady=5)
        
        self.progress = ctk.CTkProgressBar(self.root, mode='indeterminate')
        self.progress.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(self.root, 
                     text="Create by _h4ckler 1.0.3",
                     font=ctk.CTkFont(size=10), 
                     text_color="#888888").pack(side="bottom", pady=(5, 10))
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # =============================|
    # Bot Control Methods          |
    # =============================|

    def toggle_target(self):
        """Toggle between Player and Banker"""
        if not self.is_authorized:
            return
            
        if self.target_image == "img/player.png":
            self.target_image = "img/banker.png"
            self.target_name = "Banker"
            self.btn_toggle.configure(text="Banker", fg_color="#dc3545")
        else:
            self.target_image = "img/player.png"
            self.target_name = "Player"
            self.btn_toggle.configure(text="Player", fg_color="#007bff")

    def start_bot(self):
        """Start bot"""
        if not self.is_authorized or not self.check_authorization():
            messagebox.showwarning("Unauthorized", "Please login and check license")
            return
            
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.last_screenshot_time = time.time()
            self.total_clicks = 0
            self.status_label.configure(text="✅ Bot Started")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.progress.start()
            self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
            self.bot_thread.start()
            self.update_runtime()
            self.send_immediate_start_notification()

    def send_immediate_start_notification(self):
        """Send immediate notification with screenshot when bot starts"""
        if not self.discord_webhook:
            print("⚠️ No webhook configured for immediate notification")
            return
        
        def send_notification_thread():
            try:
                username = self.user_data.username if self.user_data else "Unknown"
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                screenshot_data = self.capture_screenshot()
                
                success = self.discord_webhook.send_embed(
                    title="🚀 Bot Started (Immediate)",
                    description="Sexy Bot has been started with immediate screenshot",
                    color=0x00ff00,
                    fields=[
                        {"name": "User", "value": username, "inline": True},
                        {"name": "Target", "value": self.target_name, "inline": True},
                        {"name": "Status", "value": "🟢 Running", "inline": True},
                        {"name": "Started Time", "value": current_time, "inline": False}
                    ],
                    image_data=screenshot_data
                )
                
                print("✅ Immediate start notification sent with screenshot" if success else 
                      "❌ Failed to send immediate start notification")
                    
            except Exception as e:
                print(f"Immediate start notification failed: {e}")
        
        threading.Thread(target=send_notification_thread, daemon=True).start()

    def stop_bot(self):
        """Stop bot"""
        if self.running:
            runtime = self.get_runtime_string()
            self.running = False
            self.status_label.configure(text="🛑 Bot Stopped")
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")
            self.progress.stop()
            
            self.send_discord_notification("bot_stopped", {
                "runtime": runtime,
                "clicks": self.total_clicks
            })

    def get_runtime_string(self):
        """Get formatted runtime string"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"

    def bot_loop(self):
        """Main bot loop with multi-Chrome window support"""
        last_click_positions = []
        position_timeout = 1
        max_positions = 10
        
        # เพิ่ม performance counter
        frame_times = []
        max_frame_samples = 60
        
        while self.running:
            frame_start = time.time()
            
            # ตรวจสอบ authorization แค่ทุก 10 วินาที
            if frame_start % 10 < 0.1:
                if not self.check_authorization():
                    self.running = False
                    self.root.after(0, lambda: self.status_label.configure(text="🔒 License Expired"))
                    break
            
            current_time = time.time()
            
            # ส่ง hourly report
            if current_time - self.last_screenshot_time >= self.screenshot_interval:
                self.last_screenshot_time = current_time
                threading.Thread(
                    target=lambda: self.send_discord_notification("hourly_report", {
                        "runtime": self.get_runtime_string(),
                        "clicks": self.total_clicks
                    }), 
                    daemon=True
                ).start()
            
            try:
                # ค้นหาในทุกหน้าต่าง Chrome
                screenshots = self.windows.screenshot_all_windows()
                
                if not screenshots:
                    self.root.after(0, lambda: self.status_label.configure(text="❌ No Chrome windows found"))
                    time.sleep(1)
                    continue
                
                found_target = False
                total_points = 0
                
                # วนลูปตรวจสอบทุกหน้าต่าง
                for window_data in screenshots:
                    if not self.running:
                        break
                    
                    hwnd = window_data['hwnd']
                    screenshot = window_data['screenshot']
                    window_title = window_data['title'][:30]
                    
                    search = Classbot(screenshot, self.target_image)
                    points = search.search(debug=False)
                    
                    if points:
                        found_target = True
                        total_points += len(points)
                        
                        # จำกัดจำนวน points ที่ประมวลผล
                        points = points[:3]
                        
                        for po in points:
                            if not self.running:
                                break
                            
                            # ทำความสะอาด position cache
                            current_time = time.time()
                            last_click_positions = [
                                (pos, timestamp, window_hwnd) for pos, timestamp, window_hwnd in last_click_positions[-max_positions:]
                                if current_time - timestamp < position_timeout
                            ]
                            
                            # ตรวจสอบ duplicate position (เฉพาะในหน้าต่างเดียวกัน)
                            should_click = True
                            for pos, _, window_hwnd in last_click_positions:
                                if (window_hwnd == hwnd and 
                                    abs(pos[0] - po[0]) < 15 and abs(pos[1] - po[1]) < 15):
                                    should_click = False
                                    break
                            
                            if should_click:
                                self.root.after(0, lambda x=po[0], y=po[1], title=window_title: 
                                    self.status_label.configure(text=f"🎯 Clicking at {x}, {y} in {title}"))
                                
                                # คลิกในหน้าต่างที่เจอเป้าหมาย
                                self.myclick.control_click(hwnd, po[0], po[1])
                                
                                self.total_clicks += 1
                                self.root.after(0, lambda: self.clicks_label.configure(text=f"Clicks: {self.total_clicks}"))
                                last_click_positions.append(((po[0], po[1]), current_time, hwnd))
                                
                                # ส่งการแจ้งเตือน
                                self.send_click_notification(po[0], po[1])
                                
                                print(f"✅ Clicked at ({po[0]}, {po[1]}) in Chrome: {window_title}")
                                
                                # หน่วงเวลาสั้น ๆ
                                time.sleep(0.05)
                            else:
                                self.root.after(0, lambda x=po[0], y=po[1], title=window_title: 
                                    self.status_label.configure(text=f"⏭️ Skipping recent position {x}, {y} in {title}"))
                
                # อัพเดทสถานะ
                if found_target:
                    self.root.after(0, lambda count=total_points: 
                        self.status_label.configure(text=f"🎯 Found {count} targets in {len(screenshots)} windows"))
                else:
                    self.root.after(0, lambda: 
                        self.status_label.configure(text=f"🔍 Searching {self.target_name} in {len(screenshots)} windows"))
                
                # Performance monitoring
                frame_time = time.time() - frame_start
                frame_times.append(frame_time)
                if len(frame_times) > max_frame_samples:
                    frame_times.pop(0)
                
                # Dynamic sleep based on performance
                avg_frame_time = sum(frame_times) / len(frame_times)
                if avg_frame_time < 0.05:
                    time.sleep(0.08)
                elif avg_frame_time > 0.2:
                    time.sleep(0.05)
                else:
                    time.sleep(0.1)
                
            except Exception as e:
                self.root.after(0, lambda err=str(e): 
                    self.status_label.configure(text=f"❌ Error: {err}"))
                print(f"Bot loop error: {e}")
                time.sleep(0.2)

    def send_click_notification(self, x, y):
        """Send notification when target is clicked - Enhanced for multi-window"""
        if not self.discord_webhook:
            return
        
        def send_notification_thread():
            try:
                username = self.user_data.username if self.user_data else "Unknown"
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # ดึงข้อมูล Chrome windows
                chrome_count = self.windows.get_chrome_count()
                
                success = self.discord_webhook.send_embed(
                    title="🎯 Target Found & Clicked",
                    description=f"Found and clicked {self.target_name}",
                    color=0x00ffff,
                    fields=[
                        {"name": "User", "value": username, "inline": True},
                        {"name": "Target", "value": self.target_name, "inline": True},
                        {"name": "Position", "value": f"{x}, {y}", "inline": True},
                        {"name": "Total Clicks", "value": str(self.total_clicks), "inline": True},
                        {"name": "Chrome Windows", "value": str(chrome_count), "inline": True},
                        {"name": "Runtime", "value": self.get_runtime_string(), "inline": True},
                        {"name": "Time", "value": current_time, "inline": False}
                    ]
                )
                
            except Exception as e:
                print(f"Click notification failed: {e}")
        
        threading.Thread(target=send_notification_thread, daemon=True).start()

    def update_runtime(self):
        """Update runtime display with Chrome window count"""
        if self.running and self.start_time:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            # ดูจำนวน Chrome windows
            chrome_count = self.windows.get_chrome_count()
            
            self.runtime_label.configure(text=f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d} | Chrome: {chrome_count}")
            
            if self.last_screenshot_time:
                time_since_last = time.time() - self.last_screenshot_time
                time_until_next = self.screenshot_interval - time_since_last
                if time_until_next > 0:
                    hours_next = int(time_until_next // 3600)
                    minutes_next = int((time_until_next % 3600) // 60)
                    seconds_next = int(time_until_next % 60)
                    self.screenshot_timer_label.configure(text=f"Next screenshot: {hours_next:02d}:{minutes_next:02d}:{seconds_next:02d}")
                else:
                    self.screenshot_timer_label.configure(text="Next screenshot: Soon...")
            
            self.root.after(1000, self.update_runtime)

    def on_closing(self):
        """Handle window closing"""
        if self.running:
            self.stop_bot()
        self.root.destroy()
        if self.parent_root:
            self.parent_root.deiconify()

    def run(self):
        """Start GUI"""
        self.root.mainloop()
# =============================|
# Toast Notification Class     |
# =============================|

class ToastNotification:
    def __init__(self, parent):
        self.parent = parent
        
    def show_toast(self, message, toast_type="info", duration=3000):
        """Show toast notification
        toast_type: success, error, warning, info
        duration: milliseconds
        """
        # สีและไอคอนสำหรับแต่ละประเภท
        colors = {
            "success": {"bg": "#28a745", "text": "#ffffff", "icon": "✅"},
            "error": {"bg": "#dc3545", "text": "#ffffff", "icon": "❌"},
            "warning": {"bg": "#ffc107", "text": "#000000", "icon": "⚠️"},
            "info": {"bg": "#17a2b8", "text": "#ffffff", "icon": "ℹ️"}
        }
        
        color_config = colors.get(toast_type, colors["info"])
        
        # สร้าง toast window
        toast = ctk.CTkToplevel(self.parent)
        toast.title("")
        toast.geometry("250x60")
        toast.resizable(False, False)
        toast.overrideredirect(True)  # ซ่อน title bar
        toast.attributes("-topmost", True)  # แสดงด้านบนสุด
        
        # วางตำแหน่งที่เหมาะสม
        self.parent.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 110
        y = self.parent.winfo_y() + 50
        toast.geometry(f"250x60+{x}+{y}")
        
        # สร้างเนื้อหา toast
        main_frame = ctk.CTkFrame(toast, 
                                 fg_color=color_config["bg"], 
                                 corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Icon และ message
        icon_label = ctk.CTkLabel(content_frame, 
                                 text=color_config["icon"], 
                                 font=ctk.CTkFont(size=20))
        icon_label.pack(side="left", padx=(0, 10))
        
        message_label = ctk.CTkLabel(content_frame, 
                                   text=message, 
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   text_color=color_config["text"],
                                   wraplength=250)
        message_label.pack(side="left", fill="both", expand=True)
        
        # Close button
        close_btn = ctk.CTkLabel(content_frame, 
                               text="×", 
                               font=ctk.CTkFont(size=16, weight="bold"),
                               text_color=color_config["text"],
                               cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: toast.destroy())
        
        # Animation และ auto close
        self.animate_toast(toast, duration)
        
        return toast
    
    def animate_toast(self, toast, duration):
        """Animate toast appearance and disappearance"""
        # Fade in animation
        toast.attributes("-alpha", 0.0)
        
        def fade_in(alpha=0.0):
            if alpha < 1.0:
                alpha += 0.1
                toast.attributes("-alpha", alpha)
                toast.after(50, lambda: fade_in(alpha))
            else:
                # Auto close after duration
                toast.after(duration, lambda: self.fade_out_and_close(toast))
        
        fade_in()
    
    def fade_out_and_close(self, toast):
        """Fade out animation before closing"""
        def fade_out(alpha=1.0):
            if alpha > 0.0:
                alpha -= 0.1
                toast.attributes("-alpha", alpha)
                toast.after(50, lambda: fade_out(alpha))
            else:
                toast.destroy()
        
        fade_out()

# =============================|
# SweetAlert Style Dialog      |
# =============================|

class SweetAlert:
    def __init__(self, parent):
        self.parent = parent
    
    def show_alert(self, title, message, alert_type="info", confirm_text="ตกลง", cancel_text=None):
        """Show SweetAlert style dialog
        alert_type: success, error, warning, info, question
        Returns: True if confirmed, False if cancelled
        """
        self.result = None
        
        # สีและไอคอนสำหรับแต่ละประเภท
        configs = {
            "success": {"color": "#28a745", "icon": "✅", "icon_bg": "#d4edda"},
            "error": {"color": "#dc3545", "icon": "❌", "icon_bg": "#f8d7da"},
            "warning": {"color": "#ffc107", "icon": "⚠️", "icon_bg": "#fff3cd"},
            "info": {"color": "#17a2b8", "icon": "ℹ️", "icon_bg": "#d1ecf1"},
            "question": {"color": "#6f42c1", "icon": "❓", "icon_bg": "#e2d9f3"}
        }
        
        config = configs.get(alert_type, configs["info"])
        
        # สร้าง dialog
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # วางตำแหน่งกลางหน้าจอ
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 150
        dialog.geometry(f"400x300+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog, fg_color="#ffffff", corner_radius=15)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Icon circle
        icon_frame = ctk.CTkFrame(main_frame, 
                                 fg_color=config["icon_bg"], 
                                 corner_radius=50,
                                 width=80, height=80)
        icon_frame.pack(pady=(30, 20))
        
        icon_label = ctk.CTkLabel(icon_frame, 
                                 text=config["icon"], 
                                 font=ctk.CTkFont(size=30))
        icon_label.pack(expand=True)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, 
                                  text=title, 
                                  font=ctk.CTkFont(size=18, weight="bold"),
                                  text_color="#333333")
        title_label.pack(pady=(0, 10))
        
        # Message
        message_label = ctk.CTkLabel(main_frame, 
                                    text=message, 
                                    font=ctk.CTkFont(size=12),
                                    text_color="#666666",
                                    wraplength=320)
        message_label.pack(pady=(0, 30))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 20))
        
        def on_confirm():
            self.result = True
            dialog.destroy()
        
        def on_cancel():
            self.result = False
            dialog.destroy()
        
        if cancel_text:
            # Show both confirm and cancel buttons
            cancel_btn = ctk.CTkButton(button_frame, 
                                     text=cancel_text, 
                                     command=on_cancel,
                                     width=120, height=35,
                                     fg_color="#6c757d")
            cancel_btn.pack(side="left", padx=5)
            
            confirm_btn = ctk.CTkButton(button_frame, 
                                      text=confirm_text, 
                                      command=on_confirm,
                                      width=120, height=35,
                                      fg_color=config["color"])
            confirm_btn.pack(side="right", padx=5)
        else:
            # Show only confirm button
            confirm_btn = ctk.CTkButton(button_frame, 
                                      text=confirm_text, 
                                      command=on_confirm,
                                      width=150, height=35,
                                      fg_color=config["color"])
            confirm_btn.pack()
        
        # เพิ่ม animation
        dialog.attributes("-alpha", 0.0)
        def fade_in(alpha=0.0):
            if alpha < 1.0:
                alpha += 0.1
                dialog.attributes("-alpha", alpha)
                dialog.after(30, lambda: fade_in(alpha))
        
        fade_in()
        
        # รอผลลัพธ์
        dialog.wait_window()
        return self.result
# =============================|
# KeyAuth GUI Class            |
# =============================|

class KeyAuthGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.toast = ToastNotification(self.root)
        self.sweet_alert = SweetAlert(self.root)
        self.root.title("Login")
        self.root.geometry("400x400")
        self.root.resizable(False, False)
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 250
        self.root.geometry(f'400x450+{x}+{y}')
        
        self.user_data = None
        self.current_frame = None
        self.init_keyauth()
        self.show_login_frame()

    def init_keyauth(self):
        """Initialize KeyAuth with proper error handling"""
        try:
            def getchecksum():
                md5_hash = hashlib.md5()
                try:
                    with open(sys.argv[0], "rb") as file:
                        md5_hash.update(file.read())
                    return md5_hash.hexdigest()
                except:
                    return "default_hash"
                
            self.keyauthapp = api(
                name="SEXY-GAME",
                ownerid="WViBkkZ5dX", 
                version="1.0",
                hash_to_check=getchecksum()
            )
            
        except KeyAuthInitException as e:
            messagebox.showerror("KeyAuth Init Error", str(e))
            sys.exit(1)
        except Exception as e:
            messagebox.showerror("Error", f"KeyAuth init failed: {e}")
            sys.exit(1)

    def clear_frame(self):
        """Clear current frame"""
        if self.current_frame:
            self.current_frame.destroy()

    def show_login_frame(self):
        """Show login interface"""
        self.clear_frame()
        
        self.current_frame = ctk.CTkFrame(self.root)
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.current_frame, 
                     text="Login", 
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 30))
        
        self.username_entry = ctk.CTkEntry(self.current_frame, 
                                          placeholder_text="Username", 
                                          width=280, height=40)
        self.username_entry.pack(pady=8)
        
        self.password_entry = ctk.CTkEntry(self.current_frame, 
                                          placeholder_text="Password", 
                                          show="*", 
                                          width=280, height=40)
        self.password_entry.pack(pady=8)
        self.password_entry.bind('<Return>', lambda e: self.login_user())
        
        button_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, 
                     text="เข้าสู่ระบบ", 
                     command=self.login_user, 
                     width=130, height=40, 
                     fg_color="#007bff").pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, 
                     text="สมัครสมาชิก", 
                     command=self.show_register_frame, 
                     width=130, height=40, 
                     fg_color="#28a745").pack(side="right", padx=5)

    def show_register_frame(self):
        """Show register interface"""
        self.clear_frame()
        
        self.current_frame = ctk.CTkFrame(self.root)
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self.current_frame, 
                     text="สมัครสมาชิก", 
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(20, 30))
        
        self.reg_username_entry = ctk.CTkEntry(self.current_frame, 
                                              placeholder_text="Username", 
                                              width=280, height=40)
        self.reg_username_entry.pack(pady=8)
        
        self.reg_password_entry = ctk.CTkEntry(self.current_frame, 
                                              placeholder_text="Password", 
                                              show="*", 
                                              width=280, height=40)
        self.reg_password_entry.pack(pady=8)
        
        self.reg_confirm_password_entry = ctk.CTkEntry(self.current_frame, 
                                                      placeholder_text="Confirm Password", 
                                                      show="*", 
                                                      width=280, height=40)
        self.reg_confirm_password_entry.pack(pady=8)
        
        self.reg_license_entry = ctk.CTkEntry(self.current_frame, 
                                             placeholder_text="License Key", 
                                             width=280, height=40)
        self.reg_license_entry.pack(pady=8)
        self.reg_license_entry.bind('<Return>', lambda e: self.register_user())
        
        button_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, 
                     text="สมัครสมาชิก", 
                     command=self.register_user, 
                     width=130, height=40, 
                     fg_color="#28a745").pack(side="left", padx=5)
        
        ctk.CTkButton(button_frame, 
                     text="กลับหน้าล็อกอิน", 
                     command=self.show_login_frame, 
                     width=130, height=40, 
                     fg_color="#6c757d").pack(side="right", padx=5)

    def login_user(self):
        """Login user with proper exception handling"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.toast.show_toast("กรุณากรอกชื่อผู้ใช้และรหัสผ่าน", "warning")
            return
            
        # แสดง loading toast
        loading_toast = self.toast.show_toast("กำลังเข้าสู่ระบบ...", "info", 10000)
        
        def login_thread():
            try:
                self.keyauthapp.login(username, password)
                self.user_data = self.keyauthapp.user_data
                
                # ปิด loading toast
                self.root.after(0, lambda: loading_toast.destroy() if loading_toast.winfo_exists() else None)
                
                # แสดง success notification
                self.root.after(0, lambda: self.toast.show_toast("เข้าสู่ระบบสำเร็จ!", "success"))
                
                # เปิดโปรแกรมหลัง 1 วินาที
                self.root.after(1000, self.launch_bot)
                
            except KeyAuthLoginException as e:
                # ปิด loading toast
                self.root.after(0, lambda: loading_toast.destroy() if loading_toast.winfo_exists() else None)
                
                # แสดง error toast แต่ไม่ปิดโปรแกรม
                self.root.after(0, lambda msg=str(e): self.toast.show_toast(msg, "error"))
                
            except KeyAuthHWIDException as e:
                # ปิด loading toast
                self.root.after(0, lambda: loading_toast.destroy() if loading_toast.winfo_exists() else None)
                
                # แสดง HWID error
                self.root.after(0, lambda: self.sweet_alert.show_alert(
                    "HWID ไม่ตรงกัน", 
                    "เครื่องคอมพิวเตอร์ไม่ตรงกับที่ลงทะเบียนไว้\nกรุณาติดต่อผู้ดูแลระบบ", 
                    "error"
                ))
                
            except KeyAuthException as e:
                # ปิด loading toast
                self.root.after(0, lambda: loading_toast.destroy() if loading_toast.winfo_exists() else None)
                
                # แสดง general error
                error_msg = str(e)
                self.root.after(0, lambda: self.sweet_alert.show_alert(
                    "เกิดข้อผิดพลาด", 
                    f"ไม่สามารถเข้าสู่ระบบได้\n{error_msg}", 
                    "error"
                ))
                
            except Exception as e:
                # ปิด loading toast
                self.root.after(0, lambda: loading_toast.destroy() if loading_toast.winfo_exists() else None)
                
                # แสดง unexpected error
                self.root.after(0, lambda: self.sweet_alert.show_alert(
                    "เกิดข้อผิดพลาดที่ไม่คาดคิด", 
                    f"กรุณาลองใหม่อีกครั้ง\n{str(e)}", 
                    "error"
                ))
        
        threading.Thread(target=login_thread, daemon=True).start()
    def register_user(self):
        """Register user with enhanced notifications"""
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get().strip()
        confirm_password = self.reg_confirm_password_entry.get().strip()
        license_key = self.reg_license_entry.get().strip()
        
        if not all([username, password, confirm_password, license_key]):
            self.toast.show_toast("กรุณากรอกข้อมูลให้ครบทุกช่อง", "warning")
            return
        
        if password != confirm_password:
            self.toast.show_toast("รหัสผ่านไม่ตรงกัน", "error")
            return
        
        if len(password) < 6:
            self.toast.show_toast("รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร", "warning")
            return
            
        # แสดง loading toast
        loading_toast = self.toast.show_toast("กำลังสมัครสมาชิก...", "info", 10000)
        
        def register_thread():
            try:
                self.keyauthapp.register(username, password, license_key)
                self.user_data = self.keyauthapp.user_data
                
                # ปิด loading toast
                self.root.after(0, lambda: loading_toast.destroy() if loading_toast.winfo_exists() else None)
                
                # แสดง success notification
                self.root.after(0, lambda: self.sweet_alert.show_alert(
                    "สมัครสมาชิกสำเร็จ", 
                    "ยินดีต้อนรับ! บัญชีของคุณถูกสร้างเรียบร้อยแล้ว", 
                    "success"
                ))
                
                # เปิดโปรแกรมหลัง 1 วินาที
                self.root.after(1000, self.launch_bot)
                
            except Exception as e:
                error_msg = str(e)
                
                # ปิด loading toast
                self.root.after(0, lambda: loading_toast.destroy() if loading_toast.winfo_exists() else None)
                
                # จัดการข้อผิดพลาดแต่ละประเภท
                if "username already exists" in error_msg.lower():
                    self.root.after(0, lambda: self.toast.show_toast("ชื่อผู้ใช้นี้ถูกใช้งานแล้ว", "error"))
                elif "invalid license" in error_msg.lower() or "license" in error_msg.lower():
                    self.root.after(0, lambda: self.sweet_alert.show_alert(
                        "License Key ไม่ถูกต้อง", 
                        "รหัส License ที่กรอกไม่ถูกต้องหรือถูกใช้งานแล้ว", 
                        "error"
                    ))
                else:
                    self.root.after(0, lambda: self.sweet_alert.show_alert(
                        "สมัครสมาชิกไม่สำเร็จ", 
                        f"ไม่สามารถสมัครสมาชิกได้\n{error_msg}", 
                        "error"
                    ))
        
        threading.Thread(target=register_thread, daemon=True).start()

    def launch_bot(self):
        """Launch SA Gaming Bot"""
        try:
            bot = SAGamingBot(user_data=self.user_data, parent_root=self.root, keyauth_app=self.keyauthapp)
            self.root.withdraw()
            bot.run()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch bot: {e}")
            self.root.deiconify()

    def run(self):
        """Start GUI"""
        self.root.mainloop()

# =============================|
# Main Execution               |
# =============================|

if __name__ == "__main__":
    app = KeyAuthGUI()
    app.run()