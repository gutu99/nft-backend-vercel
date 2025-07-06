from flask import Flask, jsonify, request
import requests
import hmac
import hashlib
import base64
import json
import os
from datetime import datetime
import re
import time
import random

# Create Flask app
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Simple CORS + No Cache
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # NO CACHE
    current_time = int(time.time() * 1000000)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['ETag'] = f'"fresh-{current_time}"'
    
    return response

# OKX Configuration
OKX_API_KEY = os.getenv('OKX_API_KEY', '0321b6d3-385f-428e-9516-d3f1cb013f99')
OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY', '6C366DF95B6F365B73483A63339E0F27')
OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE', '462230Gutu99!')

def validate_contract_address(address):
    """Validate contract address"""
    if not address or not isinstance(address, str):
        return False, "Contract address invalid"
    
    address = address.strip()
    if not address.startswith('0x') or len(address) != 42:
        return False, "Contract address format invalid"
    
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return False, "Contract address contains invalid characters"
    
    return True, address.lower()

def create_okx_signature(timestamp, method, request_path, body='', query_string=''):
    """Create OKX signature"""
    try:
        if query_string:
            prehash = f'{timestamp}{method}{request_path}?{query_string}{body}'
        else:
            prehash = f'{timestamp}{method}{request_path}{body}'
            
        signature = base64.b64encode(
            hmac.new(
                OKX_SECRET_KEY.encode('utf-8'),
                prehash.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode('utf-8')
        return signature
    except Exception as e:
        print(f"Signature error: {e}")
        return ""

def make_okx_request(endpoint, params=None, contract_address=None):
    """Make fresh OKX API request"""
    try:
        # Fresh timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Add cache busting
        if not params:
            params = {}
        params['_fresh'] = str(int(time.time() * 1000000))
        params['_rand'] = str(random.randint(100000, 999999))
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        signature = create_okx_signature(timestamp, 'GET', endpoint, '', query_string)
        
        headers = {
            'OK-ACCESS-KEY': OKX_API_KEY,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'User-Agent': f'OKX-Test-{random.randint(1000, 9999)}'
        }
        
        url = f"https://www.okx.com{endpoint}?{query_string}"
        
        print(f"🔄 OKX Request: {contract_address}")
        
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        session.close()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ OKX Response: {data.get('code', 'unknown')}")
            return data
        else:
            print(f"❌ OKX Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

@app.route('/')
def root():
    return jsonify({
        "status": "healthy",
        "service": "OKX NFT Backend - Parameter Testing",
        "version": "3.3.0-simple",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": [
            "/api - health check",
            "/api/test-params/<contract> - test different parameters", 
            "/api/contracts - known contracts",
            "/api/nfts/<contract> - get NFTs"
        ]
    })

@app.route('/api')
def api():
    return jsonify({
        "status": "healthy",
        "okx_keys": bool(OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/contracts')
def contracts():
    return jsonify({
        "success": True,
        "known_contracts": [
            {
                "name": "Taikoon",
                "address": "0x4a045c5016b200f7e08a4cabb2cda6e85bf53295",
                "test_url": "/api/test-params/0x4a045c5016b200f7e08a4cabb2cda6e85bf53295"
            },
            {
                "name": "Taikonauts",
                "address": "0x56b0d8d04de22f2539945258ddb288c123026775",
                "test_url": "/api/test-params/0x56b0d8d04de22f2539945258ddb288c123026775"
            }
        ]
    })

@app.route('/api/test-params/<contract>')
def test_parameters(contract):
    """Test different parameter combinations"""
    try:
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({'success': False, 'error': result}), 400
        
        contract_address = result
        
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured"
            }), 500
        
        # Simple parameter tests
        tests = [
            {
                "name": "assets_taiko",
                "endpoint": "/api/v5/mktplace/nft/asset/list",
                "params": {
                    'chain': 'taiko',
                    'contractAddress': contract_address,
                    'limit': '3'
                }
            },
            {
                "name": "assets_eth",
                "endpoint": "/api/v5/mktplace/nft/asset/list", 
                "params": {
                    'chain': 'eth',
                    'contractAddress': contract_address,
                    'limit': '3'
                }
            },
            {
                "name": "listings_taiko",
                "endpoint": "/api/v5/mktplace/nft/markets/listings",
                "params": {
                    'chain': 'taiko',
                    'contractAddress': contract_address,
                    'limit': '3'
                }
            },
            {
                "name": "listings_taiko_collection",
                "endpoint": "/api/v5/mktplace/nft/markets/listings",
                "params": {
                    'chain': 'taiko',
                    'collectionAddress': contract_address,
                    'limit': '3'
                }
            },
            {
                "name": "listings_only_chain",
                "endpoint": "/api/v5/mktplace/nft/markets/listings",
                "params": {
                    'chain': 'taiko',
                    'limit': '3'
                }
            }
        ]
        
        results = {}
        
        for test in tests:
            print(f"🧪 Testing: {test['name']}")
            
            data = make_okx_request(test['endpoint'], test['params'], contract_address)
            
            if not data:
                results[test['name']] = {"status": "no_response", "nft_count": 0}
                continue
            
            if data.get('code') != 0:
                results[test['name']] = {
                    "status": "error",
                    "okx_code": data.get('code'),
                    "nft_count": 0
                }
                continue
            
            # Get NFTs
            response_data = data.get('data', {})
            if isinstance(response_data, dict) and 'data' in response_data:
                nfts = response_data['data']
            else:
                nfts = response_data if isinstance(response_data, list) else []
            
            # Check contract matching
            contract_matches = 0
            sample_tokens = []
            
            for nft in nfts[:3]:
                token_id = nft.get('tokenId', 'unknown')
                sample_tokens.append(token_id)
                
                nft_contract = (
                    nft.get('assetContract', {}).get('contractAddress', '') or
                    nft.get('contractAddress', '') or
                    'NOT_FOUND'
                ).lower()
                
                if nft_contract == contract_address.lower():
                    contract_matches += 1
            
            results[test['name']] = {
                "status": "success",
                "okx_code": data.get('code'),
                "nft_count": len(nfts),
                "contract_matches": contract_matches,
                "sample_tokens": sample_tokens,
                "params_used": test['params'],
                "working": len(nfts) > 0 and contract_matches > 0
            }
        
        # Find best working test
        working_tests = []
        for test_name, result in results.items():
            if result.get('working'):
                working_tests.append({
                    "test": test_name,
                    "matches": result.get('contract_matches', 0),
                    "total": result.get('nft_count', 0)
                })
        
        return jsonify({
            "success": True,
            "contract_tested": contract_address,
            "test_results": results,
            "working_tests": working_tests,
            "recommendation": working_tests[0] if working_tests else "No working configuration found",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/nfts/<contract>')
def get_nfts(contract):
    """Get NFTs using best known parameters with price sorting fix"""
    try:
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({'success': False, 'error': result}), 400
        
        contract_address = result
        limit = int(request.args.get('limit', 12))
        sort_by = request.args.get('sort_by', 'none')
        
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured"
            }), 500
        
        # Use assets endpoint (confirmed working)
        params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': str(min(limit, 50))
        }
        
        data = make_okx_request('/api/v5/mktplace/nft/asset/list', params, contract_address)
        
        if not data or data.get('code') != 0:
            return jsonify({
                "success": False,
                "error": "Could not get NFTs from OKX",
                "contract_address": contract_address,
                "debug": {
                    "okx_code": data.get('code') if data else 'no_response',
                    "message": data.get('msg') if data else 'no_response'
                }
            }), 404
        
        # Process data
        response_data = data.get('data', {})
        if isinstance(response_data, dict) and 'data' in response_data:
            nfts = response_data['data']
        else:
            nfts = response_data if isinstance(response_data, list) else []
        
        # Filter by contract (confirmed working perfectly)
        filtered_nfts = []
        for nft in nfts:
            nft_contract = (
                nft.get('assetContract', {}).get('contractAddress', '') or
                nft.get('contractAddress', '')
            ).lower()
            
            if nft_contract == contract_address.lower():
                filtered_nfts.append(nft)
        
        # TRY TO GET PRICE DATA (experimental approach)
        price_data = {}
        if sort_by in ['price_asc', 'price_desc'] and len(filtered_nfts) > 0:
            print(f"💰 Attempting to get price data for {len(filtered_nfts)} NFTs")
            
            # Try to get general listings and match by token IDs
            listings_params = {
                'chain': 'taiko',
                'limit': '50'  # Get more listings to increase match chances
            }
            
            listings_data = make_okx_request('/api/v5/mktplace/nft/markets/listings', listings_params, contract_address)
            
            if listings_data and listings_data.get('code') == 0:
                listings_response = listings_data.get('data', {})
                if isinstance(listings_response, dict) and 'data' in listings_response:
                    all_listings = listings_response['data']
                else:
                    all_listings = listings_response if isinstance(listings_response, list) else []
                
                # Create token ID set from our valid NFTs
                our_token_ids = {nft.get('tokenId') for nft in filtered_nfts if nft.get('tokenId')}
                
                # Try to match prices by token ID
                matched_prices = 0
                for listing in all_listings:
                    listing_token_id = listing.get('tokenId')
                    listing_price = listing.get('price') or listing.get('listingPrice')
                    
                    # If this token ID matches one of our NFTs, store the price
                    if (listing_token_id and 
                        str(listing_token_id) in our_token_ids and 
                        listing_price):
                        price_data[str(listing_token_id)] = listing_price
                        matched_prices += 1
                
                print(f"💰 Matched prices for {matched_prices}/{len(our_token_ids)} NFTs")
        
        # Process NFTs with price enrichment
        processed_nfts = []
        for i, nft in enumerate(filtered_nfts[:limit]):
            try:
                token_id = nft.get('tokenId') or str(i + 1)
                name = nft.get('name') or f"NFT #{token_id}"
                image = nft.get('image') or nft.get('imageUrl') or ''
                
                # Check if we have price data for this token
                price = None
                price_source = 'none'
                if str(token_id) in price_data:
                    price_raw = price_data[str(token_id)]
                    try:
                        price_num = float(price_raw)
                        if price_num > 1e10:  # Convert from wei
                            price_num = price_num / 1e18
                        price = f"{price_num:.6f}".rstrip('0').rstrip('.')
                        price_source = 'listings_matched'
                    except:
                        price = str(price_raw)
                        price_source = 'listings_raw'
                
                processed_nft = {
                    'id': f"{contract_address}_{token_id}",
                    'tokenId': str(token_id),
                    'name': name,
                    'image': image,
                    'price': price,
                    'priceSource': price_source,
                    'currency': 'ETH' if price else None,
                    'status': 'listed' if price else 'unlisted',
                    'contractAddress': contract_address,
                    'fresh_timestamp': datetime.utcnow().isoformat()
                }
                
                processed_nfts.append(processed_nft)
                
            except Exception as e:
                print(f"Error processing NFT {i}: {e}")
                continue
        
        # SORTING (now with price support)
        if sort_by in ['price_asc', 'price_desc'] and len(processed_nfts) > 1:
            def get_sort_price(nft):
                price = nft.get('price')
                if not price:
                    return 0 if sort_by == 'price_asc' else float('inf')
                try:
                    return float(price)
                except:
                    return 0 if sort_by == 'price_asc' else float('inf')
            
            processed_nfts.sort(key=get_sort_price, reverse=(sort_by == 'price_desc'))
            print(f"🔄 Applied sorting: {sort_by}")
        
        with_prices = sum(1 for nft in processed_nfts if nft.get('price'))
        
        return jsonify({
            "success": True,
            "data": processed_nfts,
            "count": len(processed_nfts),
            "contract_address": contract_address,
            "sort_by": sort_by,
            "total_from_okx": len(nfts),
            "filtered_count": len(filtered_nfts),
            "price_info": {
                "nfts_with_prices": with_prices,
                "total_nfts": len(processed_nfts),
                "price_coverage": f"{round(with_prices/len(processed_nfts)*100, 1)}%" if processed_nfts else "0%",
                "sorting_applied": sort_by in ['price_asc', 'price_desc']
            },
            "okx_bug_info": {
                "assets_endpoint": "working_perfectly",
                "listings_endpoint": "ignores_contractAddress_but_used_for_prices",
                "workaround": "token_id_matching_from_general_listings_pool"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available": ["/", "/api", "/api/contracts", "/api/test-params/<contract>", "/api/nfts/<contract>"]
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "error": "Server error",
        "message": str(error)
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
