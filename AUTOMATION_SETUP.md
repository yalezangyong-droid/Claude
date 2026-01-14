# LinkedIn Automated Tracking Setup Guide

This guide will help you set up automatic tracking of your LinkedIn posts using the LinkedIn API.

## 🎯 Overview

The automated tracker will:
- ✅ Automatically fetch your LinkedIn posts
- ✅ Track engagement metrics (likes, comments, shares, views)
- ✅ Update metrics on a schedule (every 6 hours by default)
- ✅ Store historical data for trend analysis
- ✅ Work continuously in the background

## 📋 Prerequisites

Before you begin, you need:
1. A LinkedIn account
2. A LinkedIn Company Page (required for API access)
3. Python 3.7 or higher installed

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `requests` - For API calls
- `schedule` - For periodic syncing
- `python-dotenv` - For credential management
- `tabulate` - For formatted output
- `python-dateutil` - For date handling

### Step 2: Create a LinkedIn App

1. **Go to LinkedIn Developers Portal**

   Visit: https://www.linkedin.com/developers/apps

2. **Create a New App**

   Click the "Create app" button

3. **Fill in App Details**

   - **App name**: "LinkedIn Post Tracker" (or any name you prefer)
   - **LinkedIn Page**: Select your LinkedIn Company Page
     - ⚠️ Don't have a page? Create one at: https://www.linkedin.com/company/setup/new/
   - **App logo**: Upload any image (PNG/JPG, min 300x300px)
   - **Privacy policy URL**: Your website or use: https://www.linkedin.com/legal/privacy-policy
   - **Legal agreement**: Check the box to agree

   Click "Create app"

4. **Get Your Credentials**

   After creation, go to the **"Auth"** tab:
   - Copy your **Client ID**
   - Copy your **Client Secret**
   - Click "Add redirect URL" and enter: `http://localhost:8080/callback`
   - Click "Update"

5. **Request Product Access**

   Go to the **"Products"** tab and request access to:
   - ✅ "Share on LinkedIn"
   - ✅ "Sign In with LinkedIn"

   Click "Request access" for each product

   ⏱️ Approval is usually instant for personal use

### Step 3: Run Authentication Setup

Run the interactive setup script:

```bash
python linkedin_auth_setup.py
```

The script will:

1. **Ask for your credentials**
   - Enter your Client ID
   - Enter your Client Secret

2. **Generate an authorization URL**
   - Opens your browser (or copy the URL manually)
   - You'll be asked to authorize the app

3. **Complete OAuth flow**
   - After authorizing, copy the callback URL from your browser
   - The page won't load (that's OK!)
   - Paste the full URL back into the terminal

4. **Save your access token**
   - The script will save credentials to `.env` file
   - Test the connection automatically

Example output:
```
✅ AUTHENTICATION SUCCESSFUL!
👤 Authenticated as: John Doe
🔑 Access token saved to .env file
⏱️  Token expires in: 60 days

🚀 You're all set! You can now run:
   python linkedin_auto_tracker.py --sync
```

### Step 4: Test the Connection

Run a one-time sync to test everything works:

```bash
python linkedin_auto_tracker.py --sync
```

This will:
- Connect to LinkedIn API
- Fetch your recent posts
- Store them in the local database
- Display a summary

Expected output:
```
============================================================
🔄 SYNCING WITH LINKEDIN
============================================================

📥 Fetching posts from LinkedIn...
✅ Fetched 15 posts
  ✅ Added new post: My thoughts on AI development...
  ✅ Added new post: Excited to share our new feature...
  ...

============================================================
✅ SYNC COMPLETE
============================================================

📊 Results:
   Total posts fetched: 15
   New posts added: 15
   Posts updated: 0

🕐 Last sync: 2026-01-14T10:30:00
```

### Step 5: Start Automated Monitoring

Start continuous monitoring:

```bash
python linkedin_auto_tracker.py --monitor
```

This will:
- Run an initial sync
- Schedule syncs every 6 hours
- Keep running in the background
- Press Ctrl+C to stop

To customize the check interval:

```bash
# Check every 12 hours
python linkedin_auto_tracker.py --monitor --interval 12

# Check every 3 hours
python linkedin_auto_tracker.py --monitor --interval 3
```

### Step 6: Run as a Background Service (Optional)

To keep the tracker running 24/7:

#### On Linux/Mac:

```bash
# Using nohup
nohup python linkedin_auto_tracker.py --monitor > tracker.log 2>&1 &

# Check if running
ps aux | grep linkedin_auto_tracker

# Stop it
kill <process_id>
```

#### Using screen:

