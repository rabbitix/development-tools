import requests
import os

# Configuration
GITLAB_URL = "your-gitlab-url"
ACCESS_TOKEN = "your_personal_access_token"  # Replace with your token
OUTPUT_FILE = "repos.txt"   


def get_all_repositories():
    headers = {"PRIVATE-TOKEN": ACCESS_TOKEN}
    repos = []
    page = 1
    per_page = 100  

    while True:
        url = f"{GITLAB_URL}/api/v4/projects?membership=true&page={page}&per_page={per_page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error fetching repositories: {response.status_code}")
            print(response.text)
            break

        current_page_repos = response.json()
        if not current_page_repos:
            break

        for repo in current_page_repos:
            # Get SSH URL and full path with namespace
            ssh_url = repo.get('ssh_url_to_repo', '')
            path_with_namespace = repo.get('path_with_namespace', '')
            if ssh_url and path_with_namespace:
                repos.append((ssh_url, path_with_namespace))

        page += 1

    return repos


def save_to_file(repositories, filename):
    with open(filename, 'w') as f:
        for repo in repositories:
            f.write(f"{repo[0]} {repo[1]}\n")


def main():
    print("Fetching all repositories you have access to...")
    repositories = get_all_repositories()

    if not repositories:
        print("No repositories found or error occurred.")
        return

    print(f"Found {len(repositories)} repositories.")
    save_to_file(repositories, OUTPUT_FILE)
    print(f"Repository SSH URLs and paths saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()