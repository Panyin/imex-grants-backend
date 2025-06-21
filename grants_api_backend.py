# grants_api_backend.py - UPDATED VERSION
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, 
     allow_headers=["Content-Type"],
     methods=["GET", "POST", "OPTIONS"])

# Additional CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

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
        "frontend": "Update your IMEX Hub with this API URL",
        "version": "1.1"
    })

@app.route('/api/search', methods=['POST'])
def search_opportunities():
    """Proxy endpoint for grants.gov search2 API"""
    try:
        # Get request data from client
        client_data = request.get_json()
        
        # Build grants.gov compatible request
        api_request = {
            "rows": 25,  # Default number of results
            "oppNum": "",  # Opportunity number (usually empty for searches)
            "aln": "",  # ALN number (usually empty)
        }
        
        # Map our simplified format to grants.gov format
        if 'keyword' in client_data:
            api_request['keyword'] = client_data['keyword']
            # Also try keyword encoding - some keywords might need different format
            api_request['keywordEncoded'] = True
        
        if 'oppStatuses' in client_data:
            # Ensure proper pipe separation for multiple statuses
            api_request['oppStatuses'] = client_data['oppStatuses']
        else:
            # Default to all common statuses
            api_request['oppStatuses'] = "posted|forecasted"
        
        if 'agencies' in client_data and client_data['agencies']:
            api_request['agencies'] = client_data['agencies']
        
        if 'fundingCategories' in client_data and client_data['fundingCategories']:
            api_request['fundingCategories'] = client_data['fundingCategories']
        
        # Add any other fields from client
        for key in ['startRecordNum', 'eligibilities', 'sortBy', 'hitCount']:
            if key in client_data:
                api_request[key] = client_data[key]
        
        print(f"API Request to grants.gov: {json.dumps(api_request, indent=2)}")
        
        # Make request to grants.gov API
        response = requests.post(
            f"{GRANTS_API_BASE}/search2",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=api_request,
            timeout=30
        )
        
        print(f"Grants.gov Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response preview: {json.dumps(data, indent=2)[:500]}...")
            return jsonify(data)
        else:
            print(f"Error response: {response.text}")
            return jsonify({
                "error": f"API returned status {response.status_code}",
                "message": response.text,
                "request_sent": api_request
            }), response.status_code
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({
            "error": "Internal server error", 
            "message": str(e),
            "type": type(e).__name__
        }), 500

@app.route('/api/fetch-opportunity', methods=['POST'])
def fetch_opportunity_details():
    """Proxy endpoint for grants.gov fetchOpportunity API"""
    try:
        request_data = request.get_json()
        
        if 'oppId' not in request_data:
            return jsonify({"error": "oppId is required"}), 400
        
        # Build the request for fetchOpportunity
        api_request = {
            "oppId": request_data['oppId']
        }
        
        print(f"Fetching opportunity: {request_data['oppId']}")
        
        response = requests.post(
            f"{GRANTS_API_BASE}/fetchOpportunity",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=api_request,
            timeout=30
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            print(f"Error fetching opportunity: {response.text}")
            return jsonify({
                "error": f"API returned status {response.status_code}",
                "message": response.text
            }), response.status_code
            
    except Exception as e:
        print(f"Exception in fetch: {str(e)}")
        return jsonify({
            "error": "Internal server error", 
            "message": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "grants-api-proxy",
        "version": "1.1"
    })

# Debug endpoint to test what grants.gov returns
@app.route('/api/test-search', methods=['GET'])
def test_search():
    """Test endpoint with the exact example from grants.gov docs"""
    test_request = {
        "rows": 10,
        "keyword": "20231011",
        "oppNum": "TEST-PTS-20231011-OPP1",
        "eligibilities": "",
        "agencies": "",
        "oppStatuses": "forecasted|posted",
        "aln": "",
        "fundingCategories": ""
    }
    
    try:
        response = requests.post(
            f"{GRANTS_API_BASE}/search2",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=test_request,
            timeout=30
        )
        
        return jsonify({
            "status_code": response.status_code,
            "request_sent": test_request,
            "response": response.json() if response.status_code == 200 else response.text
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
