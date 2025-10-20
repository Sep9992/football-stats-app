# main.py
import schedule
import time
from api_client import init_db, collect_league_stats

LEAGUES = [39, 140, 78, 135, 61, 88, 94, 2, 3, 344]  # TOP 10 lig
SEASON = 2025

def job():
    for league_id in LEAGUES:
        collect_league_stats(league_id, SEASON)

if __name__ == "__main__":
    init_db()
    schedule.every(1).hours.do(job)

    print("🚀 Collector běží... (CTRL+C pro ukončení)")
    while True:
        schedule.run_pending()
        time.sleep(1)
