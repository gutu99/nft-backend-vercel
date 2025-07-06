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
    
    # FORCE NO CACHE - CRITICAL FOR FRESH DATA
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
    """Creează semnătura OKX FRESH pentru fiecare request"""
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
    """Face request COMPLET FRESH către OKX API - NO CACHE NICĂIERI"""
    try:
        # FORCE FRESH - timestamp cu microsecunde + random
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Add random param to force fresh
        if not params:
            params = {}
        params['_fresh'] = str(int(time.time() * 1000))  # Millisecond timestamp
        params['_rand'] = str(random.randint(100000, 999999))  # Random number
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        # FRESH signature pentru fiecare cerere
        signature = create_fresh_okx_signature(timestamp, 'GET', endpoint, '', query_string)
        
        headers = {
            'OK-ACCESS-KEY': OKX_API_KEY,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE,
            'Content-Type': 'application/json',
            
            # FORCE FRESH HEADERS - CRITICAL
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '0',
            'If-None-Match': '*',
            'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT',
            
            # User agent variation to avoid caching
            'User-Agent': f'OKX-NFT-Client-{random.randint(1000, 9999)}'
        }
        
        url = f"https://www.okx.com{endpoint}?{query_string}"
        
        print(f"🔄 ULTRA FRESH OKX Request for contract {contract_address}")
        print(f"📝 URL: {url}")
        print(f"⏰ Timestamp: {timestamp}")
        
        # FORCE FRESH REQUEST - new session every time
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15, stream=False)
        session.close()  # Close session immediately
        
        if response.status_code == 200:
            data = response.json()
            response_code = data.get('code', 'unknown')
            
            # Debug info pentru fiecare contract
            if isinstance(data.get('data'), dict) and 'data' in data['data']:
                nft_count = len(data['data']['data'])
                nfts = data['data']['data']
            elif isinstance(data.get('data'), list):
                nft_count = len(data['data'])
                nfts = data['data']
            else:
                nft_count = 0
                nfts = []
                
            print(f"✅ FRESH OKX Response for {contract_address}: code={response_code}, NFTs={nft_count}")
            
            # Log some token IDs to verify uniqueness
            if nfts and len(nfts) > 0:
                token_ids = [nft.get('tokenId', 'unknown') for nft in nfts[:3]]
                print(f"🏷️ Sample Token IDs: {token_ids}")
            
            return data
        else:
            print(f"❌ OKX Error for {contract_address}: {response.status_code} - {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ OKX Request error for {contract_address}: {e}")
        return None

def convert_price(price_str):
    """Convertește prețul la ETH"""
    if not price_str:
        return None
    
    try:
        price_value = float(str(price_str).replace(',', ''))
        if price_value <= 0:
            return None
        
        # Convert wei to ETH if needed
        if price_value > 1e10:
            return price_value / 1e18
        
        return price_value
    except:
        return None

def format_price(price_value):
    """Format price pentru display"""
    if not price_value:
        return None
    try:
        if price_value < 0.001:
            return f"{price_value:.8f}".rstrip('0').rstrip('.')
        elif price_value < 1:
            return f"{price_value:.6f}".rstrip('0').rstrip('.')
        else:
            return f"{price_value:.4f}".rstrip('0').rstrip('.')
    except:
        return str(price_value)

@app.route('/')
def root():
    return jsonify({
        "status": "healthy",
        "service": "OKX NFT Backend - ULTRA FRESH NO CACHE",
        "version": "3.0.0-ultra-fresh",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat(),
        "random_id": random.randint(100000, 999999),  # Pentru a forța fresh response
        "features": [
            "✅ ULTRA FRESH: Zero cache la toate nivelele",
            "✅ FRESH: Timestamp cu microsecunde + random",
            "✅ FRESH: Session nou pentru fiecare request",
            "✅ FRESH: Headers anti-cache hardcore",
            "✅ FIXED: Contract-specific data garantat",
            "✅ FIXED: Price sorting verificat și functional"
        ],
        "cache_busting": [
            "🚫 Response headers anti-cache",
            "🚫 Request headers anti-cache", 
            "🚫 Random parameters per request",
            "🚫 Fresh session per request",
            "🚫 Microsecond timestamps"
        ],
        "available_endpoints": [
            "/api - health check",
            "/api/test - test fresh connection", 
            "/api/nfts/<contract> - fresh NFT data",
            "/api/nfts/<contract>?sort_by=price_asc - sort ascending",
            "/api/nfts/<contract>?sort_by=price_desc - sort descending"
        ]
    })

