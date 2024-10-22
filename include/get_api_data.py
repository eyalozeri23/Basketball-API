import requests
import time
import json
import logging
from requests.exceptions import RequestException, Timeout
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from airflow.exceptions import AirflowException
import os
import redis
from datetime import datetime, timezone

API_BASE_URL = os.getenv("API_BASE_URL")
TOKEN_URL = f"{API_BASE_URL}/token"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Set Redis connection string
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_DB = os.getenv("REDIS_DB")

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


def get_access_token():
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise AirflowException("Failed to obtain access token")

# Get last timetamp from redis function
def get_last_timestamp(endpoint):
    timestamp = redis_client.get(f"last_timestamp_{endpoint}")
    if timestamp:
        return timestamp.decode('utf-8')
    return None

# Set last timetamp from redis function 
def set_last_timestamp(endpoint, timestamp):
    redis_client.set(f"last_timestamp_{endpoint}", timestamp)

# Fetch the data from API by the endpoint
def fetch_data(endpoint, use_timestamp=True):
    all_data = []
    page = 1
    per_page = 100  # Set 100 per page

    # Get the last timestamp if use_timestamp is True
    last_timestamp = get_last_timestamp(endpoint) if use_timestamp else None

    # Get access token
    access_token = get_access_token()

    while True:
        try:
            url = f"{API_BASE_URL}/{endpoint}"
            params = {
                'page': page,
                'per_page': per_page
            }
            
            # Add timestamp parameter if available
            if last_timestamp:
                params['since'] = last_timestamp

            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Settin a retry mechanism for API requests
            @retry(
                stop=stop_after_attempt(5),
                wait=wait_exponential(multiplier=1, min=4, max=60),
                retry=retry_if_exception_type((RequestException, Timeout))
            )

            # API request to get data
            def make_request():
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logging.warning(f"Rate limit hit. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)
                    raise RequestException("Rate limit exceeded")
            
                
                return response.json()
            
            data = make_request()
            
            if not data:
                break  # No more data to fetch
            
            all_data.extend(data)
            
            # Update the last timestamp if available in the response
            if data and 'timestamp' in data[-1]:
                set_last_timestamp(endpoint, data[-1]['timestamp'])
            
            # Check if there's more data to fetch
            if len(data) < per_page:
                break  # This was the last page
            
            page += 1

        # Timeout exeption    
        except Timeout:
            logging.warning("Request timed out. Retrying with extended timeout.")
            response = requests.get(url, params=params, headers=headers, timeout=60) # Extended timeout
            response.raise_for_status()
            return response.json()
        
        # Request exeption
        except RequestException as e:
            logging.error(f"Error fetching data from {endpoint}: {str(e)}")
            raise AirflowException(f"Failed to fetch data from {endpoint}")
        
        # Exeption for errors in JSON
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from {endpoint}: {str(e)}")
            raise AirflowException(f"Invalid JSON response from {endpoint}")
    
    logging.info(f"Successfully fetched {len(all_data)} items from {endpoint}")
    
    # Update the last timestamp with the current time if no data was fetched
    if not all_data and use_timestamp:
        current_time = datetime.now(timezone.utc).isoformat()
        set_last_timestamp(endpoint, current_time)
    
    return all_data