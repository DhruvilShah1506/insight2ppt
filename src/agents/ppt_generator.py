from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None
from typing import List
from ..models import PPTSlide
import tempfile
import os
from collections import Counter

# matplotlib is an optional import; only used if add_small_graph=True
try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
except Exception:
    plt = None


def _make_small_chart_image(text: str, target_path: str) -> None:
    """Create a small bar chart PNG from top word frequencies in `text`.

    This is a lightweight visual hint for each slide. If matplotlib is not
    available, this is a no-op.
    """
    if plt is None:
        return

    # Simple tokenization and frequency
    words = [w.strip('.,:;()"\'"').lower() for w in text.split()]
    words = [w for w in words if len(w) > 3]
    if not words:
        return
    counts = Counter(words)
    top = counts.most_common(4)
    labels, values = zip(*top)

    fig, ax = plt.subplots(figsize=(2.8, 1.8), dpi=100)
    bars = ax.bar(labels, values, color='#2b6cb0', edgecolor='none')
    # Add grid and nicer layout
    ax.yaxis.grid(True, color='#e6e6e6', linewidth=0.8)
    ax.set_axisbelow(True)
    # Rotate and style x labels (set ticks first to avoid warnings)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, fontsize=8)
    # Add value labels above bars
    try:
        ax.bar_label(bars, labels=[_format_value(v) for v in values], fontsize=8, padding=2)
    except Exception:
        # Older matplotlib may not have bar_label; fallback to manual text
        for b, v in zip(bars, values):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), _format_value(v), ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Count', fontsize=8)
    ax.tick_params(axis='y', labelsize=8)
    plt.tight_layout()
    fig.savefig(target_path, transparent=True)
    plt.close(fig)


def _make_chart_from_numeric(values: dict, target_path: str) -> None:
    """Create a small bar chart PNG from a numeric `values` dict.

    `values` should be a mapping of label -> numeric value.
    """
    if plt is None:
        return

    # Filter numeric entries and take top 6
    items = [(k, v) for k, v in values.items() if isinstance(v, (int, float))]
    if not items:
        return
    # sort by value desc
    items = sorted(items, key=lambda x: x[1], reverse=True)[:6]
    labels, vals = zip(*items)

    # Decide orientation: use horizontal bars if labels are long or many
    horizontal = any(len(str(l)) > 8 for l in labels) or len(labels) > 4
    if horizontal:
        fig, ax = plt.subplots(figsize=(3.0, 1.8), dpi=100)
        bars = ax.barh(range(len(labels)), vals, color='#2b6cb0')
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.xaxis.grid(True, color='#e6e6e6', linewidth=0.8)
        ax.set_xlabel('Value', fontsize=8)
        # add value labels at end of bars
        try:
            for i, b in enumerate(bars):
                w = b.get_width()
                ax.text(w + max(vals) * 0.02, b.get_y() + b.get_height() / 2, _format_value(w), va='center', fontsize=8)
        except Exception:
            pass
    else:
        fig, ax = plt.subplots(figsize=(2.8, 1.8), dpi=100)
        bars = ax.bar(labels, vals, color='#2b6cb0')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, fontsize=8)
        ax.yaxis.grid(True, color='#e6e6e6', linewidth=0.8)
        ax.set_ylabel('Value', fontsize=8)
        try:
            ax.bar_label(bars, labels=[_format_value(v) for v in vals], fontsize=8, padding=2)
        except Exception:
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(), _format_value(v), ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    fig.savefig(target_path, transparent=True)
    plt.close(fig)


def _make_fancy_chart_from_numeric(values: dict, target_path: str) -> None:
    """Create a fancier horizontal bar chart PNG with gradient and value labels.
    """
    if plt is None:
        return

    items = [(k, v) for k, v in values.items() if isinstance(v, (int, float))]
    if not items:
        return
    items = sorted(items, key=lambda x: x[1], reverse=True)[:6]
    labels, vals = zip(*items)

    fig, ax = plt.subplots(figsize=(3.2, 1.8), dpi=120)
    y_pos = range(len(labels))

    # Draw shadow bars for subtle depth
    ax.barh(y_pos, [v * 1.03 for v in vals], color='#cccccc', alpha=0.25, height=0.6)

    # Main bars with colormap
    cmap = plt.get_cmap('Blues')
    colors = [cmap(0.4 + 0.5 * (i / max(1, len(vals) - 1))) for i in range(len(vals))]
    bars = ax.barh(y_pos, vals, color=colors, height=0.5)

    # Labels and styling
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.xaxis.grid(True, color='#e9eef6', linewidth=0.8)
    ax.set_xlabel('Value', fontsize=8)
    ax.tick_params(axis='x', labelsize=8)

    # Value labels at end of bars
    for b, v in zip(bars, vals):
        ax.text(b.get_width() + max(vals) * 0.02, b.get_y() + b.get_height() / 2, _format_value(v), va='center', fontsize=8, fontweight='bold')

    # Minimal styling
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    fig.savefig(target_path, transparent=True)
    plt.close(fig)


