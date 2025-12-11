#!/usr/bin/env python3
"""
GitLab Structure Creator from Markdown (using REST API)

This script reads a markdown file with a hierarchical structure and creates
corresponding GitLab groups, subgroups, and repositories using the GitLab REST API.

Requirements:
    pip install requests

Usage:
    python gitlab_structure_creator.py --file structure.md --gitlab-url https://gitlab.com --token YOUR_TOKEN
"""

import re
import argparse
import requests
from typing import List, Dict, Optional
import time


class MarkdownParser:
    """Parse markdown hierarchical structure."""
    
    def __init__(self, content: str):
        self.content = content
        self.structure = []
    
    def parse(self) -> List[Dict]:
        """Parse the markdown content and return hierarchical structure."""
        lines = self.content.strip().split('\n')
        stack = []  # Stack to keep track of parent items
        
        for line in lines:
            if not line.strip() or line.strip().startswith('```'):
                continue
            
            # Count indentation level (spaces or tabs)
            indent_match = re.match(r'^(\s*)-\s+(.+)$', line)
            if not indent_match:
                continue
            
            indent = len(indent_match.group(1))
            name = indent_match.group(2).strip()
            
            # Calculate level (each 2 spaces = 1 level)
            level = indent // 2
            
            item = {
                'name': name,
                'level': level,
                'children': []
            }
            
            # Pop items from stack that are at same or deeper level
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            
            # Add as child to parent or as root
            if stack:
                stack[-1]['children'].append(item)
            else:
                self.structure.append(item)
            
            stack.append(item)
        
        return self.structure


