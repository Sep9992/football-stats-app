#models.py
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Numeric,
    TIMESTAMP, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Fixture(Base):
    __tablename__ = "fixtures"

    fixture_id = Column(BigInteger, primary_key=True, index=True)
    league = Column(String(100), nullable=False)
    match_date = Column(TIMESTAMP, nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    status = Column(String(10))  # např. FT, NS, HT

    # vztah na statistiky
    statistics = relationship("MatchStatistics", back_populates="fixture")

    def __repr__(self):
        return f"<Fixture(id={self.fixture_id}, {self.home_team} vs {self.away_team}, league={self.league})>"


class MatchStatistics(Base):
    __tablename__ = "match_statistics"

    fixture_id = Column(BigInteger, ForeignKey("fixtures.fixture_id"), primary_key=True)
    team_name = Column(String(100), primary_key=True)

    league = Column(String(100), nullable=False)
    match_date = Column(TIMESTAMP, nullable=False)

    shots_on_goal = Column(Integer)
    shots_off_goal = Column(Integer)
    total_shots = Column(Integer)
    blocked_shots = Column(Integer)
    shots_insidebox = Column(Integer)
    shots_outsidebox = Column(Integer)
    fouls = Column(Integer)
    corner_kicks = Column(Integer)
    offsides = Column(Integer)
    ball_possession = Column(Numeric(5, 2))  # ukládej jako číslo (např. 55.0 místo '55%')
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    goalkeeper_saves = Column(Integer)
    total_passes = Column(Integer)
    passes_accurate = Column(Integer)
    passes_percent = Column(Numeric(5, 2))
    expected_goals = Column(Numeric(4, 2))

    # vztah zpět na Fixture
    fixture = relationship("Fixture", back_populates="statistics")

    def __repr__(self):
        return f"<MatchStatistics(fixture={self.fixture_id}, team={self.team_name})>"
