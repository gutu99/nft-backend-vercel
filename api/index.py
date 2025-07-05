from flask import Flask, jsonify, request
import requests
import hmac
import hashlib
import base64
import json
import os
from datetime import datetime
import re

# Create Flask app
app = Flask(__name__)

# Enable CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
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

def create_okx_signature(timestamp, method, request_path, body='', query_string=''):
    """Creează semnătura OKX"""
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
    """Face request FRESH către OKX API pentru fiecare contract"""
    try:
        # FRESH timestamp pentru fiecare cerere
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()]) if params else ''
        
        # FRESH signature pentru fiecare cerere
        signature = create_okx_signature(timestamp, 'GET', endpoint, '', query_string)
        
        headers = {
            'OK-ACCESS-KEY': OKX_API_KEY,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',  # FORCE NO CACHE
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        url = f"https://www.okx.com{endpoint}"
        if query_string:
            url += f"?{query_string}"
        
        print(f"🔄 FRESH OKX Request for contract {contract_address}: {url}")
        print(f"📝 Params: {params}")
        
        # FORCE FRESH REQUEST - no session reuse
        response = requests.get(url, headers=headers, timeout=10, stream=False)
        
        if response.status_code == 200:
            data = response.json()
            response_code = data.get('code', 'unknown')
            
            # Debug info pentru fiecare contract
            if isinstance(data.get('data'), dict) and 'data' in data['data']:
                nft_count = len(data['data']['data'])
            elif isinstance(data.get('data'), list):
                nft_count = len(data['data'])
            else:
                nft_count = 0
                
            print(f"✅ OKX Response for {contract_address}: code={response_code}, NFTs={nft_count}")
            
            # Verifică dacă primim date reale sau goale
            if nft_count == 0:
                print(f"⚠️ No NFTs found for contract {contract_address}")
            
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
        "service": "OKX NFT Backend - FRESH DATA REQUESTS",
        "version": "2.1.0-fresh-requests",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "✅ FRESH OKX API requests pentru fiecare contract",
            "✅ No caching - date noi pentru fiecare cerere",
            "✅ Live NFT data specific contractelor",
            "✅ Price conversion and formatting",
            "✅ Detailed logging pentru debugging",
            "✅ Contract-specific responses"
        ],
        "fixes": [
            "🔧 FIXED: Nu mai cache-ază datele între contracte",
            "🔧 FIXED: Cereri fresh pentru fiecare contract",
            "🔧 FIXED: Signature și timestamp nou pentru fiecare request",
            "🔧 FIXED: Headers no-cache pentru forțarea fresh data"
        ],
        "available_endpoints": [
            "/api - health check cu info OKX keys",
            "/api/test - test FRESH OKX connection", 
            "/api/nfts/<contract> - FRESH NFT data pentru contract specific",
            "/api/collection/<contract>/stats - FRESH stats pentru contract specific"
        ]
    })

@app.route('/api')
def api():
    return jsonify({
        "status": "healthy",
        "service": "OKX NFT Backend API",
        "version": "2.0.0-real-data",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat(),
        "okx_integration": "ACTIVE",
        "environment": {
            "has_okx_api_key": bool(OKX_API_KEY),
            "has_okx_secret": bool(OKX_SECRET_KEY),
            "has_okx_passphrase": bool(OKX_PASSPHRASE),
            "keys_ready": bool(OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE)
        }
    })

