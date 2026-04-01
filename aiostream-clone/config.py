# Marketing Manager - Media Storage Configuration
# All content saves to external SSD for Mystik Singh

import os

# Higgsfield AI API Credentials
HIGGSFIELD_API_KEY_ID = "b8f2acb8-deb4-4095-b37a-f24627b45f2a"
HIGGSFIELD_API_KEY_SECRET = "44775ce5c419d544b85ff653538763171fca28aac63393638a899d52a2dfab37"

# External SSD Mount
EXTERNAL_SSD = '/mnt/media-drive/MystikSingh'

# Main directories
ALBUMS_DIR = os.path.join(EXTERNAL_SSD, 'Albums')
GENERAL_DIR = os.path.join(EXTERNAL_SSD, 'General')
SOCIAL_DIR = os.path.join(EXTERNAL_SSD, 'SocialMedia')
CONTENT_DIR = os.path.join(EXTERNAL_SSD, 'Content')

# Per-album subdirectories
ALBUM_STRUCTURE = {
    'Memento Mori Vol. 1': {
        'root': os.path.join(ALBUMS_DIR, 'Vol1'),
        'raw': os.path.join(ALBUMS_DIR, 'Vol1', 'Raw'),
        'edits': os.path.join(ALBUMS_DIR, 'Vol1', 'Edits'),
        'tiktoks': os.path.join(ALBUMS_DIR, 'Vol1', 'TikToks'),
        'reels': os.path.join(ALBUMS_DIR, 'Vol1', 'Reels'),
        'shorts': os.path.join(ALBUMS_DIR, 'Vol1', 'Shorts'),
        'youtube': os.path.join(ALBUMS_DIR, 'Vol1', 'YouTube'),
        'exports': os.path.join(ALBUMS_DIR, 'Vol1', 'Exports'),
    },
    'Memento Mori Vol. 2': {
        'root': os.path.join(ALBUMS_DIR, 'Vol2'),
        'raw': os.path.join(ALBUMS_DIR, 'Vol2', 'Raw'),
        'edits': os.path.join(ALBUMS_DIR, 'Vol2', 'Edits'),
        'tiktoks': os.path.join(ALBUMS_DIR, 'Vol2', 'TikToks'),
        'reels': os.path.join(ALBUMS_DIR, 'Vol2', 'Reels'),
        'shorts': os.path.join(ALBUMS_DIR, 'Vol2', 'Shorts'),
        'youtube': os.path.join(ALBUMS_DIR, 'Vol2', 'YouTube'),
        'exports': os.path.join(ALBUMS_DIR, 'Vol2', 'Exports'),
    },
    'Memento Mori Vol. 3': {
        'root': os.path.join(ALBUMS_DIR, 'Vol3'),
        'raw': os.path.join(ALBUMS_DIR, 'Vol3', 'Raw'),
        'edits': os.path.join(ALBUMS_DIR, 'Vol3', 'Edits'),
        'tiktoks': os.path.join(ALBUMS_DIR, 'Vol3', 'TikToks'),
        'reels': os.path.join(ALBUMS_DIR, 'Vol3', 'Reels'),
        'shorts': os.path.join(ALBUMS_DIR, 'Vol3', 'Shorts'),
        'youtube': os.path.join(ALBUMS_DIR, 'Vol3', 'YouTube'),
        'exports': os.path.join(ALBUMS_DIR, 'Vol3', 'Exports'),
    },
}

# Social media platform folders
SOCIAL_STRUCTURE = {
    'instagram': os.path.join(SOCIAL_DIR, 'Instagram'),
    'tiktok': os.path.join(SOCIAL_DIR, 'TikTok'),
    'youtube': os.path.join(SOCIAL_DIR, 'YouTube'),
    'facebook': os.path.join(SOCIAL_DIR, 'Facebook'),
}

# Format subfolders
FORMAT_FOLDERS = ['Vertical9x16', 'Horizontal16x9', 'Square1x1']

# Ensure all directories exist
def init_storage():
    """Create all storage directories on startup."""
    dirs_to_create = [
        EXTERNAL_SSD,
        ALBUMS_DIR,
        GENERAL_DIR,
        SOCIAL_DIR,
        CONTENT_DIR,
    ]
    for album_data in ALBUM_STRUCTURE.values():
        dirs_to_create.extend(album_data.values())
    dirs_to_create.extend(SOCIAL_STRUCTURE.values())
    
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)

# Get path for specific content type
def get_save_path(album: str, content_type: str, platform: str = None) -> str:
    """Get the appropriate save path for content."""
    if album in ALBUM_STRUCTURE:
        base = ALBUM_STRUCTURE[album]
        if content_type in base:
            return base[content_type]
        return base.get('root', ALBUMS_DIR)
    return GENERAL_DIR
