"""
generate_sign_images.py
------------------------
Creates one SVG illustration per sign word in static/signs/images/.

These are PLACEHOLDER illustrations (a stylised hand-shape card with the
word + Gujarati label) so the app has real image files to point to, instead
of relying on emoji characters as if they were actual ISL signs.

>>> Swap these out later: drop verified ISL sign video files into
    static/signs/videos/<word>.mp4 (spaces -> hyphens) and the app will
    automatically prefer the video over the placeholder image (see
    templates/base.html sign-card renderer in app.js).
"""
import json
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNS_JSON = os.path.join(BASE_DIR, "static", "signs", "signs.json")
IMAGES_DIR = os.path.join(BASE_DIR, "static", "signs", "images")

# A small palette so cards are visually distinguishable by category
PALETTE = ["#6C5CE7", "#4834D4", "#7C3AED", "#5B21B6", "#8B5CF6", "#6D28D9"]

# Distinct placeholder hand shapes (generic, not emoji, not verified ISL assets).
HAND_PATHS = (
"""
M100,150 C95,150 90,145 90,138 L90,80 C90,74 95,70 100,70 C105,70 110,74 110,80 L110,110
M110,110 L110,60 C110,54 115,50 121,50 C127,50 132,54 132,60 L132,110
M132,110 L132,55 C132,49 137,45 143,45 C149,45 154,49 154,55 L154,110
M154,110 L154,65 C154,59 159,55 165,55 C171,55 176,59 176,65 L176,125
C176,125 180,120 188,122 C196,124 198,132 198,140 L198,160
C198,190 180,215 150,215 L120,215 C95,215 78,195 78,170 L78,150
C78,140 86,132 96,132
""",
"""
M92,150 L92,88 C92,80 98,75 105,75 C112,75 118,80 118,88 L118,125
M118,125 L118,48 C118,40 124,35 131,35 C138,35 144,40 144,48 L144,125
M144,125 L144,62 C144,54 150,49 157,49 C164,49 170,54 170,62 L170,125
M170,125 L170,82 C170,74 176,69 183,69 C190,69 196,74 196,82 L196,155
C196,198 175,220 143,220 L124,220 C94,220 76,198 76,170 L76,150
C76,140 84,132 92,132
""",
"""
M86,170 C86,150 98,136 115,136 L115,70 C115,62 121,56 129,56
C137,56 143,62 143,70 L143,136 L143,38 C143,30 149,24 157,24
C165,24 171,30 171,38 L171,136 L171,80 C171,72 177,66 185,66
C193,66 199,72 199,80 L199,162 C199,198 178,220 146,220 L120,220
C99,220 86,200 86,170
""",
"""
M84,154 C84,143 93,135 104,135 L104,84 C104,76 110,70 118,70
C126,70 132,76 132,84 L132,135 L132,58 C132,50 138,44 146,44
C154,44 160,50 160,58 L160,135 L160,92 C160,84 166,78 174,78
C182,78 188,84 188,92 L188,140 L188,111 C188,103 194,97 202,97
C210,97 216,103 216,111 L216,160 C216,197 190,220 155,220 L122,220
C99,220 84,193 84,154
""",
"""
M102,165 C91,157 86,146 91,137 C96,128 108,126 118,132 L134,142
L119,70 C117,61 123,53 132,51 C141,49 149,55 151,64 L161,111
L160,54 C160,45 167,38 176,38 C185,38 192,45 192,54 L192,125
L198,91 C200,82 208,77 217,79 C226,81 231,89 229,98 L218,161
C211,199 187,220 153,220 L132,220 C119,220 108,205 102,165
""",
"""
M96,168 C87,159 86,146 95,138 C102,132 112,132 120,138 L138,151
L126,82 C124,73 130,65 139,63 C148,61 156,67 158,76 L166,119
L166,64 C166,55 173,48 182,48 C191,48 198,55 198,64 L198,126
L205,105 C208,96 217,92 225,96 C233,100 237,109 234,118 L218,170
C207,202 185,220 153,220 L130,220 C116,220 104,202 96,168
"""
)


def slugify(word: str) -> str:
    return word.strip().lower().replace(" ", "-")


def color_for(word: str) -> str:
    h = int(hashlib.md5(word.encode()).hexdigest(), 16)
    return PALETTE[h % len(PALETTE)]


def hand_path_for(word: str) -> str:
    h = int(hashlib.md5(word.encode()).hexdigest(), 16)
    return HAND_PATHS[h % len(HAND_PATHS)]


def make_svg(word: str, gu: str) -> str:
    color = color_for(word)
    hand_path = hand_path_for(word)
    label = word.upper()
    font_size = 20 if len(label) <= 10 else max(11, int(200 / len(label)))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 260" width="280" height="260">
  <defs>
    <linearGradient id="bg-{slugify(word)}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0.22"/>
    </linearGradient>
  </defs>
  <rect x="4" y="4" width="272" height="252" rx="22" fill="url(#bg-{slugify(word)})" stroke="{color}" stroke-width="2.5"/>
  <g transform="translate(40,10) scale(0.65)" fill="none" stroke="{color}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round">
    <path d="{hand_path}"/>
  </g>
  <text x="140" y="205" text-anchor="middle" font-family="Segoe UI, sans-serif" font-weight="700" font-size="{font_size}" fill="#2b2350">{label}</text>
  <text x="140" y="230" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="15" fill="#6b6489">{gu}</text>
  <text x="140" y="248" text-anchor="middle" font-family="Segoe UI, sans-serif" font-size="9" fill="#a39ac2">ISL placeholder — replace with verified asset</text>
</svg>'''


def main():
    with open(SIGNS_JSON, "r", encoding="utf-8") as f:
        categories = json.load(f)

    os.makedirs(IMAGES_DIR, exist_ok=True)
    count = 0
    for category, words in categories.items():
        for word, meta in words.items():
            svg = make_svg(word, meta.get("gu", ""))
            path = os.path.join(IMAGES_DIR, f"{slugify(word)}.svg")
            with open(path, "w", encoding="utf-8") as out:
                out.write(svg)
            count += 1
    print(f"Generated {count} placeholder sign images in {IMAGES_DIR}")


if __name__ == "__main__":
    main()
