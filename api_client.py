# api_client.py
import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, MatchStatistics

load_dotenv()
API_KEY = os.getenv("APISPORTS_KEY")
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY, "accept": "application/json"}

DB_CONN = os.getenv("DATABASE_URL")  # postgresql://user:pass@localhost:5433/football
engine = create_engine(DB_CONN)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

def get_fixtures(league_id, season):
    url = f"{BASE_URL}/fixtures"
    params = {"league": league_id, "season": season}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()["response"]

def get_statistics(fixture_id):
    url = f"{BASE_URL}/fixtures/statistics"
    params = {"fixture": fixture_id}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json()["response"]

def save_statistics(fixture_id, stats):
    session = Session()
    for team_stats in stats:
        team = team_stats["team"]["name"]
        data = {s["type"]: s["value"] for s in team_stats["statistics"]}
        record = MatchStatistics(
            fixture_id=fixture_id,
            team_name=team,
            shots_on_goal=data.get("Shots on Goal"),
            shots_off_goal=data.get("Shots off Goal"),
            total_shots=data.get("Total Shots"),
            possession=data.get("Ball Possession"),
            passes=data.get("Total passes"),
            passes_accurate=data.get("Passes accurate"),
            expected_goals=data.get("expected_goals")
        )
        session.merge(record)
    session.commit()
    session.close()

def collect_league_stats(league_id, season=2025):
    fixtures = get_fixtures(league_id, season)
    for f in fixtures:
        fid = f["fixture"]["id"]
        status = f["fixture"]["status"]["short"]
        if status == "FT":
            stats = get_statistics(fid)
            if stats:
                save_statistics(fid, stats)
                print(f"✅ Uloženo {fid} {f['teams']['home']['name']} vs {f['teams']['away']['name']}")
            else:
                print(f"❌ {fid} bez statistik")