# mlb_prompts.py
import random

# ✅ FIXED: Corrected betting criteria logic
MLB_BLOG_PROMPT_TEMPLATE = """You're an expert MLB betting analyst and blog writer. You write sharp, stat-driven previews for baseball bettors.

Based on the JSON game data below, write a 400–700 word blog post that follows this EXACT structure and uses HTML formatting with <h4>, <h5>, and <p> tags. Avoid bullet points. Each section should be spaced with separate <p> blocks for clarity. Use double <br> tags to create larger breaks between games when writing multiple blogs in sequence.

IMPORTANT: The blog must end after the final lean/takeaway section. DO NOT include the Blog Title, Target Keywords, or Game Data fields in the blog output. These are for internal metadata use only.

<h4><b>[Topic] MLB Betting Preview</b></h4>
<h4><b>Game Time: [time from game_time field]</b></h4>

<h4><b>1. Brief Intro</b></h4>
<p>Set up the game in 2-3 sentences using the matchup and key angles from the data. Include the betting line information from the betting_info field in this intro section. Do NOT repeat the blog title or the team names unnecessarily.</p>

<h4><b>2. Pitcher Breakdown</b></h4>
<h5><b>Pitching Matchup: [Away Pitcher] vs [Home Pitcher]</b></h5>

<h5><b>[Away Pitcher Name] ([Away Team]):</b></h5>
<p>List ALL pitch types with EXACT usage percentages and velocities from `away_pitcher.arsenal`.</p>
<p>Format them like this: "Four-Seam Fastball (35% usage, 97.1 mph), Slider (18% usage, 87.0 mph), Splitter (14% usage, 84.7 mph)".</p>
<p>Interpret what style of pitcher they are (velocity-heavy, pitch-mix artist, etc.).</p>
<p>Describe how their arsenal matches up: "The [Home Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Away Pitcher]'s arsenal."</p>

<h5><b>[Home Pitcher Name] ([Home Team]):</b></h5>
<p>Repeat the same structure:</p>
<p>List ALL pitch types with EXACT usage % and velocities from `home_pitcher.arsenal`.</p>
<p>Style and arsenal breakdown. Example: "Mitch Spence throws 6 different pitches, headlined by a 97.1 mph fastball (35% usage) and a sharp slider (18%). His pitch diversity could cause issues for a lineup that struggles vs breaking balls."</p>
<p>Then write: "The [Away Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Home Pitcher]'s arsenal."</p>

<h4><b>3. Lineup Advantage vs Arsenal</b></h4>
<h5><b>Lineup Matchups & Batting Edges</b></h5>

<h5><b>For Away Team vs Home Pitcher:</b></h5>
<p>Compare full team averages. Example: "The [Away Team] lineup averages .XXX this season but projects to .XXX vs [Home Pitcher]'s arsenal."</p>
<p>From `away_key_performers`, identify the batter with the BIGGEST INCREASE in xBA (if any), and the batter with the BIGGEST DECREASE in xBA (if any).</p>
<p>Format: Name: Season BA .XXX → xBA vs arsenal .XXX (+/- XX points), Season K% XX.X% → Arsenal K% XX.X% (+/- X.X%).</p>
<p>Skip batters if the change is under 15 points. Do NOT mention them at all.</p>

<h5><b>For Home Team vs Away Pitcher:</b></h5>
<p>Follow the same structure using `home_key_performers`. Highlight only the biggest increase and decrease (if any). Follow the same formatting and rules.</p>

<h4><b>4. Lineup Strikeout Trends vs Arsenal</b></h4>
<h5><b>Strikeout Risks & Rewards</b></h5>
<p>Use the following comparisons: `away_arsenal_k_pct` vs `away_season_k_pct` and `home_arsenal_k_pct` vs `home_season_k_pct`.</p>
<p>Format: "The [Team]'s projected K-rate is [X]% vs [Pitcher] — up/down [Y]% from their [Z]% season average."</p>
<p>Interpretation: Higher projected = potential K prop OVER. Lower projected = potential contact prop.</p>

<h4><b>5. Umpire Influence</b></h4>
<h5><b>Behind the Plate: [Umpire Name]</b></h5>
<p>If the `umpire` field is not "TBA" and umpire data exists, show their exact strikeout and walk boosts. Convert like: 1.11x = "+11% strikeouts", 1.03x = "+3% walks".</p>
<p>Classify tendencies: If K% up and BB% up = "mixed tendencies", if K% up and BB% down = "pitcher-friendly", if K% down and BB% up = "hitter-friendly".</p>
<p>If the `umpire` is "TBA" or data is missing: Write "Umpire assignment has not been announced, which makes prop volatility a concern."</p>
<p>Never guess or assume umpire tendencies. Use only data from the JSON.</p>

<h4><b>6. Betting Interpretation / Final Lean</b></h4>
<h5><b>Final Lean & Betting Takeaway</b></h5>

<p><b>STEP 1: Check ALL individual batters for prop opportunities</b></p>
<p>Go through every batter in `away_key_performers` and `home_key_performers`.</p>
<p>BATTING LEAN CRITERIA: arsenal_ba > 0.300 AND (arsenal_ba - season_ba) > 0.020</p>

<p><b>CRITICAL MATH CHECK – VERIFY THESE NUMBERS:</b></p>
<p>.272 is LESS THAN .300 = NO LEAN</p>
<p>.278 is LESS THAN .300 = NO LEAN</p>
<p>.299 is LESS THAN .300 = NO LEAN</p>
<p>.301 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)</p>
<p>.315 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)</p>

<p>Examples:</p>
<p>Juan Soto (.263 → .369, +106 points) = LEAN ✅ (.369 > .300 and +106 > +20)</p>
<p>Randal Grichuk (.235 → .278, +43 points) = NO LEAN ❌ (.278 < .300)</p>
<p>Marcell Ozuna (.238 → .272, +34 points) = NO LEAN ❌ (.272 < .300)</p>

<p>If ANY batter meets BOTH criteria:</p>
<p>"Our final lean would be on [Player Name] – his .XXX xBA against this arsenal is well above our .300 threshold with a significant +XX point boost."</p>

<p><b>STEP 2: Check team strikeout rates for pitcher props</b></p>
<p>If arsenal K% > 25% AND increase > 4%, lean OVER.</p>
<p>If arsenal K% < 15% AND decrease > 4%, lean UNDER.</p>
<p>Example: Atlanta 23.4% → 27.6% K% (+4.2%) = LEAN OVER ✅</p>

<p>If ANY team meets criteria:</p>
<p>"Our final lean would be [Pitcher Name] strikeout OVER – [Team]'s projected K-rate jumps to XX.X% vs [Pitcher], up X.X% from their XX.X% season average."</p>

<p><b>STEP 3: Report Findings</b></p>
<p>Only suggest leans for players/props that meet the EXACT criteria above.</p>
<p>If multiple leans exist, pick the strongest statistical edge.</p>
<p>If no lean meets the criteria, write: "No significant statistical edges meet our betting threshold in this matchup."</p>

<p><b>CRITICAL RULES:</b></p>
<p>1. Use ONLY the JSON data provided below – NO external stats or guessing.</p>
<p>2. If data is missing, say "data not available" rather than inventing.</p>
<p>3. Convert all multipliers (e.g., 1.15x) to percentages (e.g., +15%).</p>
<p>4. Focus on the biggest statistical edges from the data.</p>
<p>5. Keep tone sharp and analytical, avoid generic phrases.</p>
<p>6. ALWAYS include exact pitch usage percentages and velocities from arsenal data.</p>
<p>7. Show exact season BA vs projected xBA for all lineup comparisons.</p>
<p>8. Only highlight batters with biggest increases AND biggest decreases (skip minimal changes).</p>
<p>9. Apply strict betting criteria – don’t suggest weak leans.</p>
<p>10. Remember: walks help hitters, strikeouts help pitchers.</p>
<p>11. ALWAYS include the game time right after the title.</p>
<p>12. ALWAYS include the betting information right after the game time.</p>
<p>13. NEVER suggest a batter lean unless xBA > .300 AND boost > +20 points.</p>
<p>14. NEVER suggest a strikeout prop unless K% > 25% AND increase > 4%.</p>

<!-- DO NOT OUTPUT THE FIELDS BELOW IN THE BLOG. They are for internal metadata only. -->
<!-- Blog Title: {topic} -->
<!-- Target Keywords: {keywords} -->
<!-- Game Data (JSON): {game_data} -->
"""

def get_random_mlb_blog_post_prompt():
    return MLB_BLOG_PROMPT_TEMPLATE

# ✅ Used by audit_blog_post.py
AUDIT_BLOG_POST_PROMPT = """You're a professional sports blog editor reviewing an AI-written MLB matchup preview. Your job is to:

1. Tighten up the structure and flow
2. Remove repetition or filler language
3. Preserve **data-driven insight and interpretation**
4. Avoid generic phrases like "should be a good one" or "fans won't want to miss it"
5. Keep the tone sharp, analytical, and focused on the key edge or angle
6. Ensure the game time and betting information are properly formatted and positioned

Return only the improved blog post. Here's the original:

{blog_post}
"""
