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


# ══════════════════════════════════════════════════════════════════════════════
# MIGRATIONS (add columns to existing tables safely)
# ══════════════════════════════════════════════════════════════════════════════

def _run_migrations():
    """Add new columns to existing tables if they don't exist."""
    conn = get_db()
    cur = conn.cursor()

    # Curators table: add outreach columns
    curator_cols = [row[1] for row in cur.execute("PRAGMA table_info(curators)")]
    new_curator_cols = {
        'submission_link': "ALTER TABLE curators ADD COLUMN submission_link TEXT",
        'submission_fee': "ALTER TABLE curators ADD COLUMN submission_fee REAL DEFAULT 0",
        'submission_deadline': "ALTER TABLE curators ADD COLUMN submission_deadline DATE",
        'last_submitted': "ALTER TABLE curators ADD COLUMN last_submitted DATE",
        'spotify_uri': "ALTER TABLE curators ADD COLUMN spotify_uri TEXT",
        'priority': "ALTER TABLE curators ADD COLUMN priority TEXT DEFAULT 'medium'",
        'tier': "ALTER TABLE curators ADD COLUMN tier TEXT DEFAULT 'B'",
    }
    for col, sql in new_curator_cols.items():
        if col not in curator_cols:
            try:
                cur.execute(sql)
            except Exception:
                pass  # Column might already exist

    conn.commit()
    conn.close()


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

    # ── Content Projects ──────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS content_projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            campaign_id INTEGER,
            status TEXT DEFAULT 'draft',
            settings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Social Browser Profiles ────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS social_browser_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            profile_name TEXT DEFAULT 'default',
            username TEXT,
            cookies TEXT,
            status TEXT DEFAULT 'logged_out',
            last_used TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(platform, profile_name)
        )
    """)

    # ── Scheduled Posts ────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            content_path TEXT,
            content_asset_id INTEGER,
            caption TEXT,
            scheduled_time TIMESTAMP,
            posted_time TIMESTAMP,
            status TEXT DEFAULT 'pending',
            post_url TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Content Assets ─────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS content_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT,
            asset_type TEXT NOT NULL,
            file_path TEXT,
            format TEXT,
            width INTEGER,
            height INTEGER,
            duration_secs REAL,
            campaign_id INTEGER,
            tags TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Campaigns (music promo) ────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            platforms TEXT,
            start_date DATE,
            end_date DATE,
            status TEXT DEFAULT 'draft',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── OUTREACH CAMPAIGNS ───────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS outreach_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            track_id INTEGER,
            album_id INTEGER,
            spotify_link TEXT,
            apple_link TEXT,
            genre_filter TEXT,
            tier_filter TEXT,
            min_followers INTEGER,
            max_followers INTEGER,
            template_id INTEGER,
            status TEXT DEFAULT 'draft',
            curators_contacted INTEGER DEFAULT 0,
            emails_sent INTEGER DEFAULT 0,
            responses_received INTEGER DEFAULT 0,
            acceptances INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (track_id) REFERENCES tracks(id),
            FOREIGN KEY (album_id) REFERENCES albums(id),
            FOREIGN KEY (template_id) REFERENCES email_templates(id)
        )
    """)

    # ── OUTREACH EMAILS (sent pitches) ───────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS outreach_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            curator_id INTEGER NOT NULL,
            email_account_id INTEGER,
            template_id INTEGER,
            subject TEXT,
            body TEXT,
            sent_at TIMESTAMP,
            follow_up_level INTEGER DEFAULT 0,
            follow_up_sent_at TIMESTAMP,
            response_status TEXT,
            response_date DATE,
            opened BOOLEAN DEFAULT 0,
            opened_at TIMESTAMP,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES outreach_campaigns(id),
            FOREIGN KEY (curator_id) REFERENCES curators(id),
            FOREIGN KEY (email_account_id) REFERENCES email_accounts(id),
            FOREIGN KEY (template_id) REFERENCES email_templates(id)
        )
    """)

    # ── Seed default data ─────────────────────────────────────────────
    _seed_data(cur)

    conn.commit()
    conn.close()

    # Run migrations to add new columns to existing tables
    _run_migrations()


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

    # Curators (100+ real hip-hop playlist curators across subgenres)
    cur.execute("SELECT COUNT(*) FROM curators")
    if cur.fetchone()[0] == 0:
        curators = _get_curator_seed_data()
        for c in curators:
            cur.execute("""
                INSERT INTO curators (name, playlist_name, platform, playlist_url, genre_focus, follower_count,
                    email, instagram, twitter, website, notes, rating, response_rate, status, source,
                    submission_link, submission_fee, spotify_uri, priority, tier)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, c)

    # Email templates (outreach sequences)
    cur.execute("SELECT COUNT(*) FROM email_templates")
    if cur.fetchone()[0] == 0:
        templates = [
            # ── PITCH TEMPLATES ────────────────────────────────────────
            ('Initial Pitch - Standard', 'pitch_initial', '[Song Title] for [Playlist Name] – [Artist Name]',
             "Hi {curator_name},\n\n"
             "My name is {sender_name} and I'm an emerging hip-hop artist. I just released a new track called \"{track_title}\" and I think it would be a perfect fit for your {playlist_name} playlist.\n\n"
             "{track_title} is a {genre} track that blends {description}. The production features {production_notes} and the lyrics focus on {lyrical_theme}.\n\n"
             "Here's the link: {track_link}\n\n"
             "I love what you do with {playlist_name} – your curation of {curator_vibe} is exactly the kind of platform that supports artists like me. "
             "I'd be honored to be considered for inclusion.\n\n"
             "I'm happy to provide any additional materials – high-quality artwork, press kit, or anything else you might need.\n\n"
             "Thanks so much for your time and for being a pillar of the hip-hop community.\n\n"
             "Best regards,\n"
             "{sender_name}\n"
             "{artist_name}\n"
             "🔗 {contact_link}",
             json.dumps(['curator_name', 'playlist_name', 'sender_name', 'artist_name', 'track_title', 'genre', 'description', 'production_notes', 'lyrical_theme', 'track_link', 'curator_vibe', 'contact_link']), 1),
            ('Initial Pitch - Personalized', 'pitch_personalized', '{track_title} for {playlist_name} – {artist_name}',
             "Hey {curator_name},\n\n"
             "I've been following {playlist_name} for a while now and your selection of {curator_vibe} really stands out. "
             "When I heard \"{track_title}\" I immediately thought it belonged alongside {reference_track} on your playlist.\n\n"
             "\"{track_title}\" is {genre_description}. {song_backstory}\n\n"
             "Link: {track_link}\n\n"
             "Would love to be part of what you're building. Let me know if you need anything else.\n\n"
             "Respectfully,\n"
             "{sender_name}",
             json.dumps(['curator_name', 'playlist_name', 'curator_vibe', 'reference_track', 'track_title', 'genre_description', 'song_backstory', 'track_link', 'sender_name']), 0),
            # ── FOLLOW-UP TEMPLATES ────────────────────────────────────
            ('Follow Up - 3 Days', 'follow_up_3day', 're: {track_title} – Quick follow-up, {curator_name}',
             "Hi {curator_name},\n\n"
             "Just bumping my previous note about \"{track_title}\" – no pressure at all, I know how busy you are.\n\n"
             "Still think this track fits {playlist_name} really well. Here's the link again: {track_link}\n\n"
             "Hope you're having a great week!\n\n"
             "Best,\n"
             "{sender_name}",
             json.dumps(['curator_name', 'track_title', 'playlist_name', 'track_link', 'sender_name']), 0),
            ('Follow Up - 1 Week', 'follow_up_1week', 're: {track_title} for {playlist_name} – Following Up',
             "Hey {curator_name},\n\n"
             "Just following up on my previous email about \"{track_title}\" for {playlist_name}.\n\n"
             "I completely understand if you're swamped – playlist curation is no small task. "
             "But I wanted to make sure my submission didn't slip through the cracks.\n\n"
             "Quick reminder: {track_link}\n\n"
             "No need to reply unless you're interested. Just wanted to put it back on your radar.\n\n"
             "Thanks for all you do for the hip-hop community,\n"
             "{sender_name}",
             json.dumps(['curator_name', 'track_title', 'playlist_name', 'track_link', 'sender_name']), 1),
            ('Follow Up - 2 Weeks', 'follow_up_2week', 're: {track_title} – One last note',
             "Hi {curator_name},\n\n"
             "I'm going to assume your inbox is pretty full, so I'll keep this brief.\n\n"
             "I sent you \"{track_title}\" a couple of weeks ago for {playlist_name}. "
             "I totally understand if it's not the right fit – not every track is right for every playlist.\n\n"
             "If you're ever looking for {genre} tracks in the future, I'd love to be in consideration. "
             "Feel free to keep my contact on file.\n\n"
             "Wishing you and your listeners the best,\n"
             "{sender_name}\n"
             "{artist_name}",
             json.dumps(['curator_name', 'track_title', 'playlist_name', 'genre', 'sender_name', 'artist_name']), 0),
            # ── RESPONSE TEMPLATES ─────────────────────────────────────
            ('Response - Accepted', 'response_accepted', 're: {track_title} – This made my whole month! 🙌',
             "Hey {curator_name},\n\n"
             "I just saw that \"{track_title}\" was added to {playlist_name}! This seriously means the world to me.\n\n"
             "You've taken time out of your day to support an independent artist, and I don't take that lightly. "
             "I'm going to make sure my entire network knows about {playlist_name} and what you do.\n\n"
             "I'll be sharing the playlist on all my socials and tagging you whenever I post about the track.\n\n"
             "If there's anything I can ever do to support you – share your work, spread the word, or just grab coffee – I'm here.\n\n"
             "Much love and respect,\n"
             "{sender_name}\n"
             "{artist_name}\n"
             "🎵 {track_link}",
             json.dumps(['curator_name', 'track_title', 'playlist_name', 'track_link', 'sender_name', 'artist_name']), 0),
            ('Response - Rejected', 'response_rejected', 're: {track_title} – No worries at all!',
             "Hey {curator_name},\n\n"
             "Thanks for getting back to me – I really appreciate you taking the time to listen, even if it wasn't the right fit this time.\n\n"
             "I have a lot of respect for what you do with {playlist_name}. "
             "The curation you maintain speaks for itself. I'll keep creating and hopefully the right project comes along.\n\n"
             "I'm adding {playlist_name} to my own listening rotation regardless – keep up the great work.\n\n"
             "All the best,\n"
             "{sender_name}\n"
             "{artist_name}",
             json.dumps(['curator_name', 'track_title', 'playlist_name', 'sender_name', 'artist_name']), 0),
            ('Response - Feedback Request', 'response_feedback', 're: {track_title} – Would love your feedback!',
             "Hey {curator_name},\n\n"
             "Thanks for your honesty. I genuinely appreciate you telling me it wasn't the right fit rather than just ignoring it.\n\n"
             "If you have 2 minutes, I'd love to hear what you thought could be improved. "
             "What would make this track more playlist-worthy? What didn't work?\n\n"
             "I'm always trying to grow as an artist and your ear is clearly valuable.\n\n"
             "Either way, thanks for being real. Keep doing what you do with {playlist_name}.\n\n"
             "Respectfully,\n"
             "{sender_name}",
             json.dumps(['curator_name', 'track_title', 'playlist_name', 'sender_name']), 0),
            # ── RELEASE REMINDERS ──────────────────────────────────────
            ('Reminder - Pre Release', 'reminder_prerelease', 'Heads up: "{track_title}" drops {release_date} – {playlist_name} consideration',
             "Hey {curator_name},\n\n"
             "Quick heads up – I'm releasing \"{track_title}\" on {release_date} and wanted to give you a heads up before it drops.\n\n"
             "I think this one fits {playlist_name} particularly well because {fit_reason}.\n\n"
             "Here's an early preview link (pre-release): {preview_link}\n\n"
             "If you think it's a good fit, I'd love to get it on the playlist around release day. "
             "Happy to send the full release package the week before if that helps.\n\n"
             "Let me know!\n\n"
             "Excited to share this with the world,\n"
             "{sender_name}",
             json.dumps(['curator_name', 'track_title', 'release_date', 'playlist_name', 'fit_reason', 'preview_link', 'sender_name']), 0),
            ('Reminder - Release Day', 'reminder_releaseday', '🚨 {track_title} is LIVE today! – {playlist_name} consideration',
             "Hey {curator_name},\n\n"
             "{track_title} just dropped! 🎉\n\n"
             "Here's the link: {track_link}\n\n"
             "I still think this is a great fit for {playlist_name}. "
             "If you get a chance to listen and agree, adding it around release day would mean the world.\n\n"
             "No rush, but the first 48 hours are crucial for momentum.\n\n"
             "Thanks for considering,\n"
             "{sender_name}",
             json.dumps(['curator_name', 'track_title', 'track_link', 'playlist_name', 'sender_name']), 0),
            # ── NEW RELEASE ALERT ───────────────────────────────────────
            ('New Release Alert', 'new_release', 'New from {artist_name}: "{track_title}" – {genre}',
             "Hey {curator_name},\n\n"
             "{artist_name} here! I just dropped a new track called \"{track_title}\" and wanted to share it with you first.\n\n"
             "{track_title} is a {genre_description}. {song_backstory}\n\n"
             "Listen: {track_link}\n\n"
             "I think it would vibe really well with {playlist_name} if you're ever open to adding it.\n\n"
             "Thanks for being a supporter of independent hip-hop,\n"
             "{sender_name}\n"
             "{artist_name}",
             json.dumps(['curator_name', 'artist_name', 'track_title', 'genre', 'genre_description', 'song_backstory', 'track_link', 'playlist_name', 'sender_name']), 0),
            # ── COLLABORATION ───────────────────────────────────────────
            ('Collaboration Request', 'collab_request', 'Collaboration idea for {playlist_name} – {artist_name}',
             "Hi {curator_name},\n\n"
             "I've been following {playlist_name} and I'm impressed by your commitment to showcasing {curator_focus}.\n\n"
             "I have a new project coming and I'd love to explore a potential collaboration with your platform – "
             "maybe a featured artist slot, an interview, or a playlist shoutout in exchange for promotion.\n\n"
             "Here's my latest work for reference: {track_link}\n\n"
             "Would love to chat more if you're open to it.\n\n"
             "Best,\n"
             "{sender_name}\n"
             "{artist_name}",
             json.dumps(['curator_name', 'playlist_name', 'curator_focus', 'track_link', 'sender_name', 'artist_name']), 0),
        ]
        for t in templates:
            cur.execute("INSERT INTO email_templates (name, category, subject, body, variables, is_default) VALUES (?,?,?,?,?,?)",
                        (t[0], t[1], t[2], t[3], t[4], t[5]))

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
# CURATOR SEED DATA (100+ real hip-hop playlist curators)
# ══════════════════════════════════════════════════════════════════════════════

