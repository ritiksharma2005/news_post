"""
test_poster.py
Generates 3 sample poster cards matching the exact News.nit_iit template layout
with fixed emojis (📚, 🏛️, 🚀, 📌, 📸).

Run: python test_poster.py
"""

import os
import design_post

# Ensure output directory exists
os.makedirs("output/cards", exist_ok=True)

print("🎨 Generating 3 sample poster cards locally...")

# Sample 1: Student & Education (Emerald Green Theme with 📚 Books Emoji)
design_post.create_card(
    headline="India Unveils Bold New Education Scheme for Colleges",
    summary="The government announced a fresh push to modernize higher education, focusing on skill-based learning and better funding for state colleges across the country.",
    image_path=None,
    bucket="StudentEducation",
    language="en",
    output_path="output/cards/test_student.png"
)

# Sample 2: Indian Politics & Govt (Saffron Red Theme with 🏛️ Capitol Emoji)
design_post.create_card(
    headline="Parliament Passes New Education & Career Equality Bill 2026",
    summary="The Union Government has introduced a major legislative update aimed at streamlining national entrance exams, increasing recruitment transparency, and regulating coaching hubs nationwide.",
    image_path=None,
    bucket="IndianPolitics",
    language="en",
    output_path="output/cards/test_politics.png"
)

# Sample 3: Tech & Innovation (Electric Purple Theme with 🚀 Rocket Emoji)
design_post.create_card(
    headline="ISRO Successfully Launches Next-Gen AI Satellite Into Orbit",
    summary="India's space agency marks another historic milestone with the successful deployment of high-resolution Earth imaging technology built in collaboration with top IIT research labs.",
    image_path=None,
    bucket="TechInnovation",
    language="en",
    output_path="output/cards/test_tech.png"
)

print("\n✅ Success! 3 Test posters generated in output/cards/")
print("Run this command in terminal to view them: open output/cards/")
