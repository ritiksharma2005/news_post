import os
import requests
import time
import logging

logger = logging.getLogger(__name__)

class InstagramPublisher:
    def __init__(self, access_token=None, ig_user_id=None):
        self.access_token = access_token or os.getenv("EAAWH0f4vts8BSEEJCqfJRChHAFmZBTkJJ65m8aGTL3eqtNqkEU5yykIaDAQry8O7dopDHp4ETXoKrpCX3eFI3rZBXkKMJPChqgxseCs0XmOCjbIZCaqmfeTF5GLhe4MRvNtCBp5ib83sYOXrHLHfcHvIZBBamXUWB4fz4RdAYf4Y4jJsnbNVZArERFTCI")
        self.ig_user_id = ig_user_id or os.getenv("1237139552813418")
        self.graph_url = f"https://graph.facebook.com/v19.0/{self.ig_user_id}"

    def publish_photo(self, image_url: str, caption: str) -> bool:
        """
        Publishes a single photo post to Instagram using the Graph API.
        Step 1: Create a media container (POST /{ig-user-id}/media)
        Step 2: Wait for Meta to fetch the image
        Step 3: Publish the container (POST /{ig-user-id}/media_publish)
        """
        if not self.access_token or not self.ig_user_id:
            logger.error("❌ Instagram credentials missing (INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID).")
            return False

        logger.info("📸 Creating Instagram Media Container...")
        
        # Step 1: Create Media Container
        container_endpoint = f"{self.graph_url}/media"
        payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": self.access_token
        }
        
        response = requests.post(container_endpoint, data=payload)
        res_data = response.json()
        
        if "id" not in res_data:
            logger.error(f"❌ Failed to create Instagram container: {res_data}")
            return False

        creation_id = res_data["id"]
        logger.info(f"✅ Container created successfully! Creation ID: {creation_id}")

        # Wait 5 seconds to ensure Meta's servers finish downloading the image URL
        time.sleep(5)

        # Step 2: Publish Container
        logger.info("🚀 Publishing post to Instagram feed...")
        publish_endpoint = f"{self.graph_url}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }

        pub_response = requests.post(publish_endpoint, data=publish_payload)
        pub_data = pub_response.json()

        if "id" in pub_data:
            logger.info(f"🎉 SUCCESS! Published to Instagram! Post ID: {pub_data['id']}")
            return True
        else:
            logger.error(f"❌ Failed to publish to Instagram: {pub_data}")
            return False
