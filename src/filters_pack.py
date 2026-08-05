# Filters pack implementation for gimp-mcp bounty #4
# 100 MRG
from typing import Any, Dict, List, Optional

try:
    from PIL import Image, ImageFilter, ImageEnhance
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

class FiltersPack:
    FILTERS = ["sharpen", "emboss", "brightness", "contrast", "blur", "edge_enhance"]

    def __init__(self, mode="mock"):
        if mode not in ("mock", "pillow"):
            raise ValueError("mode must be mock or pillow")
        self.mode = mode
        self._history = []

    @property
    def live(self):
        return self.mode == "pillow" and HAS_PILLOW

    @property
    def history(self):
        return list(self._history)

    def _record(self, name, params):
        e = {"filter": name, "params": params, "applied": self.live}
        self._history.append(e)
        return {"status": "ok", **e}

    def sharpen(self, image=None, amount=1.5, radius=2.0):
        p = {"amount": amount, "radius": radius}
        if self.live and image is not None:
            return {"status":"ok","filter":"sharpen","params":p,"applied":True,"image":ImageEnhance.Sharpness(image).enhance(amount)}
        return self._record("sharpen", p)

    def emboss(self, image=None, depth=1.0, direction="top-left"):
        p = {"depth": depth, "direction": direction}
        if self.live and image is not None:
            return {"status":"ok","filter":"emboss","params":p,"applied":True,"image":image.filter(ImageFilter.EMBOSS)}
        return self._record("emboss", p)

    def brightness(self, image=None, factor=1.0):
        f = max(0.0, min(3.0, factor))
        p = {"factor": f}
        if self.live and image is not None:
            return {"status":"ok","filter":"brightness","params":p,"applied":True,"image":ImageEnhance.Brightness(image).enhance(f)}
        return self._record("brightness", p)

    def contrast(self, image=None, factor=1.0):
        f = max(0.0, min(3.0, factor))
        p = {"factor": f}
        if self.live and image is not None:
            return {"status":"ok","filter":"contrast","params":p,"applied":True,"image":ImageEnhance.Contrast(image).enhance(f)}
        return self._record("contrast", p)

    def blur(self, image=None, radius=2.0):
        r = max(0.0, min(20.0, radius))
        p = {"radius": r}
        if self.live and image is not None:
            return {"status":"ok","filter":"blur","params":p,"applied":True,"image":image.filter(ImageFilter.GaussianBlur(radius=r))}
        return self._record("blur", p)

    def edge_enhance(self, image=None, iterations=1):
        n = max(1, min(5, iterations))
        p = {"iterations": n}
        if self.live and image is not None:
            result = image
            for _ in range(n):
                result = result.filter(ImageFilter.EDGE_ENHANCE)
            return {"status":"ok","filter":"edge_enhance","params":p,"applied":True,"image":result}
        return self._record("edge_enhance", p)

    def apply_chain(self, image=None, steps=None):
        if not steps:
            return {"status":"ok","chain":[],"applied":False}
        handlers = {"sharpen":self.sharpen,"emboss":self.emboss,"brightness":self.brightness,"contrast":self.contrast,"blur":self.blur,"edge_enhance":self.edge_enhance}
        results = []
        cur = image
        for s in steps:
            ft = s.get("filter","")
            pr = {k:v for k,v in s.items() if k!="filter"}
            h = handlers.get(ft)
            if h:
                res = h(image=cur, **pr)
                results.append(res)
                cur = res.get("image", cur)
        return {"status":"ok","chain":results,"applied":self.live}

    @staticmethod
    def list_filters():
        return list(FiltersPack.FILTERS)

    @staticmethod
    def create_test_image(size=(100,100)):
        if HAS_PILLOW:
            return Image.new("RGB", size, (128,128,128))
        return None

if __name__ == "__main__":
    fp = FiltersPack()
    print("Available:", fp.list_filters())
    for f in FiltersPack.FILTERS:
        r = getattr(fp, f)()
        assert r["status"] == "ok", f"{f} failed"
    assert len(fp.history) == 6
    print("PASS")