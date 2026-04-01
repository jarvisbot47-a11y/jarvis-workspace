"""
Database models for the AIOStream Clone - Music Promotion Campaign Manager
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import json
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'mystik_promotion.db')


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_db()
    cur = conn.cursor()

    # ── Core tables ──────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS artist_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL DEFAULT 'Mystik Singh',
            stage_name TEXT,
            bio TEXT,
            genre TEXT DEFAULT 'Hip Hop',
            subgenres TEXT,
            location TEXT,
            email TEXT,
            website TEXT,
            instagram TEXT,
            twitter TEXT,
            tiktok TEXT,
            youtube TEXT,
            spotify_url TEXT,
            apple_music_url TEXT,
            soundcloud_url TEXT,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            release_date DATE,
            description TEXT,
            cover_path TEXT,
            spotify_url TEXT,
            apple_music_url TEXT,
            total_tracks INTEGER DEFAULT 0,
            status TEXT DEFAULT 'released',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id INTEGER,
            title TEXT NOT NULL,
            track_number INTEGER,
            duration_secs INTEGER,
            bpm INTEGER,
            key_text TEXT,
            spotify_url TEXT,
            apple_music_url TEXT,
            file_path TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (album_id) REFERENCES albums(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS curators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            playlist_name TEXT,
            platform TEXT DEFAULT 'Spotify',
            playlist_url TEXT,
            genre_focus TEXT,
            follower_count INTEGER,
            email TEXT,
            instagram TEXT,
            twitter TEXT,
            website TEXT,
            notes TEXT,
            rating INTEGER DEFAULT 3,
            response_rate REAL DEFAULT 0.0,
            last_contacted DATE,
            status TEXT DEFAULT 'active',
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curator_id INTEGER NOT NULL,
            track_id INTEGER,
            album_id INTEGER,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'normal',
            email_sent BOOLEAN DEFAULT 0,
            email_sent_at TIMESTAMP,
            email_account_id INTEGER,
            response_status TEXT,
            response_date DATE,
            follow_up_1 DATE,
            follow_up_2 DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (curator_id) REFERENCES curators(id),
            FOREIGN KEY (track_id) REFERENCES tracks(id),
            FOREIGN KEY (album_id) REFERENCES albums(id),
            FOREIGN KEY (email_account_id) REFERENCES email_accounts(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT,
            body TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            variables TEXT,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            release_type TEXT,
            release_date DATE NOT NULL,
            status TEXT DEFAULT 'planned',
            album_id INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS streaming_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER,
            album_id INTEGER,
            platform TEXT,
            stats_date DATE,
            streams INTEGER DEFAULT 0,
            listeners INTEGER DEFAULT 0,
            saves INTEGER DEFAULT 0,
            playlist_adds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (track_id) REFERENCES tracks(id),
            FOREIGN KEY (album_id) REFERENCES albums(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS campaign_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date DATE DEFAULT (date('now')),
            total_submissions INTEGER DEFAULT 0,
            pending INTEGER DEFAULT 0,
            approved INTEGER DEFAULT 0,
            rejected INTEGER DEFAULT 0,
            no_response INTEGER DEFAULT 0,
            response_rate REAL DEFAULT 0.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_address TEXT NOT NULL UNIQUE,
            display_name TEXT,
            provider TEXT,
            smtp_host TEXT,
            smtp_port INTEGER DEFAULT 587,
            smtp_username TEXT,
            smtp_password TEXT,
            use_tls INTEGER DEFAULT 1,
            daily_limit INTEGER DEFAULT 50,
            daily_used INTEGER DEFAULT 0,
            last_used DATE,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            alias_address TEXT NOT NULL,
            display_name TEXT,
            is_default INTEGER DEFAULT 0,
            FOREIGN KEY (account_id) REFERENCES email_accounts(id) ON DELETE CASCADE
        )
    """)

    # ── PROXY MANAGER ─────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proxy_string TEXT NOT NULL,
            proxy_type TEXT DEFAULT 'http',
            ip_address TEXT,
            port INTEGER,
            username TEXT,
            password TEXT,
            country TEXT,
            city TEXT,
            isp TEXT,
            geo_lat REAL,
            geo_lon REAL,
            is_active BOOLEAN DEFAULT 1,
            health_status TEXT DEFAULT 'unknown',
            last_checked TIMESTAMP,
            last_used TIMESTAMP,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            avg_response_ms INTEGER,
            rotation_strategy TEXT DEFAULT 'sequential',
            bound_account_ids TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── STREAMING ACCOUNTS ────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS streaming_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            email TEXT,
            username TEXT,
            password TEXT,
            display_name TEXT,
            profile_url TEXT,
            monthly_listeners INTEGER DEFAULT 0,
            total_followers INTEGER DEFAULT 0,
            total_plays INTEGER DEFAULT 0,
            proxy_id INTEGER,
            emulator_id INTEGER,
            profile_id INTEGER,
            status TEXT DEFAULT 'active',
            is_verified BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proxy_id) REFERENCES proxies(id)
        )
    """)

    # ── ANTI-DETECT PROFILES ─────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS anti_detect_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_agent TEXT,
            canvas_fingerprint TEXT,
            webgl_vendor TEXT,
            webgl_renderer TEXT,
            audio_fingerprint TEXT,
            screen_resolution TEXT,
            timezone TEXT,
            languages TEXT,
            hardware_concurrency INTEGER,
            device_memory INTEGER,
            platform TEXT,
            vendors TEXT,
            font_list TEXT,
            cookie_enabled BOOLEAN DEFAULT 1,
            java_enabled BOOLEAN DEFAULT 0,
            touch_support BOOLEAN DEFAULT 0,
            play_length_secs INTEGER DEFAULT 30,
            scroll_interval_secs INTEGER DEFAULT 5,
            click_interval_secs INTEGER DEFAULT 2,
            mouse_move_duration_secs INTEGER DEFAULT 3,
            is_default BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── EMULATOR INSTANCES ───────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS emulator_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            device_name TEXT,
            android_version TEXT DEFAULT '12',
            avd_path TEXT,
            status TEXT DEFAULT 'stopped',
            proxy_id INTEGER,
            account_id INTEGER,
            profile_id INTEGER,
            screen_width INTEGER DEFAULT 1080,
            screen_height INTEGER DEFAULT 1920,
            dpi INTEGER DEFAULT 480,
            cpu_cores INTEGER DEFAULT 2,
            ram_mb INTEGER DEFAULT 2048,
            started_at TIMESTAMP,
            stopped_at TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proxy_id) REFERENCES proxies(id),
            FOREIGN KEY (account_id) REFERENCES streaming_accounts(id),
            FOREIGN KEY (profile_id) REFERENCES anti_detect_profiles(id)
        )
    """)

    # ── SCHEDULED TASKS ──────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            task_name TEXT NOT NULL,
            platform TEXT,
            target_url TEXT,
            target_id TEXT,
            parameters TEXT,
            schedule_type TEXT DEFAULT 'once',
            cron_expression TEXT,
            scheduled_at TIMESTAMP,
            interval_seconds INTEGER,
            repeat_count INTEGER DEFAULT 0,
            max_repeats INTEGER DEFAULT 0,
            play_duration_secs INTEGER DEFAULT 30,
            loop_count INTEGER DEFAULT 1,
            interval_between_plays_secs INTEGER DEFAULT 10,
            priority INTEGER DEFAULT 5,
            status TEXT DEFAULT 'pending',
            account_id INTEGER,
            proxy_id INTEGER,
            emulator_id INTEGER,
            profile_id INTEGER,
            last_run_at TIMESTAMP,
            next_run_at TIMESTAMP,
            run_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES streaming_accounts(id),
            FOREIGN KEY (proxy_id) REFERENCES proxies(id),
            FOREIGN KEY (emulator_id) REFERENCES emulator_instances(id),
            FOREIGN KEY (profile_id) REFERENCES anti_detect_profiles(id)
        )
    """)

    # ── ACTIVITY LOGS ────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            platform TEXT,
            account_id INTEGER,
            emulator_id INTEGER,
            proxy_id INTEGER,
            task_id INTEGER,
            description TEXT,
            metadata TEXT,
            streams_delta INTEGER DEFAULT 0,
            listeners_delta INTEGER DEFAULT 0,
            followers_delta INTEGER DEFAULT 0,
            likes_delta INTEGER DEFAULT 0,
            success BOOLEAN DEFAULT 1,
            duration_ms INTEGER,
            ip_used TEXT,
            user_agent TEXT,
            FOREIGN KEY (account_id) REFERENCES streaming_accounts(id),
            FOREIGN KEY (emulator_id) REFERENCES emulator_instances(id),
            FOREIGN KEY (proxy_id) REFERENCES proxies(id),
            FOREIGN KEY (task_id) REFERENCES scheduled_tasks(id)
        )
    """)

    # ── TIKTOK ACCOUNTS ──────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tiktok_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT,
            password TEXT,
            phone TEXT,
            display_name TEXT,
            profile_url TEXT,
            followers INTEGER DEFAULT 0,
            following INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            proxy_id INTEGER,
            emulator_id INTEGER,
            profile_id INTEGER,
            status TEXT DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proxy_id) REFERENCES proxies(id),
            FOREIGN KEY (emulator_id) REFERENCES emulator_instances(id),
            FOREIGN KEY (profile_id) REFERENCES anti_detect_profiles(id)
        )
    """)

    # ── TIKTOK CAMPAIGNS ─────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tiktok_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_name TEXT NOT NULL,
            track_id INTEGER,
            album_id INTEGER,
            description TEXT,
            video_file_path TEXT,
            caption TEXT,
            hashtags TEXT,
            target_account_ids TEXT,
            status TEXT DEFAULT 'draft',
            total_views INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            total_comments INTEGER DEFAULT 0,
            total_shares INTEGER DEFAULT 0,
            total_followers_gained INTEGER DEFAULT 0,
            scheduled_at TIMESTAMP,
            posted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (track_id) REFERENCES tracks(id),
            FOREIGN KEY (album_id) REFERENCES albums(id)
        )
    """)

    # ── AI PLAYLISTS ─────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_name TEXT NOT NULL,
            description TEXT,
            genre TEXT,
            mood TEXT,
            platform TEXT DEFAULT 'Spotify',
            playlist_url TEXT,
            track_ids TEXT,
            generated_with TEXT DEFAULT 'openai',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Seed default data ─────────────────────────────────────────────
    _seed_data(cur)

    conn.commit()
    conn.close()


