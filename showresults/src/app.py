import os
import logging
from flask import Flask, render_template

from database import download_forecasts_db, get_latest_forecasts

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("showresults")

app = Flask(__name__)

@app.route("/")
def index():
    logger.info("Handling request for showresults dashboard root route.")
    
    # Trigger cached GCS check & download
    download_forecasts_db()
    
    # Retrieve formatted forecasts from local SQLite db
    forecasts = get_latest_forecasts()
    logger.info(f"Retrieved {len(forecasts)} forecasts for rendering.")
    
    # Compute active metrics for the header stats card
    total_tickers = len(forecasts)
    bull_count = sum(1 for f in forecasts if f["proba_spread"] is not None and f["proba_spread"] > 20)
    bear_count = sum(1 for f in forecasts if f["proba_spread"] is not None and f["proba_spread"] < -20)
    neutral_count = total_tickers - bull_count - bear_count

    return render_template(
        "index.html",
        forecasts=forecasts,
        total_tickers=total_tickers,
        bull_count=bull_count,
        bear_count=bear_count,
        neutral_count=neutral_count
    )

if __name__ == "__main__":
    # Cloud Run retrieves PORT env variable
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
