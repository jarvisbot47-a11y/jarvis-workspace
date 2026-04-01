"""
Emulator Manager - Android Emulator Lifecycle Management
Works with Android SDK emulators (AVD) for streaming/account automation.
"""
import subprocess
import threading
import os
import time
import glob

# Android Studio SDK (user-installed)
ANDROID_HOME = "/home/jarvis/Android/Sdk"
ANDROID_SDK_ROOT = ANDROID_HOME
EMULATOR_BIN = f"{ANDROID_HOME}/emulator/emulator"
ADB_BIN = "/home/jarvis/android-sdk/platform-tools/adb"
# Use GeeLark SDK for cmdline-tools (Android Studio doesn't include them)
AVDMANAGER_BIN = "/home/jarvis/android-sdk/cmdline-tools/latest/bin/avdmanager"

_emulator_processes = {}  # avd_name -> {pid, port, serial, started_at}

def get_env():
    env = os.environ.copy()
    env['ANDROID_HOME'] = ANDROID_HOME
    env['ANDROID_SDK_ROOT'] = ANDROID_SDK_ROOT
    env['ANDROID_AVD_HOME'] = os.path.expanduser('~/.android/avd')
    env['ANDROID_SDK_HOME'] = os.path.expanduser('~/.android')
    env['PATH'] = (f"{ANDROID_HOME}/emulator:"
                   f"{ANDROID_HOME}/platform-tools:"
                   f"{ANDROID_HOME}/cmdline-tools/latest/bin:"
                   + env.get('PATH', ''))
    return env


def ensure_sdk_symlinks():
    """Create symlinks so Android Studio SDK can find system images from GeeLark SDK."""
    images_dir = f"{ANDROID_HOME}/system-images"
    gee_lark_images = "/home/jarvis/android-sdk/system-images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir, exist_ok=True)
        for name in os.listdir(gee_lark_images):
            src = f"{gee_lark_images}/{name}"
            dst = f"{images_dir}/{name}"
            if not os.path.exists(dst):
                os.symlink(src, dst)

def list_avds():
    """List all available AVD definitions."""
    try:
        result = subprocess.run(
            [AVDMANAGER_BIN, 'list', 'avd'],
            capture_output=True, text=True, timeout=15,
            env=get_env()
        )
        avds = []
        current = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith('Name:'):
                if current:
                    avds.append(current)
                current = {'name': line.split('Name:')[1].strip()}
            elif ':' in line:
                parts = line.split(':', 1)
                key = parts[0].strip().lower().replace(' ', '_')
                val = parts[1].strip()
                current[key] = val
        if current:
            avds.append(current)
        return avds
    except Exception as e:
        return [{'error': str(e)}]

def list_running_emulators():
    """List all running emulators via ADB."""
    try:
        result = subprocess.run(
            [ADB_BIN, 'devices'],
            capture_output=True, text=True, timeout=10, env=get_env()
        )
        devices = []
        for line in result.stdout.splitlines()[1:]:
            line = line.strip()
            if line and '\t' in line:
                serial, state = line.split('\t', 1)
                if 'emulator' in serial or 'localhost' in serial:
                    devices.append({'serial': serial, 'state': state.strip()})
        return devices
    except:
        return []

def get_avd_port(avd_name, start_port=5554):
    """Assign a port for an emulator instance."""
    used = set()
    for d in list_running_emulators():
        if 'emulator-' in d['serial']:
            try:
                port = int(d['serial'].split('-')[1])
                used.add(port)
            except:
                pass
    # Also track our own processes
    for info in _emulator_processes.values():
        used.add(info.get('port', 0))
    
    for port in range(start_port, start_port + 20, 2):
        if port not in used:
            return port
    return start_port

