from flask import Flask, jsonify
import os
from datetime import datetime

# Create Flask app
app = Flask(__name__)

@app.route('/')
def root():
    return jsonify({
        "status": "working",
        "message": "Vercel Flask is alive!",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api')
def api():
    return jsonify({
        "status": "healthy",
        "service": "NFT Backend",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/test')
def test():
    return jsonify({
        "success": True,
        "message": "Test working!",
        "environment": {
            "python_version": "3.9+",
            "flask_working": True,
            "vercel_deployment": True
        }
    })

# Minimal NFT endpoint pentru test
@app.route('/api/nfts/<contract>')
def get_nfts_minimal(contract):
    # Doar un răspuns simplu pentru test
    return jsonify({
        "success": True,
        "contract": contract,
        "message": "NFT endpoint working",
        "data": [
            {
                "tokenId": "1",
                "name": "Test NFT #1",
                "price": "0.1",
                "status": "listed"
            },
            {
                "tokenId": "2", 
                "name": "Test NFT #2",
                "price": "0.2",
                "status": "listed"
            }
        ],
        "deployment": "vercel"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not found",
        "available_endpoints": [
            "/",
            "/api", 
            "/api/test",
            "/api/nfts/<contract>"
        ]
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "error": "Server error",
        "message": str(error)
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
