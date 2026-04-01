#!/usr/bin/env python3
"""
Marketing Manager - AIOStream Clone v2.0
Mystik Singh's All-in-One Music Promotion & Streaming Automation Platform
"""
import os, json, sqlite3, csv, random, time, hashlib, uuid
from datetime import datetime, timedelta
from io import StringIO, BytesIO
from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, session, flash, send_file, Response)
import threading

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'mystik-marketing-manager-2024')

# Increase buffer/content limits to prevent truncation issues
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
app.config['JSON_SORT_KEYS'] = False
# Allow larger session cookies (default is 4KB which is tiny)
from werkzeug.serving import run_simple
try:
    from werkzeug.wsgi import LimitedStream
    app.config['SESSION_COOKIE_SIZE'] = 16 * 1024  # 16KB session cookie
except Exception:
    pass

# Import models
sys_path = os.path.dirname(__file__)
import sys
sys.path.insert(0, sys_path)
from models import (
    init_db, get_artist_profile, update_artist_profile,
    get_albums, get_album, add_album,
    get_tracks, get_track, add_track,
    get_curators, get_curator, add_curator, update_curator,
    get_submissions, add_submission, update_submission, delete_submission,
    get_email_templates, get_email_template, add_email_template, update_email_template,
    get_releases, add_release,
    get_dashboard_stats, export_all_data, import_data,
    get_email_accounts, get_email_account, add_email_account, update_email_account, delete_email_account,
    get_email_aliases, add_email_alias, delete_email_alias,
    get_proxies, get_proxy, add_proxy, update_proxy, delete_proxy, check_proxy_health,
    get_streaming_accounts, get_streaming_account, add_streaming_account, update_streaming_account, delete_streaming_account,
    get_anti_detect_profiles, get_anti_detect_profile, add_anti_detect_profile, update_anti_detect_profile, delete_anti_detect_profile,
    get_emulator_instances, get_emulator_instance, add_emulator_instance, update_emulator_instance,
    delete_emulator_instance, start_emulator, stop_emulator,
    get_scheduled_tasks, get_scheduled_task, add_scheduled_task, update_scheduled_task, delete_scheduled_task, run_scheduled_task,
    get_activity_logs, add_activity_log, get_streaming_stats_summary, get_growth_stats,
    get_tiktok_accounts, get_tiktok_account, add_tiktok_account, update_tiktok_account, delete_tiktok_account,
    get_tiktok_campaigns, add_tiktok_campaign, update_tiktok_campaign, delete_tiktok_campaign,
    get_ai_playlists, add_ai_playlist, delete_ai_playlist,
    get_content_projects, get_content_project, add_content_project, update_content_project, delete_content_project,
    get_social_profiles, get_social_profile, add_social_profile, update_social_profile, delete_social_profile,
    get_scheduled_posts, get_scheduled_post, add_scheduled_post, update_scheduled_post, delete_scheduled_post,
    get_content_assets, add_content_asset, delete_content_asset,
    get_campaigns, get_campaign, add_campaign, update_campaign, delete_campaign,
    # Outreach
    get_outreach_campaigns, get_outreach_campaign, create_outreach_campaign, update_outreach_campaign,
    get_outreach_emails, create_outreach_email, update_outreach_email, get_outreach_stats,
    get_curators_for_campaign, get_next_follow_ups,
    PLATFORMS, EMAIL_PROVIDERS, ANDROID_VERSIONS, DEVICE_PROFILES, TASK_TYPES,
)

init_db()

# ─── Global task runner ───────────────────────────────────────────────────────
_task_thread = None
_task_running = False

def run_task_background():
    """Background thread that processes scheduled tasks."""
    global _task_running
    while _task_running:
        tasks = get_scheduled_tasks({'status': 'pending'})
        now = datetime.now()
        for t in tasks:
            if t.get('next_run_at'):
                next_run = datetime.fromisoformat(t['next_run_at'])
                if next_run <= now:
                    success, msg = run_scheduled_task(t['id'])
                    task = get_scheduled_task(t['id'])
                    # Schedule next run if repeating
                    if task and task['schedule_type'] == 'interval' and task['interval_seconds']:
                        next_dt = now + timedelta(seconds=task['interval_seconds'])
                        update_scheduled_task(t['id'], {'next_run_at': next_dt.isoformat()})
                    elif task and task['max_repeats'] > 0 and task['run_count'] >= task['max_repeats']:
                        update_scheduled_task(t['id'], {'status': 'completed'})
        time.sleep(5)


# ══════════════════════════════════════════════════════════════════════════════
# EXISTING CORE ROUTES (enhanced)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    stats = get_dashboard_stats()
    # Add streaming stats
    try:
        stats['streaming_summary'] = get_streaming_stats_summary()
        stats['recent_activity'] = get_activity_logs(limit=20)
        stats['growth'] = get_growth_stats(30)
    except:
        stats['streaming_summary'] = []
        stats['recent_activity'] = []
        stats['growth'] = []
    return render_template('dashboard.html', stats=stats, page='dashboard')


@app.route('/dashboard/stats')
def dashboard_stats():
    try:
        stats = get_dashboard_stats()
        stats['streaming_summary'] = get_streaming_stats_summary()
        stats['recent_activity'] = get_activity_logs(limit=20)
        stats['growth'] = get_growth_stats(30)
    except:
        stats = get_dashboard_stats()
    return jsonify(stats)


# ─── Profile ────────────────────────────────────────────────────────────────
@app.route('/profile')
def profile():
    artist = get_artist_profile()
    return render_template('profile.html', artist=artist, page='profile')

@app.route('/profile', methods=['POST'])
def profile_update():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    update_artist_profile(data)
    flash('Profile updated!', 'success')
    return redirect(url_for('profile'))


# ─── Albums ────────────────────────────────────────────────────────────────
@app.route('/albums')
def albums():
    return render_template('albums.html', albums=get_albums(), page='albums')

@app.route('/albums/<int:album_id>')
def album_detail(album_id):
    album = get_album(album_id)
    tracks = get_tracks(album_id)
    return render_template('album_detail.html', album=album, tracks=tracks, page='albums')

@app.route('/albums/add', methods=['POST'])
def album_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    add_album(data)
    flash('Album added!', 'success')
    return redirect(url_for('albums'))


# ─── Tracks ────────────────────────────────────────────────────────────────
@app.route('/tracks')
def tracks():
    all_tracks = get_tracks()
    album_list = get_albums()
    return render_template('tracks.html', tracks=all_tracks, albums=album_list, page='tracks')

@app.route('/tracks/add', methods=['POST'])
def track_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['track_number', 'duration_secs', 'bpm', 'album_id']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    add_track(data)
    flash('Track added!', 'success')
    return redirect(url_for('tracks'))


# ─── Curators ─────────────────────────────────────────────────────────────
@app.route('/curators')
def curators():
    filters = {}
    if request.args.get('genre'): filters['genre_focus'] = request.args.get('genre')
    if request.args.get('platform'): filters['platform'] = request.args.get('platform')
    if request.args.get('status'): filters['status'] = request.args.get('status')
    return render_template('curators.html', curators=get_curators(filters if filters else None),
                           filters=filters, page='curators')

@app.route('/curators/<int:curator_id>')
def curator_detail(curator_id):
    curator = get_curator(curator_id)
    submissions = get_submissions({'curator_id': curator_id})
    return render_template('curator_detail.html', curator=curator, submissions=submissions, page='curators')

@app.route('/curators/add', methods=['POST'])
def curator_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['follower_count', 'rating']:
        if field in data and data[field]:
            try: data[field] = float(data[field]) if field == 'rating' else int(data[field])
            except: data[field] = None
    add_curator(data)
    flash('Curator added!', 'success')
    return redirect(url_for('curators'))

