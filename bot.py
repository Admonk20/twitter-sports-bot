import os
import requests
import schedule
import time
import threading
import sqlite3
from flask import Flask, jsonify
import logging
import sys
import traceback
import socket
from requests_oauthlib import OAuth1
import random
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Load API keys from environment variables
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET, BEARER_TOKEN, OPENAI_API_KEY, ODDS_API_KEY]):
    logger.error("Missing API credentials. Ensure they are set in the environment.")
    sys.exit(1)

openai.api_key = OPENAI_API_KEY

# Initialize database
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tweets (id INTEGER PRIMARY KEY, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mentions (id INTEGER PRIMARY KEY, mention_text TEXT, username TEXT, processed INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Create a Flask app
app = Flask(__name__)

def rate_limited_request(url):
    try:
        response = requests.get(url)
        if response.status_code == 429:  # Rate limit exceeded
            logger.warning("Rate limit hit. Waiting before retrying...")
            time.sleep(60)
            return rate_limited_request(url)
        return response
    except Exception as e:
        logger.error(f"Error making request: {str(e)}")
        return None

def fetch_sports_predictions():
    try:
        sport_key = "soccer_epl"
        url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h,spreads"
        response = rate_limited_request(url)
        
        if response and response.status_code == 200:
            data = response.json()
            if not data:
                return "No current sports data available."
            
            game = random.choice(data)
            home_team = game["home_team"]
            away_team = game["away_team"]
            bookmaker = next((b for b in game["bookmakers"] if b["key"] == "fanduel"), game["bookmakers"][0])
            odds = bookmaker["markets"][0]["outcomes"]
            prediction = f"{home_team} vs {away_team} - Odds: {odds[0]['price']} for {odds[0]['name']}, {odds[1]['price']} for {odds[1]['name']}"
            return prediction
        else:
            return "Unable to fetch sports predictions at the moment."
    except Exception as e:
        logger.error(f"Error fetching Odds API data: {str(e)}")
        return "Error fetching live sports data."

def post_tweet(reply_to=None, username=None, message=None):
    try:
        if not message:
            message = fetch_sports_predictions()
        
        tweet_text = f"@{username} {message}" if username else message
        
        url = "https://api.twitter.com/2/tweets"
        auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        payload = {"text": tweet_text}
        if reply_to:
            payload["in_reply_to_status_id"] = reply_to
        
        response = requests.post(url, json=payload, auth=auth)
        
        if response.status_code == 201:
            conn = sqlite3.connect("bot.db")
            c = conn.cursor()
            c.execute("INSERT INTO tweets (content) VALUES (?)", (tweet_text,))
            conn.commit()
            conn.close()
            return {"success": True, "tweet": tweet_text}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/")
def home():
    return "MAX Sports Bot is running!"

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})

@app.route("/trigger")
def trigger_message():
    result = post_tweet()
    return jsonify(result)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    logger.info("Scheduler started successfully")

schedule.every().day.at("12:00").do(post_tweet)
schedule.every(5).minutes.do(fetch_sports_predictions)

if __name__ == "__main__":
    logger.info("Starting Flask app...")
    start_scheduler()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
