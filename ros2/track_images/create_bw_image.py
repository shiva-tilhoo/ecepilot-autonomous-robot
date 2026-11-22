from PIL import Image
import numpy as np

# Load the existing image
img = Image.open('image2.png').convert('RGB')
arr = np.array(img, dtype=np.uint8, copy=True)

# Black/white thresholds
black_thresh = 60
white_thresh = 200

# Replace the pixels
for y in range(arr.shape[0]):
	for x in range(arr.shape[1]):
		r, g, b = arr[y, x]
		# If close to black
		if r < black_thresh and g < black_thresh and b < black_thresh:
			arr[y, x] = [0, 0, 0]
		# If close to white
		elif r > white_thresh and g > white_thresh and b > white_thresh:
			arr[y, x] = [255, 255, 255]
		# Otherwise, pick the closest
		else:
			if (r+g+b)/3 < 128:
				arr[y, x] = [0, 0, 0]
			else:
				arr[y, x] = [255, 255, 255]

# Save
img_out = Image.fromarray(arr)
img_out.save('image.png')
print('image.png converted to pure black/white.')
