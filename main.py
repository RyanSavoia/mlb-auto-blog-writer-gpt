# main.py
import os
from generate_blog_post import generate_mlb_blog_post
from audit_blog_post import audit_blog_post
from generate_image import generate_image_description, generate_image
from mlb_data_fetcher import MLBDataFetcher
import uuid
import json
from datetime import datetime

def save_to_file(directory, filename, content):
    with open(os.path.join(directory, filename), 'w', encoding='utf-8') as file:
        file.write(content)

def main():
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
        
        if not os.path.exists(game_directory):
            os.makedirs(game_directory)
        
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
            
            # Generate image description
            print("  🎨 Creating image description...")
            image_description = generate_image_description(topic)
            save_to_file(game_directory, "image_description.txt", image_description)
            print("  ✅ Image description generated")
            
            # Generate image
            print("  🖼️ Generating image with DALL-E...")
            image_url = generate_image(image_description)
            save_to_file(game_directory, "image_url.txt", image_url)
            print(f"  ✅ Image generated: {image_url}")
            
            # Save game data for reference
            save_to_file(game_directory, "game_data.json", json.dumps(game_data, indent=2))
            print("  ✅ Game data saved")
            
        except Exception as e:
            print(f"  ❌ Error processing {topic}: {e}")
            continue
    
    print(f"\n🎉 Completed! Generated {len(blog_topics)} blog posts in {daily_directory}")

if __name__ == "__main__":
    main()
