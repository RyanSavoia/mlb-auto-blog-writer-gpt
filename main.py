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
        
        print(f"\n📝 Processing game {i}/{len(blog_topics)}: {game_data['matchup']}")
        
        # Create directory for the specific game
        safe_matchup = game_data['matchup'].replace(' @ ', '_vs_').replace(' ', '_')
        random_hash = uuid.uuid4().hex[:8]
        game_directory = os.path.join(daily_directory, f"{safe_matchup}_{random_hash}")
        
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
        # Get all game folders
        for folder in os.listdir(blog_dir):
            folder_path = os.path.join(blog_dir, folder)
            if os.path.isdir(folder_path):
                optimized_file = os.path.join(folder_path, "optimized_post.txt")
                if os.path.exists(optimized_file):
                    with open(optimized_file, 'r', encoding='utf-8') as f:
                        blog_content = f.read()
                        all_blogs.append(blog_content)
    
    if not all_blogs:
        return f"<h1>No blogs found for {today}</h1><p>Blogs may still be generating...</p>"
    
    # Stack all blogs with separators
    combined_blogs = "\n\n" + "="*50 + "\n\n"
    combined_blogs += f"\n\n" + "="*50 + "\n\n".join(all_blogs)
    
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
    """Run daily blog generation at 6 AM ET"""
    schedule.every().day.at("11:00").do(generate_daily_blogs)  # 11:00 UTC = 6:00 AM ET
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def initialize_app():
    """Initialize with Flask server first, then generate blogs in background"""
    print("🚀 Initializing MLB Blog Service")
    
    # Start background scheduler
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Background scheduler started - will generate daily at 6 AM ET")
    
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
