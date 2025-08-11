# main.py (Debug HTML Version - Let's see what's actually happening)
import os
import threading
import time
import schedule
from flask import Flask, Response
from generate_blog_post import generate_mlb_blog_post
from audit_blog_post import audit_blog_post
from generate_image import generate_team_logos_for_matchup
from mlb_data_fetcher import MLBDataFetcher
import uuid
import json
from datetime import datetime
import re

app = Flask(__name__)

# Internal linking phrase-to-URL mapping
INTERLINK_MAP = {
    "betting splits": "https://www.thebettinginsider.com/stats-about",
    "public money": "https://www.thebettinginsider.com/stats-about",
    "betting percentage": "https://www.thebettinginsider.com/stats-about",
    "sharp money": "https://www.thebettinginsider.com/stats-about",
    "betting trends": "https://www.thebettinginsider.com/stats-about",
    "stats dashboard": "https://www.thebettinginsider.com/stats-about",
    "pitcher arsenal data": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "pitch mix": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "arsenal-specific performance": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "batter vs pitch type stats": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "projected xBA": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "expected batting average": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "contact-adjusted xBA": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "xBA vs arsenal": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "strikeout percentage": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "K-rate": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "strikeout rate": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "whiff rate": "https://www.thebettinginsider.com/daily-mlb-game-stats",
    "swing and miss %": "https://www.thebettinginsider.com/daily-mlb-game-stats"
}

