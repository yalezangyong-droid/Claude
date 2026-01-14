"""
LinkedIn API Client
Handles authentication and data fetching from LinkedIn API
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class LinkedInAPIClient:
    """Client for interacting with LinkedIn API"""

    BASE_URL = "https://api.linkedin.com/v2"
    AUTH_URL = "https://www.linkedin.com/oauth/v2"

    def __init__(self, access_token: str = None):
        """
        Initialize LinkedIn API client

        Args:
            access_token: LinkedIn OAuth access token
        """
        self.access_token = access_token
        self.session = requests.Session()
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            })

    @staticmethod
    def get_authorization_url(client_id: str, redirect_uri: str, state: str) -> str:
        """
        Generate OAuth authorization URL

        Args:
            client_id: Your LinkedIn app client ID
            redirect_uri: Callback URL
            state: Random string for security

        Returns:
            Authorization URL to visit
        """
        scope = "r_liteprofile r_emailaddress w_member_social rw_organization_admin r_organization_social"
        params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'state': state,
            'scope': scope
        }

        query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
        return f"{LinkedInAPIClient.AUTH_URL}/authorization?{query_string}"

    @staticmethod
    def exchange_code_for_token(client_id: str, client_secret: str,
                                code: str, redirect_uri: str) -> Dict:
        """
        Exchange authorization code for access token

        Args:
            client_id: Your LinkedIn app client ID
            client_secret: Your LinkedIn app client secret
            code: Authorization code from callback
            redirect_uri: Callback URL (must match)

        Returns:
            Token response with access_token and expires_in
        """
        token_url = f"{LinkedInAPIClient.AUTH_URL}/accessToken"

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()

        return response.json()

    def get_user_profile(self) -> Dict:
        """
        Get authenticated user's profile

        Returns:
            User profile data
        """
        url = f"{self.BASE_URL}/me"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_user_posts(self, author_urn: str, count: int = 50) -> List[Dict]:
        """
        Get posts by the authenticated user

        Args:
            author_urn: User's URN (from profile)
            count: Number of posts to fetch

        Returns:
            List of post data
        """
        url = f"{self.BASE_URL}/ugcPosts"
        params = {
            'q': 'authors',
            'authors': f'List({author_urn})',
            'count': count,
            'sortBy': 'LAST_MODIFIED'
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        return data.get('elements', [])

    def get_post_statistics(self, post_urn: str) -> Dict:
        """
        Get engagement statistics for a specific post

        Args:
            post_urn: Post URN

        Returns:
            Engagement statistics
        """
        # Extract the share ID from URN
        share_id = post_urn.split(':')[-1]

        url = f"{self.BASE_URL}/socialActions/{share_id}"
        response = self.session.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            # Fallback: try organization social actions endpoint
            url = f"{self.BASE_URL}/organizationalEntityShareStatistics"
            params = {
                'q': 'organizationalEntity',
                'organizationalEntity': post_urn
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def get_post_analytics(self, post_urn: str) -> Dict:
        """
        Get detailed analytics for a post including impressions

        Args:
            post_urn: Post URN

        Returns:
            Analytics data with views, engagement, etc.
        """
        share_id = post_urn.split(':')[-1]

        # Try share statistics endpoint
        url = f"{self.BASE_URL}/shareStatistics/{share_id}"
        response = self.session.get(url)

        if response.status_code != 200:
            return self._get_fallback_analytics(post_urn)

        data = response.json()

        # Extract metrics
        metrics = {
            'likes': data.get('likeCount', 0),
            'comments': data.get('commentCount', 0),
            'shares': data.get('shareCount', 0),
            'views': data.get('impressionCount', 0),
            'clicks': data.get('clickCount', 0),
            'engagement_rate': data.get('engagement', 0)
        }

        return metrics

    def _get_fallback_analytics(self, post_urn: str) -> Dict:
        """Fallback method to get basic engagement metrics"""
        try:
            stats = self.get_post_statistics(post_urn)
            return {
                'likes': stats.get('likeCount', 0),
                'comments': stats.get('commentCount', 0),
                'shares': stats.get('shareCount', 0),
                'views': stats.get('impressionCount', 0),
                'clicks': 0,
                'engagement_rate': 0
            }
        except Exception as e:
            print(f"Warning: Could not fetch analytics for {post_urn}: {e}")
            return {
                'likes': 0,
                'comments': 0,
                'shares': 0,
                'views': 0,
                'clicks': 0,
                'engagement_rate': 0
            }

    def extract_post_info(self, post_data: Dict) -> Dict:
        """
        Extract relevant information from post data

        Args:
            post_data: Raw post data from API

        Returns:
            Cleaned post information
        """
        # Extract text content
        text = ''
        if 'specificContent' in post_data:
            content = post_data['specificContent'].get('com.linkedin.ugc.ShareContent', {})
            text = content.get('shareCommentary', {}).get('text', '')

        # Determine post type
        post_type = 'short'
        if 'media' in post_data.get('specificContent', {}).get('com.linkedin.ugc.ShareContent', {}):
            media = post_data['specificContent']['com.linkedin.ugc.ShareContent']['media']
            if media:
                media_type = media[0].get('media', '')
                if 'image' in media_type.lower():
                    post_type = 'image'
                elif 'video' in media_type.lower():
                    post_type = 'video'
                elif 'article' in media_type.lower():
                    post_type = 'article'

        # Extract timestamps
        created_at = post_data.get('created', {}).get('time', 0)
        if created_at:
            created_at = datetime.fromtimestamp(created_at / 1000).isoformat()
        else:
            created_at = datetime.now().isoformat()

        return {
            'urn': post_data.get('id', ''),
            'text': text,
            'type': post_type,
            'created_at': created_at,
            'url': self._construct_post_url(post_data)
        }

    def _construct_post_url(self, post_data: Dict) -> str:
        """Construct LinkedIn post URL"""
        urn = post_data.get('id', '')
        if urn:
            # Extract activity ID from URN
            activity_id = urn.split(':')[-1]
            return f"https://www.linkedin.com/feed/update/urn:li:activity:{activity_id}"
        return ''

    def fetch_all_posts_with_metrics(self, author_urn: str) -> List[Dict]:
        """
        Fetch all user posts with their engagement metrics

        Args:
            author_urn: User's URN

        Returns:
            List of posts with metrics
        """
        posts = self.get_user_posts(author_urn)
        enriched_posts = []

        for post in posts:
            try:
                post_info = self.extract_post_info(post)
                metrics = self.get_post_analytics(post_info['urn'])

                enriched_post = {
                    **post_info,
                    'metrics': metrics
                }
                enriched_posts.append(enriched_post)

                # Rate limiting - be nice to the API
                time.sleep(0.5)

            except Exception as e:
                print(f"Error processing post: {e}")
                continue

        return enriched_posts


class LinkedInAuthHelper:
    """Helper class for OAuth authentication flow"""

    @staticmethod
    def save_credentials(access_token: str, expires_in: int, file_path: str = ".env"):
        """Save credentials to file"""
        expires_at = datetime.now().timestamp() + expires_in

        env_path = Path(file_path)
        lines = []

        # Read existing lines
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = [line for line in f.readlines()
                        if not line.startswith('LINKEDIN_ACCESS_TOKEN') and
                        not line.startswith('LINKEDIN_TOKEN_EXPIRES_AT')]

        # Add new credentials
        lines.append(f"LINKEDIN_ACCESS_TOKEN={access_token}\n")
        lines.append(f"LINKEDIN_TOKEN_EXPIRES_AT={expires_at}\n")

        with open(env_path, 'w') as f:
            f.writelines(lines)

        print(f"✅ Credentials saved to {file_path}")

    @staticmethod
    def load_credentials(file_path: str = ".env") -> Optional[str]:
        """Load access token from file"""
        env_path = Path(file_path)

        if not env_path.exists():
            return None

        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('LINKEDIN_ACCESS_TOKEN='):
                    token = line.split('=', 1)[1].strip()
                    return token if token else None

        return None

    @staticmethod
    def is_token_expired(file_path: str = ".env") -> bool:
        """Check if token is expired"""
        env_path = Path(file_path)

        if not env_path.exists():
            return True

        expires_at = None
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('LINKEDIN_TOKEN_EXPIRES_AT='):
                    expires_at = float(line.split('=', 1)[1].strip())
                    break

        if expires_at is None:
            return True

        return datetime.now().timestamp() >= expires_at
