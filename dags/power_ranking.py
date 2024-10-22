from airflow.decorators import dag, task, task_group
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowException
from datetime import datetime
import os
import logging

API_BASE_URL = os.getenv("API_BASE_URL")
POSTGRES_CONN_ID = "basketball_db" # Based on the postgres conn id from airflow ui


default_args = {
    'owner': 'Eyal Ozeri',
    'started_at': datetime(2024,7,30)

}

@dag(
    default_args=default_args,
    schedule='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['basketball_power_ranking']
)



def power_ranking():
    
    # Create hook to interact with postgres through airflow
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)

    @task
    # Create power ranking table in postgres
    def create_power_ranking_table():
        try:
            hook.run("""
                CREATE TABLE IF NOT EXISTS power_ranking (
                    rank INTEGER PRIMARY KEY,
                    team_id INTEGER REFERENCES teams(id),
                    team_name VARCHAR(100),
                    wins INTEGER,
                    losses INTEGER,
                    points INTEGER,
                    score_differential INTEGER
                )
            """)
            logging.info("Power ranking table created or already exists")
        except Exception as e:
            logging.error(f"Error creating power ranking table: {str(e)}")
            raise AirflowException("Failed to create power ranking table")

    @task
    # Calculate team's points based on win or loss
    def calculate_power_rankings():
        
        try:
            # Calculate team stats
            hook.run("""
                WITH team_stats AS (
                    SELECT 
                        t.id AS team_id,
                        t.name AS team_name,
                        SUM(CASE 
                            WHEN g.home_team_id = t.id AND g.home_team_score > g.away_team_score THEN 1
                            WHEN g.away_team_id = t.id AND g.away_team_score > g.home_team_score THEN 1
                            ELSE 0 
                        END) AS wins,
                        SUM(CASE 
                            WHEN g.home_team_id = t.id AND g.home_team_score < g.away_team_score THEN 1
                            WHEN g.away_team_id = t.id AND g.away_team_score < g.home_team_score THEN 1
                            ELSE 0 
                        END) AS losses,
                        SUM(CASE 
                            WHEN g.home_team_id = t.id THEN g.home_team_score - g.away_team_score
                            ELSE g.away_team_score - g.home_team_score 
                        END) AS score_differential
                    FROM teams t
                    LEFT JOIN games g ON t.id = g.home_team_id OR t.id = g.away_team_id
                    GROUP BY t.id, t.name
                ),
                ranked_teams AS (
                    SELECT 
                        team_id,
                        team_name,
                        wins,
                        losses,
                        (wins * 2 + losses) AS points,
                        score_differential,
                        ROW_NUMBER() OVER (ORDER BY (wins * 2 + losses) DESC, score_differential DESC) AS rank
                    FROM team_stats
                )
                INSERT INTO power_ranking (rank, team_id, team_name, wins, losses, points, score_differential)
                SELECT rank, team_id, team_name, wins, losses, points, score_differential
                FROM ranked_teams
                ON CONFLICT (rank) DO UPDATE SET
                    team_id = EXCLUDED.team_id,
                    team_name = EXCLUDED.team_name,
                    wins = EXCLUDED.wins,
                    losses = EXCLUDED.losses,
                    points = EXCLUDED.points,
                    score_differential = EXCLUDED.score_differential
            """)
            logging.info("Power rankings calculated and updated successfully")
        except Exception as e:
            logging.error(f"Error calculating power rankings: {str(e)}")
            raise AirflowException("Failed to calculate power rankings")

    @task
    # Log the new ranking table for directly view it from Airflow UI
    def log_power_rankings():

        try:
            rankings = hook.get_records("SELECT * FROM power_ranking ORDER BY rank")
            logging.info("Current Power Rankings:")
            for rank in rankings:
                logging.info(f"Rank {rank[0]}: {rank[2]} (ID: {rank[1]}) - Points: {rank[5]}, Score Differential: {rank[6]}")
        except Exception as e:
            logging.error(f"Error logging power rankings: {str(e)}")
            raise AirflowException("Failed to log power rankings")
        

    # Set tasks dependencies

    create_table = create_power_ranking_table()
    calculate_rankings = calculate_power_rankings()
    log_rankings = log_power_rankings()

    create_table >> calculate_rankings >> log_rankings

power_ranking()
