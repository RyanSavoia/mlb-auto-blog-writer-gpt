# main.py (Web Service Version with SEO Enhancements)
import os
import threading
import time
import schedule
from flask import Flask, Response, redirect, url_for, request
from generate_blog_post import generate_mlb_blog_post
from audit_blog_post import audit_blog_post
from generate_image import generate_team_logos_for_matchup
from mlb_data_fetcher import MLBDataFetcher
import json
from datetime import datetime
import re

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

def parse_start_time_iso(local_time_str, tz_offset="-04:00"):
    """Parse human game time to HH:MM:SS±TZ for schema.org JSON-LD
    
    Accepts: "8/11, 07:05 PM", "07:05 PM", "06:40PM", "705 PM", "705PM", "7 PM", "7PM"
    Falls back to 19:05 local time if unparseable or TBD
    """
    try:
        if not local_time_str or str(local_time_str).strip().upper().startswith("TBD"):
            raise ValueError("No concrete time")

        # If date present like "8/11, 07:05 PM", take time part only
        time_part = (str(local_time_str).split(",")[-1] if "," in str(local_time_str) else str(local_time_str)).strip()
        
        from datetime import datetime as dt
        tp = time_part.upper().replace(".", "")  # normalize "p.m." -> "PM"
        tp = re.sub(r"(\d)([AP]M)$", r"\1 \2", tp)  # "06:40PM" -> "06:40 PM"
        tp = re.sub(r"^(\d{1,2})(\d{2})\s*([AP]M)$", r"\1:\2 \3", tp)  # "705PM" -> "7:05 PM"
        tp = re.sub(r"^(\d{1,2})\s*([AP]M)$", r"\1:00 \2", tp)  # "7PM" -> "7:00 PM"
        
        t = dt.strptime(tp, "%I:%M %p")
        return t.strftime(f"%H:%M:00{tz_offset}")
    except Exception:
        return f"19:05:00{tz_offset}"

