def on_save_click(canvas):
    imtk = getattr(canvas, "image_ref", None)
    if imtk is None:
        print("No image loaded (canvas.image_ref is missing).")
        return
    try:
        w, h = imtk.width(), imtk.height()
        print(f"image_ref OK -> {imtk!r}, size=({w}x{h})")
    except Exception as e:
        print(f"image_ref exists but not usable: {e}")