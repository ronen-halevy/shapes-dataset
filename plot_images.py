import numpy as np
from matplotlib import pyplot as plt
from PIL import ImageFont
from PIL import Image, ImageDraw
import json


def draw_text_on_bounding_box(image, ymin, xmin, color, display_str_list=(), font_size=30):
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf", font_size)
    except IOError:
        print("Font not found, using default font.")
        font = ImageFont.load_default()

    text_heights = [font.getsize(string)[1] for string in display_str_list]
    text_margin_factor = 0.05
    total_text_height = (1 + 2 * text_margin_factor) * sum(text_heights)

    if ymin > total_text_height:
        text_bottom = ymin
    else:
        text_bottom = ymin + total_text_height

    # Reverse list and print from bottom to top.
    for display_str in display_str_list[::-1]:
        text_width, text_height = font.getsize(display_str)
        text_margin = np.ceil(text_margin_factor * text_height)
        draw.rectangle([(xmin, text_bottom - text_height - 2 * text_margin),
                        (xmin + text_width, text_bottom)],
                       fill=color)
        draw.text((xmin + text_margin, text_bottom - text_height - text_margin),
                  display_str,
                  fill="black",
                  font=font)
        text_bottom -= text_height - 2 * text_margin
        return image


def draw_bounding_box(image, ymin, xmin, ymax, xmax, color, thickness=3):
    draw = ImageDraw.Draw(image)
    draw.line([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin),
               (xmin, ymin)],
              width=thickness,
              fill=color)
    return image


def plot_image_with_bbox(shapes_file, config_file, plot_setup):
    with open(shapes_file) as f:
        shapes = json.load(f)['shapes']
    class_names = [shape['name'] for shape in shapes]

    with open(config_file) as f:
        config = json.load(f)
    annotations_path = config['sections']['valid']["annotations_path"]
    font_size = config['annotations_font_size']
    text_color = tuple(config['annotatons_text_color'])

    with open(annotations_path, 'r') as f:
        annotations = f.readlines()

    figsize = plot_setup['figsize']
    num_plots = plot_setup['num_plots']
    start_index = plot_setup['start_index']
    random_select = plot_setup['random_select']

    plt.figure(figsize=figsize)

    for idx in range(num_plots):
        image_index = np.random.randint(start_index, len(annotations)) if random_select else start_index + idx
        line = annotations[image_index]

        ax = plt.subplot(2, 2, idx + 1)
        columns = [item.strip() for item in line.split(' ')]
        image = Image.open(columns[0])
        bboxes = columns[1:]
        for bbox in bboxes:
            class_id = list(map(int, bbox.split(',')))[4]
            bbox = list(map(int, bbox.split(',')))[:4]
            xmin, ymin, xmax, ymax = bbox
            image = draw_bounding_box(image, ymin, xmin, ymax, xmax, color='yellow', thickness=3)

            display_text = [class_names[class_id]] if class_names else [class_id]
            draw_text_on_bounding_box(image, ymin, xmin, text_color, display_str_list=display_text,
                                      font_size=font_size)

        ax.set_title(f'image index {image_index}')
        ax.imshow(image)
        plt.show()


if __name__ == '__main__':
    shapes_file = 'shapes.json'
    config_file = 'config.json'

    plot_setup = {
        'num_plots': 5,
        'start_index': 0,
        'random_select': True,
        'figsize': (15, 15)
    }

plot_image_with_bbox(shapes_file, config_file, plot_setup)
