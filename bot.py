import os
import tweepy
import schedule
import time
import random
import threading
from flask import Flask, jsonify
import logging
import sys
import traceback
import socket

# Configure logging with more verbose output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Also enable Flask's debug logging
logging.getLogger('werkzeug').setLevel(logging.DEBUG)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return False
        except socket.error:
            return True

print("\n=== Starting MAX Sports Bot ===\n")

try:
    # Create a Flask app
    app = Flask(__name__)
    print("Flask app created successfully")

    # Twitter API keys directly in code
    API_KEY = "2C5WR3QFMzqHQGYRNyOYb4rz7"
    API_SECRET = "JxPUBl4Inovj6eo9WcjnxnZlOEYjyx6jVxISjyeGonO5k7sjux"
    ACCESS_TOKEN = "1881434884427976705-Gje1mKZYjNFofMWdsXJNSB5BU2NYy4"
    ACCESS_TOKEN_SECRET = "02uLEFgbNE69S5MKVQYFmRmcnZNk3O4nbkMeXDOn8RvSm"

    print("Twitter API credentials loaded")

    # Authenticate with Twitter
    print("\nAuthenticating with Twitter...")
    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth=auth)
    print("Twitter authentication successful!")

except Exception as e:
    print(f"\nERROR during initialization: {str(e)}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)

def post_tweet():
    """Post a tweet with sports prediction"""
    try:
        print("\nGenerating new tweet...")
        predictions = [
            "The Lakers are favored to win against the Warriors tonight! Their strong defense and recent momentum give them the edge. 🏀",
            "Expecting a high-scoring game between the Celtics and Nets! Both teams are on fire offensively. 🔥",
            "The Bucks look unstoppable tonight against the Hawks. Their size advantage will be crucial. 💪",
            "Close game expected between Heat and 76ers, but Miami's home court advantage could be the difference! 🌴",
            "The Suns are set to shine against the Clippers tonight! Their backcourt is looking unstoppable. ☀️"
        ]
        
        catchphrases = [
            "The numbers don't lie! 📊",
            "Let's break it down! 🎯",
            "Game on! 🔥",
            "Time to ball! 🏀",
            "Watch this space! 👀",
            "Trust the process! 💯",
            "Let's get it! 🎮",
            "Money time! 💰"
        ]
        
        prediction = random.choice(predictions)
        catchphrase = random.choice(catchphrases)
        tweet = f"🚨 MAX's Game Prediction: {prediction}\n\n{catchphrase}\n#NBA #SportsBetting"
        
        print(f"\nPosting tweet: {tweet}")
        api.update_status(tweet)
        print("Tweet posted successfully!")
        
        return {"success": True, "tweet": tweet}
    except Exception as e:
        print(f"\nERROR posting tweet: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}

# Flask routes with error handling
@app.route("/")
def home():
    try:
        print("\nHome route accessed")
        return "MAX Sports Bot is running!"
    except Exception as e:
        print(f"\nERROR in home route: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    try:
        print("\nHealth check requested")
        return jsonify({
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "twitter_api": "initialized" if api else "not initialized"
        })
    except Exception as e:
        print(f"\nERROR in health check: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/trigger")
def trigger_message():
    """Manually trigger a tweet"""
    try:
        print("\nTrigger endpoint accessed - posting tweet...")
        result = post_tweet()
        print(f"Trigger result: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"\nERROR triggering message: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def run_scheduler():
    """Run the scheduler in a separate thread"""
    while True:
        try:
            scheduler.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"\nERROR in scheduler: {str(e)}")
            time.sleep(5)  # Wait before retrying

def start_scheduler():
    """Start the scheduler in a separate thread"""
    try:
        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        print("Scheduler started successfully")
    except Exception as e:
        print(f"\nERROR starting scheduler: {str(e)}")
        raise

# Initialize scheduler
scheduler = schedule.Scheduler()

# Run the Flask app
if __name__ == "__main__":
    try:
        print("\nStarting Flask app...")
        
        # Try different ports if default is in use
        port = int(os.getenv("PORT", 8080))
        if is_port_in_use(port):
            print(f"Port {port} is in use, trying port 5000")
            port = 5000
            if is_port_in_use(port):
                print(f"Port {port} is in use, trying port 3000")
                port = 3000
        
        print(f"\nUsing port: {port}")
        
        # Start scheduler before running the app
        print("\nStarting scheduler...")
        start_scheduler()
        
        # Run the Flask app with minimal settings first
        print(f"\nStarting Flask app on port {port}...")
        app.run(host="localhost", port=port, debug=True, use_reloader=False)
    except Exception as e:
        print(f"\nERROR starting application: {str(e)}")
        print("\nTraceback:")
        traceback.print_exc()
        sys.exit(1)
