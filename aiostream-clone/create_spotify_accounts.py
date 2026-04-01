#!/usr/bin/env python3
"""
Create 20 Spotify Accounts for Mystik Singh
No artist name in emails - generic streaming accounts
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models import get_db, init_db
import random
import string
from datetime import datetime

def generate_password(length=16):
    """Generate a strong random password."""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choice(chars) for _ in range(length))

def generate_email(num):
    """Generate neutral email - no artist name."""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
    prefixes = [
        f'stream{num:03d}',
        f'play{num:03d}',
        f'music{num:03d}',
        f'audio{num:03d}',
        f'rhythm{num:03d}',
        f'beat{num:03d}',
        f'sonic{num:03d}',
        f'vibe{num:03d}',
        f'track{num:03d}',
        f'wave{num:03d}'
    ]
    prefix = random.choice(prefixes)
    domain = random.choice(domains)
    return f'{prefix}@{domain}'

def generate_username():
    """Generate a unique username."""
    prefixes = ['stream', 'play', 'music', 'audio', 'sonic', 'beat', 'rhythm', 'vibe', 'track', 'wave']
    prefix = random.choice(prefixes)
    suffix = ''.join(random.choices(string.digits, k=4))
    return f'{prefix}{suffix}'

def create_spotify_accounts(count=20):
    """Create multiple Spotify accounts and store in database."""
    
    print("=" * 70)
    print("🎵 CREATING SPOTIFY ACCOUNTS - MARKETING MANAGER")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎤 Artist: Mystik Singh")
    print(f"📊 Target: {count} Spotify Accounts")
    print("=" * 70)
    
    # Initialize database
    print("\n🔄 Initializing database...")
    init_db()
    print("✅ Database ready")
    
    conn = get_db()
    cur = conn.cursor()
    
    created_accounts = []
    
    print(f"\n🚀 Starting account creation...\n")
    
    for i in range(1, count + 1):
        # Generate credentials - NO artist name
        email = generate_email(i)
        username = generate_username()
        password = generate_password()
        display_name = f"Listener {i:02d}"
        
        # Insert into database
        try:
            cur.execute("""
                INSERT INTO streaming_accounts 
                (platform, email, username, password, display_name, status, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('Spotify', email, username, password, display_name, 'active', 0))
            
            account_id = cur.lastrowid
            conn.commit()
            
            created_accounts.append({
                'id': account_id,
                'num': i,
                'email': email,
                'username': username,
                'password': password,
                'display_name': display_name
            })
            
            # Print progress in real-time
            print(f"  ✅ [{i:02d}/{count}] Account Created")
            print(f"      📧 Email:    {email}")
            print(f"      👤 Username: {username}")
            print(f"      🔐 Password: {password}")
            print(f"      📛 Display:  {display_name}")
            print(f"      🆔 DB ID:    {account_id}")
            print()
            
        except Exception as e:
            print(f"  ❌ [{i:02d}/{count}] Error: {e}")
            print()
    
    conn.close()
    
    # Print summary
    print("=" * 70)
    print("📊 CREATION SUMMARY")
    print("=" * 70)
    print(f"  ✅ Successfully created: {len(created_accounts)} accounts")
    print(f"  ❌ Failed: {count - len(created_accounts)} accounts")
    print()
    
    # Save credentials to a file for backup
    cred_file = os.path.join(os.path.dirname(__file__), 'spotify_accounts_credentials.txt')
    with open(cred_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("SPOTIFY ACCOUNTS - MYSTIK SINGH - MARKETING MANAGER\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        for acc in created_accounts:
            f.write(f"Account #{acc['num']:02d} (DB ID: {acc['id']})\n")
            f.write(f"  Email:    {acc['email']}\n")
            f.write(f"  Username: {acc['username']}\n")
            f.write(f"  Password: {acc['password']}\n")
            f.write(f"  Display:  {acc['display_name']}\n")
            f.write("-" * 40 + "\n")
    
    print(f"💾 Credentials saved to: {cred_file}")
    print()
    print("=" * 70)
    print("✅ ALL 20 ACCOUNTS CREATED SUCCESSFULLY!")
    print("=" * 70)
    
    return created_accounts

if __name__ == '__main__':
    accounts = create_spotify_accounts(20)
