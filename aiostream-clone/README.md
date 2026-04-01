# Marketing Manager - AIOStream Clone v2.0

**Mystik Singh's All-in-One Music Promotion & Streaming Automation Platform**

---

## ⚡ Overview

Marketing Manager is a comprehensive local web application for managing music promotion campaigns, streaming automation, and social media marketing — all from a beautiful dark-themed UI.

Built with Python Flask, SQLite, and vanilla HTML/CSS. Runs in any browser as a desktop application.

---

## 🎵 Features

### Core Modules

| Module | Description |
|--------|-------------|
| **📊 Dashboard** | Overview stats, recent activity, growth charts |
| **👥 Curator Database** | Manage playlist curators with filters by genre/platform/status |
| **📨 Submissions Tracker** | Track pitch submissions with status management |
| **✉️ Pitch Composer** | Write and send personalized pitch emails |
| **📝 Email Templates** | Reusable templates with variable substitution |
| **📧 Email Accounts** | Multi-account SMTP management with aliases |
| **💿 Albums** | Album management with release tracking |
| **🎤 Tracks** | Track management with metadata (BPM, key, duration) |
| **📅 Release Calendar** | Schedule and track upcoming releases |

### Streaming Automation Suite

| Module | Description |
|--------|-------------|
| **🌐 Proxy Manager** | Add/edit/delete proxies with health checks, geo-location, sticky sessions |
| **🔒 Streaming Accounts** | Manage accounts across 13 platforms (Spotify, SoundCloud, Apple Music, Amazon, Tidal, Deezer, Qobuz, Napster, Pandora, Boomplay, Audiomack, YouTube Music, iHeartRadio) |
| **▶️ Streaming Automation** | Simulate plays, loop tracks, boost stats manually, view activity |
| **🔐 Account Creator** | Bulk create streaming accounts with auto-generated credentials |
| **📱 Emulator Controller** | Create and manage Android emulator instances (Android 8-14) |
| **🛡️ Anti-Detect Profiles** | Fingerprint spoofing: UA, canvas, WebGL, audio, mouse simulation, timing |
| **⏰ Task Scheduler** | Schedule plays, follows, likes, comments with interval/cron support |
| **📈 Statistics** | Activity logs, stream counts, follower growth, CSV export |

### TikTok Bot

| Feature | Description |
|---------|-------------|
| **🎵 Account Management** | Bulk TikTok accounts with proxy binding |
| **🎬 Campaign Manager** | Create and execute music promotion campaigns |
| **📊 Metrics Tracking** | Views, likes, comments, shares, follower gains |

### AI Playlists

- Generate AI-curated playlists based on genre/mood
- Auto-includes Mystik Singh's tracks
- Connect to OpenAI API for intelligent recommendations

---

## 🚀 Quick Start

### Run Directly

```bash
cd aiostream-clone
pip install flask
python app.py
```

Open **http://127.0.0.1:5001** in your browser.

### Build as Desktop App

```bash
# Install PyInstaller
pip install pyinstaller

# Build for Windows
python build.py windows

# Build for macOS
python build.py macos

# Build both
python build.py all
```

The executable will be in `dist/Marketing Manager/`.

---

## 📁 Project Structure

```
aiostream-clone/
├── app.py                  # Main Flask application
├── models.py               # Database models & queries
├── templates.py            # Email pitch templates
├── build.py                # PyInstaller build script
├── Marketing Manager.spec  # PyInstaller spec file
├── mystik_promotion.db     # SQLite database
├── icon/
│   └── arc_reactor.png     # App icon (512x512)
├── templates/              # HTML templates
│   ├── base.html           # Base layout with sidebar
│   ├── dashboard.html
│   ├── proxies.html
│   ├── streaming_accounts.html
│   ├── streaming_automation.html
│   ├── account_creator.html
│   ├── anti_detect.html
│   ├── emulators.html
│   ├── scheduler.html
│   ├── statistics.html
│   ├── tiktok.html
│   ├── ai_playlists.html
│   └── ... (core templates)
├── static/
│   └── css/
└── README.md
```

---

## 🗄️ Database Tables

| Table | Purpose |
|-------|---------|
| `artist_profile` | Mystik Singh's artist info |
| `albums` | Album records |
| `tracks` | Track records |
| `curators` | Playlist curator database |
| `submissions` | Pitch submission tracking |
| `email_templates` | Reusable email templates |
| `email_accounts` | SMTP account management |
| `email_aliases` | Email aliases per account |
| `releases` | Release calendar |
| `proxies` | Proxy pool with health tracking |
| `streaming_accounts` | Platform account credentials |
| `anti_detect_profiles` | Browser fingerprint profiles |
| `emulator_instances` | Android emulator configs |
| `scheduled_tasks` | Task queue with scheduling |
| `activity_logs` | All activity logging |
| `tiktok_accounts` | TikTok account pool |
| `tiktok_campaigns` | Music promotion campaigns |
| `ai_playlists` | Generated AI playlists |

---

## ⚙️ Configuration

### Environment Variables

```bash
export SECRET_KEY='your-secret-key-here'
```

### Database Location

Database is stored at `mystik_promotion.db` (SQLite). Backup regularly via the **Backup Data** button in the sidebar.

### SMTP Setup

Configure email accounts in **Email Accounts** module. The app supports Gmail, Outlook, Yahoo, and custom SMTP providers.

---

## 🔐 Security Notes

- **Local only** — all data stays on your machine
- **Credential storage** — passwords stored in local SQLite (not encrypted in this demo)
- **Proxy security** — credentials stored locally, not transmitted
- **Use responsibly** — streaming automation features are for educational/demo purposes

---

## 🛠️ Development

```bash
# Run in debug mode
python app.py

# Re-initialize database
python -c "from models import init_db; init_db()"

# Export all data
curl http://127.0.0.1:5001/export -o backup.json
```

---

## 📝 Modules Reference

### Proxy Manager
- Add proxies in `IP:Port:User:Pass` format
- Health check tests TCP connectivity
- Bind proxies to accounts for sticky sessions
- Track success/fail counts per proxy

### Account Creator
- Bulk generate accounts (max 50 at once)
- Bind to specific proxy, emulator, anti-detect profile
- Auto-generate unique usernames/emails
- Supported platforms: Spotify, SoundCloud, Apple Music, Amazon, Tidal, Deezer, Qobuz, Napster, Pandora, Boomplay, Audiomack, YouTube Music, iHeartRadio

### Anti-Detect Profiles
- Spoof User-Agent string
- Canvas fingerprint override
- WebGL vendor/renderer spoofing
- Mouse movement/click/scroll timing simulation
- Hardware concurrency and device memory

### Task Scheduler
- One-time or interval-based execution
- Bind to specific account/proxy/emulator
- Play duration, loop count, interval between plays
- Priority queuing (1-10)
- Run count tracking

---

## 🎨 UI Design

- **Theme**: Professional dark mode (#0d0d0d background)
- **Accent**: Warm gold (#c8a45a) with subtle glow
- **Sidebar**: Fixed 240px navigation with section dividers
- **Icon**: White glowing Arc Reactor (⚡)
- **Typography**: System font stack for maximum compatibility

---

## 📄 License

For educational and personal use only. Mystik Singh 2024-2026.

---

*Memento Mori — Vol. 1 · 2 · 3*
