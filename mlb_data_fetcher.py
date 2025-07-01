# mlb_data_fetcher.py
import requests
import json
from datetime import datetime

class MLBDataFetcher:
    def __init__(self):
        self.mlb_api_url = "https://mlb-matchup-api-savant.onrender.com/latest"
        self.umpire_api_url = "https://umpire-json-api.onrender.com"
    
    def get_mlb_data(self):
        """Fetch MLB matchup data"""
        try:
            print("🌐 Fetching MLB data...")
            response = requests.get(self.mlb_api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Got {len(data.get('reports', []))} games")
            return data.get('reports', [])
        except Exception as e:
            print(f"❌ Error fetching MLB data: {e}")
            return []

    def get_umpire_data(self):
        """Fetch umpire data"""
        try:
            print("🌐 Fetching umpire data...")
            response = requests.get(self.umpire_api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"✅ Got umpire data for {len(data)} umpires")
            return data
        except Exception as e:
            print(f"❌ Error fetching umpire data: {e}")
            return []

    def find_game_umpire(self, umpires, matchup):
        """Find the umpire for a specific game matchup"""
        for ump in umpires:
            if ump.get('matchup', '-') == matchup:
                return ump
        
        if ' @ ' in matchup:
            away_team, home_team = matchup.split(' @ ')
            for ump in umpires:
                ump_matchup = ump.get('matchup', '-')
                if away_team in ump_matchup and home_team in ump_matchup:
                    return ump
        
        return None

    def format_pitcher_arsenal(self, pitcher_data):
        """Format pitcher arsenal for blog content"""
        arsenal = pitcher_data.get('arsenal', {})
        if not arsenal:
            return "Mixed arsenal"
        
        sorted_pitches = sorted(arsenal.items(), key=lambda x: x[1]['usage_rate'], reverse=True)
        arsenal_text = []
        
        for pitch_type, pitch_data in sorted_pitches:
            pitch_name = pitch_data.get('name', pitch_type)
            usage = pitch_data['usage_rate'] * 100
            speed = pitch_data['avg_speed']
            arsenal_text.append(f"{pitch_name} ({usage:.0f}% usage, {speed:.1f} mph)")
        
        return "; ".join(arsenal_text)

    def calculate_lineup_advantage(self, key_matchups, pitcher_name):
        """Calculate if lineup has advantage vs pitcher"""
        pitcher_matchups = [m for m in key_matchups if m.get('vs_pitcher') == pitcher_name]
        reliable_matchups = [m for m in pitcher_matchups if m.get('reliability', '').upper() in ['MEDIUM', 'HIGH']]
        
        if not reliable_matchups:
            return 0.0, []
        
        ba_diffs = []
        top_performers = []
        
        for matchup in reliable_matchups:
            baseline = matchup.get('baseline_stats', {})
            season_ba = baseline.get('season_avg', 0.250) if baseline else 0.250
            arsenal_ba = matchup.get('weighted_est_ba', 0.250)
            ba_diff = arsenal_ba - season_ba
            ba_diffs.append(ba_diff)
            
            # Track significant performers
            if abs(ba_diff) > 0.020:  # 20+ point difference
                batter = matchup.get('batter', 'Unknown')
                batter_name = batter.replace(', ', ' ').split()
                batter_display = f"{batter_name[1]} {batter_name[0]}" if len(batter_name) >= 2 else batter
                
                top_performers.append({
                    'name': batter_display,
                    'season_ba': season_ba,
                    'arsenal_ba': arsenal_ba,
                    'advantage': 'strong' if ba_diff > 0.020 else 'poor'
                })
        
        avg_advantage = sum(ba_diffs) / len(ba_diffs) if ba_diffs else 0.0
        return avg_advantage, top_performers

    def get_blog_topics_from_games(self):
        """Generate blog topics from current MLB games"""
        mlb_reports = self.get_mlb_data()
        umpires = self.get_umpire_data()
        
        if not mlb_reports:
            return []
        
        blog_topics = []
        
        for game_report in mlb_reports:
            try:
                matchup = game_report.get('matchup', 'Unknown')
                if ' @ ' not in matchup:
                    continue
                    
                away_team, home_team = matchup.split(' @ ')
                
                # Get pitcher data
                away_pitcher_data = game_report['pitchers']['away']
                home_pitcher_data = game_report['pitchers']['home']
                
                # Format pitcher names
                away_pitcher_name = away_pitcher_data.get('name', 'Unknown').replace(', ', ' ').split()
                away_pitcher_display = f"{away_pitcher_name[1]} {away_pitcher_name[0]}" if len(away_pitcher_name) >= 2 else away_pitcher_data.get('name', 'Unknown')
                
                home_pitcher_name = home_pitcher_data.get('name', 'Unknown').replace(', ', ' ').split()
                home_pitcher_display = f"{home_pitcher_name[1]} {home_pitcher_name[0]}" if len(home_pitcher_name) >= 2 else home_pitcher_data.get('name', 'Unknown')
                
                # Calculate lineup advantages
                key_matchups = game_report['key_matchups']
                away_advantage, away_performers = self.calculate_lineup_advantage(key_matchups, home_pitcher_data['name'])
                home_advantage, home_performers = self.calculate_lineup_advantage(key_matchups, away_pitcher_data['name'])
                
                # Find umpire
                umpire = self.find_game_umpire(umpires, matchup)
                
                # Create comprehensive game data
                game_data = {
                    'matchup': matchup,
                    'away_team': away_team,
                    'home_team': home_team,
                    'away_pitcher': {
                        'name': away_pitcher_display,
                        'arsenal': self.format_pitcher_arsenal(away_pitcher_data)
                    },
                    'home_pitcher': {
                        'name': home_pitcher_display,
                        'arsenal': self.format_pitcher_arsenal(home_pitcher_data)
                    },
                    'away_lineup_advantage': away_advantage,
                    'home_lineup_advantage': home_advantage,
                    'away_key_performers': away_performers,
                    'home_key_performers': home_performers,
                    'umpire': umpire['umpire'] if umpire else 'TBA',
                    'umpire_k_boost': umpire['k_boost'] if umpire else '1.0x',
                    'umpire_bb_boost': umpire['bb_boost'] if umpire else '1.0x'
                }
                
                # Generate topic and keywords based on game analysis
                topic = f"{away_team} vs {home_team} MLB Betting Preview"
                
                # Dynamic keywords based on game situation
                keywords = [
                    f"{away_team.lower()}", f"{home_team.lower()}", 
                    "mlb betting", "baseball preview", "pitcher analysis",
                    f"{away_pitcher_display.lower().replace(' ', '-')}", 
                    f"{home_pitcher_display.lower().replace(' ', '-')}",
                    "lineup matchups", "umpire analysis"
                ]
                
                # Add situational keywords
                if abs(away_advantage) > 0.015 or abs(home_advantage) > 0.015:
                    keywords.extend(["pitcher advantage", "matchup edge"])
                
                if umpire and umpire['umpire'] != 'TBA':
                    k_multiplier = float(umpire['k_boost'].replace('x', ''))
                    if k_multiplier > 1.1:
                        keywords.extend(["strikeout props", "pitcher friendly umpire"])
                    elif k_multiplier < 0.9:
                        keywords.extend(["hitter friendly umpire", "contact plays"])
                
                blog_topics.append({
                    'topic': topic,
                    'keywords': keywords,
                    'game_data': game_data
                })
                
            except Exception as e:
                print(f"❌ Error processing game {matchup}: {e}")
                continue
        
        return blog_topics
