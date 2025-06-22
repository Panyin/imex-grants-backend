# grants_api_backend.py - FIXED VERSION
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
        "version": "1.2"
    })

@app.route('/api/search', methods=['POST'])
def search_opportunities():
    """Proxy endpoint for grants.gov search2 API"""
    try:
        # Get request data from client
        client_data = request.get_json()
        
        # Build grants.gov compatible request
        api_request = {
            "rows": 100,  # Increased to get more results
        }
        
        # Handle keywords
        if 'keyword' in client_data and client_data['keyword']:
            api_request['keyword'] = client_data['keyword']
        
        # Handle status - this is working correctly
        if 'oppStatuses' in client_data:
            api_request['oppStatuses'] = client_data['oppStatuses']
        else:
            api_request['oppStatuses'] = "posted|forecasted"
        
        # FIX: Agency filter - grants.gov expects agency codes not names
        if 'agencies' in client_data and client_data['agencies']:
            # Clean up the agency input and handle multiple agencies
            agencies = client_data['agencies'].strip()
            # If user enters multiple agencies separated by comma
            if ',' in agencies:
                # Convert "DOD, HHS" to "DOD|HHS" format
                agency_list = [a.strip() for a in agencies.split(',')]
                api_request['agencies'] = '|'.join(agency_list)
            else:
                api_request['agencies'] = agencies
        
        # Funding categories - this is working
        if 'fundingCategories' in client_data and client_data['fundingCategories']:
            api_request['fundingCategories'] = client_data['fundingCategories']
        
        # FIX: Date range handling
        if 'postedFrom' in client_data and client_data['postedFrom']:
            api_request['postedFrom'] = client_data['postedFrom']
            print(f"Date From: {client_data['postedFrom']}")
        
        if 'postedTo' in client_data and client_data['postedTo']:
            api_request['postedTo'] = client_data['postedTo']
            print(f"Date To: {client_data['postedTo']}")
        
        # Add startRecordNum to paginate if needed
        if 'startRecordNum' in client_data:
            api_request['startRecordNum'] = client_data['startRecordNum']
        else:
            api_request['startRecordNum'] = 0
        
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
            # Log some debug info
            if 'data' in data:
                print(f"Results returned: {data['data'].get('hitCount', 0)}")
                print(f"Search params used: {data['data'].get('searchParams', {})}")
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
        "version": "1.2"
    })

# Debug endpoint to test filters
@app.route('/api/test-filters', methods=['GET'])
def test_filters():
    """Test different filter combinations"""
    tests = []
    
    # Test 1: Date range
    test1_request = {
        "rows": 10,
        "oppStatuses": "posted",
        "postedFrom": "01/01/2025",
        "postedTo": "06/30/2025"
    }
    
    # Test 2: Agency
    test2_request = {
        "rows": 10,
        "oppStatuses": "posted",
        "agencies": "DOD"
    }
    
    # Test 3: Funding Category
    test3_request = {
        "rows": 10,
        "oppStatuses": "posted",
        "fundingCategories": "HL"  # Health
    }
    
    for idx, test_req in enumerate([test1_request, test2_request, test3_request], 1):
        try:
            response = requests.post(
                f"{GRANTS_API_BASE}/search2",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=test_req,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                hit_count = data.get('data', {}).get('hitCount', 0)
                tests.append({
                    f"test{idx}": {
                        "request": test_req,
                        "hitCount": hit_count,
                        "success": True
                    }
                })
            else:
                tests.append({
                    f"test{idx}": {
                        "request": test_req,
                        "error": response.text,
                        "success": False
                    }
                })
        except Exception as e:
            tests.append({
                f"test{idx}": {
                    "request": test_req,
                    "error": str(e),
                    "success": False
                }
            })
    
    return jsonify({"filter_tests": tests})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