def _seed_data(cur):
    """Seed default records if tables are empty."""

    # Artist profile
    cur.execute("SELECT COUNT(*) FROM artist_profile")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO artist_profile (name, stage_name, bio, genre, subgenres, location, email, instagram)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'Mystik Singh', 'Mystik Singh',
            'Independent hip hop artist from Los Angeles, CA. Known for the "Memento Mori" series—three albums exploring themes of mortality, resilience, and the human spirit through hard-hitting bars and cinematic production.',
            'Hip Hop', 'Trap,Boom Bap,Conscious Hip Hop', 'Los Angeles, CA', 'contact@mystiksingh.com', '@mystiksingh'
        ))

    # Albums
    cur.execute("SELECT COUNT(*) FROM albums")
    if cur.fetchone()[0] == 0:
        albums = [
            ('Memento Mori Vol. 1', '2022-03-15', 'The debut chapter. Dark, introspective beats with raw lyricism.', 12, 'released'),
            ('Memento Mori Vol. 2', '2023-07-22', 'The sophomore follow-up. Refined production, sharper pen game.', 14, 'released'),
            ('Memento Mori Vol. 3', '2024-11-30', 'The trilogy closer. Most ambitious project—live instrumentation, cinematic interludes.', 16, 'released'),
        ]
        for t, d, desc, tr, s in albums:
            cur.execute("INSERT INTO albums (title, release_date, description, total_tracks, status) VALUES (?,?,?,?,?)", (t, d, desc, tr, s))

    # Curators
    cur.execute("SELECT COUNT(*) FROM curators")
    if cur.fetchone()[0] == 0:
        curators = [
            ('DJ Phantom', 'Late Night Lofi', 'Spotify', 'Lo-fi Hip Hop', 15000, 'djphantom@email.com', '@djphantom', 'lofiambition.com', 'Great for relaxed study beats', 5, 35.0, 'SubmitHub'),
            ('MC Lyricist', 'Bars & Breaks', 'Spotify', 'Hip Hop', 4200, 'mclyricist@email.com', '@mclyricist', '', 'Hard-hitting rap, prefers real instrumentals', 4, 28.0, 'Playlist Push'),
            ('Soulja Boy Steve', 'Trap Universe', 'Spotify', 'Trap', 89000, 'steve@trapuni.com', '@trapsteve', 'trapuniverse.com', 'Major trap playlist, heavy 808s', 4, 18.0, 'Groover'),
            ('Luna Rivera', 'Conscious Currents', 'Spotify', 'Conscious Hip Hop', 6200, 'luna@currents.com', '@lunarr', '', 'Prefers lyrically-driven tracks', 5, 42.0, 'SubmitHub'),
            ('Beat Drop Records', 'New Era Fridays', 'Spotify', 'Hip Hop', 35000, 'beats@beatdrop.com', '@beatdropREC', 'beatdroprecords.com', 'A&R-focused playlist', 4, 22.0, 'Direct'),
            ('Heavy Bass Network', 'Bass Heavy', 'Spotify', 'Trap', 28000, 'bass@heavynet.com', '@heavybass', 'heavynet.com', 'Dubstep/trap crossovers welcome', 3, 12.0, 'SubmitHub'),
        ]
        for c in curators:
            cur.execute("""
                INSERT INTO curators (name, playlist_name, platform, genre_focus, follower_count, email, instagram, website, notes, rating, response_rate, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (c[0], c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9], c[10], c[11]))

    # Email templates
    cur.execute("SELECT COUNT(*) FROM email_templates")
    if cur.fetchone()[0] == 0:
        templates = [
            ('Initial Pitch', '[Song Title] for [Playlist Name] - [Artist Name]',
             "Hi [Curator Name],\n\nI hope this message finds you well. My name is [Artist Name], an independent hip hop artist from [Location].\n\nI'm reaching out because I think my latest track \"[Track Title]\" would be a great fit for your [Playlist Name] playlist.\n\nHere's the link: [Spotify/Apple link]\n\nThanks for your time!\n\nBest,\n[Artist Name]",
             'initial', json.dumps(['Curator Name', 'Playlist Name', 'Artist Name', 'Location', 'Track Title', 'Spotify Link']), 1),
            ('Follow Up (1 Week)', 'Re: [Song Title] for [Playlist Name]',
             "Hi [Curator Name],\n\nJust wanted to bump my previous message about \"[Track Title].\" I completely understand you're probably swamped with submissions.\n\nNo worries if it's not a fit! Would you mind letting me know either way?\n\nThanks again.\n\nBest,\n[Artist Name]",
             'followup', json.dumps(['Curator Name', 'Track Title', 'Playlist Name', 'Artist Name']), 0),
            ('Quick Intro', '[Artist Name] - [Track Title]',
             "Hey [Curator Name],\n\n[Artist Name] here. Dropped a new track called \"[Track Title]\" and thought it could vibe with [Playlist Name].\n\n[2-sentence description]\n\nLink: [Link]\n\nThanks!\n[Artist Name]",
             'short', json.dumps(['Curator Name', 'Playlist Name', 'Artist Name', 'Track Title', 'Link']), 0),
        ]
        for t in templates:
            cur.execute("INSERT INTO email_templates (name, subject, body, category, variables, is_default) VALUES (?,?,?,?,?,?)", t)

    # Email accounts
    cur.execute("SELECT COUNT(*) FROM email_accounts")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO email_accounts (email_address, display_name, provider, smtp_host, smtp_port, smtp_username, smtp_password, use_tls, daily_limit, status, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, ('mystik.music.pitches@gmail.com', 'Mystik Singh', 'gmail', 'smtp.gmail.com', 587, 'mystik.music.pitches', '', 1, 50, 'active', 'Primary pitching account'))
        cur.execute("""
            INSERT INTO email_accounts (email_address, display_name, provider, smtp_host, smtp_port, smtp_username, smtp_password, use_tls, daily_limit, status, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, ('mystik.promo@outlook.com', 'Mystik Promo', 'outlook', 'smtp-mail.outlook.com', 587, 'mystik.promo', '', 1, 40, 'active', 'Secondary for follow-ups'))

    # Default anti-detect profile
    cur.execute("SELECT COUNT(*) FROM anti_detect_profiles")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO anti_detect_profiles (name, user_agent, platform, play_length_secs, scroll_interval_secs, click_interval_secs, mouse_move_duration_secs, is_default)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            'Default Profile',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Win32', 30, 5, 2, 3, 1
        ))


