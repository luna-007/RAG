# src/loaders/servicenow_loader.py
"""
ServiceNow Knowledge Article Loader.
Fetches knowledge articles via ServiceNow REST API.
"""
import os
import requests
from typing import List, Optional, Dict, Any
from langchain_classic.docstore.document import Document
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.logging_utils import get_logger

logger = get_logger("servicenow_loader")


class ServiceNowKnowledgeLoader:
    """
    Load knowledge articles from ServiceNow.
    Supports OAuth and basic authentication.
    """
    
    def __init__(
        self,
        instance_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        """
        Initialize ServiceNow loader.
        
        Args:
            instance_url: ServiceNow instance URL (e.g., 'walmart.service-now.com')
            username: ServiceNow username (for basic auth)
            password: ServiceNow password (for basic auth)
            api_token: OAuth token (alternative to username/password)
        """
        self.instance_url = instance_url.rstrip('/')
        
        # Set up authentication
        if api_token:
            self.headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            self.auth = None
        elif username and password:
            self.headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            self.auth = (username, password)
        else:
            # Try to get from environment
            username = os.getenv('SERVICENOW_USERNAME')
            password = os.getenv('SERVICENOW_PASSWORD')
            api_token = os.getenv('SERVICENOW_API_TOKEN')
            
            if api_token:
                self.headers = {
                    'Authorization': f'Bearer {api_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                self.auth = None
            elif username and password:
                self.headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                self.auth = (username, password)
            else:
                raise ValueError(
                    "ServiceNow credentials required. Provide either:\n"
                    "  - api_token\n"
                    "  - username + password\n"
                    "  - Set SERVICENOW_API_TOKEN or SERVICENOW_USERNAME/PASSWORD env vars"
                )
        
        # Set up proxy for Walmart network
        self.proxies = {
            'http': 'http://sysproxy.wal-mart.com:8080',
            'https': 'http://sysproxy.wal-mart.com:8080'
        }
        
        logger.info("ServiceNow loader initialized", instance_url=self.instance_url)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Make authenticated request to ServiceNow API.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response
        """
        url = f"{self.instance_url}{endpoint}"
        
        logger.debug("Making ServiceNow API request", url=url, params=params)
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                auth=self.auth,
                params=params,
                proxies=self.proxies,
                timeout=30
            )
            response.raise_for_status()
            
            logger.debug("ServiceNow API request successful", status_code=response.status_code)
            return response.json()
            
        except requests.exceptions.ProxyError:
            # Try without proxy if proxy fails
            logger.warning("Proxy failed, retrying without proxy")
            response = requests.get(
                url,
                headers=self.headers,
                auth=self.auth,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error("ServiceNow API request failed", error=str(e), url=url)
            raise
    
    def load(
        self,
        limit: int = 100,
        query: Optional[str] = None,
        kb_knowledge_base: Optional[str] = None,
        workflow_state: str = "published",
    ) -> List[Document]:
        """
        Load knowledge articles from ServiceNow.
        
        Args:
            limit: Maximum number of articles to fetch
            query: Custom ServiceNow query (e.g., 'category=IT^ORcategory=HR')
            kb_knowledge_base: Filter by knowledge base sys_id
            workflow_state: Article workflow state (default: 'published')
            
        Returns:
            List of LangChain Documents
        """
        logger.info("Loading ServiceNow knowledge articles",
                   limit=limit,
                   query=query,
                   kb_knowledge_base=kb_knowledge_base,
                   workflow_state=workflow_state)
        
        # Build query parameters
        params = {
            'sysparm_limit': limit,
            'sysparm_fields': 'sys_id,number,short_description,text,article_type,kb_knowledge_base,workflow_state,author,sys_created_on,sys_updated_on',
        }
        
        # Build query filter
        query_parts = []
        
        if workflow_state:
            query_parts.append(f"workflow_state={workflow_state}")
        
        if kb_knowledge_base:
            query_parts.append(f"kb_knowledge_base={kb_knowledge_base}")
        
        if query:
            query_parts.append(query)
        
        if query_parts:
            params['sysparm_query'] = '^'.join(query_parts)
        
        # Make API request
        try:
            response_data = self._make_request('/api/now/table/kb_knowledge', params)
            
            articles = response_data.get('result', [])
            logger.info(f"Retrieved {len(articles)} knowledge articles")
            
            if not articles:
                logger.warning("No knowledge articles found")
                return []
            
            # Convert to LangChain Documents
            documents = []
            for article in articles:
                # Combine title and content
                content = f"# {article.get('short_description', 'Untitled')}\n\n"
                content += article.get('text', '')
                
                # Create metadata
                metadata = {
                    'source': 'servicenow',
                    'sys_id': article.get('sys_id', ''),
                    'number': article.get('number', ''),
                    'title': article.get('short_description', ''),
                    'article_type': article.get('article_type', ''),
                    'kb_knowledge_base': article.get('kb_knowledge_base', ''),
                    'workflow_state': article.get('workflow_state', ''),
                    'author': article.get('author', ''),
                    'created_on': article.get('sys_created_on', ''),
                    'updated_on': article.get('sys_updated_on', ''),
                    'url': f"{self.instance_url}/kb_view.do?sysparm_article={article.get('number', '')}"
                }
                
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            
            logger.info(f"Converted {len(documents)} articles to documents")
            return documents
            
        except Exception as e:
            logger.error("Failed to load ServiceNow knowledge articles", error=str(e))
            raise
    
    def list_knowledge_bases(self) -> List[Dict[str, str]]:
        """
        List available knowledge bases.
        
        Returns:
            List of knowledge base info (sys_id, title)
        """
        logger.info("Listing ServiceNow knowledge bases")
        
        try:
            response_data = self._make_request(
                '/api/now/table/kb_knowledge_base',
                params={'sysparm_fields': 'sys_id,title,description'}
            )
            
            kbs = response_data.get('result', [])
            logger.info(f"Found {len(kbs)} knowledge bases")
            
            return [
                {
                    'sys_id': kb.get('sys_id', ''),
                    'title': kb.get('title', ''),
                    'description': kb.get('description', '')
                }
                for kb in kbs
            ]
            
        except Exception as e:
            logger.error("Failed to list knowledge bases", error=str(e))
            return []