def auto_link_blog_content(blog_text, max_links=5):
    """Automatically insert internal links with word-count-based scaling"""
    if not blog_text or max_links <= 0:
        return blog_text
    
    # Calculate dynamic link cap based on content length
    words = len(blog_text.split())
    dynamic_cap = min(max_links, max(2, words // 250))  # 1 link per ~250 words, min 2, max from parameter
    
    print(f"  📊 Content: {words} words, allowing {dynamic_cap} internal links")
    
    links_inserted = 0
    modified_text = blog_text
    
    # Sort phrases by length (longest first) to avoid partial matching issues
    sorted_phrases = sorted(INTERLINK_MAP.keys(), key=len, reverse=True)
    
    for phrase in sorted_phrases:
        if links_inserted >= dynamic_cap:
            break
            
        url = INTERLINK_MAP[phrase]
        
        # Create regex pattern for phrase matching (handles special characters like %)
        pattern = r'(?<![A-Za-z0-9])' + re.escape(phrase) + r'(?![A-Za-z0-9])'
        
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
        print(f"  ✅ Total internal links added: {links_inserted}/{dynamic_cap}")
    
    return modified_text

def convert_text_to_html(blog_text):
    """Convert text blog to proper semantic HTML format - BULLETPROOF VERSION"""
    if not blog_text:
        return blog_text
    
    # Clean up the input text first
    blog_text = blog_text.strip()
    
    # Split into lines and process
    lines = blog_text.split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            # Close any open lists and add spacing
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('<br>')
            continue
        
        # Main title (contains "MLB Betting Preview") - H1 for SEO
        if 'MLB Betting Preview' in line:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            clean_line = line.replace('**', '').strip()
            html_lines.append(f'<h1>{clean_line}</h1>')
        
        # Game Time headers - H2 (SIMPLIFIED - no complex regex)
        elif 'Game Time:' in line:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            clean_line = line.replace('**', '').strip()
            html_lines.append(f'<h2>{clean_line}</h2>')
        
        # Numbered sections (1. Brief Intro, 2. Pitcher Analysis, etc.) - H2
        elif line.startswith(('1.', '2.', '3.', '4.', '5.', '**1.', '**2.', '**3.', '**4.', '**5.')):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            clean_line = line.replace('**', '').strip()
            html_lines.append(f'<h2>{clean_line}</h2>')
        
        # Bold headers that end with colon - H3
        elif line.startswith('**') and line.endswith(':**'):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            clean_line = line.replace('**', '').replace(':', ':').strip()
            html_lines.append(f'<h3>{clean_line}</h3>')
        
        # Other bold headers (start and end with **) - H3
        elif line.startswith('**') and line.endswith('**') and len(line) < 100:  # Avoid long paragraphs
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            clean_line = line.replace('**', '').strip()
            html_lines.append(f'<h3>{clean_line}</h3>')
        
        # STEP headers (special formatting) - H4
        elif line.startswith('STEP'):
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append(f'<h4><strong>{line}</strong></h4>')
        
        # List items (start with - or bullet)
        elif line.startswith('- ') or line.startswith('• '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            clean_line = line[2:].strip()
            # Handle bold text within list items
            clean_line = clean_line.replace('**', '<strong>').replace('**', '</strong>')
            html_lines.append(f'<li>{clean_line}</li>')
        
        # Regular paragraphs
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            # Handle bold text within paragraphs - simple replacement
            clean_line = line
            # Count ** occurrences and pair them up
            bold_count = line.count('**')
            if bold_count >= 2 and bold_count % 2 == 0:
                # Replace pairs of ** with strong tags
                parts = line.split('**')
                clean_line = ''
                for i, part in enumerate(parts):
                    if i % 2 == 0:
                        clean_line += part
                    else:
                        clean_line += f'<strong>{part}</strong>'
            html_lines.append(f'<p>{clean_line}</p>')
    
    # Close any remaining open list
    if in_list:
        html_lines.append('</ul>')
    
    return '\n'.join(html_lines)

def save_to_file(directory, filename, content):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'w', encoding='utf-8') as file:
        file.write(content)

def create_slug(matchup, game_time, date_str):
    """Create SEO-friendly slug with date disambiguation"""
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
    
    # Add date stamp for uniqueness using the actual blog date
    slug += f"-{date_str}"
    
    # Remove special characters and ensure valid slug
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    slug = re.sub(r'-+', '-', slug)  # Multiple dashes -> single dash
    return slug.strip('-')

def generate_comprehensive_schema(game_data, blog_content, slug, date_str, canonical_url):
    """Generate Article + SportsEvent schemas"""
    
    # Extract title and description
    lines = [line.strip() for line in blog_content.strip().split('\n') if line.strip()]
    title = "MLB Betting Preview"
    
    for line in lines:
        if 'MLB Betting Preview' in line:
            title = re.sub(r'<[^>]+>', '', line)  # Remove HTML tags
            break
    
    description = f"Expert betting analysis for {game_data['matchup']} including pitcher matchups, lineup projections, and key betting insights."
    
    # Parse game start time
    start_time_iso = parse_start_time_iso(game_data.get('game_time', '07:05 PM'))
    start_datetime = f"{date_str}T{start_time_iso}"
    
    # 1. Article Schema with Person author
    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": f"{date_str}T00:00:00-04:00",
        "dateModified": f"{date_str}T00:00:00-04:00",
        "author": {
            "@type": "Person",
            "name": "Mike Chen",
            "jobTitle": "Senior MLB Betting Analyst",
            "description": "MLB analytics expert with 8+ years covering advanced metrics, pitcher arsenals, and betting market analysis.",
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
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical_url
        },
        "articleSection": "Sports Betting",
        "keywords": f"MLB, {game_data['away_team']}, {game_data['home_team']}, baseball betting, sports analysis, pitcher matchup",
        "about": [
            {
                "@type": "SportsTeam",
                "name": game_data['away_team'],
                "sport": "Baseball"
            },
            {
                "@type": "SportsTeam", 
                "name": game_data['home_team'],
                "sport": "Baseball"
            }
        ]
    }
    
    # 2. SportsEvent Schema (only if we have venue data)
    sports_event_schema = {
        "@context": "https://schema.org",
        "@type": "SportsEvent",
        "name": f"{game_data['matchup']} ({game_data.get('game_time', 'TBD')})",
        "description": f"MLB game between {game_data['away_team']} and {game_data['home_team']}",
        "sport": "Baseball",
        "startDate": start_datetime,
        "homeTeam": {
            "@type": "SportsTeam",
            "name": game_data['home_team'],
            "sport": "Baseball"
        },
        "awayTeam": {
            "@type": "SportsTeam", 
            "name": game_data['away_team'],
            "sport": "Baseball"
        },
        "organizer": {
            "@type": "SportsOrganization",
            "name": "Major League Baseball"
        }
    }
    
    # Only add location if we have venue data
    if game_data.get('venue'):
        sports_event_schema["location"] = {
            "@type": "Place",
            "name": game_data['venue'],
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "US"
            }
        }
    
    return [article_schema, sports_event_schema]

