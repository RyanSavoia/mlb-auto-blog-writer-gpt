# mlb_prompts.py 
import random

def get_blog_headers():
    """Generate randomized headers to avoid scaled content detection"""
    return {
        "intro": random.choice([
            "Brief Intro", 
            "Game Overview", 
            "Matchup Setup",
            "Today's Setup",
            "Game Preview"
        ]),
        "pitchers": random.choice([
            "Pitcher Breakdown", 
            "Rotation Report", 
            "Starting Pitching Analysis",
            "Mound Matchup",
            "Pitching Preview"
        ]),
        "lineups": random.choice([
            "Lineup Matchups", 
            "Batting Edges vs Arsenal", 
            "Offensive Breakdown",
            "Lineup Advantage vs Arsenal",
            "Hitting Matchups"
        ]),
        "strikeouts": random.choice([
            "Strikeout Trends", 
            "K-Risk Analysis", 
            "Whiff Outlook",
            "Lineup Strikeout Trends vs Arsenal",
            "Contact vs Strikeout Profile"
        ]),
        "umpire": random.choice([
            "Umpire Impact", 
            "Behind the Plate", 
            "Umpire Trends",
            "Umpire Influence",
            "Plate Umpire Analysis"
        ]),
        "lean": random.choice([
            "Final Lean & Takeaway", 
            "Betting Breakdown", 
            "Where the Edge Is",
            "Betting Interpretation / Final Lean",
            "Our Betting Take"
        ])
    }

