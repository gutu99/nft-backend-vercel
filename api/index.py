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

@app.route('/api/raw-debug/<contract>')
def raw_debug(contract):
    """Show EXACTLY what OKX returns - no processing"""
    is_valid, result = validate_contract(contract)
    if not is_valid:
        return jsonify({'error': result}), 400
    
    contract_address = result
    
    # Raw test 1: What does listings return?
    listings_params = {'chain': 'taiko', 'limit': '10'}
    listings_raw = okx_request('/api/v5/mktplace/nft/markets/listings', listings_params)
    
    # Raw test 2: What does assets return?
    assets_params = {'chain': 'taiko', 'contractAddress': contract_address, 'limit': '5'}
    assets_raw = okx_request('/api/v5/mktplace/nft/asset/list', assets_params)
    
    return jsonify({
        "contract_tested": contract_address,
        "raw_responses": {
            "listings_endpoint": {
                "params_sent": listings_params,
                "raw_response": listings_raw,
                "explanation": "This shows EXACTLY what OKX returns for listings"
            },
            "assets_endpoint": {
                "params_sent": assets_params, 
                "raw_response": assets_raw,
                "explanation": "This shows EXACTLY what OKX returns for assets"
            }
        },
        "what_to_look_for": {
            "in_listings": "Look for ANY items with 'price' field",
            "in_assets": "Look if ANY assets have price data", 
            "contract_matching": f"Look if any items have contractAddress = {contract_address}"
        }
    })
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
def get_nfts_with_metadata(contract):
    """Get NFTs with proper parameters like the old working version"""
    is_valid, result = validate_contract(contract)
    if not is_valid:
        return jsonify({'error': result}), 400
    
    contract_address = result
    limit = int(request.args.get('limit', 12))
    page = int(request.args.get('page', 1))
    sort_by = request.args.get('sort_by', 'none')
    fetch_metadata = request.args.get('fetch_metadata', 'true')
    
    # Use the SAME parameters as the old working version
    params = {
        'chain': 'taiko',
        'contractAddress': contract_address,
        'limit': str(limit),
        'page': str(page),
        'fetch_metadata': fetch_metadata,  # KEY PARAMETER!
        'sort_by': sort_by if sort_by != 'none' else None
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    print(f"🔍 Using OLD WORKING parameters: {params}")
    
    # Try assets endpoint first with the proper parameters
    assets_data = okx_request('/api/v5/mktplace/nft/asset/list', params)
    
    if assets_data and assets_data.get('code') == 0:
        print(f"✅ Assets endpoint worked with metadata params")
        response_data = assets_data.get('data', {})
        nfts = response_data.get('data', []) if isinstance(response_data, dict) else response_data
        
        # Process NFTs and check for prices
        processed_nfts = []
        with_prices = 0
        
        for nft in nfts:
            token_id = nft.get('tokenId', '')
            name = nft.get('name', f'NFT #{token_id}')
            image = nft.get('image', '')
            
            # Look for price in multiple possible fields
            price = (nft.get('price') or 
                    nft.get('listingPrice') or 
                    nft.get('priceEth') or 
                    nft.get('currentPrice') or
                    nft.get('floorPrice'))
            
            if price:
                try:
                    price_num = float(price)
                    if price_num > 1e10:  # Convert from wei
                        price_num = price_num / 1e18
                    price_display = f"{price_num:.6f}".rstrip('0').rstrip('.')
                    with_prices += 1
                    print(f"💰 Found price for token {token_id}: {price_display} ETH")
                except:
                    price_display = str(price)
                    with_prices += 1
            else:
                price_display = None
            
            processed_nfts.append({
                'tokenId': str(token_id),
                'name': name,
                'image': image,
                'price': price_display,
                'currency': 'ETH' if price_display else None,
                'status': 'listed' if price_display else 'unlisted',
                'contractAddress': contract_address,
                'raw_price_data': {
                    'price': nft.get('price'),
                    'listingPrice': nft.get('listingPrice'),
                    'priceEth': nft.get('priceEth'),
                    'currentPrice': nft.get('currentPrice'),
                    'floorPrice': nft.get('floorPrice')
                }
            })
        
        print(f"💰 Found {with_prices} NFTs with prices out of {len(processed_nfts)}")
        
        return jsonify({
            "success": True,
            "data": processed_nfts,
            "count": len(processed_nfts),
            "contract_address": contract_address,
            "params_used": params,
            "price_info": {
                "nfts_with_prices": with_prices,
                "total_nfts": len(processed_nfts),
                "price_coverage": f"{round(with_prices/len(processed_nfts)*100, 1)}%" if processed_nfts else "0%"
            },
            "metadata_fetch": fetch_metadata,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # If assets failed, try listings with the same params
    print(f"⚠️ Assets failed, trying listings with metadata params")
    listings_data = okx_request('/api/v5/mktplace/nft/markets/listings', params)
    
    if listings_data and listings_data.get('code') == 0:
        response_data = listings_data.get('data', {})
        nfts = response_data.get('data', []) if isinstance(response_data, dict) else response_data
        
        print(f"📋 Listings returned {len(nfts)} items with metadata params")
        
        # Same processing as above...
        processed_nfts = []
        for nft in nfts[:limit]:
            token_id = nft.get('tokenId', '')
            price = nft.get('price') or nft.get('listingPrice')
            
            processed_nfts.append({
                'tokenId': str(token_id),
                'name': nft.get('name', f'NFT #{token_id}'),
                'image': nft.get('image', ''),
                'price': price,
                'contractAddress': contract_address
            })
        
        return jsonify({
            "success": True,
            "data": processed_nfts,
            "count": len(processed_nfts),
            "source": "listings_with_metadata",
            "params_used": params
        })
    
    return jsonify({
        "success": False,
        "error": "No data from either endpoint with metadata params",
        "params_tried": params
    }), 404

if __name__ == '__main__':
    app.run(debug=True)
