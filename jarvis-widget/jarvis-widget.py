#!/usr/bin/env python3
"""
JARVIS SYSTEM WIDGET — ARC REACTOR EDITION
Full-screen 16:9 HUD. Everything painted on main window, title bar drawn in paintEvent.
"""

import sys, time, math, subprocess, requests, psutil
from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import (QPainter, QPen, QColor, QFont,
                          QRadialGradient, QLinearGradient, QIcon)

# ─── DISPLAY ─────────────────────────────────────────────────────────────────
DW, DH = 1920, 1080   # Designed drawing dimensions
CX, CY = DW // 2, DH // 2
TITLE_H = 50   # title bar height

# ─── COLORS ───────────────────────────────────────────────────────────────────
BG         = QColor(5, 2, 15)
ACCENT     = QColor(0, 210, 255)
ACCENT2    = QColor(0, 140, 200)
PURPLE     = QColor(138, 43, 226)
WHITE      = QColor(220, 240, 255)
DIM        = QColor(70, 110, 170)
PANEL_BG   = QColor(8, 4, 28, 200)
GREEN      = QColor(50, 220, 120)
YELLOW     = QColor(255, 200, 50)
ORANGE     = QColor(255, 130, 30)
RED        = QColor(255, 60, 60)
FONT_MAIN  = "Courier New"
REFRESH_S  = 2

# ─── DATA HELPERS ─────────────────────────────────────────────────────────────
def c_to_f(c):
    return round(c * 9/5 + 32) if c is not None else None

def get_gpu_info():
    try:
        out = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name,temperature.gpu,utilization.gpu',
             '--format=csv,noheader,nounits'], stderr=subprocess.DEVNULL).decode()
        name, temp, util = out.strip().split(', ')
        return name.strip(), int(temp), int(util)
    except:
        return None, None, None

def get_cpu_temp_f():
    try:
        import glob
        temps = [int(open(z).read().strip()) / 1000.0
                 for z in glob.glob('/sys/class/thermal/thermal_zone*/temp')
                 if 20 < int(open(z).read().strip()) / 1000.0 < 110]
        return c_to_f(round(sum(temps) / len(temps)) if temps else None)
    except:
        return None

def get_weather_f():
    try:
        r = requests.get("https://wttr.in/Mill+Creek+WA?format=j1", timeout=6)
        d = r.json()['current_condition'][0]
        return (c_to_f(int(d['temp_C'])), d['weatherDesc'][0]['value'],
                int(d['humidity']), int(d['windspeedKmph']), c_to_f(int(d['FeelsLikeC'])))
    except:
        return None, "Unavailable", None, None, None

def get_drives():
    try:
        results = []
        skip_paths = ['/boot/efi', '/boot', '/efi', '/snap', '/cow', '/run']
        skip_fstypes = ['squashfs', 'overlay', 'tmpfs', 'devtmpfs', 'devpts',
                        'sysfs', 'proc', 'cgroup', 'securityfs', 'pstore',
                        'efivarfs', 'binfmt_misc']
        for p in psutil.disk_partitions():
            # Skip non-real disks
            if p.fstype.lower() in skip_fstypes:
                continue
            if any(s in p.mountpoint.lower() for s in skip_paths):
                continue
            if 'loop' in p.device:
                continue
            if p.mountpoint == '/' or 'ntfs' in p.fstype.lower() or 'fuseblk' in p.fstype.lower():
                pass  # include these
            # Only include real physical disks
            if not any(x in p.device for x in ['/dev/sd', '/dev/nvme', '/dev/hd']):
                continue
            try:
                u = psutil.disk_usage(p.mountpoint)
                # Skip partitions < 1GB or showing 0 total
                if u.total < 1 * (1024**3):
                    continue
                label = p.device.split('/')[-1].upper()
                results.append((label, round(u.total/(1024**3), 1),
                                round(u.used/(1024**3), 1),
                                u.used / u.total * 100 if u.total else 0))
            except:
                pass
        return results[:4]
    except:
        return []

def get_uptime():
    try:
        sec = time.time() - psutil.boot_time()
        h, r = divmod(int(sec), 3600)
        m, _ = divmod(r, 60)
        return f"{h}h {m}m"
    except:
        return "N/A"


