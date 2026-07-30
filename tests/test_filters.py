"""Tests for filters pack: emboss, apply_filter (sharpen, emboss, brightness/contrast)."""

import pytest
from PIL import Image, ImageFilter

from gimp_mcp.backend.mock import MockBackend


@pytest.fixture
def backend():
    b = MockBackend()
    b.seed_demo()
    return b


@pytest.fixture
def img_id(backend):
    return list(backend._images.keys())[0]


def test_emboss_filter(backend, img_id):
    """Emboss filter produces a directional relief effect."""
    r = backend.emboss(img_id, depth=1.0, azimuth=135.0, elevation=30.0)
    assert r["ok"] is True, f"emboss failed: {r.get('error')}"


def test_emboss_defaults(backend, img_id):
    """Emboss with default parameters works."""
    r = backend.emboss(img_id)
    assert r["ok"] is True, r.get("error")


def test_apply_filter_sharpen(backend, img_id):
    """apply_filter with sharpen works."""
    r = backend.apply_filter(img_id, "sharpen", percent=200.0, radius=3.0)
    assert r["ok"] is True, r.get("error")
    assert r["filter"] == "sharpen"


def test_apply_filter_emboss(backend, img_id):
    """apply_filter with emboss works."""
    r = backend.apply_filter(img_id, "emboss", depth=2.0)
    assert r["ok"] is True, r.get("error")
    assert r["filter"] == "emboss"


def test_apply_filter_brightness(backend, img_id):
    """apply_filter with brightness works."""
    r = backend.apply_filter(img_id, "brightness", factor=1.5)
    assert r["ok"] is True, r.get("error")
    assert r["filter"] == "brightness"


def test_apply_filter_contrast(backend, img_id):
    """apply_filter with contrast works."""
    r = backend.apply_filter(img_id, "contrast", factor=1.8)
    assert r["ok"] is True, r.get("error")
    assert r["filter"] == "contrast"


def test_apply_filter_blur(backend, img_id):
    """apply_filter with blur works."""
    r = backend.apply_filter(img_id, "blur", radius=3.0)
    assert r["ok"] is True, r.get("error")
    assert r["filter"] == "blur"


def test_apply_filter_saturation(backend, img_id):
    """apply_filter with saturation works."""
    r = backend.apply_filter(img_id, "saturation", factor=2.0)
    assert r["ok"] is True, r.get("error")
    assert r["filter"] == "saturation"


def test_apply_filter_unknown_name(backend, img_id):
    """apply_filter with unknown name returns error."""
    r = backend.apply_filter(img_id, "nonexistent")
    assert r["ok"] is False


def test_apply_filter_image_unchanged(backend, img_id):
    """apply_filter with factor=1.0 keeps image dimensions."""
    before = backend.info(img_id)["image"]
    r = backend.apply_filter(img_id, "brightness", factor=1.0)
    after = backend.info(img_id)["image"]
    assert after["width"] == before["width"]
    assert after["height"] == before["height"]


def test_brightness_direct(backend, img_id):
    """Direct brightness call still works."""
    r = backend.brightness(img_id, factor=0.8)
    assert r["ok"] is True


def test_contrast_direct(backend, img_id):
    """Direct contrast call still works."""
    r = backend.contrast(img_id, factor=1.2)
    assert r["ok"] is True


def test_sharpen_direct(backend, img_id):
    """Direct sharpen call still works."""
    r = backend.sharpen(img_id, percent=150.0, radius=2.0)
    assert r["ok"] is True


def test_emboss_preserves_dimensions(backend, img_id):
    """Emboss should not change image dimensions."""
    before = backend.info(img_id)["image"]
    r = backend.emboss(img_id, depth=2.0)
    after = backend.info(img_id)["image"]
    assert after["width"] == before["width"]
    assert after["height"] == before["height"]


def test_ops_emboss_direct():
    """ops.emboss works directly on a PIL Image."""
    from gimp_mcp import ops
    im = Image.new("RGB", (100, 100), "#4488cc")
    result = ops.emboss(im, depth=1.0)
    assert result.size == (100, 100)
    assert result.mode == "RGB"


def test_ops_apply_filter_direct():
    """ops.apply_filter works directly on a PIL Image."""
    from gimp_mcp import ops
    im = Image.new("RGB", (100, 100), "#4488cc")
    result = ops.apply_filter(im, "sharpen", percent=200.0, radius=3.0)
    assert result.size == (100, 100)


def test_ops_apply_filter_invalid():
    """ops.apply_filter raises on invalid filter name."""
    from gimp_mcp import ops
    im = Image.new("RGB", (100, 100), "#4488cc")
    with pytest.raises(ValueError, match="unknown filter"):
        ops.apply_filter(im, "invalid_filter_xyz")
