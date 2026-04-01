"""
Spotify Real-Time Stats Module
Uses Spotify's private Creator API for live artist statistics.
Based on reverse-engineered endpoints from Spotify for Artists.
"""

import os
import time
import requests
import logging
from datetime import datetime, timedelta
from flask import Blueprint, session, redirect, url_for, jsonify, render_template_string, request, current_app

logger = logging.getLogger(__name__)

spotify_bp = Blueprint('spotify', __name__, url_prefix='/spotify')

# ─── Config ───────────────────────────────────────────────
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', 'YOUR_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI', 'http://localhost:5001/spotify/callback')

# Spotify private API endpoints (not publicly documented)
SPOTIFY_API_BASE = 'https://spclient.wg.spotify.com'
CREATOR_API_BASE = 'https://spclient.wg.spotify.com/creator-wordpress-api'
ARTIST_API_BASE = 'https://spclient.wg.spotify.com/artist-audio-features'

# OAuth scopes needed
SPOTIFY_SCOPES = [
    'user-read-private',
    'user-read-email',
    'streaming',
    'playlist-read-private',
    'user-library-read',
    'user-top-read',
]

# ─── OAuth ────────────────────────────────────────────────
def get_auth_url():
    """Generate Spotify OAuth URL."""
    import base64, urllib.parse
    code_verifier = base64.urlsafe_b64encode(os.urandom(96)).decode().rstrip('=')
    # Simple state token
    state = base64.urlsafe_b64encode(os.urandom(16)).decode().rstrip('=')
    session['oauth_state'] = state
    session['code_verifier'] = code_verifier
    
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': ' '.join(SPOTIFY_SCOPES),
        'state': state,
        'show_dialog': 'true',
    }
    return 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode(params)


def exchange_code_for_token(code, code_verifier):
    """Exchange authorization code for access token."""
    resp = requests.post(
        'https://accounts.spotify.com/api/token',
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
            'code_verifier': code_verifier,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    if resp.status_code != 200:
        logger.error(f"Token exchange failed: {resp.text}")
        return None
    return resp.json()


def refresh_access_token(refresh_token):
    """Refresh an expired access token."""
    resp = requests.post(
        'https://accounts.spotify.com/api/token',
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET,
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    if resp.status_code != 200:
        logger.error(f"Token refresh failed: {resp.text}")
        return None
    return resp.json()


def get_spotify_headers(token):
    """Build headers for Spotify API calls."""
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'app-platform': 'WebPlayer',
        'spotify-app': 'desktop-app',
        'client-id': SPOTIFY_CLIENT_ID,
        'origin': 'https://open.spotify.com',
        'Referer': 'https://open.spotify.com/',
    }


# ─── Private Spotify API Calls ────────────────────────────
def get_creator_audience(token):
    """
    Get real-time audience demographics from Spotify's private creator API.
    Endpoint: creator-audience (WordPress-based creator stats).
    """
    # Try the creator audience endpoint
    endpoints_to_try = [
        (f'{CREATOR_API_BASE}/creator/creator-audience', {}),
        (f'{SPOTIFY_API_BASE}/creator-wordpress-api/creator/creator-audience', {}),
    ]
    
    headers = get_spotify_headers(token)
    headers['x-creator-audio-features'] = 'true'
    
    for url, params in endpoints_to_try:
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Creator audience endpoint {url} failed: {e}")
            continue
    return {}


def get_artist_audio_features(token, artist_id):
    """
    Get real-time artist stats from Spotify's private artist-audio-features API.
    This is the core endpoint powering Spotify for Artists dashboard.
    """
    headers = get_spotify_headers(token)
    headers['x-creator-audio-features'] = 'true'
    headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    
    # Try v1 and v2 of the API
    endpoints = [
        f'{ARTIST_API_BASE}/query/v1',
        f'{ARTIST_API_BASE}/query/v2',
        f'{SPOTIFY_API_BASE}/artist-audio-features/query/v1',
    ]
    
    params = {
        'artistIds': artist_id,
        'time_range': 'last_28_days',
        'enable_total': 'true',
    }
    
    for url in endpoints:
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Artist API success: {url} → {str(data)[:200]}")
                return data
            else:
                logger.warning(f"Artist API {url} → {resp.status_code}")
        except Exception as e:
            logger.warning(f"Endpoint {url} error: {e}")
            continue
    
    return {}


def get_realtime_listeners(token, artist_id):
    """
    Get real-time active listeners count.
    This is the 'now playing' equivalent for the artist's audience.
    """
    headers = get_spotify_headers(token)
    headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    
    url = f'{SPOTIFY_API_BASE}/creator-wordpress-api/creator/now-playing'
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"Now playing endpoint failed: {e}")
    
    return {}