# ══════════════════════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _dict_row(cur, row):
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════════════════════
# ARTIST PROFILE
# ══════════════════════════════════════════════════════════════════════════════

def get_artist_profile():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM artist_profile LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_artist_profile(data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    fields += ", updated_at = CURRENT_TIMESTAMP"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE artist_profile SET {fields} WHERE id = 1", tuple(data.values()))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# ALBUMS
# ══════════════════════════════════════════════════════════════════════════════

def get_albums():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM albums ORDER BY release_date DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_album(album_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM albums WHERE id = ?", (album_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_album(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO albums (title, release_date, description, cover_path, spotify_url, apple_music_url, total_tracks, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['title'], data.get('release_date'), data.get('description'), data.get('cover_path'),
          data.get('spotify_url'), data.get('apple_music_url'), data.get('total_tracks', 0), data.get('status', 'planned')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


# ══════════════════════════════════════════════════════════════════════════════
# TRACKS
# ══════════════════════════════════════════════════════════════════════════════

def get_tracks(album_id: int = None):
    conn = get_db()
    cur = conn.cursor()
    if album_id:
        cur.execute("SELECT * FROM tracks WHERE album_id = ? ORDER BY track_number", (album_id,))
    else:
        cur.execute("SELECT * FROM tracks ORDER BY album_id, track_number")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_track(track_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_track(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tracks (album_id, title, track_number, duration_secs, bpm, key_text, spotify_url, apple_music_url, file_path, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get('album_id'), data['title'], data.get('track_number'), data.get('duration_secs'),
          data.get('bpm'), data.get('key_text'), data.get('spotify_url'), data.get('apple_music_url'),
          data.get('file_path'), data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


# ══════════════════════════════════════════════════════════════════════════════
# CURATORS
# ══════════════════════════════════════════════════════════════════════════════

def get_curators(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM curators WHERE 1=1"
    params = []
    if filters:
        if filters.get('genre_focus'):
            query += " AND genre_focus LIKE ?"
            params.append(f"%{filters['genre_focus']}%")
        if filters.get('platform'):
            query += " AND platform = ?"
            params.append(filters['platform'])
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
        if filters.get('min_followers'):
            query += " AND follower_count >= ?"
            params.append(filters['min_followers'])
    query += " ORDER BY rating DESC, follower_count DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_curator(curator_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM curators WHERE id = ?", (curator_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_curator(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO curators (name, playlist_name, platform, playlist_url, genre_focus, follower_count,
            email, instagram, twitter, website, notes, rating, response_rate, status, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['name'], data.get('playlist_name'), data.get('platform', 'Spotify'),
          data.get('playlist_url'), data.get('genre_focus'), data.get('follower_count'),
          data.get('email'), data.get('instagram'), data.get('twitter'), data.get('website'),
          data.get('notes'), data.get('rating', 3), data.get('response_rate', 0.0),
          data.get('status', 'active'), data.get('source')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_curator(curator_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE curators SET {fields} WHERE id = ?", tuple(data.values()) + (curator_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# SUBMISSIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_submissions(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = """
        SELECT s.*, c.name as curator_name, c.playlist_name, c.genre_focus,
               t.title as track_title, a.title as album_title
        FROM submissions s
        LEFT JOIN curators c ON s.curator_id = c.id
        LEFT JOIN tracks t ON s.track_id = t.id
        LEFT JOIN albums a ON s.album_id = a.id
        WHERE 1=1
    """
    params = []
    if filters:
        if filters.get('status'):
            query += " AND s.status = ?"
            params.append(filters['status'])
        if filters.get('curator_id'):
            query += " AND s.curator_id = ?"
            params.append(filters['curator_id'])
        if filters.get('album_id'):
            query += " AND s.album_id = ?"
            params.append(filters['album_id'])
    query += " ORDER BY s.created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_submission(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE curators SET last_contacted = date('now') WHERE id = ?", (data['curator_id'],))
    if data.get('email_account_id'):
        cur.execute("UPDATE email_accounts SET daily_used = daily_used + 1, last_used = date('now') WHERE id = ?",
                    (data['email_account_id'],))
    cur.execute("""
        INSERT INTO submissions (curator_id, track_id, album_id, status, priority, email_sent, email_account_id, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['curator_id'], data.get('track_id'), data.get('album_id'),
          data.get('status', 'pending'), data.get('priority', 'normal'),
          data.get('email_sent', 0), data.get('email_account_id'), data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_submission(sub_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    fields += ", updated_at = CURRENT_TIMESTAMP"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE submissions SET {fields} WHERE id = ?", tuple(data.values()) + (sub_id,))
    conn.commit()
    conn.close()


def delete_submission(sub_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM submissions WHERE id = ?", (sub_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

def get_email_templates(category: str = None):
    conn = get_db()
    cur = conn.cursor()
    if category:
        cur.execute("SELECT * FROM email_templates WHERE category = ? ORDER BY is_default DESC, name", (category,))
    else:
        cur.execute("SELECT * FROM email_templates ORDER BY is_default DESC, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_email_template(template_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM email_templates WHERE id = ?", (template_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_email_template(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO email_templates (name, subject, body, category, variables, is_default)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['name'], data.get('subject'), data['body'], data.get('category', 'general'),
          data.get('variables'), data.get('is_default', 0)))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_email_template(template_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE email_templates SET {fields} WHERE id = ?", tuple(data.values()) + (template_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# RELEASES
# ══════════════════════════════════════════════════════════════════════════════

def get_releases():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM releases ORDER BY release_date DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_release(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO releases (title, release_type, release_date, status, album_id, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data['title'], data.get('release_type'), data['release_date'],
          data.get('status', 'planned'), data.get('album_id'), data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


# ══════════════════════════════════════════════════════════════════════════════
# STATISTICS
# ══════════════════════════════════════════════════════════════════════════════

def get_dashboard_stats():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) as count FROM submissions GROUP BY status")
    status_counts = {row['status']: row['count'] for row in cur.fetchall()}
    total = sum(status_counts.values())
    approved = status_counts.get('approved', 0)
    pending = status_counts.get('pending', 0)
    response_rate = round((approved / total * 100), 1) if total > 0 else 0
    cur.execute("SELECT COUNT(*) as total FROM curators")
    total_curators = cur.fetchone()['total']
    cur.execute("""
        SELECT s.*, c.name as curator_name, c.playlist_name, t.title as track_title
        FROM submissions s LEFT JOIN curators c ON s.curator_id = c.id
        LEFT JOIN tracks t ON s.track_id = t.id ORDER BY s.created_at DESC LIMIT 10
    """)
    recent = [dict(r) for r in cur.fetchall()]
    today = datetime.now().strftime('%Y-%m-%d')
    cur.execute("""
        SELECT s.*, c.name as curator_name, c.email, t.title as track_title
        FROM submissions s LEFT JOIN curators c ON s.curator_id = c.id
        LEFT JOIN tracks t ON s.track_id = t.id
        WHERE s.status = 'pending' AND s.email_sent = 1 AND (s.follow_up_1 <= ? OR s.follow_up_2 <= ?)
    """, (today, today))
    follow_ups_due = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        'total': total, 'approved': approved, 'pending': pending,
        'no_response': status_counts.get('no_response', 0),
        'rejected': status_counts.get('rejected', 0),
        'response_rate': response_rate, 'total_curators': total_curators,
        'recent': recent, 'follow_ups_due': follow_ups_due,
        'status_counts': status_counts
    }


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT / IMPORT
# ══════════════════════════════════════════════════════════════════════════════

def export_all_data():
    conn = get_db()
    cur = conn.cursor()
    data = {}
    for table in ['artist_profile', 'albums', 'tracks', 'curators', 'submissions',
                  'email_templates', 'releases', 'streaming_stats', 'proxies',
                  'streaming_accounts', 'anti_detect_profiles', 'emulator_instances',
                  'scheduled_tasks', 'activity_logs', 'tiktok_accounts', 'tiktok_campaigns',
                  'ai_playlists', 'email_accounts', 'email_aliases']:
        cur.execute(f"SELECT * FROM {table}")
        data[table] = [dict(r) for r in cur.fetchall()]
    conn.close()
    return data


def import_data(data: dict):
    conn = get_db()
    cur = conn.cursor()
    for table, rows in data.items():
        if rows:
            cur.execute(f"DELETE FROM {table}")
            for row in rows:
                cols = ', '.join(row.keys())
                placeholders = ', '.join(['?'] * len(row))
                cur.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", tuple(row.values()))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL ACCOUNTS
# ══════════════════════════════════════════════════════════════════════════════

def get_email_accounts(status: str = None):
    conn = get_db()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM email_accounts WHERE status = ? ORDER BY last_used DESC NULLS LAST", (status,))
    else:
        cur.execute("SELECT * FROM email_accounts ORDER BY last_used DESC NULLS LAST")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_email_account(account_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM email_accounts WHERE id = ?", (account_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_email_account(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO email_accounts (email_address, display_name, provider, smtp_host, smtp_port,
            smtp_username, smtp_password, use_tls, daily_limit, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['email_address'], data.get('display_name'), data.get('provider', 'gmail'),
          data.get('smtp_host'), data.get('smtp_port', 587), data.get('smtp_username'),
          data.get('smtp_password'), data.get('use_tls', 1), data.get('daily_limit', 50),
          data.get('status', 'active'), data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_email_account(account_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE email_accounts SET {fields} WHERE id = ?", tuple(data.values()) + (account_id,))
    conn.commit()
    conn.close()


def delete_email_account(account_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM email_accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()


def get_email_aliases(account_id: int = None):
    conn = get_db()
    cur = conn.cursor()
    if account_id:
        cur.execute("SELECT * FROM email_aliases WHERE account_id = ?", (account_id,))
    else:
        cur.execute("SELECT * FROM email_aliases")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_email_alias(account_id: int, alias_address: str, display_name: str = None, is_default: int = 0):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO email_aliases (account_id, alias_address, display_name, is_default) VALUES (?, ?, ?, ?)",
                (account_id, alias_address, display_name, is_default))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def delete_email_alias(alias_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM email_aliases WHERE id = ?", (alias_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# PROXY MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def get_proxies(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM proxies WHERE 1=1"
    params = []
    if filters:
        if filters.get('is_active') is not None:
            query += " AND is_active = ?"
            params.append(filters['is_active'])
        if filters.get('health_status'):
            query += " AND health_status = ?"
            params.append(filters['health_status'])
        if filters.get('country'):
            query += " AND country = ?"
            params.append(filters['country'])
    query += " ORDER BY success_count DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_proxy(proxy_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_proxy(data: dict):
    conn = get_db()
    cur = conn.cursor()
    # Parse proxy_string into components if provided
    proxy_str = data.get('proxy_string', '')
    ip, port, user, pw = '', '', '', ''
    if proxy_str:
        parts = proxy_str.split('@')
        if len(parts) == 2:
            user_pass = parts[0].split(':')
            ip_port = parts[1].split(':')
            if len(user_pass) == 2:
                user, pw = user_pass[0], user_pass[1]
            if len(ip_port) == 2:
                ip, port = ip_port[0], ip_port[1]
        else:
            # IP:Port format
            parts2 = proxy_str.split(':')
            if len(parts2) == 4:
                ip, port, user, pw = parts2[0], parts2[1], parts2[2], parts2[3]
            elif len(parts2) == 2:
                ip, port = parts2[0], parts2[1]
    try:
        port = int(port) if port else None
    except:
        port = None
    cur.execute("""
        INSERT INTO proxies (proxy_string, proxy_type, ip_address, port, username, password,
            country, city, isp, geo_lat, geo_lon, is_active, rotation_strategy, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (proxy_str, data.get('proxy_type', 'http'), ip, port, user, pw,
          data.get('country'), data.get('city'), data.get('isp'),
          data.get('geo_lat'), data.get('geo_lon'),
          data.get('is_active', 1), data.get('rotation_strategy', 'sequential'),
          data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_proxy(proxy_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE proxies SET {fields} WHERE id = ?", tuple(data.values()) + (proxy_id,))
    conn.commit()
    conn.close()


def delete_proxy(proxy_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
    conn.commit()
    conn.close()


def check_proxy_health(proxy_id: int):
    """Test proxy connectivity and update health status."""
    import socket
    import time
    proxy = get_proxy(proxy_id)
    if not proxy:
        return None
    start = time.time()
    try:
        proxy_url = proxy['proxy_string']
        # Basic TCP check
        if ':' in proxy_url:
            parts = proxy_url.split('@')
            if len(parts) == 2:
                ip_port = parts[1].split(':')
            else:
                ip_port = proxy_url.split(':')
            if len(ip_port) >= 2:
                ip = ip_port[0]
                port = int(ip_port[1])
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex((ip, port))
                sock.close()
                elapsed = int((time.time() - start) * 1000)
                if result == 0:
                    update_proxy(proxy_id, {
                        'health_status': 'healthy',
                        'last_checked': datetime.now().isoformat(),
                        'avg_response_ms': elapsed,
                        'success_count': proxy['success_count'] + 1,
                        'fail_count': proxy['fail_count']
                    })
                    return 'healthy'
                else:
                    update_proxy(proxy_id, {
                        'health_status': 'dead',
                        'last_checked': datetime.now().isoformat(),
                        'fail_count': proxy['fail_count'] + 1
                    })
                    return 'dead'
        return 'unknown'
    except Exception as e:
        update_proxy(proxy_id, {
            'health_status': 'error',
            'last_checked': datetime.now().isoformat(),
            'fail_count': proxy['fail_count'] + 1
        })
        return f'error: {str(e)}'


# ══════════════════════════════════════════════════════════════════════════════
# STREAMING ACCOUNTS
# ══════════════════════════════════════════════════════════════════════════════

PLATFORMS = ['Spotify', 'SoundCloud', 'Apple Music', 'Amazon Music', 'Tidal', 'Qobuz',
             'Deezer', 'Napster', 'Pandora', 'Boomplay', 'Audiomack', 'YouTube Music', 'iHeartRadio']

EMAIL_PROVIDERS = ['gmail', 'yahoo', 'outlook', 'custom']


def get_streaming_accounts(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM streaming_accounts WHERE 1=1"
    params = []
    if filters:
        if filters.get('platform'):
            query += " AND platform = ?"
            params.append(filters['platform'])
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
        if filters.get('account_id'):
            query += " AND id = ?"
            params.append(filters['account_id'])
    query += " ORDER BY platform, created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_streaming_account(account_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM streaming_accounts WHERE id = ?", (account_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_streaming_account(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO streaming_accounts (platform, email, username, password, display_name, profile_url,
            proxy_id, emulator_id, profile_id, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['platform'], data.get('email'), data.get('username'), data.get('password'),
          data.get('display_name'), data.get('profile_url'), data.get('proxy_id'),
          data.get('emulator_id'), data.get('profile_id'), data.get('status', 'active'),
          data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_streaming_account(account_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    fields += ", updated_at = CURRENT_TIMESTAMP"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE streaming_accounts SET {fields} WHERE id = ?", tuple(data.values()) + (account_id,))
    conn.commit()
    conn.close()


def delete_streaming_account(account_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM streaming_accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-DETECT PROFILES
# ══════════════════════════════════════════════════════════════════════════════

def get_anti_detect_profiles():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM anti_detect_profiles ORDER BY is_default DESC, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_anti_detect_profile(profile_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM anti_detect_profiles WHERE id = ?", (profile_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_anti_detect_profile(data: dict):
    conn = get_db()
    cur = conn.cursor()
    if data.get('is_default'):
        cur.execute("UPDATE anti_detect_profiles SET is_default = 0")
    cur.execute("""
        INSERT INTO anti_detect_profiles (name, user_agent, canvas_fingerprint, webgl_vendor, webgl_renderer,
            audio_fingerprint, screen_resolution, timezone, languages, hardware_concurrency, device_memory,
            platform, vendors, font_list, cookie_enabled, java_enabled, touch_support,
            play_length_secs, scroll_interval_secs, click_interval_secs, mouse_move_duration_secs,
            is_default, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['name'], data.get('user_agent'), data.get('canvas_fingerprint'),
          data.get('webgl_vendor'), data.get('webgl_renderer'), data.get('audio_fingerprint'),
          data.get('screen_resolution'), data.get('timezone'), data.get('languages'),
          data.get('hardware_concurrency'), data.get('device_memory'), data.get('platform'),
          data.get('vendors'), data.get('font_list'), data.get('cookie_enabled', 1),
          data.get('java_enabled', 0), data.get('touch_support', 0),
          data.get('play_length_secs', 30), data.get('scroll_interval_secs', 5),
          data.get('click_interval_secs', 2), data.get('mouse_move_duration_secs', 3),
          data.get('is_default', 0), data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_anti_detect_profile(profile_id: int, data: dict):
    if data.get('is_default'):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE anti_detect_profiles SET is_default = 0")
        conn.commit()
        conn.close()
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE anti_detect_profiles SET {fields} WHERE id = ?", tuple(data.values()) + (profile_id,))
    conn.commit()
    conn.close()


def delete_anti_detect_profile(profile_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM anti_detect_profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# EMULATOR INSTANCES
# ══════════════════════════════════════════════════════════════════════════════

ANDROID_VERSIONS = ['8', '10', '12', '13', '14']

DEVICE_PROFILES = {
    'Pixel 3': {'screen_width': 1080, 'screen_height': 2160, 'dpi': 440},
    'Pixel 4': {'screen_width': 1080, 'screen_height': 2280, 'dpi': 440},
    'Pixel 5': {'screen_width': 1080, 'screen_height': 2340, 'dpi': 440},
    'Samsung S21': {'screen_width': 1080, 'screen_height': 2400, 'dpi': 420},
    'Samsung S22': {'screen_width': 1080, 'screen_height': 2340, 'dpi': 425},
    'OnePlus 9': {'screen_width': 1080, 'screen_height': 2400, 'dpi': 401},
    'Generic Phone': {'screen_width': 1080, 'screen_height': 1920, 'dpi': 480},
    'iPad-like': {'screen_width': 2048, 'screen_height': 2732, 'dpi': 264},
    'Generic Tablet': {'screen_width': 1200, 'screen_height': 1920, 'dpi': 320},
}


def get_emulator_instances(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT e.*, p.proxy_string, p.country, p.city, a.platform, a.display_name as account_name FROM emulator_instances e LEFT JOIN proxies p ON e.proxy_id = p.id LEFT JOIN streaming_accounts a ON e.account_id = a.id WHERE 1=1"
    params = []
    if filters:
        if filters.get('status'):
            query += " AND e.status = ?"
            params.append(filters['status'])
    query += " ORDER BY e.created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_emulator_instance(instance_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM emulator_instances WHERE id = ?", (instance_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_emulator_instance(data: dict):
    conn = get_db()
    cur = conn.cursor()
    device = DEVICE_PROFILES.get(data.get('device_name', 'Generic Phone'))
    screen_width = data.get('screen_width', device['screen_width'])
    screen_height = data.get('screen_height', device['screen_height'])
    dpi = data.get('dpi', device['dpi'])
    cur.execute("""
        INSERT INTO emulator_instances (name, device_name, android_version, avd_path, status,
            proxy_id, account_id, profile_id, screen_width, screen_height, dpi, cpu_cores, ram_mb, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['name'], data.get('device_name', 'Generic Phone'), data.get('android_version', '12'),
          data.get('avd_path'), 'stopped', data.get('proxy_id'), data.get('account_id'),
          data.get('profile_id'), screen_width, screen_height, dpi,
          data.get('cpu_cores', 2), data.get('ram_mb', 2048), data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_emulator_instance(instance_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE emulator_instances SET {fields} WHERE id = ?", tuple(data.values()) + (instance_id,))
    conn.commit()
    conn.close()


def delete_emulator_instance(instance_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM emulator_instances WHERE id = ?", (instance_id,))
    conn.commit()
    conn.close()


def start_emulator(instance_id: int):
    """Start an emulator instance via system command."""
    import subprocess
    inst = get_emulator_instance(instance_id)
    if not inst:
        return False, "Instance not found"
    try:
        cmd = f"cd {os.path.dirname(__file__)} && echo 'Starting emulator: {inst['name']}'"
        subprocess.run(cmd, shell=True, check=False)
        update_emulator_instance(instance_id, {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        })
        return True, f"Emulator {inst['name']} started"
    except Exception as e:
        return False, str(e)


def stop_emulator(instance_id: int):
    inst = get_emulator_instance(instance_id)
    if not inst:
        return False, "Instance not found"
    update_emulator_instance(instance_id, {
        'status': 'stopped',
        'stopped_at': datetime.now().isoformat()
    })
    return True, f"Emulator {inst['name']} stopped"


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULED TASKS
# ══════════════════════════════════════════════════════════════════════════════

TASK_TYPES = ['play', 'follow', 'like', 'comment', 'save', 'watch', 'upload', 'dm']


def get_scheduled_tasks(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM scheduled_tasks WHERE 1=1"
    params = []
    if filters:
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
        if filters.get('task_type'):
            query += " AND task_type = ?"
            params.append(filters['task_type'])
        if filters.get('platform'):
            query += " AND platform = ?"
            params.append(filters['platform'])
    query += " ORDER BY priority DESC, scheduled_at ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_scheduled_task(task_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_scheduled_task(data: dict):
    conn = get_db()
    cur = conn.cursor()
    params_json = data.get('parameters')
    if isinstance(params_json, dict):
        params_json = json.dumps(params_json)
    scheduled_at = data.get('scheduled_at')
    if scheduled_at:
        scheduled_at = scheduled_at.isoformat() if hasattr(scheduled_at, 'isoformat') else scheduled_at
    next_run = scheduled_at
    cur.execute("""
        INSERT INTO scheduled_tasks (task_type, task_name, platform, target_url, target_id, parameters,
            schedule_type, cron_expression, scheduled_at, interval_seconds, repeat_count, max_repeats,
            play_duration_secs, loop_count, interval_between_plays_secs, priority, status,
            account_id, proxy_id, emulator_id, profile_id, next_run_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['task_type'], data['task_name'], data.get('platform'), data.get('target_url'),
          data.get('target_id'), params_json, data.get('schedule_type', 'once'),
          data.get('cron_expression'), scheduled_at, data.get('interval_seconds'),
          data.get('repeat_count', 0), data.get('max_repeats', 0),
          data.get('play_duration_secs', 30), data.get('loop_count', 1),
          data.get('interval_between_plays_secs', 10), data.get('priority', 5),
          data.get('status', 'pending'), data.get('account_id'), data.get('proxy_id'),
          data.get('emulator_id'), data.get('profile_id'), next_run))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_scheduled_task(task_id: int, data: dict):
    if 'parameters' in data and isinstance(data['parameters'], dict):
        data['parameters'] = json.dumps(data['parameters'])
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE scheduled_tasks SET {fields} WHERE id = ?", tuple(data.values()) + (task_id,))
    conn.commit()
    conn.close()


def delete_scheduled_task(task_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def run_scheduled_task(task_id: int):
    """Execute a scheduled task and log the result."""
    task = get_scheduled_task(task_id)
    if not task:
        return False, "Task not found"
    start = datetime.now()
    success = True
    error_msg = ''
    try:
        # Log task execution
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO activity_logs (event_type, platform, account_id, emulator_id, proxy_id,
                task_id, description, metadata, success, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"task_run:{task['task_type']}", task.get('platform'), task.get('account_id'),
              task.get('emulator_id'), task.get('proxy_id'), task_id,
              f"Task executed: {task['task_name']}",
              json.dumps({'task_type': task['task_type'], 'target': task.get('target_url')}),
              1, start.isoformat()))
        conn.commit()
        conn.close()
        # Update task run count
        update_scheduled_task(task_id, {
            'run_count': task['run_count'] + 1,
            'success_count': task['success_count'] + 1,
            'last_run_at': start.isoformat()
        })
    except Exception as e:
        success = False
        error_msg = str(e)
    return success, error_msg if not success else "Task completed"


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOGS
# ══════════════════════════════════════════════════════════════════════════════

def get_activity_logs(filters: dict = None, limit: int = 100):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM activity_logs WHERE 1=1"
    params = []
    if filters:
        if filters.get('event_type'):
            query += " AND event_type LIKE ?"
            params.append(f"%{filters['event_type']}%")
        if filters.get('platform'):
            query += " AND platform = ?"
            params.append(filters['platform'])
        if filters.get('account_id'):
            query += " AND account_id = ?"
            params.append(filters['account_id'])
        if filters.get('success') is not None:
            query += " AND success = ?"
            params.append(filters['success'])
    query += f" ORDER BY timestamp DESC LIMIT {limit}"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_activity_log(data: dict):
    conn = get_db()
    cur = conn.cursor()
    metadata = data.get('metadata')
    if isinstance(metadata, dict):
        metadata = json.dumps(metadata)
    cur.execute("""
        INSERT INTO activity_logs (event_type, platform, account_id, emulator_id, proxy_id, task_id,
            description, metadata, streams_delta, listeners_delta, followers_delta, likes_delta,
            success, duration_ms, ip_used, user_agent, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['event_type'], data.get('platform'), data.get('account_id'), data.get('emulator_id'),
          data.get('proxy_id'), data.get('task_id'), data.get('description'), metadata,
          data.get('streams_delta', 0), data.get('listeners_delta', 0), data.get('followers_delta', 0),
          data.get('likes_delta', 0), data.get('success', 1), data.get('duration_ms'),
          data.get('ip_used'), data.get('user_agent'), data.get('timestamp')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_streaming_stats_summary():
    """Get aggregate streaming stats per platform."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT platform, COUNT(*) as account_count, SUM(total_plays) as total_plays,
               SUM(total_followers) as total_followers, SUM(monthly_listeners) as total_listeners
        FROM streaming_accounts
        GROUP BY platform
    """)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_growth_stats(days: int = 30):
    """Get growth statistics over N days."""
    conn = get_db()
    cur = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    cur.execute(f"""
        SELECT DATE(timestamp) as date,
               SUM(streams_delta) as streams,
               SUM(followers_delta) as followers,
               SUM(listeners_delta) as listeners,
               SUM(likes_delta) as likes,
               COUNT(*) as events
        FROM activity_logs
        WHERE timestamp >= ? AND success = 1
        GROUP BY DATE(timestamp)
        ORDER BY date ASC
    """, (cutoff,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════════
# TIKTOK
# ══════════════════════════════════════════════════════════════════════════════

def get_tiktok_accounts(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM tiktok_accounts WHERE 1=1"
    params = []
    if filters:
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
    query += " ORDER BY created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_tiktok_account(account_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tiktok_accounts WHERE id = ?", (account_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_tiktok_account(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tiktok_accounts (username, email, password, phone, display_name, profile_url,
            proxy_id, emulator_id, profile_id, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['username'], data.get('email'), data.get('password'), data.get('phone'),
          data.get('display_name'), data.get('profile_url'), data.get('proxy_id'),
          data.get('emulator_id'), data.get('profile_id'), data.get('status', 'active'),
          data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_tiktok_account(account_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    fields += ", updated_at = CURRENT_TIMESTAMP"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE tiktok_accounts SET {fields} WHERE id = ?", tuple(data.values()) + (account_id,))
    conn.commit()
    conn.close()


def delete_tiktok_account(account_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tiktok_accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()


def get_tiktok_campaigns(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT c.*, t.title as track_title, a.title as album_title FROM tiktok_campaigns c LEFT JOIN tracks t ON c.track_id = t.id LEFT JOIN albums a ON c.album_id = a.id WHERE 1=1"
    params = []
    if filters:
        if filters.get('status'):
            query += " AND c.status = ?"
            params.append(filters['status'])
    query += " ORDER BY c.created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_tiktok_campaign(data: dict):
    conn = get_db()
    cur = conn.cursor()
    if isinstance(data.get('target_account_ids'), list):
        data = dict(data)
        data['target_account_ids'] = json.dumps(data['target_account_ids'])
    if isinstance(data.get('hashtags'), list):
        data = dict(data)
        data['hashtags'] = json.dumps(data['hashtags'])
    scheduled = data.get('scheduled_at')
    if scheduled and hasattr(scheduled, 'isoformat'):
        data = dict(data)
        data['scheduled_at'] = scheduled.isoformat()
    cur.execute("""
        INSERT INTO tiktok_campaigns (campaign_name, track_id, album_id, description, video_file_path,
            caption, hashtags, target_account_ids, status, scheduled_at, posted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['campaign_name'], data.get('track_id'), data.get('album_id'), data.get('description'),
          data.get('video_file_path'), data.get('caption'), data.get('hashtags'),
          data.get('target_account_ids'), data.get('status', 'draft'),
          data.get('scheduled_at'), data.get('posted_at')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_tiktok_campaign(campaign_id: int, data: dict):
    if 'target_account_ids' in data and isinstance(data['target_account_ids'], list):
        data = dict(data)
        data['target_account_ids'] = json.dumps(data['target_account_ids'])
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE tiktok_campaigns SET {fields} WHERE id = ?", tuple(data.values()) + (campaign_id,))
    conn.commit()
    conn.close()


def delete_tiktok_campaign(campaign_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tiktok_campaigns WHERE id = ?", (campaign_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# AI PLAYLISTS
# ══════════════════════════════════════════════════════════════════════════════

def get_ai_playlists():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ai_playlists ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_ai_playlist(data: dict):
    conn = get_db()
    cur = conn.cursor()
    if isinstance(data.get('track_ids'), list):
        data = dict(data)
        data['track_ids'] = json.dumps(data['track_ids'])
    cur.execute("""
        INSERT INTO ai_playlists (playlist_name, description, genre, mood, platform, playlist_url,
            track_ids, generated_with, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['playlist_name'], data.get('description'), data.get('genre'),
          data.get('mood'), data.get('platform', 'Spotify'), data.get('playlist_url'),
          data.get('track_ids'), data.get('generated_with', 'openai'), data.get('notes')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def delete_ai_playlist(playlist_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM ai_playlists WHERE id = ?", (playlist_id,))
    conn.commit()
    conn.close()
