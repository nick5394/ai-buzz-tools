"""
WordPress REST API client for page operations.

Adapted from streamline v2's WordPressService, focused on page management
for AI-Buzz tool pages.
"""
import os
import logging
import time
import requests
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# Retry configuration for transient errors (503, 429, etc.)
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class WordPressService:
    """Client for WordPress REST API page operations."""
    
    def __init__(self):
        """Load config from environment variables."""
        self.site_url = os.getenv("WORDPRESS_SITE_URL", "https://www.ai-buzz.com")
        self.username = os.getenv("WORDPRESS_USERNAME")
        self.app_password = os.getenv("WORDPRESS_APP_PASSWORD")
        
        if not self.username or not self.app_password:
            logger.warning("WordPress credentials not configured")
        
        self.api_url = f"{self.site_url.rstrip('/')}/wp-json/wp/v2"
        self.auth = (self.username, self.app_password) if self.username else None
    
    def is_configured(self) -> bool:
        """Check if WordPress credentials are configured."""
        return bool(self.username and self.app_password)
    
    def _request_with_retry(
        self, 
        method: str, 
        url: str, 
        max_retries: int = MAX_RETRIES,
        **kwargs
    ) -> requests.Response:
        """Make HTTP request with retry logic for transient errors.
        
        Args:
            method: HTTP method (get, post, etc.)
            url: Request URL
            max_retries: Maximum number of retries
            **kwargs: Additional arguments passed to requests
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.request(method, url, **kwargs)
                
                # If success or non-retryable error, return immediately
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    return response
                
                # Retryable error - log and maybe retry
                if attempt < max_retries:
                    wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Request to {url} returned {response.status_code}. "
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})..."
                    )
                    print(f"  ⏳ Server returned {response.status_code}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    return response
                    
            except requests.RequestException as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = RETRY_DELAY_SECONDS * (2 ** attempt)
                    logger.warning(f"Request failed: {e}. Retrying in {wait_time}s...")
                    print(f"  ⏳ Request failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        return response
    
    def get_page_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a page by its URL slug.
        
        Args:
            slug: Page slug (e.g., 'ai-pricing-calculator')
            
        Returns:
            Dictionary containing page data if found, None if not found
        """
        try:
            response = self._request_with_retry(
                'get',
                f"{self.api_url}/pages",
                params={'slug': slug, 'per_page': 1},
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                pages = response.json()
                if pages:
                    return pages[0]
                return None
            else:
                logger.error(
                    f"Failed to get page by slug '{slug}': "
                    f"Status {response.status_code}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error getting page by slug '{slug}': {e}")
            return None
    
    def get_page(self, page_id: int) -> Optional[Dict[str, Any]]:
        """Get page by ID with full content.
        
        Args:
            page_id: WordPress page ID
            
        Returns:
            Dictionary containing page data if found, None if not found
        """
        try:
            # Request page with meta fields included using context=edit
            response = requests.get(
                f"{self.api_url}/pages/{page_id}",
                params={'context': 'edit'},  # This includes meta fields
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(
                    f"Failed to get page {page_id}: "
                    f"Status {response.status_code}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error getting page {page_id}: {e}")
            return None
    
    def create_page(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new page in WordPress.
        
        Args:
            page_data: Dictionary containing page data including:
                - title: Page title
                - content: Page content (HTML)
                - slug: URL slug
                - status: Page status (draft, publish, etc.)
                - parent: Parent page ID (optional)
                - template: Page template (optional)
                
        Returns:
            Dictionary containing page data if successful, None if failed
        """
        try:
            if not page_data.get('content'):
                raise ValueError("Page content is required")
                
            # Prepare API endpoint
            endpoint = f"{self.api_url}/pages"
            
            # Prepare page data
            api_data = {
                'title': page_data.get('title', 'Draft Page'),
                'content': page_data['content'],
                'status': page_data.get('status', 'draft'),
            }
            
            # Add optional fields if present
            if 'slug' in page_data:
                api_data['slug'] = page_data['slug']
            if 'parent' in page_data:
                api_data['parent'] = page_data['parent']
            if 'template' in page_data:
                api_data['template'] = page_data['template']
                
            # Make API request with retry logic
            response = self._request_with_retry(
                'post',
                endpoint,
                json=api_data,
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=30
            )
            
            # Check response
            if response.status_code in [200, 201]:
                page = response.json()
                logger.info(f"Successfully created page with ID: {page.get('id')}")
                logger.debug(f"WordPress API response: {page}")
                return page
            else:
                logger.error(
                    f"Failed to create page: Status {response.status_code}, "
                    f"Response: {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error creating page: {e}")
            return None
    
    def update_page(self, page_id: int, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing page in WordPress.
        
        Args:
            page_id: WordPress page ID
            page_data: Dictionary containing fields to update
                
        Returns:
            Dictionary containing updated page data if successful, None if failed
        """
        try:
            endpoint = f"{self.api_url}/pages/{page_id}"
            
            response = self._request_with_retry(
                'post',
                endpoint,
                json=page_data,
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                page = response.json()
                logger.info(f"Successfully updated page ID: {page_id}")
                return page
            else:
                logger.error(
                    f"Failed to update page: Status {response.status_code}, "
                    f"Response: {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {e}")
            return None
    
    def list_pages(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """List all pages with pagination.
        
        Args:
            per_page: Number of pages to fetch per page (max 100)
            
        Returns:
            List of page dictionaries
        """
        try:
            all_pages = []
            page = 1
            
            while True:
                response = requests.get(
                    f"{self.api_url}/pages",
                    params={
                        'per_page': min(per_page, 100),
                        'page': page,
                        'orderby': 'date',
                        'order': 'desc'
                    },
                    auth=self.auth,
                    headers={'Accept': 'application/json'},
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch pages: Status {response.status_code}")
                    break
                    
                pages = response.json()
                if not pages:
                    break
                    
                all_pages.extend(pages)
                
                # Check if there are more pages
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                    
                page += 1
            
            logger.info(f"Successfully fetched {len(all_pages)} pages from WordPress")
            return all_pages
            
        except Exception as e:
            logger.error(f"Error fetching pages: {e}")
            return []
    
    # =========================================================================
    # POST OPERATIONS (for guide/article content)
    # =========================================================================
    
    def get_post_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a post by its URL slug.
        
        Args:
            slug: Post slug (e.g., 'ai-openai-429-errors')
            
        Returns:
            Dictionary containing post data if found, None if not found
        """
        try:
            response = self._request_with_retry(
                'get',
                f"{self.api_url}/posts",
                params={'slug': slug, 'per_page': 1},
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                posts = response.json()
                if posts:
                    return posts[0]
                return None
            else:
                logger.error(
                    f"Failed to get post by slug '{slug}': "
                    f"Status {response.status_code}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error getting post by slug '{slug}': {e}")
            return None
    
    def create_post(self, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new post in WordPress.
        
        Args:
            post_data: Dictionary containing post data including:
                - title: Post title
                - content: Post content (HTML)
                - slug: URL slug
                - status: Post status (draft, publish, etc.)
                - categories: List of category IDs (optional)
                - tags: List of tag IDs (optional)
                
        Returns:
            Dictionary containing post data if successful, None if failed
        """
        try:
            if not post_data.get('content'):
                raise ValueError("Post content is required")
                
            endpoint = f"{self.api_url}/posts"
            
            api_data = {
                'title': post_data.get('title', 'Draft Post'),
                'content': post_data['content'],
                'status': post_data.get('status', 'draft'),
            }
            
            if 'slug' in post_data:
                api_data['slug'] = post_data['slug']
            if 'categories' in post_data:
                api_data['categories'] = post_data['categories']
            if 'tags' in post_data:
                api_data['tags'] = post_data['tags']
                
            response = self._request_with_retry(
                'post',
                endpoint,
                json=api_data,
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                post = response.json()
                logger.info(f"Successfully created post with ID: {post.get('id')}")
                return post
            else:
                logger.error(
                    f"Failed to create post: Status {response.status_code}, "
                    f"Response: {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return None
    
    def update_post(self, post_id: int, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing post in WordPress.
        
        Args:
            post_id: WordPress post ID
            post_data: Dictionary containing fields to update
                
        Returns:
            Dictionary containing updated post data if successful, None if failed
        """
        try:
            endpoint = f"{self.api_url}/posts/{post_id}"
            
            response = self._request_with_retry(
                'post',
                endpoint,
                json=post_data,
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                post = response.json()
                logger.info(f"Successfully updated post ID: {post_id}")
                return post
            else:
                logger.error(
                    f"Failed to update post: Status {response.status_code}, "
                    f"Response: {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}")
            return None
    
    def get_or_create_category(self, name: str, slug: str = None, description: str = None, parent: int = 0) -> Optional[int]:
        """Get category ID by name, or create it if it doesn't exist.
        
        Args:
            name: Category name
            slug: Category slug (optional, derived from name if not provided)
            description: Category description (optional)
            parent: Parent category ID (0 for top-level)
            
        Returns:
            Category ID if successful, None if failed
        """
        try:
            # First try to find existing category
            response = self._request_with_retry(
                'get',
                f"{self.api_url}/categories",
                params={'search': name, 'per_page': 100},
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                for cat in categories:
                    if cat.get('name', '').lower() == name.lower():
                        return cat['id']
            
            # Create new category
            cat_data = {'name': name}
            if slug:
                cat_data['slug'] = slug
            if description:
                cat_data['description'] = description
            if parent > 0:
                cat_data['parent'] = parent
                
            response = self._request_with_retry(
                'post',
                f"{self.api_url}/categories",
                json=cat_data,
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return response.json().get('id')
            else:
                logger.error(f"Failed to create category '{name}': {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error with category '{name}': {e}")
            return None
    
    def get_category_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a category by its slug.
        
        Args:
            slug: Category slug (e.g., 'ai-developer-tools')
            
        Returns:
            Category dict if found, None if not found
        """
        try:
            response = self._request_with_retry(
                'get',
                f"{self.api_url}/categories",
                params={'slug': slug, 'per_page': 1},
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                if categories:
                    return categories[0]
            return None
                
        except Exception as e:
            logger.error(f"Error getting category by slug '{slug}': {e}")
            return None
    
    def list_categories(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """List all categories with pagination.
        
        Args:
            per_page: Number of categories to fetch per page (max 100)
            
        Returns:
            List of category dictionaries
        """
        try:
            all_categories = []
            page = 1
            
            while True:
                response = self._request_with_retry(
                    'get',
                    f"{self.api_url}/categories",
                    params={
                        'per_page': min(per_page, 100),
                        'page': page,
                        'orderby': 'name',
                        'order': 'asc'
                    },
                    auth=self.auth,
                    headers={'Accept': 'application/json'},
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch categories: Status {response.status_code}")
                    break
                    
                categories = response.json()
                if not categories:
                    break
                    
                all_categories.extend(categories)
                
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                    
                page += 1
            
            return all_categories
            
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return []
    
    def delete_category(self, category_id: int) -> bool:
        """Delete a category by ID.
        
        Args:
            category_id: WordPress category ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self._request_with_retry(
                'delete',
                f"{self.api_url}/categories/{category_id}",
                params={'force': True},
                auth=self.auth,
                headers={'Accept': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Deleted category ID: {category_id}")
                return True
            else:
                logger.error(f"Failed to delete category: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting category {category_id}: {e}")
            return False

    def update_aioseo_meta(self, page_id: int, meta: Dict[str, str]) -> bool:
        """Update AIOSEO meta data for a page.
        
        AIOSEO stores data in its own database table and exposes it via
        a custom REST endpoint.
        
        Args:
            page_id: WordPress page ID
            meta: Dictionary containing AIOSEO fields:
                - title: SEO title
                - description: Meta description
                
        Returns:
            True if successful, False otherwise
        """
        try:
            # Method 1: Use AIOSEO's dedicated REST endpoint (preferred)
            aioseo_endpoint = f"{self.api_url.replace('/wp/v2', '/aioseo/v1')}/post/{page_id}"
            
            # Prepare AIOSEO-format data
            aioseo_payload = {
                'title': meta.get('title', ''),
                'description': meta.get('description', ''),
                'og_title': meta.get('og_title', meta.get('title', '')),
                'og_description': meta.get('og_description', meta.get('description', '')),
                'twitter_title': meta.get('twitter_title', meta.get('title', '')),
                'twitter_description': meta.get('twitter_description', meta.get('description', '')),
                'robots_default': True,
                'robots_noindex': False,
                'robots_nofollow': False,
            }
            
            response = requests.post(
                aioseo_endpoint,
                json=aioseo_payload,
                auth=self.auth,
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ AIOSEO meta updated via REST endpoint for page {page_id}")
                return True
            else:
                logger.warning(f"AIOSEO REST endpoint returned {response.status_code}")
                logger.debug(f"Response: {response.text[:500]}")
            
            # Method 2: Fallback to pages endpoint with aioseo_meta_data field
            pages_endpoint = f"{self.api_url}/pages/{page_id}"
            
            fallback_payload = {
                'aioseo_meta_data': {
                    'title': meta.get('title', ''),
                    'description': meta.get('description', ''),
                    'og_title': meta.get('og_title', meta.get('title', '')),
                    'og_description': meta.get('og_description', meta.get('description', '')),
                    'twitter_title': meta.get('twitter_title', meta.get('title', '')),
                    'twitter_description': meta.get('twitter_description', meta.get('description', '')),
                }
            }
            
            response = requests.post(
                pages_endpoint,
                json=fallback_payload,
                auth=self.auth,
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ AIOSEO meta updated via pages endpoint for page {page_id}")
                return True
            else:
                logger.error(f"❌ All AIOSEO update methods failed for page {page_id}")
                logger.debug(f"Response: {response.text[:500]}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating AIOSEO meta for page {page_id}: {e}")
            return False
