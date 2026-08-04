import json, os
def apply_sharpen(image_path, output_path, amount=1.0):
    os.system(f"gimp -i -b "(python-fu-sharpen RUN-NONINTERACTIVE "{image_path}" "{output_path}" {amount})" -b "(gimp-quit 0)"")
def apply_emboss(image_path, output_path, depth=3):
    os.system(f"gimp -i -b "(python-fu-emboss RUN-NONINTERACTIVE "{image_path}" "{output_path}" {depth})" -b "(gimp-quit 0)"")
def apply_brightness_contrast(image_path, output_path, brightness=0, contrast=0):
    os.system(f"gimp -i -b "(python-fu-brightness-contrast RUN-NONINTERACTIVE "{image_path}" "{output_path}" {brightness} {contrast})" -b "(gimp-quit 0)"")
