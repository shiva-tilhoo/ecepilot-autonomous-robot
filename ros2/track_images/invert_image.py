from PIL import Image

# Load the image
img = Image.open('image.png').convert('L')  # 'L' for greyscale

# Invert the pixels
img_inv = Image.eval(img, lambda x: 255 - x)

# Save the inverted image
img_inv.save('image_inverted.png')
print('Inverted image saved as image_inverted.png')
