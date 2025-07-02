# audit_blog_post.py
from config import OPENAI_API_KEY
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

# Template for auditing and optimizing a blog post for readability
AUDIT_BLOG_POST_PROMPT = """
Audit and optimize the following blog post for readability and simple language. Ensure the content is easy to understand for a general audience:
{blog_post}
---
only output the optimized blog post and nothing else
"""

def audit_blog_post(blog_post):
    prompt = AUDIT_BLOG_POST_PROMPT.format(blog_post=blog_post)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a professional editor who optimizes content for readability."},
                  {"role": "user", "content": prompt}],
        max_tokens=4096
    )
    
    return response.choices[0].message.content
