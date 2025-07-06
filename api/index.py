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

# Enable CORS + NUCLEAR No Cache Headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # NUCLEAR ANTI-CACHE - Every response is unique
    current_time = time.time()
    microseconds = int(current_time * 1000000)
    
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, s-maxage=0, no-transform, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
    response.headers['Last-Modified'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
    response.headers['ETag'] = f'"never-cache-{microseconds}"'
    response.headers['Vary'] = 'User-Agent, Accept-Encoding, Authorization'
    response.headers['X-Accel-Expires'] = '0'  # Nginx cache
    response.headers['X-Cache-Control'] = 'no-cache'
    response.headers['X-Fresh-Response'] = f'ultra-fresh-{microseconds}'
    
    # Vercel-specific no-cache headers
    response.headers['Vercel-Cache'] = 'MISS'
    response.headers['X-Vercel-Cache'] = 'MISS'
    response.headers['CDN-Cache-Control'] = 'no-cache'
    
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
    """Face request ULTRA FRESH către OKX API - NUCLEAR ANTI-CACHE"""
    try:
        # NUCLEAR ANTI-CACHE: Include current time in EVERYTHING
        current_time = time.time()
        microseconds = int(current_time * 1000000)
        
        # FRESH timestamp cu timezone random pentru a confunda cache-ul
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # NUCLEAR cache busting - include contract address in EVERY parameter
        if not params:
            params = {}
        
        # CRITICAL: Modify the core parameters to include contract specificity
        original_contract = params.get('contractAddress', contract_address)
        
        # EXTREME cache busting with contract-specific parameters
        params.update({
            '_ultra_fresh': str(microseconds),
            '_rand': str(random.randint(100000, 999999)),
            '_contract_hash': str(hash(contract_address))[-8:],  # Contract-specific hash
            '_ts_micro': str(microseconds),
            '_nonce': str(random.randint(1000000, 9999999)),
            '_cache_bust': f"{contract_address[-8:]}_{microseconds}",
            '_request_id': f"req_{microseconds}_{random.randint(10000, 99999)}",
            # CRITICAL: Make the chain also contract-specific to prevent cross-contamination
            '_chain_bust': f"taiko_{contract_address[-4:]}",
            '_endpoint_id': endpoint.replace('/', '_'),
            
            # Override the original contract to make it TRULY unique per request
            'contractAddress': f"{original_contract}",  # Ensure fresh
            'chain': 'taiko'  # Always set fresh
        })
        
        # Build query string with extra randomization
        query_parts = []
        for k, v in params.items():
            query_parts.append(f"{k}={v}")
        
        # Add a final random parameter that changes every millisecond
        query_parts.append(f"_final_bust={int(time.time() * 1000000)}")
        query_string = '&'.join(query_parts)
        
        # FRESH signature
        signature = create_fresh_okx_signature(timestamp, 'GET', endpoint, '', query_string)
        
        headers = {
            'OK-ACCESS-KEY': OKX_API_KEY,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE,
            'Content-Type': 'application/json',
            
            # NUCLEAR ANTI-CACHE HEADERS
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0, s-maxage=0, no-transform',
            'Pragma': 'no-cache',
            'Expires': 'Thu, 01 Jan 1970 00:00:00 GMT',
            'Last-Modified': 'Thu, 01 Jan 1970 00:00:00 GMT',
            'If-None-Match': f'"never-match-{microseconds}"',
            'If-Modified-Since': 'Thu, 01 Jan 1970 00:00:00 GMT',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Cache-Bust': f'contract-{contract_address[-8:]}-{microseconds}',
            'X-Request-ID': f'ultra-fresh-{microseconds}',
            
            # Contract-specific User-Agent to prevent cross-contamination
            'User-Agent': f'OKX-NFT-Fresh-{contract_address[-8:]}-{microseconds}'
        }
        
        # Build URL with NUCLEAR cache busting
        base_url = f"https://www.okx.com{endpoint}"
        url = f"{base_url}?{query_string}"
        
        print(f"🚀 NUCLEAR FRESH Request: {contract_address}")
        print(f"🔥 Cache bust ID: {microseconds}")
        print(f"💣 Contract-specific: {contract_address[-8:]}")
        
        # NUCLEAR FRESH REQUEST
        session = requests.Session()
        
        # Force fresh connection
        session.headers.update({
            'Connection': 'close',  # Force close after request
            'Keep-Alive': 'timeout=1, max=1'  # Minimal keep-alive
        })
        
        # Disable session caching completely
        session.trust_env = False
        
        try:
            response = session.get(
                url, 
                headers=headers, 
                timeout=15,
                stream=False,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ NUCLEAR SUCCESS for {contract_address}: {data.get('code', 'unknown')}")
                print(f"📊 Response size: {len(str(data))} chars")
                
                # CRITICAL: Verify response freshness by checking if it contains our cache-busting params
                response_str = str(data)
                if '_ultra_fresh' in response_str or str(microseconds) in response_str:
                    print(f"⚡ CONFIRMED: Response contains our fresh markers")
                else:
                    print(f"⚠️ WARNING: Response might be cached (no fresh markers)")
                
                return data
            else:
                print(f"❌ NUCLEAR ERROR for {contract_address}: {response.status_code}")
                print(f"📄 Response: {response.text[:200]}")
                return None
                
        finally:
            # ALWAYS close session to prevent any caching
            session.close()
            
    except Exception as e:
        print(f"💥 NUCLEAR REQUEST ERROR for {contract_address}: {e}")
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
            "/api/test-random - test with random contracts",
            "/api/contracts - known contracts",
            "/api/verify/<contract> - verify if contract exists",
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

@app.route('/api/test-random')
def test_random_contracts():
    """Test with completely random contracts to see if OKX ignores invalid contracts"""
    try:
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured"
            }), 500
        
        # Test contracts: 1 valid, 1 similar invalid, 1 completely random
        test_contracts = [
            {
                "name": "Valid Contract (Taikoon)",
                "address": "0x4a045c5016b200f7e08a4cabb2cda6e85bf53295",
                "expected": "should_return_real_nfts"
            },
            {
                "name": "Similar Invalid Contract", 
                "address": "0x4a04565016b200f7e08a4cabb2cda6e85bf56295",
                "expected": "should_fail_or_return_empty"
            },
            {
                "name": "Completely Random Contract",
                "address": "0x1234567890123456789012345678901234567890", 
                "expected": "should_definitely_fail"
            },
            {
                "name": "Another Random Contract",
                "address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "expected": "should_definitely_fail"
            }
        ]
        
        results = {}
        
        for test in test_contracts:
            contract_address = test["address"]
            
            # Test both endpoints
            base_params = {
                'chain': 'taiko',
                'contractAddress': contract_address,
                'limit': '3',
                '_test': f'random_{int(time.time() * 1000)}',
                '_contract_test': contract_address[-8:]  # Last 8 chars for uniqueness
            }
            
            print(f"🧪 Testing contract: {test['name']} - {contract_address}")
            
            # Test assets
            assets_data = make_fresh_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
            
            # Test listings  
            listings_data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', base_params, contract_address)
            
            def analyze_response(data, endpoint):
                if not data:
                    return {"status": "no_response", "nft_count": 0}
                
                if data.get('code') != 0:
                    return {
                        "status": "error",
                        "okx_code": data.get('code'),
                        "okx_message": data.get('msg', ''),
                        "nft_count": 0
                    }
                
                response_data = data.get('data', {})
                if isinstance(response_data, dict) and 'data' in response_data:
                    nfts = response_data['data']
                else:
                    nfts = response_data if isinstance(response_data, list) else []
                
                # Check if any NFT has contract info
                contract_info = "no_nfts"
                sample_token_ids = []
                
                if nfts:
                    sample_token_ids = [nft.get('tokenId', 'unknown') for nft in nfts[:3]]
                    
                    # Check contract from first NFT
                    first_nft = nfts[0]
                    nft_contract = (
                        first_nft.get('assetContract', {}).get('contractAddress', '') or
                        first_nft.get('contractAddress', '') or
                        'NOT_FOUND'
                    ).lower()
                    
                    if nft_contract == contract_address.lower():
                        contract_info = "matches_requested"
                    elif nft_contract != 'NOT_FOUND' and nft_contract != '':
                        contract_info = f"different_contract_{nft_contract[-8:]}"
                    else:
                        contract_info = "no_contract_info"
                
                return {
                    "status": "success",
                    "okx_code": data.get('code'),
                    "nft_count": len(nfts),
                    "contract_info": contract_info,
                    "sample_token_ids": sample_token_ids
                }
            
            results[test["name"]] = {
                "contract": contract_address,
                "expected": test["expected"],
                "assets_result": analyze_response(assets_data, "assets"),
                "listings_result": analyze_response(listings_data, "listings")
            }
        
        # Analysis
        analysis = {
            "cache_issues": False,
            "okx_ignores_invalid_contracts": False,
            "identical_responses": False
        }
        
        # Check if invalid contracts return same data as valid ones
        valid_assets = results["Valid Contract (Taikoon)"]["assets_result"]
        invalid_assets = results["Similar Invalid Contract"]["assets_result"]
        random_assets = results["Completely Random Contract"]["assets_result"]
        
        if (valid_assets.get("nft_count", 0) > 0 and 
            invalid_assets.get("nft_count", 0) > 0 and
            valid_assets.get("sample_token_ids") == invalid_assets.get("sample_token_ids")):
            analysis["identical_responses"] = True
            analysis["cache_issues"] = True
        
        if (invalid_assets.get("nft_count", 0) > 0 or random_assets.get("nft_count", 0) > 0):
            analysis["okx_ignores_invalid_contracts"] = True
        
        return jsonify({
            "success": True,
            "test_purpose": "Verify if OKX API ignores invalid contracts and returns cached/general data",
            "test_results": results,
            "analysis": analysis,
            "conclusions": [
                "If identical_responses=true: OKX has cache issues or ignores contractAddress",
                "If okx_ignores_invalid_contracts=true: OKX returns data for any contract",
                "If all invalid contracts return 0 NFTs: OKX validates contracts properly"
            ],
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
def verify_contract(contract):
    """Verify if contract exists and has NFTs - ULTRA FRESH"""
    try:
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': result,
                'provided_address': contract,
                'verification': 'format_invalid'
            }), 400
        
        contract_address = result
        verification_id = f"verify_{int(time.time() * 1000)}_{random.randint(10000, 99999)}"
        
        print(f"🔍 VERIFICATION for contract: {contract_address} (ID: {verification_id})")
        
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured"
            }), 500
        
        # Test both endpoints with ultra fresh requests
        base_params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': '5'
        }
        
        # Test assets endpoint
        print(f"🧪 Testing ASSETS endpoint for {contract_address}")
        assets_data = make_fresh_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
        
        # Test listings endpoint  
        print(f"🧪 Testing LISTINGS endpoint for {contract_address}")
        listings_data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', base_params, contract_address)
        
        # Analyze results
        def analyze_endpoint_result(data, endpoint_name):
            if not data:
                return {
                    "status": "failed",
                    "error": "No response from OKX",
                    "nft_count": 0
                }
            
            if data.get('code') != 0:
                return {
                    "status": "error",
                    "okx_code": data.get('code'),
                    "okx_message": data.get('msg', ''),
                    "nft_count": 0
                }
            
            response_data = data.get('data', {})
            if isinstance(response_data, dict) and 'data' in response_data:
                nfts = response_data['data']
            else:
                nfts = response_data if isinstance(response_data, list) else []
            
            # Sample first NFT for analysis
            sample_nft = None
            contract_match = False
            if nfts and len(nfts) > 0:
                first_nft = nfts[0]
                nft_contract = (
                    first_nft.get('assetContract', {}).get('contractAddress', '') or
                    first_nft.get('contractAddress', '') or
                    first_nft.get('asset', {}).get('contractAddress', '') or
                    'NOT_FOUND'
                ).lower()
                
                contract_match = (nft_contract == contract_address.lower())
                
                sample_nft = {
                    "tokenId": first_nft.get('tokenId'),
                    "name": first_nft.get('name'),
                    "has_price": bool(first_nft.get('price') or first_nft.get('listingPrice')),
                    "contract_from_nft": nft_contract,
                    "contract_matches": contract_match
                }
            
            return {
                "status": "success",
                "okx_code": data.get('code'),
                "nft_count": len(nfts),
                "contract_match": contract_match,
                "sample_nft": sample_nft
            }
        
        assets_result = analyze_endpoint_result(assets_data, "assets")
        listings_result = analyze_endpoint_result(listings_data, "listings")
        
        # Overall verification conclusion
        contract_exists = (
            (assets_result["status"] == "success" and assets_result["nft_count"] > 0) or
            (listings_result["status"] == "success" and listings_result["nft_count"] > 0)
        )
        
        has_listings = (listings_result["status"] == "success" and listings_result["nft_count"] > 0)
        
        return jsonify({
            "success": True,
            "contract_address": contract_address,
            "verification_id": verification_id,
            "ultra_fresh": True,
            "verification_result": {
                "contract_exists": contract_exists,
                "has_listings": has_listings,
                "recommended_endpoint": "listings" if has_listings else "assets" if contract_exists else "none"
            },
            "endpoint_tests": {
                "assets": assets_result,
                "listings": listings_result
            },
            "conclusion": {
                "usable_for_browsing": assets_result["status"] == "success" and assets_result["nft_count"] > 0,
                "usable_for_price_sorting": listings_result["status"] == "success" and listings_result["nft_count"] > 0,
                "contract_filtering_needed": not (assets_result.get("contract_match", False) and listings_result.get("contract_match", False))
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "verification": "failed"
        }), 500

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
            # Additional check for invalid contract
            error_msg = "Could not get NFTs from OKX"
            if data and data.get('code') != 0:
                error_msg = f"OKX API error: {data.get('code')} - {data.get('msg', 'Unknown error')}"
            elif len(nfts) == 0:
                error_msg = "No NFTs found - contract may not exist or have no listings"
            
            return jsonify({
                "success": False,
                "error": error_msg,
                "contract_address": contract_address,
                "endpoint_used": endpoint_used,
                "request_id": request_id,
                "contract_validation": {
                    "format_valid": True,  # Passed initial validation
                    "exists_on_okx": False,  # No NFTs found
                    "possible_reasons": [
                        "Contract address does not exist",
                        "Contract has no NFTs",
                        "Contract not indexed by OKX",
                        "Typing error in contract address"
                    ]
                },
                "debug": {
                    "okx_code": data.get('code') if data else 'no_response',
                    "okx_message": data.get('msg') if data else 'no_response',
                    "nfts_returned": len(nfts),
                    "sort_requested": sort_by,
                    "ultra_fresh_request": True,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "suggestions": [
                    "Verify the contract address is correct",
                    "Try browsing mode (no sort_by parameter)",
                    "Try known working contracts: /api/contracts",
                    "Check if contract exists on blockchain explorer"
                ]
            }), 404
        
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
