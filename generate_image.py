# generate_image.py
from config import OPENAI_API_KEY
from openai import OpenAI
import random

client = OpenAI(api_key=OPENAI_API_KEY)

# MLB team code mapping for ESPN logo URLs
TEAM_LOGOS = {
    'NYY': 'nyy', 'Yankees': 'nyy',
    'TOR': 'tor', 'Blue Jays': 'tor',
    'BOS': 'bos', 'Red Sox': 'bos', 
    'LAD': 'lad', 'Dodgers': 'lad',
    'SF': 'sf', 'Giants': 'sf',
    'HOU': 'hou', 'Astros': 'hou',
    'ATL': 'atl', 'Braves': 'atl',
    'NYM': 'nym', 'Mets': 'nym',
    'PHI': 'phi', 'Phillies': 'phi',
    'WSN': 'wsh', 'Nationals': 'wsh',
    'MIA': 'mia', 'Marlins': 'mia',
    'CHC': 'chc', 'Cubs': 'chc',
    'MIL': 'mil', 'Brewers': 'mil',
    'STL': 'stl', 'Cardinals': 'stl',
    'CIN': 'cin', 'Reds': 'cin',
    'PIT': 'pit', 'Pirates': 'pit',
    'LAA': 'laa', 'Angels': 'laa',
    'SEA': 'sea', 'Mariners': 'sea',
    'TEX': 'tex', 'Rangers': 'tex',
    'OAK': 'oak', 'Athletics': 'oak',
    'MIN': 'min', 'Twins': 'min',
    'CWS': 'chw', 'White Sox': 'chw',
    'CLE': 'cle', 'Guardians': 'cle',
    'DET': 'det', 'Tigers': 'det',
    'KC': 'kc', 'Royals': 'kc',
    'TB': 'tb', 'Rays': 'tb',
    'BAL': 'bal', 'Orioles': 'bal',
    'COL': 'col', 'Rockies': 'col',
    'ARI': 'ari', 'Diamondbacks': 'ari',
    'SD': 'sd', 'Padres': 'sd'
}

def get_team_logo_url(team_name):
    """Get official team logo URL from ESPN"""
    # Clean up team name and try to match
    team_clean = team_name.strip().upper()
    
    # Direct mapping for common variations
    team_mappings = {
        'YANKEES': 'nyy', 'NEW YORK YANKEES': 'nyy',
        'BLUE JAYS': 'tor', 'TORONTO BLUE JAYS': 'tor', 'TORONTO': 'tor',
        'RED SOX': 'bos', 'BOSTON RED SOX': 'bos', 'BOSTON': 'bos',
        'DODGERS': 'lad', 'LOS ANGELES DODGERS': 'lad',
        'GIANTS': 'sf', 'SAN FRANCISCO GIANTS': 'sf',
        'ASTROS': 'hou', 'HOUSTON ASTROS': 'hou',
        'BRAVES': 'atl', 'ATLANTA BRAVES': 'atl',
        'METS': 'nym', 'NEW YORK METS': 'nym',
        'PHILLIES': 'phi', 'PHILADELPHIA PHILLIES': 'phi',
        'NATIONALS': 'wsh', 'WASHINGTON NATIONALS': 'wsh',
        'MARLINS': 'mia', 'MIAMI MARLINS': 'mia',
        'CUBS': 'chc', 'CHICAGO CUBS': 'chc',
        'BREWERS': 'mil', 'MILWAUKEE BREWERS': 'mil',
        'CARDINALS': 'stl', 'ST LOUIS CARDINALS': 'stl',
        'REDS': 'cin', 'CINCINNATI REDS': 'cin',
        'PIRATES': 'pit', 'PITTSBURGH PIRATES': 'pit',
        'ANGELS': 'laa', 'LOS ANGELES ANGELS': 'laa',
        'MARINERS': 'sea', 'SEATTLE MARINERS': 'sea',
        'RANGERS': 'tex', 'TEXAS RANGERS': 'tex',
        'ATHLETICS': 'oak', 'OAKLAND ATHLETICS': 'oak',
        'TWINS': 'min', 'MINNESOTA TWINS': 'min',
        'WHITE SOX': 'chw', 'CHICAGO WHITE SOX': 'chw',
        'GUARDIANS': 'cle', 'CLEVELAND GUARDIANS': 'cle',
        'TIGERS': 'det', 'DETROIT TIGERS': 'det',
        'ROYALS': 'kc', 'KANSAS CITY ROYALS': 'kc',
        'RAYS': 'tb', 'TAMPA BAY RAYS': 'tb',
        'ORIOLES': 'bal', 'BALTIMORE ORIOLES': 'bal',
        'ROCKIES': 'col', 'COLORADO ROCKIES': 'col',
        'DIAMONDBACKS': 'ari', 'ARIZONA DIAMONDBACKS': 'ari',
        'PADRES': 'sd', 'SAN DIEGO PADRES': 'sd'
    }
    
    # Try exact match first
    if team_clean in TEAM_LOGOS:
        team_code = TEAM_LOGOS[team_clean]
        return f"https://a.espncdn.com/i/teamlogos/mlb/500/{team_code}.png"
    
    # Try team name mappings
    if team_clean in team_mappings:
        team_code = team_mappings[team_clean]
        return f"https://a.espncdn.com/i/teamlogos/mlb/500/{team_code}.png"
    
    # Try partial matches
    for key, code in TEAM_LOGOS.items():
        if key in team_clean or team_clean in key:
            return f"https://a.espncdn.com/i/teamlogos/mlb/500/{code}.png"
    
    # Try partial matches with team name mappings
    for name, code in team_mappings.items():
        if name in team_clean or team_clean in name:
            return f"https://a.espncdn.com/i/teamlogos/mlb/500/{code}.png"
    
    print(f"⚠️  No logo match found for: {team_name}")
    # Default to MLB logo if no match
    return "https://a.espncdn.com/i/teamlogos/mlb/500/mlb.png"

