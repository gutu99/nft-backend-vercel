from flask import Flask, jsonify, request
import os
from datetime import datetime

# Create Flask app
app = Flask(__name__)

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/')
def root():
    return jsonify({
        "status": "working",
        "message": "Vercel Flask is alive!",
        "timestamp": datetime.utcnow().isoformat(),
        "available_endpoints": [
            "/api",
            "/api/test", 
            "/api/nfts/<contract>",
            "/api/collection/<contract>/stats"
        ]
    })

@app.route('/api')
def api():
    return jsonify({
        "status": "healthy",
        "service": "NFT Backend",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0-routing-fixed",
        "endpoints": {
            "health": "/api",
            "test": "/api/test",
            "nfts": "/api/nfts/<contract>",
            "stats": "/api/collection/<contract>/stats"
        }
    })

@app.route('/api/test')
def test():
    return jsonify({
        "success": True,
        "message": "Test working! Routing FIXED!",
        "environment": {
            "python_version": "3.9+",
            "flask_working": True,
            "vercel_deployment": True,
            "routing": "FIXED"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

# Minimal NFT endpoint pentru test
@app.route('/api/nfts/<contract>')
def get_nfts_minimal(contract):
    # Validare basic
    if not contract or not contract.startswith('0x'):
        return jsonify({
            "success": False,
            "error": "Invalid contract address format"
        }), 400
    
    # Mock data pentru test
    return jsonify({
        "success": True,
        "contract_address": contract.lower(),
        "message": "NFT endpoint working with routing fix!",
        "data": [
            {
                "id": f"{contract}_1",
                "tokenId": "1",
                "name": "Test NFT #1",
                "image": "https://via.placeholder.com/300x300/667eea/white?text=NFT+1",
                "description": "Test NFT pentru verificare routing",
                "price": "0.1",
                "currency": "ETH",
                "status": "listed",
                "source": "vercel_test"
            },
            {
                "id": f"{contract}_2",
                "tokenId": "2", 
                "name": "Test NFT #2",
                "image": "https://via.placeholder.com/300x300/764ba2/white?text=NFT+2",
                "description": "Al doilea NFT de test",
                "price": "0.2",
                "currency": "ETH",
                "status": "listed",
                "source": "vercel_test"
            },
            {
                "id": f"{contract}_3",
                "tokenId": "3",
                "name": "Test NFT #3",
                "image": "https://via.placeholder.com/300x300/27ae60/white?text=NFT+3",
                "description": "Al treilea NFT de test",
                "price": None,
                "currency": "ETH",
                "status": "unlisted",
                "source": "vercel_test"
            }
        ],
        "count": 3,
        "deployment": "vercel",
        "routing": "FIXED",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/collection/<contract>/stats')
def get_collection_stats_minimal(contract):
    # Validare basic
    if not contract or not contract.startswith('0x'):
        return jsonify({
            "success": False,
            "error": "Invalid contract address format"
        }), 400
    
    # Mock stats pentru test
    return jsonify({
        "success": True,
        "contract_address": contract.lower(),
        "stats": {
            "total_supply": 100,
            "listed_count": 25,
            "floor_price": 0.05,
            "average_price": 0.15,
            "listing_percentage": 25.0
        },
        "message": "Collection stats working with routing fix!",
        "deployment": "vercel",
        "routing": "FIXED",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/",
            "/api", 
            "/api/test",
            "/api/nfts/<contract>",
            "/api/collection/<contract>/stats"
        ],
        "example_urls": [
            "/api/nfts/0xa20a8856e00f5ad024a55a663f06dcc419ffc4d5",
            "/api/collection/0xa20a8856e00f5ad024a55a663f06dcc419ffc4d5/stats"
        ],
        "routing": "FIXED"
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "error": "Server error",
        "message": str(error),
        "deployment": "vercel"
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
