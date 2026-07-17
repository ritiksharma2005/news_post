"""
test_full_card.py
Combines generate_image.py + design_post.py to build a complete card with
a real AI-generated illustration instead of a placeholder or test color.

Run: python test_full_card.py
"""

from generate_image import generate_image
from design_post import create_card

headline = "India Unveils Bold New Education Scheme for Colleges"
summary = ("The government announced a fresh push to modernize higher "
           "education, focusing on skill-based learning and better "
           "funding for state colleges across the country.")

print("Generating illustration...")
image_path = generate_image(headline, summary, output_path="output/images/full_test.jpg")

if image_path:
    print(f"Image ready: {image_path}")
else:
    print("Image generation failed, card will show placeholder instead.")

print("Building card...")
card_path = create_card(
    headline=headline,
    summary=summary,
    image_path=image_path,
    language="en",
    emoji="📚",
    output_path="output/full_test_card.png",
)
print(f"Done! Open {card_path} to see the result.")
