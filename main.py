# main.py (Enhanced Web Service Version)
import os
import threading
import time
import schedule
import logging
import uuid
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin
import json
import re
from typing import Dict, List, Optional

from flask import Flask, Response, render_template, redirect, url_for, request
import mistune
from bs4 import BeautifulSoup
import pytz

from generate_blog_post import generate_mlb_blog_post
from generate_image import generate_team_logos_for_matchup
from mlb_data_fetcher import MLBDataFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
BASE_URL = os.environ.get('BASE_URL', 'https://www.thebettinginsider.com')
TIMEZONE = pytz.timezone('US/Eastern')

# Request ID middleware
@app.before_request
def before_request():
    request.request_id = str(uuid.uuid4())[:8]

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        try:
            record.request_id = getattr(request, 'request_id', 'system')
        except RuntimeError:
            # Handle startup/no request context
            record.request_id = 'system'
        return True

# Add filter to all handlers
for handler in logging.root.handlers:
    handler.addFilter(RequestIdFilter())

# Initialize markdown parser
markdown = mistune.create_markdown(
    escape=False,
    plugins=['strikethrough', 'footnotes', 'table']
)

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

def auto_link_blog_content_safe(html_content: str, max_links: int = 5) -> str:
    """Safely insert internal links using HTML parser to avoid breaking existing links"""
    if not html_content or max_links <= 0:
        return html_content
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        links_inserted = 0
        
        # Sort phrases by length (longest first) to avoid partial matching
        sorted_phrases = sorted(INTERLINK_MAP.keys(), key=len, reverse=True)
        
        for phrase in sorted_phrases:
            if links_inserted >= max_links:
                break
                
            url = INTERLINK_MAP[phrase]
            
            # Find all text nodes that aren't inside links, headings, or script tags
            for element in soup.find_all(string=True):
                if links_inserted >= max_links:
                    break
                    
                # Skip if parent is a link, heading, script, or style tag
                if element.parent.name in ['a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'script', 'style']:
                    continue
                
                # Check if phrase exists in this text node (case-insensitive)
                text = str(element)
                pattern = r'\b' + re.escape(phrase) + r'\b'
                match = re.search(pattern, text, re.IGNORECASE)
                
                if match:
                    # Replace the text with linked version
                    matched_text = match.group()
                    # Add rel="nofollow" for promotional links
                    rel_attr = ' rel="nofollow"' if 'thebettinginsider.com' in url else ''
                    new_text = re.sub(
                        pattern, 
                        f'<a href="{url}"{rel_attr}>{matched_text}</a>', 
                        text, 
                        count=1, 
                        flags=re.IGNORECASE
                    )
                    
                    # Replace the text node with new HTML
                    new_soup = BeautifulSoup(new_text, 'html.parser')
                    element.replace_with(new_soup)
                    links_inserted += 1
                    logger.info(f"Added internal link: '{matched_text}' -> {url}")
                    break  # Move to next phrase
        
        if links_inserted > 0:
            logger.info(f"Total internal links added: {links_inserted}")
        
        return str(soup)
        
    except Exception as e:
        logger.error(f"Error in auto_link_blog_content_safe: {e}")
        return html_content

def save_to_file(directory: str, filename: str, content: str):
    """Save content to file with error handling"""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(os.path.join(directory, filename), 'w', encoding='utf-8') as file:
            file.write(content)
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")

def create_slug(matchup: str, game_time: str, game_id: str = None) -> str:
    """Create SEO-friendly slug with game_id fallback to avoid collisions"""
    # Clean the matchup: "Yankees @ Red Sox" -> "yankees-vs-red-sox"
    slug = matchup.lower().replace(' @ ', '-vs-').replace(' ', '-')
    
    # Normalize time using proper parsing
    if game_time and game_time != 'TBD':
        normalized_time = parse_and_normalize_time(game_time)
        if normalized_time:
            slug += f"-{normalized_time}"
    
    # Add game_id fallback to prevent collisions
    if game_id:
        slug += f"-{game_id}"
    
    # Remove special characters and ensure valid slug
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    slug = re.sub(r'-+', '-', slug)  # Multiple dashes -> single dash
    return slug.strip('-')

def parse_and_normalize_time(time_str: str) -> Optional[str]:
    """Parse game time string and normalize to HHMM format"""
    if not time_str or time_str == 'TBD':
        return None
    
    try:
        # Remove emojis and extra whitespace
        clean_time = re.sub(r'[🕐⏰]', '', time_str).strip()
        
        # Handle format like "7/8, 06:40PM" or just "06:40PM"
        if ',' in clean_time:
            time_part = clean_time.split(',')[1].strip()
        else:
            time_part = clean_time.strip()
        
        # Parse using datetime for robust handling
        for fmt in ['%I:%M%p', '%I:%M %p', '%H:%M']:
            try:
                dt = datetime.strptime(time_part.upper().replace(' ', ''), fmt)
                # Convert to 24-hour format HHMM
                return dt.strftime('%H%M')
            except ValueError:
                continue
                
        logger.warning(f"Could not parse time: '{time_str}'")
        return None
        
    except Exception as e:
        logger.error(f"Error parsing time '{time_str}': {e}")
        return None

def parse_game_time_for_sorting(time_str: str) -> int:
    """Parse game time for proper chronological sorting"""
    normalized = parse_and_normalize_time(time_str)
    return int(normalized) if normalized else 9999

def generate_enhanced_schema(game_data: dict, blog_result: dict, slug: str, date_str: str, absolute_url: str) -> List[dict]:
    """Generate comprehensive JSON-LD schema with multiple entities"""
    
    schemas = []
    
    # 1. NewsArticle/Article Schema
    article_schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": blog_result.get('meta_title', f"{game_data['matchup']} Preview"),
        "description": blog_result.get('meta_desc', ''),
        "datePublished": f"{date_str}T00:00:00-04:00",  # EDT timezone
        "dateModified": f"{date_str}T00:00:00-04:00",
        "author": {
            "@type": "Person",
            "name": "MLB Analytics Team",
            "jobTitle": "Sports Analyst"
        },
        "publisher": {
            "@type": "Organization",
            "name": "The Betting Insider",
            "url": BASE_URL,
            "logo": {
                "@type": "ImageObject",
                "url": f"{BASE_URL}/logo.png"
            }
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": absolute_url
        },
        "url": absolute_url,
        "articleSection": "Sports",
        "keywords": f"MLB, {game_data.get('away_team', '')}, {game_data.get('home_team', '')}, baseball, preview, betting",
        "about": [
            {
                "@type": "SportsTeam",
                "name": game_data.get('away_team', ''),
                "sport": "Baseball"
            },
            {
                "@type": "SportsTeam", 
                "name": game_data.get('home_team', ''),
                "sport": "Baseball"
            }
        ]
    }
    
    # Add image if available
    if game_data.get('away_logo') or game_data.get('home_logo'):
        article_schema["image"] = {
            "@type": "ImageObject",
            "url": game_data.get('away_logo', game_data.get('home_logo', '')),
            "width": 400,
            "height": 300
        }
    
    schemas.append(article_schema)
    
    # 2. SportsEvent Schema
    if game_data.get('game_time') and game_data['game_time'] != 'TBD':
        try:
            # Parse game time to create proper startDate
            game_datetime = datetime.strptime(f"{date_str} {game_data['game_time']}", "%Y-%m-%d %I:%M%p")
            game_datetime = TIMEZONE.localize(game_datetime)
            
            sports_event_schema = {
                "@context": "https://schema.org",
                "@type": "SportsEvent",
                "name": game_data['matchup'],
                "startDate": game_datetime.isoformat(),
                "sport": "Baseball",
                "competitor": [
                    {
                        "@type": "SportsTeam",
                        "name": game_data.get('away_team', ''),
                        "sport": "Baseball"
                    },
                    {
                        "@type": "SportsTeam",
                        "name": game_data.get('home_team', ''),
                        "sport": "Baseball"
                    }
                ],
                "location": {
                    "@type": "Place",
                    "name": f"{game_data.get('home_team', '')} Stadium"
                }
            }
            schemas.append(sports_event_schema)
            
        except Exception as e:
            logger.warning(f"Could not create SportsEvent schema: {e}")
    
    # 3. FAQPage Schema
    if blog_result.get('faq') and len(blog_result['faq']) > 0:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        for faq_item in blog_result['faq']:
            faq_schema["mainEntity"].append({
                "@type": "Question",
                "name": faq_item.get('question', ''),
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq_item.get('answer', '')
                }
            })
        
        schemas.append(faq_schema)
    
    return schemas

