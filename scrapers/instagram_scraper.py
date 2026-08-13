import os
import requests
import sys

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

def fetch_instagram_posts(username, limit=3):
    """
    Fetches posts from an Instagram account using the Instagram Scraper Stable API on RapidAPI.
    """
    # Read RapidAPI credentials from environment/config
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        api_key = getattr(config, "RAPIDAPI_KEY", "")
        
    if not api_key:
        print("[Instagram Scraper] Error: RAPIDAPI_KEY is not set in .env or config.")
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
        print(f"[Instagram Scraper] Requesting posts for '{username}'...")
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            # Instagram responses can have varying payload roots
            items = []
            if isinstance(data, dict):
                # Check different typical JSON payload roots
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
                print(f"[Instagram Scraper] Warning: API returned success but found 0 posts in response layout. Response: {str(data)[:200]}...")
                return []
                
            posts = []
            for item in items[:limit]:
                # Standard Instagram node check
                node = item.get("node", item) if isinstance(item, dict) else {}
                
                # 1. Extract Image URL
                display_url = node.get("display_url") or node.get("image") or node.get("thumbnail_src")
                
                # Check nested candidates list
                if not display_url and isinstance(node.get("image_versions2"), dict):
                    candidates = node["image_versions2"].get("candidates", [])
                    if candidates and isinstance(candidates[0], dict):
                        display_url = candidates[0].get("url")
                        
                # Check carousel media fallback
                if not display_url and isinstance(node.get("carousel_media"), list) and node["carousel_media"]:
                    first_media = node["carousel_media"][0]
                    display_url = first_media.get("display_url") or first_media.get("image")
                    if not display_url and isinstance(first_media.get("image_versions2"), dict):
                        candidates = first_media["image_versions2"].get("candidates", [])
                        if candidates:
                            display_url = candidates[0].get("url")
                
                # 2. Extract Caption Text
                caption = ""
                caption_obj = node.get("caption") or {}
                if isinstance(caption_obj, dict):
                    caption = caption_obj.get("text", "")
                elif isinstance(caption_obj, str):
                    caption = caption_obj
                
                # Alternate edge_media_to_caption check
                if not caption and isinstance(node.get("edge_media_to_caption"), dict):
                    edges = node["edge_media_to_caption"].get("edges", [])
                    if edges and isinstance(edges[0], dict):
                        caption = edges[0].get("node", {}).get("text", "")
                
                # 3. Extract taken_at and parse date
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
            
            print(f"[Instagram Scraper] Successfully compiled {len(posts)} posts.")
            return posts
        else:
            print(f"[Instagram Scraper] API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[Instagram Scraper] Connection Error: {e}")
        
    return []
