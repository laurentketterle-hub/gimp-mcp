import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.filters_pack import FiltersPack

class TestFiltersPackMock:
    def setup_method(self):
        self.fp = FiltersPack()

    def test_sharpen(self):
        r = self.fp.sharpen(amount=1.5)
        assert r["status"] == "ok"
        assert r["filter"] == "sharpen"
        assert not r["applied"]

    def test_emboss(self):
        r = self.fp.emboss(depth=2.0)
        assert r["status"] == "ok"

    def test_brightness(self):
        r = self.fp.brightness(factor=1.2)
        assert r["status"] == "ok"
        assert r["params"]["factor"] == 1.2

    def test_contrast(self):
        r = self.fp.contrast(factor=0.8)
        assert r["status"] == "ok"

    def test_blur(self):
        r = self.fp.blur(radius=3.0)
        assert r["status"] == "ok"

    def test_edge_enhance(self):
        r = self.fp.edge_enhance(iterations=2)
        assert r["status"] == "ok"

    def test_history(self):
        fp = FiltersPack()
        fp.sharpen()
        fp.emboss()
        assert len(fp.history) == 2
        assert fp.history[0]["filter"] == "sharpen"

    def test_brightness_clamp(self):
        r = self.fp.brightness(factor=5.0)
        assert r["params"]["factor"] == 3.0
        r = self.fp.brightness(factor=-1.0)
        assert r["params"]["factor"] == 0.0

    def test_contrast_clamp(self):
        r = self.fp.contrast(factor=10.0)
        assert r["params"]["factor"] == 3.0

    def test_blur_clamp(self):
        r = self.fp.blur(radius=100.0)
        assert r["params"]["radius"] == 20.0

    def test_edge_enhance_clamp(self):
        r = self.fp.edge_enhance(iterations=10)
        assert r["params"]["iterations"] == 5
        r = self.fp.edge_enhance(iterations=0)
        assert r["params"]["iterations"] == 1

    def test_apply_chain_empty(self):
        r = self.fp.apply_chain(steps=[])
        assert r["status"] == "ok"
        assert r["applied"] == False

    def test_apply_chain_multiple(self):
        steps = [{"filter":"sharpen","amount":2.0},{"filter":"contrast","factor":1.5}]
        r = self.fp.apply_chain(steps=steps)
        assert r["status"] == "ok"
        assert len(r["chain"]) == 2

    def test_list_filters(self):
        f = FiltersPack.list_filters()
        assert len(f) == 6
        assert "sharpen" in f

    def test_create_test_image(self):
        img = FiltersPack.create_test_image()
        assert img is None or hasattr(img, "size")

class TestMode:
    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            FiltersPack(mode="invalid")

    def test_default_mock(self):
        fp = FiltersPack()
        assert fp.mode == "mock"

    def test_pillow_mode(self):
        fp = FiltersPack(mode="pillow")
        assert fp.mode == "pillow"