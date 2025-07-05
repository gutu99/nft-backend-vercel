#!/usr/bin/env python3
"""
OKX NFT Backend API Server - VERCEL DEPLOYMENT
🔥 12 parallel blockchain requests + FIXED price conversion + OKX Purchase Integration
⚡ Maximum speed with correct price display + Real NFT buying functionality
🚨 ZERO hardcoded contracts - contract address OBLIGATORIU în toate cererile
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import hmac
import hashlib
import base64
import time
import random
from datetime import datetime
import json
import os
import logging
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from decimal import Decimal, getcontext
import re

# Setup logging pentru Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set decimal precision for accurate price calculations
getcontext().prec = 50

# Create Flask app
app = Flask(__name__)
CORS(app)

# Taiko Network Configuration
TAIKO_RPC = "https://rpc.ankr.com/taiko"
TAIKO_CHAIN_ID = 167000
TAIKO_AGGREGATOR_CONTRACT = "0xa7fd99748ce527eadc0bdac60cba8a4ef4090f7c"

# Initialize Web3 with error handling for Vercel
try:
    w3 = Web3(Web3.HTTPProvider(TAIKO_RPC))
    WEB3_CONNECTED = w3.is_connected()
    logger.info(f"Web3 connection: {WEB3_CONNECTED}")
except Exception as e:
    logger.warning(f"Web3 connection failed: {e}")
    w3 = None
    WEB3_CONNECTED = False

# Smart Contract ABIs
ERC721_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

ERC1155_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "id", "type": "uint256"}],
        "name": "uri",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

# OKX API Configuration - FOLOSEȘTE ENVIRONMENT VARIABLES pe Vercel
class OKXConfig:
    API_KEY = os.getenv('OKX_API_KEY', '0321b6d3-385f-428e-9516-d3f1cb013f99')
    SECRET_KEY = os.getenv('OKX_SECRET_KEY', '6C366DF95B6F365B73483A63339E0F27')
    PASSPHRASE = os.getenv('OKX_PASSPHRASE', '462230Gutu99!')
    BASE_URL = 'https://www.okx.com'
    WEB3_BASE_URL = 'https://web3.okx.com'

def validate_contract_address(address):
    """Validează strict adresa contractului - OBLIGATORIU"""
    if not address:
        return False, "Adresa contractului este OBLIGATORIE"
    
    if not isinstance(address, str):
        return False, "Adresa contractului trebuie să fie string"
    
    address = address.strip()
    
    if not address.startswith('0x'):
        return False, "Adresa contractului trebuie să înceapă cu 0x"
    
    if len(address) != 42:
        return False, "Adresa contractului trebuie să aibă 42 de caractere"
    
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return False, "Adresa contractului conține caractere invalide"
    
    return True, address.lower()

def get_contract_from_request():
    """Extrage și validează adresa contractului din request - OBLIGATORIU"""
    contract_address = None
    
    if request.method == 'GET':
        contract_address = request.args.get('contract') or request.args.get('contract_address')
    
    elif request.method == 'POST':
        data = request.get_json()
        if data:
            contract_address = data.get('contract') or data.get('contract_address')
    
    if not contract_address and hasattr(request, 'view_args') and request.view_args:
        contract_address = request.view_args.get('contract_address')
    
    if not contract_address:
        return None, "Contract address este OBLIGATORIU. Specifică 'contract' sau 'contract_address' în request."
    
    return validate_contract_address(contract_address)

class HyperFastMetadataFetcher:
    """Hyper-fast parallel metadata fetcher - optimizat pentru Vercel"""
    
    @staticmethod
    def fix_ipfs_link(url):
        """Fix IPFS links"""
        if not url:
            return url
        if url.startswith("ipfs://"):
            return url.replace("ipfs://", "https://cloudflare-ipfs.com/ipfs/")
        if "taikonfts.4everland.link/ipfs/" in url:
            return url.replace("https://taikonfts.4everland.link/ipfs/", "https://ipfs.io/ipfs/")
        return url
    
    @staticmethod
    def fetch_json_hyper_fast(url, timeout=3):
        """Hyper-fast JSON fetcher optimizat pentru Vercel"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    @classmethod
    def get_single_token_metadata(cls, contract_address, token_id):
        """Get metadata for a single token - optimizat pentru Vercel"""
        if not w3 or not WEB3_CONNECTED:
            return None
            
        try:
            checksum_address = Web3.to_checksum_address(contract_address)
            
            try:
                contract = w3.eth.contract(address=checksum_address, abi=ERC721_ABI)
                uri = contract.functions.tokenURI(int(token_id)).call()
                contract_type = 'ERC-721'
            except:
                try:
                    contract = w3.eth.contract(address=checksum_address, abi=ERC1155_ABI)
                    uri = contract.functions.uri(int(token_id)).call()
                    uri = uri.replace("{id}", format(int(token_id), '064x'))
                    contract_type = 'ERC-1155'
                except:
                    return None
            
            if not uri:
                return None
            
            metadata_url = cls.fix_ipfs_link(uri)
            metadata = cls.fetch_json_hyper_fast(metadata_url, timeout=3)
            
            if metadata:
                if 'image' in metadata:
                    metadata['image'] = cls.fix_ipfs_link(metadata['image'])
                
                result = {
                    'tokenId': str(token_id),
                    'name': metadata.get('name', f"NFT #{token_id}"),
                    'description': metadata.get('description', f'NFT #{token_id}'),
                    'image': metadata.get('image', ''),
                    'attributes': metadata.get('attributes', []),
                    'contractType': contract_type,
                    'metadataUri': metadata_url,
                    'metadataSource': 'blockchain_vercel',
                    'metadataFetched': True
                }
                
                return result
            
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching NFT #{token_id}: {e}")
            return None
    
    @classmethod
    def get_metadata_hyper_parallel(cls, nfts_list, contract_address, max_workers=8):
        """Get metadata - reducând workers pentru Vercel limits"""
        if not nfts_list or not WEB3_CONNECTED:
            return nfts_list
        
        start_time = time.time()
        metadata_tasks = []
        for nft in nfts_list:
            token_id = nft.get('tokenId') or nft.get('id')
            if token_id:
                metadata_tasks.append((nft, token_id))
        
        metadata_by_token = {}
        
        # Reduced workers pentru Vercel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_token = {
                executor.submit(cls.get_single_token_metadata, contract_address, token_id): (nft, token_id)
                for nft, token_id in metadata_tasks
            }
            
            completed_count = 0
            for future in as_completed(future_to_token):
                nft, token_id = future_to_token[future]
                try:
                    metadata = future.result(timeout=6)
                    if metadata:
                        metadata_by_token[str(token_id)] = metadata
                        completed_count += 1
                except Exception as e:
                    logger.error(f"Task failed for NFT #{token_id}: {e}")
        
        enriched_nfts = []
        for nft in nfts_list:
            token_id = str(nft.get('tokenId') or nft.get('id') or '')
            
            if token_id in metadata_by_token:
                metadata = metadata_by_token[token_id]
                enriched_nft = {**nft, **metadata}
                enriched_nfts.append(enriched_nft)
            else:
                fallback_nft = {
                    **nft,
                    'name': nft.get('name') or f"NFT #{token_id}",
                    'description': nft.get('description') or f"NFT #{token_id}",
                    'image': nft.get('image') or nft.get('imageUrl') or '',
                    'attributes': nft.get('attributes', []),
                    'metadataSource': 'okx_only',
                    'metadataFetched': False
                }
                enriched_nfts.append(fallback_nft)
        
        fetch_time = time.time() - start_time
        success_rate = (completed_count / len(metadata_tasks)) * 100 if metadata_tasks else 0
        
        logger.info(f"Vercel metadata completed: {completed_count}/{len(metadata_tasks)} NFTs in {fetch_time:.1f}s ({success_rate:.1f}% success)")
        
        return enriched_nfts

