"""
test_poster.py
Generates sample poster cards locally without calling any APIs or using secrets.

Run: python test_poster.py
"""

import os
import design_post

# Ensure output directory exists
os.makedirs("output/cards", exist_ok=True)

print("🎨 Generating 3 sample poster cards locally...")

# Sample 1: Indian Politics & Govt (Red Accent)
design_post.create_card(
    headline="Parliament Passes New Education & Career Equality Bill 2026",
    summary="The Union Government has introduced a major legislative update aimed at streamlining national entrance exams, increasing recruitment transparency, and regulating coaching hubs nationwide.",
    image_path=None,
    bucket="IndianPolitics",
    language="en",
    emoji="🏛️",
    output_path="output/cards/test_politics.png"
)

# Sample 2: Student & Exams (Green Accent)
design_post.create_card(
    headline="UPSC & SSC Announce Combined Recruitment for 50,000+ Vacancies",
    summary="Official notification released for engineering and general graduate aspirants. The application portal opens tomorrow with revised age relaxation guidelines for technical candidates.",
    image_path=None,
    bucket="StudentEducation",
    language="en",
    emoji="🎓",
    output_path="output/cards/test_student.png"
)

# Sample 3: Tech & Innovation (Purple Accent)
design_post.create_card(
    headline="ISRO Successfully Launches Next-Gen AI Satellite Into Orbit",
    summary="India's space agency marks another historic milestone with the successful deployment of high-resolution Earth imaging technology built in collaboration with top IIT research labs.",
    image_path=None,
    bucket="TechInnovation",
    language="en",
    emoji="🚀",
    output_path="output/cards/test_tech.png"
)

print("\n✅ Success! 3 Test posters generated in output/cards/")
print("Run this command in terminal to view them: open output/cards/")