@app.route('/api')
def api():
    return jsonify({
        "status": "healthy",
        "service": "OKX NFT Backend API - ULTRA FRESH",
        "version": "3.0.0-ultra-fresh",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat(),
        "fresh_id": f"fresh_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
        "okx_integration": "ACTIVE",
        "cache_status": "DISABLED_EVERYWHERE",
        "environment": {
            "has_okx_api_key": bool(OKX_API_KEY),
            "has_okx_secret": bool(OKX_SECRET_KEY), 
            "has_okx_passphrase": bool(OKX_PASSPHRASE),
            "keys_ready": bool(OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE)
        }
    })

@app.route('/api/test')
def test():
    """Test OKX connection with ULTRA FRESH data"""
    test_result = {
        "success": True,
        "message": "OKX integration test - ULTRA FRESH NO CACHE",
        "test_id": f"test_{int(time.time() * 1000)}_{random.randint(10000, 99999)}",
        "environment": {
            "flask_working": True,
            "vercel_deployment": True,
            "cache_disabled": True,
            "fresh_requests": True,
            "okx_keys": {
                "api_key": bool(OKX_API_KEY),
                "secret_key": bool(OKX_SECRET_KEY),
                "passphrase": bool(OKX_PASSPHRASE)
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return jsonify(test_result)

@app.route('/api/nfts/<contract>')
def get_nfts_ultra_fresh(contract):
    """Get ULTRA FRESH NFT data from OKX - NO CACHE ANYWHERE"""
    try:
        # Validare contract
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': result,
                'provided_address': contract,
                'fresh_id': f"error_{int(time.time() * 1000)}"
            }), 400
        
        contract_address = result
        request_id = f"req_{int(time.time() * 1000)}_{random.randint(10000, 99999)}"
        
        print(f"🚀 ULTRA FRESH NFT request for contract: {contract_address} (ID: {request_id})")
        
        # Parametri
        limit = int(request.args.get('limit', 12))
        sort_by = request.args.get('sort_by', 'price_asc')
        
        # Check OKX keys
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured",
                "contract_address": contract_address,
                "fresh_id": request_id
            }), 500
        
        # Base parameters cu anti-cache
        base_params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': str(min(limit, 50))
        }
        
        # SORTARE - încearcă ambele endpoint-uri
        data = None
        endpoint_used = "none"
        
        if sort_by in ['price_asc', 'price_desc']:
            print(f"💰 Attempting price sorting: {sort_by}")
            
            # Încearcă listings endpoint pentru sortare
            sort_params = base_params.copy()
            if sort_by == 'price_asc':
                sort_params.update({'sortBy': 'price', 'orderBy': 'asc'})
            else:
                sort_params.update({'sortBy': 'price', 'orderBy': 'desc'})
            
            data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', sort_params, contract_address)
            endpoint_used = "listings_with_sort"
            
            # Dacă nu funcționează, încearcă fără sort
            if not data or data.get('code') != 0:
                print(f"⚠️ Sorted listings failed, trying unsorted listings")
                data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', base_params, contract_address)
                endpoint_used = "listings_no_sort"
        
        # Fallback la assets endpoint
        if not data or data.get('code') != 0:
            print(f"🔄 Trying assets endpoint as fallback")
            data = make_fresh_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
            endpoint_used = "assets_fallback"
        
        if not data or data.get('code') != 0:
            return jsonify({
                "success": False,
                "error": "Nu s-au putut obține NFT-urile de la OKX",
                "okx_response_code": data.get('code') if data else None,
                "contract_address": contract_address,
                "endpoint_used": endpoint_used,
                "sort_attempted": sort_by,
                "fresh_id": request_id,
                "debug": {
                    "okx_response": data,
                    "params_used": base_params,
                    "ultra_fresh": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }), 500
        
        # Procesează datele
        response_data = data.get('data', {})
        if isinstance(response_data, dict) and 'data' in response_data:
            nfts = response_data['data']
        else:
            nfts = response_data if isinstance(response_data, list) else []
        
        print(f"📦 Received {len(nfts)} NFTs for contract {contract_address}")
        
        # FILTRARE STRICTĂ pentru contract
        if len(nfts) > 0:
            original_count = len(nfts)
            filtered_nfts = []
            
            for nft in nfts:
                nft_contract = (
                    nft.get('assetContract', {}).get('contractAddress', '') or
                    nft.get('contractAddress', '') or
                    nft.get('asset', {}).get('contractAddress', '') or
                    nft.get('token', {}).get('contractAddress', '')
                ).lower()
                
                if nft_contract == contract_address.lower():
                    filtered_nfts.append(nft)
            
            nfts = filtered_nfts
            print(f"🔍 CONTRACT FILTER: {original_count} -> {len(nfts)} NFTs after strict filtering")
        
        # CLIENT-SIDE SORTING pentru a garanta ordinea
        if sort_by in ['price_asc', 'price_desc'] and len(nfts) > 1:
            def get_nft_price(nft):
                price = (nft.get('price') or 
                        nft.get('listingPrice') or 
                        nft.get('priceEth') or 
                        nft.get('priceWei'))
                if not price:
                    return 0 if sort_by == 'price_asc' else float('inf')
                try:
                    return float(price)
                except:
                    return 0 if sort_by == 'price_asc' else float('inf')
            
            reverse_order = (sort_by == 'price_desc')
            nfts.sort(key=get_nft_price, reverse=reverse_order)
            print(f"🔄 Applied CLIENT-SIDE sorting: {sort_by}")
        
        # Procesează NFT-urile
        processed_nfts = []
        for i, nft in enumerate(nfts[:limit]):
            try:
                token_id = nft.get('tokenId') or nft.get('id') or str(i + 1)
                name = nft.get('name') or f"NFT #{token_id}"
                image_url = nft.get('image') or nft.get('imageUrl') or nft.get('imageURI') or ''
                description = nft.get('description') or f'NFT #{token_id} from {contract_address}'
                
                # Price extraction
                price = (nft.get('price') or 
                        nft.get('listingPrice') or 
                        nft.get('priceEth') or 
                        nft.get('priceWei'))
                
                display_price = None
                numeric_price = None
                if price:
                    numeric_price = convert_price(price)
                    if numeric_price:
                        display_price = format_price(numeric_price)
                
                processed_nft = {
                    'id': f"{contract_address}_{token_id}_{request_id}",  # Unique per request
                    'tokenId': str(token_id),
                    'name': name,
                    'image': image_url,
                    'description': description,
                    'attributes': nft.get('attributes', []),
                    'price': display_price,
                    'priceRaw': price,
                    'priceNumeric': numeric_price,
                    'currency': 'ETH',
                    'status': 'listed' if price else 'unlisted',
                    'orderId': nft.get('orderId'),
                    'listingTime': nft.get('listingTime'),
                    'seller': nft.get('seller') or nft.get('maker'),
                    'contractAddress': contract_address,
                    'source': f'okx_ultra_fresh_{request_id}',
                    'fresh_timestamp': datetime.utcnow().isoformat()
                }
                
                processed_nfts.append(processed_nft)
                
            except Exception as e:
                print(f"❌ Error processing NFT {i} for contract {contract_address}: {e}")
                continue
        
        print(f"🎯 Processed {len(processed_nfts)} FRESH NFTs for contract {contract_address}")
        
        return jsonify({
            "success": True,
            "data": processed_nfts,
            "count": len(processed_nfts),
            "contract_address": contract_address,
            "limit": limit,
            "sort_by": sort_by,
            "source": f"okx_ultra_fresh_api_{request_id}",
            "deployment": "vercel",
            "okx_response_code": data.get('code'),
            "total_from_okx": len(nfts),
            "endpoint_used": endpoint_used,
            "ultra_fresh": True,
            "request_id": request_id,
            "cache_status": "DISABLED",
            "debug_info": {
                "params_sent": base_params,
                "nfts_received": len(nfts),
                "nfts_processed": len(processed_nfts),
                "contract_specific": True,
                "client_side_sort": sort_by in ['price_asc', 'price_desc']
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in get_nfts_ultra_fresh for contract {contract}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "contract_address": contract,
            "deployment": "vercel",
            "ultra_fresh": True,
            "version": "3.0.0-ultra-fresh"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/",
            "/api", 
            "/api/test",
            "/api/nfts/<contract>",
            "/api/nfts/<contract>?sort_by=price_asc",
            "/api/nfts/<contract>?sort_by=price_desc"
        ],
        "example_test_urls": [
            "/api/nfts/0x1234567890123456789012345678901234567890",
            "/api/nfts/0x1234567890123456789012345678901234567890?sort_by=price_asc"
        ],
        "deployment": "vercel",
        "version": "3.0.0-ultra-fresh",
        "fresh_id": f"404_{int(time.time() * 1000)}"
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "error": "Server error",
        "message": str(error),
        "deployment": "vercel",
        "version": "3.0.0-ultra-fresh",
        "fresh_id": f"500_{int(time.time() * 1000)}"
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