class GitLabAPI:
    """GitLab REST API client."""
    
    def __init__(self, gitlab_url: str, token: str):
        """Initialize GitLab API client."""
        self.base_url = gitlab_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v4"
        self.headers = {
            'PRIVATE-TOKEN': token,
            'Content-Type': 'application/json'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_current_user(self) -> Dict:
        """Get current user information."""
        response = self.session.get(f"{self.api_url}/user")
        response.raise_for_status()
        return response.json()
    
    def create_group(self, name: str, path: str, parent_id: Optional[int] = None, visibility: str = 'private') -> Dict:
        """
        Create a new group.
        
        Args:
            name: Group name
            path: URL path for the group
            parent_id: Parent group ID (for subgroups)
            visibility: Group visibility (private, internal, public)
        
        Returns:
            Created group data
        """
        data = {
            'name': name,
            'path': path,
            'visibility': visibility
        }
        
        if parent_id:
            data['parent_id'] = parent_id
        
        response = self.session.post(f"{self.api_url}/groups", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_group(self, group_id: int) -> Dict:
        """Get group information by ID."""
        response = self.session.get(f"{self.api_url}/groups/{group_id}")
        response.raise_for_status()
        return response.json()
    
    def search_groups(self, search: str, parent_id: Optional[int] = None) -> List[Dict]:
        """
        Search for groups by name.
        
        Args:
            search: Search query
            parent_id: Filter by parent group ID
        
        Returns:
            List of matching groups
        """
        params = {'search': search}
        response = self.session.get(f"{self.api_url}/groups", params=params)
        response.raise_for_status()
        groups = response.json()
        
        # Filter by parent_id if specified
        if parent_id is not None:
            groups = [g for g in groups if g.get('parent_id') == parent_id]
        
        return groups
    
    def create_project(self, name: str, path: str, namespace_id: Optional[int] = None, visibility: str = 'private') -> Dict:
        """
        Create a new project.
        
        Args:
            name: Project name
            path: URL path for the project
            namespace_id: Group/namespace ID where project will be created
            visibility: Project visibility (private, internal, public)
        
        Returns:
            Created project data
        """
        data = {
            'name': name,
            'path': path,
            'visibility': visibility
        }
        
        if namespace_id:
            data['namespace_id'] = namespace_id
        
        response = self.session.post(f"{self.api_url}/projects", json=data)
        response.raise_for_status()
        return response.json()
    
    def search_projects(self, search: str) -> List[Dict]:
        """Search for projects by name."""
        params = {'search': search}
        response = self.session.get(f"{self.api_url}/projects", params=params)
        response.raise_for_status()
        return response.json()


class GitLabStructureCreator:
    """Create GitLab groups and repositories based on parsed structure."""
    
    def __init__(self, gitlab_url: str, token: str, parent_group_id: Optional[int] = None, dry_run: bool = False):
        """
        Initialize GitLab structure creator.
        
        Args:
            gitlab_url: GitLab instance URL
            token: Personal access token with API access
            parent_group_id: Optional parent group ID to create everything under
            dry_run: If True, only print what would be created without actually creating
        """
        self.dry_run = dry_run
        self.parent_group_id = parent_group_id
        
        if not dry_run:
            self.api = GitLabAPI(gitlab_url, token)
            try:
                user = self.api.get_current_user()
                print(f"✓ Authenticated to GitLab as: {user['username']}")
            except requests.exceptions.RequestException as e:
                print(f"✗ Authentication failed: {e}")
                raise
        else:
            print("✓ Running in DRY RUN mode - no changes will be made")
    
    def create_structure(self, structure: List[Dict], parent_id: Optional[int] = None, path_prefix: str = ""):
        """
        Recursively create groups and projects.
        
        Args:
            structure: Parsed structure from markdown
            parent_id: Parent group ID
            path_prefix: Path prefix for display
        """
        if parent_id is None:
            parent_id = self.parent_group_id
        
        for item in structure:
            name = item['name']
            full_path = f"{path_prefix}/{name}" if path_prefix else name
            
            # Determine if this is a repository (leaf node) or group (has children)
            is_repo = len(item['children']) == 0
            
            if is_repo:
                self._create_project(name, parent_id, full_path)
            else:
                # Create group and recurse
                group_id = self._create_group(name, parent_id, full_path)
                if item['children'] and group_id:
                    self.create_structure(item['children'], group_id, full_path)
    
    def _create_group(self, name: str, parent_id: Optional[int], full_path: str) -> Optional[int]:
        """Create a GitLab group."""
        path = name.lower().replace(' ', '-').replace('_', '-')
        
        if self.dry_run:
            parent_info = f" (parent: {parent_id})" if parent_id else ""
            print(f"[DRY RUN] Would create GROUP: {full_path}{parent_info}")
            return None
        
        try:
            group = self.api.create_group(name, path, parent_id)
            print(f"✓ Created group: {full_path} (ID: {group['id']})")
            time.sleep(0.5)  # Rate limiting
            return group['id']
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_message = e.response.json().get('message', {})
                if 'has already been taken' in str(error_message):
                    print(f"⚠ Group already exists: {full_path}")
                    # Try to find existing group
                    try:
                        groups = self.api.search_groups(name, parent_id)
                        for g in groups:
                            if g['path'] == path and g.get('parent_id') == parent_id:
                                print(f"  → Using existing group ID: {g['id']}")
                                return g['id']
                    except Exception as search_err:
                        print(f"  → Could not find existing group: {search_err}")
                else:
                    print(f"✗ Error creating group {full_path}: {error_message}")
            else:
                print(f"✗ Error creating group {full_path}: {e}")
            return None
    
    def _create_project(self, name: str, namespace_id: Optional[int], full_path: str):
        """Create a GitLab project (repository)."""
        path = name.lower().replace(' ', '-').replace('_', '-')
        
        if self.dry_run:
            namespace_info = f" (namespace: {namespace_id})" if namespace_id else ""
            print(f"[DRY RUN] Would create PROJECT: {full_path}{namespace_info}")
            return
        
        try:
            project = self.api.create_project(name, path, namespace_id)
            print(f"✓ Created project: {full_path} (ID: {project['id']})")
            time.sleep(0.5)  # Rate limiting
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_message = e.response.json().get('message', {})
                if 'has already been taken' in str(error_message):
                    print(f"⚠ Project already exists: {full_path}")
                else:
                    print(f"✗ Error creating project {full_path}: {error_message}")
            else:
                print(f"✗ Error creating project {full_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Create GitLab groups and repositories from markdown structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example markdown structure:
  - narbit
    - commons
      - narbit-commons-lib
      - narbit-services-serve
    - platform
      - price
        - narbit-price-lib
        - narbit-price-serve

Example usage:
  python gitlab_structure_creator.py --file structure.md --gitlab-url https://gitlab.com --token YOUR_TOKEN
  python gitlab_structure_creator.py --file structure.md --gitlab-url https://gitlab.com --token YOUR_TOKEN --dry-run
        """
    )
    
    parser.add_argument('--file', '-f', required=True, help='Markdown file with structure')
    parser.add_argument('--gitlab-url', '-u', required=True, help='GitLab instance URL (e.g., https://gitlab.com)')
    parser.add_argument('--token', '-t', required=True, help='GitLab personal access token')
    parser.add_argument('--parent-group-id', '-p', type=int, help='Parent group ID to create everything under')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Print what would be created without actually creating')
    
    args = parser.parse_args()
    
    # Read markdown file
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"✗ Error: File '{args.file}' not found")
        return 1
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return 1
    
    # Parse structure
    print("\n" + "="*60)
    print("Parsing markdown structure...")
    print("="*60 + "\n")
    
    parser_obj = MarkdownParser(content)
    structure = parser_obj.parse()
    
    if not structure:
        print("✗ No valid structure found in markdown file")
        return 1
    
    print(f"✓ Parsed structure with {len(structure)} root item(s)\n")
    
    # Create GitLab structure
    print("="*60)
    print("Creating GitLab structure...")
    print("="*60 + "\n")
    
    try:
        creator = GitLabStructureCreator(
            args.gitlab_url,
            args.token,
            args.parent_group_id,
            args.dry_run
        )
        
        creator.create_structure(structure)
        
        print("\n" + "="*60)
        print("✓ Completed!")
        print("="*60)
        
        return 0
    
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        return 1


if __name__ == '__main__':
    exit(main())