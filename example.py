#!/usr/bin/env python3
"""
Example usage of LinkedIn Tracker programmatically
This demonstrates how to use the tool from within Python code
"""

from linkedin_tracker import LinkedInTracker
from datetime import datetime, timedelta

def demo_usage():
    """Demonstrate programmatic usage"""

    # Initialize tracker
    tracker = LinkedInTracker()

    print("🚀 LinkedIn Engagement Tracker - Demo\n")

    # Add sample posts with different types and times
    print("📝 Adding sample posts...")

    posts = [
        {
            'title': '10 Productivity Hacks for Remote Workers',
            'type': 'article',
            'content': 'After 5 years of remote work, here are my top tips...'
        },
        {
            'title': 'Our team celebrating a major milestone!',
            'type': 'image',
            'content': 'So proud of what we accomplished this quarter'
        },
        {
            'title': 'Quick poll: What's your preferred tech stack?',
            'type': 'poll',
            'content': 'Curious to know what technologies you all use'
        },
        {
            'title': 'Product demo - New feature release',
            'type': 'video',
            'content': 'Check out our latest feature that will change how you work'
        },
        {
            'title': 'Thoughts on the future of AI in software development',
            'type': 'short',
            'content': 'AI tools are transforming how we code, but...'
        }
    ]

    post_ids = []
    for post in posts:
        post_id = tracker.add_post(
            title=post['title'],
            content=post['content'],
            post_type=post['type']
        )
        post_ids.append(post_id)
        print(f"  ✓ Added: {post['title'][:50]}... (ID: {post_id})")

    print(f"\n✅ Added {len(post_ids)} sample posts\n")

    # Simulate engagement data at different time intervals
    print("📊 Adding simulated engagement data...\n")

    import random

    for i, post_id in enumerate(post_ids):
        # Simulate different engagement levels
        base_views = random.randint(500, 5000)
        engagement_rate = random.uniform(0.05, 0.15)

        # 24-hour metrics
        likes_24h = int(base_views * engagement_rate * random.uniform(0.6, 0.8))
        comments_24h = int(likes_24h * random.uniform(0.1, 0.2))
        shares_24h = int(likes_24h * random.uniform(0.05, 0.15))

        tracker.update_engagement(
            post_id=post_id,
            likes=likes_24h,
            comments=comments_24h,
            shares=shares_24h,
            views=base_views
        )

        # 48-hour metrics (growth)
        likes_48h = int(likes_24h * random.uniform(1.3, 1.8))
        comments_48h = int(comments_24h * random.uniform(1.2, 1.6))
        shares_48h = int(shares_24h * random.uniform(1.3, 1.7))
        views_48h = int(base_views * random.uniform(1.5, 2.2))

        tracker.update_engagement(
            post_id=post_id,
            likes=likes_48h,
            comments=comments_48h,
            shares=shares_48h,
            views=views_48h
        )

        print(f"  ✓ Updated engagement for post {i+1}")

    print("\n✅ Engagement data added\n")

    # Now run some analyses
    print("=" * 70)
    print("📈 RUNNING ANALYSES")
    print("=" * 70 + "\n")

    # Show all posts
    print("1️⃣  Listing all tracked posts:\n")
    tracker.list_posts()

    print("\n" + "=" * 70 + "\n")

    # Show top posts
    print("2️⃣  Top performing posts:\n")
    tracker.show_top_posts(limit=3)

    print("\n" + "=" * 70 + "\n")

    # Overall summary
    print("3️⃣  Overall summary:\n")
    tracker.analyze_patterns()

    print("\n" + "=" * 70 + "\n")

    # By content type
    print("4️⃣  Performance by content type:\n")
    tracker.analyze_patterns(by_type=True)

    print("\n" + "=" * 70)
    print("✅ Demo complete! Check the data/ directory for your posts.json file")
    print("=" * 70)


if __name__ == '__main__':
    demo_usage()
