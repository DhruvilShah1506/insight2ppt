from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_AUTO_SIZE
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
    # Rotate and style x labels
    ax.set_xticklabels(labels, rotation=30, fontsize=8)
    # Add value labels above bars
    try:
        ax.bar_label(bars, labels=[str(int(v)) if float(v).is_integer() else f"{v:.1f}" for v in values], fontsize=8, padding=2)
    except Exception:
        # Older matplotlib may not have bar_label; fallback to manual text
        for b, v in zip(bars, values):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{int(v) if float(v).is_integer() else f'{v:.1f}'}", ha='center', va='bottom', fontsize=8)

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
                ax.text(w + max(vals) * 0.02, b.get_y() + b.get_height() / 2, f"{int(w) if float(w).is_integer() else f'{w:.1f}'}", va='center', fontsize=8)
        except Exception:
            pass
    else:
        fig, ax = plt.subplots(figsize=(2.8, 1.8), dpi=100)
        bars = ax.bar(labels, vals, color='#2b6cb0')
        ax.set_xticklabels(labels, rotation=30, fontsize=8)
        ax.yaxis.grid(True, color='#e6e6e6', linewidth=0.8)
        ax.set_ylabel('Value', fontsize=8)
        try:
            ax.bar_label(bars, labels=[str(int(v)) if float(v).is_integer() else f"{v:.1f}" for v in vals], fontsize=8, padding=2)
        except Exception:
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{int(v) if float(v).is_integer() else f'{v:.1f}'}", ha='center', va='bottom', fontsize=8)

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
        ax.text(b.get_width() + max(vals) * 0.02, b.get_y() + b.get_height() / 2, f"{int(v) if float(v).is_integer() else f'{v:.1f}'}", va='center', fontsize=8, fontweight='bold')

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
        ax.text(b.get_width() + max(values) * 0.02, b.get_y() + b.get_height() / 2, str(v), va='center', fontsize=8, fontweight='bold')

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()
    fig.savefig(target_path, transparent=True)
    plt.close(fig)


def create_presentation(title: str, slides: List[PPTSlide], out_path: str, background_image: str = None, add_small_graph: bool = False, add_fancy_graph: bool = False) -> str:
    prs = Presentation()
    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
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

        if slide.shapes.title:
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
                # Insert chart at bottom-right
                pic_width = Inches(2.0)
                pic_height = Inches(1.5)
                pic_left = prs.slide_width - pic_width - Inches(0.3)
                pic_top = prs.slide_height - pic_height - Inches(0.3)
                slide.shapes.add_picture(chart_path, pic_left, pic_top, width=pic_width, height=pic_height)
                try:
                    os.remove(chart_path)
                except Exception:
                    pass
            except Exception:
                pass

    prs.save(out_path)
    return out_path
