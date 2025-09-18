from PIL import Image # importing Pillow so I can work with images

# Open and scale up the image
img = Image.open("images/sweepertiles.png")  # load the big image
img = img.resize((1080, 270), Image.NEAREST)   # resize it bigger, keeping the pixel look sharp

rows, cols = 2, 8 # total layout of the grid
cell_width = 1080 // cols  # width of each small tile (135px)
cell_height = 270 // rows  # height of each small tile (135px)

# go through each row and column of the grid
for row in range(rows):  # loop rows
    for col in range(cols): # loop cols
        # figure out the exact box (left, top, right, bottom) for this cell
        left = col * cell_width  # start x position
        upper = row * cell_height # start y position
        right = left + cell_width # end x position
        lower = upper + cell_height # end y position
        # cut out the small cell from the sprite sheet
        cell = img.crop((left, upper, right, lower)) # make a sub-image
        # save that piece to its own PNG file
        cell.save(f"cell_{row}_{col}.png") # name includes its row/col
