# main.py (Web Service Version)
import os
import threading
import time
import schedule
from flask import Flask, Response, render_template, redirect, url_for
from generate_blog_post import generate_mlb_blog_post
from audit_blog_post import audit_blog_post
from generate_image import generate_team_logos_for_matchup
from mlb_data_fetcher import MLBDataFetcher
import uuid
import json
from datetime import datetime
import re
from urllib.parse import quote

app = Flask(__name__)

# Internal linking phrase-to-URL mapping
INTERLINK_MAP = {
    # Stats product
    "betting splits": "https://www.thebettinginsider.com/stats-about",
    "public money": "https://www.thebettinginsider.com/stats-about",
    "betting percentage": "https://www.thebettinginsider.com/stats-about",
    "sharp money": "https://www.thebettinginsider.com/stats-about",
    "betting trends": "https://www.thebettinginsider.com/stats-about",
    "stats dashboard": "https://www.thebettinginsider.com/stats-about",
    # Pitcher arsenal tool
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
    """Automatically insert internal links into blog content"""
    if not blog_text or max_links <= 0:
        return blog_text
    
    links_inserted = 0
    modified_text = blog_text
    
    # Sort phrases by length (longest first) to avoid partial matching issues
    sorted_phrases = sorted(INTERLINK_MAP.keys(), key=len, reverse=True)
    
    for phrase in sorted_phrases:
        if links_inserted >= max_links:
            break
            
        url = INTERLINK_MAP[phrase]
        
        # Create regex pattern for whole word/phrase matching (case-insensitive)
        pattern = r'\b' + re.escape(phrase) + r'\b'
        
        # Check if this phrase exists in the text and isn't already linked
        match = re.search(pattern, modified_text, re.IGNORECASE)
        if match:
            # Check if the matched phrase is already inside an HTML link
            matched_text = match.group()
            start_pos = match.start()
            
            # Look backwards from match to see if we're inside a link tag
            preceding_text = modified_text[:start_pos]
            last_link_start = preceding_text.rfind('<a ')
            last_link_end = preceding_text.rfind('</a>')
            
            # If we're inside a link tag, skip this phrase
            if last_link_start > last_link_end:
                continue
            
            # Replace only the first occurrence with a link
            link_html = f'<a href="{url}">{matched_text}</a>'
            modified_text = re.sub(pattern, link_html, modified_text, count=1, flags=re.IGNORECASE)
            links_inserted += 1
            
            print(f"  🔗 Added internal link: '{matched_text}' -> {url}")
    
    if links_inserted > 0:
        print(f"  ✅ Total internal links added: {links_inserted}")
    
    return modified_text

def convert_text_to_html(blog_text):
    """Convert plain text blog to HTML format"""
    if not blog_text:
        return blog_text
    
    # Split into lines and process each one
    lines = blog_text.strip().split('\n')
    html_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for different header patterns
        if line.endswith('MLB Betting Preview'):
            # Main title
            html_lines.append(f'<h4><b>{line}</b></h4>')
        elif line.startswith('Game Time:'):
            # Game time header
            html_lines.append(f'<h4><b>{line}</b></h4>')
        elif re.match(r'^\d+\.\s+', line):
            # Numbered sections like "1. Brief Intro"
            html_lines.append(f'<h4><b>{line}</b></h4>')
        elif line.endswith(':') and len(line) < 50:
            # Sub-headers that end with colon
            html_lines.append(f'<h5><b>{line}</b></h5>')
        elif line.startswith('STEP'):
            # Step headers
            html_lines.append(f'<p><b>{line}</b></p>')
        else:
            # Regular content
            html_lines.append(f'<p>{line}</p>')
    
    return '\n'.join(html_lines)

def save_to_file(directory, filename, content):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'w', encoding='utf-8') as file:
        file.write(content)

def create_slug(matchup, game_time):
    """Create SEO-friendly slug from matchup and time"""
    # Clean the matchup: "Yankees @ Red Sox" -> "yankees-vs-red-sox"
    slug = matchup.lower().replace(' @ ', '-vs-').replace(' ', '-')
    
    # Add time if available
    if game_time and game_time != 'TBD':
        try:
            # Extract time like "7/8, 06:40PM" -> "640pm"
            if ',' in game_time:
                time_part = game_time.split(',')[1].strip()
            else:
                time_part = game_time.strip()
            time_clean = time_part.lower().replace(':', '').replace(' ', '')
            slug += f"-{time_clean}"
        except:
            pass
    
    # Remove special characters and ensure valid slug
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    slug = re.sub(r'-+', '-', slug)  # Multiple dashes -> single dash
    return slug.strip('-')

