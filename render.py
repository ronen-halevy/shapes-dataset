import yaml
import os
from pathlib import Path
from PIL import Image
import random

from src.render.render_detect import draw_detection_dataset_example, draw_detection_single_file_dataset_example, \
    draw_coco_detection_dataset_example
from src.render.render_segmentation import draw_segmentation_dataset_example
from src.render.render_kpts import draw_kpts_dataset_example
from src.render.render_obb import draw_obb_dataset_example


def increment_path(path, exist_ok=False, sep='', mkdir=False):
    # Increment file or directory path, i.e. runs/exp --> runs/exp{sep}2, runs/exp{sep}3, ... etc.
    """
    :param path:
    :type path:
    :param exist_ok:
    :type exist_ok:
    :param sep:
    :type sep:
    :param mkdir:
    :type mkdir:
    :return:
    :rtype:
    """
    path = Path(path)  # os-agnostic
    if path.exists() and not exist_ok:
        path, suffix = (path.with_suffix(''), path.suffix) if path.is_file() else (path, '')

        for n in range(2, 9999):
            p = f'{path}{sep}{n}{suffix}'  # increment path
            if not os.path.exists(p):  #
                break
        path = Path(p)

    if mkdir:
        path.mkdir(parents=True, exist_ok=True)  # make directory
    return path


def render(nexamples, labels_format_type, image_dir, labels_dir, output_dir, category_names_table, split):
    """

    :param nexamples:
    :type nexamples:
    :param labels_format_type:
    :type labels_format_type:
    :param image_dir:
    :type image_dir:
    :param labels_dir:
    :type labels_dir:
    :param output_dir:
    :type output_dir:
    :param category_names_table:
    :type category_names_table:
    :param split:
    :type split:
    :return:
    :rtype:
    """
    listdir = [filename for filename in os.listdir(image_dir) if
               filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))]

    sel_files = random.sample(listdir, k=min(nexamples, len(listdir)))

    for idx, sel_fname in enumerate(sel_files):
        image_path = f'{image_dir}/{sel_fname}'
        label_path = f'{labels_dir}/{Path(sel_fname).stem}.txt'
        if not os.path.isfile(label_path):
            print(f'Label file {label_path} not found. terminating!')
            exit(1)

        dest_dir = f'{output_dir}'
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        fname = Path(image_path)
        output_path = f'{dest_dir}/{fname.stem}_annotated{fname.suffix}'

        if labels_format_type == 'detection_coco_json_format':
            annotations_path = labels_dir
            image = draw_coco_detection_dataset_example(annotations_path, category_names_table)
        elif labels_format_type == 'detection':
            image = draw_detection_dataset_example(image_path, label_path, category_names_table)
        elif labels_format_type == 'detection_unified_textfile':
            image = draw_detection_single_file_dataset_example(image_path, label_path, category_names_table)
        elif labels_format_type == 'segmentation':
            output_path = f'{dest_dir}/{fname.stem}_annotated{fname.suffix}'
            image = draw_segmentation_dataset_example(image_path, label_path, category_names_table)
        elif labels_format_type == 'obb':
            image = draw_obb_dataset_example(image_path, label_path)
        elif labels_format_type == 'kpts':
            image = draw_kpts_dataset_example(image_path, label_path)
        else:
            print(f'Unknow labels_format_type. Terminating!!! {labels_format_type}')
            exit(1)
        print(f'saving test results to {output_path}')
        image = Image.fromarray(image)

        image.save(output_path)


if __name__ == "__main__":
    config_file = './config/dataset_config.yaml'
    with open(config_file, 'r') as stream:
        config = yaml.safe_load(stream)
    split = config['split_to_render']  # 'train'  # can be 'train', 'test', 'valid'
    labels_format_type = config['labels_format_type']
    output_dir = f'{config["output_dir"]}'.replace('{labels_format_type}', config["labels_format_type"])

    if labels_format_type in ['segmentation', 'detection', 'kpts', 'obb']:
        labels_dir = f'{output_dir}/{config["labels_dir"]}/{split}'
        images_dir = f'{output_dir}/{config["image_dir"]}/{split}'
    elif labels_format_type == 'detection_coco_json_format':
        coco_json_labels_file_path = config['coco_json_labels_file_path']
        labels_dir = coco_json_labels_file_path.replace('{split}', split)
        images_dir = None  # complete path within json file
    elif labels_format_type == 'detection_unified_textfile':
        labels_dir = config['labels_all_entries_file'].replace("{split}", split)
        images_dir = config["image_dir"].replace("{split}", split)  # an offset for image filenames located in labels
    else:
        raise ('Unknown or missing labels_format_type! configuration')
    nexamples = config['nrender_examples'] + 1
    labels_format_type = config.get('labels_format_type')

    class_names_file = config['category_names_file']

    render_output_dir = f'{config["render_output_dir"]}_{labels_format_type}'
    print('\nrendering dataset images with bbox and mask overlays\n')
    render_output_dir = increment_path(render_output_dir)

    category_names = [c.strip() for c in open(class_names_file).readlines()]
    render(nexamples, labels_format_type, images_dir, labels_dir, f'{render_output_dir}/{split}', category_names, split)
