import os
import json
import sys
from difflib import SequenceMatcher

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from scrapers.playwright_scraper import scrape_google_news, scrape_bhaskar_rss
from poster import image_handler, template_en, template_hi
from publisher import telegram, instagram
from workflow.history_manager import is_duplicate_news, add_published_news

def clean_and_truncate(text, max_len):
    """Truncates text safely on word boundaries."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    trimmed = text[:max_len]
    if " " in trimmed:
        return trimmed.rsplit(" ", 1)[0] + "..."
    return trimmed + "..."

def get_similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def run_pipeline(language="en", run_type="morning", dry_run=False):
    """Executes the master pipeline using Playwright scraper and zero paid APIs."""
    print("=" * 60)
    print(f"🚀 RUNNING PLAYWRIGHT NEWS WORKFLOW: {language.upper()} | {run_type.upper()} RUN")
    print("=" * 60)
    
    # 1. Scrape News from Web using Playwright
    # Determine search queries based on language
    if language == "hi":
        general_query = "भारत समाचार"
        student_query = "परीक्षा परिणाम OR बोर्ड परीक्षा OR सरकारी नौकरी"
    else:
        general_query = "India news"
        student_query = "site:careers360.com OR site:shiksha.com OR site:nta.ac.in exam news"
        
    if language == "hi":
        print(f"\n[Workflow] Scraping Dainik Bhaskar national RSS feed...")
        general_stories = scrape_bhaskar_rss(limit=8)
    else:
        print(f"\n[Workflow] Scraping general/trending news...")
        general_stories = scrape_google_news(general_query, lang=language, limit=8)
    
    print(f"\n[Workflow] Scraping student/education news...")
    student_stories = scrape_google_news(student_query, lang=language, limit=5)
    
    # 2. Prevent duplication with morning run if this is the evening run
    morning_titles = []
    morning_log_file = f"data/morning_run_{language}.json"
    if run_type == "evening" and os.path.exists(morning_log_file):
        try:
            with open(morning_log_file, "r", encoding="utf-8") as f:
                morning_data = json.load(f)
                morning_titles = [s.get("title", "") for s in morning_data]
            print(f"Loaded {len(morning_titles)} morning stories to prevent duplication.")
        except Exception as e:
            print(f"Error loading morning log: {e}")

    # Helper to filter out similar/already published stories
    def filter_fresh_stories(stories):
        fresh = []
        for s in stories:
            # Check similarity with already selected in current run
            is_dup = False
            for f in fresh:
                if get_similarity(s["title"], f["title"]) > 0.6:
                    is_dup = True
                    break
            # Check similarity with morning stories
            for m_title in morning_titles:
                if get_similarity(s["title"], m_title) > 0.6:
                    is_dup = True
                    break
            # Check similarity with global published history
            if not is_dup and is_duplicate_news(s["title"], s.get("link")):
                is_dup = True
                
            if not is_dup:
                fresh.append(s)
        return fresh

    fresh_general = filter_fresh_stories(general_stories)
    fresh_student = filter_fresh_stories(student_stories)
    
    # 3. Apply Selection Rule (3 General + 1 Student = 4 stories)
    selected_stories = []
    
    # Take top 1 student story
    if fresh_student:
        selected_stories.append(fresh_student[0])
        # Mark as Student
        fresh_student[0]["bucket"] = "StudentEducation"
        fresh_student[0]["category"] = "छात्र समाचार" if language == "hi" else "Student"
    
    # Take top general stories to fill the remainder up to 4
    general_needed = 4 - len(selected_stories)
    for story in fresh_general[:general_needed]:
        # Simple dynamic categorization based on keywords
        title_lower = story["title"].lower()
        if any(kw in title_lower for kw in ["politics", "govt", "government", "policy", "minister", "modi", "kejriwal", "चुनाव", "सरकार", "मंत्री"]):
            story["bucket"] = "IndianPolitics"
            story["category"] = "राजनीति" if language == "hi" else "Politics"
        elif any(kw in title_lower for kw in ["market", "gdp", "golds", "rupee", "bank", "rbi", "sensex", "economy", "टैरिफ", "बैंक", "महंगाई"]):
            story["bucket"] = "Economy"
            story["category"] = "अर्थव्यवस्था" if language == "hi" else "Economy"
        elif any(kw in title_lower for kw in ["cricket", "olympics", "hockey", "sports", "match", "खेल", "क्रिकेट", "मैच"]):
            story["bucket"] = "Sports"
            story["category"] = "खेल" if language == "hi" else "Sports"
        else:
            story["bucket"] = "IndianPolitics"
            story["category"] = "राष्ट्रीय" if language == "hi" else "National"
            
        selected_stories.append(story)
        
    print(f"\n[Workflow] Selected {len(selected_stories)} final stories for the run.")
    if not selected_stories:
        print("No fresh stories selected. Stopping.")
        return
        
    # 4. Form Headlines, Summaries, and Captions (No LLM, direct formatting)
    final_posters = []
    for i, story in enumerate(selected_stories):
        # Truncate title and summary to fit card layout perfectly
        headline = clean_and_truncate(story["title"], 80)
        summary_limit = 290 if language == "hi" else 155
        summary = clean_and_truncate(story["summary"], summary_limit)
        
        story["new_headline"] = headline
        story["new_summary"] = summary
        
        # Build engagement caption
        if language == "hi":
            bucket = story.get("bucket", "")
            if bucket == "StudentEducation":
                overview_text = (
                    "यह महत्वपूर्ण अपडेट देश के लाखों छात्रों, प्रतियोगी परीक्षाओं की तैयारी कर रहे उम्मीदवारों और शैक्षणिक संस्थानों से सीधे तौर पर जुड़ा हुआ है। "
                    "वर्तमान में शिक्षा क्षेत्र में हो रहे बड़े बदलावों, बोर्ड परीक्षाओं, प्रवेश परीक्षाओं और सरकारी नौकरी की भर्ती प्रक्रियाओं से जुड़ी हर जानकारी युवाओं के करियर को सीधे प्रभावित करती है। "
                    "ऐसे में इस ताज़ा घटनाक्रम, नियमों में बदलाव, और परीक्षा परिणामों से जुड़ी हर बारीक जानकारी को समझना सभी के लिए बेहद जरूरी है। "
                    "इस पूरे समाचार को ध्यान से पढ़ें, अपने सहपाठियों और मित्रों के साथ साझा करें ताकि कोई भी महत्वपूर्ण अपडेट छूटने न पाए, और अपनी परीक्षा व भविष्य की तैयारी को एक सही दिशा दें!"
                )
            elif bucket == "IndianPolitics":
                overview_text = (
                    "देश के राजनीतिक और राष्ट्रीय घटनाक्रम सीधे तौर पर हमारे शासन, नीतियों और रोजमर्रा के जीवन को प्रभावित करते हैं। "
                    "सरकार द्वारा लिए जा रहे निर्णय, नीतिगत बदलाव और विभिन्न राजनैतिक दलों की गतिविधियां देश की दिशा तय करने में महत्वपूर्ण भूमिका निभाती हैं। "
                    "इस समाचार में दिए गए तथ्य और बदलाव हर जागरूक नागरिक, विशेषकर प्रतियोगी परीक्षाओं (जैसे UPSC व अन्य) की तैयारी कर रहे युवाओं के लिए आवश्यक हैं। "
                    "इस पूरे घटनाक्रम पर बारीक नज़र रखना और इसके सामाजिक प्रभावों को समझना अत्यंत महत्वपूर्ण है। "
                    "ताज़ा अपडेट के लिए खबर को पूरा पढ़ें और अपने दोस्तों के साथ साझा करना न भूलें।"
                )
            elif bucket == "Economy":
                overview_text = (
                    "आर्थिक नीतियों, बाज़ार के उतार-चढ़ाव, महंगाई दर और बैंकिंग क्षेत्र के नए फैसले सीधे तौर पर हमारे देश की आर्थिक स्थिति को दर्शाते हैं। "
                    "वित्त वर्ष के नीतिगत बदलाव, जीडीपी दर, टैक्स से जुड़े नियम और आम आदमी के बजट पर पड़ने वाला प्रभाव देश के विकास की गति निर्धारित करता है। "
                    "यह समाचार हमारे व्यापारिक परिदृश्य, रोजगार के अवसरों और वित्तीय साक्षरता के लिए अत्यंत प्रासंगिक है। "
                    "इस पूरे आर्थिक बदलाव और इसके दूरगामी परिणामों को समझना हर पेशेवर, छात्र और सामान्य नागरिक के लिए महत्वपूर्ण है। "
                    "इस अपडेट को पूरा समझें और वित्तीय जानकारी बढ़ाने के लिए इसे साझा करें।"
                )
            elif bucket == "Sports":
                overview_text = (
                    "खेल जगत से जुड़ी उपलब्धियां, नए रिकॉर्ड और प्रमुख टूर्नामेंट देशवासियों को गौरवान्वित और प्रेरित करते हैं। "
                    "चाहे वह क्रिकेट हो, ओलंपिक खेल हों, या कोई अन्य खेल, भारतीय खिलाड़ियों का वैश्विक स्तर पर प्रदर्शन युवाओं के लिए प्रेरणा का एक बड़ा स्रोत है। "
                    "राष्ट्रीय और अंतर्राष्ट्रीय स्तर पर खेल नीतियां, प्रशिक्षण और चैंपियनशिप युवाओं में टीम भावना और अनुशासन को बढ़ावा देती हैं। "
                    "इस ताज़ा खेल समाचार और इसके प्रमुख आंकड़ों को विस्तार से जानने के लिए इस पूरे अपडेट को ध्यान से पढ़ें। "
                    "इस जानकारी को अन्य खेल प्रेमियों के साथ शेयर करें और हमारे एथलीटों का उत्साहवर्धन करें।"
                )
            else:
                overview_text = (
                    "देश और दुनिया की इस ताज़ा खबर को लेकर युवाओं और छात्र-छात्राओं के बीच काफी चर्चा है। "
                    "शिक्षा, समाज और सरकारी नीतियों से जुड़ा यह नया अपडेट हमारे आने वाले करियर और सामाजिक परिदृश्य पर महत्वपूर्ण असर डाल सकता है। "
                    "इस पूरे घटनाक्रम को समझना और इसके सामाजिक व प्रशासनिक निहितार्थों पर चर्चा करना हर जागरूक व्यक्ति के लिए आवश्यक है। "
                    "इस पूरी जानकारी को ध्यानपूर्वक पढ़ें, इसका विश्लेषण करें, इसे अपने साथियों के साथ शेयर करें और भविष्य के अवसरों व चुनौतियों के लिए तैयार रहें।"
                )

            caption = (
                f"🔥 {headline}\n\n"
                f"📝 मुख्य बातें (Highlights):\n"
                f"{summary}\n\n"
                f"📌 विस्तार से समझें (Overview):\n"
                f"{overview_text}\n\n"
                f"💬 इस घटनाक्रम पर आपकी क्या राय है? कमेंट में जरूर बताएं! 👇\n\n"
                f"📌 ताज़ा अपडेट्स के लिए इसे अपने दोस्तों के साथ शेयर करें!\n\n"
                f"📲 हमारे इंस्टाग्राम कम्युनिटी चैनल से जुड़ें (लिंक बायो में भी उपलब्ध है): https://www.instagram.com/channel/AbYg9NWAeNaKS8gf/\n\n"
                f"#HindiNews #StudentNews #EducationUpdates #UPSC #SarkariNaukri #news_nit_iit"
            )
        else:
            bucket = story.get("bucket", "")
            if bucket == "StudentEducation":
                overview_text = (
                    "This key update is generating significant interest among students, competitive exam aspirants, and academic communities across India. "
                    "Keeping track of national policy updates, educational reforms, and current affairs is essential for shaping future career strategies. "
                    "In today's fast-changing academic environment, keeping up with board decisions, entrance exams, and government job updates is highly beneficial. "
                    "Make sure to read through the complete details, share this crucial update with your fellow peers, and stay ahead in your preparation journey!"
                )
            elif bucket == "IndianPolitics":
                overview_text = (
                    "National and political developments play a crucial role in shaping administrative decisions, public policies, and the overall social landscape. "
                    "Understanding major political movements, government actions, and legislative changes is essential for staying informed as a responsible citizen. "
                    "For students and competitive exam aspirants (especially UPSC), analyzing these political shifts provides critical context for general awareness. "
                    "Take a close look at the details presented in this update, consider its potential long-term social impacts, and share it with others to spread awareness."
                )
            elif bucket == "Economy":
                overview_text = (
                    "Economic policies, market trends, financial reforms, and inflation rates have a direct impact on the country's development and citizen livelihood. "
                    "Tracking GDP numbers, trade changes, RBI decisions, and employment opportunities offers valuable insight into the nation's financial health. "
                    "This update highlights important shifts in the economic landscape that are relevant for professionals, students, and businesses alike. "
                    "Stay informed about the fiscal updates by reading the details below, and share this update to keep your network financially aware."
                )
            elif bucket == "Sports":
                overview_text = (
                    "Sports updates, athletic records, and global tournaments serve as a massive source of inspiration and national pride for the youth. "
                    "Whether it is cricket, the Olympics, or regional championships, the dedication and performance of our athletes drive motivation and sportsmanship. "
                    "Analyzing sports policies, training setups, and match details helps us stay connected with national and international sporting spirits. "
                    "Read the full details of this exciting sporting update, keep track of the key records, and share the pride with your fellow sports enthusiasts."
                )
            else:
                overview_text = (
                    "This latest development is currently drawing major attention across various social media and public platforms nationwide. "
                    "Understanding the details of this event, its background context, and its practical implications is highly valuable for remaining informed. "
                    "Such current affairs events provide vital talking points and perspective, especially for competitive exam aspirants and active citizens. "
                    "Please read the full highlights of the news below, share it with your friends and colleagues, and let us know your thoughts in the comments."
                )

            caption = (
                f"🔥 {headline}\n\n"
                f"📝 Highlights:\n"
                f"{summary}\n\n"
                f"📌 Overview & Context:\n"
                f"{overview_text}\n\n"
                f"💬 What is your opinion on this update? Let us know in the comments below! 👇\n\n"
                f"📌 Tag a friend to keep them informed! \n\n"
                f"📲 Join our Instagram Community (Link in Bio): https://www.instagram.com/channel/AbYg9NWAeNaKS8gf/\n\n"
                f"#IndiaNews #StudentAffairs #UPSC #CompetitiveExams #GenZNews #news_nit_iit"
            )
        story["caption"] = caption
        
        # Determine output paths
        image_path = f"output/images/story_{language}_{run_type}_{i}.jpg"
        card_path = f"output/cards/story_{language}_{run_type}_{i}.png"
        
        # Prepare image (download/search/fallback)
        final_image = image_handler.prepare_image(story, image_path)
        
        # Render poster card
        if language == "hi":
            card = template_hi.create_hindi_card(
                headline=headline,
                summary=summary,
                image_path=final_image,
                bucket=story["bucket"],
                category=story["category"],
                output_path=card_path
            )
        else:
            card = template_en.create_card(
                headline=headline,
                summary=summary,
                image_path=final_image,
                bucket=story["bucket"],
                category=story["category"],
                output_path=card_path
            )
        story["card_path"] = card
        print(f"  [Card Rendered] Story {i+1} poster saved to: {card}")
        final_posters.append(story)
        
    # Save selection log
    os.makedirs("data", exist_ok=True)
    log_file = f"data/{run_type}_run_{language}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(final_posters, f, indent=2, ensure_ascii=False)
    print(f"\nSaved run logs to: {log_file}")
    
    if dry_run:
        print("\n" + "=" * 60)
        print("🔒 [DRY RUN ACTIVE] Posters generated, skipping publishing.")
        print("=" * 60)
        for idx, s in enumerate(final_posters):
            print(f"\n--- Post {idx+1} ({s['bucket']}) ---")
            print(f"Headline: {s['new_headline']}")
            print(f"Summary: {s['new_summary']}")
            print(f"Caption:\n{s['caption']}")
        return
        
    # 5. Publish to Telegram and Instagram with error catching
    telegram_err = None
    instagram_err = None
    
    try:
        print("\nSending stories to Telegram...")
        telegram.send_all_stories(final_posters)
    except Exception as e:
        print(f"  ⚠️ Telegram publishing failed: {e}")
        telegram_err = e
        
    try:
        print("\nPublishing stories to Instagram...")
        instagram.publish_all_stories(final_posters)
    except Exception as e:
        print(f"  ⚠️ Instagram publishing failed: {e}")
        instagram_err = e
        
    # 7. Save to global history (Guarantees stories are registered even on partial publish failure)
    print("\nSaving published news to history...")
    for s in final_posters:
        add_published_news(s["title"], s.get("link"))
        
    if telegram_err or instagram_err:
        raise Exception(f"Publishing finished with errors: Telegram: {telegram_err}, Instagram: {instagram_err}")
        
    print("\n" + "=" * 60)
    print(f"🏁 {language.upper()} {run_type.upper()} RUN COMPLETE!")
    print("=" * 60)