def generate_blog_schema(game_data, blog_content, slug, date_str):
    """Generate JSON-LD schema for SEO"""
    
    # Extract title from blog content (first line or H1)
    lines = blog_content.strip().split('\n')
    title = lines[0] if lines else f"{game_data['matchup']} Preview"
    if title.startswith('#'):
        title = title.replace('#', '').strip()
    
    # Generate description from first paragraph
    description = ""
    for line in lines[1:]:
        if line.strip() and not line.startswith('#'):
            description = line.strip()[:160]
            break
    
    if not description:
        description = f"MLB game preview: {game_data['matchup']} on {game_data.get('game_date', date_str)}"
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": f"{date_str}T00:00:00Z",
        "dateModified": f"{date_str}T00:00:00Z",
        "author": {
            "@type": "Organization",
            "name": "MLB Blog Generator"
        },
        "publisher": {
            "@type": "Organization",
            "name": "MLB Blog Generator"
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"/mlb-blogs/{date_str}/{slug}"
        },
        "articleSection": "Sports",
        "keywords": f"MLB, {game_data['away_team']}, {game_data['home_team']}, baseball, preview",
        "about": [
            {
                "@type": "SportsTeam",
                "name": game_data['away_team']
            },
            {
                "@type": "SportsTeam", 
                "name": game_data['home_team']
            }
        ]
    }
    
    return schema

def parse_game_time_for_sorting(time_str):
    """Parse game time for proper chronological sorting"""
    if not time_str or time_str == 'TBD':
        return 9999  # Sort TBD games to the end
    
    try:
        # Handle format like "7/8, 06:40PM" or just "06:40PM"
        if ',' in time_str:
            time_part = time_str.split(',')[1].strip()
        else:
            time_part = time_str.strip()
        
        # Convert to 24-hour format for proper sorting
        if 'PM' in time_part:
            hour = int(time_part.split(':')[0])
            if hour != 12:
                hour += 12
            minute = int(time_part.split(':')[1].replace('PM', ''))
        else:  # AM
            hour = int(time_part.split(':')[0])
            if hour == 12:
                hour = 0
            minute = int(time_part.split(':')[1].replace('AM', ''))
        
        return hour * 100 + minute  # Returns like 1840 for 6:40PM
    except Exception as e:
        print(f"⚠️ Error parsing time '{time_str}': {e}")
        return 9999  # Sort unparseable times to end

