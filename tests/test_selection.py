"""Tests for selection rectangular + fill/stroke feature."""

from gimp_mcp.config import set_mode
from gimp_mcp.backend import get_backend


def setup_function():
    set_mode("mock")


def test_selection_rect():
    """Create a rectangular selection."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    sel = b.selection_rect(iid, 50, 50, 100, 100)
    assert sel["ok"]
    assert sel["selection"]["type"] == "rectangle"
    assert sel["selection"]["x"] == 50
    assert sel["selection"]["y"] == 50
    assert sel["selection"]["width"] == 100
    assert sel["selection"]["height"] == 100
    assert sel["selection"]["feather"] is False


def test_selection_rect_with_feather():
    """Create a rectangular selection with feather enabled."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    sel = b.selection_rect(iid, 10, 10, 80, 80, feather=True, feather_radius=8.0)
    assert sel["ok"]
    assert sel["selection"]["feather"] is True
    assert sel["selection"]["feather_radius"] == 8.0


def test_selection_fill():
    """Fill a selection with color."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    # Create selection first
    b.selection_rect(iid, 50, 50, 100, 100)

    # Fill it red
    fill = b.selection_fill(iid, "#ff0000")
    assert fill["ok"]
    assert fill["image"]["id"] == iid

    # Verify the image was modified (pixel check)
    im = b._load(iid)
    # Middle of selection should be red
    px = im.getpixel((100, 100))  # center of selection
    assert px == (255, 0, 0) or px == (255, 0, 0, 255)


def test_selection_stroke():
    """Stroke (border) a selection."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    # Create selection
    b.selection_rect(iid, 50, 50, 100, 100)

    # Stroke it green with width 3
    stroke = b.selection_stroke(iid, width=3, color="#00ff00")
    assert stroke["ok"]
    assert stroke["image"]["id"] == iid

    # Verify the border was drawn
    im = b._load(iid)
    # Border pixel (top-left of selection area, should be green)
    # May be green or white depending on stroke width positioning
    # At minimum, some pixels should be green near border
    border_px = im.getpixel((50, 50))
    assert border_px == (0, 255, 0) or border_px == (0, 255, 0, 255)


def test_selection_none():
    """Clear a selection."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    b.selection_rect(iid, 50, 50, 100, 100)
    result = b.selection_none(iid)
    assert result["ok"]
    assert result["selection"] is None


def test_fill_without_selection_fails():
    """Fill should fail if no selection is active."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    result = b.selection_fill(iid, "#ff0000")
    assert not result["ok"]
    assert "No active selection" in result["error"]


def test_stroke_without_selection_fails():
    """Stroke should fail if no selection is active."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    result = b.selection_stroke(iid, width=2, color="#0000ff")
    assert not result["ok"]
    assert "No active selection" in result["error"]


def test_selection_persists_for_image():
    """Selection should persist per-image until cleared."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    b.selection_rect(iid, 10, 10, 50, 50)
    # Fill should work without re-setting selection
    fill = b.selection_fill(iid, "#0000ff")
    assert fill["ok"]

    # Clear and then fill should fail
    b.selection_none(iid)
    fill2 = b.selection_fill(iid, "#00ff00")
    assert not fill2["ok"]


def test_selection_cleared_on_image_close():
    """Selection should be cleaned up when image is closed."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    b.selection_rect(iid, 10, 10, 50, 50)
    b.close_image(iid)

    # Re-create image with same workflow — selection should not persist
    r2 = b.new_image(200, 200, "#ffffff")
    iid2 = r2["image"]["id"]
    fill = b.selection_fill(iid2, "#ff0000")
    assert not fill["ok"]


def test_selection_fill_and_stroke_combined():
    """Fill then stroke the same selection."""
    b = get_backend()
    r = b.new_image(200, 200, "#ffffff")
    iid = r["image"]["id"]

    b.selection_rect(iid, 50, 50, 100, 100)
    b.selection_fill(iid, "#ff0000")
    b.selection_stroke(iid, width=2, color="#000000")

    im = b._load(iid)
    # Center of selection should be red (fill)
    center = im.getpixel((100, 100))
    assert center == (255, 0, 0) or center == (255, 0, 0, 255)
    # Border should be black
    border = im.getpixel((50, 50))
    assert border == (0, 0, 0) or border == (0, 0, 0, 255)
