import os
from dotenv import load_dotenv
import tweepy
import requests
import schedule
import time
import random
import threading
from flask import Flask

# Load environment variables from .env file
load_dotenv()

# Get the port from the environment variable (default to 8080)
PORT = int(os.getenv("PORT", 8080))

# Create a Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "MAX Sports Bot is running!"

# Twitter API keys
API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Sports data API key
SPORTS_API_KEY = "e249e081590f7fed66b9e620f31d7eb1"

# Authenticate with Twitter
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# MAX's catchphrases
CATCHPHRASES = [
    "The numbers are in—let’s break it down!",
    "Here’s the play within the play you might’ve missed.",
    "It’s not just a game; it’s a puzzle, and I’ve got the pieces.",
    "Stats don’t lie, and neither do I!",
    "Let’s turn these numbers into knowledge!"
]

# Fetch sports data from The Odds API
def fetch_data():
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={SPORTS_API_KEY}&regions=us"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Generate prediction with reasoning
def generate_prediction():
    data = fetch_data()
    
    if data:
        # Example: Analyze data and generate a prediction
        team_a = data[0]['teams'][0]  # Team A
        team_b = data[0]['teams'][1]  # Team B
        odds_a = data[0]['sites'][0]['odds']['h2h'][0]  # Odds for Team A
        odds_b = data[0]['sites'][0]['odds']['h2h'][1]  # Odds for Team B
        
        # Simple reasoning based on odds
        if odds_a < odds_b:
            prediction = f"{team_a} is favored to win against {team_b} with odds of {odds_a}!"
        else:
            prediction = f"{team_b} is favored to win against {team_a} with odds of {odds_b}!"
    else:
        prediction = "No data available for today's games. Stay tuned!"
    
    return prediction

# Post tweet with MAX's personality
def post_tweet():
    prediction = generate_prediction()
    catchphrase = random.choice(CATCHPHRASES)  # Randomly select a catchphrase
    tweet = f"🚨 MAX's Game Prediction: {prediction} 🚨\n\n{catchphrase}\n#SportsBetting #NBA"
    try:
        api.update_status(tweet)
    except tweepy.TweepError as e:
        print(f"Error posting tweet: {e}")

# Fetch mentions
def fetch_mentions():
    mentions = api.mentions_timeline(count=5)  # Fetch the last 5 mentions
    return mentions

# Respond to mentions
def respond_to_mentions():
    mentions = fetch_mentions()
    for mention in mentions:
        tweet_id = mention.id
        username = mention.user.screen_name
        text = mention.text.lower()

        # Example: Respond to a query about predictions
        if "prediction" in text:
            prediction = generate_prediction()
            response = f"@{username} Here's MAX's prediction: {prediction} 🚀 #SportsBetting #NBA"
            api.update_status(response, in_reply_to_status_id=tweet_id)

        # Example: Respond to a query about stats
        elif "stats" in text:
            response = f"@{username} MAX is crunching the numbers for you! Stay tuned for detailed stats. 📊 #SportsAnalytics"
            api.update_status(response, in_reply_to_status_id=tweet_id)

# Schedule tasks
schedule.every().day.at("09:00").do(post_tweet)  # Post a prediction every day at 9 AM
schedule.every(15).minutes.do(respond_to_mentions)  # Check for mentions every 10 minutes

# Function to run the scheduler in a separate thread
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Run the Flask app and scheduler
if __name__ == "__main__":
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True  # Daemonize thread to exit when the main program exits
    scheduler_thread.start()

    # Start the Flask app in production mode
    app.run(host="0.0.0.0", port=PORT, debug=False)
