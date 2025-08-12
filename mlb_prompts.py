# mlb_prompts.py 
import random
import json

def get_unique_angles():
    """Generate unique per-post angles to avoid scaled content detection"""
    return {
        "team_form": random.choice([
            "Recent Form Analysis (Last 10 Games)",
            "Team Momentum & Current Streak", 
            "Hot/Cold Streak Impact",
            "Recent Performance Trends",
            "10-Game Form Guide"
        ]),
        "bullpen_status": random.choice([
            "Bullpen Fatigue Assessment",
            "Relief Pitching Workload", 
            "Bullpen Usage Patterns",
            "Relief Corps Analysis",
            "Pen Fatigue Factor"
        ]),
        "situational": random.choice([
            "Weather & Ballpark Factors",
            "Travel & Rest Advantages",
            "Home Field & Environmental Edge",
            "Situational Factors",
            "Game Context Analysis"
        ]),
        "splits": random.choice([
            "L/R Platoon Advantages", 
            "Splits-Based Matchups",
            "Handedness Edge Analysis",
            "Platoon Splits Breakdown",
            "Left/Right Pitcher Trends"
        ])
    }

def get_blog_headers():
    """Generate randomized headers with enhanced variety"""
    return {
        "intro": random.choice([
            "Game Preview & Setup", 
            "Matchup Overview", 
            "Today's Key Angles",
            "Game Breakdown",
            "Preview & Context",
            "Betting Setup",
            "Game Analysis Preview"
        ]),
        "pitchers": random.choice([
            "Starting Pitcher Breakdown", 
            "Mound Matchup Analysis", 
            "Starting Rotation Report",
            "Pitching Duel Preview",
            "Starter Analysis & Arsenal",
            "Primary Pitching Matchup",
            "Starting Pitchers Deep Dive"
        ]),
        "lineups": random.choice([
            "Offensive Matchup Analysis", 
            "Batting Order vs Arsenal Breakdown", 
            "Lineup Edges & Weaknesses",
            "Hitting Matchups by Arsenal",
            "Batter-Pitcher Advantages",
            "Offensive Production Analysis",
            "Lineup Arsenal Matchups"
        ]),
        "strikeouts": random.choice([
            "Strikeout Rate Projections", 
            "Contact vs Whiff Analysis", 
            "K-Rate Trends & Opportunities",
            "Strikeout Prop Outlook",
            "Contact Profile Assessment",
            "Whiff Rate Projections",
            "K-Risk Evaluation"
        ]),
        "umpire": random.choice([
            "Home Plate Umpire Impact", 
            "Behind the Plate Analysis", 
            "Umpire Tendencies & Effect",
            "Plate Umpire Influence",
            "Strike Zone Impact",
            "Umpire Factor Assessment",
            "Official Assignment Analysis"
        ])
    }

def get_faq_questions(game_data):
    """Generate relevant FAQ questions based on game data"""
    away_team = game_data.get('away_team', 'Away Team')
    home_team = game_data.get('home_team', 'Home Team')
    
    base_questions = [
        f"What time does the {away_team} vs {home_team} game start?",
        f"What are the betting odds for {away_team} vs {home_team}?",
        f"Where can I watch the {away_team} vs {home_team} game?",
        f"Who are the starting pitchers for {away_team} vs {home_team}?",
        "What are the best prop bets for this game?",
        "Are there any key injuries affecting this matchup?",
        f"What's the weather forecast for the {home_team} game?",
        f"How have {away_team} and {home_team} performed recently?",
        "What's the over/under total for this game?",
        f"What are {away_team}'s road stats this season?",
        f"How does {home_team} perform at home?",
        "Which team has the bullpen advantage?",
        "What are the key statistical edges in this matchup?"
    ]
    
    # Randomly select 4-6 questions
    num_questions = random.randint(4, 6)
    return random.sample(base_questions, num_questions)

def get_authority_sources():
    """Get randomized authority sources for inline citations"""
    sources = [
        {"name": "Baseball Savant", "url": "https://baseballsavant.mlb.com", "context": "advanced metrics"},
        {"name": "MLB.com", "url": "https://mlb.com", "context": "official statistics"},
        {"name": "FanGraphs", "url": "https://fangraphs.com", "context": "advanced analytics"},
        {"name": "Baseball Reference", "url": "https://baseball-reference.com", "context": "historical data"},
        {"name": "ESPN Stats", "url": "https://espn.com/mlb/stats", "context": "team statistics"}
    ]
    
    # Return 2-3 random sources
    num_sources = random.randint(2, 3)
    return random.sample(sources, num_sources)

def build_unique_angle_prompts(game_data, unique_angles):
    """Build prompts for unique angles based on available data"""
    angle_prompts = []
    
    # Team form analysis
    if game_data.get('away_recent_form') or game_data.get('home_recent_form'):
        angle_prompts.append(f"""
<h2>{unique_angles['team_form']}</h2>
<p>Analyze recent team performance over the last 10 games using any available form data. Focus on offensive production, pitching effectiveness, and momentum heading into this matchup.</p>
""")
    
    # Bullpen analysis  
    if game_data.get('away_bullpen_usage') or game_data.get('home_bullpen_usage'):
        angle_prompts.append(f"""
<h2>{unique_angles['bullpen_status']}</h2>
<p>Examine bullpen workload and availability. Consider recent usage patterns and how fatigue might impact late-game scenarios.</p>
""")
    
    # Weather/situational factors
    if game_data.get('weather') or game_data.get('ballpark_factors'):
        angle_prompts.append(f"""
<h2>{unique_angles['situational']}</h2>
<p>Evaluate environmental factors including weather conditions, ballpark dimensions, and any travel/rest advantages that could influence the outcome.</p>
""")
    
    # L/R splits analysis
    if game_data.get('away_vs_lhp') or game_data.get('away_vs_rhp'):
        angle_prompts.append(f"""
<h2>{unique_angles['splits']}</h2>
<p>Break down how each team performs against left-handed vs right-handed pitching, highlighting key platoon advantages.</p>
""")
    
    return angle_prompts

