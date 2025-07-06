from flask import Flask, jsonify, request
import requests
import hmac
import hashlib
import base64
import os
from datetime import datetime
import re
import time
import random

app = Flask(__name__)

# Simple CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers['Cache-Control'] = 'no-cache'
    return response

# OKX Config
OKX_API_KEY = os.getenv('OKX_API_KEY', '0321b6d3-385f-428e-9516-d3f1cb013f99')
OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY', '6C366DF95B6F365B73483A63339E0F27')
OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE', '462230Gutu99!')

def validate_contract(address):
    if not address or len(address) != 42 or not address.startswith('0x'):
        return False, "Invalid contract"
    return True, address.lower()

def create_signature(timestamp, method, path, body='', query=''):
    prehash = f'{timestamp}{method}{path}?{query}{body}' if query else f'{timestamp}{method}{path}{body}'
    signature = base64.b64encode(
        hmac.new(OKX_SECRET_KEY.encode(), prehash.encode(), hashlib.sha256).digest()
    ).decode()
    return signature

def okx_request(endpoint, params=None):
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    if not params:
        params = {}
    params['_t'] = str(int(time.time() * 1000))
    
    query = '&'.join([f"{k}={v}" for k, v in params.items()])
    signature = create_signature(timestamp, 'GET', endpoint, '', query)
    
    headers = {
        'OK-ACCESS-KEY': OKX_API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE,
        'Content-Type': 'application/json'
    }
    
    url = f"https://www.okx.com{endpoint}?{query}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@app.route('/')
def root():
    return jsonify({
        "status": "healthy",
        "service": "Ultra Simple OKX Backend",
        "version": "4.0.0-ultra-simple",
        "endpoints": [
            "/api/simple-test/<contract>",
            "/api/nfts/<contract>"
        ]
    })

@app.route('/api/simple-test/<contract>')
def simple_test(contract):
    """Ultra simple test of new endpoints"""
    is_valid, result = validate_contract(contract)
    if not is_valid:
        return jsonify({'error': result}), 400
    
    contract_address = result
    
    # Test 1: New query-listing endpoint
    params1 = {'chain': 'taiko', 'limit': '5'}
    data1 = okx_request('/api/v5/mktplace/nft/markets/query-listing', params1)
    
    # Test 2: New query-listing with contract
    params2 = {'chain': 'taiko', 'contractAddress': contract_address, 'limit': '5'}
    data2 = okx_request('/api/v5/mktplace/nft/markets/query-listing', params2)
    
    # Test 3: Old listings endpoint
    params3 = {'chain': 'taiko', 'limit': '5'}
    data3 = okx_request('/api/v5/mktplace/nft/markets/listings', params3)
    
    return jsonify({
        "success": True,
        "contract": contract_address,
        "test_results": {
            "query_listing_basic": {
                "working": bool(data1 and data1.get('code') == 0),
                "count": len(data1.get('data', {}).get('data', [])) if data1 and data1.get('code') == 0 else 0
            },
            "query_listing_contract": {
                "working": bool(data2 and data2.get('code') == 0),
                "count": len(data2.get('data', {}).get('data', [])) if data2 and data2.get('code') == 0 else 0
            },
            "old_listings": {
                "working": bool(data3 and data3.get('code') == 0),
                "count": len(data3.get('data', {}).get('data', [])) if data3 and data3.get('code') == 0 else 0
            }
        },
        "recommendation": "query_listing_contract" if (data2 and data2.get('code') == 0) else "old_listings",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/nfts/<contract>')
def get_nfts_simple(contract):
    """Get NFTs - ultra simple version"""
    is_valid, result = validate_contract(contract)
    if not is_valid:
        return jsonify({'error': result}), 400
    
    contract_address = result
    limit = int(request.args.get('limit', 12))
    
    # Use assets endpoint (confirmed working)
    params = {
        'chain': 'taiko',
        'contractAddress': contract_address,
        'limit': str(limit)
    }
    
    data = okx_request('/api/v5/mktplace/nft/asset/list', params)
    
    if not data or data.get('code') != 0:
        return jsonify({
            "success": False,
            "error": "No NFTs found",
            "contract": contract_address
        }), 404
    
    # Get NFTs
    response_data = data.get('data', {})
    nfts = response_data.get('data', []) if isinstance(response_data, dict) else response_data
    
    # Simple processing
    processed = []
    for i, nft in enumerate(nfts[:limit]):
        token_id = nft.get('tokenId', str(i))
        processed.append({
            'tokenId': str(token_id),
            'name': nft.get('name', f'NFT #{token_id}'),
            'image': nft.get('image', ''),
            'contractAddress': contract_address
        })
    
    return jsonify({
        "success": True,
        "data": processed,
        "count": len(processed),
        "contract": contract_address
    })

if __name__ == '__main__':
    app.run(debug=True)
