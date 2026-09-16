"""Google OAuth (spec §5.3). Desktop app client, loopback redirect. Calendar-only scope
for now — Gmail is Phase 2 and gets its own incremental-auth pass when that collector exists.
"""
from __future__ import annotations

import json

from google_auth_oauthlib.flow import InstalledAppFlow

from lifeos.secrets import get_secret, set_secret_value

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleAuthError(RuntimeError):
    pass


def run_google_auth(account: str, scopes: list[str] | None = None) -> None:
    client_json = get_secret("google_client")
    if not client_json:
        raise GoogleAuthError(
            "google_client not found in Keychain. Run: uv run lifeos secret set google_client "
            "(paste the full OAuth client JSON downloaded from Google Cloud Console)."
        )
    client_config = json.loads(client_json)

    flow = InstalledAppFlow.from_client_config(client_config, scopes=scopes or CALENDAR_SCOPES)
    creds = flow.run_local_server(port=0)

    set_secret_value(f"google_token:{account}", creds.to_json())
