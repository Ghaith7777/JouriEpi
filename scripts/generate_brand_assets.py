from pathlib import Path
from PIL import Image, ImageFilter
import shutil

root = Path(__file__).resolve().parents[1]
assets = root / 'ui_qt' / 'assets'
source = assets / 'new_logo.png'
if not source.is_file():
    raise FileNotFoundError(source)
with Image.open(source) as original:
    image = original.convert('RGBA')
    def fitted(size):
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        scale = min(size / image.width, size / image.height)
        dimensions = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        emblem = image.resize(dimensions, Image.Resampling.LANCZOS)
        canvas.alpha_composite(emblem, ((size - emblem.width) // 2, (size - emblem.height) // 2))
        return canvas
    fitted(256).save(assets / 'logo_256.png', optimize=True)
    img_32 = fitted(32)
    img_32 = img_32.filter(ImageFilter.UnsharpMask(radius=1.0, percent=120, threshold=2))
    img_32.save(assets / 'logo_32.png', optimize=True)
    fitted(192).save(assets / 'logo_header.png', optimize=True)
    fitted(256).save(assets / 'app_icon.ico', format='ICO', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
installer_icon = root / 'installer' / 'app_icon.ico'
shutil.copy2(assets / 'app_icon.ico', installer_icon)
print(f'Source: {source} ({image.width}x{image.height})')
for name in ('app_icon.ico','logo_256.png','logo_32.png','logo_header.png'):
    p = assets / name
    with Image.open(p) as im:
        print(f'{p.relative_to(root)}: {im.format} {im.size} mode={im.mode} bytes={p.stat().st_size}')
print(f'{installer_icon.relative_to(root)}: {installer_icon.stat().st_size} bytes')
