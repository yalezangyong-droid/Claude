"""
LinkedIn Engagement Pattern Analyzer
Analyzes post engagement data to identify patterns and insights
"""

from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple
import statistics


class EngagementAnalyzer:
    def __init__(self, posts_data: Dict, engagement_weights: Dict = None):
        """
        Initialize the analyzer with posts data

        Args:
            posts_data: Dictionary of all posts
            engagement_weights: Custom weights for engagement metrics
        """
        self.posts = posts_data
        self.weights = engagement_weights or {
            'likes': 1,
            'comments': 3,
            'shares': 5,
            'views': 0.01
        }

    def calculate_engagement_score(self, metrics: Dict) -> float:
        """Calculate weighted engagement score"""
        score = (
            metrics.get('likes', 0) * self.weights['likes'] +
            metrics.get('comments', 0) * self.weights['comments'] +
            metrics.get('shares', 0) * self.weights['shares'] +
            metrics.get('views', 0) * self.weights['views']
        )
        return round(score, 2)

    def get_latest_metrics(self, post: Dict) -> Dict:
        """Get the most recent engagement metrics for a post"""
        if not post.get('engagement_history'):
            return {'likes': 0, 'comments': 0, 'shares': 0, 'views': 0}
        return post['engagement_history'][-1]

    def get_top_posts(self, limit: int = 10) -> List[Tuple[str, Dict, float]]:
        """
        Get top performing posts by engagement score

        Returns:
            List of tuples (post_id, post_data, engagement_score)
        """
        scored_posts = []

        for post_id, post in self.posts.items():
            metrics = self.get_latest_metrics(post)
            score = self.calculate_engagement_score(metrics)
            scored_posts.append((post_id, post, score))

        # Sort by score descending
        scored_posts.sort(key=lambda x: x[2], reverse=True)

        return scored_posts[:limit]

    def analyze_by_content_type(self) -> Dict:
        """Analyze engagement by content type"""
        type_data = defaultdict(lambda: {
            'count': 0,
            'total_likes': 0,
            'total_comments': 0,
            'total_shares': 0,
            'total_views': 0,
            'scores': []
        })

        for post_id, post in self.posts.items():
            content_type = post.get('type', 'unknown')
            metrics = self.get_latest_metrics(post)
            score = self.calculate_engagement_score(metrics)

            type_data[content_type]['count'] += 1
            type_data[content_type]['total_likes'] += metrics.get('likes', 0)
            type_data[content_type]['total_comments'] += metrics.get('comments', 0)
            type_data[content_type]['total_shares'] += metrics.get('shares', 0)
            type_data[content_type]['total_views'] += metrics.get('views', 0)
            type_data[content_type]['scores'].append(score)

        # Calculate averages
        results = {}
        for content_type, data in type_data.items():
            count = data['count']
            results[content_type] = {
                'count': count,
                'avg_likes': round(data['total_likes'] / count, 1),
                'avg_comments': round(data['total_comments'] / count, 1),
                'avg_shares': round(data['total_shares'] / count, 1),
                'avg_views': round(data['total_views'] / count, 1),
                'avg_score': round(statistics.mean(data['scores']), 2)
            }

        return results

    def analyze_posting_times(self) -> Dict:
        """Analyze best posting times"""
        hour_data = defaultdict(lambda: {'scores': [], 'count': 0})
        day_data = defaultdict(lambda: {'scores': [], 'count': 0})

        for post_id, post in self.posts.items():
            created_at = datetime.fromisoformat(post['created_at'])
            metrics = self.get_latest_metrics(post)
            score = self.calculate_engagement_score(metrics)

            hour = created_at.hour
            day_name = created_at.strftime('%A')

            hour_data[hour]['scores'].append(score)
            hour_data[hour]['count'] += 1

            day_data[day_name]['scores'].append(score)
            day_data[day_name]['count'] += 1

        # Calculate averages
        hour_results = {}
        for hour, data in hour_data.items():
            if data['scores']:
                hour_results[hour] = {
                    'avg_score': round(statistics.mean(data['scores']), 2),
                    'count': data['count']
                }

        day_results = {}
        for day, data in day_data.items():
            if data['scores']:
                day_results[day] = {
                    'avg_score': round(statistics.mean(data['scores']), 2),
                    'count': data['count']
                }

        return {
            'by_hour': hour_results,
            'by_day': day_results
        }

    def get_engagement_trends(self, post_id: str) -> List[Dict]:
        """Get engagement trend data for a specific post"""
        if post_id not in self.posts:
            return []

        post = self.posts[post_id]
        history = post.get('engagement_history', [])

        trends = []
        for i, snapshot in enumerate(history):
            score = self.calculate_engagement_score(snapshot)
            growth = 0

            if i > 0:
                prev_score = self.calculate_engagement_score(history[i-1])
                growth = score - prev_score

            trends.append({
                'timestamp': snapshot['timestamp'],
                'score': score,
                'growth': round(growth, 2),
                'metrics': {
                    'likes': snapshot.get('likes', 0),
                    'comments': snapshot.get('comments', 0),
                    'shares': snapshot.get('shares', 0),
                    'views': snapshot.get('views', 0)
                }
            })

        return trends

    def get_summary_stats(self) -> Dict:
        """Get overall summary statistics"""
        if not self.posts:
            return {
                'total_posts': 0,
                'total_engagement': 0,
                'avg_score': 0
            }

        total_likes = 0
        total_comments = 0
        total_shares = 0
        total_views = 0
        scores = []

        for post_id, post in self.posts.items():
            metrics = self.get_latest_metrics(post)
            score = self.calculate_engagement_score(metrics)

            total_likes += metrics.get('likes', 0)
            total_comments += metrics.get('comments', 0)
            total_shares += metrics.get('shares', 0)
            total_views += metrics.get('views', 0)
            scores.append(score)

        return {
            'total_posts': len(self.posts),
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'total_views': total_views,
            'avg_score': round(statistics.mean(scores), 2) if scores else 0,
            'median_score': round(statistics.median(scores), 2) if scores else 0,
            'max_score': round(max(scores), 2) if scores else 0
        }
