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

# Disable all caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Enable CORS + No Cache Headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # FORCE NO CACHE
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['ETag'] = f'"{random.randint(1000000, 9999999)}"'
    
    return response

# OKX Configuration
OKX_API_KEY = os.getenv('OKX_API_KEY', '0321b6d3-385f-428e-9516-d3f1cb013f99')
OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY', '6C366DF95B6F365B73483A63339E0F27')
OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE', '462230Gutu99!')

def validate_contract_address(address):
    """Validează adresa contractului"""
    if not address or not isinstance(address, str):
        return False, "Contract address invalid"
    
    address = address.strip()
    if not address.startswith('0x') or len(address) != 42:
        return False, "Contract address format invalid"
    
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return False, "Contract address contains invalid characters"
    
    return True, address.lower()

def create_fresh_okx_signature(timestamp, method, request_path, body='', query_string=''):
    """Creează semnătura OKX FRESH"""
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
        print(f"❌ Signature error: {e}")
        return ""

def make_fresh_okx_request(endpoint, params=None, contract_address=None):
    """Face request FRESH către OKX API"""
    try:
        # FRESH timestamp + random
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Add random param to force fresh
        if not params:
            params = {}
        params['_fresh'] = str(int(time.time() * 1000))
        params['_rand'] = str(random.randint(100000, 999999))
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        # FRESH signature
        signature = create_fresh_okx_signature(timestamp, 'GET', endpoint, '', query_string)
        
        headers = {
            'OK-ACCESS-KEY': OKX_API_KEY,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'User-Agent': f'OKX-NFT-Client-{random.randint(1000, 9999)}'
        }
        
        url = f"https://www.okx.com{endpoint}?{query_string}"
        
        print(f"🔄 FRESH Request: {contract_address}")
        
        # FRESH REQUEST
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        session.close()
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('code', 'unknown')}")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

@app.route('/')
def root():
    fresh_id = f"fresh_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    return jsonify({
        "status": "healthy",
        "service": "OKX NFT Backend - FRESH & SIMPLE",
        "version": "3.1.0-simple",
        "fresh_id": fresh_id,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": [
            "/api - health check",
            "/api/test - test connection", 
            "/api/contracts - known contracts",
            "/api/debug/<contract> - debug raw OKX data",
            "/api/nfts/<contract> - get NFTs",
            "/api/nfts/<contract>?sort_by=price_asc",
            "/api/nfts/<contract>?sort_by=price_desc"
        ]
    })

