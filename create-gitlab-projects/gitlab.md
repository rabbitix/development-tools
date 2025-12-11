# GitLab Structure Creator (REST API)

A Python script that reads a markdown file with a hierarchical structure and automatically creates corresponding GitLab groups, subgroups, and repositories using the **GitLab REST API directly** (no external packages except `requests`).

## Features

- ✅ Uses GitLab REST API directly (no `python-gitlab` dependency)
- 📁 Parse markdown files with indented list structure
- 🏢 Create GitLab groups and subgroups automatically
- 📦 Create repositories at leaf nodes
- 👪 Support for parent groups
- 🧪 Dry-run mode to preview changes
- ⚠️ Handles existing groups/projects gracefully
- 🔄 Automatic rate limiting to avoid API throttling

## Installation

```bash
pip install requests
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

## GitLab Token Setup

You need a GitLab Personal Access Token with the following scopes:
- `api` - Full API access

To create a token:
1. Go to your GitLab instance (e.g., https://gitlab.com)
2. Click on your avatar → Settings → Access Tokens
3. Create a new token with `api` scope
4. Copy the token (you won't see it again!)

## Usage

### Basic Usage

```bash
python gitlab.py \
  --file structure.md \
  --gitlab-url https://gitlab.com \
  --token YOUR_GITLAB_TOKEN
```

### Dry Run (Preview Only)

```bash
python gitlab_structure_creator.py \
  --file structure.md \
  --gitlab-url https://gitlab.com \
  --token YOUR_GITLAB_TOKEN \
  --dry-run
```

### Create Under Parent Group

```bash
python gitlab_structure_creator.py \
  --file structure.md \
  --gitlab-url https://gitlab.com \
  --token YOUR_GITLAB_TOKEN \
  --parent-group-id 12345
```

## Markdown Structure Format

The script expects a markdown file with indented lists (2 spaces per level):

```markdown
- narbit
  - commons
    - narbit-commons-lib
    - narbit-services-serve
  - platform
    - price
      - narbit-price-lib
      - narbit-price-serve
```

**Rules:**
- Items with children → Created as **Groups**
- Items without children (leaf nodes) → Created as **Projects/Repositories**
- 2 spaces = 1 level of indentation
- Names are converted to URL-safe paths (lowercase, hyphens)

## Command Line Options

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--file` | `-f` | Yes | Path to markdown file |
| `--gitlab-url` | `-u` | Yes | GitLab instance URL |
| `--token` | `-t` | Yes | Personal access token |
| `--parent-group-id` | `-p` | No | Parent group ID |
| `--dry-run` | `-d` | No | Preview without creating |

## Example Structure

For your narbit structure:

```markdown
- narbit                           # Root group
  - commons                       # Subgroup
    - narbit-commons-lib           # Project
    - narbit-services-serve        # Project
  - platform                      # Subgroup
    - price                       # Sub-subgroup
      - narbit-price-lib           # Project
      - narbit-price-serve         # Project
```

This creates:
- **Group:** narbit
  - **Subgroup:** narbit/commons
    - **Project:** narbit/commons/narbit-commons-lib
    - **Project:** narbit/commons/narbit-services-serve
  - **Subgroup:** narbit/platform
    - **Subgroup:** narbit/platform/price
      - **Project:** narbit/platform/price/narbit-price-lib
      - **Project:** narbit/platform/price/narbit-price-serve

## API Endpoints Used

The script uses the following GitLab REST API endpoints:

- `GET /api/v4/user` - Authentication verification
- `POST /api/v4/groups` - Create groups/subgroups
- `GET /api/v4/groups` - Search existing groups
- `POST /api/v4/projects` - Create projects/repositories
- `GET /api/v4/projects` - Search existing projects

## Example Output

```
============================================================
Parsing markdown structure...
============================================================

✓ Parsed structure with 1 root item(s)

============================================================
Creating GitLab structure...
============================================================

✓ Authenticated to GitLab as: alex
✓ Created group: narbit (ID: 12345)
✓ Created group: narbit/commons (ID: 12346)
✓ Created project: narbit/commons/narbit-commons-lib (ID: 12347)
✓ Created project: narbit/commons/narbit-services-serve (ID: 12348)
✓ Created group: narbit/platform (ID: 12349)
✓ Created group: narbit/platform/price (ID: 12350)
✓ Created project: narbit/platform/price/narbit-price-lib (ID: 12351)
✓ Created project: narbit/platform/price/narbit-price-serve (ID: 12352)

============================================================
✓ Completed!
============================================================
```

## Rate Limiting

The script includes automatic rate limiting:
- 0.5 second delay between each API call
- Prevents hitting GitLab's rate limits
- Can be adjusted in the code if needed

## Error Handling

The script handles common scenarios:

- **Already exists:** Warns and tries to reuse existing groups (⚠)
- **Authentication failed:** Shows error message (✗)
- **Invalid token:** Shows error message (✗)
- **File not found:** Shows error message (✗)
- **API errors:** Shows detailed error messages

## Security Notes

- Never commit your GitLab token to version control
- Use environment variables for tokens:
  ```bash
  export GITLAB_TOKEN="your-token-here"
  python gitlab_structure_creator.py \
    --file structure.md \
    --gitlab-url https://gitlab.com \
    --token $GITLAB_TOKEN
  ```
- All projects are created as **private** by default
- Groups are also created as **private** by default

## API Response Structure

The script handles GitLab API responses in the following format:

**Group creation:**
```json
{
  "id": 12345,
  "name": "narbit",
  "path": "narbit",
  "parent_id": null,
  "visibility": "private"
}
```

**Project creation:**
```json
{
  "id": 67890,
  "name": "narbit-commons-lib",
  "path": "narbit-commons-lib",
  "namespace": {
    "id": 12346
  },
  "visibility": "private"
}
```

## Troubleshooting

### "Authentication failed"
- Check your token is valid and not expired
- Ensure token has `api` scope
- Verify GitLab URL is correct (include https://)

### "has already been taken"
- Groups/projects with same name exist
- Script will try to reuse existing groups for substructure
- Use dry-run mode first to see what exists

### "Permission denied"
- Token needs sufficient permissions
- You need at least Maintainer role in parent group (if using `--parent-group-id`)

### Rate limit errors
- Script includes built-in delays
- If you still hit limits, increase the `time.sleep()` value in the code

## Advantages Over python-gitlab Package

- ✅ No external dependencies except `requests`
- ✅ Full control over API calls
- ✅ Easier to debug and customize
- ✅ Better understanding of GitLab API
- ✅ Simpler error handling
- ✅ Lightweight and portable

## License

MIT License - Feel free to modify and use as needed.