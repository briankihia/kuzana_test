#!/usr/bin/env python3
import os
import sys
import argparse
import requests
def main():
    parser = argparse.ArgumentParser(description="Sync a local Obsidian vault directory to Kuzana-Brain.")
    parser.add_argument("--vault", required=True, help="Path to your local Obsidian vault directory")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the Kuzana-Brain backend API")
    parser.add_argument("--email", help="Your Kuzana account email (ignored if --token is set)")
    parser.add_argument("--password", help="Your Kuzana account password (ignored if --token is set)")
    parser.add_argument("--token", help="Static sync token to authenticate directly")
    
    args = parser.parse_args()
    
    vault_path = os.path.abspath(args.vault)
    if not os.path.exists(vault_path) or not os.path.isdir(vault_path):
        print(f"Error: Vault path '{vault_path}' does not exist or is not a directory.")
        sys.exit(1)
        
    token = args.token
    if not token:
        if not args.email or not args.password:
            print("Error: Either --token or both --email and --password must be provided.")
            sys.exit(1)
            
        print("Authenticating with Kuzana-Brain...")
        login_url = f"{args.url.rstrip('/')}/auth/login"
        try:
            r = requests.post(login_url, json={"email": args.email, "password": args.password}, timeout=10)
            r.raise_for_status()
            token = r.json().get("token")
            if not token:
                print("Error: Could not retrieve auth token.")
                sys.exit(1)
            print("Authenticated successfully!")
        except Exception as e:
            print(f"Error authenticating: {e}")
            sys.exit(1)
    else:
        print("Using provided static sync token.")
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Walk the vault and collect markdown/txt files
    print(f"Scanning vault folder: {vault_path}...")
    sync_files = []
    for root, dirs, files in os.walk(vault_path):
        # Skip hidden directories like .obsidian
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.lower().endswith((".md", ".txt", ".markdown")):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, vault_path)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    sync_files.append({
                        "path": rel_path,
                        "content": content
                      })
                except Exception as e:
                    print(f"Warning: Failed to read {rel_path}: {e}")
                    
    if not sync_files:
        print("No markdown or text notes found to sync.")
        sys.exit(0)
        
    print(f"Syncing {len(sync_files)} files to Kuzana-Brain...")
    sync_url = f"{args.url.rstrip('/')}/sync/vault"
    try:
        r = requests.post(sync_url, headers=headers, json={"files": sync_files}, timeout=30)
        r.raise_for_status()
        res = r.json()
        print(f"Success! Synced {res.get('synced_count')} files.")
        updated = res.get("updated_doc_ids", [])
        if updated:
            print(f"Updated/Created doc IDs: {updated}")
        else:
            print("All notes were already in sync.")
    except Exception as e:
        print(f"Error syncing notes: {e}")
        sys.exit(1)
if __name__ == "__main__":
    main()
