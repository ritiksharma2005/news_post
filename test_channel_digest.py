"""
test_channel_digest.py
Comprehensive Unit and Integration Tests for the Daily Channel Digest Feature.
Tests formatter, date filtering, duplicate prevention, and fallback handling.
"""

import unittest
from datetime import datetime, timezone, timedelta
from channel_digest.config import IST_TZ
from channel_digest.formatter import (
    extract_concise_headline,
    format_single_entry,
    build_roundup_messages
)
from channel_digest.collector import parse_timestamp_to_ist
from channel_digest.channel_publisher import InstagramBroadcastChannelPublisher
from channel_digest.database import (
    init_db,
    is_post_in_roundup,
    is_roundup_completed,
    record_roundup,
    get_roundup
)


class TestChannelDigestFormatter(unittest.TestCase):

    def test_extract_concise_headline_clean(self):
        caption = "Anti-ragging squads, police pickets to keep DU students safe\n\nFull details inside."
        headline = extract_concise_headline(caption)
        self.assertEqual(headline, "Anti-ragging squads, police pickets to keep DU students safe")

    def test_extract_concise_headline_with_emojis_and_tags(self):
        caption = "🔥 'Layoffs at Adobe, Microsoft...': Son bags Rs 15 LPA placement at MNC, father forces him for govt job\n\n📌 What happened:\n#news #iit #placements"
        headline = extract_concise_headline(caption)
        self.assertIn("Layoffs at Adobe", headline)
        self.assertNotIn("#news", headline)
        self.assertNotIn("🔥", headline)

    def test_extract_concise_headline_long_truncation(self):
        caption = "This is an extremely long headline describing a major national event in education with far too many redundant words that would exceed our maximum display limit"
        headline = extract_concise_headline(caption)
        self.assertTrue(len(headline) <= 110)
        self.assertTrue(headline.endswith("..."))

    def test_format_single_entry(self):
        post = {
            "headline": "IIT Placements Committee Sets New Rules",
            "permalink": "https://www.instagram.com/p/DB-4h38Xyz/"
        }
        entry = format_single_entry(1, post)
        self.assertIn("1. IIT Placements Committee Sets New Rules", entry)
        self.assertIn("Read here: https://www.instagram.com/p/DB-4h38Xyz/", entry)

    def test_build_roundup_messages_empty(self):
        msgs = build_roundup_messages([], "2026-10-13")
        self.assertEqual(len(msgs), 1)
        self.assertIn("No new posts were published today on @news.nit_iit.", msgs[0])
        self.assertIn("Date: 2026-10-13", msgs[0])

    def test_build_roundup_messages_standard(self):
        posts = [
            {
                "headline": "IIT Placements Committee Updates",
                "permalink": "https://www.instagram.com/p/Post1/"
            },
            {
                "headline": "GATE 2026 Registration Open",
                "permalink": "https://www.instagram.com/p/Post2/"
            }
        ]
        msgs = build_roundup_messages(posts, "2026-10-13")
        self.assertEqual(len(msgs), 1)
        self.assertIn("NEWS NIT IIT — DAILY NEWS ROUNDUP", msgs[0])
        self.assertIn("1. IIT Placements Committee Updates", msgs[0])
        self.assertIn("2. GATE 2026 Registration Open", msgs[0])
        self.assertIn("Follow @news.nit_iit for more updates!", msgs[0])

    def test_build_roundup_messages_splitting(self):
        # Create 35 posts with long headlines to force message splitting beyond character threshold
        posts = []
        for i in range(1, 40):
            posts.append({
                "headline": f"Major University Policy Announcement Number {i} Concerning Academic Rules and Examinations",
                "permalink": f"https://www.instagram.com/p/TestPermalinkLongPostIndex{i}/"
            })
        msgs = build_roundup_messages(posts, "2026-10-13")
        self.assertTrue(len(msgs) > 1)
        self.assertIn("Part 1/", msgs[0])
        self.assertIn("Follow @news.nit_iit for more updates!", msgs[-1])


class TestChannelDigestCollectorUtils(unittest.TestCase):

    def test_parse_timestamp_iso(self):
        # 10:00:00 UTC -> 15:30:00 IST (+5:30)
        dt = parse_timestamp_to_ist("2026-10-13T10:00:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.hour, 15)
        self.assertEqual(dt.minute, 30)
        self.assertEqual(dt.strftime("%Y-%m-%d"), "2026-10-13")

    def test_parse_timestamp_epoch(self):
        # Unix timestamp
        epoch = 1760350000
        dt = parse_timestamp_to_ist(epoch)
        self.assertIsNotNone(dt)
        self.assertEqual(dt.tzinfo, IST_TZ)


class TestChannelDigestDatabase(unittest.TestCase):

    def _cleanup_test_data(self):
        try:
            from channel_digest.database import get_db_connection, _load_history_json, _save_history_json
            conn = get_db_connection()
            conn.execute("DELETE FROM channel_digest_roundups WHERE roundup_date='2099-12-31'")
            conn.execute("DELETE FROM channel_digest_posts WHERE roundup_date='2099-12-31' OR media_id='test_mid_9999'")
            conn.commit()
            conn.close()
            h = _load_history_json()
            h["channel_digest_media_ids"] = [x for x in h.get("channel_digest_media_ids", []) if x != "test_mid_9999"]
            h["channel_digest_roundup_dates"] = [x for x in h.get("channel_digest_roundup_dates", []) if x != "2099-12-31"]
            _save_history_json(h)
        except Exception:
            pass

    def setUp(self):
        init_db()
        self._cleanup_test_data()

    def tearDown(self):
        self._cleanup_test_data()

    def test_record_and_check_roundup(self):
        test_date = "2099-12-31"
        test_posts = [
            {
                "media_id": "test_mid_9999",
                "permalink": "https://www.instagram.com/p/test9999/",
                "headline": "Test Future Story",
                "caption": "Test future story caption",
                "published_at_ist": "2099-12-31 10:00:00 IST"
            }
        ]
        
        # Initially not completed
        self.assertFalse(is_roundup_completed(test_date))
        self.assertFalse(is_post_in_roundup("test_mid_9999"))
        
        # Record
        success = record_roundup(
            roundup_date=test_date,
            posts=test_posts,
            roundup_text="Test Roundup Content",
            telegram_sent=True
        )
        self.assertTrue(success)
        
        # Check presence
        self.assertTrue(is_roundup_completed(test_date))
        self.assertTrue(is_post_in_roundup("test_mid_9999"))
        
        roundup = get_roundup(test_date)
        self.assertIsNotNone(roundup)
        self.assertEqual(roundup["post_count"], 1)


class TestChannelPublisherAPIReport(unittest.TestCase):

    def test_meta_api_support_status(self):
        pub = InstagramBroadcastChannelPublisher()
        # Verify it explicitly reports unsupported per Meta policies
        self.assertFalse(pub.is_api_supported())
        res = pub.publish_roundup("Sample text")
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "unsupported_by_meta_api")


if __name__ == "__main__":
    unittest.main()
