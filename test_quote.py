"""
test_quote.py
Generates today's "Life Mantra" quote poster with Author Portrait Watermark.
Run: python test_quote.py
"""

import os
import generate_quote
import generate_image
import design_quote_post

os.makedirs("output/cards", exist_ok=True)

print("🌅 Fetching today's Life Mantra quote...")
quote_data = generate_quote.fetch_daily_quote()
author_name = quote_data["author"]

print(f"\n🎨 Fetching portrait image for: {author_name}...")
portrait_path = generate_image.generate_image(
    headline=f"Minimalist black and white sketch portrait illustration of {author_name}, high quality line art",
    summary="pencil portrait sketch background",
    output_path=f"output/images/portrait_{author_name.replace(' ', '_')}.jpg"
)

print(f"\n🎨 Rendering Life Mantra Poster for {author_name}...")
card_path = design_quote_post.create_quote_card(
    quote_en=quote_data["quote_en"],
    quote_hi=quote_data["quote_hi"],
    author=author_name,
    reflection=quote_data["reflection"],
    author_image_path=portrait_path,
    output_path="output/cards/quote_today.png"
)

print(f"\n✅ Success! Life Mantra poster with author watermark ready at: {card_path}")
print("Run command: open output/cards/quote_today.png")
