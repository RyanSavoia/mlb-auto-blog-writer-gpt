# main.py (SEO-Optimized - Fixed Version)
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

def parse_start_time_iso(local_time_str, tz_offset="-04:00"):
    """Return HH:MM:SS±TZ for schema; defaults to 19:05 if TBD/unparseable."""
    try:
        if not local_time_str or local_time_str == 'TBD':
            return f"19:05:00{tz_offset}"
        time_part = local_time_str.split(',')[-1].strip() if ',' in local_time_str else local_time_str.strip()
        tp = time_part.upper().replace('.', '')
        # Ensure space before AM/PM (handles "06:40PM" → "06:40 PM")
        tp = re.sub(r'([AP])M$', r' \1M', tp)
        from datetime import datetime as dt
        fmt = "%I:%M %p" if ':' in tp else "%I %p"
        time_obj = dt.strptime(tp, fmt)
        return time_obj.strftime(f"%H:%M:00{tz_offset}")
    except Exception as e:
        print(f"parse_start_time_iso error for '{local_time_str}': {e}")
        return f"19:05:00{tz_offset}"

def convert_text_to_html_with_seo(blog_text, game_data, team_logos=None):
    """Convert plain text to SEO-optimized HTML snippet - FIXED VERSION"""
    if not blog_text:
        return blog_text

    print(f"🔧 SEO CONVERTER DEBUG:")
    print(f"   Input length: {len(blog_text)} chars")
    print(f"   Game data: {game_data.get('matchup', 'Unknown')}")
    print(f"   Team logos available: {bool(team_logos and team_logos.get('away_logo'))}")

    date_str = datetime.now().strftime("%Y-%m-%d")
    start_time_iso = parse_start_time_iso(game_data.get('game_time', 'TBD'))
    start_datetime = f"{date_str}T{start_time_iso}"

    # JSON-LD: Article + SportsEvent
    schema_objects = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{game_data['matchup']} MLB Betting Preview - {date_str}",
            "description": f"Expert betting analysis for {game_data['matchup']} with pitcher matchups and betting insights.",
            "datePublished": f"{date_str}T00:00:00-04:00",
            "dateModified": f"{date_str}T00:00:00-04:00",
            "author": {
                "@type": "Person",
                "name": "Mike Chen",
                "jobTitle": "Senior MLB Betting Analyst",
                "url": "https://www.thebettinginsider.com/author/mike-chen"
            },
            "publisher": {
                "@type": "Organization",
                "name": "The Betting Insider",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://www.thebettinginsider.com/logo.png",
                    "width": 200,
                    "height": 60
                },
                "url": "https://www.thebettinginsider.com"
            },
            "articleSection": "Sports Betting",
            "keywords": f"MLB, {game_data['away_team']}, {game_data['home_team']}, baseball betting, sports analysis, pitcher matchup",
            "about": [
                {"@type": "SportsTeam", "name": game_data['away_team'], "sport": "Baseball"},
                {"@type": "SportsTeam", "name": game_data['home_team'], "sport": "Baseball"}
            ]
        },
        {
            "@context": "https://schema.org",
            "@type": "SportsEvent",
            "name": f"{game_data['matchup']} ({game_data.get('game_time', 'TBD')})",
            "description": f"MLB game between {game_data['away_team']} and {game_data['home_team']}",
            "sport": "Baseball",
            "startDate": start_datetime,
            "homeTeam": {"@type": "SportsTeam", "name": game_data['home_team'], "sport": "Baseball"},
            "awayTeam": {"@type": "SportsTeam", "name": game_data['away_team'], "sport": "Baseball"},
            "organizer": {"@type": "SportsOrganization", "name": "Major League Baseball"}
        }
    ]
    
    if game_data.get('venue'):
        schema_objects[1]["location"] = {
            "@type": "Place",
            "name": game_data['venue'],
            "address": {"@type": "PostalAddress", "addressCountry": "US"}
        }

    schema_markup = f'<script type="application/ld+json">{json.dumps(schema_objects, indent=2)}</script>'

    # Normalize markdown bold to <strong> - FIXED REGEX
    text = blog_text
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)  # **bold**
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<strong>\1</strong>', text)  # *bold* but not **bold**
    
    print(f"   After bold conversion: {len(text)} chars")

    lines = [ln.rstrip() for ln in text.split('\n')]
    html_lines = []
    in_list = False

    # Team header with logos - ALWAYS ADD EVEN IF LOGOS FAIL
    away_team = game_data.get('away_team', 'Away')
    home_team = game_data.get('home_team', 'Home')
    game_time = game_data.get('game_time', 'TBD')
    
    header_html = f"""
<div class="game-header" style="display:flex;justify-content:space-between;align-items:center;margin:20px 0;padding:16px;background:#f8fafc;border-radius:10px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="font-weight:700;font-size:18px;">{away_team}</span>
  </div>
  <div style="text-align:center;">
    <div style="font-weight:700;font-size:20px;">@</div>
    <div style="color:#555;font-size:14px;">{game_time}</div>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="font-weight:700;font-size:18px;">{home_team}</span>
  </div>
</div>
"""
    html_lines.append(header_html)
    print(f"   Added team header")

    # Convert lines to semantic HTML - IMPROVED LOGIC
    for raw in lines:
        line = raw.strip()
        if not line:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('<br>')
            continue

        # H1 if contains MLB Betting Preview
        if 'MLB Betting Preview' in line:
            if in_list: html_lines.append('</ul>'); in_list = False
            clean = re.sub(r'^<strong>(.+?)</strong>$', r'\1', line)
            html_lines.append(f'<h1>{clean}</h1>')
            continue

        # Game Time → H2
        if 'Game Time:' in line:
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<h2>{line}</h2>')
            continue

        # Numbered sections (1., 2., etc.) → H2
        if re.match(r'^\d+\.\s+', line):
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<h2>{line}</h2>')
            continue

        # Headers starting with ### → H3
        if line.startswith('###'):
            if in_list: html_lines.append('</ul>'); in_list = False
            clean_line = line.replace('###', '').strip()
            html_lines.append(f'<h3>{clean_line}</h3>')
            continue

        # Headers starting with #### → H4
        if line.startswith('####'):
            if in_list: html_lines.append('</ul>'); in_list = False
            clean_line = line.replace('####', '').strip()
            html_lines.append(f'<h4>{clean_line}</h4>')
            continue

        # **Header:** → H3
        if re.match(r'^<strong>.+?:</strong>\s*$', line):
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<h3>{line}</h3>')
            continue

        # STEP → H4
        if line.upper().startswith('STEP'):
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<h4><strong>{line}</strong></h4>')
            continue

        # Bullets
        if line.startswith('- ') or line.startswith('• '):
            if not in_list:
                html_lines.append('<ul>'); in_list = True
            html_lines.append(f'<li>{line[2:].strip()}</li>')
            continue

        # Default → paragraph
        if in_list:
            html_lines.append('</ul>'); in_list = False
        html_lines.append(f'<p>{line}</p>')

    if in_list:
        html_lines.append('</ul>')

    # Methodology footer
    methodology_html = """
<div class="methodology" style="margin-top:24px;padding:16px;background:#f7fafc;border-left:4px solid #3182ce;border-radius:8px;">
  <h4 style="margin:0 0 8px 0;">📊 Methodology & Sources</h4>
  <p style="margin:0;">Analysis uses pitch-type performance, platoon splits, and contact-quality metrics (xBA, xSLG, whiff%) from advanced MLB data.</p>
  <p style="margin:6px 0 0 0;font-size:12px;color:#555;">
    Primary data: <a href="https://baseballsavant.mlb.com" rel="noopener" target="_blank">Baseball Savant</a>.
  </p>
</div>
"""

    final_html = '\n'.join([schema_markup] + html_lines + [methodology_html])
    print(f"   Final HTML length: {len(final_html)} chars")
    print(f"   Contains <h1>: {'<h1>' in final_html}")
    print(f"   Contains schema: {'application/ld+json' in final_html}")
    
    return final_html

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
            print("  🤖 Generating blog with GPT-4...")
            blog_post = generate_mlb_blog_post(topic, keywords, game_data)
            save_to_file(game_directory, "original_post.txt", blog_post)
            print(f"  ✅ Generated: {len(blog_post)} characters")
            
            # Skip audit for now to test if it's breaking HTML formatting
            print("  🔍 Skipping audit to test HTML formatting...")
            optimized_post = blog_post  # Skip audit completely
            print(f"  ✅ Using original post: {len(optimized_post)} characters")
            
            # Add internal links
            print("  🔗 Adding internal links...")
            optimized_post = auto_link_blog_content(optimized_post, max_links=8)
            print(f"  ✅ Links added: {len(optimized_post)} characters")
            
            # Generate team logos (try to get them, but continue if fails)
            print("  🏆 Getting team logos...")
            try:
                away_team = game_data['away_team']
                home_team = game_data['home_team']
                team_logos = generate_team_logos_for_matchup(away_team, home_team)
                print(f"  ✅ Team logos: {away_team} & {home_team}")
            except Exception as logo_error:
                print(f"  ⚠️ Logo generation failed: {logo_error}")
                team_logos = None
            
            # Convert to HTML with full SEO optimization
            print("  🔄 Converting to SEO-optimized HTML...")
            html_post = convert_text_to_html_with_seo(optimized_post, game_data, team_logos)
            print(f"  ✅ HTML generated: {len(html_post)} characters")
            
            save_to_file(game_directory, "optimized_post.html", html_post)
            
            # DEBUG: Save a simple test HTML file to verify saving works
            test_html = f"<h1>TEST HTML FOR {game_data['matchup']}</h1><p>This should be HTML</p>"
            save_to_file(game_directory, "test.html", test_html)
            
            # DEBUG: Also save the original text for comparison
            save_to_file(game_directory, "debug_original.txt", optimized_post)
            
            print(f"  🔧 DEBUG: Saved files - HTML starts with: {html_post[:100]}")
            
            # Save metadata
            if team_logos:
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
    
    print(f"\n🎉 Completed! Generated {len(blog_topics)} SEO-optimized blog posts in {daily_directory}")

