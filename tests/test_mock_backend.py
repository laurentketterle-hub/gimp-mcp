from gimp_mcp.backend import get_backend
from gimp_mcp.backend.mock import MockBackend
from gimp_mcp.config import set_mode


def test_seed_and_list():
    b = MockBackend()
    s = b.seed_demo()
    assert s["ok"] is True
    assert b.list_images()
    d = b.doctor()
    assert d["ok"] is True
    assert d["mode"] == "mock"


def test_resize_blur_export(tmp_path):
    b = MockBackend()
    s = b.seed_demo()
    iid = s["image"]["id"]
    r = b.resize(iid, 100, 80)
    assert r["ok"] is True
    assert r["image"]["width"] == 100
    assert b.blur(iid, 1.0)["ok"] is True
    out = tmp_path / "x.png"
    exp = b.export(iid, str(out))
    assert exp["ok"] is True
    assert out.is_file()


def test_batch_resize(tmp_path):
    b = MockBackend()
    s = b.seed_demo()
    src = tmp_path / "in"
    dst = tmp_path / "out"
    src.mkdir()
    # copy seeded image into input
    from shutil import copy2

    copy2(s["image"]["path"], src / "a.png")
    res = b.batch_resize(str(src), str(dst), 64, 64)
    assert res["ok"] is True
    assert res["count"] >= 1


def test_get_backend_mock():
    set_mode("mock")
    assert get_backend().name == "mock"


def test_selection_rect_fill_stroke():
    """Test selection_rect → fill_selection → stroke_selection workflow."""
    from gimp_mcp.backend.mock import MockBackend

    b = MockBackend()
    s = b.seed_demo()
    iid = s["image"]["id"]

    # 1. Create selection
    r = b.selection_rect(iid, 50, 50, 100, 80)
    assert r["ok"] is True
    assert r["selection"]["x"] == 50
    assert r["selection"]["y"] == 50
    assert r["selection"]["width"] == 100
    assert r["selection"]["height"] == 80

    # 2. Fill selection
    r = b.fill_selection(iid, color="#ff0000", opacity=0.5)
    assert r["ok"] is True

    # 3. Stroke selection
    r = b.stroke_selection(iid, color="#00ff00", line_width=3)
    assert r["ok"] is True

    # 4. Verify image dimensions unchanged
    info = b.info(iid)
    assert info["ok"] is True
    assert info["image"]["width"] == 640
    assert info["image"]["height"] == 360


def test_selection_without_selection_fails():
    """fill_selection / stroke_selection should fail without active selection."""
    from gimp_mcp.backend.mock import MockBackend

    b = MockBackend()
    s = b.seed_demo()
    iid = s["image"]["id"]

    # No selection created → fill should fail
    r = b.fill_selection(iid)
    assert r["ok"] is False
    assert "no active selection" in r.get("error", "").lower()

    # No selection → stroke should fail
    r = b.stroke_selection(iid)
    assert r["ok"] is False
    assert "no active selection" in r.get("error", "").lower()


def test_selection_pipeline_ops():
    """Verify selection ops work through the pipeline."""
    from gimp_mcp.backend.mock import MockBackend

    b = MockBackend()
    s = b.seed_demo()
    iid = s["image"]["id"]

    steps = [
        {"op": "selection_rect", "x": 20, "y": 30, "width": 200, "height": 150},
        {"op": "fill_selection", "sel_x": 20, "sel_y": 30, "sel_width": 200, "sel_height": 150, "color": "#3366cc", "opacity": 0.8},
        {"op": "stroke_selection", "sel_x": 20, "sel_y": 30, "sel_width": 200, "sel_height": 150, "color": "#ffffff", "line_width": 2},
    ]

    r = b.pipeline(iid, steps)
    assert r["ok"] is True
    assert len(r["applied"]) == 3
