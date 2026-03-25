from PIL import Image
import os


# Create a blank white image
def create_blank_image(width, height):
    return Image.new("L", (width, height), 255)


# Draw a horizontal line across the whole image
def draw_horizontal_line(img, row_index):
    pixels = img.load()
    width, height = img.size

    if 0 <= row_index < height:
        for x in range(width):
            pixels[x, row_index] = 0


# Draw a vertical line across the whole image
def draw_vertical_line(img, col_index):
    pixels = img.load()
    width, height = img.size

    if 0 <= col_index < width:
        for y in range(height):
            pixels[col_index, y] = 0


# Draw a hollow rectangle
def draw_hollow_rectangle(img, left, top, right, bottom):
    pixels = img.load()
    width, height = img.size

    # Keep coordinates inside the image
    left = max(0, left)
    top = max(0, top)
    right = min(width - 1, right)
    bottom = min(height - 1, bottom)

    if left > right or top > bottom:
        return

    for x in range(left, right + 1):
        pixels[x, top] = 0
        pixels[x, bottom] = 0

    for y in range(top, bottom + 1):
        pixels[left, y] = 0
        pixels[right, y] = 0


# Draw a filled rectangle
def draw_filled_rectangle(img, left, top, right, bottom):
    pixels = img.load()
    width, height = img.size

    # Keep coordinates inside the image
    left = max(0, left)
    top = max(0, top)
    right = min(width - 1, right)
    bottom = min(height - 1, bottom)

    if left > right or top > bottom:
        return

    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            pixels[x, y] = 0


# Draw a simple triangle
# This version makes a centered isosceles triangle as much as possible
def draw_triangle(img):
    pixels = img.load()
    width, height = img.size

    center_x = width // 2

    for y in range(height):
        # Expand the triangle as y increases
        half_span = y
        left = center_x - half_span
        right = center_x + half_span

        for x in range(left, right + 1):
            if 0 <= x < width:
                pixels[x, y] = 0


# Save one image
def save_image(img, path):
    img.save(path)


def main():
    os.makedirs("test_images", exist_ok=True)

    # You can change these two numbers later without changing the draw logic
    width = 6
    height = 3

    # 1. Horizontal line
    img1 = create_blank_image(width, height)
    draw_horizontal_line(img1, height // 2)
    save_image(img1, "test_images/horizontal_line_6x3.png")

    # 2. Vertical line
    img2 = create_blank_image(width, height)
    draw_vertical_line(img2, width // 2)
    save_image(img2, "test_images/vertical_line_6x3.png")

    # 3. Hollow rectangle
    img3 = create_blank_image(width, height)
    draw_hollow_rectangle(img3, 1, 0, width - 2, height - 1)
    save_image(img3, "test_images/hollow_rectangle_6x3.png")

    # 4. Filled rectangle
    img4 = create_blank_image(width, height)
    draw_filled_rectangle(img4, 1, 0, width - 2, height - 1)
    save_image(img4, "test_images/filled_rectangle_6x3.png")

    # 5. Triangle
    img5 = create_blank_image(width, height)
    draw_triangle(img5)
    save_image(img5, "test_images/triangle_6x3.png")

    print("Images generated successfully in test_images/")


if __name__ == "__main__":
    main()