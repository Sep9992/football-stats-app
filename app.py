# app.py
import os
from datetime import date
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# --- Env & DB ---
load_dotenv()

DB_CONN = os.getenv("DATABASE_URL")
assert DB_CONN and DB_CONN.startswith("postgresql+psycopg2://"), "DATABASE_URL není nastavené nebo má špatný prefix"

engine = create_engine(DB_CONN)

# --- UI ---
st.set_page_config(page_title="Football Stats Explorer", layout="wide")
st.title("⚽ Football Stats Explorer")

# --- Filtry ---
with st.sidebar:
    st.header("Filtry")

    # dostupné ligy (s možností všichni)
    leagues = pd.read_sql("SELECT DISTINCT league FROM fixtures", engine)["league"].tolist()
    league = st.selectbox("Vyber ligu", ["-- všichni --"] + leagues)

    # dostupné týmy podle ligy + min/max datum
    if league != "-- všichni --":
        teams_query = text("""
            SELECT DISTINCT home_team AS team FROM fixtures WHERE league = :league
            UNION
            SELECT DISTINCT away_team FROM fixtures WHERE league = :league
        """)
        teams = pd.read_sql(teams_query, engine, params={"league": league})["team"].tolist()

        min_date, max_date = pd.read_sql(
            text("SELECT MIN(match_date), MAX(match_date) FROM fixtures WHERE league = :league"),
            engine, params={"league": league}
        ).iloc[0]
    else:
        teams_query = """
            SELECT DISTINCT home_team AS team FROM fixtures
            UNION
            SELECT DISTINCT away_team FROM fixtures
        """
        teams = pd.read_sql(teams_query, engine)["team"].tolist()

        min_date, max_date = pd.read_sql(
            "SELECT MIN(match_date), MAX(match_date) FROM fixtures", engine
        ).iloc[0]

    team = st.selectbox("Vyber tým (volitelné)", ["-- všichni --"] + teams)

    # ochrana, kdyby v DB nebyla žádná data
    if pd.isnull(min_date) or pd.isnull(max_date):
        min_date = max_date = date.today()

    # date_input může vracet jedno datum nebo dvojici
    date_range = st.date_input("Rozsah dat", [min_date, max_date])
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

# --- Načtení dat z fixtures ---
if league != "-- všichni --":
    query = """
    SELECT fixture_id, league, match_date, home_team, away_team, status
    FROM fixtures
    WHERE league = :league
      AND match_date BETWEEN :start AND :end
    """
    params = {"league": league, "start": start_date, "end": end_date}
else:
    query = """
    SELECT fixture_id, league, match_date, home_team, away_team, status
    FROM fixtures
    WHERE match_date BETWEEN :start AND :end
    """
    params = {"start": start_date, "end": end_date}

fixtures_df = pd.read_sql(text(query), engine, params=params)

# volitelný filtr na tým (po načtení výsledků)
if team != "-- všichni --" and not fixtures_df.empty:
    fixtures_df = fixtures_df[
        (fixtures_df["home_team"] == team) | (fixtures_df["away_team"] == team)
    ]

st.subheader("📋 Zápasy")
st.dataframe(fixtures_df, use_container_width=True)

# --- Statistiky ---
if not fixtures_df.empty:
    fixture_ids = fixtures_df["fixture_id"].tolist()

    if fixture_ids:
        # Bezpečný dotaz pro IN seznam (SQLAlchemy bind param)
        stats_query = text("""
        SELECT fixture_id, team_name, shots_on_goal, shots_off_goal, total_shots,
               fouls, corner_kicks, offsides, ball_possession, yellow_cards, red_cards,
               total_passes, passes_accurate, passes_percent, expected_goals
        FROM match_statistics
        WHERE fixture_id = ANY(:ids)
        """)
        # Postgres dokáže přijmout pole; pandas/SQLAlchemy pošleme list → psycopg2 převede na ARRAY
        stats_df = pd.read_sql(stats_query, engine, params={"ids": fixture_ids})
    else:
        # žádné fixture_ids → prázdný DataFrame
        stats_df = pd.DataFrame(columns=[
            "fixture_id","team_name","shots_on_goal","shots_off_goal","total_shots",
            "fouls","corner_kicks","offsides","ball_possession","yellow_cards","red_cards",
            "total_passes","passes_accurate","passes_percent","expected_goals"
        ])

    st.subheader("📊 Statistiky")
    st.dataframe(stats_df, use_container_width=True)
else:
    st.info("Žádné zápasy pro zvolený filtr.")

