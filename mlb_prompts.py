# mlb_prompts.py
import random

# ✅ Used by generate_blog_post.py
MLB_BLOG_PROMPT_TEMPLATE = """You're an expert MLB betting analyst and blog writer. You write sharp, stat-driven previews for baseball bettors.

Based on the JSON game data below, write a 400–700 word blog post that follows this EXACT structure:

**1. Brief Intro**
Set up the game in 2-3 sentences using the matchup and key angles from the data.

**2. Pitcher Breakdown**
**Subhead:** `Pitching Matchup: [Away Pitcher] vs [Home Pitcher]`

Break into two parts:

**[Away Pitcher Name] ([Away Team]):**
- List ALL pitch types with EXACT usage percentages and velocities from `away_pitcher.arsenal`
- Format: "Four-Seam Fastball (35% usage, 97.1 mph), Slider (18% usage, 87.0 mph), Splitter (14% usage, 84.7 mph)"
- Interpretation: What style of pitcher (velocity-heavy, pitch-mix artist, etc.)
- How their pitches match up: "The [Home Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Away Pitcher]'s arsenal"

**[Home Pitcher Name] ([Home Team]):**
- Same detailed structure: List ALL pitches with exact usage % and mph from `home_pitcher.arsenal`
- "The [Away Team] lineup averages .XXX this season with a projected xBA of .XXX vs [Home Pitcher]'s arsenal"

**Example format:** "Mitch Spence throws 6 different pitches, headlined by a 97.1 mph fastball (35% usage) and a sharp slider (18%). His pitch diversity could cause issues for a lineup that struggles vs breaking balls."

**3. Lineup Advantage vs Arsenal**
**Subhead:** `Lineup Matchups & Batting Edges`

For **Away Team vs Home Pitcher:**
- Compare team averages: "The [Away Team] lineup averages .XXX this season but projects to .XXX vs [Home Pitcher]'s arsenal"
- From `away_key_performers`, show:
  - The batter with the BIGGEST INCREASE in xBA (if any)
  - The batter with the BIGGEST DECREASE in xBA (if any)
  - Format: Name: Season BA .XXX → xBA vs arsenal .XXX (+/- XX points), Season K% XX.X% → Arsenal K% XX.X% (+/- X.X%)
- Skip batters with minimal changes (under 15 point differences)

For **Home Team vs Away Pitcher:**
- Same detailed structure using `home_key_performers`
- Focus on biggest increase and biggest decrease only

**Example format:** 
"Tyler Soderstrom: Season BA .247 → xBA vs arsenal .272 (+25 points), Season K% 23.1% → Arsenal K% 20.5% (-2.6%)"

**4. Lineup Strikeout Trends vs Arsenal**
**Subhead:** `Strikeout Risks & Rewards`

For each team:
- Use `away_arsenal_k_pct` vs `away_season_k_pct` and `home_arsenal_k_pct` vs `home_season_k_pct`
- Format: "The [Team]'s projected K-rate is [X]% vs [Pitcher] — up/down [Y]% from their [Z]% season average."
- Interpretation: Higher = potential K prop value, Lower = potential contact play

**5. Umpire Influence**
**Subhead:** `Behind the Plate: [Umpire Name]`

If `umpire` field is NOT "TBA" and umpire data exists:
- Show exact umpire name from `umpire` field
- Convert `umpire_k_boost` from multiplier to percentage: 1.11x = "+11% strikeouts"
- Convert `umpire_bb_boost` from multiplier to percentage: 1.03x = "+3% walks"
- IMPORTANT: Higher strikeouts = pitcher-friendly, Higher walks = hitter-friendly
- Classify correctly: If K% up and BB% up = "mixed tendencies", if K% up and BB% down = "pitcher-friendly", if K% down and BB% up = "hitter-friendly"

If `umpire` field is "TBA" or missing:
- "Umpire assignment has not been announced, which makes prop volatility a concern."

**CRITICAL:** Only use umpire data that exists in the JSON. Do NOT guess or assume umpire tendencies. Remember: walks help hitters, not pitchers.

**6. Betting Interpretation / Final Lean**
**Subhead:** `Final Lean & Betting Takeaway`

**STRICT BETTING CRITERIA - Only suggest leans if:**

**For Batter Props:**
- xBA over .300 AND at least +20 points vs season average, OR  
- xBA under .200 AND at least -40 points vs season average

**For Pitcher Strikeout Props:**
- Team projected K% above 25% AND at least +4% vs season average (lean strikeout OVER), OR
- Team projected K% below 15% AND at least -4% vs season average (lean strikeout UNDER)

**If criteria met:**
- Show EXACT numbers: "Player Name (.XXX season BA → .XXX xBA vs arsenal, +XX points)"
- Include K% data if relevant
- Format: "Our final lean would be [specific lean] — the numbers strongly support this edge."

**If NO criteria met:**
- "No significant statistical edges meet our betting threshold in this matchup. The projections show modest advantages that don't warrant a lean."

**CRITICAL:** Do NOT suggest weak leans. A .250 to .275 jump (+25 points) reaching .275 does NOT meet criteria.

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

Return only the improved blog post. Here's the original:

{blog_post}
"""
