# app.py
import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

load_dotenv()
#DB_CONN = os.getenv("DATABASE_URL")  # postgresql://user:pass@localhost:5433/football
#if not DB_CONN:
#    raise ValueError("❌ DATABASE_URL není nastavený v .env souboru")
#engine = create_engine(DB_CONN)

DB_CONN = os.getenv("DATABASE_URL")
assert DB_CONN and DB_CONN.startswith("postgresql+psycopg2://"), "DATABASE_URL není nastavené nebo má špatný prefix"

# Debug výpis (bez hesla)
print("DB host:", DB_CONN.split("@")[1].split(":")[0])
print("DB name:", DB_CONN.split("/")[-1])

engine = create_engine(DB_CONN)

# Test připojení
with engine.connect() as conn:
    print("Test SELECT 1:", conn.execute(text("SELECT 1")).scalar())

st.set_page_config(page_title="Football Stats Explorer", layout="wide")
st.title("⚽ Football Stats Explorer")

# --- Filtry ---
with st.sidebar:
    st.header("Filtry")

    # dostupné ligy
    leagues = pd.read_sql("SELECT DISTINCT league FROM fixtures", engine)["league"].tolist()
    league = st.selectbox("Vyber ligu", leagues)

    # dostupné týmy
    teams = pd.read_sql("SELECT DISTINCT home_team AS team FROM fixtures UNION SELECT DISTINCT away_team FROM fixtures", engine)["team"].tolist()
    team = st.selectbox("Vyber tým (volitelné)", ["-- všichni --"] + teams)

    # datumový rozsah
    min_date, max_date = pd.read_sql("SELECT MIN(match_date), MAX(match_date) FROM fixtures", engine).iloc[0]
    date_range = st.date_input("Rozsah dat", [min_date, max_date])

# --- Načtení dat z fixtures ---
query = """
SELECT fixture_id, league, match_date, home_team, away_team, status
FROM fixtures
WHERE league = :league
  AND match_date BETWEEN :start AND :end
"""
params = {"league": league, "start": date_range[0], "end": date_range[1]}
fixtures_df = pd.read_sql(text(query), engine, params=params)

if team != "-- všichni --":
    fixtures_df = fixtures_df[(fixtures_df["home_team"] == team) | (fixtures_df["away_team"] == team)]

st.subheader("📋 Zápasy")
st.dataframe(fixtures_df, use_container_width=True)

# --- Statistiky ---
if not fixtures_df.empty:
    fixture_ids = tuple(fixtures_df["fixture_id"].tolist())
    stats_query = f"""
    SELECT fixture_id, team_name, shots_on_goal, shots_off_goal, total_shots,
           fouls, corner_kicks, offsides, ball_possession, yellow_cards, red_cards,
           total_passes, passes_accurate, passes_percent, expected_goals
    FROM match_statistics
    WHERE fixture_id IN :ids
    """
    stats_df = pd.read_sql(text(stats_query), engine, params={"ids": fixture_ids})

    st.subheader("📊 Statistiky")
    st.dataframe(stats_df, use_container_width=True)
else:
    st.info("Žádné zápasy pro zvolený filtr.")
