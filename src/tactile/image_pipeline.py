
from PIL import Image

DEFAULT_TARGET_WIDTH = 6
DEFAULT_TARGET_HEIGHT = 3
DEFAULT_THRESHOLD = 128


def load_image(image_path):
    img = Image.open(image_path).convert("L")
    return img


def resize_image(
    img, target_width=DEFAULT_TARGET_WIDTH, target_height=DEFAULT_TARGET_HEIGHT
):
    resized_img = img.resize((target_width, target_height))
    return resized_img


def binarize_image(img, threshold=DEFAULT_THRESHOLD):
    width, height = img.size
    binary_img = Image.new("L", (width, height))
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


def binary_image_to_matrix(binary_img):
    width, height = binary_img.size
    pixels = binary_img.load()
    matrix = []

    for y in range(height):
        current_row = []
        for x in range(width):
            if pixels[x, y] == 1:
                current_row.append(1)
            else:
                current_row.append(0)
        matrix.append(current_row)

    return matrix


def flatten_matrix(matrix):
    flat = []

    for row in matrix:
        for value in row:
            flat.append(value)

    return flat


def serialize_matrix_for_pico(matrix):
    parts = []

    for row in matrix:
        row_text = []
        for value in row:
            row_text.append(str(value))
        parts.append(",".join(row_text))

    return ";".join(parts)


def get_block_pixels(binary_img, start_x, start_y):
    width, height = binary_img.size
    pixels = binary_img.load()

    dot1 = pixels[start_x, start_y] if start_x < width and start_y < height else 0
    dot4 = (
        pixels[start_x + 1, start_y] if start_x + 1 < width and start_y < height else 0
    )

    dot2 = (
        pixels[start_x, start_y + 1] if start_x < width and start_y + 1 < height else 0
    )
    dot5 = (
        pixels[start_x + 1, start_y + 1]
        if start_x + 1 < width and start_y + 1 < height
        else 0
    )

    dot3 = (
        pixels[start_x, start_y + 2] if start_x < width and start_y + 2 < height else 0
    )
    dot6 = (
        pixels[start_x + 1, start_y + 2]
        if start_x + 1 < width and start_y + 2 < height
        else 0
    )

    block = []

    if dot1 == 1:
        block.append(1)
    else:
        block.append(0)

    if dot2 == 1:
        block.append(1)
    else:
        block.append(0)

    if dot3 == 1:
        block.append(1)
    else:
        block.append(0)

    if dot4 == 1:
        block.append(1)
    else:
        block.append(0)

    if dot5 == 1:
        block.append(1)
    else:
        block.append(0)

    if dot6 == 1:
        block.append(1)
    else:
        block.append(0)

    return block


def block_to_value(block):
    value = 0

    for i in range(6):
        if block[i] == 1:
            value = value | (1 << i)

    return value


def binary_image_to_braille_blocks(binary_img):
    width, height = binary_img.size
    rows = []

    for y in range(0, height, 3):
        current_row = []

        for x in range(0, width, 2):
            block = get_block_pixels(binary_img, x, y)
            current_row.append(block)

        rows.append(current_row)

    return rows


def braille_blocks_to_values(block_rows):
    rows = []

    for block_row in block_rows:
        current_row = []

        for block in block_row:
            value = block_to_value(block)
            current_row.append(value)

        rows.append(current_row)

    return rows


def flatten_rows(rows):
    flat = []

    for row in rows:
        for value in row:
            flat.append(value)

    return flat


def serialize_for_pico(rows):
    parts = []

    for row in rows:
        row_text = []
        for value in row:
            row_text.append(str(value))
        parts.append(",".join(row_text))

    return ";".join(parts)


def print_binary_image(binary_img):
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


def print_matrix(matrix):
    for row in matrix:
        print(row)


def print_braille_rows(rows):
    for row in rows:
        print(row)


def process_image(
    image_path,
    target_width=DEFAULT_TARGET_WIDTH,
    target_height=DEFAULT_TARGET_HEIGHT,
    threshold=DEFAULT_THRESHOLD,
):
    img = load_image(image_path)
    resized_img = resize_image(img, target_width, target_height)
    binary_img = binarize_image(resized_img, threshold)

    binary_matrix = binary_image_to_matrix(binary_img)
    flat_values = flatten_matrix(binary_matrix)
    pico_data = serialize_matrix_for_pico(binary_matrix)
    braille_blocks = binary_image_to_braille_blocks(binary_img)
    braille_encoded_values = braille_blocks_to_values(braille_blocks)
    braille_flat_values = flatten_rows(braille_encoded_values)
    braille_pico_data = serialize_for_pico(braille_encoded_values)

    result = {
        "image_path": image_path,
        "target_width": target_width,
        "target_height": target_height,
        "threshold": threshold,
        "rows": binary_matrix,
        "flat_values": flat_values,
        "pico_data": pico_data,
        "binary_image": binary_img,
        "binary_matrix": binary_matrix,
        "braille_blocks": braille_blocks,
        "braille_encoded_values": braille_encoded_values,
        "braille_flat_values": braille_flat_values,
        "braille_pico_data": braille_pico_data,
    }
    return result


def send_to_pico_placeholder(pico_data):
    print("Pico send placeholder:")
    print(pico_data)


def process_image_for_flask(file_path, threshold=DEFAULT_THRESHOLD):
    result = process_image(
        image_path=file_path,
        target_width=DEFAULT_TARGET_WIDTH,
        target_height=DEFAULT_TARGET_HEIGHT,
        threshold=threshold,
    )

    response = {
        "rows": result["rows"],
        "flat_values": result["flat_values"],
        "pico_data": result["pico_data"],
        "target_width": result["target_width"],
        "target_height": result["target_height"],
        "threshold": result["threshold"],
        "binary_matrix": result["binary_matrix"],
        "braille_blocks": result["braille_blocks"],
        "braille_encoded_values": result["braille_encoded_values"],
        "braille_flat_values": result["braille_flat_values"],
        "braille_pico_data": result["braille_pico_data"],
    }
    return response


def main():
    image_path = "test_images/vertical_line_6x3.png"

    result = process_image(
        image_path=image_path,
        target_width=DEFAULT_TARGET_WIDTH,
        target_height=DEFAULT_TARGET_HEIGHT,
        threshold=DEFAULT_THRESHOLD,
    )

    print("Processed image:", result["image_path"])
    print(
        "Target size:", str(result["target_width"]) + "x" + str(result["target_height"])
    )
    print("Threshold:", result["threshold"])
    print()

    print("Binary image:")
    print_binary_image(result["binary_image"])
    print()

    print("Binary matrix:")
    print_matrix(result["binary_matrix"])
    print()

    print("Flat 0/1 values:")
    print(result["flat_values"])
    print()

    print("Serialized 0/1 pico data:")
    print(result["pico_data"])
    print()

    print("Braille blocks:")
    print(result["braille_blocks"])
    print()

    print("Braille encoded values:")
    print_braille_rows(result["braille_encoded_values"])
    print()

    print("Braille serialized pico data:")
    print(result["braille_pico_data"])
    print()

    send_to_pico_placeholder(result["pico_data"])


if __name__ == "__main__":
    main()
