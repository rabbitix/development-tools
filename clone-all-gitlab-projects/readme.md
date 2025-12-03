# GitLab Repository Cloning Workflow

This documentation describes how to clone all GitLab repositories you have access to while preserving the original GitLab namespace structure.
 

## Prerequisites

- Git installed on your system
- Python 3.x installed
- GitLab account with API access
- Personal Access Token with `read_api` scope
- SSH key configured in your GitLab account

## Setup Instructions

### 1. Obtain GitLab Personal Access Token

1. Log in to your GitLab account
2. Navigate to `Settings` > `Access Tokens`
3. Create a new token with:
   - Scopes: `read_api` (check this box)
4. Copy the generated token (you won't be able to see it again!)

### 2. Configure the Scripts

Edit `fetch_repos.py` and replace these values:

```python
# Configuration
ACCESS_TOKEN = "your_personal_access_token"  # Replace with your token
```

## Usage Workflow

### Step 1: Fetch Repository List

Run the Python script to generate the repository list:

```python
python3 fetch_repos.py
```

This will:
- Connect to GitLab's API
- List all repositories you have access to
- Create repos.txt with SSH URLs and paths

### Step 2: Clone All Repositories

Make the bash script executable and run it:
```shell
chmod +x clone_repos.sh
./clone_repos.sh
```
The script will:
- Read from repos.txt
- Create directory structure matching GitLab namespaces
- Clone each repository into its proper location

### Output Structure
```
~/work/project/
    ├── group1/
    │   ├── project1/
    │   └── subgroup/
    │       └── project2/
    └── group2/
        └── project3/
```