def auto_link_blog_content(blog_text, max_links=5):
    """Add internal links to blog content"""
    if not blog_text or max_links <= 0:
        return blog_text
    
    words = len(blog_text.split())
    dynamic_cap = min(max_links, max(2, words // 250))
    
    links_inserted = 0
    modified_text = blog_text
    
    sorted_phrases = sorted(INTERLINK_MAP.keys(), key=len, reverse=True)
    
    for phrase in sorted_phrases:
        if links_inserted >= dynamic_cap:
            break
            
        url = INTERLINK_MAP[phrase]
        pattern = r'(?<![A-Za-z0-9])' + re.escape(phrase) + r'(?![A-Za-z0-9])'
        
        match = re.search(pattern, modified_text, re.IGNORECASE)
        if match:
            matched_text = match.group()
            start_pos = match.start()
            
            preceding_text = modified_text[:start_pos]
            last_link_start = preceding_text.rfind('<a ')
            last_link_end = preceding_text.rfind('</a>')
            
            if last_link_start > last_link_end:
                continue
            
            link_html = f'<a href="{url}">{matched_text}</a>'
            modified_text = re.sub(pattern, link_html, modified_text, count=1, flags=re.IGNORECASE)
            links_inserted += 1
    
    return modified_text

def simple_text_to_html(blog_text):
    """SIMPLE text to HTML converter - let's see what happens"""
    if not blog_text:
        return "<p>No blog content</p>"
    
    print(f"🔧 DEBUG: Converting text to HTML...")
    print(f"🔧 DEBUG: Input starts with: {blog_text[:100]}")
    
    # Replace asterisk formatting with HTML bold
    html_text = re.sub(r'\*([^*]+)\*', r'<strong>\1</strong>', blog_text)
    
    # Convert line breaks to paragraphs
    lines = html_text.split('\n')
    html_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append('<br>')
            continue
            
        # Main titles with "MLB Betting Preview"
        if 'MLB Betting Preview' in line:
            html_lines.append(f'<h1>{line}</h1>')
        # Game Time
        elif 'Game Time:' in line:
            html_lines.append(f'<h2>{line}</h2>')
        # Numbered sections
        elif re.match(r'^\d+\.', line) or re.match(r'^###\s+\d+\.', line):
            html_lines.append(f'<h2>{line}</h2>')
        # Headers with ###
        elif line.startswith('###'):
            clean_line = line.replace('###', '').strip()
            html_lines.append(f'<h3>{clean_line}</h3>')
        # Headers with ####
        elif line.startswith('####'):
            clean_line = line.replace('####', '').strip()
            html_lines.append(f'<h4>{clean_line}</h4>')
        # Regular paragraphs
        else:
            html_lines.append(f'<p>{line}</p>')
    
    result = '\n'.join(html_lines)
    print(f"🔧 DEBUG: Output starts with: {result[:100]}")
    return result

def save_to_file(directory, filename, content):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'w', encoding='utf-8') as file:
        file.write(content)

def parse_game_time_for_sorting(time_str):
    if not time_str or time_str == 'TBD':
        return 9999
    
    try:
        if ',' in time_str:
            time_part = time_str.split(',')[1].strip()
        else:
            time_part = time_str.strip()
        
        if 'PM' in time_part:
            hour = int(time_part.split(':')[0])
            if hour != 12:
                hour += 12
            minute = int(time_part.split(':')[1].replace('PM', ''))
        else:
            hour = int(time_part.split(':')[0])
            if hour == 12:
                hour = 0
            minute = int(time_part.split(':')[1].replace('AM', ''))
        
        return hour * 100 + minute
    except Exception as e:
        print(f"⚠️ Error parsing time '{time_str}': {e}")
        return 9999

def generate_daily_blogs():
    """Generate all blogs for today"""
    print(f"🚀 Starting daily blog generation at {datetime.now()}")
    
    mlb_fetcher = MLBDataFetcher()
    blog_topics = mlb_fetcher.get_blog_topics_from_games()
    
    if not blog_topics:
        print("❌ No games available for blog generation")
        return
    
    blog_topics.sort(key=lambda x: parse_game_time_for_sorting(x['game_data'].get('game_time', 'TBD')))
    
    base_directory = "mlb_blog_posts"
    date_str = datetime.now().strftime("%Y-%m-%d")
    daily_directory = os.path.join(base_directory, date_str)
    
    if not os.path.exists(daily_directory):
        os.makedirs(daily_directory)
    
    print(f"🚀 Generating {len(blog_topics)} MLB blog posts for {date_str}")
    
    for i, blog_topic in enumerate(blog_topics, 1):
        topic = blog_topic['topic']
        keywords = blog_topic['keywords']
        game_data = blog_topic['game_data']
        
        print(f"\n📝 Processing game {i}/{len(blog_topics)}: {game_data['matchup']} at {game_data.get('game_time', 'TBD')}")
        
        time_prefix = f"{i:02d}_"
        safe_matchup = game_data['matchup'].replace(' @ ', '_vs_').replace(' ', '_')
        random_hash = uuid.uuid4().hex[:8]
        game_directory = os.path.join(daily_directory, f"{time_prefix}{safe_matchup}_{random_hash}")
        
        try:
            # Generate blog post
            blog_post = generate_mlb_blog_post(topic, keywords, game_data)
            save_to_file(game_directory, "original_post.txt", blog_post)
            print(f"  📝 Original blog post: {len(blog_post)} chars")
            
            # Audit and optimize
            optimized_post = audit_blog_post(blog_post)
            print(f"  🔍 Audited blog post: {len(optimized_post)} chars")
            
            # Add internal links
            optimized_post = auto_link_blog_content(optimized_post, max_links=8)
            print(f"  🔗 Added internal links: {len(optimized_post)} chars")
            
            # Convert to HTML - SIMPLE VERSION FOR DEBUGGING
            html_post = simple_text_to_html(optimized_post)
            print(f"  🔄 Converted to HTML: {len(html_post)} chars")
            
            save_to_file(game_directory, "optimized_post.html", html_post)
            print(f"  ✅ Saved HTML blog post")
            
            # Generate team logos
            away_team = game_data['away_team']
            home_team = game_data['home_team']
            team_logos = generate_team_logos_for_matchup(away_team, home_team)
            print(f"  🏆 Generated team logos: {away_team} & {home_team}")
            
            logo_info = f"""Away Team: {team_logos['away_team']}
Away Logo: {team_logos['away_logo']}
Home Team: {team_logos['home_team']}
Home Logo: {team_logos['home_logo']}"""
            
            save_to_file(game_directory, "team_logos.txt", logo_info)
            save_to_file(game_directory, "game_data.json", json.dumps(game_data, indent=2))
            
        except Exception as e:
            print(f"  ❌ Error processing {topic}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n🎉 Completed! Generated {len(blog_topics)} blog posts in {daily_directory}")

@app.route('/')
def display_blogs():
    """Display all blogs as raw HTML - DEBUG VERSION"""
    today = datetime.now().strftime("%Y-%m-%d")
    blog_dir = f"mlb_blog_posts/{today}"
    
    print(f"🔧 DEBUG: Looking for blogs in: {blog_dir}")
    
    all_blogs_html = []
    
    if os.path.exists(blog_dir):
        folders = sorted([f for f in os.listdir(blog_dir) if os.path.isdir(os.path.join(blog_dir, f))])
        print(f"🔧 DEBUG: Found {len(folders)} folders")
        
        for folder in folders:
            folder_path = os.path.join(blog_dir, folder)
            html_file = os.path.join(folder_path, "optimized_post.html")
            
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    blog_content = f.read()
                    print(f"🔧 DEBUG: Loaded blog from {folder}, length: {len(blog_content)}")
                    print(f"🔧 DEBUG: Content starts with: {blog_content[:100]}")
                    all_blogs_html.append(blog_content)
            else:
                print(f"🔧 DEBUG: No HTML file found in {folder}")
    else:
        print(f"🔧 DEBUG: Blog directory doesn't exist: {blog_dir}")
    
    if not all_blogs_html:
        return f"""
        <h1>No blogs found for {today}</h1>
        <p>Blogs may still be generating...</p>
        <p>Debug info: Looked in {blog_dir}</p>
        """
    
    # Create simple HTML page
    combined_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MLB Blog Posts - {today}</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #1a365d; }}
            h2 {{ color: #2c5aa0; }}
            h3 {{ color: #4a5568; }}
            hr {{ margin: 30px 0; }}
        </style>
    </head>
    <body>
        <h1>🏟️ MLB BLOG POSTS FOR {today.upper()}</h1>
        <p>🕐 Generated at: {datetime.now().strftime('%I:%M %p ET')}</p>
        <p>📊 Total Games: {len(all_blogs_html)}</p>
        <hr>
    """
    
    for i, blog_html in enumerate(all_blogs_html):
        combined_html += blog_html
        if i < len(all_blogs_html) - 1:
            combined_html += "<hr>"
    
    combined_html += """
    </body>
    </html>
    """
    
    return Response(combined_html, mimetype='text/html')

@app.route('/generate')
def manual_generate():
    generate_daily_blogs()
    return "Blog generation triggered!"

@app.route('/health')
def health():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

def run_scheduler():
    schedule.every().day.at("11:00").do(generate_daily_blogs)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def initialize_app():
    print("🚀 Initializing Simple MLB Blog Service - DEBUG VERSION")
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    def delayed_blog_generation():
        time.sleep(5)
        generate_daily_blogs()
    
    blog_thread = threading.Thread(target=delayed_blog_generation, daemon=True)
    blog_thread.start()

if __name__ == '__main__':
    initialize_app()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
