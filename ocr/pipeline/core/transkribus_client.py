"""
Transkribus API Client for automated PDF processing and OCR
"""
import requests
import json
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class TranskribusClient:
    """Client for interacting with Transkribus API"""
    
    def __init__(self, email: str = None, password: str = None):
        self.base_url = "https://transkribus.eu/TrpServer/rest"
        self.session = requests.Session()
        self.session_id = None
        
        # Get credentials from environment or parameters
        self.email = email or os.getenv('TRANSKRIBUS_EMAIL')
        self.password = password or os.getenv('TRANSKRIBUS_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("Transkribus credentials required. Set TRANSKRIBUS_EMAIL and TRANSKRIBUS_PASSWORD environment variables.")
    
    def login(self) -> bool:
        """Login to Transkribus and get session ID"""
        try:
            # Updated login format for current Transkribus API
            login_data = {
                'user': self.email,
                'pw': self.password
            }
            
            # Set proper headers
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data=login_data,
                headers=headers
            )
            
            logger.info(f"Login response status: {response.status_code}")
            logger.info(f"Login response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    # Try to parse JSON response first
                    response_data = response.json()
                    if 'sessionId' in response_data:
                        self.session_id = response_data['sessionId']
                        logger.info("✅ Successfully logged into Transkribus (JSON response)")
                        return True
                except:
                    # Fallback to text parsing
                    pass
                
                # Check for session ID in cookies
                for cookie in self.session.cookies:
                    if cookie.name == 'JSESSIONID':
                        self.session_id = cookie.value
                        logger.info("✅ Successfully logged into Transkribus (Cookie)")
                        return True
                
                # Check response text for session info
                session_info = response.text
                if "sessionId" in session_info or "JSESSIONID" in session_info:
                    self.session_id = session_info
                    logger.info("✅ Successfully logged into Transkribus (Text response)")
                    return True
                else:
                    logger.error(f"❌ Failed to extract session ID. Response: {session_info[:200]}")
                    return False
            else:
                logger.error(f"❌ Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
    
    def get_collections(self) -> Optional[List[Dict]]:
        """Get list of available collections"""
        try:
            response = self.session.get(
                f"{self.base_url}/collections/list",
                headers={'Cookie': f'JSESSIONID={self.session_id}'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get collections: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting collections: {e}")
            return None
    
    def get_documents_in_collection(self, collection_id: int) -> Optional[List[Dict]]:
        """Get list of documents in a collection"""
        try:
            response = self.session.get(
                f"{self.base_url}/collections/{collection_id}/list",
                headers={'Cookie': f'JSESSIONID={self.session_id}'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get documents: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return None
    
    def find_document_by_name(self, document_name: str) -> Optional[Dict]:
        """Find a document by name across all collections"""
        try:
            collections = self.get_collections()
            if not collections:
                return None
            
            for collection in collections:
                collection_id = collection.get('colId')
                if collection_id:
                    documents = self.get_documents_in_collection(collection_id)
                    if documents:
                        for doc in documents:
                            if doc.get('title', '').lower() == document_name.lower():
                                doc['collection_id'] = collection_id
                                return doc
            
            logger.warning(f"Document '{document_name}' not found in any collection")
            return None
            
        except Exception as e:
            logger.error(f"Error finding document: {e}")
            return None
    
    def get_document_text(self, collection_id: int, document_id: int) -> Optional[str]:
        """Get text from an existing document using Transkribus API"""
        debug = os.environ.get('DEBUG', '').lower() in ('1', 'true', 'yes')
        
        # Create debug directories at the start
        debug_dirs = ['debug_logs', 'debug_responses', 'debug_exports']
        for dir_name in debug_dirs:
            try:
                os.makedirs(os.path.join(os.getcwd(), dir_name), exist_ok=True)
            except Exception as e:
                logger.error(f"❌ Failed to create debug directory '{dir_name}': {str(e)}")
        
        # Create a debug log file for this operation
        debug_log = []
        
        def log_debug(message: str, level: str = 'info'):
            """Helper function to log to both console and debug log"""
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            debug_log.append(log_entry)
            
            if level == 'error':
                logger.error(message)
            elif level == 'warning':
                logger.warning(message)
            elif level == 'debug':
                if debug:
                    logger.debug(message)
            else:
                logger.info(message)
        
        # Log the start of the process with full debug info
        log_debug("\n🔍 === STARTING DOCUMENT TEXT EXTRACTION ===")
        log_debug(f"📂 Collection ID: {collection_id}")
        log_debug(f"📄 Document ID: {document_id}")
        log_debug(f"🔗 Base URL: {self.base_url}")
        
        # Save debug info to a file
        def save_debug_log():
            """Save debug log to a file"""
            try:
                debug_dir = os.path.join(os.getcwd(), 'debug_logs')
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, f"transkribus_debug_{document_id}_{int(time.time())}.log")
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(debug_log))
                log_debug(f"📝 Debug log saved to: {debug_file}", 'debug')
                
                # Also save a copy with a fixed name for easier access
                latest_file = os.path.join(debug_dir, f"latest_debug_{document_id}.log")
                with open(latest_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(debug_log))
                    
            except Exception as e:
                logger.error(f"❌ Failed to save debug log: {str(e)}")
        
        # Make sure we save the debug log when we're done
        import atexit
        atexit.register(save_debug_log)
        
        try:
            # Create session with debug logging if enabled
            session = requests.Session()
            if debug:
                import http.client
                http.client.HTTPConnection.debuglevel = 1
                
                # Configure logging for requests
                import logging
                logging.basicConfig()
                logging.getLogger().setLevel(logging.DEBUG)
                requests_log = logging.getLogger("urllib3")
                requests_log.setLevel(logging.DEBUG)
                requests_log.propagate = True
            
            headers = {
                'Cookie': f'JSESSIONID={self.session_id}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            if debug:
                logger.debug(f"Using headers: {headers}")
            
            # First verify the session is still valid
            logger.info("\n🔐 Verifying session...")
            session_valid = self.verify_session()
            logger.info(f"✅ Session valid: {session_valid}")
            
            if not session_valid:
                logger.error("❌ Session is no longer valid, please log in again")
                return None
                
            # Get collection name for better logging
            collection_name = f"Collection-{collection_id}"
            try:
                collections = self.get_collections()
                for col in collections:
                    if col['colId'] == collection_id:
                        collection_name = col['colName']
                        break
                logger.info(f"📂 Collection: {collection_name}")
            except Exception as e:
                logger.warning(f"⚠️ Could not get collection name: {str(e)}")
            
            # First get document info to find the latest transcript
            doc_url = f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}"
            logger.info(f"\n📄 Getting document info from: {doc_url}")
            
            # Add a list of all endpoints we'll try
            endpoints_to_try = [
                # Main document endpoints
                f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}",
                f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/fulldoc",
                
                # Alternative endpoints that might work
                f"{self.base_url}/TrpServer/rest/collections/{collection_id}/documents/{document_id}",
                f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/metadata",
                
                # Fallback to Swagger UI endpoint format
                f"{self.base_url}/TrpServer/rest/collections/{collection_id}/documents/{document_id}/metadata"
            ]
            
            if debug:
                logger.info("\n🔍 Will try the following document endpoints:")
                for i, endpoint in enumerate(endpoints_to_try, 1):
                    logger.info(f"  {i}. {endpoint}")
            
            doc_data = None
            last_error = None
            
            # Try each endpoint until we get a successful response
            for endpoint in endpoints_to_try:
                try:
                    logger.info(f"\n🔍 Trying endpoint: {endpoint}")
                    
                    # Add delay between retries
                    if endpoint != endpoints_to_try[0]:
                        time.sleep(1)
                    
                    # Make the request with a timeout
                    response = session.get(
                        endpoint,
                        headers=headers,
                        timeout=30,
                        allow_redirects=True
                    )
                    
                    logger.info(f"📄 Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        doc_data = response.json()
                        logger.info(f"✅ Successfully retrieved document data")
                        
                        if debug:
                            logger.debug(f"Document data keys: {list(doc_data.keys())}")
                            if 'pageList' in doc_data and 'pages' in doc_data['pageList']:
                                logger.info(f"📑 Found {len(doc_data['pageList']['pages'])} pages in document")
                            
                        # If we got valid data, break out of the retry loop
                        break
                    else:
                        logger.warning(f"⚠️ Endpoint returned status {response.status_code}")
                        if response.text:
                            logger.debug(f"Response: {response.text[:500]}...")
                        
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"⚠️ Error with endpoint {endpoint}: {last_error}")
                    if debug:
                        import traceback
                        logger.debug(traceback.format_exc())
            
            # If we couldn't get document data from any endpoint, log and return
            if not doc_data:
                logger.error("❌ Failed to retrieve document data from any endpoint")
                if last_error:
                    logger.error(f"Last error: {last_error}")
                return None
                
            try:    
                # Extract document metadata
                status = doc_data.get('status', {})
                status_code = status.get('code', 0)
                status_message = status.get('message', 'No status message')
                
                logger.info("\n📊 DOCUMENT METADATA")
                logger.info("-------------------")
                logger.info(f"Title: {doc_data.get('title', 'Untitled')}")
                logger.info(f"Status: {status_code} - {status_message}")
                logger.info(f"Created: {doc_data.get('created', 'Unknown')}")
                logger.info(f"Updated: {doc_data.get('updated', 'Unknown')}")
                logger.info(f"Pages: {doc_data.get('nrOfPages', 0)}")
                
                # Log all top-level keys for debugging
                if debug:
                    logger.debug("\n🔍 Document data keys:")
                    for key in doc_data.keys():
                        value = doc_data[key]
                        if isinstance(value, (str, int, float, bool)) or value is None:
                            logger.debug(f"  {key}: {value}")
                        elif isinstance(value, (list, dict)):
                            logger.debug(f"  {key}: {type(value).__name__} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                
                if status_code != 0:
                    logger.warning(f"⚠️ Document status indicates it may not be fully processed: {status_message}")
                
                # Get pages from document data
                pages = []
                
                # Try different possible locations for pages data with more detailed logging
                possible_page_locations = [
                    ('pageList.pages', doc_data.get('pageList', {}).get('pages', [])),
                    ('pages', doc_data.get('pages', [])),
                    ('pageList (direct)', doc_data.get('pageList', [])),
                    ('pageList.pages (alternative)', doc_data.get('pageList', {}).get('pageList', {}).get('pages', [])),
                    ('document.content.pages', doc_data.get('document', {}).get('content', {}).get('pages', []))
                ]
                
                logger.info("\n🔍 Searching for pages in document data...")
                for location, page_list in possible_page_locations:
                    if isinstance(page_list, list) and len(page_list) > 0:
                        logger.info(f"✅ Found {len(page_list)} pages in {location}")
                        pages = page_list
                        if debug:
                            logger.debug(f"First page data: {json.dumps(page_list[0], indent=2, ensure_ascii=False)[:500]}...")
                        break
                    else:
                        logger.debug(f"  No pages found in {location}")
                
                logger.info(f"\n📑 Total pages found: {len(pages)}")
                
                # If we found pages, log some details about the first few
                if pages and len(pages) > 0:
                    logger.info("\n📄 Sample page information:")
                    for i, page in enumerate(pages[:3]):  # Show first 3 pages
                        if isinstance(page, dict):
                            logger.info(f"  Page {i+1}:")
                            for key in ['pageNr', 'pageId', 'tsList', 'text', 'url']:
                                if key in page:
                                    value = page[key]
                                    if key == 'tsList' and isinstance(value, dict):
                                        logger.info(f"    {key}: {len(value.get('transcripts', []))} transcript(s)")
                                    else:
                                        logger.info(f"    {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                                
                            # If we have transcripts, log their details
                            if 'tsList' in page and isinstance(page['tsList'], dict):
                                transcripts = page['tsList'].get('transcripts', [])
                                if transcripts:
                                    logger.info(f"    Transcripts:")
                                    for t in transcripts[:3]:  # Show first 3 transcripts
                                        logger.info(f"      - ID: {t.get('tsId')}, Status: {t.get('status')}, Key: {t.get('key')}")
                                    if len(transcripts) > 3:
                                        logger.info(f"      ... and {len(transcripts) - 3} more")
                        else:
                            logger.info(f"  Page {i+1}: {str(page)[:100]}...")
                    
                    if len(pages) > 3:
                        logger.info(f"  ... and {len(pages) - 3} more pages")
                
                if not pages:
                    log_debug("⚠️ No pages found in document data, trying alternative endpoints...", 'warning')
                    
                    # Try alternative endpoints to get pages
                    pages_endpoints = [
                        {
                            'url': f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/pages",
                            'description': 'Standard pages endpoint'
                        },
                        {
                            'url': f"{self.base_url}/TrpServer/rest/collections/{collection_id}/documents/{document_id}/pages",
                            'description': 'Alternative documents/pages endpoint'
                        },
                        {
                            'url': f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/list",
                            'description': 'List endpoint'
                        },
                        {
                            'url': f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/text",
                            'description': 'Direct text endpoint'
                        },
                        {
                            'url': f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/text/plain",
                            'description': 'Plain text endpoint'
                        }
                    ]
                    
                    for endpoint_info in pages_endpoints:
                        endpoint = endpoint_info['url']
                        description = endpoint_info['description']
                        
                        try:
                            log_debug(f"🔄 Trying pages endpoint: {description} ({endpoint})", 'info')
                            response = session.get(endpoint, headers=headers, timeout=30)
                            
                            log_debug(f"Response status: {response.status_code}", 'debug')
                            
                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                    log_debug(f"Response data type: {type(data).__name__}", 'debug')
                                    
                                    if isinstance(data, dict):
                                        log_debug(f"Response keys: {list(data.keys())}", 'debug')
                                        if 'pages' in data and data['pages']:
                                            pages = data['pages']
                                            log_debug(f"✅ Found {len(pages)} pages in 'pages' key", 'info')
                                        else:
                                            log_debug("No 'pages' key found in response or it's empty", 'debug')
                                            # Try to extract pages from other potential keys
                                            for key, value in data.items():
                                                if isinstance(value, list):
                                                    log_debug(f"Found list in key: {key} with {len(value)} items", 'debug')
                                                    pages = value
                                                    log_debug(f"✅ Using {len(pages)} items from '{key}' as pages", 'info')
                                                    break
                                    elif isinstance(data, list):
                                        log_debug(f"✅ Found {len(data)} items in list response", 'info')
                                        pages = data
                                    
                                    if pages:
                                        log_debug(f"✅ Successfully retrieved {len(pages)} pages via {description}", 'info')
                                        # Save the response for debugging
                                        try:
                                            debug_dir = os.path.join(os.getcwd(), 'debug_responses')
                                            os.makedirs(debug_dir, exist_ok=True)
                                            response_file = os.path.join(debug_dir, f"response_{document_id}_{int(time.time())}.json")
                                            with open(response_file, 'w', encoding='utf-8') as f:
                                                json.dump(data, f, indent=2, ensure_ascii=False)
                                            log_debug(f"📝 Saved response to: {response_file}", 'debug')
                                        except Exception as e:
                                            log_debug(f"⚠️ Failed to save response: {str(e)}", 'warning')
                                        break
                                        
                                except json.JSONDecodeError:
                                    # If it's not JSON, maybe it's plain text
                                    if response.text.strip():
                                        log_debug("⚠️ Response is not JSON, trying to process as plain text", 'warning')
                                        # Save the text response
                                        try:
                                            debug_dir = os.path.join(os.getcwd(), 'debug_responses')
                                            os.makedirs(debug_dir, exist_ok=True)
                                            response_file = os.path.join(debug_dir, f"response_{document_id}_{int(time.time())}.txt")
                                            with open(response_file, 'w', encoding='utf-8') as f:
                                                f.write(response.text)
                                            log_debug(f"📝 Saved text response to: {response_file}", 'debug')
                                            
                                            # If we got text, return it directly
                                            return response.text
                                        except Exception as e:
                                            log_debug(f"⚠️ Failed to save text response: {str(e)}", 'warning')
                                    else:
                                        log_debug("⚠️ Empty response received", 'warning')
                            else:
                                log_debug(f"⚠️ Request failed with status {response.status_code}", 'warning')
                                if response.text:
                                    log_debug(f"Response text: {response.text[:500]}...", 'debug')
                                    
                        except Exception as e:
                            log_debug(f"⚠️ Error getting pages from {endpoint}: {str(e)}", 'warning')
                            if debug:
                                import traceback
                                log_debug(f"Traceback: {traceback.format_exc()}", 'debug')
                    
                    if not pages:
                        log_debug("❌ Could not retrieve any pages from the document", 'error')
                        
                        # One last attempt - try to export the document as text
                        try:
                            export_url = f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/export?type=TXT"
                            log_debug(f"🔄 Attempting to export document as text from: {export_url}", 'warning')
                            
                            response = session.get(export_url, headers=headers, timeout=60, stream=True)
                            
                            if response.status_code == 200 and response.text.strip():
                                log_debug(f"✅ Successfully exported document text ({len(response.text)} characters)", 'info')
                                
                                # Save the exported text
                                debug_dir = os.path.join(os.getcwd(), 'debug_exports')
                                os.makedirs(debug_dir, exist_ok=True)
                                export_file = os.path.join(debug_dir, f"export_{document_id}_{int(time.time())}.txt")
                                
                                with open(export_file, 'w', encoding='utf-8') as f:
                                    f.write(response.text)
                                
                                log_debug(f"📝 Exported text saved to: {export_file}", 'info')
                                return response.text
                            else:
                                log_debug(f"⚠️ Export failed with status {response.status_code}", 'warning')
                                if response.text:
                                    log_debug(f"Export response: {response.text[:500]}...", 'debug')
                        except Exception as e:
                            log_debug(f"⚠️ Error during document export: {str(e)}", 'warning')
                            if debug:
                                import traceback
                                log_debug(f"Traceback: {traceback.format_exc()}", 'debug')
                        
                        return None
            
            except Exception as e:
                error_msg = f"❌ Error processing document data: {str(e)}"
                log_debug(error_msg, 'error')
                if debug:
                    import traceback
                    log_debug(f"Traceback: {traceback.format_exc()}", 'debug')
                return None
            
            finally:
                # Save the debug log before returning
                save_debug_log()
                
            all_text = []
            
            for page_idx, page in enumerate(pages, 1):
                page_id = page.get('pageId')
                if not page_id:
                    logger.warning("⚠️ Page has no pageId, skipping")
                    continue
                    
                logger.info(f"\n📄 Processing page {page_idx}/{len(pages)} (ID: {page_id})")
                
                if debug:
                    logger.debug(f"Page data: {json.dumps({k: v for k, v in page.items() if k != 'thumbUrl'}, indent=2, ensure_ascii=False)[:1000]}...")
                
                # Get available transcripts for this page
                transcripts = page.get('tsList', {}).get('transcripts', [])
                logger.info(f"📜 Found {len(transcripts)} transcript(s) for this page")
                
                if debug and transcripts:
                    for idx, ts in enumerate(transcripts, 1):
                        logger.debug(f"  Transcript {idx}: ID={ts.get('tsId')}, Status={ts.get('status')}, Key={ts.get('key')}")
                
                # Try multiple endpoint variations
                endpoints = []
                
                # 1. Try with transcript ID if available
                if transcripts:
                    # Sort by tsId in descending order to get the latest transcript first
                    sorted_transcripts = sorted(transcripts, key=lambda x: x.get('tsId', 0), reverse=True)
                    
                    for ts in sorted_transcripts:
                        ts_id = ts.get('tsId')
                        ts_status = ts.get('status', 'UNKNOWN')
                        ts_key = ts.get('key', 'N/A')
                        
                        if ts_id:
                            endpoint = f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/{page_id}/text?tsId={ts_id}"
                            endpoints.append(endpoint)
                            logger.info(f"📝 Found transcript: ID={ts_id}, Status={ts_status}, Key={ts_key}")
                
                # 2. Standard endpoints (try these as fallbacks)
                standard_endpoints = [
                    f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/{page_id}/text",
                    f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/{page_id}/text/plain",
                    f"{self.base_url}/TrpServer/rest/collections/{collection_id}/{document_id}/pages/{page_id}/text"
                ]
                
                # Add standard endpoints if not already in the list
                for endpoint in standard_endpoints:
                    if endpoint not in endpoints:
                        endpoints.append(endpoint)
                
                logger.info(f"🔍 Will try {len(endpoints)} different endpoints to retrieve text")
                
                # Try each endpoint until we get text
                page_text = None
                
                for endpoint_idx, endpoint in enumerate(endpoints, 1):
                    try:
                        logger.info(f"\n🔍 Attempt {endpoint_idx}/{len(endpoints)}: {endpoint}")
                        
                        if debug:
                            logger.debug(f"Sending GET request to: {endpoint}")
                        
                        # Add a small delay between requests to avoid rate limiting
                        if endpoint_idx > 1:
                            time.sleep(1)
                        
                        text_response = self.session.get(
                            endpoint, 
                            headers=headers, 
                            timeout=30,
                            allow_redirects=True
                        )
                        
                        if debug:
                            logger.debug(f"Response status: {text_response.status_code}")
                            logger.debug(f"Response headers: {dict(text_response.headers)}")
                        
                        if text_response.status_code == 200:
                            content_type = text_response.headers.get('content-type', '')
                            
                            if 'application/json' in content_type:
                                try:
                                    json_data = text_response.json()
                                    if debug:
                                        logger.debug(f"JSON response: {json.dumps(json_data, indent=2, ensure_ascii=False)[:1000]}...")
                                    
                                    # Handle different JSON response formats
                                    if 'text' in json_data:
                                        page_text = json_data['text']
                                    elif 'content' in json_data:
                                        page_text = json_data['content']
                                    elif isinstance(json_data, list) and len(json_data) > 0 and 'text' in json_data[0]:
                                        page_text = '\n'.join([item.get('text', '') for item in json_data if 'text' in item])
                                    else:
                                        logger.warning("⚠️ Unhandled JSON response format")
                                        if debug:
                                            logger.debug(f"Full response: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
                                        continue
                                    
                                    if page_text and page_text.strip():
                                        logger.info(f"✅ Successfully retrieved {len(page_text)} characters from JSON response")
                                        break
                                    
                                except json.JSONDecodeError:
                                    logger.warning("⚠️ Expected JSON but got non-JSON response")
                                    page_text = text_response.text
                                    if page_text.strip():
                                        logger.info(f"✅ Successfully retrieved {len(page_text)} characters (raw text)")
                                        break
                                    
                            else:
                                # Assume plain text response
                                page_text = text_response.text
                                if page_text.strip():
                                    logger.info(f"✅ Successfully retrieved {len(page_text)} characters (plain text)")
                                    break
                        
                        logger.warning(f"⚠️ Failed to get text (Status {text_response.status_code}): {endpoint}")
                        
                        if debug and text_response.text:
                            logger.debug(f"Response preview: {text_response.text[:500]}...")
                            
                    except requests.exceptions.RequestException as e:
                        logger.warning(f"⚠️ Request failed: {str(e)}")
                        if debug:
                            logger.debug(f"Exception details:", exc_info=True)
                    except Exception as e:
                        logger.warning(f"⚠️ Unexpected error: {str(e)}")
                        if debug:
                            logger.debug(f"Exception details:", exc_info=True)
                
                if page_text:
                    all_text.append(page_text)
                else:
                    logger.error(f"❌ All endpoints failed for page {page_id}")
                    
                    # Try to get more details about the page
                    logger.info("🔍 Page details:")
                    logger.info(f"- Page ID: {page_id}")
                    logger.info(f"- Width: {page.get('width')} x Height: {page.get('height')}")
                    logger.info(f"- Thumbnail: {page.get('thumbUrl', 'N/A')}")
                    
                    if transcripts:
                        logger.info(f"- Available transcripts: {[(t.get('status'), t.get('key')) for t in transcripts]}")
                    
            if all_text:
                combined_text = '\n\n'.join(all_text)
                logger.info(f"✅ Successfully combined text from {len(all_text)} pages ({len(combined_text)} chars)")
                return combined_text
            else:
                logger.warning("⚠️ No text content found in any pages")
                
                # Final fallback: Try the export endpoint as last resort
                export_url = f"{self.base_url}/TrpServer/rest/recognition/{collection_id}/{document_id}/text"
                logger.info(f"🔄 Trying export endpoint as last resort: {export_url}")
                
                try:
                    export_response = self.session.get(export_url, headers=headers, timeout=60)
                    if export_response.status_code == 200 and export_response.text.strip():
                        logger.info("✅ Successfully retrieved text via export endpoint")
                        return export_response.text.strip()
                    else:
                        logger.warning(f"⚠️ Export endpoint failed with status {export_response.status_code}")
                except Exception as e:
                    logger.warning(f"⚠️ Error using export endpoint: {str(e)}")
            
            # Provide detailed guidance
            logger.error(f"❌ Failed to get text from document {document_id}")
            logger.info("\n💡 Possible solutions:")
            logger.info("1. Check if the document has been fully processed in Transkribus")
            logger.info("2. Verify the document has transcription content (look for 'Transcription' tab)")
            logger.info("3. Try processing a different document that you know has text")
            logger.info("4. Check the document status in the Transkribus web interface")
            logger.info("5. For manually corrected documents, ensure you've saved all changes")
            logger.info("6. Try logging out and back in to refresh your session")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting document text: {e}")
            return None
    
    def download_document_by_name(self, document_name: str, output_path: str = None) -> Optional[str]:
        """Download text from an existing document by name"""
        try:
            # Find the document
            document = self.find_document_by_name(document_name)
            if not document:
                return None
            
            collection_id = document['collection_id']
            document_id = document['docId']
            
            # Get the text
            text = self.get_document_text(collection_id, document_id)
            if not text:
                return None
            
            # Save to file if output path specified
            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                logger.info(f"Document text saved to: {output_file}")
                return str(output_file)
            
            return text
            
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return None
    
    def interactive_collection_selection(self) -> Optional[Dict]:
        """Interactive collection selection with user prompts"""
        try:
            collections = self.get_collections()
            if not collections:
                print("❌ No collections found")
                return None
            
            print("\n📚 Available Collections:")
            print("=" * 50)
            for i, collection in enumerate(collections, 1):
                collection_name = collection.get('colName', 'Unknown')
                doc_count = collection.get('nrOfDocuments', 0)
                print(f"{i:2d}. {collection_name} ({doc_count} documents)")
            
            print("\n💡 You can also type the collection name directly")
            
            while True:
                choice = input("\n🎯 What collection: ").strip()
                
                if not choice:
                    continue
                
                # Try to parse as number first
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(collections):
                        return collections[index]
                    else:
                        print(f"❌ Invalid number. Please choose 1-{len(collections)}")
                        continue
                
                # Try to find by name
                for collection in collections:
                    if collection.get('colName', '').lower() == choice.lower():
                        return collection
                
                print(f"❌ Collection '{choice}' not found. Try again.")
                
        except Exception as e:
            logger.error(f"Error in collection selection: {e}")
            return None
    
    def interactive_document_selection(self, collection_id: int, collection_name: str) -> List[Dict]:
        """Interactive document selection with user prompts"""
        try:
            documents = self.get_documents_in_collection(collection_id)
            if not documents:
                print(f"❌ No documents found in collection: {collection_name}")
                return []
            
            print(f"\n📄 Documents in '{collection_name}':")
            print("=" * 50)
            for i, doc in enumerate(documents, 1):
                doc_title = doc.get('title', 'Untitled')
                doc_status = doc.get('status', 'Unknown')
                print(f"{i:2d}. {doc_title} (Status: {doc_status})")
            
            print("\n💡 Enter document numbers (e.g., 1,3,5) or names (e.g., Document1, Document10)")
            print("💡 You can also type 'all' to select all documents")
            
            while True:
                choice = input("\n🎯 Which document(s): ").strip()
                
                if not choice:
                    continue
                
                if choice.lower() == 'all':
                    return documents
                
                selected_docs = []
                
                # Split by comma and process each choice
                choices = [c.strip() for c in choice.split(',')]
                
                for c in choices:
                    if c.isdigit():
                        # Handle numeric selection
                        index = int(c) - 1
                        if 0 <= index < len(documents):
                            selected_docs.append(documents[index])
                        else:
                            print(f"❌ Invalid number: {c}. Please choose 1-{len(documents)}")
                            selected_docs = []  # Reset on error
                            break
                    else:
                        # Handle name selection
                        found = False
                        for doc in documents:
                            if doc.get('title', '').lower() == c.lower():
                                selected_docs.append(doc)
                                found = True
                                break
                        
                        if not found:
                            print(f"❌ Document '{c}' not found")
                            selected_docs = []  # Reset on error
                            break
                
                if selected_docs:
                    # Show selected documents for confirmation
                    print(f"\n✅ Selected {len(selected_docs)} document(s):")
                    for doc in selected_docs:
                        print(f"   📄 {doc.get('title', 'Untitled')}")
                    
                    confirm = input("\n❓ Proceed with these documents? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return selected_docs
                    else:
                        print("\n🔄 Let's try again...")
                        continue
                
        except Exception as e:
            logger.error(f"Error in document selection: {e}")
            return []
    
    def get_text_from_job(self, job_id: str) -> Optional[str]:
        """Get extracted text from completed OCR job"""
        try:
            # Get job details to find document ID
            job_response = self.session.get(
                f"{self.base_url}/jobs/{job_id}",
                headers={'Cookie': f'JSESSIONID={self.session_id}'}
            )
            
            if job_response.status_code != 200:
                logger.error(f"Failed to get job details: {job_response.status_code}")
                return None
            
            job_data = job_response.json()
            doc_id = job_data.get('docId')
            
            if not doc_id:
                logger.error("No document ID found in job data")
                return None
            
            # Get document pages
            pages_response = self.session.get(
                f"{self.base_url}/collections/{doc_id}/pages",
                headers={'Cookie': f'JSESSIONID={self.session_id}'}
            )
            
            if pages_response.status_code != 200:
                logger.error(f"Failed to get pages: {pages_response.status_code}")
                return None
            
            pages_data = pages_response.json()
            
            # Extract text from all pages
            full_text = []
            for page in pages_data.get('pageList', {}).get('pages', []):
                page_id = page.get('pageId')
                if page_id:
                    text_response = self.session.get(
                        f"{self.base_url}/collections/{doc_id}/{page_id}/text",
                        headers={'Cookie': f'JSESSIONID={self.session_id}'}
                    )
                    
                    if text_response.status_code == 200:
                        full_text.append(text_response.text)
            
            return '\n\n'.join(full_text) if full_text else None
            
        except Exception as e:
            logger.error(f"Error getting text from job: {e}")
            return None
    
    def create_document(self, collection_id: int, pdf_path: str, title: str = None) -> Optional[int]:
        """Upload PDF and create document in collection"""
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"❌ PDF file not found: {pdf_path}")
                return None
            
            # Prepare file for upload
            pdf_name = Path(pdf_path).name
            doc_title = title or Path(pdf_path).stem
            
            with open(pdf_path, 'rb') as pdf_file:
                files = {
                    'file': (pdf_name, pdf_file, 'application/pdf')
                }
                
                data = {
                    'collId': collection_id,
                    'title': doc_title
                }
                
                logger.info(f"📤 Uploading PDF: {pdf_name}")
                response = self.session.post(
                    f"{self.base_url}/uploads",
                    files=files,
                    data=data,
                    timeout=300  # 5 minute timeout for large files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    doc_id = result.get('docId')
                    logger.info(f"✅ Document created with ID: {doc_id}")
                    return doc_id
                else:
                    logger.error(f"❌ Upload failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error uploading document: {e}")
            return None
    
    def start_ocr_job(self, collection_id: int, doc_id: int, pages: str = "1-") -> Optional[str]:
        """Start OCR job for document"""
        try:
            job_data = {
                'collId': collection_id,
                'docId': doc_id,
                'pages': pages,  # "1-" means all pages
                'doWordSeg': True,
                'doLineSeg': True,
                'doPolygonToBaseline': True
            }
            
            logger.info(f"🔄 Starting OCR job for document {doc_id}")
            response = self.session.post(
                f"{self.base_url}/LA",  # Layout Analysis endpoint
                data=job_data
            )
            
            if response.status_code == 200:
                job_id = response.text.strip()
                logger.info(f"✅ OCR job started with ID: {job_id}")
                return job_id
            else:
                logger.error(f"❌ Failed to start OCR job: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error starting OCR job: {e}")
            return None
    
    def check_job_status(self, job_id: str) -> Dict[str, Any]:
        """Check status of OCR job"""
        try:
            response = self.session.get(f"{self.base_url}/jobs/{job_id}")
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ Failed to check job status: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Error checking job status: {e}")
            return {}
    
    def wait_for_job_completion(self, job_id: str, timeout: int = 600) -> bool:
        """Wait for OCR job to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.check_job_status(job_id)
            
            if status.get('state') == 'FINISHED':
                logger.info(f"✅ OCR job {job_id} completed successfully")
                return True
            elif status.get('state') == 'FAILED':
                logger.error(f"❌ OCR job {job_id} failed")
                return False
            elif status.get('state') in ['RUNNING', 'CREATED']:
                logger.info(f"⏳ OCR job {job_id} still running... ({status.get('state')})")
                time.sleep(10)  # Wait 10 seconds before checking again
            else:
                logger.warning(f"⚠️ Unknown job state: {status.get('state')}")
                time.sleep(10)
        
        logger.error(f"❌ OCR job {job_id} timed out after {timeout} seconds")
        return False
    
    def get_document_text(self, collection_id: int, doc_id: int, page_num: int = None) -> str:
        """Get extracted text from document"""
        try:
            if page_num:
                # Get specific page
                url = f"{self.base_url}/collections/{collection_id}/{doc_id}/{page_num}/text"
            else:
                # Get all pages
                url = f"{self.base_url}/collections/{collection_id}/{doc_id}/fulldoc"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                # Handle different response formats
                if response.headers.get('content-type', '').startswith('application/json'):
                    data = response.json()
                    return data.get('text', '')
                else:
                    return response.text
            else:
                logger.error(f"❌ Failed to get document text: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Error getting document text: {e}")
            return ""
    
    def process_pdf_to_text(self, pdf_path: str, collection_id: int = None, title: str = None) -> Optional[str]:
        """Complete workflow: upload PDF, run OCR, get text"""
        try:
            # Login if not already logged in
            if not self.session_id:
                if not self.login():
                    return None
            
            # Get collections if collection_id not provided
            if collection_id is None:
                collections = self.get_collections()
                if not collections:
                    logger.error("❌ No collections available")
                    return None
                collection_id = collections[0]['colId']  # Use first available collection
                logger.info(f"📚 Using collection: {collections[0]['colName']}")
            
            # Upload document
            doc_id = self.create_document(collection_id, pdf_path, title)
            if not doc_id:
                return None
            
            # Start OCR
            job_id = self.start_ocr_job(collection_id, doc_id)
            if not job_id:
                return None
            
            # Wait for completion
            if not self.wait_for_job_completion(job_id):
                return None
            
            # Get extracted text
            text = self.get_document_text(collection_id, doc_id)
            if text:
                logger.info(f"✅ Successfully extracted {len(text)} characters of text")
                return text
            else:
                logger.error("❌ No text extracted from document")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in PDF processing workflow: {e}")
            return None
    
    def logout(self):
        """Logout from Transkribus"""
        try:
            if self.session_id:
                self.session.post(f"{self.base_url}/auth/logout")
                self.session_id = None
                logger.info("✅ Logged out from Transkribus")
        except Exception as e:
            logger.warning(f"⚠️ Error during logout: {e}")
