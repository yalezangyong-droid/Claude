#!/usr/bin/env python3
"""
LinkedIn Post Engagement Tracker
Track and analyze LinkedIn post performance
"""

import json
import os
import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict
from tabulate import tabulate
from engagement_analyzer import EngagementAnalyzer


class LinkedInTracker:
    def __init__(self, data_dir: str = "data"):
        """Initialize tracker with data directory"""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.posts_file = self.data_dir / "posts.json"
        self.config_file = Path("config.json")
        self.posts = self._load_posts()
        self.config = self._load_config()

    def _load_posts(self) -> Dict:
        """Load posts from JSON file"""
        if self.posts_file.exists():
            with open(self.posts_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_posts(self):
        """Save posts to JSON file"""
        with open(self.posts_file, 'w') as f:
            json.dump(self.posts, f, indent=2)

    def _load_config(self) -> Dict:
        """Load configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {
            'timezone': 'UTC',
            'engagement_weights': {
                'likes': 1,
                'comments': 3,
                'shares': 5,
                'views': 0.01
            }
        }

    def _generate_post_id(self) -> str:
        """Generate unique post ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    def add_post(self, title: str, content: str, post_type: str, url: str = None):
        """Add a new post to track"""
        post_id = self._generate_post_id()

        post_data = {
            'title': title,
            'content': content,
            'type': post_type,
            'url': url or '',
            'created_at': datetime.now().isoformat(),
            'engagement_history': []
        }

        self.posts[post_id] = post_data
        self._save_posts()

        print(f"✅ Post added successfully!")
        print(f"📌 Post ID: {post_id}")
        print(f"📝 Title: {title}")
        print(f"🏷️  Type: {post_type}")
        print(f"\nUse this ID to update engagement: python linkedin_tracker.py update {post_id}")

        return post_id

    def update_engagement(self, post_id: str, likes: int = None, comments: int = None,
                         shares: int = None, views: int = None):
        """Update engagement metrics for a post"""
        if post_id not in self.posts:
            print(f"❌ Error: Post ID '{post_id}' not found")
            return False

        # Get current metrics or create new snapshot
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'likes': likes if likes is not None else 0,
            'comments': comments if comments is not None else 0,
            'shares': shares if shares is not None else 0,
            'views': views if views is not None else 0
        }

        self.posts[post_id]['engagement_history'].append(snapshot)
        self._save_posts()

        analyzer = EngagementAnalyzer(self.posts, self.config['engagement_weights'])
        score = analyzer.calculate_engagement_score(snapshot)

        print(f"✅ Engagement updated for post: {self.posts[post_id]['title']}")
        print(f"\n📊 Current Metrics:")
        print(f"   👍 Likes: {snapshot['likes']}")
        print(f"   💬 Comments: {snapshot['comments']}")
        print(f"   🔄 Shares: {snapshot['shares']}")
        print(f"   👁️  Views: {snapshot['views']}")
        print(f"\n🎯 Engagement Score: {score}")

        return True

    def list_posts(self, limit: int = None):
        """List all tracked posts"""
        if not self.posts:
            print("📭 No posts tracked yet. Add your first post with 'add' command.")
            return

        analyzer = EngagementAnalyzer(self.posts, self.config['engagement_weights'])

        table_data = []
        for post_id, post in list(self.posts.items())[:limit] if limit else self.posts.items():
            metrics = analyzer.get_latest_metrics(post)
            score = analyzer.calculate_engagement_score(metrics)
            created = datetime.fromisoformat(post['created_at']).strftime('%Y-%m-%d %H:%M')

            table_data.append([
                post_id,
                post['title'][:40] + '...' if len(post['title']) > 40 else post['title'],
                post['type'],
                created,
                metrics.get('likes', 0),
                metrics.get('comments', 0),
                metrics.get('shares', 0),
                score
            ])

        headers = ['ID', 'Title', 'Type', 'Created', 'Likes', 'Comments', 'Shares', 'Score']
        print("\n📋 Tracked LinkedIn Posts")
        print("=" * 100)
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        print(f"\nTotal posts: {len(self.posts)}")

    def analyze_patterns(self, best_times: bool = False, by_type: bool = False):
        """Analyze engagement patterns"""
        if not self.posts:
            print("📭 No posts to analyze yet. Add some posts first!")
            return

        analyzer = EngagementAnalyzer(self.posts, self.config['engagement_weights'])

        if best_times:
            self._show_best_times(analyzer)
        elif by_type:
            self._show_type_analysis(analyzer)
        else:
            self._show_summary(analyzer)

    def _show_summary(self, analyzer: EngagementAnalyzer):
        """Show overall summary"""
        stats = analyzer.get_summary_stats()

        print("\n" + "=" * 60)
        print("📊 LINKEDIN ENGAGEMENT SUMMARY")
        print("=" * 60)
        print(f"\n📝 Total Posts: {stats['total_posts']}")
        print(f"\n📈 Total Engagement:")
        print(f"   👍 Likes: {stats['total_likes']:,}")
        print(f"   💬 Comments: {stats['total_comments']:,}")
        print(f"   🔄 Shares: {stats['total_shares']:,}")
        print(f"   👁️  Views: {stats['total_views']:,}")
        print(f"\n🎯 Engagement Scores:")
        print(f"   Average: {stats['avg_score']}")
        print(f"   Median: {stats['median_score']}")
        print(f"   Best: {stats['max_score']}")

    def _show_best_times(self, analyzer: EngagementAnalyzer):
        """Show best posting times analysis"""
        time_data = analyzer.analyze_posting_times()

        print("\n" + "=" * 60)
        print("⏰ BEST POSTING TIMES ANALYSIS")
        print("=" * 60)

        # Best hours
        print("\n🕐 Best Hours (based on engagement):")
        hour_items = sorted(time_data['by_hour'].items(),
                          key=lambda x: x[1]['avg_score'], reverse=True)[:5]

        hour_table = []
        for hour, data in hour_items:
            hour_str = f"{hour:02d}:00"
            hour_table.append([hour_str, data['avg_score'], data['count']])

        print(tabulate(hour_table, headers=['Time', 'Avg Score', 'Posts'], tablefmt='grid'))

        # Best days
        print("\n📅 Best Days (based on engagement):")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_table = []

        for day in day_order:
            if day in time_data['by_day']:
                data = time_data['by_day'][day]
                day_table.append([day, data['avg_score'], data['count']])

        day_table.sort(key=lambda x: x[1], reverse=True)
        print(tabulate(day_table, headers=['Day', 'Avg Score', 'Posts'], tablefmt='grid'))

    def _show_type_analysis(self, analyzer: EngagementAnalyzer):
        """Show content type analysis"""
        type_data = analyzer.analyze_by_content_type()

        print("\n" + "=" * 80)
        print("🏷️  CONTENT TYPE PERFORMANCE ANALYSIS")
        print("=" * 80)

        type_table = []
        for content_type, data in sorted(type_data.items(), key=lambda x: x[1]['avg_score'], reverse=True):
            type_table.append([
                content_type.capitalize(),
                data['count'],
                data['avg_likes'],
                data['avg_comments'],
                data['avg_shares'],
                data['avg_views'],
                data['avg_score']
            ])

        headers = ['Type', 'Posts', 'Avg Likes', 'Avg Comments', 'Avg Shares', 'Avg Views', 'Avg Score']
        print(tabulate(type_table, headers=headers, tablefmt='grid'))

    def show_top_posts(self, limit: int = 10):
        """Show top performing posts"""
        if not self.posts:
            print("📭 No posts to analyze yet.")
            return

        analyzer = EngagementAnalyzer(self.posts, self.config['engagement_weights'])
        top_posts = analyzer.get_top_posts(limit)

        print("\n" + "=" * 80)
        print(f"🏆 TOP {min(limit, len(top_posts))} PERFORMING POSTS")
        print("=" * 80)

        table_data = []
        for i, (post_id, post, score) in enumerate(top_posts, 1):
            metrics = analyzer.get_latest_metrics(post)
            table_data.append([
                i,
                post['title'][:50] + '...' if len(post['title']) > 50 else post['title'],
                post['type'],
                metrics.get('likes', 0),
                metrics.get('comments', 0),
                metrics.get('shares', 0),
                score
            ])

        headers = ['Rank', 'Title', 'Type', 'Likes', 'Comments', 'Shares', 'Score']
        print(tabulate(table_data, headers=headers, tablefmt='grid'))

    def export_to_csv(self, output_file: str, report_type: str = 'posts', limit: int = None):
        """Export data to CSV file

        Args:
            output_file: Path to output CSV file
            report_type: Type of report ('posts', 'top', 'summary', 'times', 'types')
            limit: Limit number of records (for top posts)
        """
        if not self.posts:
            print("📭 No posts to export yet.")
            return False

        analyzer = EngagementAnalyzer(self.posts, self.config['engagement_weights'])
        output_path = Path(output_file)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if report_type == 'posts':
                self._export_all_posts(output_path, analyzer)
            elif report_type == 'top':
                self._export_top_posts(output_path, analyzer, limit or 10)
            elif report_type == 'summary':
                self._export_summary(output_path, analyzer)
            elif report_type == 'times':
                self._export_best_times(output_path, analyzer)
            elif report_type == 'types':
                self._export_type_analysis(output_path, analyzer)
            else:
                print(f"❌ Unknown report type: {report_type}")
                return False

            print(f"✅ Report exported successfully to: {output_path}")
            return True

        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")
            return False

    def _export_all_posts(self, output_path: Path, analyzer: EngagementAnalyzer):
        """Export all posts to CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Post ID', 'Title', 'Type', 'Content', 'URL', 'Created At',
                           'Likes', 'Comments', 'Shares', 'Views', 'Engagement Score'])

            for post_id, post in self.posts.items():
                metrics = analyzer.get_latest_metrics(post)
                score = analyzer.calculate_engagement_score(metrics)
                writer.writerow([
                    post_id,
                    post['title'],
                    post['type'],
                    post['content'],
                    post.get('url', ''),
                    post['created_at'],
                    metrics.get('likes', 0),
                    metrics.get('comments', 0),
                    metrics.get('shares', 0),
                    metrics.get('views', 0),
                    f"{score:.2f}"
                ])

    def _export_top_posts(self, output_path: Path, analyzer: EngagementAnalyzer, limit: int):
        """Export top performing posts to CSV"""
        top_posts = analyzer.get_top_posts(limit)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Rank', 'Post ID', 'Title', 'Type', 'Created At',
                           'Likes', 'Comments', 'Shares', 'Views', 'Engagement Score'])

            for i, (post_id, post, score) in enumerate(top_posts, 1):
                metrics = analyzer.get_latest_metrics(post)
                writer.writerow([
                    i,
                    post_id,
                    post['title'],
                    post['type'],
                    post['created_at'],
                    metrics.get('likes', 0),
                    metrics.get('comments', 0),
                    metrics.get('shares', 0),
                    metrics.get('views', 0),
                    f"{score:.2f}"
                ])

    def _export_summary(self, output_path: Path, analyzer: EngagementAnalyzer):
        """Export summary statistics to CSV"""
        stats = analyzer.get_summary_stats()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Posts', stats['total_posts']])
            writer.writerow(['Total Likes', stats['total_likes']])
            writer.writerow(['Total Comments', stats['total_comments']])
            writer.writerow(['Total Shares', stats['total_shares']])
            writer.writerow(['Total Views', stats['total_views']])
            writer.writerow(['Average Engagement Score', f"{stats['avg_score']:.2f}"])
            writer.writerow(['Median Engagement Score', f"{stats['median_score']:.2f}"])
            writer.writerow(['Max Engagement Score', f"{stats['max_score']:.2f}"])

    def _export_best_times(self, output_path: Path, analyzer: EngagementAnalyzer):
        """Export best posting times analysis to CSV"""
        time_data = analyzer.analyze_posting_times()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Write best hours
            writer.writerow(['Best Hours Analysis'])
            writer.writerow(['Hour', 'Average Score', 'Number of Posts'])
            hour_items = sorted(time_data['by_hour'].items(),
                              key=lambda x: x[1]['avg_score'], reverse=True)
            for hour, data in hour_items:
                writer.writerow([f"{hour:02d}:00", f"{data['avg_score']:.2f}", data['count']])

            writer.writerow([])  # Empty row separator

            # Write best days
            writer.writerow(['Best Days Analysis'])
            writer.writerow(['Day', 'Average Score', 'Number of Posts'])
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_data = [(day, time_data['by_day'][day]) for day in day_order if day in time_data['by_day']]
            day_data.sort(key=lambda x: x[1]['avg_score'], reverse=True)

            for day, data in day_data:
                writer.writerow([day, f"{data['avg_score']:.2f}", data['count']])

    def _export_type_analysis(self, output_path: Path, analyzer: EngagementAnalyzer):
        """Export content type analysis to CSV"""
        type_data = analyzer.analyze_by_content_type()

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Content Type', 'Number of Posts', 'Avg Likes', 'Avg Comments',
                           'Avg Shares', 'Avg Views', 'Avg Engagement Score'])

            sorted_types = sorted(type_data.items(), key=lambda x: x[1]['avg_score'], reverse=True)
            for content_type, data in sorted_types:
                writer.writerow([
                    content_type.capitalize(),
                    data['count'],
                    f"{data['avg_likes']:.1f}",
                    f"{data['avg_comments']:.1f}",
                    f"{data['avg_shares']:.1f}",
                    f"{data['avg_views']:.1f}",
                    f"{data['avg_score']:.2f}"
                ])


def main():
    parser = argparse.ArgumentParser(
        description='LinkedIn Post Engagement Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a new post
  python linkedin_tracker.py add --title "My Post" --type article --content "..."

  # Update engagement
  python linkedin_tracker.py update POST_ID --likes 100 --comments 20 --shares 5 --views 1000

  # List all posts
  python linkedin_tracker.py list

  # Analyze patterns
  python linkedin_tracker.py analyze
  python linkedin_tracker.py analyze --best-times
  python linkedin_tracker.py analyze --by-type

  # Show top posts
  python linkedin_tracker.py top --limit 5

  # Export to CSV
  python linkedin_tracker.py export --output reports/all_posts.csv --type posts
  python linkedin_tracker.py export --output reports/top_10.csv --type top --limit 10
  python linkedin_tracker.py export --output reports/summary.csv --type summary
  python linkedin_tracker.py export --output reports/best_times.csv --type times
  python linkedin_tracker.py export --output reports/content_types.csv --type types
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Add post command
    add_parser = subparsers.add_parser('add', help='Add a new post to track')
    add_parser.add_argument('--title', required=True, help='Post title')
    add_parser.add_argument('--type', required=True,
                           choices=['article', 'short', 'image', 'video', 'poll', 'document'],
                           help='Post type')
    add_parser.add_argument('--content', required=True, help='Post content/description')
    add_parser.add_argument('--url', help='LinkedIn post URL')

    # Update engagement command
    update_parser = subparsers.add_parser('update', help='Update engagement metrics')
    update_parser.add_argument('post_id', help='Post ID to update')
    update_parser.add_argument('--likes', type=int, help='Number of likes')
    update_parser.add_argument('--comments', type=int, help='Number of comments')
    update_parser.add_argument('--shares', type=int, help='Number of shares')
    update_parser.add_argument('--views', type=int, help='Number of views')

    # List posts command
    list_parser = subparsers.add_parser('list', help='List all tracked posts')
    list_parser.add_argument('--limit', type=int, help='Limit number of posts shown')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze engagement patterns')
    analyze_parser.add_argument('--best-times', action='store_true',
                               help='Show best posting times')
    analyze_parser.add_argument('--by-type', action='store_true',
                               help='Analyze by content type')

    # Top posts command
    top_parser = subparsers.add_parser('top', help='Show top performing posts')
    top_parser.add_argument('--limit', type=int, default=10, help='Number of top posts to show')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export data to CSV')
    export_parser.add_argument('--output', '-o', required=True, help='Output CSV file path')
    export_parser.add_argument('--type', '-t', default='posts',
                              choices=['posts', 'top', 'summary', 'times', 'types'],
                              help='Type of report to export (default: posts)')
    export_parser.add_argument('--limit', type=int, help='Limit for top posts export')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = LinkedInTracker()

    if args.command == 'add':
        tracker.add_post(args.title, args.content, args.type, args.url)

    elif args.command == 'update':
        tracker.update_engagement(args.post_id, args.likes, args.comments,
                                args.shares, args.views)

    elif args.command == 'list':
        tracker.list_posts(args.limit)

    elif args.command == 'analyze':
        tracker.analyze_patterns(args.best_times, args.by_type)

    elif args.command == 'top':
        tracker.show_top_posts(args.limit)

    elif args.command == 'export':
        tracker.export_to_csv(args.output, args.type, args.limit)


if __name__ == '__main__':
    main()