def start_emulator(avd_name, headless=True, memory=4096, gpu='swiftshader_indirect'):
    """Start an Android emulator instance."""
    ensure_sdk_symlinks()  # Set up system image symlinks first
    
    if avd_name in _emulator_processes:
        info = _emulator_processes[avd_name]
        if info.get('pid') and _is_process_running(info['pid']):
            return {'success': True, 'serial': info['serial'], 'message': 'Already running', 'port': info['port']}

    port = get_avd_port(avd_name)
    serial = f'emulator-{port}'
    
    cmd = [
        EMULATOR_BIN,
        '-avd', avd_name,
        '-port', str(port),
        '-no-snapshot',
        '-no-window' if headless else '',
        '-no-audio' if headless else '',
        '-gpu', gpu,
        '-memory', str(memory),
    ]
    cmd = [c for c in cmd if c]  # Remove empty strings
    
    env = get_env()
    env['ANDROID_EMULATOR_FLAGS'] = 'headless' if headless else ''
    # Point to correct SDK images
    env['ANDROID_PRODUCT_OUT'] = ANDROID_HOME
    env['ANDROID_PRODUCT_ROOT'] = ANDROID_HOME
    
    try:
        # Start without waiting for full boot
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            start_new_session=True
        )
        
        _emulator_processes[avd_name] = {
            'pid': proc.pid,
            'port': port,
            'serial': serial,
            'started_at': time.time(),
            'avd_name': avd_name,
        }
        
        # Wait for ADB to register the device (up to 60s)
        for i in range(60):
            time.sleep(2)
            result = subprocess.run(
                [ADB_BIN, '-s', serial, 'shell', 'echo', 'ready'],
                capture_output=True, text=True, timeout=5, env=get_env()
            )
            if result.returncode == 0:
                # Do initial setup
                _emulator_setup(serial)
                return {'success': True, 'serial': serial, 'port': port, 'pid': proc.pid}
        
        return {'success': True, 'serial': serial, 'port': port, 'pid': proc.pid, 'warning': 'Boot may still be in progress'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def _is_process_running(pid):
    """Check if a process is running."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def _emulator_setup(serial):
    """Do initial emulator setup: unlock, configure, install gapps."""
    env = get_env()
    
    def run_cmd(cmd):
        subprocess.run(
            [ADB_BIN, '-s', serial, 'shell'] + cmd,
            capture_output=True, timeout=10, env=env
        )
    
    def wait_for_boot(timeout=60):
        for _ in range(timeout):
            r = subprocess.run(
                [ADB_BIN, '-s', serial, 'shell', 'getprop', 'sys.boot_completed'],
                capture_output=True, text=True, timeout=5, env=env
            )
            if r.returncode == 0 and r.stdout.strip() == '1':
                return True
            time.sleep(2)
        return False
    
    # Wait for boot
    wait_for_boot()
    time.sleep(5)
    
    # Unlock screen (swipe up to unlock)
    subprocess.run(
        [ADB_BIN, '-s', serial, 'shell', 'input', 'keyevent', 'KEYCODE_MENU'],
        capture_output=True, timeout=5, env=env
    )
    # Dismiss keyguard
    subprocess.run(
        [ADB_BIN, '-s', serial, 'shell', 'wm', 'dismiss-keyguard'],
        capture_output=True, timeout=5, env=env
    )

def stop_emulator(avd_name=None, serial=None):
    """Stop an emulator by AVD name or serial."""
    if avd_name and avd_name in _emulator_processes:
        info = _emulator_processes[avd_name]
        pid = info.get('pid')
        serial = info.get('serial')
        del _emulator_processes[avd_name]
    
    if serial:
        env = get_env()
        # Try graceful shutdown via ADB
        subprocess.run([ADB_BIN, '-s', serial, 'emu', 'kill'],
                       capture_output=True, timeout=10, env=env)
        # Force kill if still running
        subprocess.run([ADB_BIN, '-s', serial, 'shell', 'am', 'kill', 'all'],
                       capture_output=True, timeout=5, env=env)
        subprocess.run([ADB_BIN, 'disconnect', serial],
                       capture_output=True, timeout=5, env=env)
        return {'success': True}
    
    return {'success': False, 'error': 'No serial or avd_name provided'}

def stop_all_emulators():
    """Stop all running emulators."""
    results = []
    for name in list(_emulator_processes.keys()):
        results.append(stop_emulator(avd_name=name))
    # Also kill any orphaned emulator processes
    subprocess.run(['pkill', '-f', 'emulator.*avd'],
                   capture_output=True, timeout=5)
    return results

def install_apk(serial, apk_path):
    """Install an APK on an emulator."""
    if not os.path.exists(apk_path):
        return {'success': False, 'error': f'APK not found: {apk_path}'}
    
    env = get_env()
    result = subprocess.run(
        [ADB_BIN, '-s', serial, 'install', '-r', apk_path],
        capture_output=True, text=True, timeout=120, env=env
    )
    if result.returncode == 0:
        return {'success': True, 'output': result.stdout.strip()}
    return {'success': False, 'error': result.stderr.strip() or result.stdout.strip()}

def get_emulator_status():
    """Get status of all emulator processes."""
    status = {}
    for name, info in _emulator_processes.items():
        pid = info.get('pid')
        serial = info.get('serial')
        running = _is_process_running(pid) if pid else False
        
        # Also check via ADB
        if running and serial:
            result = subprocess.run(
                [ADB_BIN, '-s', serial, 'shell', 'echo', 'ok'],
                capture_output=True, timeout=3, env=get_env()
            )
            running = result.returncode == 0
        
        status[name] = {
            **info,
            'running': running,
            'serial': serial,
            'pid': pid,
        }
    return status

def screencap(serial):
    """Capture screen of emulator."""
    env = get_env()
    result = subprocess.run(
        [ADB_BIN, '-s', serial, 'exec-out', 'screencap', '-p'],
        capture_output=True, timeout=10, env=env
    )
    if result.returncode == 0 and result.stdout:
        import base64
        return base64.b64encode(result.stdout).decode()
    return None

def get_device_info(serial):
    """Get device info from emulator."""
    env = get_env()
    props = {}
    result = subprocess.run(
        [ADB_BIN, '-s', serial, 'shell', 'getprop'],
        capture_output=True, text=True, timeout=10, env=env
    )
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if ':' in line:
                try:
                    parts = line.strip('[()]'.replace(' ', '')).split(']: [')
                    if len(parts) == 2:
                        props[parts[0]] = parts[1]
                except:
                    pass
    return props

def launch_app(serial, package):
    """Launch an app on the emulator."""
    env = get_env()
    result = subprocess.run(
        [ADB_BIN, '-s', serial, 'shell', 'monkey', '-p', package, '-c',
         'android.intent.category.LAUNCHER', '1'],
        capture_output=True, text=True, timeout=10, env=env
    )
    return {'success': result.returncode == 0, 'stdout': result.stdout, 'stderr': result.stderr}

def get_installed_apps(serial):
    """List installed apps on emulator."""
    env = get_env()
    result = subprocess.run(
        [ADB_BIN, '-s', serial, 'shell', 'pm', 'list', 'packages', '-3'],
        capture_output=True, text=True, timeout=15, env=env
    )
    if result.returncode == 0:
        apps = []
        for line in result.stdout.splitlines():
            if line.startswith('package:'):
                apps.append(line.replace('package:', '').strip())
        return apps
    return []
