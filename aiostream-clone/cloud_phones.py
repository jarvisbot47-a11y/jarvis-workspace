"""
Cloud Phones Module - Android Device Management via ADB
Manages cloud Android devices for account creation and streaming automation.
"""
import subprocess, threading, time, base64, json, os, socket
from datetime import datetime
from flask import request, jsonify, render_template
from emulator_manager import (
    list_avds, list_running_emulators, start_emulator, stop_emulator,
    stop_all_emulators, get_emulator_status, install_apk, screencap as emu_screencap,
    get_device_info as emu_get_device_info, launch_app as emu_launch_app,
    get_installed_apps as emu_get_installed_apps, _emulator_processes
)

# ─── ADB Helpers ──────────────────────────────────────────────────────────────

def get_adb_path():
    """Find ADB binary."""
    # Check common locations
    paths = ['adb', '/usr/bin/adb', '/opt/android-sdk/platform-tools/adb',
             '/home/jarvis/android-sdk/platform-tools/adb']
    for p in paths:
        try:
            result = subprocess.run([p, 'version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return p
        except:
            pass
    return 'adb'  # fallback to PATH

ADB = get_adb_path()

def run_adb(cmd, timeout=15):
    """Run an ADB command."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    try:
        result = subprocess.run([ADB] + cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return '', 'Timeout', -1
    except FileNotFoundError:
        return '', 'ADB not found', -1

def list_devices():
    """List all connected ADB devices."""
    stdout, stderr, code = run_adb('devices -l')
    devices = []
    if code == 0:
        for line in stdout.splitlines()[1:]:
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    state = parts[1]
                    device_info = {'serial': serial, 'state': state}
                    # Parse additional info
                    for p in parts[2:]:
                        if ':' in p:
                            k, v = p.split(':', 1)
                            device_info[k] = v
                    devices.append(device_info)
    return devices

def get_device_info(serial):
    """Get detailed device info."""
    stdout, _, code = run_adb(['-s', serial, 'shell', 'getprop'])
    if code != 0:
        return {}
    props = {}
    for line in stdout.splitlines():
        if ':' in line:
            try:
                # [ro.product.model]: [Pixel 6]
                parts = line.strip('[()]'.replace(' ', '')).split(']: [')
                if len(parts) == 2:
                    props[parts[0]] = parts[1]
            except:
                pass
    return props

def screencap(serial):
    """Capture screen as PNG, return base64."""
    stdout, stderr, code = run_adb(['-s', serial, 'exec-out', 'screencap', '-p'],
                                     timeout=10)
    if code == 0 and stdout:
        return base64.b64encode(stdout).decode()
    return None

def shell(serial, cmd, timeout=15):
    """Run shell command on device."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    stdout, stderr, code = run_adb(['-s', serial, 'shell'] + cmd, timeout=timeout)
    return stdout, stderr, code

def install_apk(serial, apk_path):
    """Install APK on device."""
    stdout, stderr, code = run_adb(['-s', serial, 'install', '-r', apk_path], timeout=60)
    return stdout, stderr, code

def tap(serial, x, y):
    """Tap at coordinates."""
    return shell(serial, f'input tap {x} {y}')

def swipe(serial, x1, y1, x2, y2, duration=300):
    """Swipe from (x1,y1) to (x2,y2)."""
    return shell(serial, f'input swipe {x1} {y1} {x2} {y2} {duration}')

def input_text(serial, text):
    """Input text (escaped)."""
    # Escape special characters
    text = text.replace(' ', '%s').replace("'", "\\'").replace('\\', '\\\\')
    return shell(serial, f'input text "{text}"')

def press_key(serial, keycode):
    """Press keycode (e.g. BACK, HOME, ENTER)."""
    return shell(serial, f'input keyevent {keycode}')

def start_activity(serial, package, activity=None):
    """Start an activity."""
    if activity:
        cmd = f'am start -n {package}/{activity}'
    else:
        cmd = f'am start -a android.intent.action.VIEW -n {package}'
    return shell(serial, cmd)

def dump_ui(serial):
    """Get UI hierarchy XML."""
    stdout, _, code = run_adb(['-s', serial, 'exec-out', 'uiautomator', 'dump', '/dev/fd/1'],
                               timeout=10)
    if code == 0 and stdout:
        try:
            return stdout.decode('utf-8', errors='ignore') if isinstance(stdout, bytes) else stdout
        except:
            return stdout
    return ""

def get_display_size(serial):
    """Get display dimensions."""
    stdout, _, _ = shell(serial, 'wm size')
    # Output: "Physical size: 1080x2340"
    if stdout and 'x' in stdout:
        try:
            size = stdout.split(':')[-1].strip()
            w, h = size.split('x')
            return int(w), int(h)
        except:
            pass
    return 1080, 2340

def get_device_model(serial):
    """Get device model name."""
    model, _, _ = shell(serial, 'getprop ro.product.model')
    return model.strip() if model else 'Unknown'

def get_android_version(serial):
    """Get Android version."""
    ver, _, _ = shell(serial, 'getprop ro.build.version.release')
    return ver.strip() if ver else 'Unknown'

def get_device_ip(serial):
    """Get device IP address."""
    stdout, _, _ = shell(serial, 'ip route get 1')
    if stdout:
        parts = stdout.split()
        for i, p in enumerate(parts):
            if p == 'src' and i + 1 < len(parts):
                return parts[i + 1]
    # Fallback
    stdout, _, _ = shell(serial, 'ifconfig wlan0')
    if stdout:
        lines = stdout.split('\n')
        for line in lines:
            if 'inet ' in line:
                parts = line.strip().split()
                for i, p in enumerate(parts):
                    if p == 'inet' and i + 1 < len(parts):
                        return parts[i + 1]
    return None

def set_proxy(serial, host, port):
    """Set proxy on Android device (requires app support)."""
    # Most Android devices need an app to set proxy system-wide
    # This sets WiFi proxy settings via settings database
    stdout, stderr, code = shell(serial, f'settings put global http_proxy {host}:{port}')
    return stdout, stderr, code

def clear_proxy(serial):
    """Clear proxy settings."""
    stdout, stderr, code = shell(serial, 'settings delete global http_proxy')
    shell(serial, 'settings delete global global_http_proxy_host')
    shell(serial, 'settings delete global global_http_proxy_port')
    return stdout, stderr, code

def connect_wifi(serial, wifi_ssid, wifi_password):
    """Connect device to WiFi."""
    # This is complex on Android without root
    # Most cloud phone services use pre-configured WiFi
    return "WiFi connection requires device-specific setup", "", 1

def get_installed_apps(serial):
    """List installed packages."""
    stdout, _, _ = shell(serial, 'pm list packages -3')
    packages = []
    if stdout:
        for line in stdout.splitlines():
            if line.startswith('package:'):
                packages.append(line.replace('package:', '').strip())
    return packages

def app_exists(serial, package):
    """Check if package is installed."""
    stdout, _, code = shell(serial, f'pm path {package}')
    return code == 0 and 'package:' in stdout

def start_app(serial, package):
    """Launch an app by package name."""
    return shell(serial, f'monkey -p {package} -c android.intent.category.LAUNCHER 1')

def get_current_app(serial):
    """Get the currently focused app package."""
    stdout, _, _ = shell(serial, 'dumpsys activity activities | grep mResumedActivity')
    if stdout:
        try:
            parts = stdout.split()
            for i, p in enumerate(parts):
                if 'mResumedActivity' in p and i + 1 < len(parts):
                    activity = parts[i + 1]
                    return activity.split('/')[0]
        except:
            pass
    return None

# ─── In-Memory Device Store ───────────────────────────────────────────────────
# Format: { 'serial': { 'serial', 'name', 'status', 'proxy', 'created_at', 'adb_host', 'adb_port' } }
_devices = {}
_device_locks = {}  # serial -> threading.Lock

def get_device(serial):
    return _devices.get(serial)

def get_all_devices():
    return list(_devices.values())

def add_device(serial, name=None, adb_host=None, adb_port=5555):
    if serial not in _devices:
        _devices[serial] = {
            'serial': serial,
            'name': name or serial,
            'status': 'offline',
            'proxy_host': None,
            'proxy_port': None,
            'created_at': datetime.utcnow().isoformat(),
            'adb_host': adb_host,
            'adb_port': adb_port,
            'last_seen': None,
            'model': None,
            'android_version': None,
            'ip_address': None,
            'notes': '',
            'tags': [],
        }
        _device_locks[serial] = threading.Lock()
    return _devices[serial]

def update_device(serial, **kwargs):
    if serial in _devices:
        _devices[serial].update(kwargs)

def remove_device(serial):
    if serial in _devices:
        del _devices[serial]
    if serial in _device_locks:
        del _device_locks[serial]

def connect_device(serial):
    """Connect to a network device via ADB over WiFi."""
    if ':' in serial:
        host, port = serial.rsplit(':', 1)
        try:
            port = int(port)
        except:
            port = 5555
        stdout, stderr, code = run_adb(['connect', f'{host}:{port}'], timeout=10)
        return stdout, stderr, code
    return run_adb(['connect', serial], timeout=10)

def disconnect_device(serial):
    """Disconnect a network device."""
    return run_adb(['disconnect', serial], timeout=5)

def refresh_device(serial):
    """Refresh device status from ADB."""
    devices = list_devices()
    for d in devices:
        if d['serial'] == serial:
            info = get_device_info(serial)
            model = info.get('ro.product.model', '')
            android_ver = info.get('ro.build.version.release', '')
            ip = get_device_ip(serial)
            _devices[serial].update({
                'status': 'online',
                'model': model,
                'android_version': android_ver,
                'ip_address': ip,
                'last_seen': datetime.utcnow().isoformat(),
            })
            return True
    if serial in _devices:
        _devices[serial]['status'] = 'offline'
    return False

def refresh_all_devices():
    """Refresh all managed devices."""
    for serial in list(_devices.keys()):
        refresh_device(serial)

# ─── Flask Routes ──────────────────────────────────────────────────────────────

def register_cloud_phone_routes(app, socketio=None):
    """Register all cloud phone routes with the Flask app."""

    @app.route('/cloud-phones')
    def cloud_phones_page():
        from emulator_manager import list_running_emulators, get_emulator_status
        proxies = get_proxies_internal()
        # Merge real devices + running emulators
        all_devices = get_all_devices()
        running_emu = list_running_emulators()
        emu_status = get_emulator_status()
        for e in running_emu:
            serial = e['serial']
            # Check if already in our device list
            existing = next((d for d in all_devices if d.get('serial') == serial), None)
            if not existing:
                # Add emulator as a device
                info = next((v for v in emu_status.values() if v.get('serial') == serial), {})
                all_devices.append({
                    'serial': serial,
                    'name': info.get('avd_name', serial),
                    'status': 'online',
                    'type': 'emulator',
                    'model': 'Android Emulator',
                    'android_version': '14',
                    'created_at': info.get('started_at', ''),
                })
        return render_template('cloud_phones.html', devices=all_devices,
                               proxies=proxies, page='cloud-phones')

    @app.route('/api/cloud-phones')
    def api_cloud_phones_list():
        refresh_all_devices()
        return jsonify({'devices': get_all_devices()})

    @app.route('/api/cloud-phones/scan', methods=['POST'])
    def api_cloud_phones_scan():
        """Scan for ADB devices on the network."""
        # Try connecting to common cloud phone servers
        cloud_hosts = request.json.get('hosts', []) if request.is_json else []
        found = []
        # Scan local network devices first
        stdout, _, _ = run_adb('devices')
        for line in stdout.splitlines()[1:]:
            if line.strip() and '\t' in line:
                serial = line.split('\t')[0]
                if serial not in [d['serial'] for d in found]:
                    found.append({'serial': serial, 'type': 'local'})
        # Try known cloud phone hosts
        for host in cloud_hosts:
            for port in [5555, 5556, 5557, 5558, 5559]:
                target = f'{host}:{port}'
                stdout, stderr, code = run_adb(['connect', target], timeout=3)
                if code == 0 and 'connected' in stdout.lower():
                    found.append({'serial': target, 'type': 'network'})
        return jsonify({'found': found})

    @app.route('/api/cloud-phones/connect', methods=['POST'])
    def api_cloud_phones_connect():
        data = request.json
        host = data.get('host')
        port = data.get('port', 5555)
        name = data.get('name', '')
        if not host:
            return jsonify({'error': 'Host required'}), 400
        target = f'{host}:{port}'
        stdout, stderr, code = run_adb(['connect', target], timeout=15)
        if code == 0:
            add_device(target, name=name, adb_host=host, adb_port=port)
            refresh_device(target)
            return jsonify({'success': True, 'serial': target, 'message': stdout})
        return jsonify({'error': stderr or stdout}), 500

    @app.route('/api/cloud-phones/disconnect', methods=['POST'])
    def api_cloud_phones_disconnect():
        serial = request.json.get('serial')
        if not serial:
            return jsonify({'error': 'Serial required'}), 400
        run_adb(['disconnect', serial], timeout=5)
        remove_device(serial)
        return jsonify({'success': True})

    @app.route('/api/cloud-phones/<serial>/refresh', methods=['POST'])
    def api_cloud_phones_refresh(serial):
        success = refresh_device(serial)
        dev = get_device(serial)
        return jsonify({'success': success, 'device': dev})

    @app.route('/api/cloud-phones/<serial>', methods=['GET', 'PUT', 'DELETE'])
    def api_cloud_phone(serial):
        if request.method == 'GET':
            refresh_device(serial)
            dev = get_device(serial)
            if not dev:
                # Try to get it from ADB directly
                devices = list_devices()
                for d in devices:
                    if d['serial'] == serial:
                        add_device(serial)
                        refresh_device(serial)
                        dev = get_device(serial)
                        break
            return jsonify({'device': dev})
        elif request.method == 'PUT':
            data = request.json
            update_device(serial, **data)
            return jsonify({'success': True, 'device': get_device(serial)})
        elif request.method == 'DELETE':
            run_adb(['disconnect', serial], timeout=5)
            remove_device(serial)
            return jsonify({'success': True})

    @app.route('/api/cloud-phones/<serial>/screencap')
    def api_cloud_phones_screencap(serial):
        img_data = screencap(serial)
        if img_data:
            return jsonify({'success': True, 'image': img_data})
        return jsonify({'success': False, 'error': 'Failed to capture screen'}), 500

    @app.route('/api/cloud-phones/<serial>/shell', methods=['POST'])
    def api_cloud_phones_shell(serial):
        cmd = request.json.get('cmd', '')
        if not cmd:
            return jsonify({'error': 'Command required'}), 400
        stdout, stderr, code = shell(serial, cmd)
        return jsonify({'stdout': stdout, 'stderr': stderr, 'code': code})

    @app.route('/api/cloud-phones/<serial>/tap', methods=['POST'])
    def api_cloud_phones_tap(serial):
        x = request.json.get('x')
        y = request.json.get('y')
        if x is None or y is None:
            return jsonify({'error': 'x and y required'}), 400
        stdout, stderr, code = tap(serial, int(x), int(y))
        return jsonify({'success': code == 0, 'stdout': stdout, 'stderr': stderr})

    @app.route('/api/cloud-phones/<serial>/swipe', methods=['POST'])
    def api_cloud_phones_swipe(serial):
        x1 = request.json.get('x1'); y1 = request.json.get('y1')
        x2 = request.json.get('x2'); y2 = request.json.get('y2')
        duration = request.json.get('duration', 300)
        if None in (x1, y1, x2, y2):
            return jsonify({'error': 'x1,y1,x2,y2 required'}), 400
        stdout, stderr, code = swipe(serial, int(x1), int(y1), int(x2), int(y2), duration)
        return jsonify({'success': code == 0, 'stdout': stdout, 'stderr': stderr})

    @app.route('/api/cloud-phones/<serial>/text', methods=['POST'])
    def api_cloud_phones_text(serial):
        text = request.json.get('text', '')
        stdout, stderr, code = input_text(serial, text)
        return jsonify({'success': code == 0, 'stdout': stdout, 'stderr': stderr})

    @app.route('/api/cloud-phones/<serial>/key', methods=['POST'])
    def api_cloud_phones_key(serial):
        key = request.json.get('key', 'BACK')
        stdout, stderr, code = press_key(serial, key)
        return jsonify({'success': code == 0, 'stdout': stdout, 'stderr': stderr})

    @app.route('/api/cloud-phones/<serial>/uiauto')
    def api_cloud_phones_uiauto(serial):
        xml = dump_ui(serial)
        return jsonify({'success': bool(xml), 'xml': xml})

    @app.route('/api/cloud-phones/<serial>/apps')
    def api_cloud_phones_apps(serial):
        apps = get_installed_apps(serial)
        return jsonify({'apps': apps})

    @app.route('/api/cloud-phones/<serial>/launch', methods=['POST'])
    def api_cloud_phones_launch(serial):
        package = request.json.get('package')
        if not package:
            return jsonify({'error': 'Package required'}), 400
        stdout, stderr, code = start_app(serial, package)
        return jsonify({'success': code == 0, 'stdout': stdout, 'stderr': stderr})

    @app.route('/api/cloud-phones/<serial>/proxy', methods=['POST', 'DELETE'])
    def api_cloud_phones_proxy(serial):
        if request.method == 'DELETE':
            clear_proxy(serial)
            update_device(serial, proxy_host=None, proxy_port=None)
            return jsonify({'success': True})
        host = request.json.get('host')
        port = request.json.get('port')
        if not host or not port:
            return jsonify({'error': 'host and port required'}), 400
        set_proxy(serial, host, int(port))
        update_device(serial, proxy_host=host, proxy_port=port)
        return jsonify({'success': True})

    @app.route('/api/cloud-phones/<serial>/proxy-set', methods=['POST'])
    def api_cloud_phones_proxy_set(serial):
        """Set proxy from proxy ID."""
        proxy_id = request.json.get('proxy_id')
        if not proxy_id:
            return jsonify({'error': 'proxy_id required'}), 400
        # Get proxy from database
        proxy = get_proxy_by_id(proxy_id)
        if not proxy:
            return jsonify({'error': 'Proxy not found'}), 404
        proxy_url = proxy.get('proxy_url') or proxy.get('host')
        if not proxy_url:
            return jsonify({'error': 'Invalid proxy'}), 400
        if ':' in proxy_url:
            host, port = proxy_url.rsplit(':', 1)
            set_proxy(serial, host, int(port))
            update_device(serial, proxy_host=host, proxy_port=int(port), proxy_id=proxy_id)
        else:
            host = proxy_url
            port = proxy.get('port', 8080)
            set_proxy(serial, host, port)
            update_device(serial, proxy_host=host, proxy_port=port, proxy_id=proxy_id)
        return jsonify({'success': True})

    @app.route('/api/cloud-phones/<serial>/current-app')
    def api_cloud_phones_current_app(serial):
        app = get_current_app(serial)
        return jsonify({'package': app})

    @app.route('/api/cloud-phones/<serial>/display-size')
    def api_cloud_phones_display_size(serial):
        w, h = get_display_size(serial)
        return jsonify({'width': w, 'height': h})

    # ─── Emulator Management ──────────────────────────────────────────────────
    @app.route('/emulators')
    def emulators_page():
        from models import get_proxies
        proxies = get_proxies_internal()
        avds = list_avds()
        running = list_running_emulators()
        emu_status = get_emulator_status()
        return render_template('emulators.html', avds=avds, running=running,
                               emu_status=emu_status, proxies=proxies, page='emulators')

    @app.route('/api/emulators/list-avds')
    def api_list_avds():
        avds = list_avds()
        return jsonify({'avds': avds})

    @app.route('/api/emulators/list-running')
    def api_list_running():
        running = list_running_emulators()
        # Enrich with status
        emu_status = get_emulator_status()
        result = []
        for r in running:
            serial = r['serial']
            info = {}
            for name, data in emu_status.items():
                if data.get('serial') == serial:
                    info = data
                    break
            result.append({**r, 'emu_info': info})
        return jsonify({'emulators': result})

    @app.route('/api/emulators/status')
    def api_emu_status():
        return jsonify({'status': get_emulator_status()})

    @app.route('/api/emulators/start', methods=['POST'])
    def api_start_emulator():
        data = request.json or {}
        avd_name = data.get('avd_name')
        headless = data.get('headless', True)
        memory = data.get('memory', 2048)
        if not avd_name:
            return jsonify({'error': 'avd_name required'}), 400
        result = start_emulator(avd_name, headless=headless, memory=memory)
        return jsonify(result)

    @app.route('/api/emulators/stop', methods=['POST'])
    def api_stop_emulator():
        data = request.json or {}
        avd_name = data.get('avd_name')
        serial = data.get('serial')
        result = stop_emulator(avd_name=avd_name, serial=serial)
        return jsonify(result)

    @app.route('/api/emulators/stop-all', methods=['POST'])
    def api_stop_all_emulators():
        results = stop_all_emulators()
        return jsonify({'results': results})

    @app.route('/api/emulators/<serial>/screencap')
    def api_emu_screencap(serial):
        img = emu_screencap(serial)
        if img:
            return jsonify({'success': True, 'image': img})
        return jsonify({'success': False, 'error': 'Failed to capture'}), 500

    @app.route('/api/emulators/<serial>/apps')
    def api_emu_apps(serial):
        apps = emu_get_installed_apps(serial)
        return jsonify({'apps': apps})

    @app.route('/api/emulators/<serial>/launch', methods=['POST'])
    def api_emu_launch(serial):
        package = request.json.get('package') if request.is_json else None
        if not package:
            return jsonify({'error': 'package required'}), 400
        result = emu_launch_app(serial, package)
        return jsonify(result)

    @app.route('/api/emulators/<serial>/install-apk', methods=['POST'])
    def api_emu_install_apk(serial):
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        import tempfile, os
        f = request.files['file']
        with tempfile.NamedTemporaryFile(suffix='.apk', delete=False) as tmp:
            f.save(tmp.name)
            result = install_apk(serial, tmp.name)
            os.unlink(tmp.name)
        return jsonify(result)

    @app.route('/api/emulators/<serial>/device-info')
    def api_emu_device_info(serial):
        props = emu_get_device_info(serial)
        model = props.get('ro.product.model', 'Unknown')
        android_ver = props.get('ro.build.version.release', 'Unknown')
        brand = props.get('ro.product.brand', 'Unknown')
        device = props.get('ro.product.device', 'Unknown')
        return jsonify({
            'model': model, 'android_version': android_ver,
            'brand': brand, 'device': device,
            'serial': serial
        })

    # ─── Real Device + Emulator unified control ───────────────────────────────
    @app.route('/api/devices/<serial>/control', methods=['POST'])
    def api_device_control(serial):
        """Unified control endpoint for both real devices and emulators."""
        data = request.json
        action = data.get('action')
        if not action:
            return jsonify({'error': 'action required'}), 400
        
        if action == 'tap':
            stdout, stderr, code = tap(serial, int(data['x']), int(data['y']))
        elif action == 'swipe':
            stdout, stderr, code = swipe(serial, int(data['x1']), int(data['y1']),
                                          int(data['x2']), int(data['y2']), data.get('duration', 300))
        elif action == 'text':
            stdout, stderr, code = input_text(serial, data.get('text', ''))
        elif action == 'key':
            stdout, stderr, code = press_key(serial, data.get('key', 'BACK'))
        elif action == 'launch':
            stdout, stderr, code = start_app(serial, data.get('package', ''))
        elif action == 'screencap':
            img = screencap(serial)
            if img:
                return jsonify({'success': True, 'image': img})
            return jsonify({'success': False, 'error': 'Failed'}), 500
        elif action == 'apps':
            return jsonify({'apps': get_installed_apps(serial)})
        elif action == 'current_app':
            return jsonify({'package': get_current_app(serial)})
        elif action == 'info':
            props = get_device_info(serial)
            return jsonify({
                'model': props.get('ro.product.model', ''),
                'android': props.get('ro.build.version.release', ''),
                'ip': get_device_ip(serial)
            })
        else:
            return jsonify({'error': f'Unknown action: {action}'}), 400
        
        return jsonify({'success': code == 0, 'stdout': stdout, 'stderr': stderr})

    @app.route('/api/cloud-phones/adb-devices')
    def api_adb_devices():
        """Get all ADB devices."""
        devs = list_devices()
        return jsonify({'devices': devs})

    @app.route('/api/cloud-phones/automation/run', methods=['POST'])
    def api_cloud_phones_automation():
        """Run automation sequence on a device."""
        data = request.json
        serial = data.get('serial')
        steps = data.get('steps', [])
        if not serial or not steps:
            return jsonify({'error': 'serial and steps required'}), 400
        results = []
        for step in steps:
            action = step.get('action')
            if action == 'tap':
                stdout, stderr, code = tap(serial, step['x'], step['y'])
            elif action == 'swipe':
                stdout, stderr, code = swipe(serial, step['x1'], step['y1'],
                                              step['x2'], step['y2'], step.get('duration', 300))
            elif action == 'text':
                stdout, stderr, code = input_text(serial, step['text'])
            elif action == 'key':
                stdout, stderr, code = press_key(serial, step['key'])
            elif action == 'launch':
                stdout, stderr, code = start_app(serial, step['package'])
            elif action == 'shell':
                stdout, stderr, code = shell(serial, step['cmd'])
            elif action == 'wait':
                time.sleep(step.get('seconds', 1))
                stdout, stderr, code = '', '', 0
            else:
                stdout, stderr, code = f'Unknown action: {action}', '', 1
            results.append({
                'action': action,
                'success': code == 0,
                'stdout': stdout,
                'stderr': stderr,
            })
            if code != 0 and step.get('required', False):
                break
        return jsonify({'results': results})

    # ─── WebSocket Events ───────────────────────────────────────────────────
    if socketio:
        @socketio.on('connect', namespace='/cloud-phone')
        def cloud_phone_connect():
            emit('connected', {'status': 'ok'})

        @socketio.on('subscribe_device', namespace='/cloud-phone')
        def subscribe_device(data):
            serial = data.get('serial')
            if serial:
                # Start screen streaming in a background thread
                def stream_screen():
                    while True:
                        img = screencap(serial)
                        if img:
                            socketio.emit('screencap', {'serial': serial, 'image': img},
                                         namespace='/cloud-phone')
                        time.sleep(0.5)  # ~2fps
                threading.Thread(target=stream_screen, daemon=True).start()
                emit('subscribed', {'serial': serial})

        @socketio.on('device_control', namespace='/cloud-phone')
        def device_control(data):
            serial = data.get('serial')
            action = data.get('action')
            if not serial or not action:
                return
            if action == 'tap':
                tap(serial, data.get('x', 0), data.get('y', 0))
            elif action == 'swipe':
                swipe(serial, data.get('x1', 0), data.get('y1', 0),
                      data.get('x2', 0), data.get('y2', 0))
            elif action == 'key':
                press_key(serial, data.get('key', 'BACK'))
            emit('control_ack', {'action': action, 'serial': serial})

    return app


# ─── Internal helpers to avoid circular imports ────────────────────────────────
def get_proxies_internal():
    try:
        # Import here to avoid circular dependency
        from models import get_proxies
        return get_proxies({'is_active': 1}) or []
    except Exception:
        return []

def get_proxy_by_id(proxy_id):
    try:
        from models import get_proxies
        results = get_proxies({'id': proxy_id})
        return results[0] if results else None
    except Exception:
        return None
