#!/usr/bin/env python3
"""
Flask API server for serving onion scraper data to frontend applications.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import csv
import json
import os
from datetime import datetime
import pandas as pd

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DATA_DIR = "."
SCREENSHOT_DIR = "screenshots_fast"
MAIN_CSV = "crypto_addresses_fast.csv"
TRAFFICKING_CSV = "human_trafficking_alerts.csv"
SCAM_CSV = "scam_alerts.csv"

def load_csv_data(filename):
    """Load CSV data into a list of dictionaries."""
    if not os.path.exists(filename):
        return []
    
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    
    return data

@app.route('/')
def index():
    """API root endpoint with basic info."""
    return jsonify({
        "name": "Onion Scraper API",
        "version": "1.0.0",
        "description": "API for accessing onion scraper data",
        "endpoints": {
            "/api/addresses": "Get all crypto addresses",
            "/api/addresses/<chain>": "Get addresses by blockchain",
            "/api/trafficking": "Get human trafficking alerts",
            "/api/scams": "Get scam alerts",
            "/api/stats": "Get statistics",
            "/api/search": "Search addresses and titles",
            "/screenshots/<filename>": "Get screenshot images"
        }
    })

@app.route('/api/addresses')
def get_addresses():
    """Get all crypto addresses with optional filtering."""
    data = load_csv_data(MAIN_CSV)
    
    # Parse query parameters
    chain = request.args.get('chain')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)
    
    # Filter by chain if specified
    if chain:
        data = [row for row in data if row.get('chain', '').upper() == chain.upper()]
    
    # Apply pagination
    if limit:
        data = data[offset:offset + limit]
    elif offset:
        data = data[offset:]
    
    return jsonify({
        "total": len(data),
        "offset": offset,
        "limit": limit,
        "data": data
    })

@app.route('/api/addresses/<chain>')
def get_addresses_by_chain(chain):
    """Get addresses for a specific blockchain."""
    data = load_csv_data(MAIN_CSV)
    filtered_data = [row for row in data if row.get('chain', '').upper() == chain.upper()]
    
    return jsonify({
        "chain": chain,
        "total": len(filtered_data),
        "data": filtered_data
    })

@app.route('/api/trafficking')
def get_trafficking_alerts():
    """Get human trafficking alerts."""
    data = load_csv_data(TRAFFICKING_CSV)
    
    # Parse query parameters
    priority = request.args.get('priority')
    limit = request.args.get('limit', type=int)
    
    # Filter by priority if specified
    if priority:
        data = [row for row in data if row.get('priority', '').upper() == priority.upper()]
    
    # Apply limit
    if limit:
        data = data[:limit]
    
    return jsonify({
        "total": len(data),
        "data": data
    })

@app.route('/api/scams')
def get_scam_alerts():
    """Get scam alerts."""
    data = load_csv_data(SCAM_CSV)
    
    # Parse query parameters
    priority = request.args.get('priority')
    limit = request.args.get('limit', type=int)
    
    # Filter by priority if specified
    if priority:
        data = [row for row in data if row.get('priority', '').upper() == priority.upper()]
    
    # Apply limit
    if limit:
        data = data[:limit]
    
    return jsonify({
        "total": len(data),
        "data": data
    })

@app.route('/api/stats')
def get_stats():
    """Get overall statistics."""
    addresses_data = load_csv_data(MAIN_CSV)
    trafficking_data = load_csv_data(TRAFFICKING_CSV)
    scam_data = load_csv_data(SCAM_CSV)
    
    # Calculate statistics
    stats = {
        "total_addresses": len(addresses_data),
        "total_trafficking_alerts": len(trafficking_data),
        "total_scam_alerts": len(scam_data),
        "chains": {},
        "categories": {},
        "priorities": {
            "trafficking": {},
            "scams": {}
        }
    }
    
    # Count by chain
    for row in addresses_data:
        chain = row.get('chain', 'Unknown')
        stats['chains'][chain] = stats['chains'].get(chain, 0) + 1
    
    # Count by category
    for row in addresses_data:
        categories_str = row.get('categories', '[]')
        try:
            categories = json.loads(categories_str)
            if isinstance(categories, list):
                for category in categories:
                    stats['categories'][category] = stats['categories'].get(category, 0) + 1
        except:
            pass
    
    # Count trafficking priorities
    for row in trafficking_data:
        priority = row.get('priority', 'Unknown')
        stats['priorities']['trafficking'][priority] = stats['priorities']['trafficking'].get(priority, 0) + 1
    
    # Count scam priorities
    for row in scam_data:
        priority = row.get('priority', 'Unknown')
        stats['priorities']['scams'][priority] = stats['priorities']['scams'].get(priority, 0) + 1
    
    return jsonify(stats)

@app.route('/api/search')
def search():
    """Search addresses and titles."""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    addresses_data = load_csv_data(MAIN_CSV)
    results = []
    
    for row in addresses_data:
        # Search in title, address, and description
        title = row.get('title', '').lower()
        address = row.get('address', '').lower()
        description = row.get('description', '').lower()
        url = row.get('url', '').lower()
        
        if (query in title or query in address or 
            query in description or query in url):
            results.append(row)
    
    return jsonify({
        "query": query,
        "total": len(results),
        "data": results
    })

@app.route('/screenshots/<filename>')
def get_screenshot(filename):
    """Serve screenshot images."""
    return send_from_directory(SCREENSHOT_DIR, filename)

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "files": {
            "main_csv": os.path.exists(MAIN_CSV),
            "trafficking_csv": os.path.exists(TRAFFICKING_CSV),
            "scam_csv": os.path.exists(SCAM_CSV),
            "screenshot_dir": os.path.exists(SCREENSHOT_DIR)
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Onion Scraper API Server...")
    print(f"📁 Data directory: {DATA_DIR}")
    print(f"📁 Screenshots: {SCREENSHOT_DIR}")
    print(f"📊 Main CSV: {MAIN_CSV}")
    print(f"🚨 Trafficking alerts: {TRAFFICKING_CSV}")
    print(f"🎭 Scam alerts: {SCAM_CSV}")
    print("=" * 50)
    
    # Check if data files exist
    if not os.path.exists(MAIN_CSV):
        print(f"⚠️ Warning: {MAIN_CSV} not found!")
    else:
        data = load_csv_data(MAIN_CSV)
        print(f"✅ Loaded {len(data)} addresses from {MAIN_CSV}")
    
    if not os.path.exists(TRAFFICKING_CSV):
        print(f"⚠️ Warning: {TRAFFICKING_CSV} not found!")
    else:
        data = load_csv_data(TRAFFICKING_CSV)
        print(f"✅ Loaded {len(data)} trafficking alerts from {TRAFFICKING_CSV}")
    
    if not os.path.exists(SCAM_CSV):
        print(f"⚠️ Warning: {SCAM_CSV} not found!")
    else:
        data = load_csv_data(SCAM_CSV)
        print(f"✅ Loaded {len(data)} scam alerts from {SCAM_CSV}")
    
    print("=" * 50)
    print("🌐 API Server starting on http://localhost:5000")
    print("📖 API documentation available at http://localhost:5000/")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True) 