```bash
# Start a screen session
screen -S linkedin-tracker

# Run the tracker
python linkedin_auto_tracker.py --monitor

# Detach with Ctrl+A then D
# Reattach with: screen -r linkedin-tracker
```

#### Using systemd (Linux):

Create `/etc/systemd/system/linkedin-tracker.service`:

```ini
[Unit]
Description=LinkedIn Post Tracker
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/Claude
ExecStart=/usr/bin/python3 linkedin_auto_tracker.py --monitor
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable linkedin-tracker
sudo systemctl start linkedin-tracker
sudo systemctl status linkedin-tracker
```

## 📊 Using the Data

Once automation is running, you can analyze your data anytime:

### View All Tracked Posts

```bash
python linkedin_tracker.py list
```

### Analyze Patterns

```bash
# Overall summary
python linkedin_tracker.py analyze

# Best posting times
python linkedin_tracker.py analyze --best-times

# Compare content types
python linkedin_tracker.py analyze --by-type

# Top performers
python linkedin_tracker.py top --limit 10
```

### Check Automation Status

```bash
python linkedin_auto_tracker.py --status
```

Output:
```
============================================================
📊 AUTOMATED TRACKER STATUS
============================================================

🕐 Last sync: 2026-01-14 10:30:00
   (3.2 hours ago)

⚙️  Configuration:
   Check interval: 6 hours
   Max posts: 50

📝 Tracked posts: 47
✅ API connection: OK
```

## 🔧 Troubleshooting

### "Authentication failed" error

**Solution:**
1. Verify your Client ID and Secret are correct
2. Check that redirect URL is exactly: `http://localhost:8080/callback`
3. Ensure you've requested and been approved for required products
4. Try re-running: `python linkedin_auth_setup.py`

### "Token expired" error

LinkedIn access tokens expire after 60 days.

**Solution:**
```bash
python linkedin_auth_setup.py
```

Re-authenticate to get a new token.

### "Cannot fetch posts" error

**Possible causes:**
1. LinkedIn API rate limits (wait 15 minutes)
2. Network connectivity issues
3. LinkedIn API service issues

**Solution:**
- Check your internet connection
- Wait a bit and try again
- Check LinkedIn API status: https://www.linkedin-apistatus.com/

### "No posts found"

Make sure you're fetching posts from your personal profile, not a company page.

**Solution:**
- Verify you've posted on LinkedIn recently
- Check that your posts are public
- Try increasing max_posts_to_fetch in automation_config.json

## ⚙️ Configuration

### Automation Settings

Edit `automation_config.json`:

```json
{
  "check_interval_hours": 6,
  "max_posts_to_fetch": 50,
  "enable_notifications": false,
  "last_run": "2026-01-14T10:30:00"
}
```

### Engagement Weights

Edit `config.json`:

```json
{
  "engagement_weights": {
    "likes": 1,
    "comments": 3,
    "shares": 5,
    "views": 0.01
  }
}
```

## 🔒 Security Best Practices

1. **Never commit `.env` file**
   - Already in `.gitignore`
   - Contains sensitive access tokens

2. **Protect your credentials**
   - Keep Client ID and Secret private
   - Don't share access tokens

3. **Regenerate tokens if compromised**
   - Go to your LinkedIn App settings
   - Generate new Client Secret
   - Re-run authentication setup

4. **Use environment-specific credentials**
   - Use different apps for dev/prod if needed

## 📈 Best Practices

1. **Check interval**: 6 hours is optimal
   - Too frequent: Risk hitting rate limits
   - Too infrequent: Miss engagement peaks

2. **Run on a server**: For 24/7 tracking
   - Use a cloud VM or home server
   - Set up systemd service for auto-restart

3. **Monitor regularly**: Check status weekly
   ```bash
   python linkedin_auto_tracker.py --status
   ```

4. **Backup your data**:
   ```bash
   cp data/posts.json data/posts_backup_$(date +%Y%m%d).json
   ```

## 🆘 Getting Help

If you run into issues:

1. **Check the logs**: Error messages are usually helpful
2. **Verify credentials**: Re-run authentication setup
3. **Test manually**: Try `--sync` before `--monitor`
4. **Check API limits**: LinkedIn has rate limits
5. **Review docs**: https://docs.microsoft.com/en-us/linkedin/

## 🎉 Success Checklist

- ✅ LinkedIn App created
- ✅ Client credentials obtained
- ✅ Authentication completed
- ✅ First sync successful
- ✅ Monitoring started
- ✅ Can view and analyze data

Congratulations! Your LinkedIn posts are now being tracked automatically! 🚀
