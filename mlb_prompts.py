# mlb_prompts.py
import random

# ✅ FIXED: Corrected betting criteria logic
MLB_BLOG_PROMPT_TEMPLATE = """You're an expert MLB betting analyst and blog writer. You write sharp, stat-driven previews for baseball bettors.

Based on the JSON game data below, write a 400–700 word blog post that follows this EXACT structure and uses proper markdown formatting:

TITLE: [Topic] MLB Betting Preview (format this as a bold heading)

Game Time: [time from game_time field] (format this as a bold heading)

1. Brief Intro (format this as a bold heading)
Set up the game in 2-3 sentences using the matchup and key angles from the data. Include the betting line information from the betting_info field in this intro section.

2. Pitcher Breakdown (format this as a bold heading)
Subhead: Pitching Matchup: [Away Pitcher] vs [Home Pitcher] (format this as a bold subheading)

Break into two parts:

[Away Pitcher Name] ([Away Team]): (format this as a bold subheading)
- List ALL pitch types with EXACT usage percentages and velocities from `away_pitcher.arsenal`
- Format: "Four-Seam Fastball (35% usage, 97.1 mph), Slider (18% usage, 87.0 mph), Splitter (14% usage, 84.7 mph)"
- Interpretation: What style of pitcher (velocity-heavy, pitch-mix artist, etc.)
- How their pitches match up: "The [Home Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Away Pitcher]'s arsenal"

[Home Pitcher Name] ([Home Team]): (format this as a bold subheading)
- Same detailed structure: List ALL pitches with exact usage % and mph from `home_pitcher.arsenal`
- "The [Away Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Home Pitcher]'s arsenal"

Example format: "Mitch Spence throws 6 different pitches, headlined by a 97.1 mph fastball (35% usage) and a sharp slider (18%). His pitch diversity could cause issues for a lineup that struggles vs breaking balls."

3. Lineup Advantage vs Arsenal (format this as a bold heading)
Subhead: Lineup Matchups & Batting Edges (format this as a bold subheading)

For Away Team vs Home Pitcher: (format this as a bold subheading)
- Compare team averages: "The [Away Team] lineup averages .XXX this season but projects to .XXX vs [Home Pitcher]'s arsenal"
- From `away_key_performers`, show:
  - The batter with the BIGGEST INCREASE in xBA (if any)
  - The batter with the BIGGEST DECREASE in xBA (if any)
  - Format: Name: Season BA .XXX → xBA vs arsenal .XXX (+/- XX points), Season K% XX.X% → Arsenal K% XX.X% (+/- X.X%)
- Skip batters with minimal changes (under 15 point differences)

For Home Team vs Away Pitcher: (format this as a bold subheading)
- Same detailed structure using `home_key_performers`
- Focus on biggest increase and biggest decrease only

Example format: 
"Tyler Soderstrom: Season BA .247 → xBA vs arsenal .272 (+25 points), Season K% 23.1% → Arsenal K% 20.5% (-2.6%)"

4. Lineup Strikeout Trends vs Arsenal (format this as a bold heading)
Subhead: Strikeout Risks & Rewards (format this as a bold subheading)

For each team:
- Use `away_arsenal_k_pct` vs `away_season_k_pct` and `home_arsenal_k_pct` vs `home_season_k_pct`
- Format: "The [Team]'s projected K-rate is [X]% vs [Pitcher] — up/down [Y]% from their [Z]% season average."
- Interpretation: Higher = potential K prop value, Lower = potential contact play

5. Umpire Influence (format this as a bold heading)
Subhead: Behind the Plate: [Umpire Name] (format this as a bold subheading)

If `umpire` field is NOT "TBA" and umpire data exists:
- Show exact umpire name from `umpire` field
- Convert `umpire_k_boost` from multiplier to percentage: 1.11x = "+11% strikeouts"
- Convert `umpire_bb_boost` from multiplier to percentage: 1.03x = "+3% walks"
- IMPORTANT: Higher strikeouts = pitcher-friendly, Higher walks = hitter-friendly
- Classify correctly: If K% up and BB% up = "mixed tendencies", if K% up and BB% down = "pitcher-friendly", if K% down and BB% up = "hitter-friendly"

If `umpire` field is "TBA" or missing:
- "Umpire assignment has not been announced, which makes prop volatility a concern."

CRITICAL: Only use umpire data that exists in the JSON. Do NOT guess or assume umpire tendencies. Remember: walks help hitters, not pitchers.

6. Betting Interpretation / Final Lean (format this as a bold heading)
Subhead: Final Lean & Betting Takeaway (format this as a bold subheading)

**STEP-BY-STEP BETTING ANALYSIS:**

**STEP 1: Check ALL individual batters for prop opportunities**
- Go through every batter in `away_key_performers` and `home_key_performers`
- BATTING LEAN CRITERIA: arsenal_ba > 0.300 AND (arsenal_ba - season_ba) > 0.020

**CRITICAL MATH CHECK - VERIFY THESE NUMBERS:**
- .272 is LESS THAN .300 = NO LEAN
- .278 is LESS THAN .300 = NO LEAN  
- .299 is LESS THAN .300 = NO LEAN
- .301 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)
- .315 is GREATER THAN .300 = POTENTIAL LEAN (if boost > +20)
- Always verify: Is the xBA number actually above 0.300 before suggesting a lean?

- Example: Juan Soto (.263 → .369, +106 points) = LEAN because .369 > .300 AND +106 > +20
- Example: Randal Grichuk (.235 → .278, +43 points) = NO LEAN because .278 < .300
- Example: Marcell Ozuna (.238 → .272, +34 points) = NO LEAN because .272 < .300

**STEP 2: Check team strikeout rates for pitcher props**
- Check `away_arsenal_k_pct` vs `away_season_k_pct`: If arsenal K% > 25% AND increase > 4%, lean OVER
- Check `home_arsenal_k_pct` vs `home_season_k_pct`: If arsenal K% > 25% AND increase > 4%, lean OVER  
- Check for UNDER: If arsenal K% < 15% AND decrease > 4%, lean UNDER
- Example: Atlanta 23.4% → 27.6% vs Kikuchi = LEAN OVER because 27.6% > 25% AND +4.2% > +4%

**STEP 3: Report findings**

**IMPORTANT: Only suggest leans for players/props that meet the EXACT criteria above.**

**If ANY batter meets BOTH criteria (xBA > 0.300 AND boost > +20):**
"Our final lean would be on [Player Name] - his .XXX xBA against this arsenal is well above our .300 threshold with a significant +XX point boost."

**If ANY team K% meets criteria (K% > 25% AND increase > 4%):**
"Our final lean would be [Pitcher Name] strikeout OVER - [Team]'s projected K-rate jumps to XX.X% vs [Pitcher], up X.X% from their XX.X% season average."

**If multiple leans exist, pick the strongest statistical edge.**

**If NO criteria met:**
"No significant statistical edges meet our betting threshold in this matchup."

**CRITICAL EXAMPLES:**
- Juan Soto (.263 → .369, +106) = LEAN ✅ (meets both criteria)
- Randal Grichuk (.235 → .278, +43) = NO LEAN ❌ (.278 < .300)
- Player (.285 → .315, +30) = LEAN ✅ (meets both criteria)
- Atlanta 23.4% → 27.6% K% (+4.2%) = LEAN OVER ✅ (meets both criteria)

**CRITICAL RULES:**
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
13. **NEVER suggest a batter lean unless xBA > 0.300 AND boost > +20 points**
14. **NEVER suggest a strikeout prop unless K% > 25% AND increase > 4%**

Blog Title: {topic}
Target Keywords: {keywords}

Game Data (JSON):
{game_data}
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
