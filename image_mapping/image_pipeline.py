from PIL import Image
import os


# Default hardware size for current testing
# 3 cells horizontally, 1 cell vertically
# Each cell is 2x3 pixels, so total is 6x3 pixels
DEFAULT_TARGET_WIDTH = 6
DEFAULT_TARGET_HEIGHT = 3

# Default grayscale threshold
# 0 = black, 255 = white
# pixel <= threshold -> raised pin -> 1
# pixel > threshold -> flat pin -> 0
DEFAULT_THRESHOLD = 128


def load_image(image_path):
    # Open image and convert it to grayscale
    img = Image.open(image_path).convert("L")
    return img


def resize_image(img, target_width=DEFAULT_TARGET_WIDTH, target_height=DEFAULT_TARGET_HEIGHT):
    # Resize image to the target hardware resolution
    resized_img = img.resize((target_width, target_height))
    return resized_img


def binarize_image(img, threshold=DEFAULT_THRESHOLD):
    # Convert grayscale image to binary image
    # dark pixel -> 1
    # bright pixel -> 0
    width, height = img.size
    binary_img = Image.new("1", (width, height))
    source_pixels = img.load()
    binary_pixels = binary_img.load()

    for y in range(height):
        for x in range(width):
            gray_value = source_pixels[x, y]

            if gray_value <= threshold:
                binary_pixels[x, y] = 1
            else:
                binary_pixels[x, y] = 0

    return binary_img


def get_block_pixels(binary_img, start_x, start_y):
    # Extract one 2x3 block in braille dot order:
    # dot1 dot4
    # dot2 dot5
    # dot3 dot6
    width, height = binary_img.size
    pixels = binary_img.load()

    dot1 = pixels[start_x, start_y] if start_x < width and start_y < height else 0
    dot4 = pixels[start_x + 1, start_y] if start_x + 1 < width and start_y < height else 0

    dot2 = pixels[start_x, start_y + 1] if start_x < width and start_y + 1 < height else 0
    dot5 = pixels[start_x + 1, start_y + 1] if start_x + 1 < width and start_y + 1 < height else 0

    dot3 = pixels[start_x, start_y + 2] if start_x < width and start_y + 2 < height else 0
    dot6 = pixels[start_x + 1, start_y + 2] if start_x + 1 < width and start_y + 2 < height else 0

    return [dot1, dot2, dot3, dot4, dot5, dot6]


def block_to_value(block):
    # Convert one 6-dot block to a 6-bit integer
    # block order: [dot1, dot2, dot3, dot4, dot5, dot6]
    value = 0

    for i in range(6):
        if block[i] == 1:
            value = value | (1 << i)

    return value


def binary_image_to_braille_values(binary_img):
    # Convert the whole binary image into braille cell values
    width, height = binary_img.size
    rows = []

    for y in range(0, height, 3):
        current_row = []

        for x in range(0, width, 2):
            block = get_block_pixels(binary_img, x, y)
            value = block_to_value(block)
            current_row.append(value)

        rows.append(current_row)

    return rows


def flatten_rows(rows):
    # Flatten 2D braille rows into one list
    flat = []

    for row in rows:
        for value in row:
            flat.append(value)

    return flat


def serialize_for_pico(rows):
    # Convert braille rows to a string format suitable for USB sending
    # Example: "18,18,18"
    parts = []

    for row in rows:
        row_text = []
        for value in row:
            row_text.append(str(value))
        parts.append(",".join(row_text))

    return ";".join(parts)


def print_binary_image(binary_img):
    # Print binary image in terminal
    width, height = binary_img.size
    pixels = binary_img.load()

    for y in range(height):
        line = ""
        for x in range(width):
            if pixels[x, y] == 1:
                line = line + "1 "
            else:
                line = line + "0 "
        print(line)


def print_braille_rows(rows):
    # Print braille values row by row
    for row in rows:
        print(row)


def process_image(
    image_path,
    target_width=DEFAULT_TARGET_WIDTH,
    target_height=DEFAULT_TARGET_HEIGHT,
    threshold=DEFAULT_THRESHOLD
):
    # Full processing pipeline:
    # 1. load image
    # 2. resize
    # 3. binarize
    # 4. convert to braille values
    # 5. serialize for pico
    img = load_image(image_path)
    resized_img = resize_image(img, target_width, target_height)
    binary_img = binarize_image(resized_img, threshold)
    rows = binary_image_to_braille_values(binary_img)
    flat_values = flatten_rows(rows)
    pico_data = serialize_for_pico(rows)

    result = {
        "image_path": image_path,
        "target_width": target_width,
        "target_height": target_height,
        "threshold": threshold,
        "rows": rows,
        "flat_values": flat_values,
        "pico_data": pico_data,
        "binary_image": binary_img
    }

    return result


def send_to_pico_placeholder(pico_data):
    # Placeholder for future pico sending
    # Later you can replace this with serial communication code
    print("Pico send placeholder:")
    print(pico_data)


def process_image_for_flask(file_path, threshold=DEFAULT_THRESHOLD):
    # This function is the hook for future Flask route integration
    # A Flask route can call this function directly
    result = process_image(
        image_path=file_path,
        target_width=DEFAULT_TARGET_WIDTH,
        target_height=DEFAULT_TARGET_HEIGHT,
        threshold=threshold
    )

    response = {
        "rows": result["rows"],
        "flat_values": result["flat_values"],
        "pico_data": result["pico_data"],
        "target_width": result["target_width"],
        "target_height": result["target_height"],
        "threshold": result["threshold"]
    }

    return response


def main():
    # Change this to the image you want to test
    image_path = "test_images/vertical_line_6x3.png"

    result = process_image(
        image_path=image_path,
        target_width=DEFAULT_TARGET_WIDTH,
        target_height=DEFAULT_TARGET_HEIGHT,
        threshold=DEFAULT_THRESHOLD
    )

    print("Processed image:", result["image_path"])
    print("Target size:", str(result["target_width"]) + "x" + str(result["target_height"]))
    print("Threshold:", result["threshold"])
    print()

    print("Binary image:")
    print_binary_image(result["binary_image"])
    print()

    print("Braille rows:")
    print_braille_rows(result["rows"])
    print()

    print("Flat values:")
    print(result["flat_values"])
    print()

    print("Serialized pico data:")
    print(result["pico_data"])
    print()

    send_to_pico_placeholder(result["pico_data"])


if __name__ == "__main__":
    main()