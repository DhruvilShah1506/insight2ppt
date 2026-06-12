from PIL import Image, ImageDraw, ImageFont
import os

repo_root = os.getcwd()
sb_dir = os.path.join(repo_root, 'sample_backgrounds')
bg = None
preferred = os.path.join(sb_dir, 'bg_wp_3.png')
if os.path.exists(preferred):
    bg = preferred
else:
    if os.path.isdir(sb_dir):
        for fn in sorted(os.listdir(sb_dir)):
            if fn.startswith('bg_wp_') and fn.lower().endswith('.png'):
                bg = os.path.join(sb_dir, fn)
                break
if not bg:
    raise SystemExit('No sample background found')

im = Image.open(bg).convert('RGBA')
w,h = im.size

draw = ImageDraw.Draw(im)

# Ribbon
ribbon_h = int(h * 0.08)
draw.rectangle([0, h - ribbon_h, w, h], fill=(111,66,193,220))

# Decorative circle
circ_w = int(w * 0.18)
circ_x = w - circ_w + int(w * 0.02)
circ_y = int(h * 0.06)
draw.ellipse([circ_x, circ_y, circ_x + circ_w, circ_y + circ_w], fill=(148,103,255,160))

# Title
try:
    title_font = ImageFont.truetype('arial.ttf', 64)
    body_font = ImageFont.truetype('arial.ttf', 28)
except Exception:
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()

title = 'Executive Insights'
tx = int(w * 0.06)
ty = int(h * 0.12)
draw.text((tx, ty), title, font=title_font, fill=(48,25,107))

# Save
out = os.path.join(repo_root, 'sample_slides', 'title_preview.png')
os.makedirs(os.path.dirname(out), exist_ok=True)
im.save(out)
print('Wrote', out)
