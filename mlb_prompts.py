# mlb_prompts.py 
import random

MLB_BLOG_PROMPT_TEMPLATE = """You're an expert MLB betting analyst and blog writer. You write sharp, stat-driven previews for baseball bettors.

Based on the JSON game data below, write a 400–700 word blog post that follows this EXACT structure and uses proper HTML formatting with <h4>, <h5>, and <p> tags. DO NOT use bullet points or markdown. Each section should be structured with clear headings and paragraphs. Use <br><br> to create extra space between sections if needed.

<h4><b>[Topic] MLB Betting Preview</b></h4>
<h4><b>Game Time: [time from game_time field]</b></h4>

<h4><b>1. Brief Intro</b></h4>
<p>Set up the game in 2-3 sentences using the matchup and key angles from the data. <b>Include the betting line information from the betting_info field in this intro section.</b></p>

<h4><b>2. Pitcher Breakdown</b></h4>
<h5><b>Pitching Matchup: [Away Pitcher] vs [Home Pitcher]</b></h5>

<h5><b>[Away Pitcher Name] ([Away Team]):</b></h5>
<p>List ALL pitch types with EXACT usage percentages and velocities from away_pitcher.arsenal.<br>
Format: "Four-Seam Fastball (35% usage, 97.1 mph), Slider (18% usage, 87.0 mph), Splitter (14% usage, 84.7 mph)"<br>
Interpretation: What style of pitcher (velocity-heavy, pitch-mix artist, etc.)<br>
How their pitches match up: "The [Home Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Away Pitcher]'s arsenal"</p>

<h5><b>[Home Pitcher Name] ([Home Team]):</b></h5>
<p>Same detailed structure: List ALL pitches with exact usage % and mph from home_pitcher.arsenal<br>
"The [Away Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Home Pitcher]'s arsenal"</p>

<h4><b>3. Lineup Advantage vs Arsenal</b></h4>
<h5><b>Lineup Matchups & Batting Edges</b></h5>

<h5><b>For Away Team vs Home Pitcher:</b></h5>
<p>Compare team averages: "The [Away Team] lineup averages .XXX this season but projects to .XXX vs [Home Pitcher]'s arsenal"<br>
From away_key_performers, show:<br>
The batter with the BIGGEST INCREASE in xBA (if any)<br>
The batter with the BIGGEST DECREASE in xBA (if any)<br>
Format: Name: Season BA .XXX → xBA vs arsenal .XXX (+/- XX points), Season K% XX.X% → Arsenal K% XX.X% (+/- X.X%)<br>
Skip batters with minimal changes (under 15 point differences)</p>

<h5><b>For Home Team vs Away Pitcher:</b></h5>
<p>Same detailed structure using home_key_performers.<br>
Focus on biggest increase and biggest decrease only.</p>

<h4><b>4. Lineup Strikeout Trends vs Arsenal</b></h4>
<h5><b>Strikeout Risks & Rewards</b></h5>
<p>For each team:<br>
Use away_arsenal_k_pct vs away_season_k_pct and home_arsenal_k_pct vs home_season_k_pct.<br>
Format: "The [Team]'s projected K-rate is [X]% vs [Pitcher] — up/down [Y]% from their [Z]% season average."<br>
Interpretation: Higher = potential K prop value, Lower = potential contact play</p>

<h4><b>5. Umpire Influence</b></h4>
<h5><b>Behind the Plate: [Umpire Name]</b></h5>
<p>If umpire field is NOT "TBA" and umpire data exists:<br>
Show exact umpire name from umpire field<br>
Convert umpire_k_boost from multiplier to percentage: 1.11x = "+11% strikeouts"<br>
Convert umpire_bb_boost from multiplier to percentage: 1.03x = "+3% walks"<br>
IMPORTANT: Higher strikeouts = pitcher-friendly, Higher walks = hitter-friendly<br>
Classify correctly: If K% up and BB% up = "mixed tendencies", if K% up and BB% down = "pitcher-friendly", if K% down and BB% up = "hitter-friendly"</p>
<p>If umpire field is "TBA" or missing:<br>
"Umpire assignment has not been announced, which makes prop volatility a concern."</p>
<p>CRITICAL: Only use umpire data that exists in the JSON. Do NOT guess or assume umpire tendencies. Remember: walks help hitters, not pitchers.</p>

<h4><b>6. Betting Interpretation / Final Lean</b></h4>
<h5><b>Final Lean & Betting Takeaway</b></h5>

<p><b>STEP-BY-STEP BETTING ANALYSIS:</b></p>

<p><b>STEP 1: Check ALL individual batters for prop opportunities</b><br>
Go through every batter in away_key_performers and home_key_performers<br>
BATTING LEAN CRITERIA: arsenal_ba > 0.300 AND (arsenal_ba - season_ba) > 0.020<br>
CRITICAL MATH CHECK - VERIFY THESE NUMBERS:<br>
.272 is LESS THAN .300 = NO LEAN<br>
.278 is LESS THAN .300 = NO LEAN<br>
.299 is LESS THAN .300 = NO LEAN<br>
.301 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)<br>
.315 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)<br>
Always verify: Is the xBA number actually above 0.300 before suggesting a lean?<br>
Example: Juan Soto (.263 → .369, +106 points) = LEAN because .369 > .300 AND +106 > +20<br>
Example: Randal Grichuk (.235 → .278, +43 points) = NO LEAN because .278 < .300<br>
Example: Marcell Ozuna (.238 → .272, +34 points) = NO LEAN because .272 < .300</p>

<p><b>STEP 2: Check team strikeout rates for pitcher props</b><br>
Check away_arsenal_k_pct vs away_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER<br>
Check home_arsenal_k_pct vs home_season_k_pct: If arsenal K% > 25% AND increase > 4%, lean OVER<br>
Check for UNDER: If arsenal K% < 15% AND decrease > 4%, lean UNDER<br>
Example: Atlanta 23.4% → 27.6% vs Kikuchi = LEAN OVER because 27.6% > 25% AND +4.2% > +4%</p>

<p><b>STEP 3: Report findings</b><br>
IMPORTANT: Only suggest leans for players/props that meet the EXACT criteria above.<br>
If ANY batter meets BOTH criteria (xBA > 0.300 AND boost > +20):<br>
"Our final lean would be on [Player Name] - his .XXX xBA against this arsenal is well above our .300 threshold with a significant +XX point boost."<br>
If ANY team K% meets criteria (K% > 25% AND increase > 4%):<br>
"Our final lean would be [Pitcher Name] strikeout OVER - [Team]'s projected K-rate jumps to XX.X% vs [Pitcher], up X.X% from their XX.X% season average."<br>
If multiple leans exist, pick the strongest statistical edge.<br>
If NO criteria met:<br>
"No significant statistical edges meet our betting threshold in this matchup."</p>

<p><b>CRITICAL EXAMPLES:</b><br>
Juan Soto (.263 → .369, +106) = LEAN ✅ (meets both criteria)<br>
Randal Grichuk (.235 → .278, +43) = NO LEAN ❌ (.278 < .300)<br>
Player (.285 → .315, +30) = LEAN ✅ (meets both criteria)<br>
Atlanta 23.4% → 27.6% K% (+4.2%) = LEAN OVER ✅ (meets both criteria)</p>

<p><b>CRITICAL RULES:</b><br>
1. Use ONLY the JSON data provided below - NO external stats or guessing<br>
2. If data is missing, say "data not available" rather than inventing<br>
3. Convert all multipliers (1.15x) to percentages (+15%)<br>
4. Focus on the biggest statistical edges from the data<br>
5. Keep tone sharp and analytical, avoid generic phrases<br>
6. ALWAYS include exact pitch usage percentages and velocities from arsenal data<br>
7. Show exact season BA vs projected xBA for all lineup comparisons<br>
8. Only highlight batters with biggest increases AND biggest decreases (skip minimal changes)<br>
9. Apply strict betting criteria - don't suggest weak leans<br>
10. Remember: walks help hitters, strikeouts help pitchers<br>
11. ALWAYS include the game time right after the title<br>
12. ALWAYS include the betting information right after the game time<br>
13. NEVER suggest a batter lean unless xBA > 0.300 AND boost > +20 points<br>
14. NEVER suggest a strikeout prop unless K% > 25% AND increase > 4%<br>
</p>

<!-- Blog Title: {topic} -->
<!-- Target Keywords: {keywords} -->
<!-- Game Data (JSON): {game_data} -->
"""

def get_random_mlb_blog_post_prompt():
    return MLB_BLOG_PROMPT_TEMPLATE

# audit_blog_post.py can remain as you have it.
