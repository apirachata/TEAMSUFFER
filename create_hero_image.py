#!/usr/bin/env python
from PIL import Image, ImageDraw

# Create placeholder hero image
img = Image.new('RGB', (1920, 1080), color='#0a0e27')
draw = ImageDraw.Draw(img)

# Add gradient-like effect manually
for i in range(1920):
    r = int(10 + (i / 1920) * 20)
    g = int(14 + (i / 1920) * 20)
    b = int(39 + (i / 1920) * 20)
    draw.rectangle([(i, 0), (i+1, 1080)], fill=(r, g, b))

img.save('d:\\TEAMSUFFER\\static\\images\\login-hero.jpg')
print('Created login-hero.jpg')
