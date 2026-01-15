#!/usr/bin/env python3
"""
LinkedIn Scraper Web Server

A Flask server that provides HTTP endpoints to trigger the LinkedIn scraper.
Use with ngrok or similar to expose to the internet for Google Apps Script triggers.

Usage:
    Start server:
        python scraper_server.py

    Start with custom port:
        python scraper_server.py --port 5000

    Expose to internet (in another terminal):
        ngrok http 5000

Endpoints:
    GET  /health          - Health check
    POST /scrape          - Trigger scraper with JSON body: {"days": 30}
    GET  /status          - Get last scrape status
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state for tracking scraper status
scraper_status = {
    "status": "idle",  # idle, running, completed, failed
    "last_run": None,
    "last_result": None,
    "posts_scraped": 0,
    "posts_written_to_sheets": 0,
    "error": None
}

# Lock for thread safety
status_lock = threading.Lock()

# Configuration - set these via environment variables or modify directly
CONFIG = {
    "credentials_path": os.environ.get("GOOGLE_CREDENTIALS", "credentials.json"),
    "sheet_id": os.environ.get("GOOGLE_SHEET_ID", ""),
    "sheet_name": os.environ.get("GOOGLE_SHEET_NAME", "Sheet1"),
}


def run_scraper(days: int = 30):
    """Run the LinkedIn scraper in a background thread."""
    global scraper_status

    with status_lock:
        scraper_status["status"] = "running"
        scraper_status["error"] = None
        scraper_status["last_run"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Import scraper modules
        from linkedin_scraper import LinkedInScraper
        from sheets_integration import write_to_sheets

        logger.info(f"Starting scraper for last {days} days...")

        # Create and run scraper
        scraper = LinkedInScraper(days_back=days, headless=True)
        posts = scraper.scrape_posts()

        with status_lock:
            scraper_status["posts_scraped"] = len(posts)

        logger.info(f"Scraped {len(posts)} posts")

        # Save to JSON
        scraper.save_to_json("scraped_posts.json")

        # Write to Google Sheets if configured
        sheets_count = 0
        if CONFIG["sheet_id"] and CONFIG["credentials_path"]:
            try:
                posts_dict = [post.to_dict() for post in posts]
                sheets_count = write_to_sheets(
                    posts=posts_dict,
                    credentials_path=CONFIG["credentials_path"],
                    spreadsheet_id=CONFIG["sheet_id"],
                    sheet_name=CONFIG["sheet_name"],
                    append=True
                )
                logger.info(f"Written {sheets_count} posts to Google Sheets")
            except Exception as e:
                logger.error(f"Failed to write to Sheets: {e}")

        with status_lock:
            scraper_status["status"] = "completed"
            scraper_status["posts_written_to_sheets"] = sheets_count
            scraper_status["last_result"] = {
                "posts_scraped": len(posts),
                "posts_written": sheets_count,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        logger.info("Scraper completed successfully")

    except Exception as e:
        logger.error(f"Scraper failed: {e}")
        with status_lock:
            scraper_status["status"] = "failed"
            scraper_status["error"] = str(e)


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/scrape', methods=['POST'])
def scrape():
    """
    Trigger the LinkedIn scraper.

    Request body (JSON):
        {
            "days": 30  // optional, default 30
        }

    Returns:
        {
            "status": "started",
            "message": "Scraper started for 30 days"
        }
    """
    global scraper_status

    # Check if already running
    with status_lock:
        if scraper_status["status"] == "running":
            return jsonify({
                "status": "error",
                "message": "Scraper is already running"
            }), 409

    # Parse request
    data = request.get_json() or {}
    days = data.get("days", 30)

    if days not in [30, 60]:
        return jsonify({
            "status": "error",
            "message": "Days must be 30 or 60"
        }), 400

    # Start scraper in background thread
    thread = threading.Thread(target=run_scraper, args=(days,))
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "started",
        "message": f"Scraper started for {days} days"
    })


@app.route('/status', methods=['GET'])
def status():
    """Get the current scraper status."""
    with status_lock:
        return jsonify(scraper_status)


@app.route('/config', methods=['GET', 'POST'])
def config():
    """Get or update configuration."""
    global CONFIG

    if request.method == 'GET':
        # Don't expose full credentials path for security
        return jsonify({
            "credentials_configured": bool(CONFIG["credentials_path"]),
            "sheet_id": CONFIG["sheet_id"][:10] + "..." if CONFIG["sheet_id"] else "",
            "sheet_name": CONFIG["sheet_name"]
        })

    elif request.method == 'POST':
        data = request.get_json() or {}

        if "sheet_id" in data:
            CONFIG["sheet_id"] = data["sheet_id"]
        if "sheet_name" in data:
            CONFIG["sheet_name"] = data["sheet_name"]
        if "credentials_path" in data:
            CONFIG["credentials_path"] = data["credentials_path"]

        return jsonify({
            "status": "updated",
            "message": "Configuration updated"
        })


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='LinkedIn Scraper Web Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--sheet-id', type=str, help='Google Sheet ID')
    parser.add_argument('--sheet-name', type=str, help='Worksheet name')
    parser.add_argument('--credentials', type=str, help='Path to credentials JSON')

    args = parser.parse_args()

    # Update config from command line
    if args.sheet_id:
        CONFIG["sheet_id"] = args.sheet_id
    if args.sheet_name:
        CONFIG["sheet_name"] = args.sheet_name
    if args.credentials:
        CONFIG["credentials_path"] = args.credentials

    print("=" * 60)
    print("LinkedIn Scraper Web Server")
    print("=" * 60)
    print(f"Server starting on http://{args.host}:{args.port}")
    print("")
    print("Endpoints:")
    print(f"  GET  http://localhost:{args.port}/health  - Health check")
    print(f"  POST http://localhost:{args.port}/scrape  - Start scraper")
    print(f"  GET  http://localhost:{args.port}/status  - Get status")
    print("")
    print("To expose to internet, run in another terminal:")
    print(f"  ngrok http {args.port}")
    print("=" * 60)

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
