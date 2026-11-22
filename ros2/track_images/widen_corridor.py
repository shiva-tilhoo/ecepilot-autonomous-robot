from PIL import Image
import numpy as np
from scipy.ndimage import binary_dilation

# Load the image
img = Image.open('image.png').convert('L')
arr = np.array(img)

# Binarise: True for white (corridor), False for black (wall)
binary = arr > 128

# SOLUTION: use a larger structuring element or more iterations
# Here a 5x5 disc (or square) is used to dilate faster
struct = np.ones((5, 5)) 
# More iterations give "wide corridors"
dilated = binary_dilation(binary, structure=struct, iterations=20)

# Convert to an image
# (dilated * 255) maps True to 255 (white) and False to 0 (black)
corridor_img = Image.fromarray((dilated * 255).astype(np.uint8))
corridor_img.save('image_corridor_widened.png')

print('Expansion done: the white corridors have "eaten" the black walls.')