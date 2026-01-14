# LinkedIn Engagement Pattern Analyzer

A powerful tool to track LinkedIn posts and analyze engagement patterns to optimize your content strategy.

## ✨ Two Modes Available

### 🤖 Automated Mode (NEW!)
Automatically track your LinkedIn account using the LinkedIn API:
- **Automatic data fetching** - No manual entry needed
- **Scheduled syncing** - Updates every 6 hours (customizable)
- **Background monitoring** - Run 24/7 as a service
- **OAuth authentication** - Secure API access

👉 **[Setup Automated Tracking →](AUTOMATION_SETUP.md)**

### 📝 Manual Mode
Manually track posts by entering data yourself:
- Full control over what you track
- No API setup required
- Works offline
- Perfect for testing or simple use cases

👉 **[Manual Quick Start →](QUICKSTART.md)**

## Features

- 📊 **Track Post Performance**: Monitor likes, comments, shares, and views for each post
- 🔍 **Pattern Analysis**: Identify what content performs best
- ⏰ **Optimal Timing**: Discover the best times to post based on engagement data
- 📈 **Trend Detection**: Track engagement trends over time
- 📝 **Content Type Analysis**: Compare performance across different post types
- 💾 **Local Data Storage**: All data stored securely in JSON format
- 🤖 **Automated Tracking**: Set it and forget it with LinkedIn API integration

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Option A: Automated Tracking (Recommended)

1. **Authenticate with LinkedIn**
   ```bash
   python linkedin_auth_setup.py
   ```

2. **Start automatic monitoring**
   ```bash
   python linkedin_auto_tracker.py --monitor
   ```

3. **Analyze your data**
   ```bash
   python linkedin_tracker.py analyze --best-times
   python linkedin_tracker.py top --limit 10
   ```

📖 **[Full Automation Setup Guide →](AUTOMATION_SETUP.md)**

### Option B: Manual Tracking

1. **Add a new post to track**
   ```bash
   python linkedin_tracker.py add \
     --title "My awesome post about AI" \
     --type "article" \
     --content "Check out this amazing insight..."
   ```

2. **Update engagement metrics**
   ```bash
   python linkedin_tracker.py update POST_ID \
     --likes 150 \
     --comments 25 \
     --shares 10 \
     --views 1200
   ```

3. **Analyze patterns**

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

4. **List all tracked posts**
   ```bash
   python linkedin_tracker.py list
   ```

📖 **[Detailed Manual Tracking Guide →](QUICKSTART.md)**

## Automated Tracking Commands

Once you've set up authentication (see [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md)):

### Run One-Time Sync
```bash
python linkedin_auto_tracker.py --sync
```
Fetches all your LinkedIn posts and updates engagement metrics once.

### Start Continuous Monitoring
```bash
# Check every 6 hours (default)
python linkedin_auto_tracker.py --monitor

# Custom interval (check every 12 hours)
python linkedin_auto_tracker.py --monitor --interval 12
```
Runs continuously, updating metrics on schedule.

### Check Status
```bash
python linkedin_auto_tracker.py --status
```
Shows when last sync ran and current configuration.

### Run as Background Service
```bash
# Linux/Mac
nohup python linkedin_auto_tracker.py --monitor > tracker.log 2>&1 &

# Using screen
screen -S linkedin-tracker
python linkedin_auto_tracker.py --monitor
# Press Ctrl+A then D to detach
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
- [x] ~~Integration with LinkedIn API for automatic data fetching~~ ✅ **Implemented!**
- [ ] Hashtag performance tracking
- [ ] Audience growth correlation
- [ ] Automated posting suggestions based on patterns
- [ ] Web dashboard for visualization
- [ ] Email/Slack notifications for engagement milestones
- [ ] A/B testing recommendations

## License

MIT License - Feel free to use and modify!