def get_mlb_blog_post_prompt(topic, keywords, game_data):
    """Generate enhanced MLB blog prompt with unique angles and proper structure"""
    
    # Get randomized elements
    headers = get_blog_headers()
    unique_angles = get_unique_angles()
    faq_questions = get_faq_questions(game_data)
    authority_sources = get_authority_sources()
    
    # Build unique angle sections
    unique_angle_prompts = build_unique_angle_prompts(game_data, unique_angles)
    
    # Create citations requirement
    citation_requirement = "Include these authoritative sources as inline citations:\n"
    for source in authority_sources:
        citation_requirement += f'- {source["name"]} for {source["context"]}: <a href="{source["url"]}" target="_blank">{source["name"]}</a>\n'
    
    # Build the enhanced prompt
    prompt = f"""You are an expert MLB betting analyst and blog writer. Create a comprehensive, unique analysis that avoids template-like content.

CRITICAL OUTPUT FORMAT: Return your response as a JSON object with this exact structure:
{{
    "html": "your full blog post HTML content here",
    "meta_title": "SEO-optimized title (50-60 characters)",
    "meta_description": "SEO description (140-160 characters)", 
    "faq": [
        {{"question": "Q1 text", "answer": "A1 text"}},
        {{"question": "Q2 text", "answer": "A2 text"}}
    ],
    "citations": [
        {{"source": "Source Name", "url": "https://..."}}
    ],
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}

CONTENT REQUIREMENTS:

STRUCTURE (Use proper semantic HTML):
<h1>{topic}</h1>
<p><strong>Game Time:</strong> [Extract from game_data.game_time] | <strong>Betting Lines:</strong> [Extract moneyline/spread from game_data]</p>

<h2>{headers['intro']}</h2>
<p>2-3 sentences setting up the game. Include betting line from game_data. Echo the game time and moneyline exactly once here to prevent duplication.</p>

<h2>{headers['pitchers']}</h2>
<h3>Starting Pitcher Arsenal Analysis</h3>

<h4>[Away Pitcher] ([Away Team])</h4>
<p>List ALL pitch types with EXACT percentages and velocities from away_pitcher.arsenal.
Format: "Four-seam fastball (40% usage, 97.2 mph), Slider (30%, 84.1 mph), Changeup (20%, 89.3 mph)"
Analysis: Pitcher style and how the opposing lineup projects against this specific arsenal mix.</p>

<h4>[Home Pitcher] ([Home Team])</h4>
<p>Same detailed format using home_pitcher.arsenal data.
Include projected team performance against this pitcher's specific mix.</p>

<h2>{headers['lineups']}</h2>
<h3>Key Batting Matchups vs Arsenal</h3>
<p>Focus on the 2-3 most significant xBA changes from away_key_performers and home_key_performers.
Format: "Player Name: .XXX season BA → .XXX projected xBA vs arsenal (+/- XX points)"
Only highlight changes of 15+ points to avoid noise.</p>

<h2>{headers['strikeouts']}</h2>
<h3>Strikeout Rate Analysis</h3>
<p>Compare arsenal-specific K-rates vs season averages using away_arsenal_k_pct and home_arsenal_k_pct data.
Format: "[Team] projects to XX.X% strikeouts vs [Pitcher] - up/down X.X% from season average"</p>

<h2>{headers['umpire']}</h2>
<h3>Home Plate Official Impact</h3>
<p>ONLY if umpire data exists: Convert multipliers to percentages (1.11x = +11%).
If umpire field is "TBA": mention assignment uncertainty.
NEVER fabricate umpire tendencies - use only provided data.</p>"""

    # Add unique angle sections if data supports them
    for angle_prompt in unique_angle_prompts:
        prompt += angle_prompt

    prompt += f"""
<h2>Key Takeaways</h2>
<p>Provide exactly 3 concise sentences summarizing the most important betting insights from your analysis. Focus on actionable information for bettors.</p>

<h2>Frequently Asked Questions</h2>
"""

    # Add FAQ requirements
    for i, question in enumerate(faq_questions, 1):
        prompt += f'<h3>{question}</h3>\n<p>[Provide specific answer based on game data and analysis]</p>\n'

    prompt += f"""
BETTING ANALYSIS REQUIREMENTS:
- Use EXACT criteria for recommendations:
  * Batter props: arsenal_ba > 0.300 AND boost > +20 points
  * Strikeout props: K% > 25% AND increase > 4%
- Only recommend when data strongly supports the lean
- If no strong edges exist, state: "No significant statistical edges meet our betting threshold"

CITATION REQUIREMENTS:
{citation_requirement}

CONTENT QUALITY RULES:
1. Each post must feel unique - vary analysis depth, focus areas, and insights
2. Use specific data points and exact numbers from the JSON
3. Avoid generic phrases like "this should be a great game"
4. Include methodology note: "Analysis based on xBA models and historical data. Do not bet based solely on this article."
5. Add byline: "By MLB Analytics Team | Reviewed by Senior Baseball Analysts"

Target Keywords: {keywords}
Current Game Data: {json.dumps(game_data, indent=2)}

Remember: Return the complete response as a JSON object with html, meta_title, meta_description, faq, citations, and keywords fields."""

    return prompt

def get_random_mlb_blog_post_prompt():
    """Legacy function - kept for backward compatibility"""
    return "Use get_mlb_blog_post_prompt(topic, keywords, game_data) instead"
