import os
import requests
import sys
import time

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

def fetch_via_apify(username, limit=12):
    """
    Fetches posts from an Instagram account using Apify's Instagram Scraper Actor.
    """
    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        apify_token = getattr(config, "APIFY_TOKEN", "")
        
    if not apify_token:
        return None  # Signal fallback to RapidAPI
        
    print(f"[Apify Scraper] Requesting posts for '{username}'...")
    actor_id = "apify~instagram-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={apify_token}"
    input_data = {
        "directUrls": [f"https://www.instagram.com/{username}/"],
        "resultsLimit": limit,
        "resultsType": "posts"
    }
    
    try:
        response = requests.post(run_url, json=input_data, timeout=30)
        if response.status_code not in [200, 201]:
            print(f"[Apify Scraper] Error starting Actor: {response.status_code} - {response.text}")
            return []
            
        res_data = response.json()
        run_id = res_data.get("data", {}).get("id")
        if not run_id:
            print(f"[Apify Scraper] No run ID returned: {res_data}")
            return []
            
        print(f"[Apify Scraper] Actor run started (ID: {run_id}). Polling for results...")
        max_attempts = 24
        for attempt in range(max_attempts):
            time.sleep(5)
            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={apify_token}"
            status_res = requests.get(status_url, timeout=15)
            if status_res.status_code == 200:
                run_info = status_res.json().get("data", {})
                status = run_info.get("status")
                print(f"  Attempt {attempt+1}/{max_attempts}: Status is '{status}'")
                if status == "SUCCEEDED":
                    dataset_id = run_info.get("defaultDatasetId")
                    items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={apify_token}"
                    items_res = requests.get(items_url, timeout=20)
                    if items_res.status_code == 200:
                        raw_items = items_res.json()
                        compiled_posts = []
                        for item in raw_items:
                            display_url = item.get("displayUrl")
                            if not display_url and item.get("images"):
                                display_url = item["images"][0] if isinstance(item["images"], list) and item["images"] else ""
                                
                            timestamp = item.get("timestamp", "")
                            post_date = timestamp.split("T")[0] if "T" in timestamp else timestamp
                            
                            compiled_posts.append({
                                "caption": item.get("caption", ""),
                                "image_url": display_url,
                                "id": item.get("id"),
                                "code": item.get("shortCode") or item.get("code"),
                                "taken_at": item.get("timestamp"),
                                "date": post_date,
                                "is_pinned": item.get("isPinned") or item.get("pinned") or item.get("pinnedToTop") or False
                            })
                        print(f"[Apify Scraper] Successfully compiled {len(compiled_posts)} posts.")
                        return compiled_posts
                    else:
                        print(f"[Apify Scraper] Error fetching items: {items_res.status_code}")
                        return []
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    print(f"[Apify Scraper] Actor run finished with failure status: {status}")
                    return []
                    
        print("[Apify Scraper] Timeout waiting for Actor to finish.")
        return []
    except Exception as e:
        print(f"[Apify Scraper] Exception: {e}")
        return []

def fetch_instagram_posts(username, limit=3):
    """
    Fetches posts from an Instagram account.
    If APIFY_TOKEN is set, it uses Apify Instagram Scraper.
    Otherwise, it falls back to the RapidAPI scraper.
    """
    # 1. Try Apify first if APIFY_TOKEN is configured
    apify_posts = fetch_via_apify(username, limit=limit)
    if apify_posts is not None:
        return apify_posts
        
    # 2. Fallback to RapidAPI
    # Read RapidAPI credentials from environment/config
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        api_key = getattr(config, "RAPIDAPI_KEY", "")
        
    if not api_key:
        print("[Instagram Scraper] Error: RAPIDAPI_KEY and APIFY_TOKEN are both missing.")
        return []
        
    url = "https://instagram-scraper-stable-api.p.rapidapi.com/get_ig_user_posts.php"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "username_or_url": username,
        "amount": "12",
        "pagination_token": ""
    }
    
    try:
        print(f"[Instagram Scraper] Requesting posts for '{username}' via RapidAPI...")
        response = requests.post(url, headers=headers, data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            
            # Instagram responses can have varying payload roots
            items = []
            if isinstance(data, dict):
                data_root = data.get("data", {})
                if isinstance(data_root, dict):
                    items = data_root.get("items", []) or data_root.get("edges", [])
                elif isinstance(data_root, list):
                    items = data_root
                
                if not items:
                    items = data.get("posts", []) or data.get("items", []) or data.get("edges", []) or data.get("response", {}).get("items", [])
            elif isinstance(data, list):
                items = data
                
            if not items:
                print(f"[Instagram Scraper] Warning: API returned success but found 0 posts. Response: {str(data)[:200]}...")
                return []
                
            posts = []
            for item in items[:limit]:
                node = item.get("node", item) if isinstance(item, dict) else {}
                
                display_url = node.get("display_url") or node.get("image") or node.get("thumbnail_src")
                if not display_url and isinstance(node.get("image_versions2"), dict):
                    candidates = node["image_versions2"].get("candidates", [])
                    if candidates and isinstance(candidates[0], dict):
                        display_url = candidates[0].get("url")
                        
                if not display_url and isinstance(node.get("carousel_media"), list) and node["carousel_media"]:
                    first_media = node["carousel_media"][0]
                    display_url = first_media.get("display_url") or first_media.get("image")
                    if not display_url and isinstance(first_media.get("image_versions2"), dict):
                        candidates = first_media["image_versions2"].get("candidates", [])
                        if candidates:
                            display_url = candidates[0].get("url")
                
                caption = ""
                caption_obj = node.get("caption") or {}
                if isinstance(caption_obj, dict):
                    caption = caption_obj.get("text", "")
                elif isinstance(caption_obj, str):
                    caption = caption_obj
                
                if not caption and isinstance(node.get("edge_media_to_caption"), dict):
                    edges = node["edge_media_to_caption"].get("edges", [])
                    if edges and isinstance(edges[0], dict):
                        caption = edges[0].get("node", {}).get("text", "")
                
                taken_at = node.get("taken_at")
                post_date = None
                if taken_at:
                    try:
                        import datetime
                        post_date = datetime.date.fromtimestamp(taken_at).isoformat()
                    except Exception:
                        pass
                
                posts.append({
                    "caption": caption.strip(),
                    "image_url": display_url,
                    "id": node.get("id"),
                    "code": node.get("code"),
                    "taken_at": taken_at,
                    "date": post_date
                })
            
            print(f"[Instagram Scraper] Successfully compiled {len(posts)} posts via RapidAPI.")
            return posts
        else:
            if response.status_code == 429 or "exceeded the MONTHLY quota" in response.text:
                print("\n" + "!" * 80)
                print("⚠️  [RAPIDAPI CAP LIMIT REACHED] Monthly request quota exceeded!")
                print("Please upgrade your subscription or wait for the monthly limit reset.")
                print("!" * 80 + "\n")
            print(f"[Instagram Scraper] API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[Instagram Scraper] Connection Error: {e}")
        
    return []
