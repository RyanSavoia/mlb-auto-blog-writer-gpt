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
    """Generate MLB blog prompt with randomized headers and HTML output"""
    
    # Get randomized headers
    headers = get_blog_headers()
    
    # Build the prompt template with HTML formatting instructions
    prompt = f"""You're an expert MLB betting analyst and blog writer. You write sharp, stat-driven previews for baseball bettors.

CRITICAL: Output your response using proper HTML formatting with semantic tags:
- Use <h1> for the main title
- Use <h2> for major sections (Game Time, numbered sections)
- Use <h3> for subsections like "Pitching Matchup:" and team names
- Use <h4> for STEP headers
- Use <strong> for bold text
- Use <p> for paragraphs
- Use proper line breaks between sections

Based on the JSON game data below, write a 400–700 word blog post that follows this EXACT structure:

<h1>{topic}</h1>
<h2>Game Time: [time from game_time field]</h2>

<h2>1. {headers['intro']}</h2>
<p>Set up the game in 2-3 sentences using the matchup and key angles from the data. Include the betting line information from the betting_info field in this intro section.</p>

<h2>2. {headers['pitchers']}</h2>
<h3>Pitching Matchup: [Away Pitcher] vs [Home Pitcher]</h3>

<h3>[Away Pitcher Name] ([Away Team]):</h3>
<p>List ALL pitch types with EXACT usage percentages and velocities from away_pitcher.arsenal.</p>
<p>Format: "Four-Seam Fastball (35% usage, 97.1 mph), Slider (18% usage, 87.0 mph), Splitter (14% usage, 84.7 mph)"</p>
<p>Interpretation: What style of pitcher (velocity-heavy, pitch-mix artist, etc.)</p>
<p>How their pitches match up: "The [Home Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Away Pitcher]'s arsenal"</p>

<h3>[Home Pitcher Name] ([Home Team]):</h3>
<p>Same detailed structure: List ALL pitches with exact usage % and mph from home_pitcher.arsenal</p>
<p>"The [Away Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Home Pitcher]'s arsenal"</p>

<h2>3. {headers['lineups']}</h2>
<h3>Lineup Matchups & Batting Edges</h3>

<p><strong>For Away Team vs Home Pitcher:</strong></p>
<p>Compare team averages: "The [Away Team] lineup averages .XXX this season but projects to .XXX vs [Home Pitcher]'s arsenal"</p>
<p>From away_key_performers, show:</p>
<p>The batter with the BIGGEST INCREASE in xBA (if any)</p>
<p>The batter with the BIGGEST DECREASE in xBA (if any)</p>
<p>Format: Name: Season BA .XXX → xBA vs arsenal .XXX (+/- XX points), Season K% XX.X% → Arsenal K% XX.X% (+/- X.X%)</p>
<p>Skip batters with minimal changes (under 15 point differences)</p>

<p><strong>For Home Team vs Away Pitcher:</strong></p>
<p>Same detailed structure using home_key_performers.</p>
<p>Focus on biggest increase and biggest decrease only.</p>

<h2>4. {headers['strikeouts']}</h2>
<h3>Strikeout Risks & Rewards</h3>
<p>For each team:</p>
<p>Use away_arsenal_k_pct vs away_season_k_pct and home_arsenal_k_pct vs home_season_k_pct.</p>
<p>Format: "The [Team]'s projected K-rate is [X]% vs [Pitcher] — up/down [Y]% from their [Z]% season average."</p>
<p>Interpretation: Higher = potential K prop value, Lower = potential contact play</p>

<h2>5. {headers['umpire']}</h2>
<h3>Behind the Plate: [Umpire Name]</h3>
<p>If umpire field is NOT "TBA" and umpire data exists:</p>
<p>Show exact umpire name from umpire field</p>
<p>Convert umpire_k_boost from multiplier to percentage: 1.11x = "+11% strikeouts"</p>
<p>Convert umpire_bb_boost from multiplier to percentage: 1.03x = "+3% walks"</p>
<p>IMPORTANT: Higher strikeouts = pitcher-friendly, Higher walks = hitter-friendly</p>
<p>Classify correctly: If K% up and BB% up = "mixed tendencies", if K% up and BB% down = "pitcher-friendly", if K% down and BB% up = "hitter-friendly"</p>
<p>If umpire field is "TBA" or missing:</p>
<p>"Umpire assignment has not been announced, which makes prop volatility a concern."</p>
<p>CRITICAL: Only use umpire data that exists in the JSON. Do NOT guess or assume umpire tendencies. Remember: walks help hitters, not pitchers.</p>

<h2>6. {headers['lean']}</h2>
<h3>Final Lean & Betting Takeaway</h3>

<p>STEP-BY-STEP BETTING ANALYSIS:</p>

<h4>STEP 1: Check ALL individual batters for prop opportunities</h4>
<p>Go through every batter in away_key_performers and home_key_performers</p>
<p><strong>BATTING LEAN CRITERIA: xBA > 0.300 AND boost > +20 points</strong></p>
<p><strong>CRITICAL MATH CHECK - VERIFY THESE NUMBERS:</strong></p>
<p>.272 is LESS THAN .300 = NO LEAN</p>
<p>.278 is LESS THAN .300 = NO LEAN</p>
<p>.292 is LESS THAN .300 = NO LEAN</p>
<p>.299 is LESS THAN .300 = NO LEAN</p>
<p>.301 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)</p>
<p>.315 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)</p>
<p><strong>Always verify: Is the xBA number actually above 0.300 before suggesting a lean?</strong></p>
<p>Example: Juan Soto (.263 → .369, +106 points) = LEAN because .369 > .300 AND +106 > +20</p>
<p>Example: Randal Grichuk (.235 → .278, +43 points) = NO LEAN because .278 < .300</p>
<p>Example: Bryce Harper (.260 → .292, +32 points) = NO LEAN because .292 < .300</p>
<p>Example: Marcell Ozuna (.238 → .272, +34 points) = NO LEAN because .272 < .300</p>

<h4>STEP 2: Check team strikeout rates for pitcher props</h4>
<p>Check away_arsenal_k_pct vs away_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER</p>
<p>Check home_arsenal_k_pct vs home_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER</p>
<p>Check for UNDER: If arsenal K% < 15% AND decrease > 4%, lean UNDER</p>
<p>Example: Atlanta 23.4% → 27.6% vs Kikuchi = LEAN OVER because 27.6% > 25% AND +4.2% > +4%</p>

<h4>STEP 3: Report findings</h4>
<p><strong>IMPORTANT: Only suggest leans for players/props that meet the EXACT criteria above.</strong></p>
<p>If ANY batter meets BOTH criteria (xBA > 0.300 AND boost > +20):</p>
<p>"Our final lean would be on [Player Name] - his .XXX xBA against this arsenal is well above our .300 threshold with a significant +XX point boost."</p>
<p>If ANY team K% meets criteria (K% > 25% AND increase > 4%):</p>
<p>"Our final lean would be [Pitcher Name] strikeout OVER - [Team]'s projected K-rate jumps to XX.X% vs [Pitcher], up X.X% from their XX.X% season average."</p>
<p>If multiple leans exist, pick the strongest statistical edge.</p>
<p>If NO criteria met:</p>
<p>"No significant statistical edges meet our betting threshold in this matchup."</p>

<p><strong>CRITICAL EXAMPLES:</strong></p>
<p>Juan Soto (.263 → .369, +106) = LEAN ✅ (meets both criteria)</p>
<p>Randal Grichuk (.235 → .278, +43) = NO LEAN ❌ (.278 < .300)</p>
<p>Bryce Harper (.260 → .292, +32) = NO LEAN ❌ (.292 < .300)</p>
<p>Player (.285 → .315, +30) = LEAN ✅ (meets both criteria)</p>
<p>Atlanta 23.4% → 27.6% K% (+4.2%) = LEAN OVER ✅ (meets both criteria)</p>

<p><strong>CRITICAL RULES:</strong></p>
<p>1. Use ONLY the JSON data provided below - NO external stats or guessing</p>
<p>2. If data is missing, say "data not available" rather than inventing</p>
<p>3. Convert all multipliers (1.15x) to percentages (+15%)</p>
<p>4. Focus on the biggest statistical edges from the data</p>
<p>5. Keep tone sharp and analytical, avoid generic phrases</p>
<p>6. ALWAYS include exact pitch usage percentages and velocities from arsenal data</p>
<p>7. Show exact season BA vs projected xBA for all lineup comparisons</p>
<p>8. Only highlight batters with biggest increases AND biggest decreases (skip minimal changes)</p>
<p>9. Apply strict betting criteria - don't suggest weak leans</p>
<p>10. Remember: walks help hitters, strikeouts help pitchers</p>
<p>11. ALWAYS include the game time right after the title</p>
<p>12. ALWAYS include the betting information right after the game time</p>
<p>13. <strong>NEVER suggest a batter lean unless xBA > 0.300 AND boost > +20 points</strong></p>
<p>14. <strong>NEVER suggest a strikeout prop unless K% > 25% AND increase > 4%</strong></p>

Blog Title: {topic}
Target Keywords: {keywords}

Game Data (JSON):
{game_data}
"""
    
    return prompt

def get_random_mlb_blog_post_prompt():
    """Legacy function - kept for backward compatibility"""
    return "Use get_mlb_blog_post_prompt(topic, keywords, game_data) instead"
