#!/usr/bin/env python3
"""
LinkedIn Post Scraper with Chrome Profile Persistence

Features:
- Persists login session using Chrome user profile
- Properly scrolls to load lazy-loaded content
- Stops scrolling when reaching date threshold
- Extracts full post content including hashtags
- Supports 30 or 60 day lookback periods

Usage:
    First run (login required):
        python linkedin_scraper.py --days 30

    Subsequent runs (session reused):
        python linkedin_scraper.py --days 30

    Force re-login:
        python linkedin_scraper.py --days 30 --relogin
"""

import os
import sys
import json
import argparse
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class LinkedInPost:
    """Represents a scraped LinkedIn post"""
    post_id: str
    post_url: str
    publish_date: str
    full_content: str
    likes: int
    comments: int
    reposts: int
    impressions: int
    scraped_at: str

    def to_dict(self) -> Dict:
        return asdict(self)


class LinkedInScraper:
    """
    LinkedIn Post Scraper with session persistence and proper scrolling.
    """

    # Chrome profile directory for session persistence
    DEFAULT_PROFILE_DIR = os.path.expanduser("~/.linkedin_scraper_profile")

    # LinkedIn URLs
    LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
    LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"

    # Selectors (updated for current LinkedIn layout)
    SELECTORS = {
        # Login detection
        'logged_in_indicator': 'div.feed-identity-module',
        'login_form': 'form.login__form',

        # Profile/Activity page
        'activity_posts_tab': 'button[id*="posts"]',
        'post_container': 'div.feed-shared-update-v2',
        'post_content': 'div.feed-shared-update-v2__description',
        'post_content_text': 'span.break-words',
        'see_more_button': 'button.feed-shared-inline-show-more-text__see-more-less-toggle',

        # Post metadata
        'post_time': 'span.update-components-actor__sub-description',
        'post_link': 'a.app-aware-link[href*="/posts/"], a.app-aware-link[href*="/activity"]',

        # Engagement metrics
        'reactions_count': 'span.social-details-social-counts__reactions-count',
        'comments_count': 'button[aria-label*="comment"] span.social-details-social-counts__comments',
        'reposts_count': 'button[aria-label*="repost"] span',

        # Alternative selectors for metrics
        'social_counts': 'ul.social-details-social-counts',
        'reaction_button': 'button.social-details-social-counts__count-value',
    }

    def __init__(
        self,
        profile_dir: Optional[str] = None,
        headless: bool = False,
        days_back: int = 30
    ):
        """
        Initialize the scraper.

        Args:
            profile_dir: Directory to store Chrome profile (for session persistence)
            headless: Run Chrome in headless mode (not recommended for first login)
            days_back: Number of days to look back for posts
        """
        self.profile_dir = profile_dir or self.DEFAULT_PROFILE_DIR
        self.headless = headless
        self.days_back = days_back
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.driver: Optional[webdriver.Chrome] = None
        self.posts: List[LinkedInPost] = []

        # Ensure profile directory exists
        Path(self.profile_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Using Chrome profile at: {self.profile_dir}")

    def _create_driver(self) -> webdriver.Chrome:
        """Create Chrome WebDriver with profile persistence."""
        options = Options()

        # Use persistent profile for session storage
        options.add_argument(f"--user-data-dir={self.profile_dir}")
        options.add_argument("--profile-directory=Default")

        # Standard options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Make Chrome less detectable as automation
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        if self.headless:
            options.add_argument("--headless=new")
            logger.warning("Running in headless mode - login may not work!")

        # Create driver
        driver = webdriver.Chrome(options=options)

        # Additional stealth measures
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })

        return driver

    def _wait_for_element(
        self,
        selector: str,
        by: By = By.CSS_SELECTOR,
        timeout: int = 10,
        condition: str = "presence"
    ) -> Optional[any]:
        """Wait for an element with explicit wait."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            if condition == "presence":
                return wait.until(EC.presence_of_element_located((by, selector)))
            elif condition == "clickable":
                return wait.until(EC.element_to_be_clickable((by, selector)))
            elif condition == "visible":
                return wait.until(EC.visibility_of_element_located((by, selector)))
        except TimeoutException:
            return None

    def _is_logged_in(self) -> bool:
        """Check if user is logged into LinkedIn."""
        self.driver.get(self.LINKEDIN_FEED_URL)
        time.sleep(2)

        # Check for login form (means not logged in)
        login_form = self._wait_for_element(
            self.SELECTORS['login_form'],
            timeout=3
        )
        if login_form:
            return False

        # Check for feed (means logged in)
        feed = self._wait_for_element(
            self.SELECTORS['logged_in_indicator'],
            timeout=5
        )
        return feed is not None

    def _wait_for_manual_login(self) -> bool:
        """
        Open login page and wait for user to manually log in.
        Session will be saved to Chrome profile for future use.
        """
        logger.info("=" * 60)
        logger.info("MANUAL LOGIN REQUIRED")
        logger.info("=" * 60)
        logger.info("A Chrome window has opened. Please:")
        logger.info("1. Log into your LinkedIn account")
        logger.info("2. Complete any 2FA if prompted")
        logger.info("3. Wait until you see your feed")
        logger.info("=" * 60)
        logger.info("Your session will be saved for future runs.")
        logger.info("Press Ctrl+C to cancel if needed.")
        logger.info("=" * 60)

        self.driver.get(self.LINKEDIN_LOGIN_URL)

        # Wait up to 5 minutes for user to complete login
        max_wait = 300  # 5 minutes
        check_interval = 3
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(check_interval)
            elapsed += check_interval

            # Check if we're now on the feed
            current_url = self.driver.current_url
            if "/feed" in current_url or "/in/" in current_url:
                # Verify login by checking for feed element
                feed = self._wait_for_element(
                    self.SELECTORS['logged_in_indicator'],
                    timeout=5
                )
                if feed:
                    logger.info("Login successful! Session saved.")
                    return True

            if elapsed % 30 == 0:
                logger.info(f"Waiting for login... ({elapsed}s elapsed)")

        logger.error("Login timeout - please try again")
        return False

    def ensure_logged_in(self, force_relogin: bool = False) -> bool:
        """
        Ensure user is logged in, using saved session or prompting for login.

        Args:
            force_relogin: If True, clear session and force new login

        Returns:
            True if logged in successfully
        """
        if force_relogin:
            logger.info("Forcing re-login - clearing saved session...")
            # Delete session cookies file
            cookies_file = Path(self.profile_dir) / "Default" / "Cookies"
            if cookies_file.exists():
                # Can't delete while Chrome is running, so just proceed
                pass

        if self._is_logged_in():
            logger.info("Already logged in - using saved session")
            return True

        logger.info("Not logged in - manual login required")
        return self._wait_for_manual_login()

    def _get_profile_url(self) -> Optional[str]:
        """Get the current user's profile URL."""
        try:
            # Look for profile link in the feed sidebar
            profile_link = self.driver.find_element(
                By.CSS_SELECTOR,
                'a.app-aware-link[href*="/in/"]'
            )
            href = profile_link.get_attribute('href')
            if href and '/in/' in href:
                # Extract just the profile part
                match = re.search(r'(https://www\.linkedin\.com/in/[^/?]+)', href)
                if match:
                    return match.group(1)
        except NoSuchElementException:
            pass

        # Alternative: check the nav
        try:
            nav_profile = self.driver.find_element(
                By.CSS_SELECTOR,
                'a[href*="/in/"][data-control-name="identity_profile_photo"]'
            )
            return nav_profile.get_attribute('href').split('?')[0]
        except NoSuchElementException:
            pass

        return None

    def _navigate_to_activity(self, profile_url: str) -> bool:
        """Navigate to user's activity/posts page."""
        activity_url = f"{profile_url}/recent-activity/all/"
        logger.info(f"Navigating to: {activity_url}")

        self.driver.get(activity_url)
        time.sleep(3)

        # Wait for posts to load
        posts = self._wait_for_element(
            self.SELECTORS['post_container'],
            timeout=10
        )

        return posts is not None

    def _scroll_and_load_posts(self) -> List[any]:
        """
        Scroll the page to load lazy-loaded posts.
        Stops when reaching posts older than cutoff date.

        Returns:
            List of post elements
        """
        logger.info(f"Loading posts from last {self.days_back} days...")
        logger.info(f"Cutoff date: {self.cutoff_date.strftime('%Y-%m-%d')}")

        all_posts = []
        seen_post_ids = set()
        consecutive_old_posts = 0
        max_consecutive_old = 5  # Stop after seeing 5 consecutive old posts
        scroll_count = 0
        max_scrolls = 100  # Safety limit

        while scroll_count < max_scrolls and consecutive_old_posts < max_consecutive_old:
            scroll_count += 1

            # Get current posts
            try:
                posts = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    self.SELECTORS['post_container']
                )
            except Exception as e:
                logger.warning(f"Error finding posts: {e}")
                break

            new_posts_this_scroll = 0

            for post in posts:
                try:
                    # Generate a unique ID for this post
                    post_id = post.get_attribute('data-urn') or hash(post.text[:100] if post.text else str(time.time()))

                    if post_id in seen_post_ids:
                        continue

                    seen_post_ids.add(post_id)
                    new_posts_this_scroll += 1

                    # Check post date
                    post_date = self._extract_post_date(post)
                    if post_date and post_date < self.cutoff_date:
                        consecutive_old_posts += 1
                        logger.debug(f"Found old post from {post_date.strftime('%Y-%m-%d')}")
                    else:
                        consecutive_old_posts = 0
                        all_posts.append(post)

                except StaleElementReferenceException:
                    continue

            logger.info(f"Scroll {scroll_count}: Found {len(all_posts)} posts in date range, {new_posts_this_scroll} new this scroll")

            if new_posts_this_scroll == 0:
                # No new posts loaded, might be at the end
                consecutive_old_posts += 1

            if consecutive_old_posts >= max_consecutive_old:
                logger.info("Reached posts older than cutoff date - stopping scroll")
                break

            # Scroll down
            self._scroll_page()

            # Wait for new content to load
            time.sleep(2)

            # Additional wait for dynamic content
            self._wait_for_posts_to_load()

        logger.info(f"Total posts found in date range: {len(all_posts)}")
        return all_posts

    def _scroll_page(self):
        """Scroll the page down to load more content."""
        # Scroll using multiple methods for reliability
        try:
            # Method 1: Scroll to bottom of current content
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(0.5)

            # Method 2: Scroll a fixed amount
            self.driver.execute_script(
                "window.scrollBy(0, 1000);"
            )
        except Exception as e:
            logger.warning(f"Scroll error: {e}")

    def _wait_for_posts_to_load(self):
        """Wait for new posts to load after scrolling."""
        try:
            # Wait for loading spinner to disappear
            WebDriverWait(self.driver, 5).until_not(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    'div.artdeco-loader'
                ))
            )
        except TimeoutException:
            pass  # No spinner found, continue

        # Brief pause to ensure content renders
        time.sleep(1)

    def _extract_post_date(self, post_element) -> Optional[datetime]:
        """Extract the publication date from a post element."""
        try:
            # Try multiple selectors for date/time
            date_selectors = [
                'span.update-components-actor__sub-description',
                'span.feed-shared-actor__sub-description',
                'time',
                'span[class*="time"]',
            ]

            for selector in date_selectors:
                try:
                    date_elem = post_element.find_element(By.CSS_SELECTOR, selector)
                    date_text = date_elem.text.strip()
                    if date_text:
                        return self._parse_relative_date(date_text)
                except NoSuchElementException:
                    continue

        except Exception as e:
            logger.debug(f"Error extracting date: {e}")

        return None

    def _parse_relative_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse LinkedIn's relative date format (e.g., "2d", "1w", "3mo").
        """
        date_text = date_text.lower().strip()
        now = datetime.now()

        # Remove common prefixes
        date_text = date_text.replace('edited', '').replace('•', '').strip()

        try:
            # Just now, seconds, minutes
            if any(x in date_text for x in ['now', 'just', 'second', 'sec']):
                return now

            # Hours
            match = re.search(r'(\d+)\s*h', date_text)
            if match:
                hours = int(match.group(1))
                return now - timedelta(hours=hours)

            # Days
            match = re.search(r'(\d+)\s*d', date_text)
            if match:
                days = int(match.group(1))
                return now - timedelta(days=days)

            # Weeks
            match = re.search(r'(\d+)\s*w', date_text)
            if match:
                weeks = int(match.group(1))
                return now - timedelta(weeks=weeks)

            # Months
            match = re.search(r'(\d+)\s*mo', date_text)
            if match:
                months = int(match.group(1))
                return now - timedelta(days=months * 30)

            # Years
            match = re.search(r'(\d+)\s*y', date_text)
            if match:
                years = int(match.group(1))
                return now - timedelta(days=years * 365)

        except Exception as e:
            logger.debug(f"Error parsing date '{date_text}': {e}")

        return None

    def _expand_see_more(self, post_element):
        """Click 'see more' button to expand truncated content."""
        try:
            see_more_buttons = post_element.find_elements(
                By.CSS_SELECTOR,
                self.SELECTORS['see_more_button']
            )

            for btn in see_more_buttons:
                try:
                    if btn.is_displayed() and 'more' in btn.text.lower():
                        # Scroll button into view
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block: 'center'});",
                            btn
                        )
                        time.sleep(0.3)
                        btn.click()
                        time.sleep(0.5)
                except (ElementClickInterceptedException, StaleElementReferenceException):
                    continue

        except Exception as e:
            logger.debug(f"Error expanding content: {e}")

    def _extract_post_content(self, post_element) -> str:
        """
        Extract full post content including hashtags.
        Handles 'see more' expansion.
        """
        # First, try to expand the content
        self._expand_see_more(post_element)

        content = ""

        try:
            # Try multiple selectors for content
            content_selectors = [
                'div.feed-shared-update-v2__description span.break-words',
                'div.feed-shared-text span.break-words',
                'div.feed-shared-update-v2__description',
                'span.break-words',
            ]

            for selector in content_selectors:
                try:
                    content_elem = post_element.find_element(By.CSS_SELECTOR, selector)
                    content = content_elem.text.strip()
                    if content:
                        break
                except NoSuchElementException:
                    continue

            # If still empty, get all text from the post
            if not content:
                content = post_element.text

            # Clean up but preserve hashtags and line breaks
            content = self._clean_content(content)

        except Exception as e:
            logger.debug(f"Error extracting content: {e}")

        return content

    def _clean_content(self, content: str) -> str:
        """Clean up content while preserving hashtags and meaningful line breaks."""
        if not content:
            return ""

        # Remove reaction counts and other UI elements
        lines = content.split('\n')
        cleaned_lines = []

        skip_patterns = [
            r'^\d+$',  # Just numbers
            r'^Like$', r'^Comment$', r'^Repost$', r'^Send$',
            r'^\d+ comments?$', r'^\d+ reposts?$',
            r'^Load more comments',
        ]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            skip = False
            for pattern in skip_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    skip = True
                    break

            if not skip:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _extract_post_url(self, post_element) -> str:
        """Extract the permanent URL for a post."""
        try:
            # Look for activity link
            link_selectors = [
                'a[href*="/feed/update/"]',
                'a[href*="/posts/"]',
                'a.app-aware-link[href*="activity"]',
            ]

            for selector in link_selectors:
                try:
                    link = post_element.find_element(By.CSS_SELECTOR, selector)
                    href = link.get_attribute('href')
                    if href:
                        # Clean up the URL
                        return href.split('?')[0]
                except NoSuchElementException:
                    continue

        except Exception as e:
            logger.debug(f"Error extracting URL: {e}")

        return ""

    def _extract_engagement_metrics(self, post_element) -> Tuple[int, int, int, int]:
        """
        Extract engagement metrics: likes, comments, reposts, impressions.
        Returns tuple: (likes, comments, reposts, impressions)
        """
        likes = 0
        comments = 0
        reposts = 0
        impressions = 0

        try:
            # Extract reactions (likes)
            try:
                reactions = post_element.find_element(
                    By.CSS_SELECTOR,
                    'span.social-details-social-counts__reactions-count'
                )
                likes = self._parse_count(reactions.text)
            except NoSuchElementException:
                pass

            # Extract comments count
            try:
                comments_elem = post_element.find_element(
                    By.CSS_SELECTOR,
                    'button[aria-label*="comment"]'
                )
                aria_label = comments_elem.get_attribute('aria-label') or ""
                match = re.search(r'(\d+)', aria_label)
                if match:
                    comments = int(match.group(1))
            except NoSuchElementException:
                pass

            # Extract reposts count
            try:
                reposts_elem = post_element.find_element(
                    By.CSS_SELECTOR,
                    'button[aria-label*="repost"]'
                )
                aria_label = reposts_elem.get_attribute('aria-label') or ""
                match = re.search(r'(\d+)', aria_label)
                if match:
                    reposts = int(match.group(1))
            except NoSuchElementException:
                pass

            # Impressions are usually only visible to post owner
            # Try to find them in the post metadata
            try:
                impressions_elem = post_element.find_element(
                    By.CSS_SELECTOR,
                    'span[class*="impressions"], span[class*="views"]'
                )
                impressions = self._parse_count(impressions_elem.text)
            except NoSuchElementException:
                pass

        except Exception as e:
            logger.debug(f"Error extracting metrics: {e}")

        return likes, comments, reposts, impressions

    def _parse_count(self, text: str) -> int:
        """Parse count text like '1.2K' or '500' into integer."""
        if not text:
            return 0

        text = text.strip().lower().replace(',', '')

        try:
            # Handle K (thousands)
            if 'k' in text:
                num = float(text.replace('k', ''))
                return int(num * 1000)

            # Handle M (millions)
            if 'm' in text:
                num = float(text.replace('m', ''))
                return int(num * 1000000)

            # Plain number
            return int(float(text))

        except ValueError:
            return 0

    def _extract_post_data(self, post_element) -> Optional[LinkedInPost]:
        """Extract all data from a single post element."""
        try:
            post_url = self._extract_post_url(post_element)
            post_date = self._extract_post_date(post_element)
            content = self._extract_post_content(post_element)
            likes, comments, reposts, impressions = self._extract_engagement_metrics(post_element)

            # Generate post ID from URL or content hash
            if post_url:
                post_id = post_url.split('/')[-1].split('?')[0]
            else:
                post_id = str(hash(content[:100] if content else str(time.time())))

            return LinkedInPost(
                post_id=post_id,
                post_url=post_url,
                publish_date=post_date.strftime('%Y-%m-%d %H:%M:%S') if post_date else "",
                full_content=content,
                likes=likes,
                comments=comments,
                reposts=reposts,
                impressions=impressions,
                scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )

        except Exception as e:
            logger.error(f"Error extracting post data: {e}")
            return None

    def scrape_posts(self, force_relogin: bool = False) -> List[LinkedInPost]:
        """
        Main method to scrape LinkedIn posts.

        Args:
            force_relogin: Force a new login even if session exists

        Returns:
            List of LinkedInPost objects
        """
        try:
            # Initialize browser
            logger.info("Starting Chrome browser...")
            self.driver = self._create_driver()

            # Ensure logged in
            if not self.ensure_logged_in(force_relogin):
                logger.error("Failed to log in to LinkedIn")
                return []

            # Get profile URL
            logger.info("Finding your profile...")
            profile_url = self._get_profile_url()

            if not profile_url:
                logger.error("Could not find profile URL. Please navigate to your profile manually.")
                # Fallback: ask user to provide it
                logger.info("Trying alternative method...")
                # Navigate to 'me' which redirects to actual profile
                self.driver.get("https://www.linkedin.com/in/me/recent-activity/all/")
                time.sleep(3)
                profile_url = self.driver.current_url.split('/recent-activity')[0]

            logger.info(f"Profile URL: {profile_url}")

            # Navigate to activity page
            if not self._navigate_to_activity(profile_url):
                logger.error("Failed to load activity page")
                return []

            # Scroll and load posts
            post_elements = self._scroll_and_load_posts()

            if not post_elements:
                logger.warning("No posts found in the specified date range")
                return []

            # Extract data from each post
            logger.info(f"Extracting data from {len(post_elements)} posts...")

            for i, post_elem in enumerate(post_elements, 1):
                logger.info(f"Processing post {i}/{len(post_elements)}...")

                post_data = self._extract_post_data(post_elem)
                if post_data:
                    self.posts.append(post_data)
                    logger.debug(f"  - Content preview: {post_data.full_content[:100]}...")

            logger.info(f"Successfully scraped {len(self.posts)} posts")
            return self.posts

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            raise

        finally:
            # Don't close the browser if we needed to login
            # so the session is properly saved
            if self.driver:
                logger.info("Closing browser...")
                time.sleep(1)
                self.driver.quit()

    def save_to_json(self, filepath: str = "scraped_posts.json"):
        """Save scraped posts to a JSON file."""
        data = {
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'days_back': self.days_back,
            'total_posts': len(self.posts),
            'posts': [post.to_dict() for post in self.posts]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.posts)} posts to {filepath}")
        return filepath


def main():
    """Main entry point for the scraper."""
    parser = argparse.ArgumentParser(
        description='LinkedIn Post Scraper with session persistence',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  First run (login required):
    python linkedin_scraper.py --days 30

  Subsequent runs (session reused):
    python linkedin_scraper.py --days 60

  Force re-login:
    python linkedin_scraper.py --days 30 --relogin

  Save to custom file:
    python linkedin_scraper.py --days 30 --output my_posts.json
        """
    )

    parser.add_argument(
        '--days',
        type=int,
        default=30,
        choices=[30, 60],
        help='Number of days to look back (30 or 60)'
    )

    parser.add_argument(
        '--relogin',
        action='store_true',
        help='Force re-login (ignore saved session)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (not recommended for first login)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='scraped_posts.json',
        help='Output JSON file path'
    )

    parser.add_argument(
        '--profile-dir',
        type=str,
        default=None,
        help='Chrome profile directory for session storage'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create scraper
    scraper = LinkedInScraper(
        profile_dir=args.profile_dir,
        headless=args.headless,
        days_back=args.days
    )

    # Run scraper
    try:
        posts = scraper.scrape_posts(force_relogin=args.relogin)

        if posts:
            # Save results
            scraper.save_to_json(args.output)

            # Print summary
            print("\n" + "=" * 60)
            print("SCRAPING COMPLETE")
            print("=" * 60)
            print(f"Posts scraped: {len(posts)}")
            print(f"Output file: {args.output}")
            print("=" * 60)

            # Show preview of first post
            if posts:
                print("\nFirst post preview:")
                first = posts[0]
                print(f"  Date: {first.publish_date}")
                print(f"  Likes: {first.likes}")
                print(f"  Content: {first.full_content[:200]}...")
        else:
            print("\nNo posts found in the specified date range.")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nScraping cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
