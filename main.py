# main.py (Web Service Version)
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

app = Flask(__name__)

def save_to_file(directory, filename, content):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(os.path.join(directory, filename), 'w', encoding='utf-8') as file:
        file.write(content)

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
    """Generate all blogs for today - same as your current main.py"""
    print(f"🚀 Starting daily blog generation at {datetime.now()}")
    
    # Initialize MLB data fetcher
    mlb_fetcher = MLBDataFetcher()
    
    # Get today's games as blog topics
    blog_topics = mlb_fetcher.get_blog_topics_from_games()
    
    if not blog_topics:
        print("❌ No games available for blog generation")
        return
    
    # ✅ FIXED: Use proper time-based sorting instead of alphabetical
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
    
    for i, blog_topic in enumerate(blog_topics, 1):
        topic = blog_topic['topic']
        keywords = blog_topic['keywords']
        game_data = blog_topic['game_data']
        
        print(f"\n📝 Processing game {i}/{len(blog_topics)}: {game_data['matchup']} at {game_data.get('game_time', 'TBD')}")
        
        # ✅ FIXED: Add time-based prefix to preserve order in filesystem
        time_prefix = f"{i:02d}_"  # 01_, 02_, 03_, etc.
        safe_matchup = game_data['matchup'].replace(' @ ', '_vs_').replace(' ', '_')
        random_hash = uuid.uuid4().hex[:8]
        game_directory = os.path.join(daily_directory, f"{time_prefix}{safe_matchup}_{random_hash}")
        
        try:
            # Generate MLB-specific blog post
            print("  🤖 Generating blog post with GPT-4...")
            blog_post = generate_mlb_blog_post(topic, keywords, game_data)
            save_to_file(game_directory, "original_post.txt", blog_post)
            print(f"  ✅ Generated blog post ({len(blog_post)} characters)")
            
            # Audit and optimize blog post
            print("  🔍 Optimizing for readability...")
            optimized_post = audit_blog_post(blog_post)
            save_to_file(game_directory, "optimized_post.txt", optimized_post)
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
            
            # Save game data for reference
            save_to_file(game_directory, "game_data.json", json.dumps(game_data, indent=2))
            print("  ✅ Game data saved")
            
        except Exception as e:
            print(f"  ❌ Error processing {topic}: {e}")
            continue
    
    print(f"\n🎉 Completed! Generated {len(blog_topics)} blog posts in {daily_directory}")

@app.route('/')
def display_blogs():
    """Display all today's blogs stacked on top of each other"""
    today = datetime.now().strftime("%Y-%m-%d")
    blog_dir = f"mlb_blog_posts/{today}"
    
    all_blogs = []
    
    if os.path.exists(blog_dir):
        # ✅ FIXED: Sort folders to preserve chronological order
        folders = sorted([f for f in os.listdir(blog_dir) if os.path.isdir(os.path.join(blog_dir, f))])
        print(f"📁 Found {len(folders)} blog folders in chronological order")
        
        for folder in folders:
            folder_path = os.path.join(blog_dir, folder)
            optimized_file = os.path.join(folder_path, "optimized_post.txt")
            if os.path.exists(optimized_file):
                with open(optimized_file, 'r', encoding='utf-8') as f:
                    blog_content = f.read()
                    all_blogs.append(blog_content)
                    print(f"  ✅ Loaded: {folder}")
    
    if not all_blogs:
        return f"<h1>No blogs found for {today}</h1><p>Blogs may still be generating...</p>"
    
    # Stack all blogs with separators
    combined_blogs = f"📅 MLB BLOG POSTS FOR {today.upper()}\n"
    combined_blogs += f"🕐 Generated at: {datetime.now().strftime('%I:%M %p ET')}\n"
    combined_blogs += f"📊 Total Games: {len(all_blogs)}\n"
    combined_blogs += "\n" + "="*80 + "\n\n"
    combined_blogs += f"\n\n" + "="*80 + "\n\n".join(all_blogs)
    
    # Return as plain text (just like your current blogs look)
    return Response(combined_blogs, mimetype='text/plain')

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