@app.route('/curators/<int:curator_id>/edit', methods=['POST'])
def curator_edit(curator_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['follower_count', 'rating', 'response_rate']:
        if field in data and data[field]:
            try: data[field] = float(data[field])
            except: data[field] = None
    update_curator(curator_id, data)
    flash('Curator updated!', 'success')
    return redirect(url_for('curator_detail', curator_id=curator_id))


# ─── Submissions ───────────────────────────────────────────────────────────
@app.route('/submissions')
def submissions():
    filters = {}
    if request.args.get('status'): filters['status'] = request.args.get('status')
    if request.args.get('album_id'): filters['album_id'] = int(request.args.get('album_id'))
    sub_list = get_submissions(filters if filters else None)
    return render_template('submissions.html', submissions=sub_list, albums=get_albums(),
                           curators=get_curators({'status': 'active'}), filters=filters, page='submissions')

@app.route('/submissions/add', methods=['POST'])
def submission_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['track_id', 'album_id', 'curator_id']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    add_submission(data)
    flash('Submission logged!', 'success')
    return redirect(url_for('submissions'))

@app.route('/submissions/<int:sub_id>/update', methods=['POST'])
def submission_update(sub_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    update_submission(sub_id, data)
    flash('Submission updated!', 'success')
    return redirect(url_for('submissions'))

@app.route('/submissions/<int:sub_id>/delete', methods=['POST'])
def submission_delete(sub_id):
    delete_submission(sub_id)
    flash('Submission deleted.', 'info')
    return redirect(url_for('submissions'))


# ─── Email Templates ──────────────────────────────────────────────────────
@app.route('/templates')
def templates():
    return render_template('templates.html', templates=get_email_templates(), page='templates')

@app.route('/templates/add', methods=['POST'])
def template_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    add_email_template(data)
    flash('Template added!', 'success')
    return redirect(url_for('templates'))

@app.route('/templates/<int:template_id>/edit', methods=['POST'])
def template_edit(template_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    update_email_template(template_id, data)
    flash('Template updated!', 'success')
    return redirect(url_for('templates'))


# ─── Pitch Composer ────────────────────────────────────────────────────────
@app.route('/compose')
def compose():
    artist = get_artist_profile()
    return render_template('compose.html', artist=artist, albums=get_albums(),
                           curators=get_curators({'status': 'active'}),
                           tracks=get_tracks(), page='compose',
                           template_names={t['name']: t['id'] for t in get_email_templates()})


# ─── Releases ──────────────────────────────────────────────────────────────
@app.route('/releases')
def releases():
    return render_template('releases.html', releases=get_releases(), albums=get_albums(), page='releases')

@app.route('/releases/add', methods=['POST'])
def release_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    if 'album_id' in data and data['album_id']:
        try: data['album_id'] = int(data['album_id'])
        except: data['album_id'] = None
    add_release(data)
    flash('Release scheduled!', 'success')
    return redirect(url_for('releases'))


# ─── Export / Import ───────────────────────────────────────────────────────
@app.route('/export')
def export():
    data = export_all_data()
    output = BytesIO()
    output.write(json.dumps(data, indent=2, default=str).encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='application/json',
                     as_attachment=True,
                     download_name=f'marketing_manager_backup_{datetime.now().strftime("%Y%m%d")}.json')

@app.route('/import', methods=['GET', 'POST'])
def import_page():
    if request.method == 'GET':
        return render_template('import.html', page='import')
    if 'file' not in request.files:
        flash('No file uploaded.', 'error')
        return redirect(url_for('import_page'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('import_page'))
    try:
        data = json.load(file)
        import_data(data)
        flash('Data imported successfully!', 'success')
    except Exception as e:
        flash(f'Import failed: {str(e)}', 'error')
    return redirect(url_for('index'))


# ─── Email Accounts ───────────────────────────────────────────────────────
@app.route('/email-accounts')
def email_accounts():
    return render_template('email_accounts.html', accounts=get_email_accounts(), page='email_accounts')

@app.route('/email-accounts/add', methods=['POST'])
def email_account_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['smtp_port', 'daily_limit']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    add_email_account(data)
    flash('Email account added!', 'success')
    return redirect(url_for('email_accounts'))

@app.route('/email-accounts/<int:account_id>/edit', methods=['POST'])
def email_account_edit(account_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    update_email_account(account_id, data)
    flash('Account updated!', 'success')
    return redirect(url_for('email_accounts'))

@app.route('/email-accounts/<int:account_id>/delete', methods=['POST'])
def email_account_delete(account_id):
    delete_email_account(account_id)
    flash('Account deleted.', 'info')
    return redirect(url_for('email_accounts'))

@app.route('/email-accounts/<int:account_id>/aliases')
def email_aliases(account_id):
    account = get_email_account(account_id)
    aliases = get_email_aliases(account_id)
    return render_template('email_aliases.html', account=account, aliases=aliases, page='email_accounts')

@app.route('/email-accounts/<int:account_id>/aliases/add', methods=['POST'])
def alias_add(account_id):
    add_email_alias(account_id, request.form.get('alias_address'),
                    request.form.get('display_name'),
                    1 if request.form.get('is_default') else 0)
    flash('Alias added!', 'success')
    return redirect(url_for('email_aliases', account_id=account_id))

@app.route('/email-accounts/aliases/<int:alias_id>/delete', methods=['POST'])
def alias_delete(alias_id):
    conn = sqlite3.connect(os.path.join(sys_path, 'mystik_promotion.db'))
    cur = conn.cursor()
    cur.execute("SELECT account_id FROM email_aliases WHERE id = ?", (alias_id,))
    row = cur.fetchone()
    account_id = row[0] if row else None
    conn.close()
    delete_email_alias(alias_id)
    if account_id:
        return redirect(url_for('email_aliases', account_id=account_id))
    return redirect(url_for('email_accounts'))


# ══════════════════════════════════════════════════════════════════════════════
# PROXY MANAGER MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/proxies')
def proxies():
    filters = {}
    if request.args.get('status'): filters['is_active'] = 1 if request.args.get('status') == 'active' else 0
    if request.args.get('health'): filters['health_status'] = request.args.get('health')
    proxy_list = get_proxies(filters if filters else None)
    return render_template('proxies.html', proxies=proxy_list, filters=filters, page='proxies')

@app.route('/proxies/add', methods=['POST'])
def proxy_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['port', 'geo_lat', 'geo_lon']:
        if field in data and data[field]:
            try: data[field] = float(data[field]) if field != 'port' else int(data[field])
            except: data[field] = None
    add_proxy(data)
    flash('Proxy added!', 'success')
    return redirect(url_for('proxies'))

@app.route('/proxies/<int:proxy_id>/edit', methods=['POST'])
def proxy_edit(proxy_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    update_proxy(proxy_id, data)
    flash('Proxy updated!', 'success')
    return redirect(url_for('proxies'))

@app.route('/proxies/<int:proxy_id>/delete', methods=['POST'])
def proxy_delete(proxy_id):
    delete_proxy(proxy_id)
    flash('Proxy deleted.', 'info')
    return redirect(url_for('proxies'))

@app.route('/proxies/<int:proxy_id>/check', methods=['POST'])
def proxy_check(proxy_id):
    result = check_proxy_health(proxy_id)
    return jsonify({'proxy_id': proxy_id, 'status': result})

@app.route('/proxies/check-all', methods=['POST'])
def proxy_check_all():
    all_proxies = get_proxies()
    results = []
    for p in all_proxies:
        result = check_proxy_health(p['id'])
        results.append({'proxy_id': p['id'], 'status': result})
    flash(f'Health check complete for {len(results)} proxies.', 'info')
    return redirect(url_for('proxies'))


# ══════════════════════════════════════════════════════════════════════════════
# STREAMING ACCOUNTS MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/streaming-accounts')
def streaming_accounts():
    filters = {}
    if request.args.get('platform'): filters['platform'] = request.args.get('platform')
    if request.args.get('status'): filters['status'] = request.args.get('status')
    accounts = get_streaming_accounts(filters if filters else None)
    proxy_list = get_proxies({'is_active': 1})
    emulators = get_emulator_instances({'status': 'running'})
    profiles = get_anti_detect_profiles()
    return render_template('streaming_accounts.html', accounts=accounts,
                           proxies=proxy_list, emulators=emulators, profiles=profiles,
                           platforms=PLATFORMS, filters=filters, page='streaming_accounts')

@app.route('/streaming-accounts/add', methods=['POST'])
def streaming_account_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['proxy_id', 'emulator_id', 'profile_id']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    add_streaming_account(data)
    flash('Streaming account added!', 'success')
    return redirect(url_for('streaming_accounts'))

@app.route('/streaming-accounts/<int:account_id>/edit', methods=['POST'])
def streaming_account_edit(account_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    update_streaming_account(account_id, data)
    flash('Account updated!', 'success')
    return redirect(url_for('streaming_accounts'))

@app.route('/streaming-accounts/<int:account_id>/delete', methods=['POST'])
def streaming_account_delete(account_id):
    delete_streaming_account(account_id)
    flash('Account deleted.', 'info')
    return redirect(url_for('streaming_accounts'))


# ══════════════════════════════════════════════════════════════════════════════
# ACCOUNT CREATOR MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/account-creator')
def account_creator():
    """Bulk account creation interface."""
    proxy_list = get_proxies({'is_active': 1})
    profiles = get_anti_detect_profiles()
    emulators = get_emulator_instances()
    return render_template('account_creator.html', proxies=proxy_list, profiles=profiles,
                           emulators=emulators, platforms=PLATFORMS,
                           email_providers=EMAIL_PROVIDERS, page='account_creator')

@app.route('/account-creator/bulk', methods=['POST'])
def account_creator_bulk():
    """Bulk create streaming accounts."""
    data = request.get_json()
    platform = data.get('platform')
    email_provider = data.get('email_provider', 'gmail')
    quantity = min(int(data.get('quantity', 1)), 50)
    base_username = data.get('base_username', 'musiclover')
    base_email = data.get('base_email', 'user')
    domain = data.get('domain', 'gmail.com')
    password = data.get('password', 'TempPass123!')
    proxy_id = data.get('proxy_id')
    emulator_id = data.get('emulator_id')
    profile_id = data.get('profile_id')
    results = []
    for i in range(quantity):
        unique_id = uuid.uuid4().hex[:8]
        username = f"{base_username}{unique_id}"
        if email_provider == 'custom':
            email = f"{base_email}{unique_id}@{domain}"
        else:
            email = f"{base_username}{unique_id}@{domain}"
        try:
            account_id = add_streaming_account({
                'platform': platform,
                'email': email,
                'username': username,
                'password': password,
                'display_name': username,
                'proxy_id': proxy_id,
                'emulator_id': emulator_id,
                'profile_id': profile_id,
                'status': 'active'
            })
            results.append({'success': True, 'username': username, 'email': email, 'id': account_id})
        except Exception as e:
            results.append({'success': False, 'username': username, 'email': email, 'error': str(e)})
    return jsonify({'results': results, 'total': quantity, 'successful': sum(1 for r in results if r['success'])})

@app.route('/account-creator/reset-passwords', methods=['POST'])
def account_creator_reset():
    """Bulk reset passwords."""
    data = request.get_json()
    account_ids = data.get('account_ids', [])
    new_password = data.get('new_password', 'NewPass123!')
    results = []
    for aid in account_ids:
        try:
            update_streaming_account(aid, {'password': new_password})
            results.append({'success': True, 'account_id': aid})
        except Exception as e:
            results.append({'success': False, 'account_id': aid, 'error': str(e)})
    return jsonify({'results': results})


# ══════════════════════════════════════════════════════════════════════════════
# STREAMING AUTOMATION MODULE (REAL - uses Playwright + real Spotify accounts)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/streaming-automation')
def streaming_automation():
    """Main streaming automation dashboard."""
    try:
        from spotify_streaming_manager import get_streaming_manager, PLAYWRIGHT_AVAILABLE, ALBUMS
        manager = get_streaming_manager()
        status = manager.get_status()
    except Exception as e:
        status = {'running': False, 'error': str(e)}

    try:
        from spotify_streaming_manager import PLAYWRIGHT_AVAILABLE as PW
        playwright_ok = PW
    except Exception:
        playwright_ok = False

    accounts = get_streaming_accounts({'status': 'active'})
    stats_summary = get_streaming_stats_summary()
    recent = get_activity_logs({'event_type': 'play:spotify'}, 100)
    albums = [
        {'name': 'Memento Mori Vol. 1', 'url': 'https://open.spotify.com/album/1m9ciXW7myuZbo6CrrnuUr'},
        {'name': 'Memento Mori Vol. 2', 'url': 'https://open.spotify.com/album/0Pe4dekB0JHj1WctvSMLo1'},
        {'name': 'Memento Mori Vol. 3', 'url': 'https://open.spotify.com/album/0wb6BVYUNtFW0YST2IwgG5'},
    ]
    return render_template('streaming_automation.html',
                           accounts=accounts, stats=stats_summary,
                           recent=recent, albums=albums,
                           streaming_status=status,
                           playwright_ok=playwright_ok,
                           platforms=PLATFORMS, page='streaming_automation')


@app.route('/streaming-automation/start', methods=['POST'])
def streaming_start():
    """
    Start REAL Spotify streaming automation.
    Uses Playwright with real Chrome browsers and Spotify accounts.
    """
    try:
        from spotify_streaming_manager import get_streaming_manager
        manager = get_streaming_manager()
        if manager.running:
            return jsonify({'success': False, 'error': 'Already running'}), 400

        background = request.json.get('background', True) if request.is_json else True
        manager.start(background=background)

        return jsonify({
            'success': True,
            'message': 'Real Spotify streaming started',
            'status': manager.get_status()
        })
    except ImportError as e:
        return jsonify({'success': False, 'error': f'Module error: {e}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/streaming-automation/stop', methods=['POST'])
def streaming_stop():
    """Stop all real streaming."""
    try:
        from spotify_streaming_manager import get_streaming_manager
        manager = get_streaming_manager()
        manager.stop()
        return jsonify({'success': True, 'message': 'Streaming stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/streaming-automation/status', methods=['GET'])
def streaming_status():
    """Get current real streaming status."""
    try:
        from spotify_streaming_manager import get_streaming_manager
        manager = get_streaming_manager()
        return jsonify(manager.get_status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/streaming-automation/test-stream', methods=['POST'])
def streaming_test():
    """
    Test a single real stream on one account.
    Streams for a short duration (default 30s) to verify setup.
    """
    data = request.get_json() or {}
    account_id = data.get('account_id')
    album_url = data.get('album_url')
    duration = data.get('duration_secs', 30)

    if not account_id or not album_url:
        return jsonify({'success': False, 'error': 'account_id and album_url required'}), 400

    try:
        from spotify_streaming_manager import get_streaming_manager
        manager = get_streaming_manager()
        result = manager.test_single_stream(account_id, album_url, duration)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/streaming-automation/start-play', methods=['POST'])
def streaming_start_play():
    """
    Start real streaming on a specific account for a specific album.
    Uses Playwright with anti-detect fingerprints - REAL streams, real Spotify plays.
    """
    data = request.get_json()
    account_id = data.get('account_id')
    target_url = data.get('target_url')
    duration = data.get('duration_secs', 300)  # Default 5 min test
    loop = data.get('loop_count', 1)

    if not account_id or not target_url:
        return jsonify({'success': False, 'error': 'account_id and target_url required'}), 400

    # Find account
    account = get_streaming_account(account_id)
    if not account:
        return jsonify({'success': False, 'error': f'Account {account_id} not found'}), 404

    # Find album name from URL
    albums_map = {
        '1m9ciXW7myuZbo6CrrnuUr': 'Memento Mori Vol. 1',
        '0Pe4dekB0JHj1WctvSMLo1': 'Memento Mori Vol. 2',
        '0wb6BVYUNtFW0YST2IwgG5': 'Memento Mori Vol. 3',
    }
    import re
    album_id_match = re.search(r'/album/([a-zA-Z0-9]+)', target_url)
    album_id = album_id_match.group(1) if album_id_match else None
    album_name = albums_map.get(album_id, 'Unknown Album')

    try:
        from spotify_streaming_manager import SpotifyStreamer, get_streaming_manager
        import random

        profiles = get_anti_detect_profiles()
        proxies = get_proxies({'is_active': 1})
        profile = random.choice(profiles) if profiles else None
        proxy = random.choice(proxies) if proxies else None

        album = {'name': album_name, 'url': target_url}
        streamer = SpotifyStreamer(account=account, album=album,
                                   profile=profile, proxy=proxy,
                                   headless=True)

        total_streamed = 0
        for i in range(loop):
            result = streamer.stream(duration)
            if result['success']:
                total_streamed += 1

        return jsonify({
            'success': total_streamed > 0,
            'message': f'Real stream completed: {total_streamed}/{loop} successful',
            'streamed_secs': total_streamed * duration,
            'account': account.get('email'),
            'album': album_name,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/streaming-automation/get-stats', methods=['GET'])
def streaming_get_stats():
    """Get streaming stats from real activity logs."""
    summary = get_streaming_stats_summary()
    growth = get_growth_stats(30)
    recent = get_activity_logs({'event_type': 'play:spotify'}, 100)
    return jsonify({'summary': summary, 'growth': growth, 'recent': [dict(r) for r in recent]})


@app.route('/streaming-automation/log-boost', methods=['POST'])
def streaming_log_boost():
    """
    Log a manual boost of streams — ONLY logs to DB.
    NOTE: This does NOT create real streams. For real streams, use start-play.
    """
    data = request.get_json()
    account_id = data.get('account_id')
    boost_type = data.get('boost_type', 'streams')
    amount = data.get('amount', 0)
    account = get_streaming_account(account_id) if account_id else None

    add_activity_log({
        'event_type': f'boost:{boost_type}',
        'platform': account['platform'] if account else data.get('platform', 'Spotify'),
        'account_id': account_id,
        'description': f'Manual boost: {amount} {boost_type}',
        'streams_delta': amount if boost_type == 'streams' else 0,
        'success': 1,
        'timestamp': datetime.now().isoformat()
    })

    if account and account_id:
        current_plays = account.get('total_plays', 0)
        update_streaming_account(account_id, {'total_plays': current_plays + amount})

    return jsonify({
        'success': True,
        'boost_type': boost_type,
        'amount': amount,
        'note': 'This logs to DB only. Use /streaming-automation/start-play for real streams.'
    })


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-DETECT PROFILES MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/anti-detect')
def anti_detect():
    profiles = get_anti_detect_profiles()
    return render_template('anti_detect.html', profiles=profiles, page='anti_detect')

@app.route('/anti-detect/add', methods=['POST'])
def anti_detect_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['hardware_concurrency', 'device_memory', 'play_length_secs', 'scroll_interval_secs',
                  'click_interval_secs', 'mouse_move_duration_secs']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    if 'cookie_enabled' not in data: data['cookie_enabled'] = 0
    if 'java_enabled' not in data: data['java_enabled'] = 0
    if 'touch_support' not in data: data['touch_support'] = 0
    if 'is_default' in data: data['is_default'] = 1
    add_anti_detect_profile(data)
    flash('Anti-detect profile added!', 'success')
    return redirect(url_for('anti_detect'))

@app.route('/anti-detect/<int:profile_id>/edit', methods=['POST'])
def anti_detect_edit(profile_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['hardware_concurrency', 'device_memory', 'play_length_secs', 'scroll_interval_secs',
                  'click_interval_secs', 'mouse_move_duration_secs']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    if 'is_default' in data: data['is_default'] = 1
    update_anti_detect_profile(profile_id, data)
    flash('Profile updated!', 'success')
    return redirect(url_for('anti_detect'))

@app.route('/anti-detect/<int:profile_id>/delete', methods=['POST'])
def anti_detect_delete(profile_id):
    delete_anti_detect_profile(profile_id)
    flash('Profile deleted.', 'info')
    return redirect(url_for('anti_detect'))


# ══════════════════════════════════════════════════════════════════════════════
# EMULATOR CONTROLLER MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/emulators')
def emulators():
    instances = get_emulator_instances()
    proxies = get_proxies({'is_active': 1})
    accounts = get_streaming_accounts()
    profiles = get_anti_detect_profiles()
    return render_template('emulators.html', instances=instances, proxies=proxies,
                           accounts=accounts, profiles=profiles,
                           android_versions=ANDROID_VERSIONS,
                           device_profiles=DEVICE_PROFILES, page='emulators')

@app.route('/emulators/add', methods=['POST'])
def emulator_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['proxy_id', 'account_id', 'profile_id', 'screen_width', 'screen_height',
                  'dpi', 'cpu_cores', 'ram_mb']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    add_emulator_instance(data)
    flash('Emulator instance created!', 'success')
    return redirect(url_for('emulators'))

@app.route('/emulators/<int:instance_id>/edit', methods=['POST'])
def emulator_edit(instance_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['proxy_id', 'account_id', 'profile_id', 'screen_width', 'screen_height',
                  'dpi', 'cpu_cores', 'ram_mb']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    update_emulator_instance(instance_id, data)
    flash('Instance updated!', 'success')
    return redirect(url_for('emulators'))

@app.route('/emulators/<int:instance_id>/delete', methods=['POST'])
def emulator_delete(instance_id):
    delete_emulator_instance(instance_id)
    flash('Instance deleted.', 'info')
    return redirect(url_for('emulators'))

@app.route('/emulators/<int:instance_id>/start', methods=['POST'])
def emulator_start(instance_id):
    success, msg = start_emulator(instance_id)
    if success:
        flash(f'Emulator started: {msg}', 'success')
    else:
        flash(f'Failed to start emulator: {msg}', 'error')
    return redirect(url_for('emulators'))

@app.route('/emulators/<int:instance_id>/stop', methods=['POST'])
def emulator_stop(instance_id):
    success, msg = stop_emulator(instance_id)
    if success:
        flash(f'Emulator stopped: {msg}', 'info')
    else:
        flash(f'Failed to stop: {msg}', 'error')
    return redirect(url_for('emulators'))


# ══════════════════════════════════════════════════════════════════════════════
# TASK SCHEDULER MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/scheduler')
def scheduler():
    tasks = get_scheduled_tasks()
    accounts = get_streaming_accounts()
    proxies = get_proxies({'is_active': 1})
    emulators = get_emulator_instances()
    profiles = get_anti_detect_profiles()
    return render_template('scheduler.html', tasks=tasks, accounts=accounts,
                           proxies=proxies, emulators=emulators, profiles=profiles,
                           task_types=TASK_TYPES, platforms=PLATFORMS, page='scheduler')

@app.route('/scheduler/add', methods=['POST'])
def scheduler_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['account_id', 'proxy_id', 'emulator_id', 'profile_id', 'interval_seconds',
                  'repeat_count', 'max_repeats', 'play_duration_secs', 'loop_count',
                  'interval_between_plays_secs', 'priority']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    add_scheduled_task(data)
    flash('Task scheduled!', 'success')
    return redirect(url_for('scheduler'))

@app.route('/scheduler/<int:task_id>/edit', methods=['POST'])
def scheduler_edit(task_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['account_id', 'proxy_id', 'emulator_id', 'profile_id', 'interval_seconds',
                  'repeat_count', 'max_repeats', 'play_duration_secs', 'loop_count',
                  'interval_between_plays_secs', 'priority']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    update_scheduled_task(task_id, data)
    flash('Task updated!', 'success')
    return redirect(url_for('scheduler'))

@app.route('/scheduler/<int:task_id>/delete', methods=['POST'])
def scheduler_delete(task_id):
    delete_scheduled_task(task_id)
    flash('Task deleted.', 'info')
    return redirect(url_for('scheduler'))

@app.route('/scheduler/<int:task_id>/run', methods=['POST'])
def scheduler_run(task_id):
    success, msg = run_scheduled_task(task_id)
    if success:
        flash(f'Task executed: {msg}', 'success')
    else:
        flash(f'Task failed: {msg}', 'error')
    return redirect(url_for('scheduler'))

@app.route('/scheduler/<int:task_id>/toggle', methods=['POST'])
def scheduler_toggle(task_id):
    task = get_scheduled_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    new_status = 'paused' if task['status'] == 'active' else 'active'
    update_scheduled_task(task_id, {'status': new_status})
    return jsonify({'task_id': task_id, 'status': new_status})


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVITY LOGS & STATISTICS MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/statistics')
def statistics():
    summary = get_streaming_stats_summary()
    growth = get_growth_stats(30)
    logs = get_activity_logs(limit=200)
    return render_template('statistics.html', summary=summary, growth=growth,
                           logs=logs, platforms=PLATFORMS, page='statistics')

@app.route('/statistics/export', methods=['GET'])
def statistics_export():
    growth = get_growth_stats(365)
    logs = get_activity_logs(limit=10000)
    output = BytesIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Event Type', 'Platform', 'Account', 'Description',
                     'Streams', 'Listeners', 'Followers', 'Likes', 'Success', 'Duration (ms)'])
    for log in logs:
        writer.writerow([
            log.get('timestamp', ''), log.get('event_type', ''), log.get('platform', ''),
            log.get('account_id', ''), log.get('description', ''),
            log.get('streams_delta', 0), log.get('listeners_delta', 0),
            log.get('followers_delta', 0), log.get('likes_delta', 0),
            'Yes' if log.get('success') else 'No', log.get('duration_ms', '')
        ])
    output.seek(0)
    return send_file(output, mimetype='text/csv',
                     as_attachment=True,
                     download_name=f'activity_log_{datetime.now().strftime("%Y%m%d")}.csv')


# ══════════════════════════════════════════════════════════════════════════════
# TIKTOK BOT MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/tiktok')
def tiktok():
    accounts = get_tiktok_accounts()
    campaigns = get_tiktok_campaigns()
    proxies = get_proxies({'is_active': 1})
    profiles = get_anti_detect_profiles()
    emulators = get_emulator_instances()
    return render_template('tiktok.html', accounts=accounts, campaigns=campaigns,
                           proxies=proxies, profiles=profiles, emulators=emulators,
                           page='tiktok')

@app.route('/tiktok/accounts/add', methods=['POST'])
def tiktok_account_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['proxy_id', 'emulator_id', 'profile_id']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    add_tiktok_account(data)
    flash('TikTok account added!', 'success')
    return redirect(url_for('tiktok'))

@app.route('/tiktok/accounts/<int:account_id>/edit', methods=['POST'])
def tiktok_account_edit(account_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    update_tiktok_account(account_id, data)
    flash('Account updated!', 'success')
    return redirect(url_for('tiktok'))

@app.route('/tiktok/accounts/<int:account_id>/delete', methods=['POST'])
def tiktok_account_delete(account_id):
    delete_tiktok_account(account_id)
    flash('Account deleted.', 'info')
    return redirect(url_for('tiktok'))

@app.route('/tiktok/campaigns/add', methods=['POST'])
def tiktok_campaign_add():
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    for field in ['track_id', 'album_id']:
        if field in data and data[field]:
            try: data[field] = int(data[field])
            except: data[field] = None
    add_tiktok_campaign(data)
    flash('Campaign created!', 'success')
    return redirect(url_for('tiktok'))

@app.route('/tiktok/campaigns/<int:campaign_id>/edit', methods=['POST'])
def tiktok_campaign_edit(campaign_id):
    data = {k: (v if v != '' else None) for k, v in request.form.to_dict().items()}
    update_tiktok_campaign(campaign_id, data)
    flash('Campaign updated!', 'success')
    return redirect(url_for('tiktok'))

@app.route('/tiktok/campaigns/<int:campaign_id>/delete', methods=['POST'])
def tiktok_campaign_delete(campaign_id):
    delete_tiktok_campaign(campaign_id)
    flash('Campaign deleted.', 'info')
    return redirect(url_for('tiktok'))

@app.route('/tiktok/campaigns/<int:campaign_id>/execute', methods=['POST'])
def tiktok_campaign_execute(campaign_id):
    """Simulate executing a TikTok campaign."""
    campaign = get_tiktok_campaigns({'status': 'draft'})  # just demo
    add_activity_log({
        'event_type': 'tiktok:campaign_execute',
        'description': f'TikTok campaign executed: ID {campaign_id}',
        'success': 1,
        'timestamp': datetime.now().isoformat()
    })
    update_tiktok_campaign(campaign_id, {'status': 'running', 'posted_at': datetime.now().isoformat()})
    flash('Campaign execution started (simulated).', 'success')
    return redirect(url_for('tiktok'))


# ══════════════════════════════════════════════════════════════════════════════
# AI PLAYLIST CREATOR MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/ai-playlists')
def ai_playlists():
    playlists = get_ai_playlists()
    tracks = get_tracks()
    return render_template('ai_playlists.html', playlists=playlists, tracks=tracks, page='ai_playlists')

@app.route('/ai-playlists/generate', methods=['POST'])
def ai_playlist_generate():
    """Generate an AI playlist using OpenAI."""
    data = request.get_json()
    genre = data.get('genre', 'Hip Hop')
    mood = data.get('mood', 'Chill')
    platform = data.get('platform', 'Spotify')
    name = data.get('name', f'{genre} {mood} Mix')
    # In production, this would call OpenAI API
    # For now, create a placeholder playlist
    playlist_id = add_ai_playlist({
        'playlist_name': name,
        'description': f'AI-generated {genre} {mood} playlist for Mystik Singh promotion.',
        'genre': genre,
        'mood': mood,
        'platform': platform,
        'notes': 'Generated by Marketing Manager AI'
    })
    return jsonify({
        'success': True,
        'playlist_id': playlist_id,
        'message': f'Playlist "{name}" generated! In production, this would query OpenAI for track recommendations.'
    })

@app.route('/ai-playlists/<int:playlist_id>/delete', methods=['POST'])
def ai_playlist_delete(playlist_id):
    delete_ai_playlist(playlist_id)
    flash('Playlist deleted.', 'info')
    return redirect(url_for('ai_playlists'))


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT CREATOR MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/content-creator')
def content_creator():
    projects = get_content_projects()
    campaigns = get_campaigns()
    stats = {
        'projects': len([p for p in projects if p.get('status') == 'draft']),
        'queued': len([p for p in projects if p.get('status') == 'processing']),
        'exported': len([p for p in projects if p.get('status') == 'completed']),
        'errors': len([p for p in projects if p.get('status') == 'error']),
    }
    hf_api_key = os.environ.get('HIGGSFIELD_API_KEY', '')
    return render_template('content_creator.html', projects=projects, campaigns=campaigns,
                           stats=stats, hf_api_key=hf_api_key, page='content_creator')


@app.route('/content-project/create', methods=['POST'])
def content_project_create():
    data = {k: (v[0] if isinstance(v, list) else v) for k, v in request.form.to_dict().items()}
    if 'platforms' in data:
        data['platforms'] = request.form.getlist('platforms')
    import uuid
    data['id'] = str(uuid.uuid4())[:12]
    data['status'] = 'draft'
    add_content_project(data)
    flash('Project created!', 'success')
    return redirect(url_for('content_creator'))


@app.route('/content-project/<project_id>/delete', methods=['POST'])
def content_project_delete(project_id):
    delete_content_project(project_id)
    flash('Project deleted.', 'info')
    return redirect(url_for('content_creator'))


@app.route('/api/content/generate', methods=['POST'])
def api_content_generate():
    """Generate AI video using Higgsfield browser automation, then format for platforms."""
    data = request.get_json()
    from content_creator import ContentCreator, ContentProject
    creator = ContentCreator()

    project = ContentProject(
        name=data.get('name', 'AI Generation ' + datetime.now().strftime('%H:%M')),
        quality=data.get('quality', 'standard'),
        platforms=data.get('platforms', ['tiktok']),
        color_grade=data.get('color_grade', 'cinematic'),
        add_captions=data.get('add_captions', True),
    )
    
    use_browser = data.get('use_browser', True)
    
    # Handle uploaded image if any
    result = creator.generate_ai_video(
        prompt=data.get('prompt', 'Cinematic music video'),
        image_path=data.get('image_path'),
        quality=data.get('quality', 'standard'),
        use_browser=use_browser,
    )
    if result.get('success'):
        flash('AI video generation complete! (check media library for output)', 'success')
        return jsonify({
            'success': True,
            'message': f'Video saved: {result.get("video_path", "N/A")}',
            'generation_id': result.get('generation_id'),
            'video_path': result.get('video_path'),
        })
    else:
        return jsonify({'success': False, 'error': result.get('error', 'Generation failed')})


@app.route('/api/content/generate/browser', methods=['POST'])
def api_content_generate_browser():
    """
    Dedicated endpoint for browser-based Higgsfield video generation.
    Returns streaming progress via SSE.
    """
    data = request.get_json()
    from content_creator import ContentCreator
    
    def generate():
        creator = ContentCreator()
        
        def log_progress(msg, status="info"):
            yield f"data: {json.dumps({'status': status, 'message': msg})}\n\n"
        
        try:
            yield from log_progress("Starting Higgsfield browser automation...", "info")
            
            # Use browser-based generation with progress tracking
            result = creator.generate_ai_video_browser(
                prompt=data.get('prompt', 'Cinematic music video'),
                image_path=data.get('image_path'),
                duration=data.get('duration', 5),
                quality=data.get('quality', 'standard'),
                headless=data.get('headless', False),
            )
            
            if result.get('success'):
                yield from log_progress(f"Video generated: {result.get('video_path')}", "success")
                yield f"data: {json.dumps({'status': 'complete', 'video_path': result.get('video_path'), 'success': True})}\n\n"
            else:
                yield from log_progress(f"Generation failed: {result.get('error')}", "error")
                yield f"data: {json.dumps({'status': 'error', 'error': result.get('error'), 'success': False})}\n\n"
                
        except Exception as e:
            yield from log_progress(f"Error: {str(e)}", "error")
            yield f"data: {json.dumps({'status': 'error', 'error': str(e), 'success': False})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/higgsfield/test-browser', methods=['GET'])
def higgsfield_test_browser():
    """Test Higgsfield browser connection."""
    from higgsfield_automation import HiggsfieldAutomation, test_connection, DEFAULT_OUTPUT_DIR
    
    try:
        # Quick connectivity test
        if not test_connection():
            return jsonify({'success': False, 'error': 'Cannot reach Higgsfield website'})
        
        return jsonify({
            'success': True,
            'message': 'Higgsfield is reachable',
            'output_dir': DEFAULT_OUTPUT_DIR
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ══════════════════════════════════════════════════════════════════════════════
# SOCIAL BROWSER MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/social-profiles')
def social_profiles():
    filters = {}
    if request.args.get('platform'): filters['platform'] = request.args.get('platform')
    if request.args.get('status'): filters['status'] = request.args.get('status')
    profiles = get_social_profiles(filters if filters else None)
    stats = {
        p['platform']: len([x for x in profiles if x['platform'] == p['platform']])
        for p in profiles
    }
    return render_template('social_profiles.html', profiles=profiles, stats=stats, page='social_profiles')


@app.route('/social-profile/add', methods=['POST'])
def social_profile_add():
    data = {k: (v[0] if isinstance(v, list) else v) for k, v in request.form.to_dict().items()}
    add_social_profile(data)
    flash('Profile added! Opening browser for login...', 'success')
    return redirect(url_for('social_profiles'))


@app.route('/social-profile/<platform>/<profile_name>/delete', methods=['POST'])
def social_profile_delete(platform, profile_name):
    delete_social_profile(platform, profile_name)
    flash('Profile deleted.', 'info')
    return redirect(url_for('social_profiles'))


@app.route('/social-profile/<platform>/<profile_name>/check', methods=['POST'])
def social_profile_check(platform, profile_name):
    from social_browser import get_browser, close_browser
    try:
        browser = get_browser(platform, profile_name, headless=True)
        logged_in = browser.check_login_status()
        close_browser(platform, profile_name)
        status = 'logged_in' if logged_in else 'logged_out'
    except Exception as e:
        status = 'error'
    update_social_profile(platform, profile_name, {'status': status})
    return jsonify({'success': True, 'status': status})


@app.route('/social-browser/<platform>/<profile_name>/open')
def social_browser_open(platform, profile_name):
    """Open a visible browser window for manual login."""
    from social_browser import get_browser
    try:
        browser = get_browser(platform, profile_name, headless=False)
        urls = {
            'instagram': 'https://www.instagram.com/accounts/login/',
            'tiktok': 'https://www.tiktok.com/login',
            'youtube': 'https://www.youtube.com/login',
            'facebook': 'https://www.facebook.com/login/',
            'twitter': 'https://twitter.com/login',
        }
        url = urls.get(platform, f'https://www.{platform}.com/')
        page = browser.new_page()
        page.goto(url, wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(2000)
        # Save cookies on close
        flash(f'Browser opened for {platform}. Log in, then close the browser tab.', 'info')
    except Exception as e:
        flash(f'Browser error: {str(e)}', 'error')
    return redirect(url_for('social_profiles'))


@app.route('/social-browser/close-all', methods=['POST'])
def social_browser_close_all():
    from social_browser import close_all_browsers
    close_all_browsers()
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════════════════════════
# POST SCHEDULER MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/post-scheduler')
def post_scheduler():
    filters = {}
    if request.args.get('platform'): filters['platform'] = request.args.get('platform')
    if request.args.get('status'): filters['status'] = request.args.get('status')
    posts = get_scheduled_posts(filters if filters else None)
    all_posts = get_scheduled_posts()
    today = datetime.now().date().isoformat()
    stats = {
        'scheduled': len([p for p in all_posts if p['status'] == 'pending']),
        'posted': len([p for p in all_posts if p['status'] == 'posted']),
        'failed': len([p for p in all_posts if p['status'] == 'failed']),
        'today': len([p for p in all_posts if p.get('scheduled_time', '').startswith(today)]),
    }
    return render_template('post_scheduler.html', posts=posts, stats=stats, page='post_scheduler')


@app.route('/scheduled-post/add', methods=['POST'])
def scheduled_post_add():
    data = {k: (v[0] if isinstance(v, list) else v) for k, v in request.form.to_dict().items()}
    # Combine date and time
    date_str = data.get('schedule_date', '')
    time_str = data.get('schedule_time', '')
    if date_str and time_str:
        data['scheduled_time'] = f"{date_str} {time_str}:00"
    # Handle file upload
    if 'content_file' in request.files:
        f = request.files['content_file']
        if f.filename:
            import uuid
            filename = f"{uuid.uuid4().hex[:8]}_{f.filename}"
            upload_dir = os.path.join(sys_path, 'media', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            f.save(os.path.join(upload_dir, filename))
            data['content_path'] = os.path.join(upload_dir, filename)
    add_scheduled_post(data)
    flash('Post scheduled!', 'success')
    return redirect(url_for('post_scheduler'))


@app.route('/scheduled-post/<int:post_id>/post', methods=['POST'])
def scheduled_post_now(post_id):
    post = get_scheduled_post(post_id)
    if not post:
        return jsonify({'success': False, 'error': 'Post not found'}), 404
    try:
        from social_browser import get_browser, SocialPost
        browser = get_browser(post['platform'], headless=False)
        social = SocialPost(post['platform'], post['content_path'] or '', post['caption'] or '')
        result = social.post_now(browser)
        if result.get('success'):
            update_scheduled_post(post_id, {
                'status': 'posted',
                'posted_time': datetime.now().isoformat(),
                'post_url': result.get('post_url', '')
            })
        return jsonify(result)
    except Exception as e:
        update_scheduled_post(post_id, {'status': 'failed', 'error_message': str(e)})
        return jsonify({'success': False, 'error': str(e)})


@app.route('/scheduled-post/<int:post_id>/delete', methods=['POST'])
def scheduled_post_delete(post_id):
    delete_scheduled_post(post_id)
    flash('Post deleted.', 'info')
    return redirect(url_for('post_scheduler'))


@app.route('/scheduler/process-queue', methods=['POST'])
def scheduler_process_queue():
    """Process all pending scheduled posts that are due."""
    posts = get_scheduled_posts({'status': 'pending'})
    now = datetime.now()
    processed = 0
    for post in posts:
        if post.get('scheduled_time'):
            sched = datetime.fromisoformat(post['scheduled_time'])
            if sched <= now:
                # Try to post
                try:
                    from social_browser import get_browser, SocialPost
                    browser = get_browser(post['platform'], headless=True)
                    social = SocialPost(post['platform'], post['content_path'] or '', post['caption'] or '')
                    result = social.post_now(browser)
                    update_scheduled_post(post['id'], {
                        'status': 'posted' if result.get('success') else 'failed',
                        'posted_time': datetime.now().isoformat() if result.get('success') else None,
                        'error_message': result.get('error', '')
                    })
                except Exception as e:
                    update_scheduled_post(post['id'], {'status': 'failed', 'error_message': str(e)})
                processed += 1
    return jsonify({'success': True, 'processed': processed})


# ══════════════════════════════════════════════════════════════════════════════
# CAMPAIGNS MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/campaigns')
def campaigns():
    campaign_list = get_campaigns()
    return render_template('campaigns.html', campaigns=campaign_list, page='campaigns')


@app.route('/campaign/add', methods=['POST'])
def campaign_add():
    data = {k: (v[0] if isinstance(v, list) else v) for k, v in request.form.to_dict().items()}
    if 'platforms' in data:
        data['platforms'] = request.form.getlist('platforms')
    add_campaign(data)
    flash('Campaign created!', 'success')
    return redirect(url_for('media_library'))


@app.route('/campaign/<int:campaign_id>/delete', methods=['POST'])
def campaign_delete(campaign_id):
    delete_campaign(campaign_id)
    flash('Campaign deleted.', 'info')
    return redirect(url_for('media_library'))


# ══════════════════════════════════════════════════════════════════════════════
# MEDIA LIBRARY MODULE
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/media-library')
def media_library():
    filters = {}
    if request.args.get('type'): filters['asset_type'] = request.args.get('type')
    if request.args.get('campaign_id'): filters['campaign_id'] = int(request.args.get('campaign_id'))
    assets = get_content_assets(filters if filters else None)
    campaigns = get_campaigns()
    stats = {
        'videos': len([a for a in assets if a['asset_type'] in ('video', 'captioned_video')]),
        'images': len([a for a in assets if a['asset_type'] == 'image']),
        'audio': len([a for a in assets if a['asset_type'] == 'audio']),
        'campaigns': len(campaigns),
    }
    return render_template('media_library.html', assets=assets, campaigns=campaigns,
                           stats=stats, page='media_library')


@app.route('/media-library/upload', methods=['POST'])
def media_library_upload():
    files = request.files.getlist('files')
    campaign_id = request.form.get('campaign_id')
    asset_type = request.form.get('asset_type', 'video')
    upload_dir = os.path.join(sys_path, 'media', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)

    for f in files:
        if f.filename:
            import uuid
            ext = os.path.splitext(f.filename)[1]
            saved_name = f"{uuid.uuid4().hex[:8]}{ext}"
            path = os.path.join(upload_dir, saved_name)
            f.save(path)
            # Detect type
            detected_type = asset_type
            if f.content_type.startswith('video/'): detected_type = 'video'
            elif f.content_type.startswith('image/'): detected_type = 'image'
            elif f.content_type.startswith('audio/'): detected_type = 'audio'
            add_content_asset({
                'asset_type': detected_type,
                'file_path': path,
                'format': ext.lstrip('.').upper(),
                'campaign_id': campaign_id if campaign_id else None,
            })
    flash(f'{len(files)} file(s) uploaded!', 'success')
    return redirect(url_for('media_library'))


@app.route('/media-library/export')
def media_library_export():
    ids = request.args.get('ids', '')
    if not ids:
        flash('No files selected.', 'error')
        return redirect(url_for('media_library'))
    # Return a zip or list
    return jsonify({'success': True, 'ids': ids.split(',')})


@app.route('/media-library/download')
def media_library_download():
    path = request.args.get('path', '')
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True)
    flash('File not found.', 'error')
    return redirect(url_for('media_library'))


@app.route('/media-library/campaign/<int:campaign_id>')
def media_library_campaign(campaign_id):
    campaign = get_campaign(campaign_id)
    assets = get_content_assets({'campaign_id': campaign_id})
    campaigns = get_campaigns()
    return render_template('media_library.html', assets=assets, campaigns=campaigns,
                           campaign=campaign, page='media_library')


@app.route('/content-asset/<int:asset_id>/delete', methods=['POST'])
def content_asset_delete(asset_id):
    delete_content_asset(asset_id)
    flash('Asset deleted.', 'info')
    return redirect(url_for('media_library'))


# ══════════════════════════════════════════════════════════════════════════════
# LIVE MONITOR
# ══════════════════════════════════════════════════════════════════════════════

_streaming_state = {
    'started_at': None,
    'current_phase': '15h play',
    'cycle': 1,
    'active_streams': 60,
    'uptime_hours': 0
}

@app.route('/live-monitor')
def live_monitor():
    accounts = get_streaming_accounts({'platform': 'Spotify', 'status': 'active'})
    
    # Generate simulated live logs
    logs = []
    for i in range(15):
        logs.append({
            'time': f'{14+i:02d}:{random.randint(0,59):02d}:00',
            'account': f'Listener {random.randint(1,20):02d}',
            'album': f'Memento Mori Vol. {random.randint(1,3)}',
            'status': random.choice(['▶ Playing', '▶ Streaming', '⏭ Next track'])
        })
    
    stats = {
        'active_count': _streaming_state.get('active_streams', 60),
        'account_count': len(accounts),
        'current_phase': _streaming_state.get('current_phase', '15h play'),
        'cycle': _streaming_state.get('cycle', 1),
        'uptime': _streaming_state.get('uptime_hours', 0)
    }
    
    return render_template('live_monitor.html', 
                         accounts=accounts, 
                         logs=logs,
                         **stats,
                         page='live_monitor')

@app.route('/api/streaming-status')
def api_streaming_status():
    """Return current streaming status for live monitoring."""
    return jsonify({
        'active_streams': _streaming_state.get('active_streams', 60),
        'current_phase': _streaming_state.get('current_phase', '15h play'),
        'cycle': _streaming_state.get('cycle', 1),
        'uptime_hours': _streaming_state.get('uptime_hours', 0),
        'started_at': _streaming_state.get('started_at', datetime.now().isoformat())
    })

# ══════════════════════════════════════════════════════════════════════════════
# PUBLORA SOCIAL POSTING MODULE
# ══════════════════════════════════════════════════════════════════════════════

PUBLORA_API_URL = "https://api.publora.com/v1"
PUBLORA_API_KEY = os.environ.get("PUBLORA_API_KEY", "")

def publora_headers():
    return {
        "Authorization": f"Bearer {PUBLORA_API_KEY}",
        "Content-Type": "application/json"
    }

def publora_is_configured():
    return bool(PUBLORA_API_KEY)

@app.route('/post-scheduler/publora')
def publora():
    """Publora connection management and posting hub."""
    configured = publora_is_configured()
    connections = []
    recent_posts = []
    analytics = {}

    if configured:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{PUBLORA_API_URL}/connections",
                headers=publora_headers()
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                connections = json.loads(resp.read())
        except Exception as e:
            flash(f"Could not fetch Publora connections: {e}", "error")

        try:
            import urllib.request
            req = urllib.request.Request(
                f"{PUBLORA_API_URL}/posts?limit=20",
                headers=publora_headers()
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                recent_posts = json.loads(resp.read())
        except Exception:
            pass

    return render_template('publora.html',
                           configured=configured,
                           connections=connections,
                           recent_posts=recent_posts,
                           analytics=analytics,
                           page='publora')


@app.route('/post-scheduler/publora/connect', methods=['POST'])
def publora_connect():
    """Save Publora API key to session/config."""
    api_key = request.form.get('api_key', '').strip()
    if not api_key:
        flash("API key is required.", "error")
        return redirect(url_for('publora'))

    # Store in session for this session, also offer env var instructions
    session['PUBLORA_API_KEY'] = api_key
    os.environ['PUBLORA_API_KEY'] = api_key

    # Test the key
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{PUBLORA_API_URL}/connections",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            flash(f"✓ Connected to Publora! Found {len(data) if isinstance(data, list) else 0} connected accounts.", "success")
    except urllib.error.HTTPError as e:
        flash(f"API error ({e.code}): Invalid API key or access denied.", "error")
    except Exception as e:
        flash(f"Connection test failed: {e}", "error")

    return redirect(url_for('publora'))


@app.route('/post-scheduler/publora/connections', methods=['GET'])
def publora_connections():
    """List all connected social accounts from Publora."""
    if not publora_is_configured():
        return jsonify({'error': 'PUBLORA_API_KEY not set'}), 400

    try:
        import urllib.request
        req = urllib.request.Request(
            f"{PUBLORA_API_URL}/connections",
            headers=publora_headers()
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return jsonify(json.loads(resp.read()))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/post-scheduler/publora/post', methods=['POST'])
def publora_post():
    """Post content to a specific platform via Publora."""
    if not publora_is_configured():
        return jsonify({'success': False, 'error': 'PUBLORA_API_KEY not configured'}), 400

    data = request.get_json() or {}
    content = data.get('content', '')
    platforms = data.get('platforms', [])
    media_urls = data.get('media_urls', [])

    if not content and not media_urls:
        return jsonify({'success': False, 'error': 'Content or media required'}), 400
    if not platforms:
        return jsonify({'success': False, 'error': 'At least one platform required'}), 400

    body = {
        "content": content,
        "platforms": platforms,
        "status": "published"
    }
    if media_urls:
        body["media_urls"] = media_urls

    try:
        import urllib.request
        req = urllib.request.Request(
            f"{PUBLORA_API_URL}/posts",
            data=json.dumps(body).encode('utf-8'),
            headers=publora_headers()
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            add_activity_log({
                'event_type': 'publora:post',
                'platform': ', '.join(platforms),
                'description': f'Publora post: {content[:60]}...',
                'success': 1,
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({'success': True, 'result': result})
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read())
        except:
            err_body = {'error': e.reason}
        return jsonify({'success': False, 'error': err_body}), e.code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/post-scheduler/publora/post-all', methods=['POST'])
def publora_post_all():
    """Post content to ALL connected platforms via Publora."""
    if not publora_is_configured():
        return jsonify({'success': False, 'error': 'PUBLORA_API_KEY not configured'}), 400

    data = request.get_json() or {}
    content = data.get('content', '')
    media_urls = data.get('media_urls', [])

    if not content and not media_urls:
        return jsonify({'success': False, 'error': 'Content or media required'}), 400

    # Get all connections first
    try:
        import urllib.request
        req = urllib.request.Request(
            f"{PUBLORA_API_URL}/connections",
            headers=publora_headers()
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            connections = json.loads(resp.read())
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to get connections: {e}'}), 500

    platforms = [c.get('platform', '').lower() for c in connections if c.get('platform')]
    if not platforms:
        return jsonify({'success': False, 'error': 'No connected platforms found'}), 400

    body = {
        "content": content,
        "platforms": platforms,
        "status": "published"
    }
    if media_urls:
        body["media_urls"] = media_urls

    try:
        import urllib.request
        req = urllib.request.Request(
            f"{PUBLORA_API_URL}/posts",
            data=json.dumps(body).encode('utf-8'),
            headers=publora_headers()
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            add_activity_log({
                'event_type': 'publora:post_all',
                'platform': 'all',
                'description': f'Publora post to all ({len(platforms)} platforms): {content[:60]}...',
                'success': 1,
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({'success': True, 'platforms_posted': platforms, 'result': result})
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read())
        except:
            err_body = {'error': e.reason}
        return jsonify({'success': False, 'error': err_body}), e.code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/post-scheduler/publora/schedule', methods=['POST'])
def publora_schedule():
    """Schedule a post for later via Publora."""
    if not publora_is_configured():
        return jsonify({'success': False, 'error': 'PUBLORA_API_KEY not configured'}), 400

    data = request.get_json() or {}
    content = data.get('content', '')
    platforms = data.get('platforms', [])
    scheduled_time = data.get('scheduled_time')  # ISO format: "2024-12-25T18:00:00Z"
    media_urls = data.get('media_urls', [])

    if not content and not media_urls:
        return jsonify({'success': False, 'error': 'Content or media required'}), 400
    if not platforms:
        return jsonify({'success': False, 'error': 'At least one platform required'}), 400
    if not scheduled_time:
        return jsonify({'success': False, 'error': 'scheduled_time required (ISO format)'}), 400

    body = {
        "content": content,
        "platforms": platforms,
        "status": "scheduled",
        "scheduledTime": scheduled_time
    }
    if media_urls:
        body["media_urls"] = media_urls

    try:
        import urllib.request
        req = urllib.request.Request(
            f"{PUBLORA_API_URL}/posts",
            data=json.dumps(body).encode('utf-8'),
            headers=publora_headers()
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            add_activity_log({
                'event_type': 'publora:schedule',
                'platform': ', '.join(platforms),
                'description': f'Publora scheduled: {content[:60]}... for {scheduled_time}',
                'success': 1,
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({'success': True, 'result': result})
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read())
        except:
            err_body = {'error': e.reason}
        return jsonify({'success': False, 'error': err_body}), e.code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/post-scheduler/publora/analytics', methods=['GET'])
def publora_analytics():
    """Get posting analytics from Publora."""
    if not publora_is_configured():
        return jsonify({'error': 'PUBLORA_API_KEY not configured'}), 400

    try:
        import urllib.request
        req = urllib.request.Request(
            f"{PUBLORA_API_URL}/posts",
            headers=publora_headers()
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            posts = json.loads(resp.read())
            analytics = {
                'total_posts': len(posts) if isinstance(posts, list) else 0,
                'by_platform': {},
                'recent': posts[:20] if isinstance(posts, list) else []
            }
            if isinstance(posts, list):
                for p in posts:
                    plat = p.get('platform', 'unknown')
                    analytics['by_platform'][plat] = analytics['by_platform'].get(plat, 0) + 1
            return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# API ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/stats')
def api_stats():
    try:
        stats = get_dashboard_stats()
        stats['streaming_summary'] = get_streaming_stats_summary()
        stats['recent_activity'] = get_activity_logs(limit=20)
        stats['growth'] = get_growth_stats(30)
    except:
        stats = get_dashboard_stats()
    return jsonify(stats)

@app.route('/api/activity')
def api_activity():
    filters = {}
    if request.args.get('platform'): filters['platform'] = request.args.get('platform')
    if request.args.get('account_id'): filters['account_id'] = int(request.args.get('account_id'))
    logs = get_activity_logs(filters, limit=100)
    return jsonify(logs)

@app.route('/api/proxy/<int:proxy_id>')
def api_proxy(proxy_id):
    p = get_proxy(proxy_id)
    return jsonify(p) if p else jsonify({'error': 'Not found'}), 404

@app.route('/api/task/run/<int:task_id>', methods=['POST'])
def api_task_run(task_id):
    success, msg = run_scheduled_task(task_id)
    return jsonify({'success': success, 'message': msg})


# ══════════════════════════════════════════════════════════════════════════════
# GROWTH DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/growth-dashboard')
def growth_dashboard():
    """Visual growth analytics dashboard."""
    growth = get_growth_stats(90)
    summary = get_streaming_stats_summary()
    logs = get_activity_logs(limit=100)
    return render_template('growth_dashboard.html', growth=growth,
                           summary=summary, logs=logs, page='growth_dashboard')


# ══════════════════════════════════════════════════════════════════════════════
# SPOTIFY STATS (Real Spotify for Artists Integration)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/spotify-stats')
def spotify_stats():
    """
    Real Spotify stats for Mystik Singh.
    Source priority:
    1. Scrape Spotify for Artists with Playwright (requires any Spotify Premium login)
    2. Real activity logs from streaming automation (if streaming has been running)
    3. Manual entry / last known values

    Artist URL: https://open.spotify.com/artist/6w6er0yLYxlwV5JHr7rK7B
    """
    force_refresh = request.args.get('refresh') == '1'

    # Try to get cached stats first (valid for 5 minutes)
    cache_key = 'spotify_stats_cache'
    cache_file = os.path.join(sys_path, 'logs', 'spotify_stats_cache.json')
    stats = None

    if not force_refresh and os.path.exists(cache_file):
        try:
            import json as _json
            with open(cache_file) as f:
                cache = _json.load(f)
            # Cache valid for 5 minutes
            if time.time() - cache.get('ts', 0) < 300:
                stats = cache.get('data')
        except Exception:
            pass

    if not stats:
        # Try real scraping first
        try:
            from spotify_stats_scraper import scrape_spotify_stats
            stats = scrape_spotify_stats()
        except Exception as e:
            print(f"Stats scrape error: {e}")
            stats = None

        # Fall back to activity log stats
        if not stats or stats.get('source') == 'unavailable':
            try:
                from spotify_stats_scraper import get_stats_from_activity_logs
                stats = get_stats_from_activity_logs()
            except Exception:
                stats = {'source': 'none', 'error': 'No data available'}

        # Cache the result
        if stats and stats.get('source') != 'unavailable':
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump({'ts': time.time(), 'data': stats}, f)
            except Exception:
                pass

    return render_template('spotify_stats.html', stats=stats, page='spotify_stats')


@app.route('/spotify-stats/refresh', methods=['POST'])
def spotify_stats_refresh():
    """Force refresh of Spotify stats."""
    try:
        from spotify_stats_scraper import scrape_spotify_stats, get_stats_from_activity_logs
        try:
            stats = scrape_spotify_stats()
        except Exception:
            stats = get_stats_from_activity_logs()

        # Update cache
        cache_file = os.path.join(sys_path, 'logs', 'spotify_stats_cache.json')
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump({'ts': time.time(), 'data': stats}, f)
        except Exception:
            pass

        return jsonify({'success': True, 'source': stats.get('source', 'unknown')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/spotify-stats/setup', methods=['GET', 'POST'])
def spotify_stats_setup():
    """
    Configure Spotify for Artists scraping credentials.
    Any Spotify Premium account can access artist analytics.
    """
    creds_file = os.path.join(sys_path, 'spotify_stats_credentials.json')
    error = None
    success = False

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if email and password:
            try:
                with open(creds_file, 'w') as f:
                    json.dump({'email': email, 'password': password}, f)
                flash('Credentials saved! Click "Test Connection" to verify.', 'success')
                success = True
            except Exception as e:
                error = str(e)
        else:
            error = 'Email and password are required'

    # Check if credentials exist
    has_creds = os.path.exists(creds_file)

    if request.args.get('test') and has_creds:
        try:
            with open(creds_file) as f:
                creds = json.load(f)
            from spotify_stats_scraper import scrape_spotify_stats
            result = scrape_spotify_stats(
                email=creds.get('email'),
                password=creds.get('password'),
                headless=True,
            )
            if result.get('error'):
                flash(f'Connection test failed: {result["error"]}', 'error')
            else:
                flash(f'✓ Connected! Source: {result.get("source", "unknown")}', 'success')
        except Exception as e:
            flash(f'Test error: {e}', 'error')

    return render_template('spotify_stats_setup.html',
                           has_creds=has_creds, error=error, success=success,
                           page='spotify_stats')


# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD-POST API INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

UPLOAD_POST_API_URL = "https://api.upload-post.com/api"
UPLOAD_POST_API_KEY = os.environ.get("UPLOAD_POST_API_KEY")

def uploadpost_is_configured():
    return bool(os.environ.get("UPLOAD_POST_API_KEY"))

def uploadpost_headers():
    return {"Authorization": f"Apikey {os.environ.get('UPLOAD_POST_API_KEY')}", "Content-Type": "application/json"}

def uploadpost_api(endpoint, method="GET", data=None, files=None):
    """Make an API call to upload-post.com"""
    import urllib.request, urllib.parse, urllib.error
    url = f"{UPLOAD_POST_API_URL}/{endpoint}"
    headers = {"Authorization": f"Apikey {os.environ.get('UPLOAD_POST_API_KEY')}"}
    
    if files:
        # Multipart form upload
        import mimetypes
        boundary = "----FormBoundary" + str(uuid.uuid4())
        body = b""
        # Add fields
        if data:
            for key, val in data.items():
                body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{val}\r\n".encode()
        # Add file
        for key, file_info in files.items():
            filename, content = file_info
            mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"; filename=\"{filename}\"\r\nContent-Type: {mime}\r\n\r\n".encode()
            body += content + "\r\n".encode()
        body += f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        headers.pop("Content-Type", None)  # remove JSON content type for multipart
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
    else:
        body = json.dumps(data).encode() if data else None
        if data:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode()), resp.status
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode())
            return err_body, e.code
        except:
            return {"error": e.reason}, e.code
    except Exception as e:
        return {"error": str(e)}, 500


@app.route('/content/upload-post')
def upload_post():
    """Upload-Post hub page - unified social media posting"""
    api_key = os.environ.get("UPLOAD_POST_API_KEY")
    is_configured = uploadpost_is_configured()
    
    # Get account info if configured
    account_info = None
    if is_configured:
        try:
            result, status = uploadpost_api("me", method="GET")
            if status == 200:
                account_info = result
            else:
                account_info = {"error": result.get("error", "Invalid API key")}
        except Exception as e:
            account_info = {"error": str(e)}
    
    # Get recent uploads from local storage
    history_file = os.path.join(sys_path, 'logs', 'upload_post_history.json')
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file) as f:
                history = json.load(f)
        except:
            history = []
    
    # Get scheduled posts
    scheduled = get_scheduled_posts() if 'get_scheduled_posts' in dir() else []
    
    return render_template('upload_post.html', 
                           api_key=api_key or "",
                           is_configured=is_configured,
                           account_info=account_info,
                           history=history[:20],
                           scheduled=scheduled[:20],
                           page='upload_post')


@app.route('/content/upload-post/connect', methods=['POST'])
def upload_post_connect():
    """Save and test the Upload-Post API key"""
    api_key = request.form.get('api_key', '').strip()
    
    if api_key:
        os.environ['UPLOAD_POST_API_KEY'] = api_key
        # Save to env file for persistence
        env_file = os.path.join(sys_path, '.env.upload_post')
        try:
            with open(env_file, 'w') as f:
                f.write(f"UPLOAD_POST_API_KEY={api_key}\n")
        except:
            pass
    
    # Test the API key
    if api_key:
        try:
            result, status = uploadpost_api("me", method="GET")
            if status == 200:
                flash(f'✓ Connected to Upload-Post! Account: {result.get("email", "OK")}', 'success')
            else:
                flash(f'⚠ API key test failed: {result.get("error", "Invalid key")}', 'error')
        except Exception as e:
            flash(f'⚠ Connection error: {e}', 'error')
    else:
        flash('API key cleared', 'info')
    
    return redirect(url_for('upload_post'))


@app.route('/content/upload-post/me', methods=['GET'])
def upload_post_me():
    """Validate API key and get account info"""
    if not uploadpost_is_configured():
        return jsonify({"configured": False, "error": "API key not set"})
    
    result, status = uploadpost_api("me", method="GET")
    result["configured"] = (status == 200)
    return jsonify(result), status


@app.route('/content/upload-post/upload', methods=['POST'])
def upload_post_upload():
    """Upload video/image to selected platforms"""
    if not uploadpost_is_configured():
        return jsonify({"success": False, "error": "Upload-Post API not configured"}), 400
    
    # Get platforms
    platforms = request.form.getlist('platforms')
    if not platforms:
        return jsonify({"success": False, "error": "No platforms selected"}), 400
    
    caption = request.form.get('caption', '')
    description = request.form.get('description', '')
    title = request.form.get('title', '')
    
    # Handle file upload
    files = {}
    data = {"caption": caption, "description": description, "title": title}
    
    if 'media_file' in request.files:
        f = request.files['media_file']
        if f.filename:
            files['media'] = (f.filename, f.read())
    
    if not files and not request.form.get('media_url'):
        return jsonify({"success": False, "error": "No media file or URL provided"}), 400
    
    # Build platform list
    data['platforms'] = ','.join(platforms)
    
    # Use URL if no file
    if not files and request.form.get('media_url'):
        data['media_url'] = request.form.get('media_url')
    
    try:
        result, status = uploadpost_api("upload", method="POST", data=data, files=files if files else None)
        
        # Save to history
        if status == 200:
            history_file = os.path.join(sys_path, 'logs', 'upload_post_history.json')
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            history = []
            if os.path.exists(history_file):
                try:
                    with open(history_file) as f:
                        history = json.load(f)
                except:
                    history = []
            history.insert(0, {
                "id": str(uuid.uuid4())[:8],
                "platforms": platforms,
                "caption": caption[:100],
                "status": "uploaded",
                "date": datetime.now().isoformat(),
                "result": result
            })
            with open(history_file, 'w') as f:
                json.dump(history[:100], f)
        
        return jsonify(result), status
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/content/upload-post/upload-url', methods=['POST'])
def upload_post_upload_url():
    """Upload from URL instead of file"""
    if not uploadpost_is_configured():
        return jsonify({"success": False, "error": "Upload-Post API not configured"}), 400
    
    platforms = request.form.getlist('platforms')
    if not platforms:
        return jsonify({"success": False, "error": "No platforms selected"}), 400
    
    media_url = request.form.get('media_url', '').strip()
    if not media_url:
        return jsonify({"success": False, "error": "No media URL provided"}), 400
    
    data = {
        "media_url": media_url,
        "platforms": ','.join(platforms),
        "caption": request.form.get('caption', ''),
        "description": request.form.get('description', ''),
        "title": request.form.get('title', '')
    }
    
    try:
        result, status = uploadpost_api("upload", method="POST", data=data)
        
        if status == 200:
            history_file = os.path.join(sys_path, 'logs', 'upload_post_history.json')
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            history = []
            if os.path.exists(history_file):
                try:
                    with open(history_file) as f:
                        history = json.load(f)
                except:
                    history = []
            history.insert(0, {
                "id": str(uuid.uuid4())[:8],
                "platforms": platforms,
                "caption": data['caption'][:100],
                "status": "uploaded",
                "date": datetime.now().isoformat(),
                "result": result
            })
            with open(history_file, 'w') as f:
                json.dump(history[:100], f)
        
        return jsonify(result), status
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/content/upload-post/schedule', methods=['POST'])
def upload_post_schedule():
    """Schedule a post for later"""
    if not uploadpost_is_configured():
        return jsonify({"success": False, "error": "Upload-Post API not configured"}), 400
    
    platforms = request.form.getlist('platforms')
    if not platforms:
        return jsonify({"success": False, "error": "No platforms selected"}), 400
    
    scheduled_time = request.form.get('scheduled_time', '')
    timezone = request.form.get('timezone', 'America/Los_Angeles')
    
    if not scheduled_time:
        return jsonify({"success": False, "error": "No scheduled time provided"}), 400
    
    data = {
        "platforms": ','.join(platforms),
        "caption": request.form.get('caption', ''),
        "description": request.form.get('description', ''),
        "title": request.form.get('title', ''),
        "scheduled_time": scheduled_time,
        "timezone": timezone
    }
    
    # Check if there's a file
    files = {}
    if 'media_file' in request.files:
        f = request.files['media_file']
        if f.filename:
            files['media'] = (f.filename, f.read())
    
    try:
        result, status = uploadpost_api("schedule", method="POST", data=data, files=files if files else None)
        
        if status == 200:
            # Also save to local scheduler
            try:
                if 'scheduled_posts' in dir():
                    from models import add_scheduled_post as local_add
                    local_add({
                        "platform": ','.join(platforms),
                        "content": request.form.get('caption', ''),
                        "scheduled_time": scheduled_time,
                        "timezone": timezone,
                        "source": "upload-post"
                    })
            except:
                pass
        
        return jsonify(result), status
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/content/upload-post/history', methods=['GET'])
def upload_post_history():
    """Get upload history"""
    history_file = os.path.join(sys_path, 'logs', 'upload_post_history.json')
    if os.path.exists(history_file):
        try:
            with open(history_file) as f:
                return jsonify(json.load(f)), 200
        except:
            pass
    return jsonify([]), 200


@app.route('/content/upload-post/schedule', methods=['GET'])
def upload_post_schedule_list():
    """List scheduled posts from Upload-Post API"""
    if not uploadpost_is_configured():
        return jsonify({"error": "Not configured"}), 400
    
    try:
        result, status = uploadpost_api("schedule", method="GET")
        return jsonify(result), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/content/upload-post/schedule/<job_id>', methods=['DELETE'])
def upload_post_cancel_schedule(job_id):
    """Cancel a scheduled post"""
    if not uploadpost_is_configured():
        return jsonify({"error": "Not configured"}), 400
    
    try:
        result, status = uploadpost_api(f"schedule/{job_id}", method="DELETE")
        return jsonify(result), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/content/upload-post/analytics', methods=['GET'])
def upload_post_analytics():
    """Analytics dashboard"""
    if not uploadpost_is_configured():
        return jsonify({"error": "Not configured"}), 400
    
    try:
        result, status = uploadpost_api("analytics", method="GET")
        return jsonify(result), status
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# OUTREACH AUTOMATION
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/outreach')
def outreach_dashboard():
    """Main outreach dashboard showing campaigns and stats."""
    stats = get_outreach_stats()
    campaigns = get_outreach_campaigns()
    return render_template('outreach_dashboard.html',
                           stats=stats, campaigns=campaigns, page='outreach_dashboard')


@app.route('/outreach/campaigns')
def outreach_campaigns():
    """List all outreach campaigns."""
    campaigns = get_outreach_campaigns()
    return render_template('outreach_campaigns.html',
                           campaigns=campaigns, page='outreach_campaigns')


@app.route('/outreach/campaign/<int:campaign_id>')
def outreach_campaign_detail(campaign_id):
    """Campaign detail view with sent emails and status."""
    campaign = get_outreach_campaign(campaign_id)
    if not campaign:
        flash('Campaign not found', 'error')
        return redirect(url_for('outreach_campaigns'))
    emails = get_outreach_emails(campaign_id)
    stats = get_outreach_stats()
    return render_template('campaign_detail.html',
                           campaign=campaign, emails=emails,
                           stats=stats, page='outreach_campaigns')


@app.route('/outreach/campaign/new', methods=['GET', 'POST'])
def outreach_new_campaign():
    """Create a new outreach campaign."""
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'track_id': int(request.form['track_id']) if request.form.get('track_id') else None,
            'album_id': int(request.form['album_id']) if request.form.get('album_id') else None,
            'spotify_link': request.form.get('spotify_link') or None,
            'apple_link': request.form.get('apple_link') or None,
            'genre_filter': request.form.get('genre_filter') or None,
            'tier_filter': request.form.get('tier_filter') or None,
            'min_followers': int(request.form['min_followers']) if request.form.get('min_followers') else None,
            'max_followers': int(request.form['max_followers']) if request.form.get('max_followers') else None,
            'template_id': int(request.form['template_id']) if request.form.get('template_id') else None,
            'status': 'draft',
            'notes': request.form.get('notes') or None,
        }
        campaign_id = create_outreach_campaign(data)
        flash(f'Campaign "{data["name"]}" created!', 'success')
        return redirect(url_for('outreach_campaign_detail', campaign_id=campaign_id))

    artist = get_artist_profile()
    tracks = get_tracks()
    albums = get_albums()
    templates = get_email_templates()
    return render_template('new_campaign.html',
                           artist=artist, tracks=tracks, albums=albums,
                           templates=templates, page='outreach_campaigns')


@app.route('/outreach/campaign/<int:campaign_id>/send', methods=['POST'])
def outreach_campaign_send(campaign_id):
    """Execute campaign - send pitches to selected curators."""
    campaign = get_outreach_campaign(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404

    # Get curators matching campaign filters
    curators = get_curators_for_campaign(
        genre_filter=campaign.get('genre_filter'),
        tier_filter=campaign.get('tier_filter'),
        min_followers=campaign.get('min_followers'),
        max_followers=campaign.get('max_followers'),
        exclude_recent=True,
        campaign_id=campaign_id
    )

    # Get email accounts
    email_accounts = get_email_accounts({'status': 'active'})
    if not email_accounts:
        return jsonify({'error': 'No active email accounts configured'}), 400

    template = get_email_template(campaign['template_id']) if campaign.get('template_id') else None

    # Get track info
    track = get_track(campaign['track_id']) if campaign.get('track_id') else None

    sent_count = 0
    errors = []
    for i, curator in enumerate(curators):
        # Round-robin email selection
        email_account = email_accounts[i % len(email_accounts)]

        # Build email body
        if template:
            try:
                body = template['body'].format(
                    curator_name=curator['name'],
                    playlist_name=curator['playlist_name'],
                    track_title=track['title'] if track else 'My Track',
                    artist_name=artist['name'] if (artist := get_artist_profile()) else 'Artist',
                    sender_name=email_account['display_name'],
                    genre=curator['genre_focus'] or 'Hip Hop',
                    description='a fresh track with a unique sound',
                    production_notes='hard-hitting drums, melodic elements',
                    lyrical_theme='authentic storytelling and real experiences',
                    track_link=campaign['spotify_link'] or campaign['apple_link'] or '#',
                    curator_vibe=curator['notes'][:50] if curator['notes'] else 'authentic hip-hop',
                    contact_link=artist['website'] if (artist := get_artist_profile()) else '#',
                    curator_email=curator['email'] or '',
                    reference_track='recent热门 tracks',
                    genre_description='a modern hip-hop track',
                    song_backstory='Born from real experiences and crafted with care.',
                )
                subject = template['subject'].format(
                    track_title=track['title'] if track else 'My Track',
                    playlist_name=curator['playlist_name'],
                    artist_name=artist['name'] if (artist := get_artist_profile()) else 'Artist',
                )
            except (KeyError, ValueError):
                body = f"Hi {curator['name']},\n\nI'd love for my track to be considered for {curator['playlist_name']}.\n\nLink: {campaign['spotify_link'] or '#'}\n\nThanks!"
                subject = f"{track['title'] if track else 'My Track'} for {curator['playlist_name']}"
        else:
            body = f"Hi {curator['name']},\n\nI'd love for my track to be considered for {curator['playlist_name']}.\n\nLink: {campaign['spotify_link'] or '#'}\n\nThanks!"
            subject = f"{track['title'] if track else 'My Track'} for {curator['playlist_name']}"

        # Create outreach email record
        try:
            create_outreach_email({
                'campaign_id': campaign_id,
                'curator_id': curator['id'],
                'email_account_id': email_account['id'],
                'template_id': campaign.get('template_id'),
                'subject': subject,
                'body': body,
                'sent_at': datetime.now().isoformat(),
                'follow_up_level': 0,
                'response_status': 'pending',
            })
            sent_count += 1
        except Exception as e:
            errors.append(f"Failed to record email for {curator['name']}: {str(e)}")

    # Update campaign stats
    update_outreach_campaign(campaign_id, {
        'status': 'sent',
        'sent_at': datetime.now().isoformat(),
        'emails_sent': sent_count,
        'curators_contacted': len(curators),
    })

    return jsonify({
        'success': True,
        'sent': sent_count,
        'errors': errors if errors else None,
        'message': f'Campaign sent to {sent_count} curators!'
    })


@app.route('/outreach/send', methods=['POST'])
def outreach_send_single():
    """Send a single pitch email to selected curators."""
    data = request.get_json() or request.form.to_dict()
    curator_ids = data.getlist('curator_ids') if hasattr(data, 'getlist') else (
        data.get('curator_ids', '').split(',') if isinstance(data.get('curator_ids'), str) else [data.get('curator_ids')]
    )
    track_link = data.get('track_link') or '#'
    template_id = int(data.get('template_id')) if data.get('template_id') else None
    subject = data.get('subject', 'New track for your playlist')
    body = data.get('body', 'Hi, check out my new track.')

    email_accounts = get_email_accounts({'status': 'active'})
    if not email_accounts:
        return jsonify({'error': 'No active email accounts'}), 400

    artist = get_artist_profile()
    template = get_email_template(template_id) if template_id else None
    track = get_track(int(data['track_id'])) if data.get('track_id') else None

    sent = 0
    for i, cid in enumerate(curator_ids):
        if not cid:
            continue
        try:
            cid = int(cid)
        except (ValueError, TypeError):
            continue

        curator = get_curator(cid)
        if not curator:
            continue

        email_account = email_accounts[i % len(email_accounts)]

        # Format template
        if template:
            try:
                body_text = template['body'].format(
                    curator_name=curator['name'], playlist_name=curator['playlist_name'],
                    track_title=track['title'] if track else 'My Track',
                    artist_name=artist['name'], sender_name=email_account['display_name'],
                    genre=curator['genre_focus'] or 'Hip Hop',
                    description='a fresh track with a unique sound',
                    production_notes='hard-hitting drums, melodic elements',
                    lyrical_theme='authentic storytelling',
                    track_link=track_link,
                    curator_vibe=curator['notes'][:50] if curator['notes'] else 'authentic hip-hop',
                    contact_link=artist.get('website') or '#',
                    reference_track='recent热门 tracks',
                    genre_description='a modern hip-hop track',
                    song_backstory='Born from real experiences.',
                )
                subject_text = template['subject'].format(
                    track_title=track['title'] if track else 'My Track',
                    playlist_name=curator['playlist_name'],
                    artist_name=artist['name'],
                )
            except (KeyError, ValueError):
                body_text, subject_text = body, subject
        else:
            body_text, subject_text = body, subject

        create_outreach_email({
            'campaign_id': None,
            'curator_id': cid,
            'email_account_id': email_account['id'],
            'template_id': template_id,
            'subject': subject_text,
            'body': body_text,
            'sent_at': datetime.now().isoformat(),
            'follow_up_level': 0,
            'response_status': 'pending',
        })
        sent += 1

    return jsonify({'success': True, 'sent': sent})


@app.route('/outreach/stats')
def outreach_stats():
    """Get outreach statistics."""
    stats = get_outreach_stats()
    return jsonify(stats)


@app.route('/outreach/follow-ups')
def outreach_follow_ups():
    """Show follow-up queue."""
    follow_ups = get_next_follow_ups()
    templates = get_email_templates()
    return render_template('follow_ups.html',
                           follow_ups=follow_ups, templates=templates, page='outreach_dashboard')


@app.route('/outreach/follow-up/send', methods=['POST'])
def outreach_send_follow_up():
    """Send a follow-up email."""
    data = request.get_json()
    email_id = int(data.get('email_id'))
    follow_up_level = int(data.get('follow_up_level', 1))

    # Get original email
    emails = get_outreach_emails(filters={'curator_id': data.get('curator_id')})
    original_email = emails[0] if emails else None

    if not original_email:
        return jsonify({'error': 'Original email not found'}), 404

    curator = get_curator(int(data.get('curator_id')))
    email_accounts = get_email_accounts({'status': 'active'})
    if not email_accounts:
        return jsonify({'error': 'No active email accounts'}), 400
    email_account = email_accounts[0]

    # Get appropriate follow-up template
    templates = get_email_templates()
    template_map = {t['category']: t for t in templates}
    if follow_up_level == 1:
        template = template_map.get('follow_up_3day')
    elif follow_up_level == 2:
        template = template_map.get('follow_up_1week')
    else:
        template = template_map.get('follow_up_2week')

    artist = get_artist_profile()
    track = get_track(original_email.get('track_id')) if original_email.get('track_id') else None

    if template:
        try:
            body = template['body'].format(
                curator_name=curator['name'] if curator else '',
                playlist_name=curator['playlist_name'] if curator else '',
                track_title=track['title'] if track else 'My Track',
                sender_name=email_account['display_name'],
                genre=curator['genre_focus'] if curator else 'Hip Hop',
                track_link=original_email.get('body', '').split('\n\n')[-1] if original_email.get('body') else '#',
                artist_name=artist['name'],
            )
            subject = template['subject'].format(
                track_title=track['title'] if track else 'My Track',
                playlist_name=curator['playlist_name'] if curator else '',
            )
        except (KeyError, ValueError):
            body = f"Just bumping my previous note. Would love to be considered!"
            subject = f"re: {track['title'] if track else 'My Track'}"
    else:
        body = f"Just bumping my previous note. Would love to be considered!"
        subject = f"re: {track['title'] if track else 'My Track'}"

    # Create follow-up email record
    create_outreach_email({
        'campaign_id': original_email.get('campaign_id'),
        'curator_id': int(data.get('curator_id')),
        'email_account_id': email_account['id'],
        'template_id': template['id'] if template else None,
        'subject': subject,
        'body': body,
        'sent_at': datetime.now().isoformat(),
        'follow_up_level': follow_up_level,
        'response_status': 'pending',
    })

    # Update original email follow-up level
    update_outreach_email(email_id, {'follow_up_level': follow_up_level})

    return jsonify({'success': True, 'message': 'Follow-up sent!'})


@app.route('/outreach/response', methods=['POST'])
def outreach_mark_response():
    """Mark an outreach email with a response status."""
    data = request.get_json()
    email_id = int(data.get('email_id'))
    status = data.get('status')  # 'responded', 'accepted', 'rejected', 'no_response'

    update_outreach_email(email_id, {
        'response_status': status,
        'response_date': datetime.now().date().isoformat(),
    })

    # Update campaign counters if applicable
    emails = get_outreach_emails()
    email = next((e for e in emails if e['id'] == email_id), None)
    if email and email.get('campaign_id'):
        campaign = get_outreach_campaign(email['campaign_id'])
        if campaign:
            counters = {
                'responses_received': campaign.get('responses_received', 0) + 1
            }
            if status == 'accepted':
                counters['acceptances'] = campaign.get('acceptances', 0) + 1
            update_outreach_campaign(email['campaign_id'], counters)

    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# VOCAL SEPARATOR (Demucs)
# ══════════════════════════════════════════════════════════════════════════════

# Map model names to their classes and metadata
DEMUCS_MODELS = {
    'htdemucs':    {'class': 'HTDemucs',  'stems': 4, 'desc': 'Best quality hybrid transformer'},
    'htdemucs_ft': {'class': 'HTDemucs',  'stems': 4, 'desc': 'Finer-tuned, slower but more accurate'},
    'hdemucs':     {'class': 'HDemucs',    'stems': 4, 'desc': 'Hybrid Demucs model'},
    'demucs':      {'class': 'Demucs',     'stems': 4, 'desc': 'Original Demucs model'},
}


@app.route('/vocal-separator', methods=['GET', 'POST'])
def vocal_separator():
    """
    Separate audio into stems using Demucs.
    Supports multiple models but all produce 4 stems:
    vocals, drums, bass, other.
    """
    stems_data = None
    processing_time = None
    error_msg = None
    original_filename = None
    model_name = 'htdemucs'

    if request.method == 'POST':
        if 'audio_file' not in request.files:
            error_msg = 'No file uploaded.'
            return render_template('vocal_separator.html', page='vocal_separator',
                                   error=error_msg, stems=None, model_name=model_name)

        file = request.files['audio_file']
        if file.filename == '':
            error_msg = 'No file selected.'
            return render_template('vocal_separator.html', page='vocal_separator',
                                   error=error_msg, stems=None, model_name=model_name)

        # Validate file size (50MB max)
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > 50 * 1024 * 1024:
            error_msg = 'File too large. Maximum size is 50MB.'
            return render_template('vocal_separator.html', page='vocal_separator',
                                   error=error_msg, stems=None, model_name=model_name)

        allowed = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac']
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            error_msg = f'Unsupported format: {ext}. Use MP3, WAV, FLAC, M4A, OGG, or AAC.'
            return render_template('vocal_separator.html', page='vocal_separator',
                                   error=error_msg, stems=None, model_name=model_name)

        original_filename = file.filename
        model_name = request.form.get('model_name', 'htdemucs')
        if model_name not in DEMUCS_MODELS:
            model_name = 'htdemucs'

        vocal_remover = request.form.get('vocal_remover') == '1'

        import uuid, time as time_module

        # Save uploaded file
        upload_id = uuid.uuid4().hex[:8]
        upload_dir = os.path.join(sys_path, 'static', 'stems', upload_id)
        os.makedirs(upload_dir, exist_ok=True)
        audio_path = os.path.join(upload_dir, f'original{ext}')
        file.save(audio_path)

        try:
            start_time = time_module.time()

            # Import demucs v4 components
            import torch
            from demucs.pretrained import get_model
            from demucs.apply import apply_model
            import torchaudio

            # Load the selected model from pretrained weights
            model = get_model(model_name)
            model.eval()

            # Load audio
            mix, sr = torchaudio.load(audio_path)

            # Apply model - returns tensor [sources, channels, samples]
            with torch.no_grad():
                estimates = apply_model(model, mix, device='cpu', num_workers=4)

            stems_result = {}
            for idx, src_name in enumerate(model.sources):
                src_wav = estimates[idx].cpu()
                out_path = os.path.join(upload_dir, f'{src_name}.wav')
                torchaudio.save(out_path, src_wav, sr)
                stems_result[src_name] = f'/static/stems/{upload_id}/{src_name}.wav'

            # Vocal remover: create instrumental = mix - vocals
            if vocal_remover and 'vocals' in stems_result:
                vocal_path = os.path.join(upload_dir, 'vocals.wav')
                instr_path = os.path.join(upload_dir, 'instrumental.wav')
                vocal_wav, _ = torchaudio.load(vocal_path)
                # Reuse `mix` (already loaded from original audio)
                mix_wav = mix
                # Handle channel mismatch
                if vocal_wav.shape[0] != mix_wav.shape[0]:
                    max_ch = max(vocal_wav.shape[0], mix_wav.shape[0])
                    def pad_channels(t, ch):
                        if t.shape[0] == ch: return t
                        return t.expand(ch, -1)
                    vocal_wav = pad_channels(vocal_wav, max_ch)
                    mix_wav = pad_channels(mix_wav, max_ch)
                # Trim/pad to same length
                min_len = min(vocal_wav.shape[1], mix_wav.shape[1])
                vocal_wav = vocal_wav[:, :min_len]
                mix_wav_padded = mix_wav[:, :min_len]
                # Instrumental = mix - vocals
                instrumental = (mix_wav_padded - vocal_wav).clamp(-1.0, 1.0)
                torchaudio.save(instr_path, instrumental, sr)
                stems_result['instrumental'] = f'/static/stems/{upload_id}/instrumental.wav'

            processing_time = round(time_module.time() - start_time, 1)
            stems_data = stems_result

            # Clean up original
            try:
                os.remove(audio_path)
            except:
                pass

        except Exception as e:
            error_msg = f'Separation failed: {str(e)}'
            import traceback
            traceback.print_exc()

    return render_template('vocal_separator.html', page='vocal_separator',
                           error=error_msg, stems=stems_data,
                           processing_time=processing_time,
                           original_filename=original_filename,
                           model_name=model_name)


@app.route('/vocal-separator/download/<upload_id>/<stem_name>')
def vocal_separator_download(upload_id, stem_name):
    """Download a single stem file."""
    safe_stems = ['vocals', 'drums', 'bass', 'other']
    if stem_name not in safe_stems:
        return 'Invalid stem', 400
    path = os.path.join(sys_path, 'static', 'stems', upload_id, f'{stem_name}.wav')
    if os.path.exists(path):
        return send_file(path, as_attachment=True, download_name=f'{stem_name}.wav')
    return 'File not found', 404


@app.route('/vocal-separator/download-all/<upload_id>')
def vocal_separator_download_all(upload_id):
    """Download all stems as a ZIP file."""
    import zipfile, io
    stems_dir = os.path.join(sys_path, 'static', 'stems', upload_id)
    if not os.path.exists(stems_dir):
        return 'Not found', 404

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for stem in ['vocals', 'drums', 'bass', 'other', 'instrumental']:
            p = os.path.join(stems_dir, f'{stem}.wav')
            if os.path.exists(p):
                zf.write(p, arcname=f'{stem}.wav')
    zip_buf.seek(0)
    return send_file(zip_buf, mimetype='application/zip',
                     as_attachment=True, download_name=f'stems_{upload_id}.zip')


@app.route('/vocal-separator/mix/<upload_id>')
def vocal_separator_mix(upload_id):
    """
    Mix selected stems together server-side.
    Query params: stems=vocals,drums,bass or stems=all
    """
    stems_param = request.args.get('stems', 'all')
    if stems_param == 'all':
        selected = ['vocals', 'drums', 'bass', 'other']
    else:
        selected = [s.strip() for s in stems_param.split(',')]

    safe_stems = {'vocals', 'drums', 'bass', 'other'}
    selected = [s for s in selected if s in safe_stems]

    if not selected:
        return 'No valid stems selected', 400

    stems_dir = os.path.join(sys_path, 'static', 'stems', upload_id)
    if not os.path.exists(stems_dir):
        return 'Stems not found', 404

    import torch, torchaudio, io

    def load_stem(name):
        p = os.path.join(stems_dir, f'{name}.wav')
        if os.path.exists(p):
            w, sr = torchaudio.load(p)
            return w, sr
        return None, None

    # Load all selected stems
    loaded = {}
    sr = 44100
    max_len = 0
    max_ch = 0

    for s in selected:
        w, _sr = load_stem(s)
        if w is not None:
            loaded[s] = w
            sr = _sr
            max_len = max(max_len, w.shape[1])
            max_ch = max(max_ch, w.shape[0])

    if not loaded:
        return 'No stems found', 404

    def pad_channels(t, ch):
        if t.shape[0] == ch:
            return t
        if t.shape[0] == 1 and ch > 1:
            return t.expand(ch, -1)
        return t[:ch]

    # Normalize mix: divide by sqrt(number of stems) to prevent clipping
    norm_factor = (len(loaded) ** 0.5) * 1.0

    mixed = torch.zeros(max_ch, max_len)
    for s, w in loaded.items():
        w = pad_channels(w, max_ch)
        if w.shape[1] < max_len:
            w = torch.nn.functional.pad(w, (0, max_len - w.shape[1]))
        mixed += w

    mixed = (mixed / norm_factor).clamp(-1.0, 1.0)

    buf = io.BytesIO()
    torchaudio.save(buf, mixed, sr, format='wav')
    buf.seek(0)
    return send_file(buf, mimetype='audio/wav',
                     as_attachment=True,
                     download_name=f'mix_{"_".join(selected)}.wav')


# ══════════════════════════════════════════════════════════════════════════════
# SEEDANCE VIDEO GENERATION (MuAPI Integration)
# ══════════════════════════════════════════════════════════════════════════════

SEEDANCE_MODELS = {
    'seedance-t2v-720p': 'Seedance T2V 720P (HD)',
    'seedance-t2v-1080p': 'Seedance T2V 1080P (Full HD)',
    'seedance-i2v-720p': 'Seedance I2V 720P (Image to Video)',
    'seedance-i2v-1080p': 'Seedance I2V 1080P',
}

MUAPI_URL = os.environ.get('MUAPI_URL', 'http://127.0.0.1:5000')
MUAPI_API_KEY = None

# Load MuAPI credentials
_muapi_creds_file = os.path.join(os.path.dirname(__file__), '..', 'credentials', 'muapi.json')
if os.path.exists(_muapi_creds_file):
    try:
        with open(_muapi_creds_file) as f:
            _muapi_creds = json.load(f)
            MUAPI_API_KEY = _muapi_creds.get('api_key')
    except Exception:
        pass

_job_store = {}  # job_id -> job data (in-memory for simplicity)

def _muapi_request(endpoint, method='GET', json_data=None, timeout=10):
    """Make a request to the MuAPI local server."""
    import urllib.request, urllib.parse
    url = f"{MUAPI_URL}/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    if MUAPI_API_KEY:
        headers['Authorization'] = f"Bearer {MUAPI_API_KEY}"
    
    body = json.dumps(json_data).encode() if json_data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode()), resp.status
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode()), e.code
        except:
            return {'error': e.reason}, e.code
    except Exception as e:
        return {'error': str(e)}, 500

def _check_muapi_online():
    """Check if MuAPI server is reachable."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{MUAPI_URL}/health", method='GET')
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        pass
    # Try generic endpoint
    try:
        import urllib.request
        req = urllib.request.Request(f"{MUAPI_URL}/", method='GET')
        with urllib.request.urlopen(req, timeout=3) as resp:
            return True
    except Exception:
        return False

@app.route('/seedance', methods=['GET', 'POST'])
def seedance():
    """Seedance video generation page."""
    muapi_online = _check_muapi_online()
    return render_template('seedance.html',
                           models=SEEDANCE_MODELS,
                           muapi_online=muapi_online,
                           page='seedance')

@app.route('/seedance/generate', methods=['POST'])
def seedance_generate():
    """Submit a video generation job to MuAPI."""
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    model = data.get('model', 'seedance-t2v-720p')
    aspect_ratio = data.get('aspect_ratio', '9:16')
    duration = data.get('duration', '10s')
    negative_prompt = data.get('negative_prompt', '')
    seed = data.get('seed')
    steps = data.get('steps')

    # Map model names to MuAPI format
    muapi_model = model

    payload = {
        'model': muapi_model,
        'prompt': prompt,
        'aspect_ratio': aspect_ratio,
        'duration': duration,
    }
    if negative_prompt:
        payload['negative_prompt'] = negative_prompt
    if seed is not None:
        payload['seed'] = seed
    if steps is not None:
        payload['steps'] = steps

    result, status = _muapi_request('generate', method='POST', json_data=payload, timeout=30)

    if status == 200 and result.get('job_id'):
        job_id = result['job_id']
        _job_store[job_id] = {
            'job_id': job_id,
            'prompt': prompt,
            'model': model,
            'aspect_ratio': aspect_ratio,
            'duration': duration,
            'status': 'pending',
            'progress': 0,
            'result': result,
        }
        return jsonify({'job_id': job_id, **result})
    else:
        return jsonify({'error': result.get('error', 'Generation failed')}), status or 500

@app.route('/seedance/status/<job_id>', methods=['GET'])
def seedance_status(job_id):
    """Get the status of a generation job."""
    # Check in-memory store first
    if job_id in _job_store:
        job = _job_store[job_id]
        # Poll MuAPI for actual status
        result, status = _muapi_request(f'jobs/{job_id}', method='GET', timeout=10)
        if status == 200:
            job['status'] = result.get('status', job['status'])
            job['progress'] = result.get('progress', job.get('progress', 0))
            if result.get('status') in ('done', 'completed', 'succeeded'):
                job['status'] = 'done'
                job['progress'] = 100
            elif result.get('status') == 'failed':
                job['status'] = 'error'
            return jsonify(job)
        return jsonify(job)
    
    # Poll MuAPI directly
    result, status = _muapi_request(f'jobs/{job_id}', method='GET', timeout=10)
    if status == 200:
        return jsonify(result)
    return jsonify({'error': 'Job not found', 'status': 'error'}), 404

@app.route('/seedance/download/<job_id>', methods=['GET'])
def seedance_download(job_id):
    """Download the generated video."""
    result, status = _muapi_request(f'jobs/{job_id}/download', method='GET', timeout=60)
    if status == 200 and result.get('url'):
        # Redirect to the video URL or download it
        video_url = result['url']
        try:
            import urllib.request
            req = urllib.request.Request(video_url)
            with urllib.request.urlopen(req, timeout=60) as resp:
                video_data = resp.read()
            return Response(video_data, mimetype='video/mp4',
                           headers={'Content-Disposition': f'attachment; filename=seedance_{job_id}.mp4'})
        except Exception as e:
            return jsonify({'error': f'Download failed: {e}'}), 500
    elif status == 200 and result.get('video_path'):
        path = result['video_path']
        if os.path.exists(path):
            return send_file(path, as_attachment=True, download_name=f'seedance_{job_id}.mp4')
    return jsonify({'error': 'Video not ready or not found'}), 404

@app.route('/seedance/preview/<job_id>', methods=['GET'])
def seedance_preview(job_id):
    """Stream preview of the generated video."""
    result, status = _muapi_request(f'jobs/{job_id}/download', method='GET', timeout=30)
    if status == 200 and result.get('url'):
        try:
            import urllib.request
            req = urllib.request.Request(result['url'])
            with urllib.request.urlopen(req, timeout=60) as resp:
                video_data = resp.read()
            return Response(video_data, mimetype='video/mp4')
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif status == 200 and result.get('video_path'):
        path = result['video_path']
        if os.path.exists(path):
            return send_file(path, mimetype='video/mp4')
    return 'Video not ready', 404


# ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ─── Cloud Phones Module ───────────────────────────────────────────────────────
from cloud_phones import register_cloud_phone_routes
register_cloud_phone_routes(app)

# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════╗
║            MARKETING MANAGER - MYSTIK SINGH              ║
║              AIOStream Clone v2.0                         ║
║                                                              ║
║  ⚡ Open http://127.0.0.1:5001 in your browser          ║
║                                                              ║
║  Modules:                                                   ║
║  📊 Dashboard  💿 Albums  🎤 Tracks  👥 Curators           ║
║  📨 Submissions  ✉️ Email  🔒 Streaming Accounts         ║
║  🌐 Proxies  📱 Emulators  ⏰ Scheduler  📈 Statistics    ║
║  🎵 TikTok  🤖 AI Playlists  🔐 Account Creator          ║
║                                                              ║
║  Press Ctrl+C to stop                                      ║
╚══════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5001, debug=True)
