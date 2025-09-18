from PIL import Image

# Open and scale up the image
img = Image.open("images/sweepertiles.png")
img = img.resize((1080, 270), Image.NEAREST)  # keeps pixel art crisp

rows, cols = 2, 8
cell_width = 1080 // cols  # 135
cell_height = 270 // rows  # 135

for row in range(rows):
    for col in range(cols):
        left = col * cell_width
        upper = row * cell_height
        right = left + cell_width
        lower = upper + cell_height

        cell = img.crop((left, upper, right, lower))
        cell.save(f"cell_{row}_{col}.png")