def extract_teams_from_topic(topic):
    """Extract team names from blog topic"""
    # Example: "Yankees vs Blue Jays MLB Betting Preview"
    try:
        if ' vs ' in topic:
            teams_part = topic.split(' vs ')[0], topic.split(' vs ')[1].split(' ')[0]
            return teams_part[0].strip(), teams_part[1].strip()
        elif ' @ ' in topic:
            teams_part = topic.split(' @ ')
            return teams_part[0].strip(), teams_part[1].strip()
    except:
        pass
    
    # Fallback - try to find any team names in the topic
    for team_name in TEAM_LOGOS.keys():
        if team_name.lower() in topic.lower():
            return team_name, None
    
    return None, None

def generate_image_description(topic):
    """Generate a simple description for team logo usage"""
    away_team, home_team = extract_teams_from_topic(topic)
    
    if away_team and home_team:
        return f"MLB matchup featuring {away_team} vs {home_team} team logos"
    elif away_team:
        return f"MLB game featuring {away_team} team logo"
    else:
        return "MLB baseball game with official team branding"

def generate_image(image_description):
    """Return team logo URL instead of generating AI image"""
    # Extract topic from the calling context or use a fallback approach
    # For now, we'll return a generic MLB logo, but this could be enhanced
    
    # Try to extract team from description
    for team_name in TEAM_LOGOS.keys():
        if team_name.lower() in image_description.lower():
            return get_team_logo_url(team_name)
    
    # Return MLB logo as fallback
    return "https://a.espncdn.com/i/teamlogos/mlb/500/mlb.png"

def generate_team_logos_for_matchup(away_team, home_team):
    """Generate both team logos for a matchup"""
    away_logo = get_team_logo_url(away_team)
    home_logo = get_team_logo_url(home_team)
    
    return {
        'away_team': away_team,
        'away_logo': away_logo,
        'home_team': home_team,
        'home_logo': home_logo,
        'combined_url': f"Matchup: {away_team} ({away_logo}) @ {home_team} ({home_logo})"
    }

# Test function
if __name__ == "__main__":
    print("Testing team logo URLs:")
    test_teams = ['NYY', 'TOR', 'BOS', 'LAD']
    for team in test_teams:
        url = get_team_logo_url(team)
        print(f"{team}: {url}")
    
    print("\nTesting matchup extraction:")
    test_topic = "Yankees vs Blue Jays MLB Betting Preview"
    away, home = extract_teams_from_topic(test_topic)
    print(f"Away: {away}, Home: {home}")
