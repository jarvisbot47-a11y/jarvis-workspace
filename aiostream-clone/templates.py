"""
Pre-built email pitch templates for playlist curators.
"""

PITCH_TEMPLATES = {
    "standard": {
        "name": "Standard Playlist Pitch",
        "subject": "New Track: {track_title} by {artist_name}",
        "body": """Hi {curator_name},

I hope this message finds you well. My name is {artist_name}, an independent hip hop artist from {location}.

I recently released a new track called "{track_title}" and I think it would be a great fit for your {playlist_name} playlist.

The track features {unique_characteristic} and explores {theme}. I've attached a Spotify/Apple Music link below for your review:

{track_link}

If you have any questions or need additional material (high-quality audio file, press kit, etc.), please don't hesitate to ask.

Thanks so much for your time and for the work you do supporting independent artists!

Best regards,
{artist_name}
{website}
{social_link}"""
    },

    "short": {
        "name": "Quick Pitch (Short)",
        "subject": "{track_title} – {artist_name} (Submission for {playlist_name})",
        "body": """Hey {curator_name},

{artist_name} here – just dropped "{track_title}" and thought it might vibe with your {playlist_name} playlist.

{vibe_description}

Listen: {track_link}

No pressure if it's not the right fit. Thanks for listening!

{artist_name}"""
    },

    "conscious": {
        "name": "Conscious/Lyric-Heavy Pitch",
        "subject": "Lyrically-Driven Hip Hop: {track_title} for {playlist_name}",
        "body": """Hi {curator_name},

I wanted to reach out about my latest release, "{track_title}" – a lyrically-driven hip hop track that I believe aligns with the thoughtful curation of {playlist_name}.

The song touches on {theme}, with bars that dig into {subject_matter}. Production-wise, it's built around {production_description}, giving it a {mood} feel that I think your listeners would appreciate.

I've been building a loyal underground following with releases like {album_reference}, and I'm always looking to connect with curators who care about substance over hype.

Listen: {track_link}

Would love to hear your thoughts. Happy to provide any additional materials!

Thanks for your time,
{artist_name}
{website}"""
    },

    "aggressive": {
        "name": "Hard-Hitting / Trap Pitch",
        "subject": "{track_title} – Heavy 808s & Hard Bars for {playlist_name}",
        "body": """Yo {curator_name},

{artist_name} coming at you with "{track_title}" – this one's got {bass_description} and {drum_description} for days.

This track is for listeners who want {listener_vibe}. Perfect for your {playlist_name} playlist if you're looking to add {energy_level} energy.

Hit this link to stream: {track_link}

Let me know if you need the WAV file or any other assets.

{artist_name}
{social_link}"""
    },

    "follow_up": {
        "name": "Follow Up (1 Week After Initial)",
        "subject": "Re: {track_title} – Still Interested? ({artist_name})",
        "body": """Hi {curator_name},

Just bumping my earlier message about "{track_title}" – no pressure at all if it's not the right fit!

I wanted to mention that since releasing it, the track has organically hit {stream_count} streams and is resonating with fans of {comparable_artists}.

If {playlist_name} isn't the right home for it, do you know any other curators I should reach out to?

Either way, thanks for your time and keep doing what you do – playlists like yours are how underground artists get discovered.

Best,
{artist_name}"""
    },

    "second_followup": {
        "name": "Second Follow Up",
        "subject": "Final Check-In: {track_title} for {playlist_name}",
        "body": """Hey {curator_name},

One last check on my submission for {playlist_name}. I know you're probably flooded with pitches, so I totally understand if this one slipped through.

I've stopped sending submissions to artists and playlists that aren't responding – but since I genuinely thought {track_title} was a strong fit for your curation, I wanted to give it one more shot.

If you're not accepting submissions right now or if this isn't the right vibe, just let me know and I'll focus my energy elsewhere. Truly no hard feelings.

Thanks for everything you do for the indie scene.

{artist_name}"""
    },

    "thank_you_accepted": {
        "name": "Thank You (After Playlist Acceptance)",
        "subject": "Thank You + More Where That Came From ({artist_name})",
        "body": """Hi {curator_name},

I just saw that "{track_title}" was added to {playlist_name} – honestly made my day!

Thank you so much for taking a chance on an independent artist. It really does mean the world and helps us get in front of listeners we could never reach alone.

If you ever want to check out my other work ({album_reference} is a recent project), or if you need anything else from me, I'm just an email away.

I'll be sharing {playlist_name} with my followers as well – let's help each other grow.

Grateful,
{artist_name}

{website}"""
    },

    "release_announcement": {
        "name": "New Release Announcement",
        "subject": "New Release: {album_title} by {artist_name} ({release_date})",
        "body": """Hi {curator_name},

{artist_name} here – wanted to personally reach out before my new project "{album_title}" drops on {release_date}.

This is my {volume_number} installment in the "Memento Mori" series, and it's my most ambitious work yet. {album_description}

I'm specifically looking for playlists that feature {genre_tags}, and {playlist_name} came to mind immediately.

If you're interested in previewing the album before release or adding any tracks, I'd be happy to send a private link. I can also provide high-res artwork, bios, and any materials you need.

Release date: {release_date}
Genre: {genre_tags}
Sound: {sound_description}

Let me know if you'd like early access!

Thanks for your time,
{artist_name}
{website}"""
    }
}


def fill_template(template_key: str, **kwargs) -> tuple:
    """
    Fill a template with provided values.
    Returns (subject, body) tuple.
    """
    if template_key not in PITCH_TEMPLATES:
        return ("", "")

    t = PITCH_TEMPLATES[template_key]
    try:
        subject = t['subject'].format(**kwargs)
        body = t['body'].format(**kwargs)
        return (subject, body)
    except KeyError as e:
        # Return template with unfilled placeholders
        return (t['subject'], t['body'])


def get_all_template_names():
    return {k: v['name'] for k, v in PITCH_TEMPLATES.items()}
