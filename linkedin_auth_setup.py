#!/usr/bin/env python3
"""
LinkedIn OAuth Authentication Setup
Interactive script to help users set up LinkedIn API authentication
"""

import os
import uuid
from pathlib import Path
from linkedin_api import LinkedInAPIClient, LinkedInAuthHelper


def print_header():
    """Print welcome header"""
    print("\n" + "=" * 70)
    print("🔐 LINKEDIN API AUTHENTICATION SETUP")
    print("=" * 70)
    print("\nThis tool will help you set up authentication for the")
    print("LinkedIn Automated Tracker.\n")


def print_instructions():
    """Print setup instructions"""
    print("=" * 70)
    print("📋 SETUP INSTRUCTIONS")
    print("=" * 70)
    print("""
To use the automated tracker, you need to create a LinkedIn App
and get API credentials. Follow these steps:

1. Go to LinkedIn Developers Portal:
   https://www.linkedin.com/developers/apps

2. Click "Create app"

3. Fill in the required information:
   - App name: "My LinkedIn Tracker" (or any name)
   - LinkedIn Page: Select your LinkedIn page or create one
   - App logo: Upload any image
   - Legal agreement: Check the box

4. Click "Create app"

5. Once created, go to the "Auth" tab:
   - Copy your "Client ID"
   - Copy your "Client Secret"
   - Add redirect URL: http://localhost:8080/callback

6. Go to the "Products" tab:
   - Request access to "Share on LinkedIn"
   - Request access to "Sign In with LinkedIn"

7. Wait for approval (usually instant for personal use)

8. Come back here with your Client ID and Client Secret!

""")


def get_user_input():
    """Get credentials from user"""
    print("=" * 70)
    print("🔑 ENTER YOUR CREDENTIALS")
    print("=" * 70)
    print()

    client_id = input("Enter your LinkedIn Client ID: ").strip()
    client_secret = input("Enter your LinkedIn Client Secret: ").strip()

    if not client_id or not client_secret:
        print("\n❌ Error: Client ID and Client Secret are required!")
        return None, None

    return client_id, client_secret


def start_oauth_flow(client_id: str, client_secret: str):
    """Start OAuth authentication flow"""
    print("\n" + "=" * 70)
    print("🌐 STARTING OAUTH FLOW")
    print("=" * 70)

    # Generate state for security
    state = str(uuid.uuid4())

    # Generate authorization URL
    redirect_uri = "http://localhost:8080/callback"
    auth_url = LinkedInAPIClient.get_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state
    )

    print(f"""
Step 1: Visit this URL in your browser:

{auth_url}

Step 2: Authorize the application

Step 3: You'll be redirected to:
        http://localhost:8080/callback?code=XXXXX&state={state}

Step 4: Copy the entire URL from your browser's address bar
        (even though the page won't load, that's OK!)

""")

    callback_url = input("Paste the full callback URL here: ").strip()

    if not callback_url or 'code=' not in callback_url:
        print("\n❌ Error: Invalid callback URL!")
        return False

    # Extract authorization code
    try:
        code = callback_url.split('code=')[1].split('&')[0]
    except IndexError:
        print("\n❌ Error: Could not extract authorization code from URL!")
        return False

    print(f"\n✅ Authorization code received: {code[:20]}...")

    # Exchange code for access token
    print("\n🔄 Exchanging code for access token...")

    try:
        token_response = LinkedInAPIClient.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=code,
            redirect_uri=redirect_uri
        )

        access_token = token_response.get('access_token')
        expires_in = token_response.get('expires_in', 5184000)  # Default 60 days

        if not access_token:
            print("\n❌ Error: Failed to get access token!")
            return False

        # Save credentials
        LinkedInAuthHelper.save_credentials(access_token, expires_in)

        # Test the token
        print("\n🧪 Testing API connection...")
        client = LinkedInAPIClient(access_token)
        profile = client.get_user_profile()

        print("\n" + "=" * 70)
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print("=" * 70)
        print(f"\n👤 Authenticated as:")
        print(f"   Name: {profile.get('localizedFirstName', '')} {profile.get('localizedLastName', '')}")
        print(f"   User ID: {profile.get('id', '')}")
        print(f"\n🔑 Access token saved to .env file")
        print(f"⏱️  Token expires in: {expires_in / 86400:.0f} days")

        print("\n🚀 You're all set! You can now run:")
        print("   python linkedin_auto_tracker.py --sync")
        print("   python linkedin_auto_tracker.py --monitor")

        return True

    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your Client ID and Secret are correct")
        print("2. Ensure the redirect URI matches exactly: http://localhost:8080/callback")
        print("3. Check that you've requested access to required products")
        print("4. Try generating a new authorization code")
        return False


def check_existing_credentials():
    """Check if credentials already exist"""
    if Path(".env").exists():
        token = LinkedInAuthHelper.load_credentials()
        if token and not LinkedInAuthHelper.is_token_expired():
            print("\n✅ Found existing valid credentials!")
            response = input("\nDo you want to re-authenticate? (y/N): ").strip().lower()
            return response == 'y'
    return True


def save_app_credentials(client_id: str, client_secret: str):
    """Save app credentials for future use"""
    env_path = Path(".env")
    lines = []

    # Read existing lines
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = [line for line in f.readlines()
                    if not line.startswith('LINKEDIN_CLIENT_ID') and
                    not line.startswith('LINKEDIN_CLIENT_SECRET')]

    # Add credentials
    lines.append(f"LINKEDIN_CLIENT_ID={client_id}\n")
    lines.append(f"LINKEDIN_CLIENT_SECRET={client_secret}\n")

    with open(env_path, 'w') as f:
        f.writelines(lines)


def main():
    """Main setup flow"""
    print_header()

    # Check for existing credentials
    if not check_existing_credentials():
        print("\n👋 Keeping existing credentials. Goodbye!")
        return

    print_instructions()

    proceed = input("Have you created your LinkedIn App? (y/N): ").strip().lower()

    if proceed != 'y':
        print("\n⏸️  No problem! Create your app first, then run this script again.")
        print("   Visit: https://www.linkedin.com/developers/apps")
        return

    # Get credentials
    client_id, client_secret = get_user_input()

    if not client_id or not client_secret:
        return

    # Save app credentials
    save_app_credentials(client_id, client_secret)

    # Start OAuth flow
    success = start_oauth_flow(client_id, client_secret)

    if not success:
        print("\n❌ Setup failed. Please try again.")
        print("   Run: python linkedin_auth_setup.py")
    else:
        print("\n" + "=" * 70)
        print("🎉 Setup complete! Happy tracking!")
        print("=" * 70)


if __name__ == '__main__':
    main()
