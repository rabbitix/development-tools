#!/bin/bash

# GitHub Repository Secrets Setup Script
# Usage: ./setup-secrets.sh <repository-url> <github-token>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required arguments are provided
if [ $# -ne 2 ]; then
    print_error "Usage: $0 <repository-url> <github-token>"
    print_error "Example: $0 https://github.com/username/repo ghp_xxxxxxxxxxxx"
    exit 1
fi

REPO_URL="$1"
GITHUB_TOKEN="$2"

# Extract owner and repo name from URL
if [[ $REPO_URL =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    # Remove .git suffix if present
    REPO="${REPO%.git}"
else
    print_error "Invalid GitHub repository URL format"
    print_error "Expected format: https://github.com/owner/repo or git@github.com:owner/repo.git"
    exit 1
fi

print_status "Repository: $OWNER/$REPO"

# Prompt for secret values
echo
print_status "Please provide the values for the secrets:"
echo

read -p "PRIVATE_KEY (SSH private key): " -s PRIVATE_KEY
echo
read -p "SERVER_ADDRESS (server IP/hostname): " SERVER_ADDRESS
read -p "SERVER_USERNAME (SSH username): " SERVER_USERNAME
read -p "SERVER_PATH (deployment path): " SERVER_PATH

echo
print_status "Setting up secrets for $OWNER/$REPO..."

# Function to create a secret
create_secret() {
    local secret_name="$1"
    local secret_value="$2"
    
    # Encrypt the secret value using GitHub's public key
    local public_key_response=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$OWNER/$REPO/actions/secrets/public-key")
    
    if [ $? -ne 0 ]; then
        print_error "Failed to get repository public key"
        return 1
    fi
    
    local key_id=$(echo "$public_key_response" | grep -o '"key_id":"[^"]*' | cut -d'"' -f4)
    local public_key=$(echo "$public_key_response" | grep -o '"key":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$key_id" ] || [ -z "$public_key" ]; then
        print_error "Failed to extract public key information"
        return 1
    fi
    
    # Use Python to encrypt the secret (requires PyNaCl library)
    local encrypted_value=$(python3 -c "
import base64
from nacl import encoding, public

def encrypt_secret(public_key: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')

print(encrypt_secret('$public_key', '''$secret_value'''))
" 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$encrypted_value" ]; then
        print_error "Failed to encrypt secret. Make sure PyNaCl is installed: pip install PyNaCl"
        return 1
    fi
    
    # Create the secret
    local response=$(curl -s -w "%{http_code}" -X PUT \
        -H "Authorization: token $GITHUB_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"encrypted_value\":\"$encrypted_value\",\"key_id\":\"$key_id\"}" \
        "https://api.github.com/repos/$OWNER/$REPO/actions/secrets/$secret_name")
    
    local http_code="${response: -3}"
    
    if [ "$http_code" = "201" ] || [ "$http_code" = "204" ]; then
        print_status "✓ Created secret: $secret_name"
        return 0
    else
        print_error "✗ Failed to create secret: $secret_name (HTTP $http_code)"
        return 1
    fi
}

# Check if Python and PyNaCl are available
python3 -c "import nacl" 2>/dev/null
if [ $? -ne 0 ]; then
    print_error "PyNaCl library is required for encryption"
    print_error "Install it with: pip install PyNaCl"
    exit 1
fi

# Verify GitHub token has access to the repository
print_status "Verifying access to repository..."
repo_check=$(curl -s -w "%{http_code}" -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$OWNER/$REPO")

http_code="${repo_check: -3}"
if [ "$http_code" != "200" ]; then
    print_error "Cannot access repository $OWNER/$REPO"
    print_error "Please check:"
    print_error "1. Repository exists and is accessible"
    print_error "2. GitHub token has 'repo' scope"
    print_error "3. Token has access to this repository"
    exit 1
fi

print_status "Repository access verified"

# Create all secrets
echo
print_status "Creating secrets..."

create_secret "PRIVATE_KEY" "$PRIVATE_KEY"
create_secret "SERVER_ADDRESS" "$SERVER_ADDRESS"
create_secret "SERVER_USERNAME" "$SERVER_USERNAME"
create_secret "SERVER_PATH" "$SERVER_PATH"

echo
print_status "🎉 All secrets have been set up successfully!"
print_status "You can verify them at: https://github.com/$OWNER/$REPO/settings/secrets/actions"