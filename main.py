# main.py (Clean SEO Version - No Duplicates)
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

def convert_to_html_with_seo(blog_text, game_data):
    """Convert text to HTML with SEO features - handles all GPT formatting variations"""
    if not blog_text:
        return blog_text
    
    print(f"🔧 HTML CONVERTER: Input {len(blog_text)} chars")
    
    # Step 1: Convert bold formatting
    html_text = blog_text
    html_text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', html_text)  # **bold**
    html_text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<strong>\1</strong>', html_text)  # *bold*
    
    # Step 2: Convert to HTML
    lines = html_text.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('<br>')
            continue
            
        # Main titles with "MLB Betting Preview"
        if 'MLB Betting Preview' in line:
            if in_list: html_lines.append('</ul>'); in_list = False
            clean_line = re.sub(r'^<strong>(.+?)</strong>$', r'\1', line)
            html_lines.append(f'<h1>{clean_line}</h1>')
        # Game Time
        elif 'Game Time:' in line:
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<h2>{line}</h2>')
        # Numbered sections
        elif re.match(r'^\d+\.\s+', line):
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<h2>{line}</h2>')
        # Markdown headers ###
        elif line.startswith('###'):
            if in_list: html_lines.append('</ul>'); in_list = False
            clean_line = line.replace('###', '').strip()
            html_lines.append(f'<h3>{clean_line}</h3>')
        # Markdown headers ####
        elif line.startswith('####'):
            if in_list: html_lines.append('</ul>'); in_list = False
            clean_line = line.replace('####', '').strip()
            html_lines.append(f'<h4>{clean_line}</h4>')
        # STEP headers
        elif line.upper().startswith('STEP'):
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<h4>{line}</h4>')
        # Bold headers ending with colon
        elif line.startswith('<strong>') and line.endswith(':</strong>'):
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<h3>{line}</h3>')
        # List items
        elif line.startswith('- ') or line.startswith('• '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line[2:].strip()}</li>')
        # Regular paragraphs
        else:
            if in_list: html_lines.append('</ul>'); in_list = False
            html_lines.append(f'<p>{line}</p>')
    
    if in_list:
        html_lines.append('</ul>')
    
    # Add SEO schema
    date_str = datetime.now().strftime("%Y-%m-%d")
    schema = f'''<script type="application/ld+json">{{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{game_data['matchup']} MLB Betting Preview - {date_str}",
        "datePublished": "{date_str}T00:00:00-04:00",
        "author": {{"@type": "Person", "name": "Mike Chen", "jobTitle": "Senior MLB Betting Analyst"}},
        "publisher": {{"@type": "Organization", "name": "The Betting Insider"}},
        "keywords": "MLB, {game_data['away_team']}, {game_data['home_team']}, baseball betting",
        "about": [
            {{"@type": "SportsTeam", "name": "{game_data['away_team']}", "sport": "Baseball"}},
            {{"@type": "SportsTeam", "name": "{game_data['home_team']}", "sport": "Baseball"}}
        ]
    }}</script>'''
    
    # Methodology footer
    methodology = '''
<div style="margin-top:24px;padding:16px;background:#f7fafc;border-left:4px solid #3182ce;border-radius:8px;">
  <h4 style="margin:0 0 8px 0;">📊 Methodology & Sources</h4>
  <p style="margin:0;">Analysis uses pitch-type performance, platoon splits, and contact-quality metrics from advanced MLB data.</p>
  <p style="margin:6px 0 0 0;font-size:12px;color:#555;">Primary data: <a href="https://baseballsavant.mlb.com" target="_blank">Baseball Savant</a>.</p>
</div>
'''
    
    result = schema + '\n' + '\n'.join(html_lines) + methodology
    print(f"🔧 HTML CONVERTER: Output {len(result)} chars, Contains <h1>: {'<h1>' in result}")
    
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
            print("  🤖 Generating blog with GPT-4...")
            blog_post = generate_mlb_blog_post(topic, keywords, game_data)
            save_to_file(game_directory, "original_post.txt", blog_post)
            print(f"  ✅ Generated: {len(blog_post)} characters")
            
            # Skip audit (it was breaking formatting)
            optimized_post = blog_post
            print(f"  ✅ Skipped audit: {len(optimized_post)} characters")
            
            # Add internal links
            print("  🔗 Adding internal links...")
            optimized_post = auto_link_blog_content(optimized_post, max_links=8)
            print(f"  ✅ Links added: {len(optimized_post)} characters")
            
            # Convert to HTML with SEO
            print("  🔄 Converting to HTML...")
            html_post = convert_to_html_with_seo(optimized_post, game_data)
            print(f"  ✅ HTML generated: {len(html_post)} characters")
            
            save_to_file(game_directory, "optimized_post.html", html_post)
            
            # Generate team logos for metadata
            try:
                away_team = game_data['away_team']
                home_team = game_data['home_team']
                team_logos = generate_team_logos_for_matchup(away_team, home_team)
                
                logo_info = f"""Away Team: {team_logos['away_team']}
Away Logo: {team_logos['away_logo']}
Home Team: {team_logos['home_team']}
Home Logo: {team_logos['home_logo']}"""
                
                save_to_file(game_directory, "team_logos.txt", logo_info)
            except:
                pass
            
            save_to_file(game_directory, "game_data.json", json.dumps(game_data, indent=2))
            
        except Exception as e:
            print(f"  ❌ Error processing {topic}: {e}")
            continue
    
    print(f"\n🎉 Completed! Generated {len(blog_topics)} SEO-optimized blog posts")

@app.route('/')
def display_blogs():
    """Display all blogs as HTML"""
    today = datetime.now().strftime("%Y-%m-%d")
    blog_dir = f"mlb_blog_posts/{today}"
    
    all_blogs_html = []
    
    if os.path.exists(blog_dir):
        folders = sorted([f for f in os.listdir(blog_dir) if os.path.isdir(os.path.join(blog_dir, f))])
        
        for folder in folders:
            folder_path = os.path.join(blog_dir, folder)
            html_file = os.path.join(folder_path, "optimized_post.html")
            
            if os.path.exists(html_file):
                with open(html_file, 'r', encoding='utf-8') as f:
                    blog_content = f.read()
                    all_blogs_html.append(blog_content)
    
    if not all_blogs_html:
        return "<h1>No blogs found</h1><p>Blogs may still be generating...</p>"
    
    # Simple HTML output
    combined_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MLB Blog Posts - {today}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #1a365d; }}
        h2 {{ color: #2c5aa0; }}
        h3 {{ color: #4a5568; }}
        h4 {{ color: #666; }}
        a {{ color: #3182ce; }}
        strong {{ color: #1a365d; }}
        hr {{ margin: 30px 0; }}
    </style>
</head>
<body>
    <h1>🏟️ MLB BLOG POSTS FOR {today.upper()}</h1>
    <p>🕐 Generated at: {datetime.now().strftime('%I:%M %p ET')} | 📊 Total Games: {len(all_blogs_html)}</p>
    <hr>
'''
    
    for i, blog_html in enumerate(all_blogs_html):
        combined_html += blog_html
        if i < len(all_blogs_html) - 1:
            combined_html += "<hr>"
    
    combined_html += "</body></html>"
    
    return Response(combined_html, mimetype='text/html', headers={
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache'
    })

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
    print("🚀 Initializing MLB Blog Service")
    
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
