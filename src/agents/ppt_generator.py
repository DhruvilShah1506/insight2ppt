from pptx import Presentation
from pptx.util import Inches, Pt
from typing import List
from ..models import PPTSlide


def create_presentation(title: str, slides: List[PPTSlide], out_path: str) -> str:
    prs = Presentation()
    # Title slide
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)
    slide.shapes.title.text = title

    for s in slides:
        layout = prs.slide_layouts[1] if len(s.content) < 800 else prs.slide_layouts[5]
        slide = prs.slides.add_slide(layout)
        if slide.shapes.title:
            slide.shapes.title.text = s.title
        # Add body
        left = Inches(0.5)
        top = Inches(1.5)
        width = Inches(9)
        height = Inches(5)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        # Clear default paragraph(s)
        try:
            tf.clear()
        except Exception:
            tf.text = ""

        for line in s.content.splitlines():
            line = line.rstrip()
            if not line:
                p = tf.add_paragraph()
                p.text = ""
                p.font.size = Pt(14)
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
            p.font.size = Pt(14)

    prs.save(out_path)
    return out_path
