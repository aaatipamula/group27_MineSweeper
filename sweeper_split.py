from PIL import Image

# Open and scale up the image
img = Image.open("images/analog#.png")
img = img.resize((668, 94), Image.NEAREST)  # keeps pixel art crisp

rows, cols = 1, 12
cell_width = 680 // cols  # 135
cell_height = 94 // rows  # 135

for row in range(rows):
    for col in range(cols):
        left = col * cell_width
        upper = row * cell_height
        right = left + cell_width
        lower = upper + cell_height

        cell = img.crop((left, upper, right, lower))
        cell.save(f"cell{col}.png")