def generate_daily_blogs():
    """Generate all blogs for today with SEO metadata"""
    print(f"🚀 Starting daily blog generation at {datetime.now()}")
    
    # Initialize MLB data fetcher
    mlb_fetcher = MLBDataFetcher()
    
    # Get today's games as blog topics
    blog_topics = mlb_fetcher.get_blog_topics_from_games()
    
    if not blog_topics:
        print("❌ No games available for blog generation")
        return
    
    # Sort by game time
    print(f"🔄 Sorting {len(blog_topics)} games by time...")
    blog_topics.sort(key=lambda x: parse_game_time_for_sorting(x['game_data'].get('game_time', 'TBD')))
    
    # Debug: Print sorted order
    for i, topic in enumerate(blog_topics):
        game_time = topic['game_data'].get('game_time', 'TBD')
        print(f"  {i+1}. {topic['topic']} - {game_time}")
    
    base_directory = "mlb_blog_posts"
    date_str = datetime.now().strftime("%Y-%m-%d")
    daily_directory = os.path.join(base_directory, date_str)
    
    if not os.path.exists(daily_directory):
        os.makedirs(daily_directory)
    
    print(f"🚀 Generating {len(blog_topics)} MLB blog posts for {date_str}")
    
    blog_index = []  # Store metadata for index page
    
    for i, blog_topic in enumerate(blog_topics, 1):
        topic = blog_topic['topic']
        keywords = blog_topic['keywords']
        game_data = blog_topic['game_data']
        
        print(f"\n📝 Processing game {i}/{len(blog_topics)}: {game_data['matchup']} at {game_data.get('game_time', 'TBD')}")
        
        # Create SEO-friendly slug
        slug = create_slug(game_data['matchup'], game_data.get('game_time'))
        game_directory = os.path.join(daily_directory, slug)
        
        try:
            # Generate MLB-specific blog post
            print("  🤖 Generating blog post with GPT-4...")
            blog_post = generate_mlb_blog_post(topic, keywords, game_data)
            save_to_file(game_directory, "original_post.txt", blog_post)
            print(f"  ✅ Generated blog post ({len(blog_post)} characters)")
            
            # Audit and optimize blog post
            print("  🔍 Optimizing for readability...")
            optimized_post = audit_blog_post(blog_post)
            
            # Add internal links
            print("  🔗 Adding internal links...")
            optimized_post = auto_link_blog_content(optimized_post)
            
            # Convert to HTML format
            print("  🔄 Converting to HTML format...")
            html_post = convert_text_to_html(optimized_post)
            
            save_to_file(game_directory, "optimized_post.txt", html_post)
            print("  ✅ Optimized blog post saved")
            
            # Generate team logos
            print("  🏆 Getting team logos...")
            away_team = game_data['away_team']
            home_team = game_data['home_team']
            team_logos = generate_team_logos_for_matchup(away_team, home_team)
            
            # Save team logo information
            logo_info = f"""Away Team: {team_logos['away_team']}
Away Logo: {team_logos['away_logo']}
Home Team: {team_logos['home_team']}
Home Logo: {team_logos['home_logo']}"""
            
            save_to_file(game_directory, "team_logos.txt", logo_info)
            save_to_file(game_directory, "image_url.txt", f"Away: {team_logos['away_logo']}\nHome: {team_logos['home_logo']}")
            print(f"  ✅ Team logos saved: {away_team} & {home_team}")
            
            # Generate and save SEO schema
            print("  🔍 Generating SEO schema...")
            schema = generate_blog_schema(game_data, html_post, slug, date_str)
            save_to_file(game_directory, "schema.json", json.dumps(schema, indent=2))
            print("  ✅ SEO schema saved")
            
            # Create metadata for this blog
            meta = {
                "slug": slug,
                "title": schema["headline"],
                "description": schema["description"],
                "matchup": game_data['matchup'],
                "game_time": game_data.get('game_time', 'TBD'),
                "away_team": game_data['away_team'],
                "home_team": game_data['home_team'],
                "away_logo": team_logos['away_logo'],
                "home_logo": team_logos['home_logo'],
                "url": f"/mlb-blogs/{date_str}/{slug}",
                "generated_at": datetime.now().isoformat()
            }
            
            save_to_file(game_directory, "meta.json", json.dumps(meta, indent=2))
            blog_index.append(meta)
            print("  ✅ Blog metadata saved")
            
            # Save game data for reference
            save_to_file(game_directory, "game_data.json", json.dumps(game_data, indent=2))
            print("  ✅ Game data saved")
            
        except Exception as e:
            print(f"  ❌ Error processing {topic}: {e}")
            continue
    
    # Save daily index
    save_to_file(daily_directory, "index.json", json.dumps({
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "total_blogs": len(blog_index),
        "blogs": blog_index
    }, indent=2))
    
    print(f"\n🎉 Completed! Generated {len(blog_topics)} blog posts in {daily_directory}")

@app.route('/')
def home():
    """Redirect to today's blog index"""
    today = datetime.now().strftime("%Y-%m-%d")
    return redirect(url_for('blog_index', date=today))

