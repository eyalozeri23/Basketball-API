from airflow.decorators import dag, task, task_group
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowException
from datetime import datetime
import logging


from include.get_api_data import fetch_data # Import fetch_data function from include for API read

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
    tags=['basketball']
)

def basketball_data_pipeline():


    # Set task group for parallel ingest
    @task_group(group_id='ingest_data')
    def ingest_data():

        # Fetch teams data from API
        @task(task_id="fetch_teams_data")
        def fetch_teams_data():
            return fetch_data('teams')

        # Fetch games data from API
        @task(task_id="fetch_games_data")
        def fetch_games_data():
            return fetch_data('games')
        
        teams_data = fetch_teams_data()
        games_data = fetch_games_data()

        return {'teams' : teams_data, 'games' : games_data}
        

    

    # Set task group for parallel load
    @task_group(group_id='load_data')
    def load_data(data):

        # Create the dedicated tables on postgres in case its not exists
        def create_table(hook, table_name, schema):
            try:
                hook.run(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
            except Exception as e:
                logging.error(f"Error creating table {table_name}: {str(e)}")
                raise AirflowException(f"Failed to create table {table_name}")

        @task
        def load_teams_table(teams_data):

            # Set hook for interact with postgres through airflow
            hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
            
            create_table(hook, "teams", """
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                city VARCHAR(100) NOT NULL,
                primary_color VARCHAR(50)
            """)

            try:

                # Upsert teams data from API
                for team in teams_data:
                    hook.run(
                        """
                        INSERT INTO teams (id, name, city, primary_color) 
                        VALUES (%s, %s, %s, %s) 
                        ON CONFLICT (id) DO UPDATE SET 
                            name = EXCLUDED.name, 
                            city = EXCLUDED.city, 
                            primary_color = EXCLUDED.primary_color
                        """,
                        parameters=(
                            team['id'],
                            team['name'],
                            team['city'],
                            team['primary_color']
                        )
                    )
            except Exception as e:
                logging.error(f"Error inserting team data: {str(e)}")
                raise AirflowException("Failed to insert team data")

        @task
        def load_games_table(games_data):

            # Set hook for interact with postgres through airflow
            hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
            
            create_table(hook, "games", """
                id SERIAL PRIMARY KEY,
                game_date DATE NOT NULL,
                home_team_id INTEGER REFERENCES teams(id),
                away_team_id INTEGER REFERENCES teams(id),
                home_team_score INTEGER,
                away_team_score INTEGER
            """)

            try:

                # Upsert games data from API
                for game in games_data:
                    hook.run(
                        """
                        INSERT INTO games (id, game_date, home_team_id, away_team_id, home_team_score, away_team_score) 
                        VALUES (%s, %s, %s, %s, %s, %s) 
                        ON CONFLICT (id) DO UPDATE SET 
                            game_date = EXCLUDED.game_date, 
                            home_team_id = EXCLUDED.home_team_id, 
                            away_team_id = EXCLUDED.away_team_id, 
                            home_team_score = EXCLUDED.home_team_score, 
                            away_team_score = EXCLUDED.away_team_score
                        """,
                        parameters=(
                            game['id'],
                            game['game_date'],
                            game['home_team_id'],
                            game['away_team_id'],
                            game['home_team_score'],
                            game['away_team_score']
                        )
                    )
            except Exception as e:
                logging.error(f"Error inserting game data: {str(e)}")
                raise AirflowException("Failed to insert game data")

        load_teams_table(data['teams'])
        load_games_table(data['games'])

    # Declair tasks dependencies
    ingested_data = ingest_data()
    load_data(ingested_data)

basketball_data_pipeline()

