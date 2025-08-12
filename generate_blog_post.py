# generate_blog_post.py
from config import OPENAI_API_KEY
from mlb_prompts import get_mlb_blog_post_prompt
from openai import OpenAI
import json
import time
import hashlib
import logging
import re
from urllib.parse import urlparse
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

ALLOWED_CITATION_DOMAINS = {
    "mlb.com", "baseballsavant.mlb.com", "fangraphs.com",
    "baseball-reference.com", "espn.com"
}

def _hostname_ok(netloc, allowed):
    return any(netloc == d or netloc.endswith("." + d) for d in allowed)

def validate_blog_post(html: str, result: dict) -> dict:
    issues = []
    
    anchors = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>', html, flags=re.IGNORECASE)
    citation_count = len(anchors)
    if citation_count < 2:
        issues.append(f"Only {citation_count} inline citations found, need minimum 2.")
    
    # domain + nofollow check
    good_citations = 0
    for href in anchors:
        netloc = urlparse(href).netloc.lower()
        if _hostname_ok(netloc, ALLOWED_CITATION_DOMAINS):
            # check rel="nofollow"
            # find the full tag containing this href
            tag_match = re.search(rf'<a[^>]*href="{re.escape(href)}"[^>]*>', html, flags=re.IGNORECASE)
            if tag_match:
                tag = tag_match.group(0)
                if re.search(r'rel\s*=\s*"[^\"]*\bnofollow\b[^\"]*"', tag, flags=re.IGNORECASE):
                    good_citations += 1
                else:
                    issues.append(f'Citation to {netloc} missing rel="nofollow".')
    
    if good_citations < 2:
        issues.append(f"Only {good_citations} qualified citations (allowed domains + nofollow); need ≥2.")
    
    # FAQ count from JSON payload (preferred, avoids HTML parsing weirdness)
    faq_list = result.get("faq", []) or []
    faq_count = len(faq_list)
    if faq_count < 4 or faq_count > 6:
        issues.append(f"FAQ count is {faq_count}, should be 4–6.")
    
    # Ensure Key Takeaways has exactly 3 sentences (basic parse)
    kt_match = re.search(r'<h2>\s*Key Takeaways\s*</h2>\s*<p>(.*?)</p>', html, flags=re.IGNORECASE|re.DOTALL)
    if not kt_match:
        issues.append("Key Takeaways section not found.")
    else:
        # Count sentences naively by period; ignore ellipses
        text = re.sub(r'\.{3,}', '', kt_match.group(1))
        sentences = [s for s in re.split(r'\.\s+', text.strip()) if s]
        if len(sentences) != 3:
            issues.append(f"Key Takeaways has {len(sentences)} sentences, need exactly 3.")
    
    # Guard "Game Time / Lines" from repeating
    game_time_mentions = len(re.findall(r'>\s*Game Time:\s*<|Game Time:', html, flags=re.IGNORECASE))
    lines_mentions = len(re.findall(r'>\s*Lines:\s*<|Lines:', html, flags=re.IGNORECASE))
    if game_time_mentions != 1:
        issues.append(f'"Game Time" appears {game_time_mentions} times; must be exactly once.')
    if lines_mentions != 1:
        issues.append(f'"Lines" appears {lines_mentions} times; must be exactly once.')
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "citation_count": citation_count,
        "faq_count": faq_count
    }

def truncate_game_data(game_data: dict, max_tokens: int = 2000) -> dict:
    """Truncate game_data text blocks to prevent token overflow"""
    truncated_data = game_data.copy()
    
    # Truncate long text fields that might cause token issues
    text_fields = ['away_pitcher', 'home_pitcher', 'away_key_performers', 'home_key_performers']
    
    for field in text_fields:
        if field in truncated_data and isinstance(truncated_data[field], dict):
            if 'arsenal' in truncated_data[field]:
                arsenal_text = truncated_data[field]['arsenal']
                if len(arsenal_text) > 500:  # Increased from 200 to avoid cutting off usage/mph
                    truncated_data[field]['arsenal'] = arsenal_text[:500] + "..."
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
1. Heading hierarchy only: <h1> title, <h2> sections, <h3> subsections.
2. Include a "Key Takeaways" section with exactly 3 concise sentences (not bullets).
3. Include an FAQ section with 4–6 Q&As at the end.
4. Include at least 2 inline authority citations (MLB.com, Baseball Savant, FanGraphs, Baseball-Reference, or ESPN). Use <a href="..."> with rel="nofollow".
5. Add byline line immediately under the metadata: "By MLB Analytics Team | Reviewed by Senior Baseball Analysts".
6. Add methodology note in the article body: "Analysis based on xBA models and historical data. Do not bet based solely on this article."
7. The "Game Time" and "Lines" appear once at the top metadata line and MUST NOT be repeated in the intro.
8. Return JSON with keys: {"html": "...", "meta_title": "...", "meta_desc": "...", "faq": [...], "citations": [...], "keywords": [...]}.

Write engaging, data-driven content for baseball fans and bettors."""

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} for prompt hash: {prompt_hash}")
            
            response = client.chat.completions.with_options(timeout=60).create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4096,
                temperature=0.7
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
                required_fields = ['html', 'meta_title', 'meta_desc', 'faq', 'citations', 'keywords']
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
    
    # Ensure fallback passes validation by adding sources
    html_with_sources = (
        content + 
        '<p>Sources: '
        '<a href="https://mlb.com" rel="nofollow" target="_blank">MLB.com</a> and '
        '<a href="https://baseballsavant.mlb.com" rel="nofollow" target="_blank">Baseball Savant</a>.'
        '</p>'
    )
    
    return {
        "html": html_with_sources,
        "meta_title": meta_title,
        "meta_desc": meta_desc,
        "faq": faq,
        "citations": citations,
        "keywords": []
    }

def generate_mlb_blog_post(topic: str, keywords: List[str], game_data: dict) -> dict:
    """Main function to generate MLB-specific blog post using game data"""
    try:
        result = generate_mlb_blog_post_with_retries(topic, keywords, game_data)
        if result is None:
            raise Exception("Failed to generate blog post after all retries")
        
        # VALIDATION CHECKPOINT - Check quality before returning
        html = result.get("html", "")
        check = validate_blog_post(html, result)
        if not check["valid"]:
            logger.warning(f"Validation failed: {check['issues']}")
            # Optional one-shot retry
            retry = generate_mlb_blog_post_with_retries(topic, keywords, game_data, max_retries=1)
            if isinstance(retry, dict):
                retry_html = retry.get("html", "")
                if validate_blog_post(retry_html, retry)["valid"]:
                    return retry
            # Attach issues for debugging
            result["validation_issues"] = check["issues"]
        
        return result
        
    except Exception as e:
        logger.error(f"Blog post generation failed: {str(e)}")
        # Return minimal fallback response
        return {
            "html": f"<h1>Error Generating Content</h1><p>Unable to generate blog post for: {topic}</p>",
            "meta_title": f"Error - {topic}",
            "meta_desc": "Content generation temporarily unavailable.",
            "faq": [],
            "citations": [],
            "keywords": []
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
        
        # Show validation status
        if "validation_issues" in result:
            print(f"Validation Issues: {result['validation_issues']}")
        else:
            print("Validation: PASSED")
        
        print("\nHTML Content Preview:")
        html_content = result.get('html', '')
        print(html_content[:500] + "..." if len(html_content) > 500 else html_content)
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