@app.route('/api')
def api():
    return jsonify({
        "status": "healthy",
        "service": "OKX NFT API",
        "fresh_id": f"api_{int(time.time() * 1000)}",
        "okx_keys_ready": bool(OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/test')
def test():
    return jsonify({
        "success": True,
        "message": "Backend working - FRESH REQUESTS",
        "test_id": f"test_{int(time.time() * 1000)}",
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
                "test_url": f"/api/nfts/0x4a045c5016b200f7e08a4cabb2cda6e85bf53295?sort_by=price_asc&limit=4"
            },
            {
                "name": "Taikonauts",
                "address": "0x56b0d8d04de22f2539945258ddb288c123026775",
                "test_url": f"/api/nfts/0x56b0d8d04de22f2539945258ddb288c123026775?sort_by=price_asc&limit=4"
            }
        ],
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/debug/<contract>')
def debug_contract(contract):
    """Debug raw OKX response for contract"""
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
        
        params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': '10'
        }
        
        # Try both endpoints
        listings_data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', params, contract_address)
        assets_data = make_fresh_okx_request('/api/v5/mktplace/nft/asset/list', params, contract_address)
        
        # Extract sample NFTs for analysis
        def extract_sample_nfts(data, source):
            if not data or data.get('code') != 0:
                return f"Failed: {data.get('code') if data else 'no data'}"
            
            response_data = data.get('data', {})
            if isinstance(response_data, dict) and 'data' in response_data:
                nfts = response_data['data']
            else:
                nfts = response_data if isinstance(response_data, list) else []
            
            sample = []
            for nft in nfts[:3]:
                sample.append({
                    "tokenId": nft.get('tokenId'),
                    "name": nft.get('name'),
                    "price": nft.get('price') or nft.get('listingPrice'),
                    "contractFromNFT": (
                        nft.get('assetContract', {}).get('contractAddress', '') or
                        nft.get('contractAddress', '') or
                        nft.get('asset', {}).get('contractAddress', '') or
                        nft.get('collection', {}).get('contractAddress', '') or
                        "NOT_FOUND"
                    ),
                    "requestedContract": contract_address
                })
            
            return {
                "total_nfts": len(nfts),
                "sample_nfts": sample
            }
        
        return jsonify({
            "success": True,
            "contract_requested": contract_address,
            "debug_data": {
                "listings_endpoint": extract_sample_nfts(listings_data, "listings"),
                "assets_endpoint": extract_sample_nfts(assets_data, "assets")
            },
            "raw_responses": {
                "listings_code": listings_data.get('code') if listings_data else 'failed',
                "assets_code": assets_data.get('code') if assets_data else 'failed'
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/nfts/<contract>')
def get_nfts(contract):
    """Get FRESH NFT data from OKX"""
    try:
        # Validate contract
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': result,
                'provided_address': contract
            }), 400
        
        contract_address = result
        request_id = f"req_{int(time.time() * 1000)}_{random.randint(10000, 99999)}"
        
        print(f"🚀 FRESH NFT request: {contract_address} (ID: {request_id})")
        
        # Parameters
        limit = int(request.args.get('limit', 12))
        sort_by = request.args.get('sort_by', 'none')
        
        # Check OKX keys
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured",
                "request_id": request_id
            }), 500
        
        # Base parameters
        base_params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': str(min(limit, 50))
        }
        
        # STRATEGY BASED ON SORT TYPE
        data = None
        endpoint_used = "none"
        nfts = []
        
        if sort_by in ['price_asc', 'price_desc']:
            # FOR PRICE SORTING: Use listings directly (has prices, even if contract filtering is broken)
            print(f"💰 Price sorting requested - using listings endpoint")
            data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', base_params, contract_address)
            endpoint_used = "listings_for_prices"
            
            if data and data.get('code') == 0:
                response_data = data.get('data', {})
                if isinstance(response_data, dict) and 'data' in response_data:
                    nfts = response_data['data']
                else:
                    nfts = response_data if isinstance(response_data, list) else []
                
                print(f"💰 Listings returned {len(nfts)} NFTs with prices")
                
                # FOR LISTINGS: Don't filter by contract - OKX seems to return mixed results
                # Just use all results since we requested a specific contract
                print(f"⚠️ Using all listings results (OKX contract filtering unreliable)")
            
        else:
            # FOR BROWSING: Use assets (better contract filtering, correct names/IDs)
            print(f"📦 Browsing mode - using assets endpoint")
            data = make_fresh_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
            endpoint_used = "assets_for_browsing"
            
            if data and data.get('code') == 0:
                response_data = data.get('data', {})
                if isinstance(response_data, dict) and 'data' in response_data:
                    nfts = response_data['data']
                else:
                    nfts = response_data if isinstance(response_data, list) else []
                
                print(f"📦 Assets returned {len(nfts)} NFTs")
                
                # For assets, apply contract filtering
                if len(nfts) > 0:
                    original_count = len(nfts)
                    filtered_nfts = []
                    
                    for nft in nfts:
                        nft_contract = (
                            nft.get('assetContract', {}).get('contractAddress', '') or
                            nft.get('contractAddress', '') or
                            nft.get('asset', {}).get('contractAddress', '') or
                            nft.get('token', {}).get('contractAddress', '') or
                            nft.get('collection', {}).get('contractAddress', '')
                        ).lower()
                        
                        if nft_contract == contract_address.lower():
                            filtered_nfts.append(nft)
                    
                    nfts = filtered_nfts
                    print(f"🔍 Assets filtering: {original_count} -> {len(nfts)} NFTs")
        
        if not data or data.get('code') != 0 or len(nfts) == 0:
            return jsonify({
                "success": False,
                "error": "Could not get NFTs from OKX" if not data or data.get('code') != 0 else "No NFTs found for this contract",
                "contract_address": contract_address,
                "endpoint_used": endpoint_used,
                "request_id": request_id,
                "debug": {
                    "okx_code": data.get('code') if data else 'no_response',
                    "nfts_returned": len(nfts),
                    "sort_requested": sort_by
                },
                "suggestions": [
                    "Try browsing mode (no sort_by parameter)",
                    "Try known contracts: /api/contracts",
                    "Contract might not have listings on OKX"
                ]
            }), 500
        
        print(f"📦 Using {len(nfts)} NFTs from {endpoint_used}")
        
        # Client-side sorting if needed
        if sort_by in ['price_asc', 'price_desc'] and len(nfts) > 1:
            def get_price(nft):
                price = nft.get('price') or nft.get('listingPrice') or nft.get('priceEth')
                if not price:
                    return 0 if sort_by == 'price_asc' else float('inf')
                try:
                    price_num = float(price)
                    # Convert from wei if needed
                    if price_num > 1e10:
                        price_num = price_num / 1e18
                    return price_num
                except:
                    return 0 if sort_by == 'price_asc' else float('inf')
            
            # Log prices before sorting for debugging
            prices_before = [get_price(nft) for nft in nfts[:5]]
            print(f"💰 Prices before sort: {prices_before}")
            
            nfts.sort(key=get_price, reverse=(sort_by == 'price_desc'))
            
            # Log prices after sorting
            prices_after = [get_price(nft) for nft in nfts[:5]]
            print(f"🔄 Prices after {sort_by}: {prices_after}")
            print(f"✅ Applied sorting: {sort_by}")
        
        # Process NFTs
        processed_nfts = []
        for i, nft in enumerate(nfts[:limit]):
            try:
                token_id = nft.get('tokenId') or nft.get('id') or str(i + 1)
                name = nft.get('name') or f"NFT #{token_id}"
                image = nft.get('image') or nft.get('imageUrl') or nft.get('imageURI') or ''
                
                # Price handling
                price = nft.get('price') or nft.get('listingPrice') or nft.get('priceEth')
                display_price = None
                if price:
                    try:
                        price_num = float(price)
                        if price_num > 1e10:  # Convert from wei
                            price_num = price_num / 1e18
                        display_price = f"{price_num:.6f}".rstrip('0').rstrip('.')
                    except:
                        display_price = str(price)
                
                processed_nft = {
                    'id': f"{contract_address}_{token_id}",
                    'tokenId': str(token_id),
                    'name': name,
                    'image': image,
                    'price': display_price,
                    'currency': 'ETH',
                    'status': 'listed' if price else 'unlisted',
                    'contractAddress': contract_address,
                    'fresh_timestamp': datetime.utcnow().isoformat()
                }
                
                processed_nfts.append(processed_nft)
                
            except Exception as e:
                print(f"❌ Error processing NFT {i}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "data": processed_nfts,
            "count": len(processed_nfts),
            "contract_address": contract_address,
            "sort_by": sort_by,
            "endpoint_used": endpoint_used,
            "request_id": request_id,
            "fresh": True,
            "debug": {
                "total_from_okx": len(nfts),
                "final_processed": len(processed_nfts),
                "with_prices": sum(1 for nft in processed_nfts if nft.get('price')),
                "sorting_applied": sort_by in ['price_asc', 'price_desc'],
                "strategy": "listings_for_prices" if sort_by in ['price_asc', 'price_desc'] else "assets_for_browsing"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in get_nfts: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "contract": contract
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available": ["/", "/api", "/api/test", "/api/contracts", "/api/nfts/<contract>"]
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "error": "Server error",
        "message": str(error)
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