def get_stream_stats(token, artist_id, time_range='last_28_days'):
    """
    Get comprehensive stream statistics.
    """
    headers = get_spotify_headers(token)
    headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    headers['x-creator-audio-features'] = 'true'
    
    # Primary streams endpoint
    url = f'{SPOTIFY_API_BASE}/creator-wordpress-api/creator/statistics/v2'
    params = {
        'artist_id': artist_id,
        'time_range': time_range,
        'enable_total': 'true',
        'enable_subscriber': 'true',
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"Stream stats endpoint failed: {e}")
    
    # Fallback
    url2 = f'{SPOTIFY_API_BASE}/creator-wordpress-api/creator/stream-stats'
    try:
        resp = requests.get(url2, headers=headers, params={'artist_id': artist_id}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"Stream stats fallback failed: {e}")
    
    return {}


def get_spotify_user_profile(token):
    """Get authenticated user's Spotify profile."""
    resp = requests.get(
        'https://api.spotify.com/v1/me',
        headers=get_spotify_headers(token),
        timeout=10
    )
    if resp.status_code == 200:
        return resp.json()
    return {}


def get_top_tracks(token, artist_id, limit=20):
    """Get artist's top tracks from public API."""
    resp = requests.get(
        f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks',
        headers=get_spotify_headers(token),
        params={'market': 'US'},
        timeout=10
    )
    if resp.status_code == 200:
        return resp.json().get('tracks', [])
    return []


def get_artist_followers(token, artist_id):
    """Get follower count from public API."""
    resp = requests.get(
        f'https://api.spotify.com/v1/artists/{artist_id}',
        headers=get_spotify_headers(token),
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        return {
            'total': data.get('followers', {}).get('total', 0),
            'href': data.get('followers', {}).get('href', ''),
        }
    return {'total': 0}


# ─── Combined Stats Aggregator ─────────────────────────────
def get_all_stats(token, artist_id):
    """
    Aggregate all available stats into a single response.
    Tries multiple endpoints and combines results.
    """
    stats = {
        'timestamp': datetime.now().isoformat(),
        'artist_id': artist_id,
        'source': 'spotify-private-api',
    }
    
    # Public API data (always works)
    profile = get_spotify_user_profile(token)
    if profile:
        stats['user'] = {
            'display_name': profile.get('display_name', ''),
            'id': profile.get('id', ''),
            'email': profile.get('email', ''),
            'country': profile.get('country', ''),
            'product': profile.get('product', ''),
        }
    
    # Artist public data
    artist_data = requests.get(
        f'https://api.spotify.com/v1/artists/{artist_id}',
        headers=get_spotify_headers(token),
        timeout=10
    ).json() if token else {}
    
    stats['artist'] = {
        'name': artist_data.get('name', ''),
        'followers': artist_data.get('followers', {}).get('total', 0),
        'genres': artist_data.get('genres', []),
        'popularity': artist_data.get('popularity', 0),
        'uri': artist_data.get('uri', ''),
    }
    
    # Try private API for real-time data
    audio_features = get_artist_audio_features(token, artist_id)
    if audio_features:
        stats['audio_features'] = audio_features
    
    stream_stats = get_stream_stats(token, artist_id)
    if stream_stats:
        stats['stream_stats'] = stream_stats
    
    creator = get_creator_audience(token)
    if creator:
        stats['audience'] = creator
    
    # Top tracks (public API)
    tracks = get_top_tracks(token, artist_id)
    if tracks:
        stats['top_tracks'] = [
            {
                'name': t['name'],
                'id': t['id'],
                'uri': t['uri'],
                'duration_ms': t['duration_ms'],
                'popularity': t.get('popularity', 0),
                'preview_url': t.get('preview_url'),
                'external_urls': t.get('external_urls', {}),
                'album': {
                    'name': t.get('album', {}).get('name', ''),
                    'images': t.get('album', {}).get('images', []),
                },
            }
            for t in tracks[:20]
        ]
    
    return stats


# ─── Routes ──────────────────────────────────────────────
@spotify_bp.route('/login')
def login():
    """Redirect to Spotify OAuth."""
    return redirect(get_auth_url())


@spotify_bp.route('/callback')
def callback():
    """Handle Spotify OAuth callback."""
    error = request.args.get('error')
    if error:
        return jsonify({'error': error}), 400
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Verify state
    if state != session.get('oauth_state'):
        return jsonify({'error': 'State mismatch'}), 400
    
    code_verifier = session.get('code_verifier', '')
    token_data = exchange_code_for_token(code, code_verifier)
    
    if not token_data:
        return jsonify({'error': 'Token exchange failed'}), 500
    
    # Store tokens in session
    session['spotify_access_token'] = token_data.get('access_token')
    session['spotify_refresh_token'] = token_data.get('refresh_token')
    session['spotify_expires_at'] = time.time() + token_data.get('expires_in', 3600)
    session['spotify_connected'] = True
    
    return redirect(url_for('spotify.dashboard'))


@spotify_bp.route('/logout')
def logout():
    """Clear Spotify session."""
    session.pop('spotify_access_token', None)
    session.pop('spotify_refresh_token', None)
    session.pop('spotify_expires_at', None)
    session.pop('spotify_connected', None)
    return redirect(url_for('spotify.login'))


def ensure_valid_token():
    """Refresh token if expired."""
    if not session.get('spotify_connected'):
        return None
    
    if time.time() > session.get('spotify_expires_at', 0) - 60:
        token_data = refresh_access_token(session.get('spotify_refresh_token', ''))
        if token_data:
            session['spotify_access_token'] = token_data.get('access_token')
            session['spotify_refresh_token'] = token_data.get('refresh_token', session.get('spotify_refresh_token'))
            session['spotify_expires_at'] = time.time() + token_data.get('expires_in', 3600)
    
    return session.get('spotify_access_token')


@spotify_bp.route('/api/stats/<artist_id>')
def api_stats(artist_id):
    """Return all stats for an artist as JSON."""
    token = ensure_valid_token()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    stats = get_all_stats(token, artist_id)
    return jsonify(stats)


@spotify_bp.route('/api/refresh/<artist_id>')
def api_refresh(artist_id):
    """Force-refresh stats."""
    token = ensure_valid_token()
    if not token:
        return jsonify({'error': 'Not authenticated'}), 401
    
    stats = get_all_stats(token, artist_id)
    return jsonify(stats)


@spotify_bp.route('/dashboard')
def dashboard():
    """Live Spotify stats dashboard."""
    import os
    
    # Check if Spotify API is configured
    client_id = os.environ.get('SPOTIFY_CLIENT_ID', '')
    if not client_id or client_id == 'YOUR_CLIENT_ID':
        return render_template_string('''
        <!DOCTYPE html>
        <html><head><title>Spotify Setup</title></head>
        <body style="font-family:-apple-system,sans-serif;background:#0a0a0f;color:#fff;padding:40px;text-align:center;">
        <h2 style="color:#1DB954;">Spotify API Not Configured</h2>
        <p style="color:#a0a0b0;line-height:2;">
            Set environment variables:<br>
            <code style="background:#111;padding:4px 10px;border-radius:6px;">SPOTIFY_CLIENT_ID</code><br>
            <code style="background:#111;padding:4px 10px;border-radius:6px;">SPOTIFY_CLIENT_SECRET</code><br>
            <code style="background:#111;padding:4px 10px;border-radius:6px;">SPOTIFY_REDIRECT_URI=http://localhost:5001/spotify/callback</code>
        </p>
        <p style="margin-top:20px;font-size:13px;color:#606070;">
            1. Create app at <a href="https://developer.spotify.com/dashboard" style="color:#1DB954;">developer.spotify.com</a><br>
            2. Add redirect URI: <code>http://localhost:5001/spotify/callback</code><br>
            3. Restart app with env vars set
        </p>
        </body></html>
        ''', setup_needed=True)
    
    token = ensure_valid_token()
    if not token:
        return redirect(url_for('spotify.login'))
    
    artist_id = session.get('spotify_artist_id', '')
    if not artist_id:
        profile = get_spotify_user_profile(token)
        artist_id = profile.get('id', '')
        session['spotify_artist_id'] = artist_id
    
    stats = get_all_stats(token, artist_id) if artist_id else {}
    
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'spotify_dashboard.html')
    if os.path.exists(template_path):
        with open(template_path) as f:
            template = f.read()
        from flask import render_template_string
        return render_template_string(template, stats=stats, artist_id=artist_id, setup_needed=False)
    
    return jsonify(stats)