class OKXClient:
    def __init__(self):
        self.config = OKXConfig()
        self.last_request_time = 0
        self.min_delay = 2  # Reduced pentru Vercel
    
    def _wait_for_rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last + random.uniform(0.5, 1)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _create_signature(self, timestamp, method, request_path, body='', query_string=''):
        try:
            if query_string:
                prehash = f'{timestamp}{method}{request_path}?{query_string}{body}'
            else:
                prehash = f'{timestamp}{method}{request_path}{body}'
            
            signature = base64.b64encode(
                hmac.new(
                    self.config.SECRET_KEY.encode('utf-8'),
                    prehash.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
            
            return signature
        except Exception as e:
            logger.error(f"Error creating signature: {e}")
            return ""
    
    def _get_headers(self, method, request_path, body='', query_string=''):
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        signature = self._create_signature(timestamp, method, request_path, body, query_string)
        
        return {
            'OK-ACCESS-KEY': self.config.API_KEY,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.config.PASSPHRASE,
            'Content-Type': 'application/json'
        }

    def _make_request(self, endpoint, params=None, method='GET', data=None, use_web3_url=False):
        try:
            self._wait_for_rate_limit()
            
            query_string = ''
            if params:
                query_string = '&'.join([f"{k}={v}" for k, v in params.items() if v is not None])
            
            body = ''
            if data and method == 'POST':
                body = json.dumps(data)
            
            headers = self._get_headers(method, endpoint, body, query_string)
            
            base_url = self.config.WEB3_BASE_URL if use_web3_url else self.config.BASE_URL
            url = f"{base_url}{endpoint}"
            if query_string:
                url += f"?{query_string}"
            
            # Reduced timeout pentru Vercel
            timeout = 20
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                response = requests.post(url, headers=headers, data=body, timeout=timeout)
                
            if response.status_code == 200:
                data = response.json()
                return data
            elif response.status_code == 429:
                time.sleep(5)
                return None
            else:
                logger.error(f"HTTP Error: {response.status_code}")
                return None
            
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None

    def get_nft_assets(self, chain, contract_address, limit=50):
        """Get NFT assets"""
        params = {
            'chain': chain,
            'contractAddress': contract_address,
            'limit': str(limit)
        }
        return self._make_request('/api/v5/mktplace/nft/asset/list', params, use_web3_url=True)
    
    def get_nft_listings(self, chain, contract_address, limit=50, sort_by=None, cursor=None):
        """Get NFT listings with sorting"""
        params = {
            'chain': chain,
            'contractAddress': contract_address,
            'limit': str(limit)
        }
        
        if cursor:
            params['cursor'] = cursor
        
        if sort_by:
            sort_mapping = {
                'price_asc': 'priceAsc',
                'price_desc': 'priceDesc',
                'listing_time_desc': 'listingTimeDesc',
                'listing_time_asc': 'listingTimeAsc'
            }
            
            if sort_by in sort_mapping:
                params['sort'] = sort_mapping[sort_by]
        
        return self._make_request('/api/v5/mktplace/nft/markets/listings', params, use_web3_url=True)

    def buy_nft(self, buy_request):
        """Execute NFT purchase through OKX"""
        buy_endpoints = [
            '/api/v5/waas/nft/market/take-orders',
            '/api/v5/mktplace/nft/orders/buy',
            '/api/v5/mktplace/nft/markets/buy'
        ]
        
        for endpoint in buy_endpoints:
            try:
                use_web3 = True if 'waas' in endpoint else False
                response = self._make_request(endpoint, method='POST', data=buy_request, use_web3_url=use_web3)
                
                if response:
                    if (response.get('code') == '0' or response.get('code') == 0 or 
                        response.get('success') == True or 'data' in response):
                        return {'success': True, 'data': response.get('data', {}), 'response': response}
                        
            except Exception as e:
                continue
        
        return {'success': False, 'error': 'All OKX buy endpoints failed'}

# Initialize clients
okx_client = OKXClient()
metadata_fetcher = HyperFastMetadataFetcher()

def convert_price_to_float_fixed(price_str):
    """FIXED price conversion"""
    if not price_str:
        return float('inf')
    
    try:
        if isinstance(price_str, (int, float)):
            price_value = float(price_str)
        else:
            clean_price = str(price_str).replace(',', '').strip()
            if not clean_price or clean_price == '0':
                return float('inf')
            price_value = float(clean_price)
        
        if price_value <= 0:
            return float('inf')
        
        if price_value > 1e10:
            eth_value = price_value / 1e18
            return eth_value
        elif 0.000001 <= price_value <= 1000000:
            return price_value
        elif price_value < 0.000001:
            potential_eth = price_value * 1e18
            if 0.001 <= potential_eth <= 1000:
                return potential_eth
            else:
                return price_value
        else:
            return price_value
            
    except (ValueError, TypeError, OverflowError) as e:
        return float('inf')

def format_price_smart(price_value):
    """Smart price formatting"""
    if not price_value or price_value == float('inf') or price_value <= 0:
        return None
    
    try:
        decimal_price = Decimal(str(price_value))
        
        if decimal_price < Decimal('0.000001'):
            return f"{decimal_price:.10f}".rstrip('0').rstrip('.')
        elif decimal_price < Decimal('0.001'):
            return f"{decimal_price:.8f}".rstrip('0').rstrip('.')
        elif decimal_price < Decimal('1'):
            return f"{decimal_price:.6f}".rstrip('0').rstrip('.')
        elif decimal_price < Decimal('1000'):
            return f"{decimal_price:.4f}".rstrip('0').rstrip('.')
        else:
            return f"{decimal_price:.2f}"
            
    except Exception as e:
        return str(price_value)

# ============================================================================
# ROUTES - VERCEL COMPATIBLE
# ============================================================================

@app.route('/')
@app.route('/api')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "OKX NFT Backend API - VERCEL DEPLOYMENT",
        "version": "11.0.0-VERCEL-READY",
        "timestamp": datetime.utcnow().isoformat(),
        "deployment": "Vercel Serverless Functions",
        "features": [
            "🚀 Deployed pe Vercel",
            "⚡ Serverless functions",
            "🔥 Environment variables pentru API keys",
            "🎯 Optimizat pentru timeout limits",
            "💰 FIXED price conversion",
            "🛒 OKX WaaS API integration"
        ],
        "blockchain_info": {
            "network": "Taiko Mainnet",
            "web3_connected": WEB3_CONNECTED,
            "parallel_workers": 8
        }
    })

