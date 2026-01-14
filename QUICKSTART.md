# Quick Start Guide

Get started with the LinkedIn Engagement Pattern Analyzer in 5 minutes!

## Step 1: Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Step 2: Add Your First Posts

Let's track a few posts from different days and times:

```bash
# Monday morning article
python linkedin_tracker.py add \
  --title "5 Python Tips Every Developer Should Know" \
  --type "article" \
  --content "Here are my favorite Python tips that will save you hours..."

# Note the Post ID (e.g., "a1b2c3d4")
```

Output:
```
✅ Post added successfully!
📌 Post ID: a1b2c3d4
📝 Title: 5 Python Tips Every Developer Should Know
🏷️  Type: article

Use this ID to update engagement: python linkedin_tracker.py update a1b2c3d4
```

Add a few more posts:

```bash
# Tuesday afternoon image post
python linkedin_tracker.py add \
  --title "Our team's workspace setup" \
  --type "image" \
  --content "Check out how we've optimized our office for productivity"

# Thursday evening short post
python linkedin_tracker.py add \
  --title "Quick thought on code reviews" \
  --type "short" \
  --content "Code reviews aren't just about finding bugs..."

# Friday video
python linkedin_tracker.py add \
  --title "Demo of our new feature" \
  --type "video" \
  --content "Excited to share our latest product feature!"
```

## Step 3: Update Engagement After 24 Hours

Check your LinkedIn posts after 24 hours and update the metrics:

```bash
# Update first post (replace with your actual Post ID)
python linkedin_tracker.py update a1b2c3d4 \
  --likes 234 \
  --comments 45 \
  --shares 12 \
  --views 3400
```

Output:
```
✅ Engagement updated for post: 5 Python Tips Every Developer Should Know

📊 Current Metrics:
   👍 Likes: 234
   💬 Comments: 45
   🔄 Shares: 12
   👁️  Views: 3400

🎯 Engagement Score: 433.0
```

Update your other posts similarly.

## Step 4: Track Engagement Over Time

You can update the same post multiple times to see trends:

```bash
# After 48 hours
python linkedin_tracker.py update a1b2c3d4 \
  --likes 456 \
  --comments 67 \
  --shares 23 \
  --views 5200

# After 1 week
python linkedin_tracker.py update a1b2c3d4 \
  --likes 789 \
  --comments 102 \
  --shares 45 \
  --views 8900
```

## Step 5: View Your Posts

```bash
python linkedin_tracker.py list
```

You'll see a formatted table with all your posts and their latest metrics.

## Step 6: Analyze Patterns

### Get Overall Summary
```bash
python linkedin_tracker.py analyze
```

Output:
```
============================================================
📊 LINKEDIN ENGAGEMENT SUMMARY
============================================================

📝 Total Posts: 15

📈 Total Engagement:
   👍 Likes: 2,345
   💬 Comments: 456
   🔄 Shares: 123
   👁️  Views: 34,567

🎯 Engagement Scores:
   Average: 312.45
   Median: 289.0
   Best: 892.5
```

### Find Best Posting Times
```bash
python linkedin_tracker.py analyze --best-times
```

This shows you which hours and days get the best engagement!

### Compare Content Types
```bash
python linkedin_tracker.py analyze --by-type
```

See which content types (articles, videos, images, etc.) perform best for you.

### View Top Performers
```bash
python linkedin_tracker.py top --limit 5
```

See your 5 best performing posts ranked by engagement score.

## Step 7: Build Your Dataset

For meaningful insights, aim to track:
- **At least 20-30 posts** for basic patterns
- **Different content types** to compare performance
- **Various posting times** to find optimal windows
- **Multiple updates per post** to track growth trends

## Pro Tips

### 1. Consistent Tracking Schedule
Update metrics at consistent intervals:
- 24 hours after posting
- 48 hours after posting
- 1 week after posting
- 1 month after posting

### 2. Add Context with Titles
Use descriptive titles so you remember what each post was about:
```bash
--title "Python tips - list comprehensions vs loops"
```

### 3. Include URLs for Reference
```bash
--url "https://linkedin.com/posts/yourname-123456789"
```

### 4. Customize Engagement Weights
Create a `config.json` file to emphasize what matters to you:

```json
{
  "engagement_weights": {
    "likes": 1,
    "comments": 5,
    "shares": 10,
    "views": 0.005
  }
}
```

This configuration values shares and comments more highly.

## Common Workflows

### Daily Check-In
```bash
# List posts from the last few days
python linkedin_tracker.py list --limit 5

# Update engagement for recent posts
python linkedin_tracker.py update <POST_ID> --likes X --comments Y --shares Z --views W
```

### Weekly Analysis
```bash
# See what's working
python linkedin_tracker.py top --limit 10

# Check if timing matters
python linkedin_tracker.py analyze --best-times

# Compare content types
python linkedin_tracker.py analyze --by-type
```

### Monthly Deep Dive
```bash
# Get full summary
python linkedin_tracker.py analyze

# Review all posts
python linkedin_tracker.py list

# Adjust strategy based on insights
```

## What to Look For

### 🔍 Engagement Score
Higher is better! This weighted score helps you compare posts fairly.

### 📊 Content Type Trends
If "article" posts consistently outperform "short" posts, create more articles!

### ⏰ Timing Patterns
Post when your audience is most active for maximum engagement.

### 📈 Growth Patterns
Track how engagement grows over time. Some posts may have slow burns while others peak quickly.

## Next Steps

1. **Build your dataset** - Track 20+ posts over the next month
2. **Update regularly** - Set reminders to check engagement
3. **Analyze patterns** - Run analysis weekly
4. **Optimize strategy** - Apply insights to your content calendar
5. **Iterate** - Keep refining based on what you learn

Happy tracking! 🚀
