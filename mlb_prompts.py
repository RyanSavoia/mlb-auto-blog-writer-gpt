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
    """Always include 2-3 angle sections with fallbacks when data is missing"""
    angle_prompts = []
    
    # Always include team form analysis
    angle_prompts.append(f"""
<h2>{unique_angles['team_form']}</h2>
<p>If away_recent_form and home_recent_form fields are missing, write "Data not available for recent team form analysis." Otherwise: Analyze recent team performance over the last 10 games using the available form data. Focus on offensive production, pitching effectiveness, and momentum heading into this matchup.</p>
""")
    
    # Always include bullpen analysis
    angle_prompts.append(f"""
<h2>{unique_angles['bullpen_status']}</h2>
<p>If bullpen usage fields are missing, write "Data not available for bullpen fatigue analysis." Otherwise: Examine bullpen workload and availability. Consider recent usage patterns and how fatigue might impact late-game scenarios.</p>
""")
    
    # Add situational factors
    angle_prompts.append(f"""
<h2>{unique_angles['situational']}</h2>
<p>If weather and ballpark_factors fields are missing, write "Data not available for environmental factors analysis." Otherwise: Evaluate environmental factors including weather conditions, ballpark dimensions, and any travel/rest advantages that could influence the outcome.</p>
""")

    # Add splits analysis
    angle_prompts.append(f"""
<h2>{unique_angles['splits']}</h2>
<p>If platoon splits data is missing, write "Data not available for platoon splits analysis." Otherwise: Analyze left/right handed matchup advantages for both teams' key hitters against opposing pitchers' arsenals.</p>
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
    
    # Shuffle and cap at 3 for variety
    random.shuffle(unique_angle_prompts)
    unique_angle_prompts = unique_angle_prompts[:3]
    
    # Create citations requirement with improved instruction
    citation_requirement = (
        "Use at least 2 of these authoritative sources as inline citations "
        "(do not print this list verbatim; cite inline where relevant):\n" +
        "\n".join([
            f'- {s["name"]} for {s["context"]}: <a href="{s["url"]}" target="_blank">{s["name"]}</a>'
            for s in authority_sources
        ])
    )
    
    # Build the enhanced prompt
    prompt = f"""You are an expert MLB betting analyst. Write a comprehensive, unique preview that avoids template-like content.

CRITICAL: Return ONLY a JSON object with this exact structure:
{{
    "html": "your complete HTML blog post",
    "meta_title": "SEO title 50-60 chars", 
    "meta_desc": "SEO description 140-160 chars",
    "faq": [{{"question": "Q text", "answer": "A text"}}],
    "citations": [{{"source": "Source Name", "url": "https://url"}}],
    "keywords": ["keyword1", "keyword2"]
}}

HTML STRUCTURE REQUIREMENTS:
<h1>{topic}</h1>
<p><strong>Game Time:</strong> [game_data.game_time or "data not available"] | <strong>Lines:</strong> [game_data.moneyline or game_data.betting_info or "data not available"]</p>
<p>By MLB Analytics Team | Reviewed by Senior Baseball Analysts</p>

<h2>{headers['intro']}</h2>
<p>Set up the game in 2-3 sentences. Do not repeat game time or lines here.</p>

<h2>{headers['pitchers']}</h2>
<h3>[Away Pitcher] vs [Home Pitcher]</h3>
<p><strong>[Away Pitcher]:</strong> List exact arsenal from away_pitcher.arsenal with usage% and mph.
<strong>[Home Pitcher]:</strong> List exact arsenal from home_pitcher.arsenal with usage% and mph.</p>

<h2>{headers['lineups']}</h2>  
<h3>Projected xBA vs Arsenal</h3>
<p>Show 2-3 biggest xBA changes from <code>away_key_performers</code> and <code>home_key_performers</code>. Format: "Name: .XXX → .XXX (+/-XX pts)"</p>

<h2>{headers['strikeouts']}</h2>
<h3>K-Rate Projections</h3> 
<p>Arsenal K% vs season K% for both teams. Format: "Team: XX.X% vs Pitcher (±X.X% from season)"</p>

<h2>{headers['umpire']}</h2>
<h3>Plate Umpire: [umpire name or "TBA"]</h3>
<p>If data exists: Convert multipliers to % (1.11x = +11%). If TBA: mention uncertainty.</p>"""

    # Add unique angle sections (only once)
    for angle_prompt in unique_angle_prompts:
        prompt += angle_prompt

    prompt += f"""
<h2>Key Takeaways</h2>
<p>Provide exactly 3 concise sentences summarizing the most important betting insights from your analysis. Focus on actionable information for bettors.</p>

<h2>Frequently Asked Questions</h2>"""

    # Add FAQ structure (only once)
    for question in faq_questions:
        prompt += f'<h3>{question}</h3>\n<p>[Provide specific answer based on game data and analysis]</p>\n'

    prompt += f"""
BETTING ANALYSIS REQUIREMENTS:
- Use EXACT criteria for recommendations:
  * Batter props: arsenal_ba > 0.300 AND boost > +20 points
  * Strikeout props: K% > 25% AND increase > 4%
- Only recommend when data strongly supports the lean
- If no strong edges exist, state: "No significant statistical edges meet our betting threshold"

CONTENT QUALITY RULES:
1. Each post must feel unique - vary analysis depth, focus areas, and insights
2. Use specific data points and exact numbers from the JSON
3. Avoid generic phrases like "this should be a great game"
4. Include methodology note: "Analysis based on xBA models and historical data. Do not bet based solely on this article."
5. Must include at least 2 of these authority citations as inline links: {citation_requirement}
6. Use only fields present in game_data; if a field is missing, write "data not available" for that item. No guessing.
7. If a unique-angle section lacks data, include one sentence: "Data not available for this section."
8. BETTING CRITERIA - Only recommend when data meets exact thresholds:
   - Batter props: arsenal_ba > 0.300 AND boost > +20 points  
   - Strikeout props: K% > 25% AND increase > +4%
   - If no strong edges exist: "No significant statistical edges meet our betting threshold"

Target Keywords: {keywords}
Game Data: {json.dumps(game_data, indent=2)}"""

    return prompt

def get_random_mlb_blog_post_prompt():
    """Legacy function - kept for backward compatibility"""
    return "Use get_mlb_blog_post_prompt(topic, keywords, game_data) instead"

def validate_blog_post(html_content):
    """Post-generation validator to ensure quality standards at scale"""
    issues = []
    
    # Check for minimum 2 citations (look for <a href patterns)
    citation_count = html_content.count('<a href=')
    if citation_count < 2:
        issues.append(f"Only {citation_count} citations found, need minimum 2")
    
    # Check FAQ count (4-6 questions)
    faq_count = html_content.count('<h3>') - html_content.count('<h3>[')  # Exclude template placeholders
    if faq_count < 4 or faq_count > 6:
        issues.append(f"FAQ count is {faq_count}, should be 4-6")
    
    # Check Key Takeaways has exactly 3 sentences
    takeaways_section = html_content.split('<h2>Key Takeaways</h2>')
    if len(takeaways_section) > 1:
        # Get the takeaways paragraph content
        takeaways_content = takeaways_section[1].split('</p>')[0].split('<p>')[1] if '<p>' in takeaways_section[1] else ""
        sentence_count = takeaways_content.count('.') - takeaways_content.count('...') # Exclude ellipses
        if sentence_count != 3:
            issues.append(f"Key Takeaways has {sentence_count} sentences, need exactly 3")
    else:
        issues.append("Key Takeaways section not found")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "citation_count": citation_count,
        "faq_count": faq_count
    }
