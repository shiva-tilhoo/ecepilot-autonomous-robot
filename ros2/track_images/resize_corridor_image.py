from PIL import Image

# Parameters
input_path = 'image.png'  # Path of the image to enlarge
output_path = 'image.png'  # Output path
scale_factor = 3  # Enlargement factor (e.g. 1.5 = +50%)

# Load the image
img = Image.open(input_path)

# Compute the new size
new_size = (int(img.width * scale_factor), int(img.height * scale_factor))

# Redimensionnement
img_resized = img.resize(new_size, resample=Image.NEAREST)

# Save
img_resized.save(output_path)
print(f"Resized image saved as {output_path} (factor {scale_factor})")
