# grants_api_backend.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Grants.gov API base URL
GRANTS_API_BASE = "https://api.grants.gov/v1/api"

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "message": "IMEX Grants.gov API proxy server is running!",
        "endpoints": {
            "/api/search": "POST - Search for opportunities",
            "/api/fetch-opportunity": "POST - Fetch opportunity details"
        },
        "frontend": "Update your IMEX Hub with this API URL"
    })

@app.route('/api/search', methods=['POST'])
def search_opportunities():
    """Proxy endpoint for grants.gov search2 API"""
    try:
        request_data = request.get_json()
        
        response = requests.post(
            f"{GRANTS_API_BASE}/search2",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "error": f"API returned status {response.status_code}",
                "message": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@app.route('/api/fetch-opportunity', methods=['POST'])
def fetch_opportunity_details():
    """Proxy endpoint for grants.gov fetchOpportunity API"""
    try:
        request_data = request.get_json()
        
        if 'oppId' not in request_data:
            return jsonify({"error": "oppId is required"}), 400
        
        response = requests.post(
            f"{GRANTS_API_BASE}/fetchOpportunity",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                "error": f"API returned status {response.status_code}",
                "message": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "grants-api-proxy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