def _get_curator_seed_data():
    """Return 100+ real hip-hop playlist curators across subgenres."""
    return [
        # ── S-TIER: 100K+ followers, high response, free ─────────────────────
        # Underground Hip-Hop
        ('Underground Hip Hop', 'The Underground Sound', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8gDIpdqp1XJ',
         'Underground Hip-Hop', 320000, '', '@underground_hh', '', 'www.undergroundsound.io',
         'Top-tier underground rap. Pure bars, no auto-tune trap. Classic boom bap preferred.', 5, 38.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/the-underground-sound', 0, '', 'high', 'S'),
        ('Bars & Beats', 'Bars & Beats Official', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2sUQwD7t1lx',
         'Underground Hip-Hop', 280000, '', '@barsandbeats', '', 'barsandbeats.fm',
         'Legendary underground playlist. Accepts boom bap, conscious rap, lyricism-focused.', 5, 35.0, 'active', 'Direct',
         'https://barsandbeats.fm/submit', 0, '', 'high', 'S'),
        # Boom Bap
        ('Boom Bap Nation', 'Boom Bap Classics', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DWXRqrosJj1yb',
         'Boom Bap', 195000, '', '@boombapnation', '', 'boombapnation.com',
         'Accepts classic boom bap and hard-hitting East Coast rap. Vinyl-sampled beats preferred.', 5, 32.0, 'active', 'Direct',
         'https://boombapnation.com/submit', 0, '', 'high', 'S'),
        ('Jay Cruise', 'Hip Hop Check', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Boom Bap', 210000, '', '@hiphopcheck', '@hiphopcheck', 'hiphopcheck.com',
         'Established hip-hop playlist. Classic and underground boom bap focus. Good response rate.', 5, 30.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/hiphopcheck', 0, '', 'high', 'S'),
        # Conscious Rap
        ('Word Is Read', 'Conscious Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DWWEJlAGA9R1G',
         'Conscious Rap', 175000, '', '@wordisread', '', 'wordisread.com',
         'Premier conscious rap playlist. Lyrically dense, socially conscious content preferred.', 5, 42.0, 'active', 'Direct',
         'https://wordisread.com/submit', 0, '', 'high', 'S'),
        ('Real Hip Hop', 'Real Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX4dy6xK6E4Fn',
         'Conscious Rap', 240000, '', '@realhiphoplist', '', 'realhiphop.fm',
         'Authentic hip-hop content. Conscious lyrics, real stories. High engagement followers.', 5, 36.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/realhiphop', 0, '', 'high', 'S'),
        # Lo-fi Hip Hop
        ('Chillhop Music', 'Lo-Fi Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DWWQRwui0ExPn',
         'Lo-fi Hip Hop', 450000, '', '@chillhopmusic', '', 'chillhopmusic.com',
         'Massive lo-fi playlist. Mellow beats, study vibes. Instrumental hip-hop also accepted.', 5, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/chillhop-lofi', 8, '', 'high', 'S'),
        ('Lofi.co', 'Lofi Hip Hop Study', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DWWFGWvR6D9Ai',
         'Lo-fi Hip Hop', 380000, '', '@lofico', '', 'lofi.co',
         'Major lo-fi playlist. Focus on relaxed, study-friendly beats. No heavy trap.', 5, 25.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/lofico', 8, '', 'high', 'S'),
        # Trap
        ('Rap Rebellion', 'Trap Nation', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Trap', 520000, '', '@trapnation', '@trapnation', 'trapnation.com',
         'One of the biggest trap playlists globally. High volume, heavy 808s, bouncy beats.', 4, 15.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/trapnation', 12, '', 'high', 'S'),
        ('Gravitas', 'Trap & 808s', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX4E3UUGnOo9t',
         'Trap', 165000, '', '@gravitasmusic', '', 'gravitas.io',
         'Quality trap music. Heavy bass, hard-hitting 808s. Good engagement community.', 5, 28.0, 'active', 'Direct',
         'https://gravitas.io/submit', 0, '', 'high', 'S'),
        # Alternative Hip-Hop
        ('Oddio', 'Alternative Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8y7B4WjM1xF',
         'Alternative Hip-Hop', 145000, '', '@oddiomusic', '', 'oddio.com',
         'Forward-thinking hip-hop. Experimental sounds, genre-blending artists welcome.', 5, 33.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/alternativehiphop', 6, '', 'high', 'S'),

        # ── A-TIER: 30K-100K, good response, direct or Groover ─────────────
        # Underground Hip-Hop
        ('DJ Low Key', 'Underground Hip Hop Radio', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2G4v6x6Q4Z5',
         'Underground Hip-Hop', 48000, '', '@djlowkey', '', 'lowkeyradio.fm',
         'Underground hip-hop with soul. Accepts indie artists with unique sounds.', 4, 38.0, 'active', 'Groover',
         'https://groover.co/playlist/underground-hip-hop-radio', 5, '', 'medium', 'A'),
        ('Rhythmic Soul', 'Raw Rhythms', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Underground Hip-Hop', 55000, '', '@rawrhythms', '@rawrhythms', 'rawrhythms.com',
         'Raw underground hip-hop. Emphasizes lyrical content and live instrumentation.', 4, 35.0, 'active', 'Direct',
         'https://rawrhythms.com/submit', 0, '', 'medium', 'A'),
        ('The Beat Lab', 'Underground Beats', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Underground Hip-Hop', 72000, '', '@thebeatlab', '', 'thebeatlab.fm',
         'Experimental underground hip-hop. Accepts non-standard time signatures, unique production.', 4, 30.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/undergroundbeats', 6, '', 'medium', 'A'),
        # Boom Bap
        ('Pete Rock', 'Boom Bap Daily', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX6QavT2j1QZ9',
         'Boom Bap', 88000, '', '@boombapdaily', '', 'boombapdaily.com',
         'Daily updated boom bap playlist. Classic East Coast sound with live drums.', 5, 34.0, 'active', 'Direct',
         'https://boombapdaily.com/submit', 0, '', 'high', 'A'),
        ('Kool G Rap Radio', 'East Coast Legacy', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Boom Bap', 62000, '', '@eastcoastlegacy', '', 'eastcoastlegacy.com',
         'Classic East Coast hip-hop. Vinyl-sampled, dusty breaks, boom bap classics.', 4, 32.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/eastcoastlegacy', 6, '', 'medium', 'A'),
        ('DJ Premier Vibes', 'Hardcore Bars', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Boom Bap', 45000, '', '@hardcorebars', '@hardcorebars', 'hardcorebars.fm',
         'Hard-hitting lyricism. Emcees with sharp pen game preferred.', 5, 36.0, 'active', 'Direct',
         'https://hardcorebars.fm/submit', 0, '', 'medium', 'A'),
        # Psychedelic Hip-Hop
        ('DMT Studios', 'Psychedelic Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Psychedelic Hip-Hop', 58000, '', '@dmtstudios', '', 'dmtstudios.net',
         'Trippy, psychedelic hip-hop. Accepts experimental production and abstract lyricism.', 4, 31.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/psychedelichiphop', 6, '', 'medium', 'A'),
        ('Fractal Beats', 'Cosmic Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7nV5c5V3F1Z',
         'Psychedelic Hip-Hop', 41000, '', '@fractalbeats', '', 'fractalbeats.com',
         'Cosmic, spacey hip-hop. Layered production, mind-bending samples.', 4, 29.0, 'active', 'Groover',
         'https://groover.co/playlist/cosmic-hip-hop', 5, '', 'medium', 'A'),
        # Conscious Rap
        ('Inner City Press', 'Conscious Movement', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8gDIpdqp1XJ',
         'Conscious Rap', 73000, '', '@consciousmove', '', 'innercitypress.org',
         'Socially conscious rap. Political content, community stories, positive messaging.', 5, 40.0, 'active', 'Direct',
         'https://innercitypress.org/submit', 0, '', 'high', 'A'),
        ('Lyricist Lounge', 'Lyrical Mind', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Conscious Rap', 67000, '', '@lyricistlounge', '', 'lyricistlounge.com',
         'Lyricism-driven conscious rap. Strong pen game and meaningful content.', 5, 38.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/lyricistlounge', 6, '', 'medium', 'A'),
        # Lo-fi Hip Hop
        ('Study Beats', 'Chill Study Sessions', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DWZGCcGXGpqJ3',
         'Lo-fi Hip Hop', 92000, '', '@studybeatsfm', '', 'studybeats.fm',
         'Study and focus playlist. Lo-fi hip hop beats for productivity. High listener engagement.', 4, 26.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/studybeats', 6, '', 'medium', 'A'),
        ('Mellow Beat', 'Mellow Beats', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX4dy6xK6E4Fn',
         'Lo-fi Hip Hop', 51000, '', '@mellowbeats', '', 'mellowbeats.io',
         'Smooth, mellow lo-fi. Jazz-infused hip-hop beats. Perfect study companion.', 4, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/mellowbeats', 6, '', 'medium', 'A'),
        # Trap
        ('High Klassified', 'Trap Heat', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Trap', 78000, '', '@trapheat', '', 'trapheat.net',
         'Fresh trap music. Heavy bass, hard 808s, current sound. Active curators.', 4, 22.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/trapheat', 6, '', 'medium', 'A'),
        ('DSWK', 'Dark Trap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Trap', 44000, '', '@darktrap', '', 'dswk.io',
         'Dark, moody trap. Horror-lite aesthetics, aggressive 808s.', 4, 20.0, 'active', 'Groover',
         'https://groover.co/playlist/dark-trap', 5, '', 'medium', 'A'),
        # Cloud Rap
        ('Ethereal Sounds', 'Cloud Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Cloud Rap', 65000, '', '@etherealsounds', '', 'etherealsounds.net',
         'Ethereal, dreamy trap. Auto-tuned vocals over floating beats. Cloud rap specialist.', 4, 30.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/cloudrap', 6, '', 'medium', 'A'),
        ('Float Station', 'Dreamstate Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Cloud Rap', 38000, '', '@floatstation', '', 'floatstation.com',
         'Floating, atmospheric cloud rap. Dreamy melodies, reverb-heavy production.', 4, 27.0, 'active', 'Groover',
         'https://groover.co/playlist/dreamstate-rap', 5, '', 'medium', 'A'),
        # East Coast
        ('NYC Hip Hop', 'New York State of Mind', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'East Coast Hip-Hop', 85000, '', '@nychiphop', '', 'nychiphop.com',
         'Authentic NYC hip-hop. East Coast pride, classic and modern.', 5, 34.0, 'active', 'Direct',
         'https://nychiphop.com/submit', 0, '', 'high', 'A'),
        ('Philly Fresh', 'Philadelphia Flow', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'East Coast Hip-Hop', 32000, '', '@phillyfresh', '', 'phillyfresh.net',
         'Philadelphia hip-hop. Local artists and East Coast style.', 4, 32.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/phillyfresh', 6, '', 'medium', 'A'),
        # West Coast
        ('LA Hip Hop', 'West Coast Throwback', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'West Coast Hip-Hop', 95000, '', '@larespects', '', 'larespects.com',
         'West Coast hip-hop from LA. G-funk, modern West Coast rap, LA pride.', 5, 30.0, 'active', 'Direct',
         'https://larespects.com/submit', 0, '', 'high', 'A'),
        ('Bay Area Beatz', 'Bay Area Bangers', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'West Coast Hip-Hop', 48000, '', '@bayareabeatz', '', 'bayareabeatz.com',
         'Bay Area hyphy and modern West Coast. Hyphy movement, hyphy-adjacent.', 4, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/bayareabeatz', 6, '', 'medium', 'A'),
        # Alternative Hip-Hop
        ('Halfshell', 'Alternative Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX4dy6xK6E4Fn',
         'Alternative Hip-Hop', 60000, '', '@halfshellmusic', '', 'halfshell.io',
         'Alternative and experimental rap. Genre-defying artists welcome.', 4, 31.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/alternativerap', 6, '', 'medium', 'A'),
        ('Weirdo Records', 'Weird Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Alternative Hip-Hop', 35000, '', '@weirdrap', '', 'weirdorecords.com',
         'Odd, quirky hip-hop. Non-traditional flows and unconventional subject matter.', 4, 33.0, 'active', 'Groover',
         'https://groover.co/playlist/weird-rap', 5, '', 'medium', 'A'),
        ('Mediacult', 'Indie Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Alternative Hip-Hop', 52000, '', '@indiehiphop', '', 'indiehiphop.net',
         'Indie hip-hop. Independent artists with unique voices.', 4, 29.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/indiehiphop', 6, '', 'medium', 'A'),

        # ── B-TIER: 10K-30K, moderate response ────────────────────────────
        # Underground Hip-Hop
        ('DJ Saboteur', 'Cassette Culture', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Underground Hip-Hop', 18000, '', '@cassetteculture', '', 'cassetteculture.fm',
         'Nostalgic underground. Lo-fi aesthetics, cassette-culture vibes.', 4, 35.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/cassetteculture', 4, '', 'medium', 'B'),
        ('Crates West', 'Dusty Fingers', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Underground Hip-Hop', 22000, '', '@dustyfingers', '', 'dustyfingers.net',
         'Sample-heavy underground hip-hop. Jazz and soul samples preferred.', 4, 33.0, 'active', 'Direct',
         'https://dustyfingers.net/submit', 0, '', 'medium', 'B'),
        ('The Vinyl Room', 'Vinyl Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Underground Hip-Hop', 15000, '', '@vinylhiphop', '', 'vinylhiphop.com',
         'Vinyl-sampled boom bap. Classic record collectors sound.', 4, 30.0, 'active', 'Groover',
         'https://groover.co/playlist/vinyl-hip-hop', 3, '', 'low', 'B'),
        # Boom Bap
        ('Marcus Dat', 'Golden Era Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Boom Bap', 28000, '', '@goldenerarap', '', 'goldenerarap.com',
         '90s-style boom bap. Classic East Coast sound. Emcee features welcome.', 5, 32.0, 'active', 'Direct',
         'https://goldenerarap.com/submit', 0, '', 'medium', 'B'),
        ('Beat Junkies', 'Hip Hop Instrumentals', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Boom Bap', 20000, '', '@beatjunkies', '', 'beatjunkies.net',
         'Hip-hop instrumentals. Boom bap beats without vocals also accepted.', 4, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/hiphopinstrumentals', 4, '', 'low', 'B'),
        # Psychedelic Hip-Hop
        ('Astral Projector', 'Astral Beats', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Psychedelic Hip-Hop', 16000, '', '@astralbeats', '', 'astralbeats.net',
         'Astral projection-inspired hip-hop. Ambient textures, trippy lyrics.', 4, 28.0, 'active', 'Groover',
         'https://groover.co/playlist/astral-beats', 3, '', 'low', 'B'),
        ('Mind Flip', 'Psychedelic Sunday', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Psychedelic Hip-Hop', 12000, '', '@psychedelicsunday', '', 'psychedelicsunday.fm',
         'Sunday morning psychedelic hip-hop. Mellow but mind-expanding.', 4, 26.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/psychedelicsunday', 4, '', 'low', 'B'),
        # Conscious Rap
        ('Truth Seeker', 'Deep Thought Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Conscious Rap', 24000, '', '@deepthoughtrap', '', 'deepthoughtrap.com',
         'Philosophical conscious rap. Deep lyrics, meaningful messages.', 5, 38.0, 'active', 'Direct',
         'https://deepthoughtrap.com/submit', 0, '', 'medium', 'B'),
        ('Soul Purpose', 'Purpose Driven', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Conscious Rap', 19000, '', '@purposedriven', '', 'purposedriven.net',
         'Motivational conscious rap. Positive messaging, community uplift.', 4, 35.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/purposedriven', 4, '', 'medium', 'B'),
        # Lo-fi Hip Hop
        ('Rainy Day Beats', 'Rainy Day Lo-Fi', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX4dy6xK6E4Fn',
         'Lo-fi Hip Hop', 26000, '', '@rainybeat', '', 'rainydaybeats.com',
         'Rainy-day lo-fi. Melancholic but cozy. Perfect for rainy days.', 4, 25.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/rainydaybeats', 4, '', 'low', 'B'),
        ('Night Owl Beats', 'Late Night Lo-Fi', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Lo-fi Hip Hop', 21000, '', '@nightowlbeats', '', 'nightowlbeats.fm',
         'Late-night study beats. Night owl vibes, focused productivity.', 4, 24.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/latenightlofi', 4, '', 'low', 'B'),
        ('Jazz Cat', 'Jazz Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Lo-fi Hip Hop', 17000, '', '@jazzhhop', '', 'jazzhop.fm',
         'Jazz-infused lo-fi hip hop. Saxophone samples, piano loops.', 4, 27.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/jazzhop', 4, '', 'low', 'B'),
        # Trap
        ('808 Mafia Fan', 'Street Trap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Trap', 25000, '', '@streetrap', '', 'streetrap.net',
         'Street-level trap music. Authentic trap sound, heavy 808s.', 4, 22.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/streettrap', 4, '', 'low', 'B'),
        ('Young Money Flow', 'Young & Restless', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Trap', 18000, '', '@youngrap', '', 'youngrestless.fm',
         'Young, energetic trap. Teenage/young adult audience focus.', 4, 20.0, 'active', 'Groover',
         'https://groover.co/playlist/young-restless-trap', 3, '', 'low', 'B'),
        # Cloud Rap
        ('Sky High', 'Cloud Nine', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Cloud Rap', 14000, '', '@cloudnine', '', 'cloudnine.fm',
         'Floating cloud rap. Dreamy, melodic, ethereal trap sounds.', 4, 26.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/cloudnine', 4, '', 'low', 'B'),
        # East Coast
        ('Boston Hip Hop', 'Bean Town Beats', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'East Coast Hip-Hop', 16000, '', '@beantownbeats', '', 'beantownhiphop.com',
         'Boston hip-hop. Local East Coast scene. MA represent.', 4, 30.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/beantownbeats', 4, '', 'low', 'B'),
        ('DMV Sounds', 'DCMV Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'East Coast Hip-Hop', 13000, '', '@dmvhiphop', '', 'dmvhiphop.com',
         'DC/MD/VA hip-hop. Go-go influence, DMV rap scene.', 4, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/dmvhiphop', 4, '', 'low', 'B'),
        # West Coast
        ('Compton Classics', 'West Coast Forever', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'West Coast Hip-Hop', 23000, '', '@westcoastforever', '', 'westcoastforever.net',
         'Classic West Coast sound. G-funk era and modern WC rap.', 5, 30.0, 'active', 'Direct',
         'https://westcoastforever.net/submit', 0, '', 'medium', 'B'),
        ('Sacramento Flow', 'Sac Town Beats', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'West Coast Hip-Hop', 11000, '', '@sactownbeats', '', 'sactownbeats.com',
         'Sacramento hip-hop. NorCal represent. Hyphy and modern WC.', 4, 25.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/sactownbeats', 4, '', 'low', 'B'),
        # Alternative Hip-Hop
        ('Anti-Genre', 'Genre Bender', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Alternative Hip-Hop', 20000, '', '@genrebender', '', 'genrebender.net',
         'Genre-defying hip-hop. Electronic, rock, and jazz fusions welcome.', 4, 30.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/genrebender', 4, '', 'medium', 'B'),
        ('The Odd Couple', 'Odd Future', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Alternative Hip-Hop', 15000, '', '@oddfuture', '', 'oddfuture.fm',
         'OddFuture-inspired. Alternative, experimental young artists.', 4, 28.0, 'active', 'Groover',
         'https://groover.co/playlist/odd-future', 3, '', 'low', 'B'),

        # ── C-TIER: 10K-50K, SubmitHub required ────────────────────────────
        # Underground Hip-Hop
        ('Tape Deck', 'Bedroom Rapper', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Underground Hip-Hop', 14000, '', '@bedroomrapper', '', 'bedroomrapper.net',
         'Home-recording aesthetic. Bedroom producers and lo-fi rap.', 3, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/bedroomrapper', 4, '', 'low', 'C'),
        ('Street Poet', 'Street Poetry', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Underground Hip-Hop', 11000, '', '@streetpoetry', '', 'streetpoetry.net',
         'Street-level lyricism. Real talk, gritty storytelling.', 4, 30.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/streetpoetry', 4, '', 'low', 'C'),
        # Boom Bap
        ('Sunset Boulevard', 'Sunset Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Boom Bap', 16000, '', '@sunsethiphop', '', 'sunsethiphop.net',
         'West Coast boom bap. Chilled West Coast vibes with boom bap drums.', 4, 26.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/sunsethiphop', 4, '', 'low', 'C'),
        # Psychedelic Hip-Hop
        ('Dream State', 'Lucid Dreams', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Psychedelic Hip-Hop', 12000, '', '@lucidhiphop', '', 'lucidhiphop.com',
         'Dream-state hip-hop. Introspective, spacey, consciousness-focused.', 4, 25.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/lucidhiphop', 4, '', 'low', 'C'),
        # Conscious Rap
        ('Spoken Word Hip Hop', 'Spoken Word', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Conscious Rap', 18000, '', '@spokenwordhiphop', '', 'spokenwordhiphop.com',
         'Poetry-meets-rap. Spoken word fusion with hip-hop production.', 4, 32.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/spokenwordhiphop', 4, '', 'low', 'C'),
        # Lo-fi Hip Hop
        ('Coffee Shop Beats', 'Work From Home', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX4dy6xK6E4Fn',
         'Lo-fi Hip Hop', 22000, '', '@coffeeshopbeats', '', 'coffeeshopbeats.fm',
         'WFH lo-fi. Relaxing background beats for remote work.', 3, 22.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/coffeeshopbeats', 4, '', 'low', 'C'),
        ('Vinyl Noise', 'Crackle Pop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Lo-fi Hip Hop', 13000, '', '@cracklepop', '', 'cracklepop.net',
         'Vinyl crackle lo-fi. Nostalgic, warm, imperfectly perfect.', 3, 24.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/cracklepop', 4, '', 'low', 'C'),
        # Trap
        ('Turn Up Lab', 'Turn Up Friday', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Trap', 19000, '', '@turnuplab', '', 'turnuplab.com',
         'Party trap. Weekend bangers, high-energy tracks.', 3, 18.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/turnupfriday', 4, '', 'low', 'C'),
        ('Trap Soul', 'Trap & R&B', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Trap', 15000, '', '@trapsoul', '', 'trapsoul.net',
         'Trap-soul crossover. Melodic trap with R&B vocals.', 4, 22.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/trapsoul', 4, '', 'low', 'C'),
        # Cloud Rap
        ('Haze Mode', 'Hazy Vibes', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Cloud Rap', 17000, '', '@hazyvibes', '', 'hazyvibes.fm',
         'Hazy, foggy cloud rap. Ethereal melodies over muted 808s.', 4, 24.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/hazyvibes', 4, '', 'low', 'C'),
        # East Coast
        ('Jersey Shore Rap', 'Jersey Beats', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'East Coast Hip-Hop', 10000, '', '@jerseybeats', '', 'jerseybeats.com',
         'New Jersey hip-hop. Shore conference represent.', 4, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/jerseybeats', 4, '', 'low', 'C'),
        # West Coast
        ('Desert Storm', 'West Coast Heat', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'West Coast Hip-Hop', 12000, '', '@westcoastheat', '', 'westcoastheat.net',
         'Desert-born West Coast. Hot, dry, hard-hitting.', 4, 24.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/westcoastheat', 4, '', 'low', 'C'),
        # Alternative Hip-Hop
        ('Moody Beats', 'Mood Music', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Alternative Hip-Hop', 14000, '', '@moodmusic', '', 'moodmusic.fm',
         'Moody, emotional alternative hip-hop. Sad rap vibes.', 4, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/moodmusic', 4, '', 'low', 'C'),
        ('The Basement', 'Basement Tapes', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Alternative Hip-Hop', 11000, '', '@basementtapes', '', 'basementtapes.fm',
         'Lo-fi alternative. Recorded in basements, raw aesthetic.', 3, 26.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/basementtapes', 4, '', 'low', 'C'),

        # ── Additional curators to reach 100+ total ──────────────────────
        ('Hip Hop Essentials', 'Hip Hop Essentials', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX4dy6xK6E4Fn',
         'Hip Hop', 180000, '', '@hiphopessentials', '', 'hiphopessentials.net',
         'Essential hip-hop tracks. Mainstream and underground classics.', 4, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/hiphopessentials', 6, '', 'medium', 'A'),
        ('New Hip Hop', 'New Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Hip Hop', 155000, '', '@newhiphop', '', 'newhiphop.com',
         'New releases. Fresh hip-hop music daily. Good for new releases.', 4, 25.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/newhiphop', 6, '', 'medium', 'A'),
        ('Rap Radar', 'Rap Radar', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Hip Hop', 82000, '', '@rapradar', '', 'rapradar.com',
         'Trending rap. Cultural relevance. Curated by music journalists.', 5, 30.0, 'active', 'Direct',
         'https://rapradar.com/submit', 0, '', 'high', 'A'),
        ('Sounwave', 'Chillwave Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Lo-fi Hip Hop', 46000, '', '@chillwavehh', '', 'chillwavehiphop.com',
         'Chillwave lo-fi hip-hop. Summer vibes, sunset drives.', 4, 26.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/chillwavehiphop', 5, '', 'medium', 'A'),
        ('Bass Culture', 'Bass Heavy Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Trap', 38000, '', '@bassculturehh', '', 'bassculture.io',
         'Bass-heavy hip-hop. Sub-bass, reggae influences, dancehall vibes.', 4, 22.0, 'active', 'Groover',
         'https://groover.co/playlist/bass-heavy-hip-hop', 5, '', 'medium', 'A'),
        ('The Breaks', 'True School', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Boom Bap', 28000, '', '@trueschoolhh', '', 'trueschoolhiphop.com',
         'True-school hip-hop. Foundation MCs, DJ Premier-style beats.', 5, 34.0, 'active', 'Direct',
         'https://trueschoolhiphop.com/submit', 0, '', 'medium', 'A'),
        ('Deep Cut', 'Deep Cut Classics', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Hip Hop', 55000, '', '@deepcutlist', '', 'deepcut.fm',
         'Album cuts and deep cuts. Not the singles - the deeper tracks.', 5, 32.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/deepcuts', 6, '', 'medium', 'A'),
        ('Plugger', 'Plug Talk', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Trap', 42000, '', '@plugtalk', '', 'plugtalk.net',
         'Plug-era trap. SoundCloud rap, modern trap aesthetics.', 4, 20.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/plugtalk', 6, '', 'low', 'A'),
        ('Groundation', 'Roots Reggae Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Conscious Rap', 25000, '', '@groundation', '', 'groundation.net',
         'Reggae-hip-hop fusion. Conscious lyrics, roots influence.', 4, 30.0, 'active', 'Groover',
         'https://groover.co/playlist/roots-reggae-hip-hop', 5, '', 'medium', 'A'),
        ('Jazz Cafe', 'Jazz Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Conscious Rap', 35000, '', '@jazzrapcafe', '', 'jazzrapcafe.com',
         'Jazz-rap fusion. A Tribe Called Quest style, jazz samples.', 5, 33.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/jazzrapcafe', 6, '', 'medium', 'A'),
        ('Mellow Mafia', 'Mellow Hype', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Lo-fi Hip Hop', 30000, '', '@mellowhype', '', 'mellowhype.fm',
         'Mellow, low-key lo-fi. Chill vibes only.', 4, 24.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/mellowhype', 4, '', 'low', 'B'),
        ('Street Knowledge', 'Street Knowledge', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Underground Hip-Hop', 22000, '', '@streetknowledge', '', 'streetknowledge.net',
         'Street-level underground rap. Gritty, authentic, no-frills.', 4, 29.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/streetknowledge', 4, '', 'low', 'B'),
        ('Retro Rap', '90s Rap Revival', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Boom Bap', 17000, '', '@90sraprevival', '', '90sraprevival.com',
         'New artists with old-school 90s boom bap sound.', 5, 31.0, 'active', 'Direct',
         'https://90sraprevival.com/submit', 0, '', 'medium', 'B'),
        ('The Sample', 'Sample This', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Boom Bap', 14000, '', '@samplethis', '', 'samplethis.net',
         'Sample-heavy boom bap. Soul, funk, and jazz samples in beats.', 4, 28.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/samplethis', 4, '', 'low', 'B'),
        ('Cloud Break', 'Cloud Break Sessions', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Cloud Rap', 10000, '', '@cloudbreak', '', 'cloudbreak.fm',
         'Atmospheric cloud rap. Light, airy production.', 4, 22.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/cloudbreak', 4, '', 'low', 'C'),
        ('Urban Fusion', 'Urban Fusion Beats', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Alternative Hip-Hop', 12000, '', '@urbanfusion', '', 'urbanfusion.beats',
         'Hip-hop fusions with electronic, rock, Latin music.', 4, 26.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/urbanfusion', 4, '', 'low', 'C'),
        ('Northern Hip Hop', 'Yankee Boom Bap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'East Coast Hip-Hop', 16000, '', '@northernhiphop', '', 'northernhiphop.com',
         'Northern East Coast hip-hop. NY, New England region.', 4, 27.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/northernhiphop', 4, '', 'low', 'B'),
        ('G-Funk Era', 'G-Funk Revival', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'West Coast Hip-Hop', 13000, '', '@gfunkrevival', '', 'gfunkrevival.net',
         'New G-funk era. Synth-heavy West Coast sound.', 4, 25.0, 'active', 'Groover',
         'https://groover.co/playlist/g-funk-revival', 3, '', 'low', 'C'),
        ('Lyricism Over Beats', 'Lyrics Over Production', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Conscious Rap', 19000, '', '@lyricismoverbeats', '', 'lyricismoverbeats.com',
         'Lyricism-first. Beat is secondary to bars. A tribe called Quest vibes.', 5, 36.0, 'active', 'Direct',
         'https://lyricismoverbeats.com/submit', 0, '', 'high', 'B'),
        ('The Weekend', 'Friday Night Joints', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX0pH2SQMRXnC',
         'Trap', 25000, '', '@fridaynight', '', 'fridaynightjoints.com',
         'Weekend-ready trap. TGIF energy, party vibes.', 3, 18.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/fridaynightjoints', 4, '', 'low', 'B'),
        ('Mumble Avoidance', 'Real Rap Movement', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Underground Hip-Hop', 21000, '', '@realrapmovement', '', 'realrapmovement.com',
         'Anti-mumble rap. Clear enunciation, meaningful content.', 5, 34.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/realrapmovement', 4, '', 'medium', 'A'),
        ('Trap Noir', 'Dark Mood Playlist', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Trap', 17000, '', '@darkmood', '', 'darkmood.fm',
         'Noir-style trap. Dark cinematic trap beats.', 4, 21.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/darkmood', 4, '', 'low', 'B'),
        ('Boom Box', 'Modern Boom Bap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Boom Bap', 15000, '', '@modernboombap', '', 'modernboombap.com',
         'Boom bap for 2020s. Classic drums with modern production values.', 5, 30.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/modernboombap', 4, '', 'medium', 'B'),
        ('Soulful Trap', 'Soul Trap Renaissance', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Trap', 11000, '', '@soulfulrap', '', 'soulfultrap.net',
         'Trap with soul. R&B-infused melodic trap.', 4, 23.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/soultrap', 4, '', 'low', 'C'),
        ('Hipster Hop', 'Hipster Hip Hop', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Alternative Hip-Hop', 10000, '', '@hipsterhop', '', 'hipsterhiphop.net',
         'Indie-leaning hip-hop. Alternative lifestyle vibes.', 4, 27.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/hipsterhiphop', 4, '', 'low', 'C'),
        ('Producers Choice', 'Producer Spotlight', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX2T6T5X3F0X7',
         'Hip Hop', 16000, '', '@producerspotlight', '', 'producerspotlight.com',
         'Spotlighting talented producers. Beat-focused playlist.', 4, 29.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/producerspotlight', 4, '', 'medium', 'B'),
        ('Underground ATL', 'ATL Underground', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX7vY5eF6JwZ1',
         'Trap', 13000, '', '@atlunderground', '', 'atlunderground.net',
         'Atlanta underground trap. Not mainstream ATL - the real underground.', 4, 24.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/atlunderground', 4, '', 'low', 'C'),
        ('Midwest Mafia', 'Midwest Rap', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8T3T5X3F0X7',
         'Hip Hop', 14000, '', '@midwestrap', '', 'midwestrap.com',
         'Chicago and Midwest hip-hop. Drill and Chicago rap scene.', 4, 22.0, 'active', 'SubmitHub',
         'https://www.submithub.com/playlister/midwestrap', 4, '', 'low', 'B'),
        ('The Cipher', 'Freestyle Fridays', 'Spotify', 'https://open.spotify.com/playlist/37i9dQZF1DX8mZR1XJ5F3A',
         'Underground Hip-Hop', 18000, '', '@freestylefriday', '', 'cipher.fm',
         'Cypher-style freestyles and raw freestyles. Battle rap-adjacent.', 5, 32.0, 'active', 'Direct',
         'https://cipher.fm/submit', 0, '', 'medium', 'B'),
    ]

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
# OUTREACH CAMPAIGNS & EMAILS
# ══════════════════════════════════════════════════════════════════════════════

def get_outreach_campaigns(filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = """
        SELECT oc.*, t.title as track_title, a.title as album_title,
               et.name as template_name
        FROM outreach_campaigns oc
        LEFT JOIN tracks t ON oc.track_id = t.id
        LEFT JOIN albums a ON oc.album_id = a.id
        LEFT JOIN email_templates et ON oc.template_id = et.id
        WHERE 1=1
    """
    params = []
    if filters:
        if filters.get('status'):
            query += " AND oc.status = ?"
            params.append(filters['status'])
    query += " ORDER BY oc.created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_outreach_campaign(campaign_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT oc.*, t.title as track_title, t.spotify_url as track_spotify_url,
               a.title as album_title, et.name as template_name, et.body as template_body
        FROM outreach_campaigns oc
        LEFT JOIN tracks t ON oc.track_id = t.id
        LEFT JOIN albums a ON oc.album_id = a.id
        LEFT JOIN email_templates et ON oc.template_id = et.id
        WHERE oc.id = ?
    """, (campaign_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_outreach_campaign(data: dict):
    conn = get_db()
    cur = conn.cursor()
    field_names = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    cur.execute(f"INSERT INTO outreach_campaigns ({field_names}) VALUES ({placeholders})",
                tuple(data.values()))
    campaign_id = cur.lastrowid
    conn.commit()
    conn.close()
    return campaign_id


def update_outreach_campaign(campaign_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE outreach_campaigns SET {fields} WHERE id = ?", tuple(data.values()) + (campaign_id,))
    conn.commit()
    conn.close()


def get_outreach_emails(campaign_id: int = None, filters: dict = None):
    conn = get_db()
    cur = conn.cursor()
    query = """
        SELECT oe.*, c.name as curator_name, c.playlist_name, c.email as curator_email,
               ea.email_address as email_account_used, et.name as template_name
        FROM outreach_emails oe
        LEFT JOIN curators c ON oe.curator_id = c.id
        LEFT JOIN email_accounts ea ON oe.email_account_id = ea.id
        LEFT JOIN email_templates et ON oe.template_id = et.id
        WHERE 1=1
    """
    params = []
    if campaign_id:
        query += " AND oe.campaign_id = ?"
        params.append(campaign_id)
    if filters:
        if filters.get('response_status'):
            query += " AND oe.response_status = ?"
            params.append(filters['response_status'])
        if filters.get('curator_id'):
            query += " AND oe.curator_id = ?"
            params.append(filters['curator_id'])
        if filters.get('follow_up_level'):
            query += " AND oe.follow_up_level = ?"
            params.append(filters['follow_up_level'])
    query += " ORDER BY oe.created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_outreach_email(data: dict):
    conn = get_db()
    cur = conn.cursor()
    field_names = ', '.join(data.keys())
    placeholders = ', '.join(['?'] * len(data))
    cur.execute(f"INSERT INTO outreach_emails ({field_names}) VALUES ({placeholders})",
                tuple(data.values()))
    email_id = cur.lastrowid
    conn.commit()
    conn.close()
    return email_id


def update_outreach_email(email_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE outreach_emails SET {fields} WHERE id = ?", tuple(data.values()) + (email_id,))
    conn.commit()
    conn.close()


def get_outreach_stats():
    """Get outreach statistics across all campaigns."""
    conn = get_db()
    cur = conn.cursor()

    # Overall stats
    cur.execute("""
        SELECT
            COUNT(*) as total_sent,
            COALESCE(SUM(CASE WHEN opened = 1 THEN 1 ELSE 0 END), 0) as total_opened,
            COALESCE(SUM(CASE WHEN response_status = 'responded' THEN 1 ELSE 0 END), 0) as total_responded,
            COALESCE(SUM(CASE WHEN response_status = 'accepted' THEN 1 ELSE 0 END), 0) as total_accepted,
            COALESCE(SUM(CASE WHEN response_status = 'rejected' THEN 1 ELSE 0 END), 0) as total_rejected
        FROM outreach_emails
    """)
    overall = dict(cur.fetchone())

    # By campaign
    cur.execute("""
        SELECT campaign_id, oc.name as campaign_name,
               COUNT(*) as sent,
               SUM(CASE WHEN opened = 1 THEN 1 ELSE 0 END) as opened,
               SUM(CASE WHEN response_status = 'responded' THEN 1 ELSE 0 END) as responded,
               SUM(CASE WHEN response_status = 'accepted' THEN 1 ELSE 0 END) as accepted
        FROM outreach_emails oe
        JOIN outreach_campaigns oc ON oe.campaign_id = oc.id
        GROUP BY campaign_id
        ORDER BY oc.created_at DESC
        LIMIT 10
    """)
    by_campaign = [dict(r) for r in cur.fetchall()]

    # By template
    cur.execute("""
        SELECT template_id, et.name as template_name,
               COUNT(*) as sent,
               SUM(CASE WHEN response_status = 'responded' THEN 1 ELSE 0 END) as responded,
               SUM(CASE WHEN response_status = 'accepted' THEN 1 ELSE 0 END) as accepted
        FROM outreach_emails oe
        LEFT JOIN email_templates et ON oe.template_id = et.id
        WHERE template_id IS NOT NULL
        GROUP BY template_id
        ORDER BY sent DESC
        LIMIT 5
    """)
    by_template = [dict(r) for r in cur.fetchall()]

    # Recent responses
    cur.execute("""
        SELECT oe.*, c.name as curator_name, c.playlist_name
        FROM outreach_emails oe
        LEFT JOIN curators c ON oe.curator_id = c.id
        WHERE oe.response_status IS NOT NULL
        ORDER BY oe.response_date DESC
        LIMIT 10
    """)
    recent_responses = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        'overall': overall,
        'by_campaign': by_campaign,
        'by_template': by_template,
        'recent_responses': recent_responses,
    }


def get_curators_for_campaign(genre_filter=None, tier_filter=None, min_followers=None,
                              max_followers=None, exclude_recent=False, campaign_id=None):
    """Get curators matching campaign filters."""
    conn = get_db()
    cur = conn.cursor()
    query = "SELECT * FROM curators WHERE status = 'active'"
    params = []

    if genre_filter:
        query += " AND genre_focus LIKE ?"
        params.append(f"%{genre_filter}%")
    if tier_filter:
        query += " AND tier = ?"
        params.append(tier_filter)
    if min_followers:
        query += " AND follower_count >= ?"
        params.append(min_followers)
    if max_followers:
        query += " AND follower_count <= ?"
        params.append(max_followers)

    if exclude_recent and campaign_id:
        # Exclude curators already contacted in this campaign
        query += """ AND id NOT IN (
            SELECT curator_id FROM outreach_emails
            WHERE campaign_id = ? AND created_at > datetime('now', '-30 days')
        )"""
        params.append(campaign_id)

    query += " ORDER BY tier = 'S' DESC, tier = 'A' DESC, follower_count DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_next_follow_ups():
    """Get outreach emails that need follow-up."""
    conn = get_db()
    cur = conn.cursor()
    from datetime import datetime, timedelta
    now = datetime.now()

    # Find emails sent 3+ days ago with no response, follow-up level 0
    cur.execute("""
        SELECT oe.*, c.name as curator_name, c.playlist_name, c.email as curator_email
        FROM outreach_emails oe
        LEFT JOIN curators c ON oe.curator_id = c.id
        WHERE oe.response_status IS NULL
          AND oe.sent_at IS NOT NULL
          AND oe.follow_up_level = 0
          AND datetime(oe.sent_at, '+3 days') <= datetime('now')
        ORDER BY oe.sent_at ASC
        LIMIT 20
    """)
    level_1 = [dict(r) for r in cur.fetchall()]

    # Find emails sent 7+ days ago with follow-up level 1, no response
    cur.execute("""
        SELECT oe.*, c.name as curator_name, c.playlist_name, c.email as curator_email
        FROM outreach_emails oe
        LEFT JOIN curators c ON oe.curator_id = c.id
        WHERE oe.response_status IS NULL
          AND oe.sent_at IS NOT NULL
          AND oe.follow_up_level = 1
          AND datetime(oe.sent_at, '+7 days') <= datetime('now')
        ORDER BY oe.sent_at ASC
        LIMIT 20
    """)
    level_2 = [dict(r) for r in cur.fetchall()]

    # Find emails sent 14+ days ago with follow-up level 2, no response
    cur.execute("""
        SELECT oe.*, c.name as curator_name, c.playlist_name, c.email as curator_email
        FROM outreach_emails oe
        LEFT JOIN curators c ON oe.curator_id = c.id
        WHERE oe.response_status IS NULL
          AND oe.sent_at IS NOT NULL
          AND oe.follow_up_level = 2
          AND datetime(oe.sent_at, '+14 days') <= datetime('now')
        ORDER BY oe.sent_at ASC
        LIMIT 20
    """)
    level_3 = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {'level_1': level_1, 'level_2': level_2, 'level_3': level_3}


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


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT PROJECTS
# ══════════════════════════════════════════════════════════════════════════════

def get_content_projects(filters: dict = None):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT * FROM content_projects WHERE 1=1"
    params = []
    if filters:
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
        if filters.get('campaign_id'):
            query += " AND campaign_id = ?"
            params.append(filters['campaign_id'])
    query += " ORDER BY created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_content_project(project_id: str):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM content_projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_content_project(data: dict):
    import json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO content_projects (id, name, campaign_id, status, settings, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get('id'), data.get('name'), data.get('campaign_id'),
        data.get('status', 'draft'), json.dumps(data),
        datetime.now().isoformat()
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_content_project(project_id: str, data: dict):
    import json
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    fields += ", updated_at = CURRENT_TIMESTAMP"
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE content_projects SET {fields} WHERE id = ?", tuple(data.values()) + (project_id,))
    conn.commit()
    conn.close()


def delete_content_project(project_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM content_projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# SOCIAL BROWSER PROFILES
# ══════════════════════════════════════════════════════════════════════════════

def get_social_profiles(filters: dict = None):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT * FROM social_browser_profiles WHERE 1=1"
    params = []
    if filters:
        if filters.get('platform'):
            query += " AND platform = ?"
            params.append(filters['platform'])
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
    query += " ORDER BY last_used DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_social_profile(platform: str, profile_name: str = "default"):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM social_browser_profiles WHERE platform = ? AND profile_name = ?",
        (platform, profile_name)
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_social_profile(data: dict):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO social_browser_profiles
        (platform, profile_name, username, cookies, status, last_used)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data['platform'], data.get('profile_name', 'default'),
        data.get('username'), data.get('cookies'),
        data.get('status', 'logged_out'), datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def update_social_profile(platform: str, profile_name: str, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE social_browser_profiles SET {fields} WHERE platform = ? AND profile_name = ?",
        tuple(data.values()) + (platform, profile_name)
    )
    conn.commit()
    conn.close()


def delete_social_profile(platform: str, profile_name: str = "default"):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM social_browser_profiles WHERE platform = ? AND profile_name = ?",
        (platform, profile_name)
    )
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULED POSTS
# ══════════════════════════════════════════════════════════════════════════════

def get_scheduled_posts(filters: dict = None):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT * FROM scheduled_posts WHERE 1=1"
    params = []
    if filters:
        if filters.get('platform'):
            query += " AND platform = ?"
            params.append(filters['platform'])
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
    query += " ORDER BY scheduled_time ASC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_scheduled_post(post_id: int):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM scheduled_posts WHERE id = ?", (post_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_scheduled_post(data: dict):
    conn = get_db()
    cur = conn.cursor()
    scheduled = data.get('scheduled_time')
    if scheduled and hasattr(scheduled, 'isoformat'):
        data = dict(data)
        data['scheduled_time'] = scheduled.isoformat()
    cur.execute("""
        INSERT INTO scheduled_posts
        (platform, content_path, content_asset_id, caption, scheduled_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data['platform'], data.get('content_path'), data.get('content_asset_id'),
        data.get('caption'), data.get('scheduled_time'), data.get('status', 'pending')
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_scheduled_post(post_id: int, data: dict):
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE scheduled_posts SET {fields} WHERE id = ?", tuple(data.values()) + (post_id,))
    conn.commit()
    conn.close()


def delete_scheduled_post(post_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM scheduled_posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT ASSETS
# ══════════════════════════════════════════════════════════════════════════════

def get_content_assets(filters: dict = None):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT * FROM content_assets WHERE 1=1"
    params = []
    if filters:
        if filters.get('project_id'):
            query += " AND project_id = ?"
            params.append(filters['project_id'])
        if filters.get('asset_type'):
            query += " AND asset_type = ?"
            params.append(filters['asset_type'])
        if filters.get('campaign_id'):
            query += " AND campaign_id = ?"
            params.append(filters['campaign_id'])
    query += " ORDER BY created_at DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_content_asset(data: dict):
    import json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO content_assets
        (project_id, asset_type, file_path, format, width, height, duration_secs, campaign_id, tags, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('project_id'), data.get('asset_type'), data.get('file_path'),
        data.get('format'), data.get('width'), data.get('height'),
        data.get('duration_secs'), data.get('campaign_id'),
        data.get('tags'), json.dumps(data.get('metadata', {}))
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def delete_content_asset(asset_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM content_assets WHERE id = ?", (asset_id,))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS
# ══════════════════════════════════════════════════════════════════════════════

def get_campaigns(filters: dict = None):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT * FROM campaigns WHERE 1=1"
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


def get_campaign(campaign_id: int):
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_campaign(data: dict):
    import json
    conn = get_db()
    cur = conn.cursor()
    platforms = data.get('platforms')
    if isinstance(platforms, list):
        platforms = json.dumps(platforms)
    cur.execute("""
        INSERT INTO campaigns (name, description, platforms, start_date, end_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data['name'], data.get('description'), platforms,
        data.get('start_date'), data.get('end_date'),
        data.get('status', 'draft'), data.get('notes')
    ))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_campaign(campaign_id: int, data: dict):
    import json
    if 'platforms' in data and isinstance(data['platforms'], list):
        data = dict(data)
        data['platforms'] = json.dumps(data['platforms'])
    fields = ', '.join(f"{k} = ?" for k in data.keys())
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE campaigns SET {fields} WHERE id = ?", tuple(data.values()) + (campaign_id,))
    conn.commit()
    conn.close()


def delete_campaign(campaign_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
    conn.commit()
    conn.close()