def register_routes(app):
    """Register Spotify blueprint with the Flask app."""
    app.register_blueprint(spotify_bp)
    
    @app.route('/spotify-setup')
    def spotify_setup():
        """Setup page for configuring Spotify OAuth."""
        return '''
        <html><head><title>Spotify Setup</title></head>
        <body style="font-family:sans-serif;background:#121212;color:#fff;padding:40px;">
        <h2 style="color:#1DB954;">Spotify API Setup</h2>
        <p>To enable live Spotify stats, you need a Spotify Developer App.</p>
        <ol style="line-height:2;">
            <li>Go to <a href="https://developer.spotify.com/dashboard" style="color:#1DB954;">developer.spotify.com/dashboard</a></li>
            <li>Create an app (choose "Non-Commercial" or "Commercial" as appropriate)</li>
            <li>Copy your <b>Client ID</b> and <b>Client Secret</b></li>
            <li>Add <code style="background:#222;padding:2px 6px;border-radius:4px;">http://localhost:5001/spotify/callback</code> as a Redirect URI in your Spotify app settings</li>
            <li>Set environment variables:
                <pre style="background:#222;padding:16px;border-radius:8px;margin:10px 0;">export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"
export SPOTIFY_REDIRECT_URI="http://localhost:5001/spotify/callback"</pre>
            </li>
            <li>Restart the app and visit <a href="/spotify/login" style="color:#1DB954;">/spotify/login</a></li>
        </ol>
        <p><b>Note:</b> The live/private API endpoints require a Spotify for Artists account and may require additional OAuth scopes. Some endpoints are undocumented and may change.</p>
        </body></html>
        '''
