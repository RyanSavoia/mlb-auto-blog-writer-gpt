# generate_blog_post.py
from config import OPENAI_API_KEY
from mlb_prompts import get_mlb_blog_post_prompt
from openai import OpenAI
import json
import time
import hashlib
import logging
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

def truncate_game_data(game_data: dict, max_tokens: int = 2000) -> dict:
    """Truncate game_data text blocks to prevent token overflow"""
    truncated_data = game_data.copy()
    
    # Truncate long text fields that might cause token issues
    text_fields = ['away_pitcher', 'home_pitcher', 'away_key_performers', 'home_key_performers']
    
    for field in text_fields:
        if field in truncated_data and isinstance(truncated_data[field], dict):
            if 'arsenal' in truncated_data[field]:
                arsenal_text = truncated_data[field]['arsenal']
                if len(arsenal_text) > 200:  # Rough token estimation
                    truncated_data[field]['arsenal'] = arsenal_text[:200] + "..."
        elif field in truncated_data and isinstance(truncated_data[field], list):
            # Limit list size
            truncated_data[field] = truncated_data[field][:5]
    
    return truncated_data

def generate_mlb_blog_post_with_retries(topic: str, keywords: List[str], game_data: dict, max_retries: int = 3) -> Optional[dict]:
    """Generate MLB blog post with retry logic and robust error handling"""
    
    # Truncate game data to prevent token overflow
    safe_game_data = truncate_game_data(game_data)
    
    # Get the formatted prompt
    prompt = get_mlb_blog_post_prompt(topic, keywords, safe_game_data)
    
    # Create prompt hash for logging
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
    logger.info(f"Generating blog post with prompt hash: {prompt_hash}")
    
    # Enhanced system prompt with strict requirements
    system_prompt = """You are a professional MLB betting analyst and blog writer who specializes in pitcher-batter matchups and umpire analysis. 

STRICT REQUIREMENTS:
1. Use proper heading hierarchy: <h1> for main title, <h2> for major sections, <h3> for subsections
2. Include a "Key Takeaways" section with 3-5 bullet points
3. Include an FAQ section with 3-6 Q&As at the end
4. Include at least 2 authority citations with <a rel="nofollow"> links to MLB.com, Baseball Savant, or FanGraphs
5. Add byline: "By [Analyst Name] | Reviewed by MLB Analytics Team"
6. Include methodology note: "Analysis based on xBA models and historical data. Do not bet based solely on this article."
7. Echo game time and moneyline exactly once in the intro
8. Return response as JSON with structure: {"html": "...", "meta_title": "...", "meta_desc": "...", "faq": [...], "citations": [...]}

Write engaging, data-driven content for baseball fans and bettors."""

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} for prompt hash: {prompt_hash}")
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096,
                temperature=0.7,
                timeout=60  # 60 second timeout
            )
            
            # Log response ID for debugging
            response_id = getattr(response, 'id', 'unknown')
            logger.info(f"Success! Response ID: {response_id}, Prompt hash: {prompt_hash}")
            
            # Try to parse as JSON first, fallback to plain text
            content = response.choices[0].message.content
            
            try:
                # Attempt to parse as JSON
                parsed_response = json.loads(content)
                
                # Validate required fields
                required_fields = ['html', 'meta_title', 'meta_desc', 'faq', 'citations']
                if all(field in parsed_response for field in required_fields):
                    return parsed_response
                else:
                    logger.warning("JSON response missing required fields, using fallback format")
                    return create_fallback_response(content, topic)
                    
            except json.JSONDecodeError:
                # If not JSON, create structured response
                logger.info("Response not in JSON format, creating structured response")
                return create_fallback_response(content, topic)
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All retry attempts failed for prompt hash: {prompt_hash}")
                raise e
    
    return None

def create_fallback_response(content: str, topic: str) -> dict:
    """Create a structured response when JSON parsing fails"""
    
    # Extract FAQ if present
    faq = []
    if "FAQ" in content or "Frequently Asked" in content:
        # Simple extraction - can be improved
        faq = [
            {"question": "What should I consider before betting?", "answer": "Always do your own research and bet responsibly."},
            {"question": "How accurate are these predictions?", "answer": "These are analytical insights, not guarantees. Past performance doesn't predict future results."}
        ]
    
    # Extract citations if present
    citations = []
    if "MLB.com" in content or "Baseball Savant" in content or "FanGraphs" in content:
        citations = [
            {"source": "MLB.com", "url": "https://mlb.com"},
            {"source": "Baseball Savant", "url": "https://baseballsavant.mlb.com"}
        ]
    
    # Generate meta title and description
    meta_title = topic[:60] + "..." if len(topic) > 60 else topic
    meta_desc = f"Expert MLB analysis and betting insights for {topic}. Data-driven predictions and key matchup breakdowns."[:160]
    
    return {
        "html": content,
        "meta_title": meta_title,
        "meta_desc": meta_desc,
        "faq": faq,
        "citations": citations
    }

def generate_mlb_blog_post(topic: str, keywords: List[str], game_data: dict) -> dict:
    """Main function to generate MLB-specific blog post using game data"""
    try:
        result = generate_mlb_blog_post_with_retries(topic, keywords, game_data)
        if result is None:
            raise Exception("Failed to generate blog post after all retries")
        return result
        
    except Exception as e:
        logger.error(f"Blog post generation failed: {str(e)}")
        # Return minimal fallback response
        return {
            "html": f"<h1>Error Generating Content</h1><p>Unable to generate blog post for: {topic}</p>",
            "meta_title": f"Error - {topic}",
            "meta_desc": "Content generation temporarily unavailable.",
            "faq": [],
            "citations": []
        }

# Keep the original function for backward compatibility
def generate_blog_post(topic: str, keywords: List[str]) -> str:
    """Original function - kept for compatibility"""
    result = generate_mlb_blog_post(topic, keywords, {})
    return result.get('html', '') if isinstance(result, dict) else str(result)

if __name__ == "__main__":
    # Test the function
    print("Testing MLB blog post generation...")
    test_topic = "Yankees vs Red Sox MLB Betting Preview"
    test_keywords = ["yankees", "red sox", "mlb betting"]
    test_game_data = {
        'matchup': 'Yankees @ Red Sox',
        'game_time': '7:10 PM EST',
        'moneyline': 'NYY -150 / BOS +130',
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
    
    try:
        result = generate_mlb_blog_post(test_topic, test_keywords, test_game_data)
        print("\n=== GENERATED BLOG POST STRUCTURE ===")
        print(f"Meta Title: {result.get('meta_title', 'N/A')}")
        print(f"Meta Description: {result.get('meta_desc', 'N/A')}")
        print(f"FAQ Count: {len(result.get('faq', []))}")
        print(f"Citations Count: {len(result.get('citations', []))}")
        print("\nHTML Content Preview:")
        html_content = result.get('html', '')
        print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
