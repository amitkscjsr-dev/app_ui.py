"""
linkedin_auth.py
────────────────
Run this ONCE to get your LinkedIn access token.
It opens a browser for OAuth, catches the callback, saves the token to .env

Usage:
    python linkedin_auth.py

Requirements in .env:
    LINKEDIN_CLIENT_ID
    LINKEDIN_CLIENT_SECRET
    LINKEDIN_REDIRECT_URI  (default: http://localhost:8080/callback)
"""

import os
import json
import time
import webbrowser
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv, set_key

load_dotenv()

CLIENT_ID     = os.getenv("LINKEDIN_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
REDIRECT_URI  = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8080/callback")
SCOPES        = "r_liteprofile r_emailaddress w_member_social"

ENV_FILE      = ".env"
_auth_code    = None


# ── Step 1: Local callback server ────────────────────────────────────────────
class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
                <h2 style="color:#0a66c2">LinkedIn authorization successful!</h2>
                <p>You can close this tab and return to your terminal.</p>
                </body></html>
            """)
        else:
            error = params.get("error_description", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"<html><body>Error: {error}</body></html>".encode())

    def log_message(self, format, *args):
        pass  # suppress server logs


def _get_auth_code() -> str:
    """Open browser for OAuth, return the authorization code."""
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "scope":         SCOPES,
        "state":         "ai_content_os_auth",
    })
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{params}"

    print(f"\n Opening browser for LinkedIn authorization...")
    print(f" If it doesn't open, visit:\n {auth_url}\n")
    webbrowser.open(auth_url)

    # Start local server to catch the callback
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.timeout = 120  # 2 minute timeout
    server.handle_request()

    if not _auth_code:
        raise RuntimeError("Authorization failed — no code received")
    return _auth_code


# ── Step 2: Exchange code for access token ───────────────────────────────────
def _exchange_code(code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    data = urllib.parse.urlencode({
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ── Step 3: Fetch Person URN ──────────────────────────────────────────────────
def _get_person_urn(access_token: str) -> str:
    """Fetch your LinkedIn person URN (needed for posting)."""
    req = urllib.request.Request(
        "https://api.linkedin.com/v2/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        person_id = data["id"]
        return f"urn:li:person:{person_id}"


# ── Main flow ────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  LinkedIn OAuth Token Generator — AI Content OS")
    print("=" * 55)

    if not CLIENT_ID or not CLIENT_SECRET:
        print("\n ERROR: Missing LINKEDIN_CLIENT_ID or LINKEDIN_CLIENT_SECRET in .env")
        print("  1. Go to linkedin.com/developers → your app → Auth tab")
        print("  2. Copy Client ID and Client Secret")
        print("  3. Add them to your .env file")
        print("  4. Run this script again\n")
        return

    print(f"\n Client ID  : {CLIENT_ID[:8]}...")
    print(f" Redirect   : {REDIRECT_URI}")
    print(f" Scopes     : {SCOPES}\n")

    # Get auth code via browser
    try:
        code = _get_auth_code()
        print(f" Auth code received (length: {len(code)})")
    except Exception as e:
        print(f"\n ERROR getting auth code: {e}")
        return

    # Exchange for tokens
    try:
        print(" Exchanging code for access token...")
        token_data = _exchange_code(code)
        access_token  = token_data["access_token"]
        expires_in    = token_data.get("expires_in", 5184000)  # 60 days default
        refresh_token = token_data.get("refresh_token", "")
        print(f" Token received! Expires in {expires_in // 86400} days")
    except Exception as e:
        print(f"\n ERROR exchanging code: {e}")
        return

    # Get Person URN
    try:
        print(" Fetching your LinkedIn Person URN...")
        person_urn = _get_person_urn(access_token)
        print(f" Person URN: {person_urn}")
    except Exception as e:
        print(f" WARNING: Could not fetch URN: {e}")
        person_urn = "urn:li:person:MANUALLY_ADD_THIS"

    # Save to .env
    print("\n Saving tokens to .env...")
    set_key(ENV_FILE, "LINKEDIN_ACCESS_TOKEN", access_token)
    set_key(ENV_FILE, "LINKEDIN_PERSON_URN",   person_urn)
    if refresh_token:
        set_key(ENV_FILE, "LINKEDIN_REFRESH_TOKEN", refresh_token)

    # Calculate expiry
    expiry_ts   = int(time.time()) + expires_in
    expiry_date = time.strftime("%Y-%m-%d", time.localtime(expiry_ts))
    set_key(ENV_FILE, "LINKEDIN_TOKEN_EXPIRY", expiry_date)

    print("\n" + "=" * 55)
    print("  SUCCESS — token saved to .env")
    print("=" * 55)
    print(f"  Access token : {access_token[:20]}...")
    print(f"  Person URN   : {person_urn}")
    print(f"  Expires      : {expiry_date}")
    if refresh_token:
        print(f"  Refresh token: {refresh_token[:20]}...")
    print()
    print("  Next step: Set up your Make.com scenario and")
    print("  add MAKE_WEBHOOK_URL to .env")
    print("=" * 55 + "\n")


# ── Token refresh helper (call from your app if needed) ──────────────────────
def refresh_access_token() -> str:
    """
    Use refresh token to get a new access token.
    Call this when LINKEDIN_TOKEN_EXPIRY is within 5 days.
    """
    load_dotenv()
    refresh_token = os.getenv("LINKEDIN_REFRESH_TOKEN", "")
    if not refresh_token:
        raise ValueError("No refresh token in .env — run linkedin_auth.py again")

    data = urllib.parse.urlencode({
        "grant_type":    "refresh_token",
        "refresh_token": refresh_token,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        token_data    = json.loads(resp.read())
        access_token  = token_data["access_token"]
        expires_in    = token_data.get("expires_in", 5184000)
        expiry_date   = time.strftime("%Y-%m-%d", time.localtime(time.time() + expires_in))

        set_key(ENV_FILE, "LINKEDIN_ACCESS_TOKEN", access_token)
        set_key(ENV_FILE, "LINKEDIN_TOKEN_EXPIRY",  expiry_date)
        if "refresh_token" in token_data:
            set_key(ENV_FILE, "LINKEDIN_REFRESH_TOKEN", token_data["refresh_token"])

        print(f"Token refreshed — new expiry: {expiry_date}")
        return access_token


def check_token_expiry() -> dict:
    """Check if token needs refreshing. Call this at app startup."""
    load_dotenv()
    expiry_str = os.getenv("LINKEDIN_TOKEN_EXPIRY", "")
    if not expiry_str:
        return {"status": "unknown", "days_left": None, "needs_refresh": True}

    expiry     = time.strptime(expiry_str, "%Y-%m-%d")
    expiry_ts  = time.mktime(expiry)
    days_left  = int((expiry_ts - time.time()) / 86400)

    return {
        "status":        "ok" if days_left > 5 else "expiring_soon" if days_left > 0 else "expired",
        "days_left":     days_left,
        "expiry_date":   expiry_str,
        "needs_refresh": days_left <= 5,
    }


if __name__ == "__main__":
    main()
