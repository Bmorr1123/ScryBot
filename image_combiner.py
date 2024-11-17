import io, requests
from PIL import Image


def combine_images(image_urls, show=False) -> io.BytesIO | None:

    max_width = 672 * 5

    image_sizes = {}

    for url in image_urls:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            image = Image.open(io.BytesIO(r.content))
            if image.size not in image_sizes:
                image_sizes[image.size] = {"count": 1, "images": [image]}
            else:
                image_sizes[image.size]["count"] += 1
                image_sizes[image.size]["images"].append(image)

    total_width, total_height = 0, 0

    for image_size, info in image_sizes.items():
        count = info["count"]
        required_width = min(image_size[0] * count, max_width)
        images_per_row = required_width // image_size[0]
        column_count = count // images_per_row
        if column_count != count / images_per_row:  # Check if not evenly divisible
            column_count += 1

        total_width = max(total_width, required_width)
        total_height += column_count * image_size[1]
        info["total_height"] = total_height

    base_image = Image.new("RGBA", (total_width, total_height))
    current_width, current_height = 0, 0
    print(total_width, total_height)
    for image_size, info in image_sizes.items():
        total_height = info["total_height"]

        for image in info["images"]:
            print(current_width, current_height)
            base_image.paste(image, (current_width, current_height))
            current_width += image.width
            if current_width >= total_width:
                current_width = 0
                current_height += image.height

        current_width = 0
        current_height = total_height

    # base_image.save("combined.png", "PNG")
    if show:
        base_image.show("Lol")
    else:
        return_buffer = io.BytesIO()
        base_image.save(return_buffer, format="PNG")
        return_buffer.seek(0)
        return return_buffer


if __name__ == "__main__":
    urls = [
        "https://cards.scryfall.io/large/front/8/f/8fed056f-a8f5-41ec-a7d2-a80a238872d1.jpg?1682715725",
        "https://cards.scryfall.io/large/back/8/f/8fed056f-a8f5-41ec-a7d2-a80a238872d1.jpg?1682715725"
    ] * 3 + [
        "https://cards.scryfall.io/small/front/8/f/8fed056f-a8f5-41ec-a7d2-a80a238872d1.jpg?1682715725",
        "https://cards.scryfall.io/small/back/8/f/8fed056f-a8f5-41ec-a7d2-a80a238872d1.jpg?1682715725",
    ] * 10
    combine_images(urls, show=True)
