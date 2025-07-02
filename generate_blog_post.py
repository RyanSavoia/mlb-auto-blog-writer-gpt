# generate_blog_post.py
from config import OPENAI_API_KEY
from mlb_prompts import get_random_mlb_blog_post_prompt
from openai import OpenAI
import json

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_mlb_blog_post(topic, keywords, game_data):
    """Generate MLB-specific blog post using game data"""
    prompt_template = get_random_mlb_blog_post_prompt()

    # ✅ NEW: Send raw JSON to Claude/GPT for accuracy
    game_info = json.dumps(game_data, indent=2)

    prompt = prompt_template.format(
        topic=topic, 
        keywords=", ".join(keywords),
        game_data=game_info
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a professional MLB betting analyst and blog writer who specializes in pitcher-batter matchups and umpire analysis. Write engaging, data-driven content for baseball fans and bettors."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=4096,
        temperature=0.7
    )

    return response.choices[0].message.content


# Keep the original function for backward compatibility
def generate_blog_post(topic, keywords):
    """Original function - kept for compatibility"""
    return generate_mlb_blog_post(topic, keywords, {})


if __name__ == "__main__":
    # Test the function
    print("Testing MLB blog post generation...")
    test_topic = "Yankees vs Red Sox MLB Betting Preview"
    test_keywords = ["yankees", "red sox", "mlb betting"]
    test_game_data = {
        'matchup': 'Yankees @ Red Sox',
        'away_pitcher': {'name': 'Gerrit Cole', 'arsenal': 'Four-seam fastball (40%, 97.2 mph); Slider (30%, 84.1 mph)'},
        'home_pitcher': {'name': 'Chris Sale', 'arsenal': 'Slider (45%, 84.8 mph); Four-seam fastball (35%, 93.1 mph)'},
        'away_lineup_advantage': 0.025,
        'home_lineup_advantage': -0.018,
        'umpire': 'Angel Hernandez',
        'umpire_k_boost': '1.15x',
        'umpire_bb_boost': '0.92x',
        'away_key_performers': [],
        'home_key_performers': []
    }

    result = generate_mlb_blog_post(test_topic, test_keywords, test_game_data)
    print("Generated blog post preview:")
    print(result[:500] + "..." if len(result) > 500 else result)