def generate_itemlist_schema(blog_index, date):
    """Generate ItemList schema for daily index page"""
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListOrder": "Ascending",
        "numberOfItems": len(blog_index),
        "name": f"MLB Game Previews - {date}",
        "description": f"Complete list of MLB betting previews for {date}",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": blog['url'],
                "name": blog['matchup'],
                "description": blog.get('description', '')
            }
            for i, blog in enumerate(blog_index)
        ]
    }

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
    """Generate all blogs for today with comprehensive SEO metadata"""
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
        
        # Create SEO-friendly slug with proper date
        slug = create_slug(game_data['matchup'], game_data.get('game_time'), date_str)
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
            
            # Add internal links with smart scaling
            print("  🔗 Adding internal links...")
            optimized_post = auto_link_blog_content(optimized_post, max_links=8)  # Increased cap
            
            # Convert to HTML format
            print("  🔄 Converting to HTML format...")
            print(f"  DEBUG: Before conversion - starts with: {optimized_post[:50]}")
            html_post = convert_text_to_html(optimized_post)
            print(f"  DEBUG: After conversion - starts with: {html_post[:50]}")
            
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
            
            # Create enhanced metadata with absolute URLs
            meta = {
                "slug": slug,
                "title": f"{game_data['matchup']} MLB Betting Preview - {date_str}",
                "description": f"Expert betting analysis for {game_data['matchup']} on {date_str}. Pitcher arsenal breakdown, lineup projections, and prop betting insights.",
                "matchup": game_data['matchup'],
                "game_time": game_data.get('game_time', 'TBD'),
                "away_team": game_data['away_team'],
                "home_team": game_data['home_team'],
                "away_logo": team_logos['away_logo'],
                "home_logo": team_logos['home_logo'],
                "url": f"https://www.thebettinginsider.com/mlb-blogs/{date_str}/{slug}",
                "generated_at": datetime.now().isoformat(),
                "featured_image": team_logos.get('away_logo', ''),
                "word_count": len(optimized_post.split())
            }
            
            save_to_file(game_directory, "meta.json", json.dumps(meta, indent=2))
            blog_index.append(meta)
            print("  ✅ Enhanced blog metadata saved")
            
            # Save game data for reference
            save_to_file(game_directory, "game_data.json", json.dumps(game_data, indent=2))
            print("  ✅ Game data saved")
            
        except Exception as e:
            print(f"  ❌ Error processing {topic}: {e}")
            continue
    
    # Generate and save ItemList schema for the daily index
    itemlist_schema = generate_itemlist_schema(blog_index, date_str)
    save_to_file(daily_directory, "itemlist_schema.json", json.dumps(itemlist_schema, indent=2))
    
    # Save daily index with enhanced metadata
    save_to_file(daily_directory, "index.json", json.dumps({
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "total_blogs": len(blog_index),
        "blogs": blog_index,
        "itemlist_schema": itemlist_schema
    }, indent=2))
    
    print(f"\n🎉 Completed! Generated {len(blog_topics)} blog posts with enhanced SEO in {daily_directory}")

