import win32gui, win32ui, win32con
import numpy as np
from ctypes import windll

class WindowCapture:
    def __init__(self, window_name):
        self.window_name = window_name
        # ไม่ใช้ single hwnd แล้ว เปลี่ยนเป็นหาทุกหน้าต่าง Chrome
        self.chrome_hwnds = []
        self.update_chrome_windows()
    
    def update_chrome_windows(self):
        """อัพเดทรายการหน้าต่าง Chrome ทั้งหมด"""
        self.chrome_hwnds = []
        def enum_windows_callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd):
                class_name = win32gui.GetClassName(hwnd)
                if class_name == 'Chrome_WidgetWin_1':
                    title = win32gui.GetWindowText(hwnd)
                    if 'Google Chrome' in title or 'Chrome' in title:
                        hwnds.append(hwnd)
        
        win32gui.EnumWindows(enum_windows_callback, self.chrome_hwnds)
        print(f"Found {len(self.chrome_hwnds)} Chrome windows")
        return len(self.chrome_hwnds) > 0

    def screenshot_single_window(self, hwnd):
        """แคปหน้าจอหน้าต่างเดียว"""
        try:
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            w = right - left
            h = bottom - top
            
            # ตรวจสอบขนาดหน้าต่าง
            if w <= 0 or h <= 0:
                return None
                
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
            save_dc.SelectObject(bitmap)
            
            # ลองใช้ PrintWindow ก่อน
            result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)
            
            bmpinfo = bitmap.GetInfo()
            bmpstr = bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4))
            img = img[..., :3]  # ตัด alpha channel
            img = np.ascontiguousarray(img)
            
            # ทำความสะอาด
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            
            return img
            
        except Exception as e:
            print(f"Error capturing window {hwnd}: {e}")
            return None

    def screenshot(self):
        """แคปหน้าจอหน้าต่างแรกที่หาได้ (สำหรับ backward compatibility)"""
        # อัพเดทรายการหน้าต่างก่อน
        if not self.update_chrome_windows():
            print("No Chrome windows found")
            return None
        
        # ส่งกลับหน้าจอของหน้าต่างแรก
        return self.screenshot_single_window(self.chrome_hwnds[0])

    def screenshot_all_windows(self):
        """แคปหน้าจอทุกหน้าต่าง Chrome"""
        screenshots = []
        
        # อัพเดทรายการหน้าต่าง
        if not self.update_chrome_windows():
            return screenshots
        
        for i, hwnd in enumerate(self.chrome_hwnds):
            try:
                # ตรวจสอบว่าหน้าต่างยังมีอยู่
                if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
                    continue
                
                screenshot = self.screenshot_single_window(hwnd)
                if screenshot is not None:
                    screenshots.append({
                        'hwnd': hwnd,
                        'screenshot': screenshot,
                        'title': win32gui.GetWindowText(hwnd),
                        'index': i
                    })
                    
            except Exception as e:
                print(f"Failed to capture window {hwnd}: {e}")
                continue
        
        print(f"Successfully captured {len(screenshots)} Chrome windows")
        return screenshots

    def get_chrome_count(self):
        """ดูจำนวนหน้าต่าง Chrome"""
        self.update_chrome_windows()
        return len(self.chrome_hwnds)