def _make_fancy_chart_from_text(text: str, target_path: str) -> None:
    """Create a fancier chart from text frequency (small horizontal bars).
    """
    if plt is None:
        return

    words = [w.strip('.,:;()"\'"').lower() for w in text.split()]
    words = [w for w in words if len(w) > 3]
    if not words:
        return
    counts = Counter(words)
    items = counts.most_common(4)
    labels, values = zip(*items)

    fig, ax = plt.subplots(figsize=(3.2, 1.6), dpi=120)
    y_pos = range(len(labels))
    cmap = plt.get_cmap('Oranges')
    colors = [cmap(0.5 + 0.4 * (i / max(1, len(values) - 1))) for i in range(len(values))]

    bars = ax.barh(y_pos, values, color=colors, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.xaxis.grid(True, color='#fff4e6', linewidth=0.8)

    for b, v in zip(bars, values):
        ax.text(b.get_width() + max(values) * 0.02, b.get_y() + b.get_height() / 2, _format_value(v), va='center', fontsize=8, fontweight='bold')

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    fig.savefig(target_path, transparent=True)
    plt.close(fig)


def _make_gradient_background(path: str, width_px: int, height_px: int, color1: tuple, color2: tuple) -> None:
    """Create a vertical gradient PNG from color1 to color2 at given pixel size."""
    if Image is None:
        return
    try:
        base = Image.new('RGB', (width_px, height_px), color1)
        top = Image.new('RGB', (width_px, height_px), color2)
        mask = Image.new('L', (width_px, height_px))
        mask_data = []
        # vertical gradient mask from top (color1) to bottom (color2)
        for y in range(height_px):
            mask_data.extend([int(255 * (y / max(1, height_px - 1)))] * width_px)
        mask.putdata(mask_data)
        grad = Image.composite(top, base, mask)
        # Add a subtle vertical vignette to darken top/bottom edges for a professional look
        try:
            vignette = Image.new('L', (width_px, height_px))
            vdata = []
            cy = height_px / 2.0
            for y in range(height_px):
                # distance from center (0..1)
                d = abs((y - cy) / cy)
                # curve to increase effect towards edges
                alpha = int(180 * (d ** 1.4))
                vdata.extend([alpha] * width_px)
            vignette.putdata(vdata)
            # create a semi-transparent black overlay and composite it
            black = Image.new('RGBA', (width_px, height_px), (0, 0, 0, 0))
            black.putalpha(vignette)
            grad = grad.convert('RGBA')
            grad = Image.alpha_composite(grad, black)
            grad = grad.convert('RGB')
        except Exception:
            pass
        grad.save(path, format='PNG')
    except Exception:
        return


def _format_value(v):
    """Format numeric values: use percent for 0..1 floats, commas for large ints."""
    try:
        if isinstance(v, float) and 0 <= v <= 1:
            # Show percentage
            return f"{v*100:.1f}%"
        if isinstance(v, (int,)):
            return f"{v:,}"
        if isinstance(v, float):
            if abs(v - round(v)) < 1e-9:
                return f"{int(round(v)):,}"
            return f"{v:,.1f}"
        return str(v)
    except Exception:
        return str(v)


def create_presentation(title: str, slides: List[PPTSlide], out_path: str, background_image: str = None, add_small_graph: bool = False, add_fancy_graph: bool = False) -> str:
    prs = Presentation()
    # If no background_image provided, try to use sample white->purple background bg_wp_3.png
    if not background_image:
        try:
            repo_root = os.getcwd()
            candidate = os.path.join(repo_root, 'sample_backgrounds', 'bg_wp_3.png')
            if os.path.exists(candidate):
                background_image = candidate
            else:
                # fallback: any bg_wp_*.png in sample_backgrounds
                sb_dir = os.path.join(repo_root, 'sample_backgrounds')
                if os.path.isdir(sb_dir):
                    for fn in sorted(os.listdir(sb_dir)):
                        if fn.startswith('bg_wp_') and fn.lower().endswith('.png'):
                            background_image = os.path.join(sb_dir, fn)
                            break
        except Exception:
            background_image = background_image
    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    # Apply background for the title slide: prefer provided background_image, otherwise fall back to generated gradient
    try:
        if background_image and os.path.exists(background_image):
            try:
                pic = slide.shapes.add_picture(background_image, 0, 0, width=prs.slide_width, height=prs.slide_height)
                slide.shapes._spTree.remove(pic._element)
                slide.shapes._spTree.insert(2, pic._element)
            except Exception:
                pass
        else:
            if Image is not None:
                fd, title_bg = tempfile.mkstemp(suffix='.png')
                os.close(fd)
                dpi = 150
                try:
                    width_px = int(prs.slide_width / 914400 * dpi)
                    height_px = int(prs.slide_height / 914400 * dpi)
                except Exception:
                    width_px, height_px = 1920, 1080
                # soft white->lavender for title
                c1, c2 = (255, 255, 255), (245, 235, 255)
                _make_gradient_background(title_bg, width_px, height_px, c1, c2)
                try:
                    pic = slide.shapes.add_picture(title_bg, 0, 0, width=prs.slide_width, height=prs.slide_height)
                    slide.shapes._spTree.remove(pic._element)
                    slide.shapes._spTree.insert(2, pic._element)
                except Exception:
                    pass
                try:
                    os.remove(title_bg)
                except Exception:
                    pass
            else:
                bg = slide.background
                fill = bg.fill
                fill.solid()
                fill.fore_color.rgb = RGBColor(245, 248, 252)
    except Exception:
        pass

    # Style title text for the title slide
    try:
        slide.shapes.title.text = title
        tf_title = slide.shapes.title.text_frame
        p = tf_title.paragraphs[0]
        p.font.size = Pt(44)
        p.font.bold = True
        p.font.color.rgb = RGBColor(48, 25, 107)
    except Exception:
        slide.shapes.title.text = title

    for s in slides:
        layout = prs.slide_layouts[1] if len(s.content) < 800 else prs.slide_layouts[5]
        slide = prs.slides.add_slide(layout)
        # Decide background image: per-slide overrides global
        chosen_bg = None
        if getattr(s, 'background_image', None):
            chosen_bg = s.background_image
        elif background_image:
            chosen_bg = background_image

        # If background image provided, place it behind other shapes
        if chosen_bg and os.path.exists(chosen_bg):
            try:
                pic = slide.shapes.add_picture(chosen_bg, 0, 0, width=prs.slide_width, height=prs.slide_height)
                # send to back by reordering: picture should be first shape
                slide.shapes._spTree.remove(pic._element)
                slide.shapes._spTree.insert(2, pic._element)
            except Exception:
                # ignore background failures
                pass
        else:
            # Try to generate a fancy gradient PNG background (PIL required).
            try:
                if Image is not None:
                    # Create a temporary PNG background sized to slide dimensions
                    fd, bg_path = tempfile.mkstemp(suffix='.png')
                    os.close(fd)
                    # Convert EMU to pixels: 1 inch = 914400 EMU. Use 150 DPI for good quality.
                    try:
                        dpi = 150
                        width_px = int(prs.slide_width / 914400 * dpi)
                        height_px = int(prs.slide_height / 914400 * dpi)
                    except Exception:
                        width_px, height_px = 1920, 1080

                    # Pick two colors from a small palette based on slide title hash
                    palette_pairs = [((250, 251, 253), (235, 244, 255)), ((247, 249, 252), (236, 245, 242)), ((250, 248, 244), (255, 243, 230)), ((245, 248, 252), (237, 242, 250))]
                    idx = abs(hash(getattr(s, 'title', s.title if hasattr(s, 'title') else title) or title)) % len(palette_pairs)
                    c1, c2 = palette_pairs[idx]
                    _make_gradient_background(bg_path, width_px, height_px, c1, c2)
                    # Insert generated background image behind other shapes
                    try:
                        pic = slide.shapes.add_picture(bg_path, 0, 0, width=prs.slide_width, height=prs.slide_height)
                        slide.shapes._spTree.remove(pic._element)
                        slide.shapes._spTree.insert(2, pic._element)
                    except Exception:
                        pass
                    try:
                        os.remove(bg_path)
                    except Exception:
                        pass
                else:
                    # Fallback to solid color if PIL not available
                    bg = slide.background
                    fill = bg.fill
                    fill.solid()
                    palette = [RGBColor(250, 251, 253), RGBColor(247, 249, 252), RGBColor(250, 248, 244), RGBColor(245, 248, 252)]
                    idx = abs(hash(getattr(s, 'title', s.title if hasattr(s, 'title') else title) or title)) % len(palette)
                    fill.fore_color.rgb = palette[idx]
            except Exception:
                # If anything goes wrong, ignore and continue
                pass

        # Add decorative accents (purple ribbon and circular shape) to emulate the provided template
        try:
            # Purple bottom ribbon
            ribbon_height = Inches(0.5)
            ribbon = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, prs.slide_height - ribbon_height, prs.slide_width, ribbon_height)
            ribbon.fill.solid()
            ribbon.fill.fore_color.rgb = RGBColor(111, 66, 193)
            try:
                ribbon.line.fill.background()
            except Exception:
                pass

            # Decorative circle on the right
            circ_w = Inches(2.4)
            circ_h = Inches(2.4)
            circ = slide.shapes.add_shape(MSO_SHAPE.OVAL, prs.slide_width - circ_w + Inches(0.4), Inches(0.6), circ_w, circ_h)
            circ.fill.solid()
            circ.fill.fore_color.rgb = RGBColor(148, 103, 255)
            try:
                circ.line.fill.background()
            except Exception:
                pass
        except Exception:
            pass

        if slide.shapes.title:
            # Style the title to match modern business templates
            try:
                slide.shapes.title.text = s.title
                tf_title = slide.shapes.title.text_frame
                p = tf_title.paragraphs[0]
                p.font.size = Pt(28)
                p.font.bold = True
                p.font.color.rgb = RGBColor(48, 25, 107)
            except Exception:
                slide.shapes.title.text = s.title
        # Add body
        left = Inches(0.5)
        top = Inches(1.5)
        width = Inches(9)
        height = Inches(5)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        # Enable word wrap and try to auto-size text to fit shape
        try:
            tf.word_wrap = True
        except Exception:
            pass
        try:
            tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        except Exception:
            # Older python-pptx may not support auto_size on TextFrame
            pass

        # Reduce margins to give more room
        try:
            tf.margin_top = Inches(0.05)
            tf.margin_bottom = Inches(0.05)
            tf.margin_left = Inches(0.05)
            tf.margin_right = Inches(0.05)
        except Exception:
            pass

        # Clear default paragraph(s)
        try:
            tf.clear()
        except Exception:
            tf.text = ""

        # Choose base font size based on content length to avoid overflow
        content_len = len(s.content or "")
        if content_len < 800:
            base_size = 14
        elif content_len < 1600:
            base_size = 12
        else:
            base_size = 10

        for line in s.content.splitlines():
            line = line.rstrip()
            if not line:
                p = tf.add_paragraph()
                p.text = ""
                p.font.size = Pt(base_size)
                continue
            if line.startswith("- "):
                p = tf.add_paragraph()
                p.text = line[2:].strip()
                p.level = 1
            else:
                p = tf.add_paragraph()
                p.text = line

            if line.endswith(":"):
                p.font.bold = True
            p.font.size = Pt(base_size)

        # Optionally add a small chart image to the bottom-right of the slide
        if add_small_graph and plt is not None:
            try:
                fd, chart_path = tempfile.mkstemp(suffix='.png')
                os.close(fd)
                # Prefer numeric data if provided
                if getattr(s, 'numeric_values', None) and isinstance(s.numeric_values, dict) and any(isinstance(v, (int, float)) for v in s.numeric_values.values()):
                    if add_fancy_graph:
                        _make_fancy_chart_from_numeric(s.numeric_values, chart_path)
                    else:
                        _make_chart_from_numeric(s.numeric_values, chart_path)
                else:
                    if add_fancy_graph:
                        _make_fancy_chart_from_text(s.content or s.title or '', chart_path)
                    else:
                        _make_small_chart_image(s.content or s.title or '', chart_path)
                # Insert chart: increase sizes and display centered at bottom (above ribbon)
                bottom_margin = Inches(0.6)  # space above bottom edge / ribbon
                if add_fancy_graph:
                    pic_width = Inches(5.0)
                    pic_height = Inches(3.0)
                else:
                    pic_width = Inches(3.5)
                    pic_height = Inches(2.0)
                pic_left = (prs.slide_width - pic_width) / 2
                pic_top = prs.slide_height - pic_height - bottom_margin
                slide.shapes.add_picture(chart_path, pic_left, pic_top, width=pic_width, height=pic_height)
                try:
                    os.remove(chart_path)
                except Exception:
                    pass
            except Exception:
                pass

    prs.save(out_path)
    return out_path
