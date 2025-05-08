import argparse
import sys
import requests
import json

import os

REGISTER_URL = os.environ.get("JENTIC_API_URL", "https://api.jentic.com")
REGISTER_URL = REGISTER_URL.rstrip("/") + "/api/v1/auth/register"

def register(email: str = None):
    payload = {"email": email} if email else {}
    headers = {"Content-Type": "application/json"}
    response = requests.post(REGISTER_URL, headers=headers, data=json.dumps(payload))
    try:
        data = response.json()
        uuid = data.get("uuid")
        if uuid:
            print(f"Your Jentic UUID: {uuid}")
            print("\nSave this UUID in your environment:")
            print(f"export JENTIC_UUID={uuid}")
        else:
            print(f"{response.status_code} {response.text}")
            sys.exit(1)
    except Exception:
        print(f"{response.status_code} {response.text}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Jentic CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Register command
    register_parser = subparsers.add_parser("register", help="Register and obtain a Jentic UUID")
    register_parser.add_argument("--email", type=str, help="Optional email for higher rate limits and early access")

    args = parser.parse_args()

    if args.command == "register":
        register(email=args.email)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
