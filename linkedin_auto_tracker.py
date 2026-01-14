#!/usr/bin/env python3
"""
LinkedIn Automated Tracker
Automatically fetches and tracks LinkedIn post engagement
"""

import os
import schedule
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

from linkedin_api import LinkedInAPIClient, LinkedInAuthHelper
from linkedin_tracker import LinkedInTracker
from engagement_analyzer import EngagementAnalyzer


class AutomatedLinkedInTracker:
    """Automated tracker that fetches data from LinkedIn API"""

    def __init__(self, check_interval_hours: int = 6):
        """
        Initialize automated tracker

        Args:
            check_interval_hours: How often to check for updates (default: 6 hours)
        """
        load_dotenv()

        self.check_interval = check_interval_hours
        self.tracker = LinkedInTracker()
        self.api_client = None
        self.user_urn = None
        self.last_check = None
        self.config_file = Path("automation_config.json")
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load automation configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)

        return {
            'check_interval_hours': 6,
            'max_posts_to_fetch': 50,
            'enable_notifications': False,
            'last_run': None
        }

    def _save_config(self):
        """Save automation configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def initialize_api_client(self) -> bool:
        """
        Initialize LinkedIn API client with credentials

        Returns:
            True if successful, False otherwise
        """
        # Check if token is expired
        if LinkedInAuthHelper.is_token_expired():
            print("❌ LinkedIn access token is expired or missing")
            print("Please run: python linkedin_auth_setup.py")
            return False

        # Load access token
        access_token = LinkedInAuthHelper.load_credentials()

        if not access_token:
            print("❌ No LinkedIn access token found")
            print("Please run: python linkedin_auth_setup.py")
            return False

        self.api_client = LinkedInAPIClient(access_token)

        # Test connection and get user URN
        try:
            profile = self.api_client.get_user_profile()
            self.user_urn = profile.get('id', '')
            print(f"✅ Connected to LinkedIn API")
            print(f"👤 Authenticated as: {profile.get('localizedFirstName', '')} {profile.get('localizedLastName', '')}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to LinkedIn API: {e}")
            print("Please check your credentials and try again")
            return False

    def sync_posts(self) -> Dict:
        """
        Fetch latest posts from LinkedIn and sync with local database

        Returns:
            Summary of sync operation
        """
        if not self.api_client:
            raise Exception("API client not initialized. Call initialize_api_client() first.")

        print("\n" + "=" * 60)
        print("🔄 SYNCING WITH LINKEDIN")
        print("=" * 60)

        try:
            # Fetch posts from LinkedIn
            print(f"\n📥 Fetching posts from LinkedIn...")
            posts = self.api_client.fetch_all_posts_with_metrics(self.user_urn)
            print(f"✅ Fetched {len(posts)} posts")

            new_posts = 0
            updated_posts = 0
            errors = 0

            # Sync each post
            for post in posts:
                try:
                    post_id = self._get_post_id_from_urn(post['urn'])

                    # Check if post exists in local database
                    if post_id not in self.tracker.posts:
                        # Add new post
                        self._add_post_to_tracker(post_id, post)
                        new_posts += 1
                    else:
                        # Update existing post with new metrics
                        self._update_post_metrics(post_id, post)
                        updated_posts += 1

                except Exception as e:
                    print(f"❌ Error syncing post: {e}")
                    errors += 1

            # Update config
            self.config['last_run'] = datetime.now().isoformat()
            self._save_config()

            summary = {
                'total_posts': len(posts),
                'new_posts': new_posts,
                'updated_posts': updated_posts,
                'errors': errors,
                'timestamp': datetime.now().isoformat()
            }

            self._print_sync_summary(summary)

            return summary

        except Exception as e:
            print(f"\n❌ Sync failed: {e}")
            raise

    def _get_post_id_from_urn(self, urn: str) -> str:
        """Extract post ID from URN"""
        # Use last part of URN as post ID
        return urn.split(':')[-1][-8:]

    def _add_post_to_tracker(self, post_id: str, post_data: Dict):
        """Add new post to tracker"""
        # Extract title (first 100 chars of text)
        title = post_data['text'][:100] if post_data['text'] else "Untitled post"

        post_entry = {
            'title': title,
            'content': post_data['text'],
            'type': post_data['type'],
            'url': post_data['url'],
            'created_at': post_data['created_at'],
            'urn': post_data['urn'],
            'engagement_history': []
        }

        # Add initial metrics
        metrics = post_data['metrics']
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'likes': metrics['likes'],
            'comments': metrics['comments'],
            'shares': metrics['shares'],
            'views': metrics['views']
        }
        post_entry['engagement_history'].append(snapshot)

        # Save to tracker
        self.tracker.posts[post_id] = post_entry
        self.tracker._save_posts()

        print(f"  ✅ Added new post: {title[:50]}...")

    def _update_post_metrics(self, post_id: str, post_data: Dict):
        """Update metrics for existing post"""
        metrics = post_data['metrics']

        # Check if metrics have changed
        latest_metrics = self.tracker.posts[post_id]['engagement_history'][-1] if \
            self.tracker.posts[post_id]['engagement_history'] else None

        if latest_metrics:
            # Only add new snapshot if metrics changed
            if (metrics['likes'] != latest_metrics.get('likes', 0) or
                metrics['comments'] != latest_metrics.get('comments', 0) or
                metrics['shares'] != latest_metrics.get('shares', 0) or
                metrics['views'] != latest_metrics.get('views', 0)):

                snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'likes': metrics['likes'],
                    'comments': metrics['comments'],
                    'shares': metrics['shares'],
                    'views': metrics['views']
                }
                self.tracker.posts[post_id]['engagement_history'].append(snapshot)
                self.tracker._save_posts()

                print(f"  📊 Updated: {self.tracker.posts[post_id]['title'][:50]}...")

    def _print_sync_summary(self, summary: Dict):
        """Print sync summary"""
        print("\n" + "=" * 60)
        print("✅ SYNC COMPLETE")
        print("=" * 60)
        print(f"\n📊 Results:")
        print(f"   Total posts fetched: {summary['total_posts']}")
        print(f"   New posts added: {summary['new_posts']}")
        print(f"   Posts updated: {summary['updated_posts']}")
        if summary['errors'] > 0:
            print(f"   ⚠️  Errors: {summary['errors']}")
        print(f"\n🕐 Last sync: {summary['timestamp']}")

    def run_once(self):
        """Run sync once"""
        if not self.initialize_api_client():
            return False

        self.sync_posts()
        return True

    def start_monitoring(self):
        """Start continuous monitoring with scheduled updates"""
        print("=" * 60)
        print("🤖 LINKEDIN AUTOMATED TRACKER")
        print("=" * 60)
        print(f"\n⚙️  Configuration:")
        print(f"   Check interval: Every {self.check_interval} hours")
        print(f"   Max posts to fetch: {self.config.get('max_posts_to_fetch', 50)}")

        if not self.initialize_api_client():
            print("\n❌ Failed to start monitoring. Please set up authentication first.")
            return

        # Initial sync
        print("\n🚀 Running initial sync...")
        self.sync_posts()

        # Schedule periodic syncs
        schedule.every(self.check_interval).hours.do(self.sync_posts)

        print(f"\n✅ Monitoring started!")
        print(f"📅 Next sync in {self.check_interval} hours")
        print(f"\nPress Ctrl+C to stop\n")

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping automated tracker...")
            print("👋 Goodbye!")

    def show_status(self):
        """Show current monitoring status"""
        print("=" * 60)
        print("📊 AUTOMATED TRACKER STATUS")
        print("=" * 60)

        if self.config.get('last_run'):
            last_run = datetime.fromisoformat(self.config['last_run'])
            print(f"\n🕐 Last sync: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")

            time_since = datetime.now() - last_run
            hours = time_since.total_seconds() / 3600
            print(f"   ({hours:.1f} hours ago)")
        else:
            print("\n⚠️  No sync has been run yet")

        print(f"\n⚙️  Configuration:")
        print(f"   Check interval: {self.config.get('check_interval_hours', 6)} hours")
        print(f"   Max posts: {self.config.get('max_posts_to_fetch', 50)}")

        # Show tracked posts count
        print(f"\n📝 Tracked posts: {len(self.tracker.posts)}")

        # Show API status
        if self.initialize_api_client():
            print("✅ API connection: OK")
        else:
            print("❌ API connection: Not configured")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='LinkedIn Automated Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run sync once
  python linkedin_auto_tracker.py --sync

  # Start continuous monitoring (check every 6 hours)
  python linkedin_auto_tracker.py --monitor

  # Start monitoring with custom interval
  python linkedin_auto_tracker.py --monitor --interval 12

  # Show status
  python linkedin_auto_tracker.py --status
        """
    )

    parser.add_argument('--sync', action='store_true',
                       help='Run sync once and exit')
    parser.add_argument('--monitor', action='store_true',
                       help='Start continuous monitoring')
    parser.add_argument('--status', action='store_true',
                       help='Show monitoring status')
    parser.add_argument('--interval', type=int, default=6,
                       help='Check interval in hours (default: 6)')

    args = parser.parse_args()

    tracker = AutomatedLinkedInTracker(check_interval_hours=args.interval)

    if args.sync:
        tracker.run_once()
    elif args.monitor:
        tracker.start_monitoring()
    elif args.status:
        tracker.show_status()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