def generate_daily_blogs():
    """Generate all blogs for today with enhanced SEO and error handling"""
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"Starting daily blog generation - Request ID: {request_id}")
    
    try:
        # Initialize MLB data fetcher
        mlb_fetcher = MLBDataFetcher()
        
        # Get today's games as blog topics
        blog_topics = mlb_fetcher.get_blog_topics_from_games()
        
        if not blog_topics:
            logger.warning("No games available for blog generation")
            return
        
        # Sort by game time
        logger.info(f"Sorting {len(blog_topics)} games by time...")
        blog_topics.sort(key=lambda x: parse_game_time_for_sorting(x['game_data'].get('game_time', 'TBD')))
        
        base_directory = "mlb_blog_posts"
        date_str = datetime.now().strftime("%Y-%m-%d")
        daily_directory = os.path.join(base_directory, date_str)
        
        if not os.path.exists(daily_directory):
            os.makedirs(daily_directory)
        
        logger.info(f"Generating {len(blog_topics)} MLB blog posts for {date_str}")
        
        blog_index = []  # Store metadata for index page
        
        for i, blog_topic in enumerate(blog_topics, 1):
            topic = blog_topic['topic']
            keywords = blog_topic['keywords']
            game_data = blog_topic['game_data']
            game_id = game_data.get('game_id', str(uuid.uuid4())[:8])
            
            logger.info(f"Processing game {i}/{len(blog_topics)}: {game_data['matchup']}")
            
            # Create SEO-friendly slug with game_id fallback
            slug = create_slug(game_data['matchup'], game_data.get('game_time'), game_id)
            game_directory = os.path.join(daily_directory, slug)
            absolute_url = urljoin(BASE_URL, f"/mlb-blogs/{date_str}/{slug}")
            
            try:
                # Generate MLB-specific blog post (now returns structured data)
                logger.info("Generating blog post with enhanced structure...")
                blog_result = generate_mlb_blog_post(topic, keywords, game_data)
                
                if not isinstance(blog_result, dict):
                    logger.error(f"Blog generation returned invalid format for {topic}")
                    continue
                
                # Save original structured result
                save_to_file(game_directory, "blog_result.json", json.dumps(blog_result, indent=2))
                
                # Get HTML content for processing
                html_content = blog_result.get('html', '')
                if not html_content:
                    logger.error(f"No HTML content generated for {topic}")
                    continue
                
                # Convert to proper HTML using markdown parser
                if html_content.startswith('#') or '\n#' in html_content:
                    # Looks like markdown, convert it
                    html_content = markdown(html_content)
                
                # Skip audit step - use content directly
                logger.info("Processing content...")
                optimized_post = html_content
                
                # Add internal links safely
                logger.info("Adding internal links...")
                optimized_post = auto_link_blog_content_safe(optimized_post)
                
                save_to_file(game_directory, "optimized_post.html", optimized_post)
                
                # Generate team logos
                logger.info("Getting team logos...")
                away_team = game_data.get('away_team', '')
                home_team = game_data.get('home_team', '')
                team_logos = generate_team_logos_for_matchup(away_team, home_team)
                
                # Update game_data with logo info
                game_data.update({
                    'away_logo': team_logos['away_logo'],
                    'home_logo': team_logos['home_logo']
                })
                
                save_to_file(game_directory, "team_logos.json", json.dumps(team_logos, indent=2))
                
                # Generate comprehensive schema
                logger.info("Generating comprehensive SEO schema...")
                schemas = generate_enhanced_schema(game_data, blog_result, slug, date_str, absolute_url)
                save_to_file(game_directory, "schemas.json", json.dumps(schemas, indent=2))
                
                # Create metadata for this blog
                meta = {
                    "slug": slug,
                    "title": blog_result.get('meta_title', f"{game_data['matchup']} Preview"),
                    "description": blog_result.get('meta_desc', ''),
                    "matchup": game_data['matchup'],
                    "game_time": game_data.get('game_time', 'TBD'),
                    "away_team": away_team,
                    "home_team": home_team,
                    "away_logo": team_logos['away_logo'],
                    "home_logo": team_logos['home_logo'],
                    "url": f"/mlb-blogs/{date_str}/{slug}",
                    "absolute_url": absolute_url,
                    "generated_at": datetime.now().isoformat(),
                    "faq_count": len(blog_result.get('faq', [])),
                    "citations_count": len(blog_result.get('citations', []))
                }
                
                save_to_file(game_directory, "meta.json", json.dumps(meta, indent=2))
                blog_index.append(meta)
                
                # Save enhanced game data
                save_to_file(game_directory, "game_data.json", json.dumps(game_data, indent=2))
                
                logger.info(f"✅ Successfully processed {topic}")
                
            except Exception as e:
                logger.error(f"Error processing {topic}: {e}", exc_info=True)
                continue
        
        # Save daily index with enhanced metadata
        daily_meta = {
            "date": date_str,
            "generated_at": datetime.now().isoformat(),
            "total_blogs": len(blog_index),
            "successful_blogs": len([b for b in blog_index if b]),
            "blogs": blog_index,
            "archive_url": f"/mlb-blogs/{date_str}",
            "sitemap_urls": [b["absolute_url"] for b in blog_index]
        }
        
        save_to_file(daily_directory, "index.json", json.dumps(daily_meta, indent=2))
        
        logger.info(f"✅ Completed! Generated {len(blog_index)} blog posts in {daily_directory}")
        
    except Exception as e:
        logger.error(f"Daily blog generation failed: {e}", exc_info=True)

