# GitHub Repository Secrets Setup Scripts

Automated scripts to set up the 4 essential GitHub Action secrets for deployment:
- `PRIVATE_KEY` (SSH private key)
- `SERVER_ADDRESS` (server IP/hostname) 
- `SERVER_USERNAME` (SSH username)
- `SERVER_PATH` (deployment path)

Both Python and Bash versions are available with identical functionality.

## 🔑 Prerequisites

### 1. Create GitHub Personal Access Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Give it a descriptive name (e.g., "Secrets Management")
4. Select the **`repo`** scope (this provides full repository access)
5. Click **"Generate token"**
6. **Copy the token immediately** (starts with `ghp_`) - you won't see it again!

### 2. Install Dependencies

**For Python version:**
```bash
pip install PyNaCl requests
```

**For Bash version:**
```bash
# PyNaCl is still required for encryption
pip install PyNaCl
```

## 🐍 Python Version

### Download and Setup
```bash
# Download the script
curl -O https://raw.githubusercontent.com/your-repo/setup_secrets.py
# Or create the file and copy the content

# Make it executable (optional)
chmod +x setup_secrets.py
```

### Usage
```bash
python setup_secrets.py <repository-url> <github-token>
```

### Examples
```bash
# Basic usage
python setup_secrets.py https://github.com/myuser/myproject ghp_abc123xyz

# Works with different URL formats
python setup_secrets.py git@github.com:myuser/myproject.git ghp_abc123xyz
python setup_secrets.py https://github.com/myuser/myproject.git ghp_abc123xyz
```

### Features
- ✅ Clean Python code with proper error handling
- ✅ Secure input using `getpass` (hides sensitive values)
- ✅ Colored terminal output for better readability
- ✅ Comprehensive URL validation
- ✅ Token and repository access verification

## 🔧 Bash Version

### Download and Setup
```bash
# Download the script
curl -O https://raw.githubusercontent.com/your-repo/setup-secrets.sh
# Or create the file and copy the content

# Make it executable
chmod +x setup-secrets.sh
```

### Usage
```bash
./setup-secrets.sh <repository-url> <github-token>
```

### Examples
```bash
# Basic usage
./setup-secrets.sh https://github.com/myuser/myproject ghp_abc123xyz

# Works with SSH URLs too
./setup-secrets.sh git@github.com:myuser/myproject.git ghp_abc123xyz
```

### Features
- ✅ Native bash with minimal dependencies
- ✅ Secure password input with `-s` flag
- ✅ Colored output for status messages
- ✅ Cross-platform compatibility (Linux/macOS/WSL)

## 📋 Interactive Prompts

Both scripts will prompt you for the following values:

```
PRIVATE_KEY (SSH private key): [hidden input]
SERVER_ADDRESS (server IP/hostname): your-server.com
SERVER_USERNAME (SSH username): deploy
SERVER_PATH (deployment path): /var/www/html
```

**Important Notes:**
- `PRIVATE_KEY` input is hidden for security
- Press Enter after each value
- All fields are required (cannot be empty)

## 🔒 Security Features

### Encryption
- Secrets are encrypted using GitHub's public key before transmission
- Uses industry-standard NaCl (Networking and Cryptography library)
- No plaintext secrets are stored or transmitted

### Token Safety
- Script verifies token has proper `repo` scope
- Validates repository access before making changes
- No tokens are logged or stored

### Input Protection
- SSH private key input is masked/hidden
- Script validates all inputs before processing
- Secure HTTPS communication with GitHub API

## 🚨 Troubleshooting

### Common Issues

**"PyNaCl library is required"**
```bash
pip install PyNaCl
# or
pip3 install PyNaCl
```

**"Cannot access repository"**
- ✅ Check repository exists and is spelled correctly
- ✅ Verify token has `repo` scope (not just `public_repo`)
- ✅ Ensure you have access to the repository (owner/collaborator)

**"Invalid GitHub repository URL"**
- ✅ Use format: `https://github.com/owner/repo`
- ✅ Or SSH format: `git@github.com:owner/repo.git`
- ✅ Don't include trailing slashes or extra paths

**"Failed to encrypt secret"**
- ✅ Ensure PyNaCl is properly installed
- ✅ Check that the private key format is correct
- ✅ Try updating PyNaCl: `pip install --upgrade PyNaCl`

### Token Scopes Required

Your GitHub token needs the **`repo`** scope, which includes:
- `repo:status` - Access commit status
- `repo_deployment` - Access deployment status  
- `public_repo` - Access public repositories
- `repo:invite` - Access repository invitations
- **Full control of private repositories**

## 📁 File Structure

After running either script successfully, your repository will have these secrets:

```
Repository Settings → Secrets and variables → Actions
├── PRIVATE_KEY ●●●●●●●● (SSH private key)
├── SERVER_ADDRESS ●●●●●●●● (Server hostname/IP)  
├── SERVER_USERNAME ●●●●●●●● (SSH username)
└── SERVER_PATH ●●●●●●●● (Deployment directory)
```

## 🔄 Usage in GitHub Actions

Once secrets are set up, use them in your workflows:

```yaml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.SERVER_ADDRESS }}
          username: ${{ secrets.SERVER_USERNAME }}
          key: ${{ secrets.PRIVATE_KEY }}
          script: |
            cd ${{ secrets.SERVER_PATH }}
            # Your deployment commands here
```

## ❓ FAQ

**Q: Which version should I use?**
A: Use Python if you're comfortable with Python and want better error handling. Use Bash if you prefer shell scripts or have Python dependency constraints.

**Q: Can I run this on Windows?**
A: Yes! Python version works on Windows. Bash version works in WSL, Git Bash, or any Unix-like environment.

**Q: Are my secrets safe?**
A: Yes. Secrets are encrypted before transmission and stored securely by GitHub. The scripts don't log or store any sensitive data.

**Q: Can I update existing secrets?**
A: Yes! Both scripts will update existing secrets if they already exist.

**Q: Can I use this for multiple repositories?**
A: Currently, you need to run the script once per repository. You can create a wrapper script to batch process multiple repos if needed.

## 📄 License

These scripts are provided as-is for educational and practical use. Feel free to modify and distribute according to your needs.

---

**💡 Pro Tip:** Store your commonly used values (like `SERVER_ADDRESS`, `SERVER_USERNAME`, `SERVER_PATH`) in a secure note-taking app so you can quickly copy-paste them when setting up new repositories!