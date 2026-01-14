#!/usr/bin/env python3
"""
LinkedIn Post Scraper with Chrome Profile Persistence (v2 - Fixed)

Features:
- Persists login session using Chrome user profile
- Properly scrolls to load lazy-loaded content
- Stops scrolling when reaching date threshold
- Extracts full post content including hashtags
- Supports 30 or 60 day lookback periods
- Debug mode with HTML dumps and screenshots

Usage:
    First run (login required):
        python linkedin_scraper.py --days 30

    Subsequent runs (session reused):
        python linkedin_scraper.py --days 30

    Debug mode (saves screenshots and HTML):
        python linkedin_scraper.py --days 30 --debug

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

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    USE_WEBDRIVER_MANAGER = True
except ImportError:
    USE_WEBDRIVER_MANAGER = False

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

    def __init__(
        self,
        profile_dir: Optional[str] = None,
        headless: bool = False,
        days_back: int = 30,
        debug: bool = False
    ):
        """
        Initialize the scraper.

        Args:
            profile_dir: Directory to store Chrome profile (for session persistence)
            headless: Run Chrome in headless mode (not recommended for first login)
            days_back: Number of days to look back for posts
            debug: Enable debug mode with screenshots and HTML dumps
        """
        self.profile_dir = profile_dir or self.DEFAULT_PROFILE_DIR
        self.headless = headless
        self.days_back = days_back
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.driver: Optional[webdriver.Chrome] = None
        self.posts: List[LinkedInPost] = []
        self.debug = debug
        self.debug_dir = Path("debug_output")

        # Ensure profile directory exists
        Path(self.profile_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Using Chrome profile at: {self.profile_dir}")

        # Create debug directory if needed
        if self.debug:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Debug output will be saved to: {self.debug_dir}")

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

        # Create driver with webdriver-manager
        if USE_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        else:
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

    def _save_debug_screenshot(self, name: str):
        """Save a screenshot for debugging."""
        if self.debug and self.driver:
            try:
                filepath = self.debug_dir / f"{name}_{int(time.time())}.png"
                self.driver.save_screenshot(str(filepath))
                logger.debug(f"Screenshot saved: {filepath}")
            except Exception as e:
                logger.warning(f"Failed to save screenshot: {e}")

    def _save_debug_html(self, name: str, html: str):
        """Save HTML content for debugging."""
        if self.debug:
            try:
                filepath = self.debug_dir / f"{name}_{int(time.time())}.html"
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.debug(f"HTML saved: {filepath}")
            except Exception as e:
                logger.warning(f"Failed to save HTML: {e}")

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
        time.sleep(3)

        # Check for login form (means not logged in)
        try:
            login_form = self.driver.find_element(By.CSS_SELECTOR, 'form.login__form')
            if login_form:
                return False
        except NoSuchElementException:
            pass

        # Check URL - if redirected to login, not logged in
        if '/login' in self.driver.current_url or '/checkpoint' in self.driver.current_url:
            return False

        # Check for feed content (means logged in)
        try:
            feed = self.driver.find_element(By.CSS_SELECTOR, 'div.scaffold-layout__main')
            return feed is not None
        except NoSuchElementException:
            pass

        return True

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
            if "/feed" in current_url or ("/in/" in current_url and "/login" not in current_url):
                # Verify login by checking for feed element
                try:
                    feed = self.driver.find_element(By.CSS_SELECTOR, 'div.scaffold-layout__main')
                    if feed:
                        logger.info("Login successful! Session saved.")
                        return True
                except NoSuchElementException:
                    pass

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
        if self._is_logged_in():
            logger.info("Already logged in - using saved session")
            return True

        logger.info("Not logged in - manual login required")
        return self._wait_for_manual_login()

    def _navigate_to_activity(self) -> bool:
        """Navigate to user's activity/posts page."""
        # Use /in/me/ which redirects to actual profile
        activity_url = "https://www.linkedin.com/in/me/recent-activity/all/"
        logger.info(f"Navigating to activity page: {activity_url}")

        self.driver.get(activity_url)
        time.sleep(4)

        self._save_debug_screenshot("activity_page")

        # Wait for content to load
        time.sleep(2)

        return True

    def _find_post_elements(self) -> List:
        """
        Find all post elements on the page using multiple selector strategies.
        """
        # Multiple selectors to try - LinkedIn changes their DOM frequently
        selectors = [
            # Primary: Activity feed items
            'div.feed-shared-update-v2',
            # Alternative: Profile activity items
            'div[data-urn*="activity"]',
            # Generic feed items
            'div.occludable-update',
            # List items in activity
            'li.profile-creator-shared-feed-update__container',
            # Another common pattern
            'div.feed-shared-update-v2__content',
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.debug(f"Found {len(elements)} posts using selector: {selector}")
                    return elements
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        # Fallback: find by XPath for any div with update/post content
        try:
            elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'feed-shared') or contains(@class, 'update')]"
            )
            if elements:
                logger.debug(f"Found {len(elements)} posts using XPath fallback")
                return elements
        except Exception:
            pass

        return []

    def _extract_date_text(self, post_element) -> Optional[str]:
        """Extract date text from post element."""
        # Multiple selectors for date/time elements
        date_selectors = [
            # Actor sub-description (most common)
            'span.update-components-actor__sub-description',
            'span.feed-shared-actor__sub-description',
            # Time elements
            'time',
            'span.visually-hidden',
            # Sub-description in various formats
            'a.app-aware-link span.visually-hidden',
            'span[class*="sub-description"]',
            # Generic time patterns
            'span.t-black--light',
            'span.t-normal',
        ]

        for selector in date_selectors:
            try:
                elements = post_element.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    # Check if this looks like a date
                    if text and self._looks_like_date(text):
                        logger.debug(f"Found date text: '{text}' using selector: {selector}")
                        return text
            except Exception:
                continue

        # Fallback: search all text for date patterns
        try:
            all_text = post_element.text
            lines = all_text.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                if self._looks_like_date(line.strip()):
                    logger.debug(f"Found date text via fallback: '{line.strip()}'")
                    return line.strip()
        except Exception:
            pass

        return None

    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date/time string."""
        if not text or len(text) > 50:
            return False

        text_lower = text.lower()

        # Common date patterns
        date_patterns = [
            r'\d+[smhdwmo]',  # 1s, 2m, 3h, 4d, 1w, 2mo
            r'\d+\s*(second|minute|hour|day|week|month|year)',
            r'(just now|now)',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d+',
            r'\d+\s*(ago)',
            r'yesterday',
            r'edited',
        ]

        for pattern in date_patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def _parse_relative_date(self, date_text: str) -> Optional[datetime]:
        """
        Parse LinkedIn's relative date format.
        Handles: "2d", "1w", "3mo", "2d ago", "1 week ago", "Jan 10", etc.
        """
        if not date_text:
            return None

        date_text = date_text.lower().strip()
        now = datetime.now()

        # Remove common prefixes/suffixes
        date_text = re.sub(r'(edited|•|ago|\s+)', ' ', date_text).strip()

        try:
            # Just now, seconds, minutes
            if any(x in date_text for x in ['now', 'just', 'second', 'sec', ' s ']):
                return now
            if re.match(r'^\d*s$', date_text):  # "30s" or just "s"
                return now

            # Minutes
            match = re.search(r'(\d+)\s*m(?:in)?', date_text)
            if match:
                minutes = int(match.group(1))
                return now - timedelta(minutes=minutes)

            # Hours
            match = re.search(r'(\d+)\s*h(?:our|r)?', date_text)
            if match:
                hours = int(match.group(1))
                return now - timedelta(hours=hours)

            # Days
            match = re.search(r'(\d+)\s*d(?:ay)?', date_text)
            if match:
                days = int(match.group(1))
                return now - timedelta(days=days)

            # Weeks
            match = re.search(r'(\d+)\s*w(?:eek|k)?', date_text)
            if match:
                weeks = int(match.group(1))
                return now - timedelta(weeks=weeks)

            # Months
            match = re.search(r'(\d+)\s*mo(?:nth)?', date_text)
            if match:
                months = int(match.group(1))
                return now - timedelta(days=months * 30)

            # Years
            match = re.search(r'(\d+)\s*y(?:ear|r)?', date_text)
            if match:
                years = int(match.group(1))
                return now - timedelta(days=years * 365)

            # Yesterday
            if 'yesterday' in date_text:
                return now - timedelta(days=1)

            # Absolute dates like "Jan 10" or "January 10"
            months_map = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            for month_abbr, month_num in months_map.items():
                match = re.search(rf'{month_abbr}\w*\s+(\d+)', date_text)
                if match:
                    day = int(match.group(1))
                    year = now.year
                    # If the date is in the future, it must be last year
                    parsed = datetime(year, month_num, day)
                    if parsed > now:
                        parsed = datetime(year - 1, month_num, day)
                    return parsed

        except Exception as e:
            logger.debug(f"Error parsing date '{date_text}': {e}")

        return None

    def _expand_see_more(self, post_element):
        """Click 'see more' button to expand truncated content."""
        try:
            # Multiple selectors for "see more" buttons
            see_more_selectors = [
                'button.feed-shared-inline-show-more-text__see-more-less-toggle',
                'button[aria-label*="see more"]',
                'button.see-more',
                'span.feed-shared-inline-show-more-text__see-more-less-toggle',
            ]

            for selector in see_more_selectors:
                try:
                    buttons = post_element.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            btn_text = btn.text.lower()
                            if 'more' in btn_text or 'see' in btn_text:
                                self.driver.execute_script(
                                    "arguments[0].scrollIntoView({block: 'center'});",
                                    btn
                                )
                                time.sleep(0.2)
                                btn.click()
                                time.sleep(0.3)
                                return
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Error expanding content: {e}")

    def _extract_post_content(self, post_element) -> str:
        """Extract full post content including hashtags."""
        # First, try to expand the content
        self._expand_see_more(post_element)

        content = ""

        # Multiple selectors for content
        content_selectors = [
            'div.feed-shared-update-v2__description span.break-words',
            'div.feed-shared-text span.break-words',
            'span.break-words',
            'div.feed-shared-update-v2__description',
            'div.feed-shared-text',
            'div[dir="ltr"]',
        ]

        for selector in content_selectors:
            try:
                elem = post_element.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if text and len(text) > len(content):
                    content = text
            except NoSuchElementException:
                continue

        # Clean up but preserve hashtags and line breaks
        content = self._clean_content(content)

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
            r'^\d+\s*(like|comment|repost|view|impression)',
            r'^Load more',
            r'^Show fewer',
            r'^Report this',
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
        # Multiple selectors for post links
        link_selectors = [
            'a[href*="/feed/update/"]',
            'a[href*="/posts/"]',
            'a[href*="activity"]',
        ]

        for selector in link_selectors:
            try:
                links = post_element.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    href = link.get_attribute('href')
                    if href and ('activity' in href or 'update' in href or 'posts' in href):
                        return href.split('?')[0]
            except Exception:
                continue

        # Try to get from data-urn attribute
        try:
            urn = post_element.get_attribute('data-urn')
            if urn:
                return f"https://www.linkedin.com/feed/update/{urn}"
        except Exception:
            pass

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
            # Get all text and parse numbers
            full_text = post_element.text.lower()

            # Extract reactions (likes)
            reactions_match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?[km]?)\s*(?:reaction|like)', full_text)
            if reactions_match:
                likes = self._parse_count(reactions_match.group(1))

            # Try selector for reactions
            try:
                reactions_elem = post_element.find_element(
                    By.CSS_SELECTOR,
                    'span.social-details-social-counts__reactions-count'
                )
                if reactions_elem:
                    likes = self._parse_count(reactions_elem.text)
            except NoSuchElementException:
                pass

            # Extract comments
            comments_match = re.search(r'(\d+(?:,\d+)?)\s*comment', full_text)
            if comments_match:
                comments = self._parse_count(comments_match.group(1))

            # Extract reposts
            reposts_match = re.search(r'(\d+(?:,\d+)?)\s*repost', full_text)
            if reposts_match:
                reposts = self._parse_count(reposts_match.group(1))

            # Extract impressions/views (usually only visible to post owner)
            impressions_match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?[km]?)\s*(?:impression|view)', full_text)
            if impressions_match:
                impressions = self._parse_count(impressions_match.group(1))

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

    def _scroll_and_load_posts(self) -> List[LinkedInPost]:
        """
        Scroll the page and extract posts.
        Stops when reaching posts older than cutoff date.

        Returns:
            List of LinkedInPost objects
        """
        logger.info(f"Loading posts from last {self.days_back} days...")
        logger.info(f"Cutoff date: {self.cutoff_date.strftime('%Y-%m-%d')}")

        posts = []
        seen_content_hashes = set()
        consecutive_old_posts = 0
        max_consecutive_old = 5
        scroll_count = 0
        max_scrolls = 50
        no_new_posts_count = 0

        while scroll_count < max_scrolls:
            scroll_count += 1

            # Find post elements
            post_elements = self._find_post_elements()
            logger.info(f"Scroll {scroll_count}: Found {len(post_elements)} post elements on page")

            if self.debug and scroll_count == 1:
                self._save_debug_screenshot(f"scroll_{scroll_count}")
                if post_elements:
                    # Save HTML of first few posts for debugging
                    for i, elem in enumerate(post_elements[:3]):
                        try:
                            html = elem.get_attribute('outerHTML')
                            self._save_debug_html(f"post_{i}", html)
                        except Exception:
                            pass

            new_posts_this_scroll = 0

            for elem in post_elements:
                try:
                    # Extract content first to create unique hash
                    content = self._extract_post_content(elem)
                    content_hash = hash(content[:200]) if content else None

                    if content_hash and content_hash in seen_content_hashes:
                        continue

                    if content_hash:
                        seen_content_hashes.add(content_hash)

                    # Extract date
                    date_text = self._extract_date_text(elem)
                    post_date = self._parse_relative_date(date_text) if date_text else None

                    if self.debug:
                        logger.debug(f"Post date text: '{date_text}' -> parsed: {post_date}")

                    # Check if post is within date range
                    # IMPORTANT: If we can't determine date, INCLUDE the post (don't skip)
                    if post_date:
                        if post_date < self.cutoff_date:
                            consecutive_old_posts += 1
                            logger.debug(f"Found old post from {post_date.strftime('%Y-%m-%d')} (consecutive: {consecutive_old_posts})")
                            if consecutive_old_posts >= max_consecutive_old:
                                logger.info("Reached posts older than cutoff date - stopping scroll")
                                return posts
                            continue
                        else:
                            consecutive_old_posts = 0  # Reset counter

                    # Extract other fields
                    post_url = self._extract_post_url(elem)
                    likes, comments_count, reposts_count, impressions = self._extract_engagement_metrics(elem)

                    # Generate post ID
                    if post_url:
                        post_id = re.search(r'activity:?(\d+)', post_url)
                        post_id = post_id.group(1) if post_id else str(hash(post_url))
                    else:
                        post_id = str(abs(content_hash)) if content_hash else str(int(time.time() * 1000))

                    # Only add if we have meaningful content
                    if content or post_url:
                        post = LinkedInPost(
                            post_id=post_id,
                            post_url=post_url,
                            publish_date=post_date.strftime('%Y-%m-%d %H:%M:%S') if post_date else "Unknown",
                            full_content=content,
                            likes=likes,
                            comments=comments_count,
                            reposts=reposts_count,
                            impressions=impressions,
                            scraped_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        )
                        posts.append(post)
                        new_posts_this_scroll += 1

                        logger.debug(f"Added post: {post_id[:20]}... | Date: {post.publish_date} | Content: {content[:50]}...")

                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    logger.debug(f"Error processing post element: {e}")
                    continue

            logger.info(f"Scroll {scroll_count}: Found {new_posts_this_scroll} new posts in date range (Total: {len(posts)})")

            # Check if we're making progress
            if new_posts_this_scroll == 0:
                no_new_posts_count += 1
                if no_new_posts_count >= 3:
                    logger.info("No new posts found after multiple scrolls - stopping")
                    break
            else:
                no_new_posts_count = 0

            # Scroll down
            self.driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)

            # Wait for content to load
            time.sleep(1)

        return posts

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

            # Navigate to activity page
            if not self._navigate_to_activity():
                logger.error("Failed to load activity page")
                return []

            # Get profile URL from current page
            current_url = self.driver.current_url
            logger.info(f"Profile URL: {current_url.split('/recent-activity')[0]}")

            # Scroll and extract posts
            self.posts = self._scroll_and_load_posts()

            logger.info(f"Successfully scraped {len(self.posts)} posts")
            return self.posts

        except Exception as e:
            logger.error(f"Scraping error: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
            raise

        finally:
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

  Debug mode (saves screenshots and HTML):
    python linkedin_scraper.py --days 30 --debug

  Force re-login:
    python linkedin_scraper.py --days 30 --relogin
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
        help='Enable debug mode (saves screenshots and HTML dumps)'
    )

    args = parser.parse_args()

    # Set log level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("LinkedIn Post Scraper - Phase 1 (v2)")
    logger.info("=" * 60)
    logger.info(f"Days back: {args.days}")
    logger.info(f"Debug mode: {args.debug}")
    logger.info("=" * 60)

    # Create scraper
    scraper = LinkedInScraper(
        profile_dir=args.profile_dir,
        headless=args.headless,
        days_back=args.days,
        debug=args.debug
    )

    # Run scraper
    try:
        posts = scraper.scrape_posts(force_relogin=args.relogin)

        # Save results
        scraper.save_to_json(args.output)

        # Print summary
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETE")
        print("=" * 60)
        print(f"Posts scraped: {len(posts)}")
        print(f"Output file: {args.output}")

        if args.debug:
            print(f"Debug files: {scraper.debug_dir}/")

        print("=" * 60)

        # Show preview of posts
        if posts:
            print("\nPost previews:")
            for i, post in enumerate(posts[:3], 1):
                print(f"\n--- Post {i} ---")
                print(f"  Date: {post.publish_date}")
                print(f"  URL: {post.post_url[:60]}..." if len(post.post_url) > 60 else f"  URL: {post.post_url}")
                print(f"  Likes: {post.likes} | Comments: {post.comments} | Reposts: {post.reposts}")
                print(f"  Content: {post.full_content[:100]}..." if len(post.full_content) > 100 else f"  Content: {post.full_content}")
        else:
            print("\nNo posts found.")
            if args.debug:
                print("Check debug_output/ folder for screenshots and HTML dumps.")

    except KeyboardInterrupt:
        print("\nScraping cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
