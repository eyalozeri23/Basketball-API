# Basketball Data Project

This project implements a comprehensive data pipeline for basketball statistics, including an API built from scratch for data ingestion and Airflow DAGs for data processing, storage in PostgreSQL, and analysis.

## Project Overview

The Basketball Data Pipeline consists of two main components:
1. A FastAPI-based API for serving basketball data
2. Airflow DAGs for data ingestion, processing, and power ranking calculation

The project uses Astro CLI for initial setup and management of Airflow in a Docker environment.
Astro CLI provides a pre-configured PostgreSQL connection and creates a docker-compose.yml file in the background, setting up postgres, triggerer, scheduler, and webserver containers.
For creating your own infrastructure setup, you can create a docker-compose-override.yml to override the default setup of Astro CLI.

## API

The API is built using FastAPI and provides endpoints for teams and games data.

### Endpoints

- `/teams`: Get all teams or create a new team
- `/teams/{team_id}`: Get a specific team
- `/games`: Get all games or create a new game
- `/games/{game_id}`: Get a specific game

### Rate Limiting

The API implements rate limiting to prevent abuse:
- 20 requests per minute for GET endpoints
- 10 requests per minute for POST endpoints

## Airflow DAGs

### 1. Data Ingestion DAG (basketball_data_insert.py)

This DAG is responsible for fetching data from the API and loading it into a PostgreSQL database.

Key features:
- Fetches teams and games data from the API
- Handles pagination and rate limiting
- Uses Redis to store the last fetched timestamp for incremental loads (fast retrieval)
- Loads data into PostgreSQL tables

### 2. Power Ranking DAG (basketball_power_ranking.py)

This DAG calculates and updates power rankings for teams based on their performance.

Key features:
- Calculates team rankings based on wins, losses, and score differentials
- Updates a `power_ranking` table in PostgreSQL
- Logs the current rankings for easy viewing

## Setup

1. Clone the repository:

```bash
git clone https://github.com/your-username/basketball-data-project.git
cd basketball-data-project
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Set up the API:

- Run the API:

```bash
python run.py
```

- The API should now be running at `http://localhost:8000`
- Access the Swagger UI at `http://localhost:8000/docs` to explore and test the available endpoints.

4. Set up Airflow using Astro CLI:

- Install Astro CLI:
  - Linux:
    ```bash
    curl -sSL install.astronomer.io | sudo bash -s
    ```
  - Windows WSL (PowerShell):
    ```powershell
    winget install -e --id Astronomer.Astro
    ```

- Initialize Airflow environment:
```bash
astro dev init
```

- Start Airflow:
```bash
astro dev start
```

5. Configure Airflow connections:
- Set up a PostgreSQL connection named "basketball_db", use the default connection string generated from Astro CLI
- Configure Redis connection if using timestamp storage for API ingest

6. Place the DAG files in your Airflow DAGs folder

## Environment Variables

Ensure the following environment variables are set:
- `API_BASE_URL`: URL of your FastAPI application
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` (if using Redis)
- `PORT` (for the API server)

## Usage

1. Start your FastAPI application
2. Ensure Airflow is running (use Astro CLI commands)
3. Trigger the DAGs manually or let them run on their scheduled intervals
4. Run tasks manually for testing by entering the scheduler container:

```bash
astro dev bash
```

## Monitoring

- Use the Airflow UI to monitor DAG runs and task statuses
- Use Swagger UI for testing the API
- Check Airflow logs for detailed information, including power ranking results

## Contributing

Contributions to improve the project are welcome. Please submit pull requests with any enhancements.

## License

All rights reserved. Copyright © 2024 Eyal Ozeri.