def get_mlb_blog_post_prompt(topic, keywords, game_data):
    """Generate MLB blog prompt with randomized headers"""
    
    # Get randomized headers
    headers = get_blog_headers()
    
    # Build the prompt template with variable headers
    prompt = f"""You're an expert MLB betting analyst and blog writer. You write sharp, stat-driven previews for baseball bettors.

Based on the JSON game data below, write a 400–700 word blog post that follows this EXACT structure:

{topic}
Game Time: [time from game_time field]

1. {headers['intro']}
Set up the game in 2-3 sentences using the matchup and key angles from the data. Include the betting line information from the betting_info field in this intro section.

2. {headers['pitchers']}
Pitching Matchup: [Away Pitcher] vs [Home Pitcher]

[Away Pitcher Name] ([Away Team]):
List ALL pitch types with EXACT usage percentages and velocities from away_pitcher.arsenal.
Format: "Four-Seam Fastball (35% usage, 97.1 mph), Slider (18% usage, 87.0 mph), Splitter (14% usage, 84.7 mph)"
Interpretation: What style of pitcher (velocity-heavy, pitch-mix artist, etc.)
How their pitches match up: "The [Home Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Away Pitcher]'s arsenal"

[Home Pitcher Name] ([Home Team]):
Same detailed structure: List ALL pitches with exact usage % and mph from home_pitcher.arsenal
"The [Away Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Home Pitcher]'s arsenal"

3. {headers['lineups']}
Lineup Matchups & Batting Edges

For Away Team vs Home Pitcher:
Compare team averages: "The [Away Team] lineup averages .XXX this season but projects to .XXX vs [Home Pitcher]'s arsenal"
From away_key_performers, show:
The batter with the BIGGEST INCREASE in xBA (if any)
The batter with the BIGGEST DECREASE in xBA (if any)
Format: Name: Season BA .XXX → xBA vs arsenal .XXX (+/- XX points), Season K% XX.X% → Arsenal K% XX.X% (+/- X.X%)
Skip batters with minimal changes (under 15 point differences)

For Home Team vs Away Pitcher:
Same detailed structure using home_key_performers.
Focus on biggest increase and biggest decrease only.

4. {headers['strikeouts']}
Strikeout Risks & Rewards
For each team:
Use away_arsenal_k_pct vs away_season_k_pct and home_arsenal_k_pct vs home_season_k_pct.
Format: "The [Team]'s projected K-rate is [X]% vs [Pitcher] — up/down [Y]% from their [Z]% season average."
Interpretation: Higher = potential K prop value, Lower = potential contact play

5. {headers['umpire']}
Behind the Plate: [Umpire Name]
If umpire field is NOT "TBA" and umpire data exists:
Show exact umpire name from umpire field
Convert umpire_k_boost from multiplier to percentage: 1.11x = "+11% strikeouts"
Convert umpire_bb_boost from multiplier to percentage: 1.03x = "+3% walks"
IMPORTANT: Higher strikeouts = pitcher-friendly, Higher walks = hitter-friendly
Classify correctly: If K% up and BB% up = "mixed tendencies", if K% up and BB% down = "pitcher-friendly", if K% down and BB% up = "hitter-friendly"
If umpire field is "TBA" or missing:
"Umpire assignment has not been announced, which makes prop volatility a concern."
CRITICAL: Only use umpire data that exists in the JSON. Do NOT guess or assume umpire tendencies. Remember: walks help hitters, not pitchers.

6. {headers['lean']}
Final Lean & Betting Takeaway

STEP-BY-STEP BETTING ANALYSIS:

STEP 1: Check ALL individual batters for prop opportunities
Go through every batter in away_key_performers and home_key_performers
BATTING LEAN CRITERIA: arsenal_ba > 0.300 AND (arsenal_ba - season_ba) > 0.020
CRITICAL MATH CHECK - VERIFY THESE NUMBERS:
.272 is LESS THAN .300 = NO LEAN
.278 is LESS THAN .300 = NO LEAN
.299 is LESS THAN .300 = NO LEAN
.301 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)
.315 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)
Always verify: Is the xBA number actually above 0.300 before suggesting a lean?
Example: Juan Soto (.263 → .369, +106 points) = LEAN because .369 > .300 AND +106 > +20
Example: Randal Grichuk (.235 → .278, +43 points) = NO LEAN because .278 < .300
Example: Marcell Ozuna (.238 → .272, +34 points) = NO LEAN because .272 < .300

STEP 2: Check team strikeout rates for pitcher props
Check away_arsenal_k_pct vs away_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER
Check home_arsenal_k_pct vs home_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER
Check for UNDER: If arsenal K% < 15% AND decrease > 4%, lean UNDER
Example: Atlanta 23.4% → 27.6% vs Kikuchi = LEAN OVER because 27.6% > 25% AND +4.2% > +4%

STEP 3: Report findings
IMPORTANT: Only suggest leans for players/props that meet the EXACT criteria above.
If ANY batter meets BOTH criteria (xBA > 0.300 AND boost > +20):
"Our final lean would be on [Player Name] - his .XXX xBA against this arsenal is well above our .300 threshold with a significant +XX point boost."
If ANY team K% meets criteria (K% > 25% AND increase > 4%):
"Our final lean would be [Pitcher Name] strikeout OVER - [Team]'s projected K-rate jumps to XX.X% vs [Pitcher], up X.X% from their XX.X% season average."
If multiple leans exist, pick the strongest statistical edge.
If NO criteria met:
"No significant statistical edges meet our betting threshold in this matchup."

CRITICAL EXAMPLES:
Juan Soto (.263 → .369, +106) = LEAN ✅ (meets both criteria)
Randal Grichuk (.235 → .278, +43) = NO LEAN ❌ (.278 < .300)
Player (.285 → .315, +30) = LEAN ✅ (meets both criteria)
Atlanta 23.4% → 27.6% K% (+4.2%) = LEAN OVER ✅ (meets both criteria)

CRITICAL RULES:
1. Use ONLY the JSON data provided below - NO external stats or guessing
2. If data is missing, say "data not available" rather than inventing
3. Convert all multipliers (1.15x) to percentages (+15%)
4. Focus on the biggest statistical edges from the data
5. Keep tone sharp and analytical, avoid generic phrases
6. ALWAYS include exact pitch usage percentages and velocities from arsenal data
7. Show exact season BA vs projected xBA for all lineup comparisons
8. Only highlight batters with biggest increases AND biggest decreases (skip minimal changes)
9. Apply strict betting criteria - don't suggest weak leans
10. Remember: walks help hitters, strikeouts help pitchers
11. ALWAYS include the game time right after the title
12. ALWAYS include the betting information right after the game time
13. NEVER suggest a batter lean unless xBA > 0.300 AND boost > +20 points
14. NEVER suggest a strikeout prop unless K% > 25% AND increase > 4%

Blog Title: {topic}
Target Keywords: {keywords}

Game Data (JSON):
{game_data}
"""
    
    return prompt

def get_random_mlb_blog_post_prompt():
    """Legacy function - kept for backward compatibility"""
    return "Use get_mlb_blog_post_prompt(topic, keywords, game_data) instead"