@app.route('/api/collection/<contract_address>/stats')
def get_collection_stats(contract_address):
    """Get collection statistics"""
    try:
        is_valid, result = validate_contract_address(contract_address)
        if not is_valid:
            return jsonify({'success': False, 'error': result}), 400
        
        contract_address = result
        data = okx_client.get_nft_assets('taiko', contract_address, 100)
        
        if data and data.get('code') == 0:
            response_data = data.get('data', {})
            if isinstance(response_data, dict) and 'data' in response_data:
                sample_nfts = response_data['data']
            else:
                sample_nfts = response_data if isinstance(response_data, list) else []
            
            total_sample = len(sample_nfts)
            listed_nfts = [nft for nft in sample_nfts if nft.get('price')]
            listed_count = len(listed_nfts)
            
            prices = []
            for nft in listed_nfts:
                price = nft.get('price')
                if price:
                    numeric_price = convert_price_to_float_fixed(price)
                    if numeric_price != float('inf'):
                        prices.append(numeric_price)
            
            floor_price = min(prices) if prices else None
            average_price = sum(prices) / len(prices) if prices else None
            listing_percentage = (listed_count / total_sample * 100) if total_sample > 0 else 0
            
            stats = {
                "contract_address": contract_address,
                "total_supply": total_sample,
                "listed_count": listed_count,
                "floor_price": floor_price,
                "average_price": average_price,
                "listing_percentage": listing_percentage,
                "sample_size": total_sample
            }
            
            return jsonify({
                "success": True,
                "stats": stats,
                "contract_address": contract_address,
                "timestamp": datetime.utcnow().isoformat(),
                "deployment": "vercel"
            })
        else:
            return jsonify({
                "success": False,
                "error": "No data available for this collection"
            }), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/nfts/<contract_address>')