@app.route('/api/test')
def test():
    """Test OKX connection with FRESH data"""
    # Test basic functionality
    test_result = {
        "success": True,
        "message": "OKX integration test - FRESH REQUEST",
        "environment": {
            "flask_working": True,
            "vercel_deployment": True,
            "routing": "FIXED",
            "okx_keys": {
                "api_key": bool(OKX_API_KEY),
                "secret_key": bool(OKX_SECRET_KEY),
                "passphrase": bool(OKX_PASSPHRASE)
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Test OKX API call cu FRESH REQUEST
    try:
        if OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE:
            # Test cu un contract cunoscut - FRESH REQUEST
            test_contract = "0xa20a8856e00f5ad024a55a663f06dcc419ffc4d5"
            params = {
                'chain': 'taiko',
                'contractAddress': test_contract,
                'limit': '3'  # Mic pentru test
            }
            
            print(f"🧪 Testing FRESH OKX request for: {test_contract}")
            okx_response = make_okx_request('/api/v5/mktplace/nft/asset/list', params, test_contract)
            
            if okx_response:
                # Analizează răspunsul detailed
                response_data = okx_response.get('data', {})
                if isinstance(response_data, dict) and 'data' in response_data:
                    nfts = response_data['data']
                else:
                    nfts = response_data if isinstance(response_data, list) else []
                
                test_result["okx_test"] = {
                    "status": "SUCCESS",
                    "response_code": okx_response.get('code'),
                    "contract_tested": test_contract,
                    "nft_count": len(nfts),
                    "first_nft": nfts[0] if nfts else None,
                    "message": f"FRESH OKX API call successful! Found {len(nfts)} NFTs",
                    "fresh_timestamp": datetime.utcnow().isoformat()
                }
            else:
                test_result["okx_test"] = {
                    "status": "FAILED",
                    "message": "OKX API call failed - check logs",
                    "contract_tested": test_contract
                }
        else:
            test_result["okx_test"] = {
                "status": "NO_KEYS",
                "message": "OKX keys not configured"
            }
            
    except Exception as e:
        test_result["okx_test"] = {
            "status": "ERROR",
            "error": str(e)
        }
    
    return jsonify(test_result)

@app.route('/api/nfts/<contract>')
def get_nfts_real(contract):
    """Get FRESH NFT data from OKX pentru fiecare contract"""
    try:
        # Validare contract
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': result,
                'provided_address': contract
            }), 400
        
        contract_address = result
        print(f"🔄 FRESH NFT request for contract: {contract_address}")
        
        # Parametri
        limit = int(request.args.get('limit', 12))
        sort_by = request.args.get('sort_by', 'price_asc')
        
        # Check dacă avem OKX keys
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured",
                "fallback": "Using mock data",
                "contract_address": contract_address
            }), 500
        
        # FRESH REQUEST params pentru acest contract specific
        params = {
            'chain': 'taiko',
            'contractAddress': contract_address,  # SPECIFIC pentru acest contract
            'limit': str(min(limit, 50))
        }
        
        print(f"📝 Making FRESH OKX request with params: {params}")
        
        # Încearcă listings endpoint pentru sorting - FRESH REQUEST
        data = None
        endpoint_used = "none"
        
        if sort_by in ['price_asc', 'price_desc']:
            sort_mapping = {
                'price_asc': 'priceAsc',
                'price_desc': 'priceDesc'
            }
            params['sort'] = sort_mapping[sort_by]
            endpoint_used = "listings"
            data = make_okx_request('/api/v5/mktplace/nft/markets/listings', params, contract_address)
        
        # Fallback la assets endpoint - FRESH REQUEST
        if not data or data.get('code') != 0:
            # Remove sort param pentru assets endpoint
            assets_params = {k: v for k, v in params.items() if k != 'sort'}
            endpoint_used = "assets"
            data = make_okx_request('/api/v5/mktplace/nft/asset/list', assets_params, contract_address)
        
        if not data or data.get('code') != 0:
            return jsonify({
                "success": False,
                "error": "Nu s-au putut obține NFT-urile de la OKX",
                "okx_response_code": data.get('code') if data else None,
                "contract_address": contract_address,
                "endpoint_used": endpoint_used,
                "debug": {
                    "okx_response": data,
                    "params_used": params,
                    "fresh_request": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }), 500
        
        # Procesează datele FRESH
        response_data = data.get('data', {})
        if isinstance(response_data, dict) and 'data' in response_data:
            nfts = response_data['data']
        else:
            nfts = response_data if isinstance(response_data, list) else []
        
        print(f"✅ Received {len(nfts)} NFTs for contract {contract_address}")
        
        # Verifică dacă datele sunt specifice contractului
        if len(nfts) > 0:
            first_nft = nfts[0]
            print(f"📊 First NFT: {first_nft.get('name', 'No name')} - TokenID: {first_nft.get('tokenId', 'No ID')}")
        
        # Procesează NFT-urile - FRESH DATA
        processed_nfts = []
        for i, nft in enumerate(nfts[:limit]):
            try:
                token_id = nft.get('tokenId') or nft.get('id') or str(i + 1)
                name = nft.get('name') or f"NFT #{token_id}"
                image_url = nft.get('image') or nft.get('imageUrl') or ''
                description = nft.get('description') or f'NFT #{token_id} from {contract_address}'
                price = nft.get('price')
                
                # Convertește și formatează prețul
                display_price = None
                numeric_price = None
                if price:
                    numeric_price = convert_price(price)
                    if numeric_price:
                        display_price = format_price(numeric_price)
                
                processed_nft = {
                    'id': f"{contract_address}_{token_id}",
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
                    'contractAddress': contract_address,  # Explicit contract address
                    'source': 'okx_fresh_data',
                    'fresh_timestamp': datetime.utcnow().isoformat()
                }
                
                processed_nfts.append(processed_nft)
                
            except Exception as e:
                print(f"❌ Error processing NFT {i} for contract {contract_address}: {e}")
                continue
        
        print(f"🎯 Processed {len(processed_nfts)} NFTs for contract {contract_address}")
        
        return jsonify({
            "success": True,
            "data": processed_nfts,
            "count": len(processed_nfts),
            "contract_address": contract_address,
            "limit": limit,
            "sort_by": sort_by,
            "source": "okx_fresh_api",
            "deployment": "vercel",
            "okx_response_code": data.get('code'),
            "total_from_okx": len(nfts),
            "endpoint_used": endpoint_used,
            "fresh_request": True,
            "debug_info": {
                "params_sent": params,
                "nfts_received": len(nfts),
                "nfts_processed": len(processed_nfts),
                "contract_specific": True
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in get_nfts_real for contract {contract}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "contract_address": contract,
            "deployment": "vercel",
            "fresh_request": True
        }), 500

@app.route('/api/collection/<contract>/stats')
def get_collection_stats_real(contract):
    """Collection stats with FRESH OKX data pentru fiecare contract"""
    try:
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({'success': False, 'error': result}), 400
        
        contract_address = result
        print(f"📊 FRESH stats request for contract: {contract_address}")
        
        # Check OKX keys
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured"
            }), 500
        
        # FRESH REQUEST params pentru acest contract specific
        params = {
            'chain': 'taiko',
            'contractAddress': contract_address,  # SPECIFIC pentru acest contract
            'limit': '100'  # Sample mai mare pentru stats accurate
        }
        
        print(f"📝 Making FRESH stats request with params: {params}")
        
        data = make_okx_request('/api/v5/mktplace/nft/asset/list', params, contract_address)
        
        if not data or data.get('code') != 0:
            return jsonify({
                "success": False,
                "error": "Nu s-au putut obține statisticile de la OKX",
                "okx_response_code": data.get('code') if data else None,
                "contract_address": contract_address,
                "debug": {
                    "fresh_request": True,
                    "params_used": params,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }), 500
        
        response_data = data.get('data', {})
        if isinstance(response_data, dict) and 'data' in response_data:
            nfts = response_data['data']
        else:
            nfts = response_data if isinstance(response_data, list) else []
        
        print(f"📊 Received {len(nfts)} NFTs for stats calculation for {contract_address}")
        
        total_sample = len(nfts)
        listed_nfts = [nft for nft in nfts if nft.get('price')]
        listed_count = len(listed_nfts)
        
        # Calculate FRESH prices pentru acest contract
        prices = []
        for nft in listed_nfts:
            price = convert_price(nft.get('price'))
            if price:
                prices.append(price)
        
        floor_price = min(prices) if prices else None
        average_price = sum(prices) / len(prices) if prices else None
        
        # FRESH stats pentru acest contract specific
        stats = {
            "contract_address": contract_address,
            "total_supply": total_sample,
            "listed_count": listed_count,
            "floor_price": floor_price,
            "average_price": average_price,
            "listing_percentage": (listed_count / total_sample * 100) if total_sample > 0 else 0,
            "price_range": {
                "min": min(prices) if prices else None,
                "max": max(prices) if prices else None
            },
            "fresh_calculation": True,
            "calculation_timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"✅ Calculated FRESH stats for {contract_address}: {listed_count}/{total_sample} listed")
        
        return jsonify({
            "success": True,
            "stats": stats,
            "source": "okx_fresh_stats",
            "sample_size": total_sample,
            "deployment": "vercel",
            "okx_response_code": data.get('code'),
            "fresh_request": True,
            "debug_info": {
                "contract_specific": True,
                "nfts_analyzed": total_sample,
                "listed_nfts": listed_count,
                "prices_found": len(prices)
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in get_collection_stats_real for contract {contract}: {e}")
        return jsonify({
            "success": False, 
            "error": str(e),
            "deployment": "vercel",
            "fresh_request": True,
            "contract_address": contract
        }), 500

@app.route('/api/okx/buy', methods=['POST'])
def okx_buy_proxy():
    """Proxy pentru OKX purchase"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({
                "success": False,
                "error": "No request data provided"
            }), 400
        
        # Check OKX keys
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured"
            }), 500
        
        # Validate required fields
        required_fields = ['chain', 'items', 'walletAddress']
        for field in required_fields:
            if field not in request_data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # For now, return success (implement actual buying later)
        return jsonify({
            "success": True,
            "message": "Buy functionality ready - implement with WaaS API",
            "data": request_data,
            "deployment": "vercel",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "deployment": "vercel"
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
            "/api/collection/<contract>/stats",
            "/api/okx/buy"
        ],
        "example_urls": [
            "/api/nfts/0xa20a8856e00f5ad024a55a663f06dcc419ffc4d5",
            "/api/collection/0xa20a8856e00f5ad024a55a663f06dcc419ffc4d5/stats"
        ],
        "deployment": "vercel"
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
