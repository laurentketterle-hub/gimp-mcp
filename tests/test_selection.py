"""Tests for selection tools (issue #7)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from gimp_mcp.backend.mock import MockBackend


class TestSelectionRectangular:
    def setup_method(self):
        self.mock = MockBackend()
        r = self.mock.new_image(800, 600)
        self.img_id = r["image"]["id"]

    def test_basic(self):
        result = self.mock.selection_rectangular(self.img_id, 10, 20, 200, 150)
        assert result["ok"] is True
        assert result["selection"]["x"] == 10
        assert result["selection"]["width"] == 200
        assert self.mock._selection is not None
        assert self.mock._selection["x"] == 10

    def test_stores_selection_state(self):
        self.mock.selection_rectangular(self.img_id, 50, 50, 300, 200)
        assert self.mock._selection["x"] == 50
        assert self.mock._selection["y"] == 50
        assert self.mock._selection["width"] == 300

    def test_negative_coords_clamped(self):
        result = self.mock.selection_rectangular(self.img_id, -5, -10, 100, 100)
        assert result["ok"] is True
        assert result["selection"]["x"] == 0

    def test_bad_image_id(self):
        result = self.mock.selection_rectangular("bad_id_999", 0, 0, 100, 100)
        assert result["ok"] is False


class TestFillSelection:
    def setup_method(self):
        self.mock = MockBackend()
        r = self.mock.new_image(800, 600)
        self.img_id = r["image"]["id"]

    def test_fill_after_selection(self):
        self.mock.selection_rectangular(self.img_id, 0, 0, 100, 100)
        result = self.mock.fill_selection(self.img_id, "#ff0000")
        assert result["ok"] is True
        assert result["color"] == "#ff0000"

    def test_fill_no_selection(self):
        result = self.mock.fill_selection(self.img_id, "#00ff00")
        assert result["ok"] is False
        assert "no active selection" in result["error"]

    def test_fill_default_color(self):
        self.mock.selection_rectangular(self.img_id, 0, 0, 50, 50)
        result = self.mock.fill_selection(self.img_id)
        assert result["ok"] is True
        assert result["color"] == "#000000"


class TestStrokeSelection:
    def setup_method(self):
        self.mock = MockBackend()
        r = self.mock.new_image(800, 600)
        self.img_id = r["image"]["id"]

    def test_stroke_after_selection(self):
        self.mock.selection_rectangular(self.img_id, 10, 10, 150, 150)
        result = self.mock.stroke_selection(self.img_id, "#0000ff", 3)
        assert result["ok"] is True
        assert result["width"] == 3
        assert result["color"] == "#0000ff"

    def test_stroke_default_width(self):
        self.mock.selection_rectangular(self.img_id, 0, 0, 200, 200)
        result = self.mock.stroke_selection(self.img_id, "#ffff00")
        assert result["ok"] is True
        assert result["width"] == 2

    def test_stroke_no_selection(self):
        result = self.mock.stroke_selection(self.img_id, "#ffffff", 1)
        assert result["ok"] is False
        assert "no active selection" in result["error"]


class TestSelectionChain:
    def setup_method(self):
        self.mock = MockBackend()
        r = self.mock.new_image(800, 600)
        self.img_id = r["image"]["id"]

    def test_full_chain(self):
        r1 = self.mock.selection_rectangular(self.img_id, 0, 0, 300, 300)
        assert r1["ok"] is True
        r2 = self.mock.fill_selection(self.img_id, "#333333")
        assert r2["ok"] is True
        r3 = self.mock.stroke_selection(self.img_id, "#ffffff", 2)
        assert r3["ok"] is True

    def test_chain_preserves_image(self):
        self.mock.selection_rectangular(self.img_id, 100, 100, 200, 200)
        self.mock.fill_selection(self.img_id, "#ff0000")
        self.mock.stroke_selection(self.img_id, "#000000", 1)
        info = self.mock.info(self.img_id)
        assert info["ok"] is True
        assert info["image"]["width"] == 800