# ─── JARVIS WINDOW ─────────────────────────────────────────────────────────────
class JarvisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('/home/jarvis/.openclaw/workspace/jarvis-widget/arc-reactor.png'))
        self.setWindowTitle("Jarvis Widget")
        # Size to available geometry so nothing gets covered
        desk = QApplication.desktop()
        ag = desk.availableGeometry()
        self.resize(ag.width(), ag.height())
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

        # Position at screen top-left — use full screen geometry so no border appears
        # availableGeometry() excludes panels/taskbars, screenGeometry() gives the full screen
        desk = QApplication.desktop()
        ag = desk.availableGeometry()
        # Center in available area
        win_w = self.width()
        win_h = self.height()
        x = ag.x() + (ag.width() - win_w) // 2
        y = ag.y() + (ag.height() - win_h) // 2
        self.move(x, y)

        self._drag = False
        self._drag_start = QPoint()
        self._angle = 0.0
        self._sub_angle = 0.0
        self._data = {}
        self._drives = []
        self._painting = False
        self._ready = False
        self._maximized = False
        self._normal_geo = self.geometry()

        # ── Window control buttons (real Qt widgets) ─────────────────────────
        btn_style = f"""
            QPushButton {{
                background: rgba(0, 140, 200, 40);
                border: 1px solid rgba(0, 180, 220, 100);
                color: rgba(0, 210, 255, 200);
                border-radius: 5px;
                padding: 2px 14px;
                font-family: '{FONT_MAIN}';
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(0, 210, 255, 80);
                color: white;
            }}
        """
        btn_close_style = f"""
            QPushButton {{
                background: rgba(180, 30, 30, 70);
                border: 1px solid rgba(220, 60, 60, 140);
                color: rgba(255, 130, 130, 220);
                border-radius: 5px;
                padding: 2px 14px;
                font-family: '{FONT_MAIN}';
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(220, 50, 50, 180);
                color: white;
            }}
        """

        self._btn_min   = QPushButton("─", self)
        self._btn_max   = QPushButton("□", self)
        self._btn_close = QPushButton("✕", self)
        for btn in [self._btn_min, self._btn_max]:
            btn.setStyleSheet(btn_style)
            btn.setFixedSize(42, 30)
            btn.setAttribute(Qt.WA_TranslucentBackground, True)
        self._btn_close.setStyleSheet(btn_close_style)
        self._btn_close.setFixedSize(50, 30)
        self._btn_close.setAttribute(Qt.WA_TranslucentBackground, True)

        self._btn_min.clicked.connect(self.showMinimized)
        self._btn_max.clicked.connect(self._toggle_max)
        self._btn_close.clicked.connect(QApplication.quit)

        # Position buttons in title bar area
        self._update_btn_positions()

        # Start after show
        QTimer.singleShot(100, self._first_paint)

    def _update_btn_positions(self):
        w = self.width()
        self._btn_min.move(w - 150, 10)
        self._btn_max.move(w - 100, 10)
        self._btn_close.move(w - 48, 10)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_btn_positions()

    def _toggle_max(self):
        desk = QApplication.desktop()
        ag = desk.availableGeometry()
        if self._maximized:
            self.setGeometry(self._normal_geo)
            self._maximized = False
            self._btn_max.setText("□")
        else:
            self._normal_geo = self.geometry()
            # Maximize to available area (respects taskbar on all sides)
            self.resize(ag.width(), ag.height())
            x = ag.x() + (ag.width() - self.width()) // 2
            y = ag.y() + (ag.height() - self.height()) // 2
            self.move(x, y)
            self._maximized = True
            self._btn_max.setText("❐")

    def _first_paint(self):
        self._ready = True
        self._fetch_all()
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(35)
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self._fetch_all)
        self._data_timer.start(REFRESH_S * 1000)
        self.update()

    def _fetch_all(self):
        d = {}
        d['cpu'] = int(psutil.cpu_percent(interval=0.1))
        d['cpu_temp'] = get_cpu_temp_f()
        gname, gt, gu = get_gpu_info()
        d['gpu_name'] = gname or None
        d['gpu_temp'] = c_to_f(gt) if gt else None
        d['gpu_util'] = gu
        ram = psutil.virtual_memory()
        d['ram_total'] = ram.total / (1024**3)
        d['ram_used']  = ram.used  / (1024**3)
        d['uptime'] = get_uptime()
        tf, cond, hum, wind, feels = get_weather_f()
        d['temp_f'] = tf; d['condition'] = cond; d['humidity'] = hum
        d['wind'] = wind; d['feels_f'] = feels
        self._data = d
        self._drives = get_drives()
        if self._ready:
            self.update()

    def _animate(self):
        if self._painting or not self._ready:
            return
        self._angle     = (self._angle + 0.4) % 360
        self._sub_angle = (self._sub_angle + 0.15) % 360
        self.update()

    def paintEvent(self, e):
        if not self._ready:
            return
        if self._painting:
            return
        self._painting = True
        p = QPainter(self)
        if not p.isActive():
            self._painting = False
            return
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        # Scale drawing to fit actual window size
        sw = self.width()
        sh = self.height()
        sx = sw / DW
        sy = sh / DH
        p.scale(sx, sy)

        # Draw background + all HUD elements
        self._draw_all(p)

        # Draw title bar last (on top of everything)
        self._draw_title_bar(p)

        p.end()
        self._painting = False

    def _draw_title_bar(self, p):
        # Title bar background
        p.fillRect(0, 0, DW, TITLE_H, QColor(5, 2, 20, 235))
        # Bottom border
        p.setPen(QPen(QColor(0, 180, 220, 80), 1))
        p.drawLine(0, TITLE_H, DW, TITLE_H)
        # JARVIS title
        p.setFont(QFont(FONT_MAIN, 12, QFont.Bold))
        p.setPen(QPen(QColor(0, 210, 255, 200)))
        p.drawText(20, 0, DW - 180, TITLE_H, Qt.AlignVCenter | Qt.AlignLeft, "Jarvis Widget")

    # ─── Layout zones ─────────────────────────────────────────────────────────
    # Title bar:   y=0 to y=TITLE_H=50
    # Row 1 (y=60-230): CPU arc (left), ARC REACTOR (center), RAM arc (right)
    # Row 2 (y=240-380): GPU arc (left), WEATHER panel (right)
    # Row 3 (y=390-DH-170): TIME (center)
    # Bottom bar:  y=DH-170 to y=DH (storage + uptime)

    # ─── Draw ────────────────────────────────────────────────────────────
    def _draw_all(self, p):
        # Background
        p.fillRect(0, 0, DW, DH, BG)
        nb = QRadialGradient(CX, CY - 80, DH * 0.85)
        nb.setColorAt(0, QColor(40, 0, 60, 70))
        nb.setColorAt(0.6, QColor(20, 0, 35, 50))
        nb.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, DW, DH, nb)
        p.setPen(QColor(0, 150, 200, 10))
        for x in range(0, DW, 60):
            p.drawLine(x, 0, x, DH)
        for y in range(0, DH, 60):
            p.drawLine(0, y, DW, y)

        self._draw_row1_arcs(p)
        self._draw_row2(p)
        self._draw_time_date(p)
        self._draw_bottom_bar(p)
        self._draw_corners(p)

    def _draw_row1_arcs(self, p):
        d = self._data
        # Row 1 — evenly spaced: CPU(left) arc(920) RAM(right)
        ARC_Y = 155   # y center for row 1 elements

        # CPU arc gauge — left
        self._arc_gauge(p, 260, ARC_Y, 85,
                        d.get('cpu', 0)/100, "CPU",
                        f"{int(d.get('cpu',0))}%",
                        f"{d.get('cpu_temp','--')}°F" if d.get('cpu_temp') else "N/A",
                        ACCENT, QColor(0, 100, 180), False)

        # Arc reactor — center, above time
        self._draw_arc_reactor(p, CX, ARC_Y)

        # RAM arc gauge — right
        ram_t = d.get('ram_total', 1); ram_u = d.get('ram_used', 0)
        self._arc_gauge(p, DW-260, ARC_Y, 85,
                        ram_u/ram_t if ram_t else 0, "RAM",
                        f"{int(ram_u/ram_t*100)}%",
                        f"{ram_u:.0f}GB",
                        QColor(180,100,255), QColor(90,40,150), False)

    def _draw_row2(self, p):
        d = self._data
        ROW2_Y = 315   # y center for row 2 — below arc reactor (ends ~285)

        # Weather panel — right (moved right to avoid RAM overlap)
        self._weather_panel(p, DW-180, ROW2_Y, d)

        # Network stats — center area (between GPU and weather)
        try:
            net = psutil.net_io_counters()
            sent = net.bytes_sent / (1024**2); recv = net.bytes_recv / (1024**2)
            p.setFont(QFont(FONT_MAIN, 10)); p.setPen(QPen(DIM))
            p.drawText(CX-80, ROW2_Y-50, 160, 16, Qt.AlignHCenter, "NETWORK")
            p.setFont(QFont(FONT_MAIN, 11)); p.setPen(QPen(GREEN))
            p.drawText(CX-80, ROW2_Y-32, 80, 18, Qt.AlignHCenter, f"↑{sent:.0f}MB")
            p.setPen(QPen(ACCENT)); p.drawText(CX, ROW2_Y-32, 80, 18, Qt.AlignHCenter, f"↓{recv:.0f}MB")
        except: pass

        # GPU arc gauge — left
        if d.get('gpu_name'):
            self._arc_gauge(p, 260, ROW2_Y, 75,
                            (d.get('gpu_util') or 0)/100, "GPU",
                            f"{d.get('gpu_util','N/A')}%",
                            f"{d.get('gpu_temp','--')}°F" if d.get('gpu_temp') else "N/A",
                            ORANGE, QColor(150,60,0), False)
            p.setFont(QFont(FONT_MAIN, 8)); p.setPen(QPen(DIM))
            name = (d.get('gpu_name') or "N/A")[:24]
            p.drawText(260-100, ROW2_Y+80, 200, 14, Qt.AlignHCenter, name)

    def _draw_arc_reactor(self, p, cx, cy):
        a, sa = self._angle, self._sub_angle
        # Compact — bottom of reactor at cy+145, well above time at y=425
        for glow_r, glow_w, alpha in [(145, 30, 12), (132, 22, 18), (122, 16, 22)]:
            pen = QPen(QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), alpha), glow_w)
            p.setPen(pen)
            p.drawEllipse(QPoint(cx, cy), glow_r, glow_r)

        p.save(); p.translate(cx, cy); p.rotate(a)
        pen = QPen(ACCENT, 2); pen.setDashPattern([8, 5]); p.setPen(pen)
        p.drawEllipse(QPoint(0,0), 122, 122); p.restore()

        p.save(); p.translate(cx, cy); p.rotate(-sa * 1.3)
        pen = QPen(PURPLE, 1.5); pen.setDashPattern([6, 5]); p.setPen(pen)
        p.drawEllipse(QPoint(0,0), 112, 112); p.restore()

        p.save(); p.translate(cx, cy)
        p.setPen(QPen(QColor(ACCENT2.red(), ACCENT2.green(), ACCENT2.blue(), 60), 1))
        p.drawEllipse(QPoint(0,0), 105, 105)
        for i in range(36):
            ang = math.radians(i * 10)
            inn = 103 if i % 3 == 0 else 104
            x1 = math.cos(ang) * inn; y1 = math.sin(ang) * inn
            x2 = math.cos(ang) * 105; y2 = math.sin(ang) * 105
            p.drawLine(int(x1), int(y1), int(x2), int(y2))
        p.restore()

        for r, w, a in [(95, 12, 18), (88, 9, 28), (82, 7, 38)]:
            pen = QPen(QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), a), w)
            p.setPen(pen)
            p.drawEllipse(QPoint(cx, cy), r, r)

        p.save(); p.translate(cx, cy); p.rotate(a * 1.6)
        pen = QPen(ACCENT, 2); pen.setDashPattern([9, 5]); p.setPen(pen)
        p.drawEllipse(QPoint(0,0), 78, 78); p.restore()

        p.save(); p.translate(cx, cy); p.rotate(-sa * 0.9)
        pen = QPen(PURPLE, 1.5); pen.setDashPattern([7, 5]); p.setPen(pen)
        p.drawEllipse(QPoint(0,0), 70, 70); p.restore()

        cg = QRadialGradient(cx, cy, 45)
        cg.setColorAt(0, QColor(0, 200, 255, 90))
        cg.setColorAt(0.5, QColor(0, 100, 200, 40))
        cg.setColorAt(1, QColor(0, 50, 120, 0))
        p.fillRect(cx-45, cy-45, 90, 90, cg)

    def _draw_time_date(self, p):
        now = datetime.now()
        # Time — starts well below arc reactor bottom (y=300)
        p.setFont(QFont(FONT_MAIN, 68, QFont.Bold))
        p.setPen(QPen(ACCENT, 2))
        p.drawText(0, 320, DW, 75, Qt.AlignHCenter | Qt.AlignVCenter,
                   now.strftime("%H:%M"))
        p.setFont(QFont(FONT_MAIN, 18)); p.setPen(QPen(DIM))
        p.drawText(CX+105, 330, 55, 22, Qt.AlignLeft, now.strftime("%S"))
        p.drawText(CX+105, 350, 55, 18, Qt.AlignLeft, now.strftime("%p"))
        p.setFont(QFont(FONT_MAIN, 20)); p.setPen(QPen(WHITE))
        p.drawText(0, 395, DW, 28, Qt.AlignHCenter,
                   now.strftime("%A, %B %d, %Y").upper())
        day_sec = now.hour*3600 + now.minute*60 + now.second
        pct = day_sec / 86400
        bw = 280; bx = CX - bw//2; by2 = 430
        p.fillRect(bx, by2, bw, 5, QColor(20, 20, 50))
        clr = YELLOW if pct > 0.7 else GREEN
        p.fillRect(bx, by2, int(bw*pct), 5, clr)
        p.setFont(QFont(FONT_MAIN, 8)); p.setPen(QPen(DIM))
        p.drawText(bx-30, by2-2, "00:00"); p.drawText(bx+bw+5, by2-2, "24:00")
        p.drawText(bx+bw//2-18, by2+10, f"DAY {int(pct*100)}%")

    def _arc_gauge(self, p, cx, cy, r, pct, label, value, sub, color, color2, large=False):
        p.save(); p.translate(cx, cy)
        p.setPen(QPen(QColor(25,25,55), 8))
        p.drawArc(-r,-r,r*2,r*2, 30*16, 120*16)
        if pct > 0:
            p.setPen(QPen(color, 8))
            p.drawArc(-r,-r,r*2,r*2, 30*16, int(120*16*min(pct,1)))
        p.setPen(QPen(color, 1)); p.drawArc(-r-3,-r-3,(r+3)*2,(r+3)*2, 0, 360*16)
        vfs = 22 if large else 18; sfs = 10 if large else 9
        p.setFont(QFont(FONT_MAIN, 9)); p.setPen(QPen(DIM))
        p.drawText(-r, -r-12, r*2, 14, Qt.AlignHCenter, label)
        p.setFont(QFont(FONT_MAIN, vfs, QFont.Bold)); p.setPen(QPen(color))
        p.drawText(-r, -10, r*2, 26, Qt.AlignHCenter | Qt.AlignVCenter, value)
        p.setFont(QFont(FONT_MAIN, sfs)); p.setPen(QPen(color2))
        p.drawText(-r, 16, r*2, 14, Qt.AlignHCenter | Qt.AlignTop, sub)
        p.restore()

    def _weather_panel(self, p, cx, cy, d):
        pw, ph = 180, 130; px = cx - pw//2; py = cy - ph//2
        p.fillRect(px, py, pw, ph, PANEL_BG)
        p.setPen(QPen(ACCENT, 1)); p.drawRect(px, py, pw, ph)
        p.setFont(QFont(FONT_MAIN, 9)); p.setPen(QPen(DIM))
        p.drawText(px+12, py+12, "MILL CREEK, WA")
        tmp = f"{d.get('temp_f','--')}°F" if d.get('temp_f') else "--°F"
        p.setFont(QFont(FONT_MAIN, 36, QFont.Bold)); p.setPen(QPen(ACCENT))
        p.drawText(px+12, py+14, pw-24, 50, Qt.AlignLeft | Qt.AlignVCenter, tmp)
        fls = f"Feels {d.get('feels_f','--')}°" if d.get('feels_f') else ""
        p.setFont(QFont(FONT_MAIN, 9)); p.setPen(QPen(DIM))
        p.drawText(px+12, py+62, 80, 14, Qt.AlignLeft, fls)
        cond = d.get('condition', 'Loading...')[:20]
        p.setFont(QFont(FONT_MAIN, 9)); p.setPen(QPen(PURPLE))
        p.drawText(px+12, py+78, pw-24, 14, Qt.AlignLeft, cond)
        my = py + 98
        p.setFont(QFont(FONT_MAIN, 9)); p.setPen(QPen(DIM))
        p.drawText(px+12, my, "HUM"); p.drawText(px+65, my, "WIND")
        p.setFont(QFont(FONT_MAIN, 11, QFont.Bold)); p.setPen(QPen(ACCENT))
        hum = d.get('humidity'); wind = d.get('wind')
        p.drawText(px+12, my+12, f"{hum}%" if hum else "--%")
        p.drawText(px+65, my+12, f"{wind}mph" if wind else "--mph")

    def _draw_bottom_bar(self, p):
        # Bottom margin: 40px from window bottom
        by = DH - 140   # y start of bottom bar content
        # STORAGE: left-aligned, 3 bars stacked vertically
        # Layout: [NAME   ====BAR====] [PCT] [VALUE] per row
        drive_names = ['SSD', 'HDD', 'NVME', 'USB']
        p.setFont(QFont(FONT_MAIN, 11)); p.setPen(QPen(DIM))
        p.drawText(100, by-22, "STORAGE")

        # Bar: x=100, width=1150 → ends at x=1250
        # Gap between bars: 38px
        bw = 1150   # total bar section width
        bh = 16     # bar height
        bx = 100    # bar start x
        for i, (label, total, used, pct) in enumerate(self._drives[:3]):
            dy = by + i * 38
            name = drive_names[i] if i < len(drive_names) else label[:6]
            bar_color = GREEN if pct < 75 else YELLOW if pct < 90 else RED
            # Draw name label ABOVE the bar (to the left), not ON the bar
            p.setFont(QFont(FONT_MAIN, 10, QFont.Bold)); p.setPen(QPen(WHITE))
            p.drawText(bx, dy-2, f"  {name}")   # 2-char padding
            # Background bar
            p.fillRect(bx, dy+14, bw, bh, QColor(15,15,35))
            # Filled portion
            fw = int(bw * min(pct/100, 1.0))
            if fw > 0:
                grad = QLinearGradient(bx, dy+14, bx+fw, dy+14)
                grad.setColorAt(0, bar_color)
                grad.setColorAt(1, QColor(bar_color.red()//2, bar_color.green()//2, bar_color.blue()//2))
                p.fillRect(bx, dy+14, fw, bh, grad)
            # Segmented tick marks
            p.setPen(QColor(10,10,25,200))
            for t in range(1, 10):
                tx = bx + t*(bw//10); p.drawLine(tx, dy+14, tx, dy+14+bh)
            # Value text: right of bar
            p.setFont(QFont(FONT_MAIN, 10, QFont.Bold)); p.setPen(QPen(bar_color))
            p.drawText(bx+bw+8, dy+12, f"{int(pct)}%")
            p.setFont(QFont(FONT_MAIN, 9)); p.setPen(QPen(DIM))
            p.drawText(bx+bw+52, dy+12, f"{used:.0f}GB / {total:.0f}GB")

        # UPTIME: right side with proper right margin (40px)
        p.setFont(QFont(FONT_MAIN, 11)); p.setPen(QPen(DIM))
        p.drawText(1370, by-22, "UPTIME")
        p.setFont(QFont(FONT_MAIN, 14, QFont.Bold)); p.setPen(QPen(ACCENT))
        p.drawText(1370, by+5, self._data.get('uptime', '--'))

    def _draw_corners(self, p):
        cs = 40; p.setPen(QPen(ACCENT, 2))
        p.drawLine(20,20,20+cs,20);    p.drawLine(20,20,20,20+cs)
        p.drawLine(DW-20,20,DW-20-cs,20); p.drawLine(DW-20,20,DW-20,20+cs)
        p.drawLine(20,DH-20,20+cs,DH-20); p.drawLine(20,DH-20,20,DH-20-cs)
        p.drawLine(DW-20,DH-20,DW-20-cs,DH-20); p.drawLine(DW-20,DH-20,DW-20,DH-20-cs)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = True
            self._drag_start = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton and self._drag:
            self.move(e.globalPos() - self._drag_start)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag = False


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setQuitOnLastWindowClosed(False)
    w = JarvisWindow()
    w.show()
    sys.exit(app.exec_())
