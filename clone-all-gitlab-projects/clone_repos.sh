#!/bin/bash

# Define the file containing the repository SSH addresses and paths
REPO_FILE="repos.txt"

# Define the base directory where repositories will be cloned
WORK_DIR="$HOME/work"

# Create the base work directory if it does not exist
mkdir -p "$WORK_DIR"

# Check if the file exists
if [[ ! -f "$REPO_FILE" ]]; then
    echo "Error: $REPO_FILE not found!"
    exit 1
fi

# Read each line from the file and clone the repository
while IFS= read -r line; do
    if [[ -n "$line" ]]; then
        # Split line into URL and path
        read -r repo_url repo_path <<< "$line"

        # Create full target path
        target_dir="$WORK_DIR/$repo_path"

        # Create parent directories if they don't exist
        mkdir -p "$(dirname "$target_dir")"

        echo "Cloning $repo_url into $target_dir"
        git clone "$repo_url" "$target_dir"
    else
        echo "Skipping empty line"
    fi
done < "$REPO_FILE"

echo "All repositories cloned!"