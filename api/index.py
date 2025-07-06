return jsonify(test_result)

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
                
                if data.get('code') != 0from flask import Flask, jsonify, request
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
        "service": "OKX NFT Backend - BUG WORKAROUND IMPLEMENTED",
        "version": "3.2.0-okx-bug-fixed",
        "fresh_id": fresh_id,
        "timestamp": datetime.utcnow().isoformat(),
        "okx_bug_discovered": {
            "issue": "OKX listings endpoint ignores contractAddress parameter",
            "impact": "Returns general listings pool instead of contract-specific NFTs",
            "workaround": "Using assets endpoint + selective price enrichment",
            "status": "FIXED"
        },
        "endpoints": [
            "/api - health check",
            "/api/test - test connection", 
            "/api/test-random - test with random contracts",
            "/api/test-chain-params/<contract> - test chain parameter values",
            "/api/test-listings-params/<contract> - test listings parameters",
            "/api/contracts - known contracts",
            "/api/verify/<contract> - verify if contract exists",
            "/api/debug/<contract> - debug raw OKX data",
            "/api/nfts/<contract> - get NFTs (fixed with workaround)",
            "/api/nfts/<contract>?sort_by=price_asc - sort ascending (fixed)",
            "/api/nfts/<contract>?sort_by=price_desc - sort descending (fixed)"
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

@app.route('/api/test-chain-params/<contract>')
def test_chain_parameters(contract):
    """Test different chain parameter values based on OKX URL patterns"""
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
        
        # Test different chain parameter values based on OKX marketplace URL patterns
        chain_variants = [
            {
                "name": "taiko_lowercase",
                "chain_value": "taiko",
                "note": "Current value - matches OKX URL /nft/collection/taiko/"
            },
            {
                "name": "TAIKO_uppercase", 
                "chain_value": "TAIKO",
                "note": "Uppercase variant"
            },
            {
                "name": "Taiko_titlecase",
                "chain_value": "Taiko", 
                "note": "Title case variant"
            },
            {
                "name": "taiko_mainnet",
                "chain_value": "taiko-mainnet",
                "note": "With mainnet suffix"
            },
            {
                "name": "167000_chain_id",
                "chain_value": "167000",
                "note": "Using Taiko chain ID number"
            },
            {
                "name": "tko_token_symbol",
                "chain_value": "tko",
                "note": "Using token symbol"
            }
        ]
        
        results = {}
        
        for variant in chain_variants:
            chain_value = variant["chain_value"]
            
            # Test both endpoints with this chain value
            base_params = {
                'chain': chain_value,
                'contractAddress': contract_address,
                'limit': '3',
                '_test_chain': f'{chain_value}_{int(time.time() * 1000)}'
            }
            
            print(f"🌐 Testing chain parameter: {variant['name']} = '{chain_value}'")
            
            # Test assets endpoint
            assets_data = make_fresh_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
            
            # Test listings endpoint
            listings_data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', base_params, contract_address)
            
            def analyze_chain_response(data, endpoint_name):
                if not data:
                    return {"status": "no_response", "nft_count": 0, "working": False}
                
                if data.get('code') != 0:
                    return {
                        "status": "error",
                        "okx_code": data.get('code'),
                        "okx_message": data.get('msg', ''),
                        "nft_count": 0,
                        "working": False
                    }
                
                response_data = data.get('data', {})
                if isinstance(response_data, dict) and 'data' in response_data:
                    nfts = response_data['data']
                else:
                    nfts = response_data if isinstance(response_data, list) else []
                
                # Check contract matching for assets endpoint
                contract_matches = 0
                if endpoint_name == "assets" and nfts:
                    for nft in nfts:
                        nft_contract = (
                            nft.get('assetContract', {}).get('contractAddress', '') or
                            nft.get('contractAddress', '')
                        ).lower()
                        
                        if nft_contract == contract_address.lower():
                            contract_matches += 1
                
                return {
                    "status": "success",
                    "okx_code": data.get('code'),
                    "nft_count": len(nfts),
                    "contract_matches": contract_matches,
                    "working": len(nfts) > 0,
                    "contract_specific": contract_matches > 0 if endpoint_name == "assets" else "unknown"
                }
            
            assets_result = analyze_chain_response(assets_data, "assets")
            listings_result = analyze_chain_response(listings_data, "listings")
            
            results[variant["name"]] = {
                "chain_value": chain_value,
                "note": variant["note"],
                "assets_endpoint": assets_result,
                "listings_endpoint": listings_result,
                "overall_working": assets_result["working"] or listings_result["working"]
            }
        
        # Find best working chain values
        working_chains = []
        best_chains = []
        
        for variant_name, result in results.items():
            if result["overall_working"]:
                working_chains.append(variant_name)
                
                # Prefer assets endpoint that returns contract-specific data
                if (result["assets_endpoint"]["working"] and 
                    result["assets_endpoint"]["contract_specific"] == True):
                    best_chains.append({
                        "variant": variant_name,
                        "chain_value": result["chain_value"],
                        "reason": f"Assets endpoint returns {result['assets_endpoint']['contract_matches']} contract-specific NFTs"
                    })
        
        return jsonify({
            "success": True,
            "contract_tested": contract_address,
            "test_results": results,
            "analysis": {
                "total_variants_tested": len(chain_variants),
                "working_chain_values": working_chains,
                "best_chain_values": best_chains,
                "current_chain_working": "taiko_lowercase" in working_chains
            },
            "recommendations": best_chains if best_chains else [
                "No chain values returned contract-specific data",
                "Current 'taiko' value may be correct but contract might not exist",
                "Try with a known working contract address"
            ],
            "url_pattern_analysis": {
                "okx_marketplace_url": f"/nft/collection/taiko/{contract_address}",
                "suggests_chain_param": "taiko",
                "current_usage": "taiko (matches URL pattern)"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    """Test different parameter combinations for listings endpoint"""
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
        
        # Test different parameter combinations for listings endpoint
        test_variants = [
            {
                "name": "Standard_contractAddress_chain",
                "params": {
                    'chain': 'taiko',
                    'contractAddress': contract_address,
                    'limit': '5'
                }
            },
            {
                "name": "Only_chain",
                "params": {
                    'chain': 'taiko',
                    'limit': '5'
                }
            },
            {
                "name": "Chain_with_slug",
                "params": {
                    'chain': 'taiko',
                    'slug': 'taikoon',  # Try with collection slug
                    'limit': '5'
                }
            },
            {
                "name": "Chain_with_collectionAddress",
                "params": {
                    'chain': 'taiko',
                    'collectionAddress': contract_address,  # Maybe it's collectionAddress not contractAddress
                    'limit': '5'
                }
            },
            {
                "name": "Chain_with_tokenAddress",
                "params": {
                    'chain': 'taiko',
                    'tokenAddress': contract_address,  # Maybe it's tokenAddress
                    'limit': '5'
                }
            },
            {
                "name": "Chain_with_specific_tokenId",
                "params": {
                    'chain': 'taiko',
                    'contractAddress': contract_address,
                    'tokenId': '388',  # Try with specific token ID from our valid contract
                    'limit': '5'
                }
            },
            {
                "name": "Chain_with_collection_field",
                "params": {
                    'chain': 'taiko',
                    'collection': contract_address,
                    'limit': '5'
                }
            }
        ]
        
        results = {}
        
        for test in test_variants:
            test_name = test["name"]
            params = test["params"]
            
            print(f"🧪 Testing listings with params: {test_name}")
            
            # Test this parameter combination
            data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', params, contract_address)
            
            def analyze_listings_response(data, variant_name):
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
                
                # Check contract matching
                contract_match_count = 0
                different_contracts = set()
                sample_token_ids = []
                
                for nft in nfts[:5]:  # Check first 5
                    token_id = nft.get('tokenId', 'unknown')
                    sample_token_ids.append(token_id)
                    
                    nft_contract = (
                        nft.get('assetContract', {}).get('contractAddress', '') or
                        nft.get('contractAddress', '') or
                        nft.get('asset', {}).get('contractAddress', '') or
                        nft.get('collectionAddress', '') or
                        'NOT_FOUND'
                    ).lower()
                    
                    if nft_contract == contract_address.lower():
                        contract_match_count += 1
                    elif nft_contract != 'not_found' and nft_contract:
                        different_contracts.add(nft_contract[-8:])  # Last 8 chars
                
                return {
                    "status": "success",
                    "okx_code": data.get('code'),
                    "nft_count": len(nfts),
                    "contract_matches": contract_match_count,
                    "contract_match_percentage": round((contract_match_count / len(nfts) * 100), 1) if nfts else 0,
                    "different_contracts_found": list(different_contracts),
                    "sample_token_ids": sample_token_ids,
                    "seems_contract_specific": contract_match_count > len(nfts) * 0.8  # 80%+ match rate
                }
            
            results[test_name] = {
                "params_used": params,
                "result": analyze_listings_response(data, test_name)
            }
        
        # Analysis and recommendations
        working_variants = []
        contract_specific_variants = []
        
        for variant_name, variant_data in results.items():
            result = variant_data["result"]
            if result["status"] == "success" and result["nft_count"] > 0:
                working_variants.append(variant_name)
                
                if result["seems_contract_specific"]:
                    contract_specific_variants.append({
                        "variant": variant_name,
                        "params": variant_data["params_used"],
                        "match_rate": result["contract_match_percentage"]
                    })
        
        return jsonify({
            "success": True,
            "contract_tested": contract_address,
            "test_results": results,
            "analysis": {
                "working_variants": working_variants,
                "contract_specific_variants": contract_specific_variants,
                "total_variants_tested": len(test_variants),
                "variants_returning_data": len(working_variants)
            },
            "recommendations": contract_specific_variants if contract_specific_variants else [
                "No variants found that return contract-specific data",
                "Listings endpoint may not support contract filtering",
                "Consider using assets endpoint for contract-specific data"
            ],
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
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
        
        # STRATEGY BASED ON REQUIREMENTS - FIXED FOR OKX BUG
        data = None
        endpoint_used = "none"
        nfts = []
        
        # ALWAYS use assets endpoint first (it's the only one that works correctly)
        print(f"📦 Using ASSETS endpoint (only reliable endpoint)")
        data = make_fresh_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
        endpoint_used = "assets_primary"
        
        if data and data.get('code') == 0:
            response_data = data.get('data', {})
            if isinstance(response_data, dict) and 'data' in response_data:
                nfts = response_data['data']
            else:
                nfts = response_data if isinstance(response_data, list) else []
            
            print(f"📦 Assets returned {len(nfts)} NFTs")
            
            # Apply strict contract filtering for assets
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
            
            # FOR PRICE SORTING: Try to get price data from listings ONLY if we have valid NFTs
            if sort_by in ['price_asc', 'price_desc'] and len(nfts) > 0:
                print(f"💰 Trying to enrich with price data from listings")
                
                # Get token IDs from our valid NFTs
                valid_token_ids = {nft.get('tokenId') for nft in nfts if nft.get('tokenId')}
                print(f"🏷️ Looking for prices for token IDs: {list(valid_token_ids)[:5]}...")
                
                # Try listings to get price data
                listings_data = make_fresh_okx_request('/api/v5/mktplace/nft/markets/listings', base_params, contract_address)
                
                if listings_data and listings_data.get('code') == 0:
                    response_data_listings = listings_data.get('data', {})
                    if isinstance(response_data_listings, dict) and 'data' in response_data_listings:
                        listings_nfts = response_data_listings['data']
                    else:
                        listings_nfts = response_data_listings if isinstance(response_data_listings, list) else []
                    
                    print(f"💰 Listings returned {len(listings_nfts)} entries")
                    
                    # Create price lookup ONLY for our valid token IDs
                    price_lookup = {}
                    price_matches = 0
                    
                    for listing in listings_nfts:
                        listing_token_id = listing.get('tokenId')
                        listing_price = listing.get('price') or listing.get('listingPrice')
                        
                        # ONLY use price if token ID matches our valid NFTs
                        if (listing_token_id and 
                            str(listing_token_id) in valid_token_ids and 
                            listing_price):
                            price_lookup[str(listing_token_id)] = listing_price
                            price_matches += 1
                    
                    print(f"💰 Found {price_matches} price matches for our NFTs")
                    
                    # Enrich our NFTs with prices
                    for nft in nfts:
                        token_id = nft.get('tokenId')
                        if token_id and str(token_id) in price_lookup:
                            nft['price'] = price_lookup[str(token_id)]
                            nft['priceSource'] = 'listings_matched'
                        else:
                            nft['priceSource'] = 'assets_only'
        
        if not data or data.get('code') != 0 or len(nfts) == 0:
            # Enhanced error message explaining the OKX listings bug
            error_msg = "Could not get NFTs from OKX"
            if data and data.get('code') != 0:
                error_msg = f"OKX API error: {data.get('code')} - {data.get('msg', 'Unknown error')}"
            elif len(nfts) == 0:
                error_msg = "No NFTs found - contract may not exist or have no NFTs on this chain"
            
            return jsonify({
                "success": False,
                "error": error_msg,
                "contract_address": contract_address,
                "endpoint_used": endpoint_used,
                "request_id": request_id,
                "okx_bug_info": {
                    "listings_endpoint_broken": True,
                    "explanation": "OKX listings endpoint ignores contractAddress parameter and returns general pool",
                    "workaround": "Using assets endpoint + price enrichment from listings",
                    "recommendation": "Use assets endpoint for reliable contract-specific data"
                },
                "contract_validation": {
                    "format_valid": True,
                    "exists_on_okx": False,
                    "possible_reasons": [
                        "Contract address does not exist",
                        "Contract has no NFTs on Taiko chain",
                        "Contract not indexed by OKX assets endpoint",
                        "Typing error in contract address"
                    ]
                },
                "debug": {
                    "okx_code": data.get('code') if data else 'no_response',
                    "okx_message": data.get('msg') if data else 'no_response',
                    "nfts_returned": len(nfts),
                    "sort_requested": sort_by,
                    "nuclear_fresh_request": True,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "suggestions": [
                    "Verify the contract address is correct",
                    "Check if contract exists on Taiko blockchain explorer",
                    "Try known working contracts: /api/contracts",
                    "Contract might not have any NFTs minted"
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
                    'priceSource': nft.get('priceSource', 'assets_only'),
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
            "okx_bug_workaround": {
                "listings_endpoint_broken": True,
                "explanation": "OKX listings endpoint ignores contractAddress and returns general pool",
                "solution": "Using assets endpoint + selective price enrichment",
                "price_matching": sort_by in ['price_asc', 'price_desc']
            },
            "debug": {
                "total_from_assets": len(nfts),
                "final_processed": len(processed_nfts),
                "with_prices": sum(1 for nft in processed_nfts if nft.get('price')),
                "price_sources": {
                    "listings_matched": sum(1 for nft in processed_nfts if nft.get('priceSource') == 'listings_matched'),
                    "assets_only": sum(1 for nft in processed_nfts if nft.get('priceSource') == 'assets_only')
                },
                "sorting_applied": sort_by in ['price_asc', 'price_desc'],
                "strategy": "assets_primary_with_price_enrichment",
                "contract_filtering": "strict_assets_only"
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
