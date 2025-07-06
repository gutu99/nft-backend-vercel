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
def get_nfts_final(contract):
    """Final working version with price sorting"""
    is_valid, result = validate_contract(contract)
    if not is_valid:
        return jsonify({'error': result}), 400
    
    contract_address = result
    limit = int(request.args.get('limit', 12))
    sort_by = request.args.get('sort_by', 'none')
    
    # Step 1: Get NFTs using assets endpoint (confirmed perfect)
    assets_params = {
        'chain': 'taiko',
        'contractAddress': contract_address,
        'limit': str(min(limit * 2, 50))  # Get more to ensure we have enough after filtering
    }
    
    assets_data = okx_request('/api/v5/mktplace/nft/asset/list', assets_params)
    
    if not assets_data or assets_data.get('code') != 0:
        return jsonify({
            "success": False,
            "error": "Could not get NFTs",
            "contract": contract_address
        }), 404
    
    # Process assets data
    assets_response = assets_data.get('data', {})
    all_nfts = assets_response.get('data', []) if isinstance(assets_response, dict) else assets_response
    
    # Filter NFTs by contract (extra safety)
    contract_nfts = []
    for nft in all_nfts:
        nft_contract = (
            nft.get('assetContract', {}).get('contractAddress', '') or
            nft.get('contractAddress', '')
        ).lower()
        
        if nft_contract == contract_address.lower():
            contract_nfts.append(nft)
    
    print(f"📦 Found {len(contract_nfts)} NFTs for contract {contract_address}")
    
    # Step 2: Get price data if sorting by price
    price_data = {}
    if sort_by in ['price_asc', 'price_desc'] and len(contract_nfts) > 0:
        print(f"💰 Getting price data for sorting...")
        
        # Use old listings endpoint (confirmed working with 5 items)
        listings_params = {'chain': 'taiko', 'limit': '50'}
        listings_data = okx_request('/api/v5/mktplace/nft/markets/listings', listings_params)
        
        if listings_data and listings_data.get('code') == 0:
            listings_response = listings_data.get('data', {})
            all_listings = listings_response.get('data', []) if isinstance(listings_response, dict) else listings_response
            
            print(f"💰 Got {len(all_listings)} total listings")
            
            # Create token ID set from our NFTs
            our_token_ids = {str(nft.get('tokenId')) for nft in contract_nfts if nft.get('tokenId')}
            
            # Manual contract filtering + price matching
            matched_prices = 0
            for listing in all_listings:
                # Check if listing is from our contract
                listing_contract = (
                    listing.get('assetContract', {}).get('contractAddress', '') or
                    listing.get('contractAddress', '') or
                    ''
                ).lower()
                
                # Only process listings from our specific contract
                if listing_contract == contract_address.lower():
                    listing_token_id = str(listing.get('tokenId', ''))
                    listing_price = listing.get('price') or listing.get('listingPrice')
                    
                    # Match price with our NFTs
                    if listing_token_id in our_token_ids and listing_price:
                        price_data[listing_token_id] = listing_price
                        matched_prices += 1
            
            print(f"💰 Matched {matched_prices} prices for our contract")
    
    # Step 3: Process and enrich NFTs
    processed_nfts = []
    for nft in contract_nfts:
        token_id = nft.get('tokenId', '')
        name = nft.get('name', f'NFT #{token_id}')
        image = nft.get('image', '')
        
        # Add price if available
        price = None
        if str(token_id) in price_data:
            price_raw = price_data[str(token_id)]
            try:
                price_num = float(price_raw)
                if price_num > 1e10:  # Convert from wei
                    price_num = price_num / 1e18
                price = f"{price_num:.6f}".rstrip('0').rstrip('.')
            except:
                price = str(price_raw)
        
        processed_nfts.append({
            'tokenId': str(token_id),
            'name': name,
            'image': image,
            'price': price,
            'priceNumeric': float(price) if price else None,
            'currency': 'ETH' if price else None,
            'status': 'listed' if price else 'unlisted',
            'contractAddress': contract_address
        })
    
    # Step 4: Apply sorting
    if sort_by in ['price_asc', 'price_desc'] and len(processed_nfts) > 1:
        def get_sort_price(nft):
            price_num = nft.get('priceNumeric')
            if price_num is None:
                return 0 if sort_by == 'price_asc' else float('inf')
            return price_num
        
        processed_nfts.sort(key=get_sort_price, reverse=(sort_by == 'price_desc'))
        print(f"🔄 Applied sorting: {sort_by}")
    
    # Step 5: Limit results
    final_nfts = processed_nfts[:limit]
    with_prices = sum(1 for nft in final_nfts if nft.get('price'))
    
    return jsonify({
        "success": True,
        "data": final_nfts,
        "count": len(final_nfts),
        "contract_address": contract_address,
        "sort_by": sort_by,
        "price_info": {
            "nfts_with_prices": with_prices,
            "total_nfts": len(final_nfts),
            "price_coverage": f"{round(with_prices/len(final_nfts)*100, 1)}%" if final_nfts else "0%"
        },
        "endpoints_used": {
            "assets": "perfect_contract_filtering",
            "old_listings": "price_data_with_manual_filtering"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True)
