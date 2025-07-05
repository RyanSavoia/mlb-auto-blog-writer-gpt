# audit_blog_post.py
from config import OPENAI_API_KEY
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Much more conservative audit prompt - only fix obvious issues
AUDIT_BLOG_POST_PROMPT = """
Fix only obvious grammar, spelling, and punctuation errors in this blog post. 

CRITICAL RULES:
- DO NOT change any numbers, statistics, or data points
- DO NOT change any subheadings or structure
- DO NOT change any betting terminology or odds
- DO NOT change any player names or team names
- DO NOT change any percentages or technical terms
- DO NOT rewrite sentences unless they have clear grammar errors
- DO NOT change the game time or betting information
- Only fix obvious typos, grammar mistakes, and punctuation errors

{blog_post}
---
Only output the corrected blog post with minimal changes.
"""

def audit_blog_post(blog_post):
    prompt = AUDIT_BLOG_POST_PROMPT.format(blog_post=blog_post)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a proofreader who only fixes obvious errors without changing content or structure."},
                  {"role": "user", "content": prompt}],
        max_tokens=4096
    )
    
    return response.choices[0].message.content
