import win32api, win32gui, win32con
from keyboardData import VK_CODE
from time import sleep

class Click:
    def __init__(self, windowsname=None):
        self.windowsname = windowsname

    def gethwid(self):
        hwid = win32gui.FindWindow('LDPlayerMainFrame', self.windowsname)
        childs = win32gui.FindWindowEx(hwid, None, 'RenderWindow', 'TheRender')
        return childs
    
    def getfirefoxid(self):
        hwid = win32gui.FindWindow('MozillaWindowClass', self.windowsname)
        return hwid
    
    def getchromeid(self):
        hwid = win32gui.FindWindow('Chrome_WidgetWin_1', self.windowsname)
        return hwid

    def control_click(self, hwid, x, y):
        l_param = win32api.MAKELONG(x, y)
        win32gui.SendMessage(hwid, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        win32gui.SendMessage(hwid, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, l_param)
    def get_all_chrome_hwids(self):
        hwids = []
        def enum_windows_callback(hwnd, hwids):
            if win32gui.IsWindowVisible(hwnd):
                class_name = win32gui.GetClassName(hwnd)
                if class_name == 'Chrome_WidgetWin_1':
                    title = win32gui.GetWindowText(hwnd)
                    if 'Google Chrome' in title:
                        hwids.append(hwnd)
        win32gui.EnumWindows(enum_windows_callback, hwids)
        return hwids
    
        
    def control_click_all_chrome(self, x, y):
        chrome_hwids = self.get_all_chrome_hwids()
        if not chrome_hwids:
            print("No Chrome windows found.")
            return
        for hwid in chrome_hwids:
            self.control_click(hwid, x, y)
            print(f"Clicked at ({x}, {y}) in Chrome window {hwid}")
    def control_click_with_info(self, hwid, x, y):
        """คลิกพร้อมแสดงข้อมูล Chrome window"""
        try:
            window_title = win32gui.GetWindowText(hwid)
            l_param = win32api.MAKELONG(x, y)
            win32gui.SendMessage(hwid, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
            win32gui.SendMessage(hwid, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, l_param)
            print(f"✅ Clicked at ({x}, {y}) in Chrome: {window_title[:50]}...")
            return True
        except Exception as e:
            print(f"❌ Click failed for Chrome {hwid}: {e}")
            return False

    def get_chrome_windows_info(self):
        """ดูข้อมูล Chrome windows ทั้งหมด"""
        chrome_info = []
        hwids = self.get_all_chrome_hwids()
        
        for hwid in hwids:
            try:
                title = win32gui.GetWindowText(hwid)
                rect = win32gui.GetWindowRect(hwid)
                is_visible = win32gui.IsWindowVisible(hwid)
                chrome_info.append({
                    'hwid': hwid,
                    'title': title,
                    'rect': rect,
                    'visible': is_visible
                })
            except Exception as e:
                print(f"Error getting info for Chrome {hwid}: {e}")
        
        return chrome_info

    def control_click_debug_mode(self, x, y):
        """คลิกแบบ debug - แสดงข้อมูลแต่ละ Chrome"""
        chrome_hwids = self.get_all_chrome_hwids()
        if not chrome_hwids:
            print("❌ No Chrome windows found.")
            return 0
        
        success_count = 0
        print(f"🎯 Clicking at ({x}, {y}) in {len(chrome_hwids)} Chrome windows:")
        
        for i, hwid in enumerate(chrome_hwids, 1):
            try:
                window_title = win32gui.GetWindowText(hwid)
                if self.control_click_with_info(hwid, x, y):
                    success_count += 1
                print(f"  {i}. Chrome {hwid}: {window_title[:30]}... ✅")
            except Exception as e:
                print(f"  {i}. Chrome {hwid}: Error - {e} ❌")
        
        print(f"📊 Successfully clicked in {success_count}/{len(chrome_hwids)} Chrome windows")
        return success_count
    def send_key(self, hwid, key):
        keycode = VK_CODE[key]
        win32api.SendMessage(hwid, win32con.WM_KEYDOWN, keycode, 0)
        win32api.SendMessage(hwid, win32con.WM_KEYUP, keycode, 0)
        
    def send_input(self, hwid, msg):
        for c in msg:
            if c == "\n":
                win32api.SendMessage(hwid, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                win32api.SendMessage(hwid, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
            else:
                win32api.SendMessage(hwid, win32con.WM_CHAR, ord(c), 0)   
            
    def drag_and_drop(self, hwid, start_pos, end_pos):
        WM_LBUTTONDOWN = 0x0201
        WM_LBUTTONUP = 0x0202
        WM_MOUSEMOVE = 0x0200
        start_x, start_y = start_pos
        end_x, end_y = end_pos
        start_point = win32api.MAKELONG(start_x, start_y)
        end_point = win32api.MAKELONG(end_x, end_y)
        win32api.PostMessage(hwid, WM_LBUTTONDOWN, win32con.MK_LBUTTON, start_point)
        win32api.PostMessage(hwid, WM_MOUSEMOVE, 0, end_point)
        win32api.PostMessage(hwid, WM_LBUTTONUP, 0, end_point)

    def click_and_hold(self, hwid, position, hold_duration=0.1):
        WM_LBUTTONDOWN = 0x0201
        WM_LBUTTONUP = 0x0202
        x, y = position
        point = win32api.MAKELONG(x, y)
        win32api.PostMessage(hwid, WM_LBUTTONDOWN, win32con.MK_LBUTTON, point)
        
    def click_hold_and_move(self, hwid, start_position, end_position, hold_duration):
        WM_LBUTTONDOWN = 0x0201
        WM_LBUTTONUP = 0x0202
        WM_MOUSEMOVE = 0x0200
        start_x, start_y = start_position
        end_x, end_y = end_position
        start_point = win32api.MAKELONG(start_x, start_y)
        end_point = win32api.MAKELONG(end_x, end_y)
        win32api.PostMessage(hwid, WM_LBUTTONDOWN, win32con.MK_LBUTTON, start_point)
        dx = end_x - start_x
        dy = end_y - start_y
        num_steps = max(abs(dx), abs(dy))
        delay = hold_duration / num_steps
        for step in range(1, num_steps + 1):
            x = start_x + int(dx * step / num_steps)
            y = start_y + int(dy * step / num_steps)
            point = win32api.MAKELONG(x, y)
            win32api.PostMessage(hwid, WM_MOUSEMOVE, 0, point)
            sleep(delay)
        win32api.PostMessage(hwid, WM_LBUTTONUP, 0, end_point)
        # เพิ่มฟังก์ชันเหล่านี้ในคลาส Click

    def control_click_specific_window(self, hwnd, x, y):
        """คลิกในหน้าต่างที่ระบุ hwnd"""
        try:
            # ตรวจสอบว่าหน้าต่างยังมีอยู่และมองเห็นได้
            if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
                return False
                
            l_param = win32api.MAKELONG(x, y)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, l_param)
            return True
            
        except Exception as e:
            print(f"Error clicking in window {hwnd}: {e}")
            return False

    def get_window_info(self, hwnd):
        """ดูข้อมูลหน้าต่าง"""
        try:
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            is_visible = win32gui.IsWindowVisible(hwnd)
            
            return {
                'hwnd': hwnd,
                'title': title,
                'rect': rect,
                'class_name': class_name,
                'visible': is_visible,
                'width': rect[2] - rect[0],
                'height': rect[3] - rect[1]
            }
        except Exception as e:
            print(f"Error getting window info: {e}")
            return None

    def control_click_all_chrome_enhanced(self, x, y, debug=False):
        """คลิกทุก Chrome แบบปรับปรุง"""
        chrome_hwids = self.get_all_chrome_hwids()
        if not chrome_hwids:
            if debug:
                print("❌ No Chrome windows found.")
            return 0
        
        success_count = 0
        failed_count = 0
        
        if debug:
            print(f"🎯 Clicking at ({x}, {y}) in {len(chrome_hwids)} Chrome windows:")
        
        for i, hwnd in enumerate(chrome_hwids, 1):
            try:
                # ดูข้อมูลหน้าต่าง
                window_info = self.get_window_info(hwnd)
                if not window_info:
                    failed_count += 1
                    continue
                
                # ตรวจสอบว่าหน้าต่างพร้อมใช้งาน
                if not window_info['visible'] or window_info['width'] <= 0 or window_info['height'] <= 0:
                    if debug:
                        print(f"  {i}. Chrome {hwnd}: Not visible or invalid size ⚠️")
                    failed_count += 1
                    continue
                
                # คลิก
                if self.control_click_specific_window(hwnd, x, y):
                    success_count += 1
                    if debug:
                        title = window_info['title'][:30] + "..." if len(window_info['title']) > 30 else window_info['title']
                        print(f"  {i}. Chrome {hwnd}: {title} ✅")
                else:
                    failed_count += 1
                    if debug:
                        print(f"  {i}. Chrome {hwnd}: Click failed ❌")
                    
            except Exception as e:
                failed_count += 1
                if debug:
                    print(f"  {i}. Chrome {hwnd}: Error - {e} ❌")
        
        if debug:
            print(f"📊 Results: {success_count} successful, {failed_count} failed")
        
        return success_count

    def get_chrome_windows_detailed(self):
        """ดูข้อมูล Chrome windows แบบละเอียด"""
        chrome_hwids = self.get_all_chrome_hwids()
        detailed_info = []
        
        for hwnd in chrome_hwids:
            info = self.get_window_info(hwnd)
            if info:
                detailed_info.append(info)
        
        return detailed_info

    def test_chrome_connectivity(self):
        """ทดสอบการเชื่อมต่อกับ Chrome windows"""
        print("🔍 Testing Chrome window connectivity...")
        
        chrome_info = self.get_chrome_windows_detailed()
        
        if not chrome_info:
            print("❌ No Chrome windows found!")
            return False
        
        print(f"📊 Found {len(chrome_info)} Chrome windows:")
        
        for i, info in enumerate(chrome_info, 1):
            status = "✅ Ready" if info['visible'] and info['width'] > 0 and info['height'] > 0 else "⚠️ Not ready"
            title = info['title'][:40] + "..." if len(info['title']) > 40 else info['title']
            print(f"  {i}. {info['hwnd']} - {title} ({info['width']}x{info['height']}) {status}")
        
        ready_count = sum(1 for info in chrome_info if info['visible'] and info['width'] > 0 and info['height'] > 0)
        print(f"📈 {ready_count}/{len(chrome_info)} windows are ready for clicking")
        
        return ready_count > 0