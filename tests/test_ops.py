"""Tests for filter and selection operations."""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import pytest

@pytest.fixture
def img(): return Image.new("RGB", (100, 100), (128, 128, 128))

def test_sharpen(img):
    from gimp_mcp.ops import sharpen_op
    result = sharpen_op(img)
    assert result.size == img.size

def test_emboss(img):
    from gimp_mcp.ops import emboss_op
    result = emboss_op(img)
    assert result.size == img.size

def test_brightness_contrast(img):
    from gimp_mcp.ops import brightness_contrast_op
    result = brightness_contrast_op(img, 1.5, 1.2)
    assert result.size == img.size

def test_fill_op(img):
    from gimp_mcp.ops import fill_op
    sel = {"type": "rect", "x": 10, "y": 10, "width": 50, "height": 50}
    result = fill_op(img, sel, "#ff0000")
    assert result.size == img.size

def test_stroke_op(img):
    from gimp_mcp.ops import stroke_op
    sel = {"type": "rect", "x": 10, "y": 10, "width": 50, "height": 50}
    result = stroke_op(img, sel, 3, "#0000ff")
    assert result.size == img.size

def test_edge_detect(img):
    from gimp_mcp.ops import edge_detect_op
    result = edge_detect_op(img)
    assert result.size == img.size

def test_smooth(img):
    from gimp_mcp.ops import smooth_op
    result = smooth_op(img)
    assert result.size == img.size

def test_detail(img):
    from gimp_mcp.ops import detail_op
    result = detail_op(img)
    assert result.size == img.size
