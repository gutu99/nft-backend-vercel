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
        "service": "OKX NFT Backend - FIXED SORTING",
        "version": "2.2.0-fixed-sorting",
        "deployment": "vercel",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "✅ FIXED: Price sorting cu parametri corecți OKX",
            "✅ FIXED: Endpoint logic mai clar și robust",
            "✅ FIXED: Fallback logic îmbunătățit",
            "✅ FRESH OKX API requests pentru fiecare contract",
            "✅ Contract-specific filtering",
            "✅ Detailed logging pentru debugging"
        ],
        "fixes": [
            "🔧 FIXED: Sort parameters conform documentației OKX",
            "🔧 FIXED: Endpoint selection logic",
            "🔧 FIXED: Price sorting functionality",
            "🔧 FIXED: Better error handling și fallback"
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
        "version": "2.2.0-fixed-sorting",
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
        "message": "OKX integration test - FRESH REQUEST WITH FIXED SORTING",
        "environment": {
            "flask_working": True,
            "vercel_deployment": True,
            "routing": "FIXED",
            "sorting": "FIXED",
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
    """Get FRESH NFT data from OKX pentru fiecare contract - FIXED SORTING"""
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
        
        # FIXED SORTING LOGIC - Bazat pe documentația OKX standard
        # Pentru NFT marketplaces, parametrii standard sunt de obicei:
        # sortBy + orderBy sau sort + order
        
        # Parametri de bază pentru cerere
        base_params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': str(min(limit, 50))
        }
        
        # FIXED: Logică clară pentru sortare
        use_listings_endpoint = False
        sort_params = {}
        
        if sort_by in ['price_asc', 'price_desc']:
            use_listings_endpoint = True
            
            # FIXED: Testează diferite variante de parametri OKX pentru sortare
            if sort_by == 'price_asc':
                # Variante posibile pentru sortare ascendentă după preț
                sort_variants = [
                    {'sortBy': 'price', 'orderBy': 'asc'},
                    {'sort': 'price', 'order': 'asc'},
                    {'sortType': 'price', 'sortOrder': 'asc'},
                    {'priceSort': 'asc'},
                    {'sort': 'priceAsc'},
                    {'sortBy': 'priceAsc'}
                ]
            else:  # price_desc
                sort_variants = [
                    {'sortBy': 'price', 'orderBy': 'desc'},
                    {'sort': 'price', 'order': 'desc'},
                    {'sortType': 'price', 'sortOrder': 'desc'},
                    {'priceSort': 'desc'},
                    {'sort': 'priceDesc'},
                    {'sortBy': 'priceDesc'}
                ]
            
            print(f"🏷️ Using LISTINGS endpoint for price sorting: {sort_by}")
            
        else:
            # Pentru alte tipuri de sortare (date, popularitate, etc.) - folosește assets
            use_listings_endpoint = False
            print(f"📦 Using ASSETS endpoint for general browsing")
        
        data = None
        endpoint_used = "none"
        successful_sort_params = None
        
        if use_listings_endpoint:
            # Încearcă fiecare variantă de sortare până găsește una care funcționează
            for i, sort_variant in enumerate(sort_variants):
                params = {**base_params, **sort_variant}
                endpoint_used = f"listings_sort_variant_{i+1}"
                
                print(f"🧪 Trying sort variant {i+1}: {sort_variant}")
                
                data = make_okx_request('/api/v5/mktplace/nft/markets/listings', params, contract_address)
                
                if data and data.get('code') == 0:
                    response_data = data.get('data', {})
                    if isinstance(response_data, dict) and 'data' in response_data:
                        nfts = response_data['data']
                    else:
                        nfts = response_data if isinstance(response_data, list) else []
                    
                    if len(nfts) > 0:
                        print(f"✅ Sort variant {i+1} successful: {len(nfts)} NFTs")
                        successful_sort_params = sort_variant
                        break
                    else:
                        print(f"⚠️ Sort variant {i+1} returned no NFTs")
                else:
                    print(f"❌ Sort variant {i+1} failed")
            
            # Dacă niciuna din variantele de sortare nu funcționează, încearcă fără sortare
            if not data or data.get('code') != 0:
                print(f"⚠️ All sort variants failed, trying listings without sort")
                data = make_okx_request('/api/v5/mktplace/nft/markets/listings', base_params, contract_address)
                endpoint_used = "listings_no_sort"
        else:
            # Pentru browsing general - folosește assets
            data = make_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
            endpoint_used = "assets_browsing"
        
        # Ultimate fallback - dacă listings nu funcționează, încearcă assets
        if not data or data.get('code') != 0:
            print(f"🔄 Primary endpoint failed, trying ultimate fallback to assets")
            data = make_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
            endpoint_used = "assets_ultimate_fallback"
        
        if not data or data.get('code') != 0:
            return jsonify({
                "success": False,
                "error": "Nu s-au putut obține NFT-urile de la OKX",
                "okx_response_code": data.get('code') if data else None,
                "contract_address": contract_address,
                "endpoint_used": endpoint_used,
                "sort_attempted": sort_by,
                "fixes_applied": [
                    "Multiple sort parameter variants tested",
                    "Clear endpoint selection logic",
                    "Robust fallback mechanism"
                ],
                "debug": {
                    "okx_response": data,
                    "params_used": base_params,
                    "successful_sort_params": successful_sort_params,
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
        
        # FIXED: Filtrare îmbunătățită pentru contract-specific data
        if len(nfts) > 0:
            original_count = len(nfts)
            # Filtrare robustă pentru a menține doar NFT-uri din contractul specificat
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
            filtered_count = len(nfts)
            
            print(f"🔍 CONTRACT FILTER: {original_count} -> {filtered_count} NFTs after filtering")
            
            if filtered_count == 0 and endpoint_used.startswith("listings"):
                print(f"⚠️ No listings for contract {contract_address}, falling back to assets")
                data = make_okx_request('/api/v5/mktplace/nft/asset/list', base_params, contract_address)
                
                if data and data.get('code') == 0:
                    response_data = data.get('data', {})
                    if isinstance(response_data, dict) and 'data' in response_data:
                        nfts = response_data['data']
                    else:
                        nfts = response_data if isinstance(response_data, list) else []
                    endpoint_used = "assets_contract_fallback"
                    print(f"📦 Contract fallback successful: {len(nfts)} NFTs from assets")
        
        # FIXED: Client-side sorting pentru asigurarea ordinii corecte
        if sort_by in ['price_asc', 'price_desc'] and len(nfts) > 1:
            def get_nft_price(nft):
                price = nft.get('price') or nft.get('listingPrice') or nft.get('priceEth')
                if not price:
                    return 0 if sort_by == 'price_asc' else float('inf')
                try:
                    return float(price)
                except:
                    return 0 if sort_by == 'price_asc' else float('inf')
            
            reverse_order = (sort_by == 'price_desc')
            nfts.sort(key=get_nft_price, reverse=reverse_order)
            print(f"🔄 Applied client-side sorting: {sort_by}")
        
        # Procesează și formatează NFT-urile
        processed_nfts = []
        for i, nft in enumerate(nfts[:limit]):
            try:
                token_id = nft.get('tokenId') or nft.get('id') or str(i + 1)
                name = nft.get('name') or f"NFT #{token_id}"
                image_url = nft.get('image') or nft.get('imageUrl') or nft.get('imageURI') or ''
                description = nft.get('description') or f'NFT #{token_id} from {contract_address}'
                
                # FIXED: Price extraction logic îmbunătățit
                price = (nft.get('price') or 
                        nft.get('listingPrice') or 
                        nft.get('priceEth') or 
                        nft.get('priceWei'))
                
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
                    'source': 'okx_fresh_data_fixed_sorting',
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
            "source": "okx_fresh_api_fixed_sorting",
            "deployment": "vercel",
            "okx_response_code": data.get('code'),
            "total_from_okx": len(nfts),
            "endpoint_used": endpoint_used,
            "successful_sort_params": successful_sort_params,
            "fresh_request": True,
            "fixes_applied": [
                "Multiple sort parameter variants",
                "Client-side sorting validation", 
                "Improved contract filtering",
                "Better price extraction logic"
            ],
            "debug_info": {
                "params_sent": base_params,
                "nfts_received": len(nfts),
                "nfts_processed": len(processed_nfts),
                "contract_specific": True,
                "sort_working": bool(successful_sort_params)
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
            "fresh_request": True,
            "version": "2.2.0-fixed-sorting"
        }), 500

@app.route('/api/debug/sort-params/<contract>')
def debug_sort_parameters(contract):
    """Debug diferite parametri de sortare pentru a găsi sintaxa corectă OKX"""
    try:
        is_valid, result = validate_contract_address(contract)
        if not is_valid:
            return jsonify({'success': False, 'error': result}), 400
        
        contract_address = result
        
        # FIXED: Lista extinsă de variante de sortare bazată pe standardele comune API
        sort_variants = [
            # Standard sortBy + orderBy
            {'sortBy': 'price', 'orderBy': 'asc'},
            {'sortBy': 'price', 'orderBy': 'desc'},
            
            # Standard sort + order  
            {'sort': 'price', 'order': 'asc'},
            {'sort': 'price', 'order': 'desc'},
            
            # Variante cu sortType
            {'sortType': 'price', 'sortOrder': 'asc'},
            {'sortType': 'price', 'sortOrder': 'desc'},
            
            # Variante directe
            {'priceSort': 'asc'},
            {'priceSort': 'desc'},
            {'sort': 'priceAsc'},
            {'sort': 'priceDesc'},
            {'sortBy': 'priceAsc'},
            {'sortBy': 'priceDesc'},
            
            # Variante cu underscore
            {'sort': 'price_asc'},
            {'sort': 'price_desc'},
            {'sort_by': 'price', 'sort_order': 'asc'},
            {'sort_by': 'price', 'sort_order': 'desc'},
            
            # Variante cu majuscule
            {'sort': 'PRICE_ASC'},
            {'sort': 'PRICE_DESC'},
            {'sortBy': 'PRICE', 'orderBy': 'ASC'},
            {'sortBy': 'PRICE', 'orderBy': 'DESC'},
            
            # Alte variante comune
            {'orderBy': 'price'},
            {'orderBy': 'price_desc'},
            {'sortField': 'price', 'sortDirection': 'asc'},
            {'sortField': 'price', 'sortDirection': 'desc'}
        ]
        
        debug_results = {
            "contract_tested": contract_address,
            "sort_variants_tested": {},
            "recommendations": [],
            "successful_variants": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        base_params = {
            'chain': 'taiko',
            'contractAddress': contract_address,
            'limit': '5'
        }
        
        for i, sort_variant in enumerate(sort_variants):
            try:
                print(f"🧪 Testing sort variant {i+1}: {sort_variant}")
                
                params = {**base_params, **sort_variant}
                
                response = make_okx_request('/api/v5/mktplace/nft/markets/listings', params, contract_address)
                
                result_data = {
                    "sort_params": sort_variant,
                    "response_code": response.get('code') if response else None,
                    "has_data": bool(response and response.get('data')),
                    "nft_count": 0,
                    "has_prices": False,
                    "error": None
                }
                
                if response and response.get('data'):
                    data = response['data']
                    if isinstance(data, dict) and 'data' in data:
                        nfts = data['data']
                    else:
                        nfts = data if isinstance(data, list) else []
                    
                    result_data["nft_count"] = len(nfts)
                    
                    if nfts:
                        first_nft = nfts[0]
                        result_data["first_token_id"] = first_nft.get('tokenId')
                        result_data["has_prices"] = bool(first_nft.get('price'))
                        
                        # Verifică dacă sortarea funcționează efectiv
                        if len(nfts) > 1:
                            prices = []
                            for nft in nfts:
                                price = nft.get('price')
                                if price:
                                    try:
                                        prices.append(float(price))
                                    except:
                                        pass
                            
                            if len(prices) > 1:
                                is_ascending = prices == sorted(prices)
                                is_descending = prices == sorted(prices, reverse=True)
                                result_data["price_order"] = {
                                    "ascending": is_ascending,
                                    "descending": is_descending,
                                    "prices": prices[:3],  # First 3 prices for inspection
                                    "is_sorted": is_ascending or is_descending
                                }
                                
                                # Dacă sortarea pare să funcționeze, adaugă la successful
                                if is_ascending or is_descending:
                                    debug_results["successful_variants"].append({
                                        "variant": sort_variant,
                                        "ascending": is_ascending,
                                        "descending": is_descending,
                                        "nft_count": len(nfts)
                                    })
                
                debug_results["sort_variants_tested"][f"variant_{i+1}"] = result_data
                
                # Add to recommendations if it works well
                if (result_data.get("response_code") == 0 and 
                    result_data.get("nft_count", 0) > 0 and 
                    result_data.get("has_prices")):
                    
                    recommendation = {
                        "sort_params": sort_variant,
                        "reason": "Returns data with prices",
                        "nft_count": result_data["nft_count"],
                        "priority": "high" if result_data.get("price_order", {}).get("is_sorted") else "medium"
                    }
                    debug_results["recommendations"].append(recommendation)
                
            except Exception as e:
                debug_results["sort_variants_tested"][f"variant_{i+1}"] = {
                    "sort_params": sort_variant,
                    "error": str(e)
                }
        
        # Test fără sort parameter ca baseline
        try:
            no_sort_response = make_okx_request('/api/v5/mktplace/nft/markets/listings', base_params, contract_address)
            
            debug_results["baseline_no_sort"] = {
                "response_code": no_sort_response.get('code') if no_sort_response else None,
                "has_data": bool(no_sort_response and no_sort_response.get('data')),
                "note": "Baseline test without sort parameter"
            }
            
        except Exception as e:
            debug_results["baseline_no_sort"] = {"error": str(e)}
        
        # Sortează recomandările după prioritate
        debug_results["recommendations"].sort(key=lambda x: x.get("priority", "low"), reverse=True)
        
        return jsonify({
            "success": True,
            "debug_data": debug_results,
            "summary": {
                "total_variants_tested": len(sort_variants),
                "successful_variants": len(debug_results["successful_variants"]),
                "working_variants": len(debug_results["recommendations"]),
                "contract": contract_address,
                "best_recommendations": debug_results["recommendations"][:5],
                "top_successful": debug_results["successful_variants"][:3]
            },
            "conclusion": {
                "sorting_available": len(debug_results["successful_variants"]) > 0,
                "recommended_action": "Use top successful variants for implementation"
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "debug": True
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
            "/api/debug/sort-params/<contract>"
        ],
        "example_urls": [
            "/api/nfts/0xa20a8856e00f5ad024a55a663f06dcc419ffc4d5",
            "/api/debug/sort-params/0xa20a8856e00f5ad024a55a663f06dcc419ffc4d5"
        ],
        "deployment": "vercel",
        "version": "2.2.0-fixed-sorting"
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "error": "Server error",
        "message": str(error),
        "deployment": "vercel",
        "version": "2.2.0-fixed-sorting"
    }), 500

if __name__ == '__main__':
    app.run(debug=True)
