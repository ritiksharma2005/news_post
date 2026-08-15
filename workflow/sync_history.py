import json
import os
import subprocess

HISTORY_FILE = "data/published_history.json"

def sync_history():
    print("[Sync History] Starting conflict-free history sync...")
    if not os.path.exists(HISTORY_FILE):
        print("[Sync History] Local history file does not exist. Nothing to merge.")
        return

    # Load local history
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            local_data = json.load(f)
    except Exception as e:
        print(f"[Sync History] Error loading local history: {e}")
        return

    # Try to checkout the remote history file to a temp path
    temp_remote_file = "data/remote_history.json"
    try:
        # Fetch latest origin
        subprocess.run(["git", "fetch", "origin", "main"], check=True)
        # Checkout the remote version of history file from origin/main to temp path
        with open(temp_remote_file, "w", encoding="utf-8") as f:
            subprocess.run(["git", "show", "origin/main:data/published_history.json"], stdout=f, check=True)
    except Exception as e:
        print(f"[Sync History] No remote history file found or fetch failed: {e}")
        if os.path.exists(temp_remote_file):
            os.remove(temp_remote_file)
        return

    # Load remote history
    try:
        with open(temp_remote_file, "r", encoding="utf-8") as f:
            remote_data = json.load(f)
    except Exception as e:
        print(f"[Sync History] Error loading remote history: {e}")
        if os.path.exists(temp_remote_file):
            os.remove(temp_remote_file)
        return

    # Merge keys (news_links, news_titles, quotes, insta_ids)
    merged_data = {}
    for key in ["news_links", "news_titles", "quotes", "insta_ids"]:
        local_arr = local_data.get(key, [])
        remote_arr = remote_data.get(key, [])
        
        # Merge arrays while preserving order and uniqueness
        seen = set()
        merged_arr = []
        for item in remote_arr + local_arr:
            if item not in seen:
                seen.add(item)
                merged_arr.append(item)
        merged_data[key] = merged_arr

    # Write merged history back to HISTORY_FILE
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print("[Sync History] Successfully merged local and remote publication history!")

    # Clean up temp file
    if os.path.exists(temp_remote_file):
        os.remove(temp_remote_file)

if __name__ == "__main__":
    sync_history()