@app.route('/mlb-blogs/<date>')
def blog_index(date):
    """Display index of all blogs for a specific date"""
    blog_dir = f"mlb_blog_posts/{date}"
    index_file = os.path.join(blog_dir, "index.json")
    
    if not os.path.exists(index_file):
        return f"""
        <html>
        <head><title>No Blogs Found - {date}</title></head>
        <body>
            <h1>No blogs found for {date}</h1>
            <p>Blogs may still be generating...</p>
            <p><a href="/generate">Trigger manual generation</a></p>
        </body>
        </html>
        """, 404
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    # Generate HTML index page
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MLB Blog Posts - {date}</title>
        <meta name="description" content="Daily MLB game previews and analysis for {date}. {index_data['total_blogs']} games covered.">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .game-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .game-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; }}
            .game-card:hover {{ box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .matchup {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
            .game-time {{ color: #666; margin-bottom: 10px; }}
            .teams {{ display: flex; align-items: center; gap: 10px; margin: 10px 0; }}
            .team-logo {{ width: 30px; height: 30px; }}
            .description {{ color: #555; line-height: 1.5; }}
            .read-more {{ display: inline-block; margin-top: 10px; color: #007bff; text-decoration: none; }}
            .read-more:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏟️ MLB Blog Posts - {date}</h1>
            <p>📊 {index_data['total_blogs']} games • 🕐 Generated at {index_data['generated_at'][:19].replace('T', ' ')}</p>
        </div>
        <div class="game-grid">
    """
    
    for blog in index_data['blogs']:
        html += f"""
            <div class="game-card">
                <div class="matchup">{blog['matchup']}</div>
                <div class="game-time">⏰ {blog['game_time']}</div>
                <div class="teams">
                    <img src="{blog['away_logo']}" alt="{blog['away_team']}" class="team-logo" onerror="this.style.display='none'">
                    <span>vs</span>
                    <img src="{blog['home_logo']}" alt="{blog['home_team']}" class="team-logo" onerror="this.style.display='none'">
                </div>
                <div class="description">{blog['description']}</div>
                <a href="{blog['url']}" class="read-more">Read Full Preview →</a>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/mlb-blogs/<date>/<slug>')
def show_blog(date, slug):
    """Display individual blog post as raw HTML for Webflow integration"""
    folder_path = f"mlb_blog_posts/{date}/{slug}"
    file_path = os.path.join(folder_path, "optimized_post.txt")
    schema_path = os.path.join(folder_path, "schema.json")
    meta_path = os.path.join(folder_path, "meta.json")
    
    if not os.path.exists(file_path):
        return "<h1>Blog not found</h1>", 404
    
    with open(file_path, 'r', encoding='utf-8') as f:
        blog_content = f.read()
    
    schema = {}
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    # Create team metadata section with logo URLs
    team_meta_html = f"""
    <div class="team-meta">
        <div class="away-team" data-team="{meta.get('away_team', '')}" data-logo="{meta.get('away_logo', '')}">
            <span class="team-name">{meta.get('away_team', '')}</span>
            <img src="{meta.get('away_logo', '')}" alt="{meta.get('away_team', '')} logo" class="team-logo">
        </div>
        <div class="game-info">
            <span class="vs-text">@</span>
            <span class="game-time">{meta.get('game_time', 'TBD')}</span>
        </div>
        <div class="home-team" data-team="{meta.get('home_team', '')}" data-logo="{meta.get('home_logo', '')}">
            <span class="team-name">{meta.get('home_team', '')}</span>
            <img src="{meta.get('home_logo', '')}" alt="{meta.get('home_team', '')} logo" class="team-logo">
        </div>
    </div>
    """
    
    # Add SEO schema as invisible JSON for Webflow
    schema_html = ""
    if schema:
        schema_html = f'<script type="application/ld+json">{json.dumps(schema, indent=2)}</script>'
    
    # Generate raw HTML output for Webflow
    raw_html = f"""<!-- SEO Meta Data -->
<meta name="title" content="{schema.get('headline', meta.get('title', f'MLB: {meta.get('matchup', 'Game Preview')}'))}">
<meta name="description" content="{schema.get('description', meta.get('description', ''))}">
<link rel="canonical" href="/mlb-blogs/{date}/{slug}">

<!-- Team Metadata for Webflow -->
{team_meta_html}

<!-- Blog Content -->
{blog_content}

<!-- SEO Schema -->
{schema_html}

<!-- Metadata for Webflow CMS -->
<div class="blog-metadata" style="display:none;">
    <span class="matchup">{meta.get('matchup', '')}</span>
    <span class="date">{date}</span>
    <span class="slug">{slug}</span>
    <span class="away-team">{meta.get('away_team', '')}</span>
    <span class="home-team">{meta.get('home_team', '')}</span>
    <span class="away-logo-url">{meta.get('away_logo', '')}</span>
    <span class="home-logo-url">{meta.get('home_logo', '')}</span>
    <span class="game-time">{meta.get('game_time', 'TBD')}</span>
</div>"""
    
    return raw_html

@app.route('/generate')
def manual_generate():
    """Manual trigger to generate blogs"""
    generate_daily_blogs()
    return "Blog generation triggered! Check back in a few minutes."

@app.route('/health')
def health():
    """Health check"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

def run_scheduler():
    """Run daily blog generation at 7 AM EDT"""
    schedule.every().day.at("11:00").do(generate_daily_blogs)  # 11:00 UTC = 7:00 AM EDT
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def initialize_app():
    """Initialize with Flask server first, then generate blogs in background"""
    print("🚀 Initializing MLB Blog Service")
    
    # Start background scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Background scheduler started - will generate daily at 7 AM EDT")
    
    # Generate blogs in background after Flask starts
    def delayed_blog_generation():
        time.sleep(5)  # Wait for Flask to start
        generate_daily_blogs()
    
    blog_thread = threading.Thread(target=delayed_blog_generation, daemon=True)
    blog_thread.start()
    print("✅ Blog generation started in background")

if __name__ == '__main__':
    initialize_app()
    
    # Start Flask web server immediately
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