@app.route('/')
def home():
    """Redirect to today's blog index"""
    today = datetime.now().strftime("%Y-%m-%d")
    return redirect(url_for('blog_index', date=today))

@app.route('/mlb-blogs/')
def blog_archive():
    """Display archive of all available dates"""
    base_dir = "mlb_blog_posts"
    if not os.path.exists(base_dir):
        return render_archive_template([], "No blog archives found yet.")
    
    # Get all available dates
    dates = []
    for item in os.listdir(base_dir):
        date_path = os.path.join(base_dir, item)
        if os.path.isdir(date_path) and re.match(r'\d{4}-\d{2}-\d{2}', item):
            # Load index to get metadata
            index_file = os.path.join(date_path, "index.json")
            if os.path.exists(index_file):
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                    dates.append({
                        'date': item,
                        'total_blogs': index_data.get('total_blogs', 0),
                        'url': f'/mlb-blogs/{item}'
                    })
                except Exception as e:
                    logger.warning(f"Could not load index for {item}: {e}")
    
    # Sort by date (newest first)
    dates.sort(key=lambda x: x['date'], reverse=True)
    
    return render_archive_template(dates, f"MLB Blog Archives - {len(dates)} days available")

def render_archive_template(dates: List[dict], title: str) -> str:
    """Render archive page template"""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <meta name="description" content="Browse MLB game previews and analysis by date. Daily expert insights and betting analysis.">
        <link rel="canonical" href="{BASE_URL}/mlb-blogs/">
        <meta property="og:title" content="{title}">
        <meta property="og:description" content="Browse MLB game previews and analysis by date.">
        <meta property="og:type" content="website">
        <meta property="og:url" content="{BASE_URL}/mlb-blogs/">
        <meta name="twitter:card" content="summary">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .date-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }}
            .date-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; text-align: center; }}
            .date-card:hover {{ box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .date-card a {{ text-decoration: none; color: #333; }}
            .date-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
            .date-stats {{ color: #666; }}
            nav {{ margin-bottom: 20px; }}
            nav a {{ margin-right: 15px; color: #007bff; }}
        </style>
    </head>
    <body>
        <nav>
            <a href="/">← Home</a>
            <a href="/mlb-blogs/">Archive</a>
            <a href="/sitemap.xml">Sitemap</a>
        </nav>
        
        <main>
            <div class="header">
                <h1>🏟️ {title}</h1>
            </div>
            
            <div class="date-grid">
    """
    
    if dates:
        for date_info in dates:
            date_obj = datetime.strptime(date_info['date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%B %d, %Y')
            html += f"""
                <div class="date-card">
                    <a href="{date_info['url']}">
                        <div class="date-title">{formatted_date}</div>
                        <div class="date-stats">{date_info['total_blogs']} games</div>
                    </a>
                </div>
            """
    else:
        html += "<p>No blog archives found yet. Check back later!</p>"
    
    html += """
            </div>
        </main>
    </body>
    </html>
    """
    
    return html

@app.route('/mlb-blogs/<date>')
def blog_index(date):
    """Display index of all blogs for a specific date with enhanced SEO"""
    blog_dir = f"mlb_blog_posts/{date}"
    index_file = os.path.join(blog_dir, "index.json")
    
    if not os.path.exists(index_file):
        return f"""
        <html>
        <head>
            <title>No Blogs Found - {date}</title>
            <meta name="robots" content="noindex">
        </head>
        <body>
            <nav><a href="/mlb-blogs/">← Archive</a></nav>
            <main>
                <h1>No blogs found for {date}</h1>
                <p>Blogs may still be generating...</p>
                <p><a href="/generate">Trigger manual generation</a></p>
            </main>
        </body>
        </html>
        """, 404
    
    with open(index_file, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    
    # Enhanced HTML index page
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%B %d, %Y')
    canonical_url = f"{BASE_URL}/mlb-blogs/{date}"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MLB Games - {formatted_date} | {index_data['total_blogs']} Game Previews</title>
        <meta name="description" content="Expert MLB analysis for {formatted_date}. {index_data['total_blogs']} game previews with betting insights, pitcher matchups, and key stats.">
        <link rel="canonical" href="{canonical_url}">
        
        <!-- Open Graph -->
        <meta property="og:title" content="MLB Games - {formatted_date}">
        <meta property="og:description" content="{index_data['total_blogs']} expert game previews with betting analysis">
        <meta property="og:type" content="website">
        <meta property="og:url" content="{canonical_url}">
        
        <!-- Twitter Card -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="MLB Games - {formatted_date}">
        <meta name="twitter:description" content="{index_data['total_blogs']} expert game previews">
        
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .game-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }}
            .game-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; }}
            .game-card:hover {{ box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
            .matchup {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
            .game-time {{ color: #666; margin-bottom: 10px; }}
            .teams {{ display: flex; align-items: center; gap: 10px; margin: 10px 0; }}
            .team-logo {{ width: 32px; height: 32px; loading: lazy; decoding: async; }}
            .description {{ color: #555; line-height: 1.5; margin-bottom: 15px; }}
            .stats {{ font-size: 12px; color: #777; margin-bottom: 10px; }}
            .read-more {{ display: inline-block; color: #007bff; text-decoration: none; font-weight: bold; }}
            .read-more:hover {{ text-decoration: underline; }}
            nav {{ margin-bottom: 20px; }}
            nav a {{ margin-right: 15px; color: #007bff; text-decoration: none; }}
            nav a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <nav>
            <a href="/mlb-blogs/">← Archive</a>
            <a href="/">Home</a>
        </nav>
        
        <main>
            <div class="header">
                <h1>🏟️ MLB Games - {formatted_date}</h1>
                <p>📊 {index_data['total_blogs']} games • 🕐 Updated {index_data['generated_at'][:19].replace('T', ' ')}</p>
            </div>
            
            <div class="game-grid">
    """
    
    for blog in index_data['blogs']:
        html += f"""
            <article class="game-card">
                <div class="matchup">{blog['matchup']}</div>
                <div class="game-time">⏰ {blog['game_time']}</div>
                <div class="teams">
                    <img src="{blog['away_logo']}" alt="{blog['away_team']} logo" class="team-logo" width="32" height="32" loading="lazy" decoding="async" onerror="this.style.display='none'">
                    <span>@</span>
                    <img src="{blog['home_logo']}" alt="{blog['home_team']} logo" class="team-logo" width="32" height="32" loading="lazy" decoding="async" onerror="this.style.display='none'">
                </div>
                <div class="description">{blog['description'][:120]}...</div>
                <div class="stats">📝 {blog.get('faq_count', 0)} FAQs • 🔗 {blog.get('citations_count', 0)} Sources</div>
                <a href="{blog['url']}" class="read-more">Read Full Preview →</a>
            </article>
        """
    
    html += """
            </div>
        </main>
    </body>
    </html>
    """
    
    return html

@app.route('/mlb-blogs/<date>/<slug>')
def show_blog(date, slug):
    """Display individual blog post with comprehensive SEO"""
    folder_path = f"mlb_blog_posts/{date}/{slug}"
    content_path = os.path.join(folder_path, "optimized_post.html")
    schemas_path = os.path.join(folder_path, "schemas.json")
    meta_path = os.path.join(folder_path, "meta.json")
    blog_result_path = os.path.join(folder_path, "blog_result.json")
    
    if not os.path.exists(content_path):
        return "<h1>Blog not found</h1>", 404
    
    # Load all data
    with open(content_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    schemas = []
    if os.path.exists(schemas_path):
        with open(schemas_path, 'r', encoding='utf-8') as f:
            schemas = json.load(f)
    
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    blog_result = {}
    if os.path.exists(blog_result_path):
        with open(blog_result_path, 'r', encoding='utf-8') as f:
            blog_result = json.load(f)
    
    # Generate comprehensive HTML page
    title = meta.get('title', f"MLB: {meta.get('matchup', 'Game Preview')}")
    description = meta.get('description', '')[:160]
    canonical_url = meta.get('absolute_url', f"{BASE_URL}/mlb-blogs/{date}/{slug}")
    
    # Generate Open Graph image URL (could be team logos composite)
    og_image = meta.get('away_logo', f"{BASE_URL}/default-mlb-preview.png")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <meta name="description" content="{description}">
        <link rel="canonical" href="{canonical_url}">
        
        <!-- Open Graph -->
        <meta property="og:title" content="{title}">
        <meta property="og:description" content="{description}">
        <meta property="og:type" content="article">
        <meta property="og:url" content="{canonical_url}">
        <meta property="og:image" content="{og_image}">
        
        <!-- Twitter Card -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="{title}">
        <meta name="twitter:description" content="{description}">
        <meta name="twitter:image" content="{og_image}">
        
        <!-- JSON-LD Schemas -->
    """
    
    # Add all schemas
    for schema in schemas:
        html += f"""
        <script type="application/ld+json">
        {json.dumps(schema, indent=2)}
        </script>"""
    
    html += f"""
        
        <style>
            body {{ font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            h3 {{ color: #555; }}
            .meta {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .teams {{ display: flex; align-items: center; gap: 15px; margin: 20px 0; }}
            .team {{ display: flex; align-items: center; gap: 10px; }}
            .team-logo {{ width: 40px; height: 40px; loading: lazy; decoding: async; }}
            .back-link {{ margin: 20px 0; }}
            .back-link a {{ color: #3498db; text-decoration: none; }}
            .back-link a:hover {{ text-decoration: underline; }}
            .faq-section {{ background: #f9f9f9; padding: 20px; border-radius: 5px; margin: 30px 0; }}
            .faq-item {{ margin-bottom: 15px; }}
            .faq-question {{ font-weight: bold; margin-bottom: 5px; }}
            .faq-answer {{ color: #555; }}
            .citations {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }}
            .citations h3 {{ color: #666; }}
            .citations ul {{ list-style-type: none; padding: 0; }}
            .citations li {{ margin-bottom: 5px; }}
            .citations a {{ color: #007bff; }}
            nav {{ margin-bottom: 20px; }}
            nav a {{ color: #3498db; text-decoration: none; margin-right: 15px; }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <nav>
            <a href="/mlb-blogs/{date}">← Back to {date} Games</a>
            <a href="/mlb-blogs/">Archive</a>
            <a href="/">Home</a>
        </nav>
        
        <main>
            <div class="meta">
                <div class="teams">
                    <div class="team">
                        <img src="{meta.get('away_logo', '')}" alt="{meta.get('away_team', '')} logo" class="team-logo" width="40" height="40" loading="lazy" decoding="async" onerror="this.style.display='none'">
                        <strong>{meta.get('away_team', '')}</strong>
                    </div>
                    <span>@</span>
                    <div class="team">
                        <img src="{meta.get('home_logo', '')}" alt="{meta.get('home_team', '')} logo" class="team-logo" width="40" height="40" loading="lazy" decoding="async" onerror="this.style.display='none'">
                        <strong>{meta.get('home_team', '')}</strong>
                    </div>
                </div>
                <div>🕐 Game Time: {meta.get('game_time', 'TBD')}</div>
            </div>
            
            <article>
                {html_content}
            </article>
    """
    
    # Add FAQ section if available
    if blog_result.get('faq'):
        html += '''
            <div class="faq-section">
                <h2>Frequently Asked Questions</h2>
        '''
        for faq_item in blog_result['faq']:
            html += f'''
                <div class="faq-item">
                    <div class="faq-question">{faq_item.get('question', '')}</div>
                    <div class="faq-answer">{faq_item.get('answer', '')}</div>
                </div>
            '''
        html += '</div>'
    
    # Add citations if available
    if blog_result.get('citations'):
        html += '''
            <div class="citations">
                <h3>Sources & References</h3>
                <ul>
        '''
        for citation in blog_result['citations']:
            html += f'''
                <li><a href="{citation.get('url', '#')}" target="_blank" rel="nofollow">{citation.get('source', 'Source')}</a></li>
            '''
        html += '''
                </ul>
            </div>
        '''
    
    html += f"""
        </main>
        
        <nav>
            <a href="/mlb-blogs/{date}">← Back to {date} Games</a>
        </nav>
    </body>
    </html>
    """
    
    return html

@app.route('/sitemap.xml')
def sitemap():
    """Generate XML sitemap for all blog posts"""
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'''
    
    # Add main pages
    xml += f'''
    <url>
        <loc>{BASE_URL}/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{BASE_URL}/mlb-blogs/</loc>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>'''
    
    # Add all blog posts
    base_dir = "mlb_blog_posts"
    if os.path.exists(base_dir):
        for date_dir in os.listdir(base_dir):
            date_path = os.path.join(base_dir, date_dir)
            if os.path.isdir(date_path) and re.match(r'\d{4}-\d{2}-\d{2}', date_dir):
                # Add date index
                xml += f'''
    <url>
        <loc>{BASE_URL}/mlb-blogs/{date_dir}</loc>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>'''
                
                # Add individual posts
                index_file = os.path.join(date_path, "index.json")
                if os.path.exists(index_file):
                    try:
                        with open(index_file, 'r', encoding='utf-8') as f:
                            index_data = json.load(f)
                        
                        for blog in index_data.get('blogs', []):
                            xml += f'''
    <url>
        <loc>{blog.get('absolute_url', '')}</loc>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>'''
                    except Exception as e:
                        logger.warning(f"Could not process sitemap for {date_dir}: {e}")
    
    xml += '\n</urlset>'
    
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    """Generate robots.txt"""
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""
    return Response(robots_txt, mimetype='text/plain')

@app.route('/generate')
def manual_generate():
    """Manual trigger to generate blogs"""
    logger.info("Manual blog generation triggered")
    
    # Run in background thread to avoid timeout
    def background_generate():
        generate_daily_blogs()
    
    thread = threading.Thread(target=background_generate, daemon=True)
    thread.start()
    
    return "Blog generation triggered! Check back in a few minutes."

@app.route('/health')
def health():
    """Enhanced health check"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'timezone': str(TIMEZONE),
        'base_url': BASE_URL
    }

def run_scheduler():
    """Run daily blog generation at 7 AM EDT"""
    schedule.every().day.at("11:00").do(generate_daily_blogs)  # 11:00 UTC = 7:00 AM EDT
    
    logger.info("Scheduler started - will generate daily at 7 AM EDT")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def initialize_app():
    """Initialize with enhanced error handling and background processes"""
    logger.info("Initializing Enhanced MLB Blog Service")
    
    try:
        # Start background scheduler
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("✅ Background scheduler started")
        
        # Generate blogs in background after Flask starts
        def delayed_blog_generation():
            time.sleep(10)  # Wait for Flask to fully start
            try:
                generate_daily_blogs()
            except Exception as e:
                logger.error(f"Initial blog generation failed: {e}")
        
        blog_thread = threading.Thread(target=delayed_blog_generation, daemon=True)
        blog_thread.start()
        logger.info("✅ Initial blog generation started in background")
        
    except Exception as e:
        logger.error(f"Initialization error: {e}")

if __name__ == '__main__':
    initialize_app()
    
    # Start Flask web server
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🌐 Starting Enhanced Flask server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