def get_nfts_vercel_optimized(contract_address):
    """Get NFTs - optimizat pentru Vercel"""
    try:
        start_time = time.time()
        
        is_valid, result = validate_contract_address(contract_address)
        if not is_valid:
            return jsonify({'success': False, 'error': result}), 400
        
        contract_address = result
        
        sort_by = request.args.get('sort_by', None)
        limit = int(request.args.get('limit', 12))
        page = int(request.args.get('page', 1))
        cursor = request.args.get('cursor', None)
        fetch_metadata = request.args.get('fetch_metadata', 'true').lower() == 'true'
        
        if sort_by and sort_by in ['price_asc', 'price_desc', 'listing_time_desc', 'listing_time_asc']:
            fetch_limit = max(limit * page + 24, 60)
            data = okx_client.get_nft_listings('taiko', contract_address, fetch_limit, sort_by, cursor)
            
            if data and data.get('code') == 0:
                response_data = data.get('data', {})
                if isinstance(response_data, dict) and 'data' in response_data:
                    sorted_nfts = response_data['data']
                    next_cursor = response_data.get('cursor')
                else:
                    sorted_nfts = response_data if isinstance(response_data, list) else []
                    next_cursor = None
                
                start_index = (page - 1) * limit
                end_index = start_index + limit
                page_nfts = sorted_nfts[start_index:end_index]
                
                if fetch_metadata and page_nfts:
                    enriched_page_nfts = metadata_fetcher.get_metadata_hyper_parallel(
                        page_nfts, contract_address, max_workers=8
                    )
                else:
                    enriched_page_nfts = page_nfts
                
                processed_nfts = []
                for i, nft in enumerate(enriched_page_nfts):
                    try:
                        token_id = nft.get('tokenId') or nft.get('id') or str(start_index + i + 1)
                        name = nft.get('name') or f"NFT #{token_id}"
                        image_url = nft.get('image') or nft.get('imageUrl') or ''
                        description = nft.get('description') or f'NFT #{token_id}'
                        attributes = nft.get('attributes', [])
                        price = nft.get('price')
                        currency = nft.get('currency') or 'ETH'
                        order_id = nft.get('orderId') or nft.get('id')
                        
                        display_price = None
                        numeric_price = None
                        
                        if price:
                            numeric_price = convert_price_to_float_fixed(price)
                            if numeric_price != float('inf'):
                                display_price = format_price_smart(numeric_price)
                        
                        status = 'listed' if price and display_price else 'unlisted'
                        
                        processed_nft = {
                            'id': f"{contract_address}_{token_id}",
                            'name': name,
                            'tokenId': str(token_id),
                            'image': image_url,
                            'description': description,
                            'attributes': attributes,
                            'price': display_price,
                            'priceRaw': price,
                            'priceNumeric': numeric_price if numeric_price != float('inf') else None,
                            'currency': currency,
                            'status': status,
                            'orderId': order_id,
                            'listingTime': nft.get('listingTime'),
                            'seller': nft.get('seller') or nft.get('maker'),
                            'contractVerified': True,
                            'sortedBy': sort_by,
                            'source': 'vercel_okx_sorted',
                            'metadataSource': nft.get('metadataSource', 'okx_only'),
                            'metadataFetched': nft.get('metadataFetched', False),
                            'contractType': nft.get('contractType')
                        }
                        
                        processed_nfts.append(processed_nft)
                        
                    except Exception as e:
                        continue
                
                has_more = end_index < len(sorted_nfts) or bool(next_cursor)
                total_pages = (len(sorted_nfts) + limit - 1) // limit
                loading_time = time.time() - start_time
                
                enriched_count = len([n for n in enriched_page_nfts if n.get('metadataFetched')])
                
                return jsonify({
                    "success": True,
                    "data": processed_nfts,
                    "count": len(processed_nfts),
                    "page": page,
                    "limit": limit,
                    "has_more": has_more,
                    "next_cursor": next_cursor,
                    "total_available": len(sorted_nfts),
                    "total_pages": total_pages,
                    "sort_by": sort_by,
                    "sorting_method": "vercel_okx_server_side",
                    "metadata_enriched": fetch_metadata,
                    "enrichment_count": enriched_count,
                    "enrichment_rate": f"{(enriched_count/len(page_nfts)*100):.1f}%" if page_nfts else "0%",
                    "parallel_workers": 8,
                    "web3_connected": WEB3_CONNECTED,
                    "contract_address": contract_address,
                    "loading_time_seconds": round(loading_time, 1),
                    "deployment": "vercel",
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        else:
            # No sorting path
            fetch_limit = limit * page + 24
            data = okx_client.get_nft_assets('taiko', contract_address, fetch_limit)
            
            if data and data.get('code') == 0:
                response_data = data.get('data', {})
                if isinstance(response_data, dict) and 'data' in response_data:
                    all_nfts = response_data['data']
                else:
                    all_nfts = response_data if isinstance(response_data, list) else []
                
                start_index = (page - 1) * limit
                end_index = start_index + limit
                page_nfts = all_nfts[start_index:end_index]
                
                if fetch_metadata and page_nfts:
                    enriched_page_nfts = metadata_fetcher.get_metadata_hyper_parallel(
                        page_nfts, contract_address, max_workers=8
                    )
                else:
                    enriched_page_nfts = page_nfts
                
                processed_nfts = []
                for i, nft in enumerate(enriched_page_nfts):
                    try:
                        token_id = nft.get('tokenId') or nft.get('id') or str(start_index + i + 1)
                        name = nft.get('name') or f"NFT #{token_id}"
                        image_url = nft.get('image') or nft.get('imageUrl') or ''
                        description = nft.get('description') or f'NFT #{token_id}'
                        attributes = nft.get('attributes', [])
                        price = nft.get('price')
                        currency = nft.get('currency') or 'ETH'
                        order_id = nft.get('orderId') or nft.get('id')
                        
                        display_price = None
                        if price:
                            numeric_price = convert_price_to_float_fixed(price)
                            if numeric_price != float('inf'):
                                display_price = format_price_smart(numeric_price)
                        
                        status = 'listed' if price and display_price else 'unlisted'
                        
                        processed_nft = {
                            'id': f"{contract_address}_{token_id}",
                            'name': name,
                            'tokenId': str(token_id),
                            'image': image_url,
                            'description': description,
                            'attributes': attributes,
                            'price': display_price,
                            'currency': currency,
                            'status': status,
                            'orderId': order_id,
                            'contractVerified': True,
                            'sortedBy': 'none',
                            'source': 'vercel_assets',
                            'metadataSource': nft.get('metadataSource', 'okx_only'),
                            'metadataFetched': nft.get('metadataFetched', False),
                            'contractType': nft.get('contractType')
                        }
                        
                        processed_nfts.append(processed_nft)
                        
                    except Exception as e:
                        continue
                
                has_more = end_index < len(all_nfts)
                total_pages = (len(all_nfts) + limit - 1) // limit
                loading_time = time.time() - start_time
                
                enriched_count = len([n for n in enriched_page_nfts if n.get('metadataFetched')])
                
                return jsonify({
                    "success": True,
                    "data": processed_nfts,
                    "count": len(processed_nfts),
                    "page": page,
                    "limit": limit,
                    "has_more": has_more,
                    "total_available": len(all_nfts),
                    "total_pages": total_pages,
                    "sort_by": "none",
                    "sorting_method": "vercel_none",
                    "metadata_enriched": fetch_metadata,
                    "enrichment_count": enriched_count,
                    "enrichment_rate": f"{(enriched_count/len(page_nfts)*100):.1f}%" if page_nfts else "0%",
                    "parallel_workers": 8,
                    "web3_connected": WEB3_CONNECTED,
                    "contract_address": contract_address,
                    "loading_time_seconds": round(loading_time, 1),
                    "deployment": "vercel",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "No NFT data found on OKX for this contract"
                }), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/okx/buy', methods=['POST'])
def okx_buy_proxy():
    """Proxy endpoint for OKX purchases"""
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({"success": False, "error": "No request data provided"}), 400
        
        required_fields = ['chain', 'items', 'walletAddress']
        for field in required_fields:
            if field not in request_data:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
        
        if request_data['chain'] != 'taiko':
            return jsonify({"success": False, "error": "Only Taiko chain is supported"}), 400
        
        items = request_data['items']
        if not items or not isinstance(items, list):
            return jsonify({"success": False, "error": "Items must be a non-empty list"}), 400
        
        for item in items:
            if 'orderId' not in item:
                return jsonify({"success": False, "error": "Each item must have an orderId"}), 400
        
        okx_response = okx_client.buy_nft(request_data)
        
        if okx_response and okx_response.get('success'):
            return jsonify({
                "success": True,
                "data": okx_response.get('data', {}),
                "message": "OKX purchase request successful",
                "deployment": "vercel",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            error_msg = okx_response.get('error', 'OKX API call failed') if okx_response else 'No response from OKX'
            return jsonify({
                "success": False,
                "error": error_msg,
                "debug_info": {"okx_response": okx_response},
                "deployment": "vercel",
                "timestamp": datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "deployment": "vercel",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api/test/blockchain')
def test_blockchain():
    """Test blockchain connectivity"""
    try:
        is_connected = WEB3_CONNECTED
        latest_block = None
        
        if is_connected and w3:
            try:
                latest_block = w3.eth.block_number
            except:
                latest_block = "Error fetching block"
        
        return jsonify({
            "success": True,
            "web3_connected": is_connected,
            "latest_block": latest_block,
            "rpc_url": TAIKO_RPC,
            "deployment": "vercel",
            "parallel_workers": 8,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "deployment": "vercel",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "deployment": "vercel",
        "available_endpoints": [
            "/api/nfts/<contract_address>",
            "/api/collection/<contract_address>/stats",
            "/api/okx/buy",
            "/api/test/blockchain"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "deployment": "vercel"
    }), 500

# Pentru Vercel, exportăm app-ul
app = app

if __name__ == '__main__':
    app.run(debug=True)