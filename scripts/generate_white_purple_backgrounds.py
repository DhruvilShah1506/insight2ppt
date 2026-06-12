from PIL import Image, ImageDraw
import os

OUT_DIR = 'sample_backgrounds'
os.makedirs(OUT_DIR, exist_ok=True)

palette_pairs = [
    ((255, 255, 255), (245, 235, 255)),  # white -> soft lavender
    ((255, 255, 255), (240, 225, 255)),  # white -> light mauve
    ((255, 255, 255), (250, 240, 255)),  # white -> pale purple
    ((255, 255, 255), (238, 228, 255)),  # white -> pastel violet
]

WIDTH = 1920
HEIGHT = 1080

for idx, (c1, c2) in enumerate(palette_pairs):
    # Create vertical gradient
    base = Image.new('RGB', (WIDTH, HEIGHT), c1)
    top = Image.new('RGB', (WIDTH, HEIGHT), c2)
    mask = Image.new('L', (WIDTH, HEIGHT))
    mask_data = []
    for y in range(HEIGHT):
        ratio = y / max(1, HEIGHT - 1)
        mask_data.extend([int(255 * ratio)] * WIDTH)
    mask.putdata(mask_data)
    grad = Image.composite(top, base, mask)

    # subtle vignette (darken edges slightly)
    vign = Image.new('L', (WIDTH, HEIGHT))
    vdata = []
    cx = WIDTH / 2.0
    cy = HEIGHT / 2.0
    maxd = (cx**2 + cy**2) ** 0.5
    for y in range(HEIGHT):
        for x in range(WIDTH):
            dx = (x - cx)
            dy = (y - cy)
            d = ((dx*dx + dy*dy) ** 0.5) / maxd
            # alpha grows towards edges
            alpha = int(90 * (d ** 1.4))
            vdata.append(alpha)
    vign.putdata(vdata)
    grad = grad.convert('RGBA')
    black = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    black.putalpha(vign)
    try:
        combined = Image.alpha_composite(grad, black).convert('RGB')
    except Exception:
        combined = grad.convert('RGB')

    # optional decorative soft shape (transparent circle)
    overlay = Image.new('RGBA', (WIDTH, HEIGHT), (255,255,255,0))
    draw = ImageDraw.Draw(overlay)
    circ_w = int(WIDTH * 0.28)
    circ_h = circ_w
    circ_x = WIDTH - circ_w - int(WIDTH * 0.06)
    circ_y = int(HEIGHT * 0.08)
    draw.ellipse([circ_x, circ_y, circ_x + circ_w, circ_y + circ_h], fill=(200,170,255,60))
    combined = Image.alpha_composite(combined.convert('RGBA'), overlay).convert('RGB')

    out_path = os.path.join(OUT_DIR, f'bg_wp_{idx}.png')
    combined.save(out_path, format='PNG')
    print('Wrote', out_path)