@app.route('/')
def display_blogs():
    """Display all blogs as HTML with proper styling"""
    today = datetime.now().strftime("%Y-%m-%d")
    blog_dir = f"mlb_blog_posts/{today}"
    
    print(f"🔧 DISPLAY DEBUG: Looking in {blog_dir}")
    
    all_blogs_html = []
    
    if os.path.exists(blog_dir):
        folders = sorted([f for f in os.listdir(blog_dir) if os.path.isdir(os.path.join(blog_dir, f))])
        print(f"🔧 DISPLAY DEBUG: Found {len(folders)} folders")
        
        for folder in folders:
            folder_path = os.path.join(blog_dir, folder)
            html_file = os.path.join(folder_path, "optimized_post.html")
            
            print(f"🔧 DISPLAY DEBUG: Checking {folder}")
            print(f"🔧 DISPLAY DEBUG: Looking for file: {html_file}")
            print(f"🔧 DISPLAY DEBUG: File exists: {os.path.exists(html_file)}")
            
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    blog_content = f.read()
                    print(f"🔧 DISPLAY DEBUG: Loaded {len(blog_content)} chars from {folder}")
                    print(f"🔧 DISPLAY DEBUG: Content starts with: '{blog_content[:100]}'")
                    print(f"🔧 DISPLAY DEBUG: Contains <h1>: {'<h1>' in blog_content}")
                    all_blogs_html.append(blog_content)
            else:
                # List all files in the folder to see what's actually there
                files = os.listdir(folder_path)
                print(f"🔧 DISPLAY DEBUG: Files in {folder}: {files}")
    else:
        print(f"🔧 DISPLAY DEBUG: Directory doesn't exist: {blog_dir}")
    
    if not all_blogs_html:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>No Blogs Found</title></head>
        <body>
            <h1>No blogs found for {today}</h1>
            <p>Blogs may still be generating...</p>
        </body>
        </html>
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>No Blogs Found</title></head>
        <body>
            <h1>No blogs found for {today}</h1>
            <p>Blogs may still be generating...</p>
        </body>
        </html>
        """
    
    # Create complete HTML document with all SEO-optimized blogs
    combined_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MLB Blog Posts - {today}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
            h1 {{ color: #1a365d; font-size: 28px; margin: 30px 0 20px 0; }}
            h2 {{ color: #2c5aa0; font-size: 22px; margin: 25px 0 15px 0; }}
            h3 {{ color: #4a5568; font-size: 18px; margin: 20px 0 10px 0; }}
            h4 {{ color: #4a5568; font-size: 16px; margin: 15px 0 8px 0; }}
            p {{ margin-bottom: 15px; }}
            ul {{ margin: 15px 0; padding-left: 25px; }}
            li {{ margin-bottom: 8px; }}
            a {{ color: #3182ce; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            strong {{ color: #1a365d; }}
            hr {{ margin: 40px 0; border: none; height: 2px; background: linear-gradient(90deg, #e2e8f0 0%, #cbd5e0 50%, #e2e8f0 100%); }}
            .game-header {{ background: #f8fafc !important; }}
        </style>
    </head>
    <body>
        <h1 style="text-align: center;">🏟️ MLB BLOG POSTS FOR {today.upper()}</h1>
        <p style="text-align: center;">🕐 Generated at: {datetime.now().strftime('%I:%M %p ET')} | 📊 Total Games: {len(all_blogs_html)}</p>
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
    print("🚀 Initializing SEO-Optimized MLB Blog Service")
    
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
