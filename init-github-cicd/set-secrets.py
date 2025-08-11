

# !/usr/bin/env python3
"""
GitHub Repository Secrets Setup Script
Usage: python setup_secrets.py <repository-url> <github-token>
"""

import sys
import re
import json
import base64
import getpass
import requests
from urllib.parse import urlparse
from nacl import encoding, public


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_status(message):
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")


def print_warning(message):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def print_error(message):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def extract_repo_info(repo_url):
    """Extract owner and repo name from GitHub URL"""
    patterns = [
        r'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$',
        r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    ]

    for pattern in patterns:
        match = re.search(pattern, repo_url)
        if match:
            owner = match.group(1)
            repo = match.group(2).rstrip('.git')
            return owner, repo

    return None, None


def encrypt_secret(public_key_b64, secret_value):
    """Encrypt a secret using GitHub's public key"""
    try:
        public_key_bytes = base64.b64decode(public_key_b64)
        public_key_obj = public.PublicKey(public_key_bytes)
        sealed_box = public.SealedBox(public_key_obj)
        encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print_error(f"Failed to encrypt secret: {e}")
        return None


def get_public_key(owner, repo, token):
    """Get the repository's public key for encryption"""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print_error(f"Failed to get public key: {e}")
        return None


def create_secret(owner, repo, token, secret_name, secret_value, key_id, public_key):
    """Create or update a repository secret"""
    encrypted_value = encrypt_secret(public_key, secret_value)
    if not encrypted_value:
        return False

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }

    data = {
        'encrypted_value': encrypted_value,
        'key_id': key_id
    }

    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code in [201, 204]:
            print_status(f"✓ Created secret: {secret_name}")
            return True
        else:
            print_error(f"✗ Failed to create secret: {secret_name} (HTTP {response.status_code})")
            return False
    except requests.RequestException as e:
        print_error(f"✗ Failed to create secret {secret_name}: {e}")
        return False


def verify_repo_access(owner, repo, token):
    """Verify that the token has access to the repository"""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    try:
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_secret_values():
    """Prompt user for secret values"""
    secrets = {}

    print("\nPlease provide the values for the secrets:")
    print()

    secrets['PRIVATE_KEY'] = getpass.getpass("PRIVATE_KEY (SSH private key): ")
    secrets['SERVER_ADDRESS'] = input("SERVER_ADDRESS (server IP/hostname): ").strip()
    secrets['SERVER_USERNAME'] = input("SERVER_USERNAME (SSH username): ").strip()
    secrets['SERVER_PATH'] = input("SERVER_PATH (deployment path): ").strip()

    return secrets


def main():
    if len(sys.argv) != 3:
        print_error("Usage: python setup_secrets.py <repository-url> <github-token>")
        print_error("Example: python setup_secrets.py https://github.com/username/repo ghp_xxxxxxxxxxxx")
        sys.exit(1)

    repo_url = sys.argv[1]
    github_token = sys.argv[2]

    # Extract repository information
    owner, repo = extract_repo_info(repo_url)
    if not owner or not repo:
        print_error("Invalid GitHub repository URL format")
        print_error("Expected format: https://github.com/owner/repo or git@github.com:owner/repo.git")
        sys.exit(1)

    print_status(f"Repository: {owner}/{repo}")

    # Verify repository access
    print_status("Verifying access to repository...")
    if not verify_repo_access(owner, repo, github_token):
        print_error(f"Cannot access repository {owner}/{repo}")
        print_error("Please check:")
        print_error("1. Repository exists and is accessible")
        print_error("2. GitHub token has 'repo' scope")
        print_error("3. Token has access to this repository")
        sys.exit(1)

    print_status("Repository access verified")

    # Get repository's public key
    print_status("Getting repository public key...")
    key_info = get_public_key(owner, repo, github_token)
    if not key_info:
        print_error("Failed to get repository public key")
        sys.exit(1)

    key_id = key_info['key_id']
    public_key = key_info['key']

    # Get secret values from user
    secrets = get_secret_values()

    # Validate that all secrets have values
    empty_secrets = [name for name, value in secrets.items() if not value.strip()]
    if empty_secrets:
        print_error(f"The following secrets cannot be empty: {', '.join(empty_secrets)}")
        sys.exit(1)

    # Create secrets
    print()
    print_status("Creating secrets...")

    success_count = 0
    for secret_name, secret_value in secrets.items():
        if create_secret(owner, repo, github_token, secret_name, secret_value, key_id, public_key):
            success_count += 1

    print()
    if success_count == len(secrets):
        print_status("🎉 All secrets have been set up successfully!")
        print_status(f"You can verify them at: https://github.com/{owner}/{repo}/settings/secrets/actions")
    else:
        print_error(f"Only {success_count}/{len(secrets)} secrets were created successfully")
        sys.exit(1)


if __name__ == "__main__":
    try:
        import nacl
    except ImportError:
        print_error("PyNaCl library is required for encryption")
        print_error("Install it with: pip install PyNaCl requests")
        sys.exit(1)

    main()