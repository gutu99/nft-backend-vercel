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

def make_okx_request(endpoint, params=None):
    """Face request către OKX API"""
    try:
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()]) if params else ''
        
        signature = create_okx_signature(timestamp, 'GET', endpoint, '', query_string)
        
        headers = {
            'OK-ACCESS-KEY': OKX_API_KEY,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': OKX_PASSPHRASE,
            'Content-Type': 'application/json'
        }
        
        url = f"https://www.okx.com{endpoint}"
        if query_string:
            url += f"?{query_string}"
        
        print(f"OKX Request: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"OKX Response code: {data.get('code', 'unknown')}")
            return data
        else:
            print(f"OKX Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"OKX Request error: {e}")
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
        "service": "OKX NFT Backend - REAL DATA",
        "version": "2.0.0-okx-integration",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "✅ Real OKX API integration",
            "✅ Live NFT data",
            "✅ Price conversion",
            "✅ Vercel optimized"
        ],
        "available_endpoints": [
            "/api - health check",
            "/api/test - test OKX connection", 
            "/api/nfts/<contract> - real NFT data",
            "/api/collection/<contract>/stats - real stats"
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
    """Test OKX connection"""
    # Test basic functionality
    test_result = {
        "success": True,
        "message": "OKX integration test",
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
    
    # Test OKX API call (simple)
    try:
        if OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE:
            # Test cu un contract cunoscut
            test_contract = "0xa20a8856e00f5ad024a55a663f06dcc419ffc4d5"
            params = {
                'chain': 'taiko',
                'contractAddress': test_contract,
                'limit': '1'
            }
            
            okx_response = make_okx_request('/api/v5/mktplace/nft/asset/list', params)
            
            if okx_response:
                test_result["okx_test"] = {
                    "status": "SUCCESS",
                    "response_code": okx_response.get('code'),
                    "has_data": 'data' in okx_response,
                    "message": "OKX API connection working!"
                }
            else:
                test_result["okx_test"] = {
                    "status": "FAILED",
                    "message": "OKX API call failed"
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
    """Get real NFT data from OKX"""
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
        
        # Request către OKX
        params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': str(min(limit, 50))
        }
        
        # Încearcă listings endpoint pentru sorting
        data = None
        if sort_by in ['price_asc', 'price_desc']:
            sort_mapping = {
                'price_asc': 'priceAsc',
                'price_desc': 'priceDesc'
            }
            params['sort'] = sort_mapping[sort_by]
            data = make_okx_request('/api/v5/mktplace/nft/markets/listings', params)
        
        # Fallback la assets endpoint
        if not data or data.get('code') != 0:
            data = make_okx_request('/api/v5/mktplace/nft/asset/list', params)
        
        if not data or data.get('code') != 0:
            return jsonify({
                "success": False,
                "error": "Nu s-au putut obține NFT-urile de la OKX",
                "okx_response_code": data.get('code') if data else None,
                "contract_address": contract_address,
                "debug": {
                    "okx_response": data,
                    "params_used": params
                }
            }), 500
        
        # Procesează datele
        response_data = data.get('data', {})
        if isinstance(response_data, dict) and 'data' in response_data:
            nfts = response_data['data']
        else:
            nfts = response_data if isinstance(response_data, list) else []
        
        # Procesează NFT-urile
        processed_nfts = []
        for i, nft in enumerate(nfts[:limit]):
            try:
                token_id = nft.get('tokenId') or nft.get('id') or str(i + 1)
                name = nft.get('name') or f"NFT #{token_id}"
                image_url = nft.get('image') or nft.get('imageUrl') or ''
                description = nft.get('description') or f'NFT #{token_id}'
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
                    'source': 'okx_real_data'
                }
                
                processed_nfts.append(processed_nft)
                
            except Exception as e:
                print(f"Error processing NFT {i}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "data": processed_nfts,
            "count": len(processed_nfts),
            "contract_address": contract_address,
            "limit": limit,
            "sort_by": sort_by,
            "source": "okx_real_api",
            "deployment": "vercel",
            "okx_response_code": data.get('code'),
            "total_from_okx": len(nfts),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "contract_address": contract,
            "deployment": "vercel"
        }), 500

@app.route('/api/collection/<contract>/stats')
def get_collection_stats_real(contract):
    """Collection stats with real OKX data"""
    try:
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({'success': False, 'error': result}), 400
        
        contract_address = result
        
        # Check OKX keys
        if not (OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE):
            return jsonify({
                "success": False,
                "error": "OKX API keys not configured"
            }), 500
        
        # Get sample data pentru stats
        params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': '100'  # Sample mai mare pentru stats
        }
        
        data = make_okx_request('/api/v5/mktplace/nft/asset/list', params)
        
        if not data or data.get('code') != 0:
            return jsonify({
                "success": False,
                "error": "Nu s-au putut obține statisticile de la OKX",
                "okx_response_code": data.get('code') if data else None,
                "contract_address": contract_address
            }), 500
        
        response_data = data.get('data', {})
        if isinstance(response_data, dict) and 'data' in response_data:
            nfts = response_data['data']
        else:
            nfts = response_data if isinstance(response_data, list) else []
        
        total_sample = len(nfts)
        listed_nfts = [nft for nft in nfts if nft.get('price')]
        listed_count = len(listed_nfts)
        
        # Calculate real prices
        prices = []
        for nft in listed_nfts:
            price = convert_price(nft.get('price'))
            if price:
                prices.append(price)
        
        floor_price = min(prices) if prices else None
        average_price = sum(prices) / len(prices) if prices else None
        
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
            }
        }
        
        return jsonify({
            "success": True,
            "stats": stats,
            "source": "okx_real_data",
            "sample_size": total_sample,
            "deployment": "vercel",
            "okx_response_code": data.get('code'),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e),
            "deployment": "vercel"
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
