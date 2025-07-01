# mlb_prompts.py
import random

MLB_BLOG_POST_PROMPTS = [
    """
    Write a comprehensive MLB betting preview blog post on "{topic}" using the following game data and keywords: {keywords}.
    
    Game Data:
    {game_data}
    
    Structure the post with these sections:
    1. Game Overview: Introduce the matchup and why it's compelling
    2. Pitching Analysis: Deep dive into each starter's arsenal and effectiveness
    3. Lineup Matchups: Analyze how each team's offense matches up against opposing pitching
    4. Key Player Spotlights: Highlight 2-3 players with significant advantages/disadvantages
    5. Umpire Impact: Discuss how the home plate umpire might influence the game
    6. Betting Recommendations: Provide 2-3 specific betting angles with reasoning
    7. Final Prediction: Give a confident take on the game outcome
    
    Make it engaging for baseball fans and bettors. Use statistics and data to support your analysis.
    Include SEO-friendly headings and write 1500-2000 words.
    """,
    
    """
    Create an in-depth MLB game preview for "{topic}" focusing on advanced analytics and matchup advantages. Include keywords: {keywords}.
    
    Game Information:
    {game_data}
    
    Organize with these sections:
    1. Matchup Introduction: Set the stage with team contexts and stakes
    2. Starting Pitcher Breakdown: Analyze arsenals, recent form, and matchup history
    3. Offensive Approach Analysis: How each lineup should attack the opposing starter
    4. X-Factor Players: Identify 3-4 players who could swing the game
    5. Umpire Influence: Explain how the umpire's tendencies affect betting markets
    6. Weather & Ballpark Factors: Consider environmental impacts (if relevant)
    7. Best Bets & Props: Recommend specific wagers with confidence levels
    8. Bottom Line: Conclude with your strongest conviction plays
    
    Write for knowledgeable baseball fans who bet on games. Be analytical but accessible.
    Target 1500-2000 words with proper SEO structure.
    """,
    
    """
    Generate a detailed MLB betting guide for "{topic}" emphasizing data-driven insights. Target keywords: {keywords}.
    
    Available Data:
    {game_data}
    
    Structure as follows:
    1. Executive Summary: Quick-hit analysis for busy readers
    2. Pitcher Arsenal Deep Dive: Break down each starter's strengths/weaknesses
    3. Lineup Construction & Matchups: How batting orders exploit opposing pitching
    4. Historical Context: Recent head-to-head trends and relevant statistics  
    5. Umpire Report Card: How today's ump impacts key betting markets
    6. Contrarian Angles: Identify where public might be wrong
    7. Lock & Load Picks: Your highest confidence bets with rationale
    8. Hedge Opportunities: How to manage risk during live betting
    
    Target serious baseball bettors who want actionable intelligence, not just opinions.
    Write 1500-2000 words with clear headings and bullet points where appropriate.
    """
]

def get_random_mlb_blog_post_prompt():
    return random.choice(MLB_BLOG_POST_PROMPTS)
