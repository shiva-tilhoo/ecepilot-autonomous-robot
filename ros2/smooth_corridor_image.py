from PIL import Image
import numpy as np
from scipy.ndimage import binary_erosion, binary_dilation

# Load the existing image
img = Image.open('image.png').convert('L')
arr = np.array(img)

# Binarise (black corridor, white elsewhere)
corridor = arr < 128

# Apply a dilation then an erosion to round the edges
corridor_smoothed = binary_dilation(corridor, structure=np.ones((7,7)))
corridor_smoothed = binary_erosion(corridor_smoothed, structure=np.ones((7,7)))

# Rebuild the image
arr_out = np.where(corridor_smoothed, 0, 255).astype(np.uint8)
img_out = Image.fromarray(arr_out, mode='L')
img_out.save('image.png')
print('image.png: corridor rounded and smoothed.')