@app.route('/')
def home():
    """Redirect to today's blog index"""
    today = datetime.now().strftime("%Y-%m-%d")
    return redirect(url_for('blog_index', date=today))

@app.route('/mlb-blogs/<date>')
def blog_index(date):
    """Display index with on-demand game list"""
    
    # Create a simple index page without relying on stored files
    today = datetime.now().strftime("%Y-%m-%d")
    if date != today:
        return f"""
        <html>
        <head><title>No Blogs Found - {date}</title></head>
        <body>
            <h1>No blogs found for {date}</h1>
            <p>Only today's games are available.</p>
            <p><a href="/mlb-blogs/{today}">View today's games</a></p>
        </body>
        </html>
        """, 404
    
    # Create mock games list for today
    games = [
        {'matchup': 'Phillies @ Reds', 'time': '06:10PM', 'slug': 'phi-vs-cin-0610pm-2025-08-11'},
        {'matchup': 'Twins @ Yankees', 'time': '07:05PM', 'slug': 'min-vs-nyy-0705pm-2025-08-11'}, 
        {'matchup': 'Tigers @ White Sox', 'time': '07:40PM', 'slug': 'det-vs-cws-0740pm-2025-08-11'},
        {'matchup': 'Nationals @ Royals', 'time': '07:40PM', 'slug': 'wsh-vs-kc-0740pm-2025-08-11'},
        {'matchup': 'Pirates @ Brewers', 'time': '07:40PM', 'slug': 'pit-vs-mil-0740pm-2025-08-11'},
        {'matchup': 'Rockies @ Cardinals', 'time': '07:45PM', 'slug': 'col-vs-stl-0745pm-2025-08-11'},
        {'matchup': 'Diamondbacks @ Rangers', 'time': '08:05PM', 'slug': 'az-vs-tex-0805pm-2025-08-11'},
        {'matchup': 'Red Sox @ Astros', 'time': '08:10PM', 'slug': 'bos-vs-hou-0810pm-2025-08-11'},
        {'matchup': 'Dodgers @ Angels', 'time': '09:38PM', 'slug': 'lad-vs-laa-0938pm-2025-08-11'},
        {'matchup': 'Padres @ Giants', 'time': '09:38PM', 'slug': 'sd-vs-sf-0938pm-2025-08-11'},
        {'matchup': 'Rays @ Athletics', 'time': '10:05PM', 'slug': 'tb-vs-ath-1005pm-2025-08-11'}
    ]
    
    # Generate HTML index page
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MLB Betting Previews - {date} | The Betting Insider</title>
        <meta name="description" content="Complete MLB game previews for {date}. Expert analysis covering {len(games)} games with pitcher matchups and betting insights.">
        <link rel="canonical" href="{request.url}">
        
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
            .header {{ text-align: center; margin-bottom: 40px; }}
            .header h1 {{ color: #1a365d; margin-bottom: 10px; }}
            .game-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }}
            .game-card {{ border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; background: white; transition: all 0.2s; }}
            .game-card:hover {{ box-shadow: 0 8px 25px rgba(0,0,0,0.1); transform: translateY(-2px); }}
            .matchup {{ font-size: 20px; font-weight: 700; margin-bottom: 12px; color: #1a365d; }}
            .game-time {{ color: #718096; margin-bottom: 15px; font-weight: 500; }}
            .description {{ color: #4a5568; line-height: 1.6; margin-bottom: 15px; }}
            .read-more {{ display: inline-block; margin-top: 10px; color: #3182ce; text-decoration: none; font-weight: 600; }}
            .read-more:hover {{ text-decoration: underline; color: #2c5aa0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏟️ MLB Betting Previews - {date}</h1>
            <p>📊 {len(games)} games analyzed • 🕐 Live generation</p>
        </div>
        <div class="game-grid">
    """
    
    for game in games:
        html += f"""
            <div class="game-card">
                <div class="matchup">{game['matchup']}</div>
                <div class="game-time">⏰ {game['time']}</div>
                <div class="description">Expert betting analysis with pitcher matchups, lineup projections, and prop betting insights.</div>
                <a href="/mlb-blogs/{date}/{game['slug']}" class="read-more">Read Full Analysis →</a>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return Response(html, mimetype='text/html')

@app.route('/mlb-blogs/<date>/<slug>')
def show_blog(date, slug):
    """Generate and display individual blog post on-demand"""
    
    # Extract game info from slug
    # Slug format: "det-vs-cws-0740pm-2025-08-11"
    try:
        # Parse slug to get team info and time
        parts = slug.split('-')
        if len(parts) >= 4:
            away_team_code = parts[0].upper()
            home_team_code = parts[2].upper()  # Skip "vs"
            
            # Map common team codes to full names
            team_map = {
                'DET': 'Tigers', 'CWS': 'White Sox', 'MIN': 'Twins', 'NYY': 'Yankees',
                'PHI': 'Phillies', 'CIN': 'Reds', 'WSH': 'Nationals', 'KC': 'Royals',
                'PIT': 'Pirates', 'MIL': 'Brewers', 'COL': 'Rockies', 'STL': 'Cardinals',
                'AZ': 'Diamondbacks', 'TEX': 'Rangers', 'BOS': 'Red Sox', 'HOU': 'Astros',
                'LAD': 'Dodgers', 'LAA': 'Angels', 'SD': 'Padres', 'SF': 'Giants',
                'TB': 'Rays', 'ATH': 'Athletics'
            }
            
            away_team = team_map.get(away_team_code, away_team_code)
            home_team = team_map.get(home_team_code, home_team_code)
            
            # Create mock game data for blog generation
            game_data = {
                'matchup': f"{away_team} @ {home_team}",
                'away_team': away_team,
                'home_team': home_team,
                'game_time': '7:40 PM',  # Default time
                'game_date': date
            }
            
            # Generate blog content on-demand
            topic = f"{away_team} at {home_team} MLB Betting Preview"
            keywords = f"MLB, {away_team}, {home_team}, betting, preview"
            
            try:
                # Generate the blog post
                blog_post = generate_mlb_blog_post(topic, keywords, game_data)
                
                # Optimize it
                optimized_post = audit_blog_post(blog_post)
                
                # Add internal links
                optimized_post = auto_link_blog_content(optimized_post, max_links=8)
                
                # Convert to HTML - THIS IS THE KEY STEP!
                html_post = convert_text_to_html(optimized_post)
                
                print(f"DEBUG CONVERSION: Before: {optimized_post[:100]}")
                print(f"DEBUG CONVERSION: After: {html_post[:100]}")
                
                # Get team logos
                team_logos = generate_team_logos_for_matchup(away_team, home_team)
                
                # Create meta info
                meta = {
                    'title': f"{away_team} vs {home_team} MLB Betting Preview - {date}",
                    'description': f"Expert betting analysis for {away_team} vs {home_team} on {date}",
                    'matchup': game_data['matchup'],
                    'game_time': game_data.get('game_time', 'TBD'),
                    'away_team': away_team,
                    'home_team': home_team,
                    'away_logo': team_logos['away_logo'],
                    'home_logo': team_logos['home_logo']
                }
                
            except Exception as e:
                # Fallback if blog generation fails
                print(f"Error generating blog: {e}")
                html_post = f"""
                <h1>{away_team} vs {home_team} MLB Betting Preview</h1>
                <p>Game preview for {away_team} at {home_team} on {date}.</p>
                <p>Detailed analysis coming soon...</p>
                """
                meta = {
                    'title': f"{away_team} vs {home_team} MLB Betting Preview",
                    'description': f"MLB game preview for {away_team} vs {home_team}",
                    'away_team': away_team,
                    'home_team': home_team,
                    'away_logo': '',
                    'home_logo': ''
                }
            
        else:
            raise ValueError("Invalid slug format")
            
    except Exception as e:
        print(f"Error parsing slug {slug}: {e}")
        return "<h1>Blog not found</h1><p>Invalid URL format.</p>", 404
    
    # Generate comprehensive schemas
    canonical_url = request.url
    
    # Create simple schemas for the generated content
    enhanced_schemas = [{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": meta['title'],
        "description": meta['description'],
        "datePublished": f"{date}T00:00:00-04:00",
        "author": {
            "@type": "Person",
            "name": "Mike Chen",
            "jobTitle": "Senior MLB Betting Analyst"
        },
        "publisher": {
            "@type": "Organization",
            "name": "The Betting Insider"
        }
    }]
    
    # Pre-calculate meta values
    meta_title = meta['title']
    meta_desc = meta['description']
    featured_image = meta.get('away_logo', '')
    
    # Enhanced SEO meta tags
    seo_meta_html = f"""
    <!-- Enhanced SEO Meta Tags -->
    <meta name="title" content="{meta_title}" />
    <meta name="description" content="{meta_desc}" />
    <link rel="canonical" href="{canonical_url}" />
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article" />
    <meta property="og:url" content="{canonical_url}" />
    <meta property="og:title" content="{meta_title}" />
    <meta property="og:description" content="{meta_desc}" />
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image" />
    <meta property="twitter:title" content="{meta_title}" />
    <meta property="twitter:description" content="{meta_desc}" />
    """
    
    # Team header
    team_meta_html = f"""
    <div class="game-header" style="display: flex; justify-content: space-between; align-items: center; margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 12px;">
        <div class="away-team" style="display: flex; align-items: center; gap: 15px;">
            <span class="team-name" style="font-weight: 700; font-size: 18px; color: #1a365d;">{meta.get('away_team', '')}</span>
        </div>
        <div class="game-info" style="text-align: center;">
            <div class="vs-text" style="font-size: 24px; font-weight: bold; color: #4a5568;">@</div>
            <div class="game-time" style="color: #718096; font-size: 14px;">{meta.get('game_time', 'TBD')}</div>
        </div>
        <div class="home-team" style="display: flex; align-items: center; gap: 15px;">
            <span class="team-name" style="font-weight: 700; font-size: 18px; color: #1a365d;">{meta.get('home_team', '')}</span>
        </div>
    </div>
    """
    
    # JSON-LD schema
    schema_html = f'<script type="application/ld+json">{json.dumps(enhanced_schemas, indent=2)}</script>'
    
    # Generate complete HTML document
    complete_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {seo_meta_html}
    {schema_html}
    <title>{meta_title}</title>
    
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.7; color: #2d3748; }}
        h1 {{ color: #1a365d; font-size: 32px; margin-bottom: 20px; }}
        h2 {{ color: #2c5aa0; font-size: 24px; margin: 30px 0 15px 0; }}
        h3 {{ color: #4a5568; font-size: 20px; margin: 25px 0 10px 0; }}
        h4 {{ color: #4a5568; font-size: 18px; margin: 20px 0 10px 0; }}
        p {{ margin-bottom: 15px; }}
        ul {{ margin: 15px 0; padding-left: 25px; }}
        li {{ margin-bottom: 8px; }}
        a {{ color: #3182ce; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        strong {{ color: #1a365d; }}
    </style>
</head>
<body>
    {team_meta_html}
    
    <!-- Main Blog Content -->
    <article>
        {html_post}
    </article>
</body>
</html>"""
    
    return Response(complete_html, mimetype='text/html')

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
    print("🚀 Initializing Enhanced MLB Blog Service")
    
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
    print("✅ Enhanced blog generation started in background")

if __name__ == '__main__':
    initialize_app()
    
    # Start Flask web server immediately
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
