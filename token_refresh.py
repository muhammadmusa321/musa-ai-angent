import base64
import json
import os
import urllib.request
import urllib.parse
import urllib.error

from nacl import encoding, public
from utils.telegram_helper import send_telegram_message

INSTAGRAM_APP_ID = os.environ["INSTAGRAM_APP_ID"]
INSTAGRAM_APP_SECRET = os.environ["INSTAGRAM_APP_SECRET"]
CURRENT_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
GH_PAT = os.environ["GH_PAT"]
GITHUB_REPOSITORY = os.environ["GITHUB_REPOSITORY"]  # format: "owner/repo"

SECRET_NAME = "INSTAGRAM_ACCESS_TOKEN"


def refresh_long_lived_token():
    url = (
        "https://graph.facebook.com/v19.0/oauth/access_token"
        f"?grant_type=fb_exchange_token"
        f"&client_id={INSTAGRAM_APP_ID}"
        f"&client_secret={INSTAGRAM_APP_SECRET}"
        f"&fb_exchange_token={CURRENT_ACCESS_TOKEN}"
    )
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        new_token = data.get("access_token")
        expires_in = data.get("expires_in", "unknown")
        if not new_token:
            raise RuntimeError(f"No access_token in response: {data}")
        return new_token, expires_in
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise RuntimeError(f"HTTP {e.code} refreshing token: {error_body}")


def get_repo_public_key():
    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/secrets/public-key"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {GH_PAT}",
        "Accept": "application/vnd.github+json"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return data["key"], data["key_id"]


def encrypt_secret(public_key_b64, secret_value):
    public_key = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()


def update_github_secret(secret_name, secret_value):
    public_key_b64, key_id = get_repo_public_key()
    encrypted_value = encrypt_secret(public_key_b64, secret_value)

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/secrets/{secret_name}"
    payload = json.dumps({
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        method="PUT",
        headers={
            "Authorization": f"Bearer {GH_PAT}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def main():
    try:
        new_token, expires_in = refresh_long_lived_token()
        update_github_secret(SECRET_NAME, new_token)

        days_valid = "~60" if expires_in == "unknown" else round(int(expires_in) / 86400)
        send_telegram_message(
            f"🔑 Instagram access token refreshed successfully. "
            f"New token valid for approximately {days_valid} days."
        )
    except Exception as e:
        send_telegram_message(
            f"🚨 URGENT: Automatic token refresh FAILED.\n\n"
            f"Error: {e}\n\n"
            f"Your Instagram posting and reply automation will stop working once the "
            f"current token expires. You'll need to manually regenerate it via "
            f"Graph API Explorer (same process as initial setup) and update the "
            f"INSTAGRAM_ACCESS_TOKEN secret."
        )
        raise


if __name__ == "__main__":
    main()
