from PIL import Image, ImageFilter, ImageOps

DEFAULT_TARGET_WIDTH = 16
DEFAULT_TARGET_HEIGHT = 16
DEFAULT_THRESHOLD = 128


def _resample_nearest():
    if hasattr(Image, "Resampling"):
        return Image.Resampling.NEAREST
    return Image.NEAREST


def _resample_lanczos():
    if hasattr(Image, "Resampling"):
        return Image.Resampling.LANCZOS
    return Image.LANCZOS


def load_image(image_path):
    img = Image.open(image_path).convert("RGBA")

    white_background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white_background.paste(img, mask=img.getchannel("A"))

    return white_background.convert("L")


def resize_image(
    img, target_width=DEFAULT_TARGET_WIDTH, target_height=DEFAULT_TARGET_HEIGHT
):
    resized_img = img.resize((target_width, target_height), _resample_lanczos())
    return resized_img


def detect_dark_foreground(img):
    width, height = img.size
    pixels = img.load()
    border_values = []

    for x in range(width):
        border_values.append(pixels[x, 0])
        border_values.append(pixels[x, height - 1])

    for y in range(height):
        border_values.append(pixels[0, y])
        border_values.append(pixels[width - 1, y])

    border_values.sort()
    background_value = border_values[len(border_values) // 2]

    return background_value >= 128


def create_foreground_mask(img, threshold=DEFAULT_THRESHOLD):
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.MedianFilter(3))

    width, height = img.size
    pixels = img.load()
    mask = Image.new("L", (width, height), 0)
    mask_pixels = mask.load()

    dark_foreground = True

    for y in range(height):
        for x in range(width):
            gray_value = pixels[x, y]

            if dark_foreground:
                if gray_value <= threshold:
                    mask_pixels[x, y] = 255
                else:
                    mask_pixels[x, y] = 0
            else:
                if gray_value >= threshold:
                    mask_pixels[x, y] = 255
                else:
                    mask_pixels[x, y] = 0

    return mask


def crop_foreground(mask, padding=2):
    bbox = mask.getbbox()

    if bbox is None:
        return mask

    left, top, right, bottom = bbox
    width, height = mask.size

    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(width, right + padding)
    bottom = min(height, bottom + padding)

    return mask.crop((left, top, right, bottom))


def thicken_foreground(mask):
    return mask.filter(ImageFilter.MaxFilter(3))


def finalize_binary_image(mask, threshold=DEFAULT_THRESHOLD):
    width, height = mask.size
    pixels = mask.load()
    binary_img = Image.new("L", (width, height), 0)
    binary_pixels = binary_img.load()

    for y in range(height):
        for x in range(width):
            if pixels[x, y] >= threshold:
                binary_pixels[x, y] = 1
            else:
                binary_pixels[x, y] = 0

    return binary_img


def binarize_image(img, threshold=DEFAULT_THRESHOLD):
    mask = create_foreground_mask(img, threshold)
    return finalize_binary_image(mask, threshold)


def remove_isolated_pixels(matrix):
    height = len(matrix)

    if height == 0:
        return matrix

    width = len(matrix[0])
    cleaned = []

    for y in range(height):
        row = []

        for x in range(width):
            value = matrix[y][x]

            if value == 0:
                row.append(0)
                continue

            count = 0

            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue

                    ny = y + dy
                    nx = x + dx

                    if 0 <= ny < height and 0 <= nx < width:
                        if matrix[ny][nx] == 1:
                            count += 1

            if count == 0:
                row.append(0)
            else:
                row.append(1)

        cleaned.append(row)

    return cleaned


def matrix_to_binary_image(matrix):
    height = len(matrix)

    if height == 0:
        return Image.new("L", (0, 0))

    width = len(matrix[0])
    img = Image.new("L", (width, height), 0)
    pixels = img.load()

    for y in range(height):
        for x in range(width):
            if matrix[y][x] == 1:
                pixels[x, y] = 1
            else:
                pixels[x, y] = 0

    return img


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
    dot4 = pixels[start_x + 1, start_y] if start_x + 1 < width and start_y < height else 0
    dot2 = pixels[start_x, start_y + 1] if start_x < width and start_y + 1 < height else 0
    dot5 = pixels[start_x + 1, start_y + 1] if start_x + 1 < width and start_y + 1 < height else 0
    dot3 = pixels[start_x, start_y + 2] if start_x < width and start_y + 2 < height else 0
    dot6 = pixels[start_x + 1, start_y + 2] if start_x + 1 < width and start_y + 2 < height else 0

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
    mask = create_foreground_mask(img, threshold)

    bbox = mask.getbbox()
    if bbox is not None:
        content = mask.crop(bbox)
    else:
        content = mask

    content_width, content_height = content.size

    scale = min(
        target_width / content_width,
        target_height / content_height,
        1
    )

    new_width = max(1, int(content_width * scale))
    new_height = max(1, int(content_height * scale))

    resized_content = content.resize((new_width, new_height), _resample_nearest())

    canvas = Image.new("L", (target_width, target_height), 0)

    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2

    canvas.paste(resized_content, (paste_x, paste_y))

    binary_img = finalize_binary_image(canvas, threshold)

    binary_matrix = binary_image_to_matrix(binary_img)
    binary_matrix = remove_isolated_pixels(binary_matrix)
    binary_img = matrix_to_binary_image(binary_matrix)

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
    print("Target size:", str(result["target_width"]) + "x" + str(result["target_height"]))
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