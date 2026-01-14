# LinkedIn Engagement Pattern Analyzer

A powerful tool to track LinkedIn posts and analyze engagement patterns to optimize your content strategy.

## Features

- 📊 **Track Post Performance**: Monitor likes, comments, shares, and views for each post
- 🔍 **Pattern Analysis**: Identify what content performs best
- ⏰ **Optimal Timing**: Discover the best times to post based on engagement data
- 📈 **Trend Detection**: Track engagement trends over time
- 📝 **Content Type Analysis**: Compare performance across different post types
- 💾 **Local Data Storage**: All data stored securely in JSON format

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Add a new post to track

```bash
python linkedin_tracker.py add \
  --title "My awesome post about AI" \
  --type "article" \
  --content "Check out this amazing insight..."
```

### 2. Update engagement metrics

```bash
python linkedin_tracker.py update POST_ID \
  --likes 150 \
  --comments 25 \
  --shares 10 \
  --views 1200
```

### 3. Analyze patterns

```bash
# Get overall engagement summary
python linkedin_tracker.py analyze

# Find best posting times
python linkedin_tracker.py analyze --best-times

# Compare content types
python linkedin_tracker.py analyze --by-type

# View top performing posts
python linkedin_tracker.py top --limit 5
```

### 4. List all tracked posts

```bash
python linkedin_tracker.py list
```

## Post Types

Track different content types:
- `article` - Long-form articles
- `short` - Short text posts
- `image` - Image posts
- `video` - Video content
- `poll` - Polls
- `document` - PDF/document posts

## Data Storage

Posts are stored in `data/posts.json` with the following structure:

```json
{
  "post_id": {
    "title": "Post title",
    "content": "Post content",
    "type": "article",
    "created_at": "2026-01-14T10:30:00",
    "engagement_history": [
      {
        "timestamp": "2026-01-14T12:00:00",
        "likes": 50,
        "comments": 10,
        "shares": 5,
        "views": 500
      }
    ]
  }
}
```

## Analysis Features

### Engagement Score
Each post gets an engagement score calculated as:
```
score = (likes × 1) + (comments × 3) + (shares × 5) + (views × 0.01)
```
Comments and shares are weighted higher as they indicate deeper engagement.

### Best Posting Times
Analyzes your historical data to find:
- Best hours of the day
- Best days of the week
- Optimal posting frequency

### Content Type Performance
Compare average engagement across different post types to find what resonates with your audience.

## Examples

### Track a new post
```bash
python linkedin_tracker.py add \
  --title "5 Tips for Better Code Reviews" \
  --type "article" \
  --content "Here are my top tips..." \
  --url "https://linkedin.com/posts/..."
```

### Update after 24 hours
```bash
python linkedin_tracker.py update abc123 \
  --likes 234 --comments 45 --shares 12 --views 3400
```

### Get insights
```bash
python linkedin_tracker.py analyze --best-times
```

Output:
```
📊 Best Posting Times Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best Hours (UTC):
  9 AM - Avg engagement: 245
  2 PM - Avg engagement: 198
  7 PM - Avg engagement: 167

Best Days:
  Tuesday - Avg engagement: 312
  Thursday - Avg engagement: 289
  Wednesday - Avg engagement: 245
```

## Configuration

Create a `config.json` file to customize settings:

```json
{
  "timezone": "UTC",
  "engagement_weights": {
    "likes": 1,
    "comments": 3,
    "shares": 5,
    "views": 0.01
  },
  "data_directory": "data"
}
```

## Tips for Best Results

1. **Regular Updates**: Update engagement metrics at consistent intervals (24h, 48h, 1 week)
2. **Track Everything**: Include all post types to get comprehensive insights
3. **Add Context**: Use descriptive titles to remember what each post was about
4. **Time Consistency**: Record posting times accurately for timing analysis
5. **Be Patient**: Need at least 20-30 posts for meaningful pattern analysis

## Future Enhancements

Potential features to add:
- [ ] Export reports to PDF/CSV
- [ ] Integration with LinkedIn API for automatic data fetching
- [ ] Hashtag performance tracking
- [ ] Audience growth correlation
- [ ] Automated posting suggestions based on patterns
- [ ] Web dashboard for visualization

## License

MIT License - Feel free to use and modify!
