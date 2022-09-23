#! /usr/bin/env python
# coding=utf-8
# ================================================================
#   Copyright (C) 2022 . All rights reserved.
#
#   File name   : create_shapes_dataset.py
#   Author      : ronen halevy
#   Created date:  4/16/22
#   Description :
#
# ================================================================

import numpy as np
from PIL import Image, ImageDraw
import math
import yaml
import os
import json
from datetime import date, datetime
import random


def compute_iou(box1, box2):
    """x_min, y_min, x_max, y_max"""
    area_box_1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area_box_2 = (box2[2] - box2[0]) * (box2[3] - box2[1])

    x_min = max(box1[0], box2[0])
    y_min = max(box1[1], box2[1])
    x_max = min(box1[2], box2[2])
    y_max = min(box1[3], box2[3])

    if y_min >= y_max or x_min >= x_max:
        return 0
    return ((x_max - x_min) * (y_max - y_min)) / (area_box_2 + area_box_1)


def create_bbox(image_size, bboxes, shape_width_choices, axis_ratio, iou_thresh, margin_from_edge,
                size_fluctuation=0.01):
    """
                
    :param image_size: Canvas size
    :type image_size: 
    :param bboxes: 
    :type bboxes: 
    :param shape_width_choices: 
    :type shape_width_choices: 
    :param axis_ratio: 
    :type axis_ratio: 
    :param iou_thresh: 
    :type iou_thresh: 
    :param margin_from_edge: 
    :type margin_from_edge: 
    :param size_fluctuation: 
    :type size_fluctuation: 
    :return: 
    :rtype: 
    """
    max_count = 10000
    count = 0
    # Iterative loop to find location for shape placement i.e. center. Max iou with prev boxes should be g.t. iou_thresh
    while True:
        shape_width = np.random.choice(shape_width_choices)
        shape_height = shape_width * axis_ratio * random.uniform(1 - size_fluctuation, 1)
        # add fluctuations - config defuned
        shape_width = shape_width * random.uniform(1 - size_fluctuation, 1)
        radius = np.array([shape_width / 2, shape_height / 2])
        center = np.random.randint(
            low=radius + margin_from_edge, high=np.floor(image_size - radius - margin_from_edge), size=2)
        # bbox_sides = radius
        new_bbox = np.concatenate(np.tile(center, 2).reshape(2, 2) +
                                  np.array([np.negative(radius), radius]))
        # iou new shape bbox with all prev bboxes. skip shape if max iou > thresh - try another placement for shpe
        iou = list(map(lambda x: compute_iou(new_bbox, x), bboxes))

        if len(iou) == 0 or max(iou) <= iou_thresh:
            break
        if count > max_count:
            max_iou = max(iou)
            raise Exception(
                f'Shape Objects Placement Failed after {count} placement itterations: max(iou)={max_iou}, '
                f'but required iou_thresh is {iou_thresh} shape_width: {shape_width},'
                f' shape_height: {shape_height}. . \nHint: reduce objects size or quantity of objects in an image')
        count += 1

    return new_bbox


def draw_shape(draw, shape, bbox, fill_color, outline_color):
    if shape in ['ellipse', 'circle']:
        x_min, y_min, x_max, y_max = bbox.tolist()
        draw.ellipse([x_min, y_min, x_max, y_max], fill=fill_color, outline=outline_color, width=3)

    elif shape in ['rectangle', 'square']:
        x_min, y_min, x_max, y_max = bbox.tolist()
        draw.rectangle((x_min, y_min, x_max, y_max), fill=fill_color, outline=outline_color, width=3)

    elif shape == 'triangle':
        x_min, y_min, x_max, y_max = bbox.tolist()
        vertices = [x_min, y_max, x_max, y_max, (x_min + x_max) / 2, y_min]
        draw.polygon(vertices, fill=fill_color, outline=outline_color)

    elif shape == 'triangle':
        x_min, y_min, x_max, y_max = bbox.tolist()
        vertices = [x_min, y_max, x_max, y_max, (x_min + x_max) / 2, y_min]
        draw.polygon(vertices, fill=fill_color, outline=outline_color)

    elif shape in ['trapezoid''hexagon']:
        sides = 5 if shape == 'trapezoid' else 6
        x_min, y_min, x_max, y_max = bbox.tolist()
        center_x, center_y = (x_min + x_max) / 2, (y_min + y_max) / 2
        rad_x, rad_y = (x_max - x_min) / 2, (y_max - y_min) / 2
        xy = [
            (math.cos(th) * rad_x + center_x,
             math.sin(th) * rad_y + center_y)
            for th in [i * (2 * math.pi) / sides for i in range(sides)]
        ]
        draw.polygon(xy, fill=fill_color, outline=outline_color)


def make_image(shapes, image_size, min_objects_in_image, max_objects_in_image, bg_color, iou_thresh, margin_from_edge,
               bbox_margin,
               size_fluctuation

               ):
    image = Image.new('RGB', image_size, bg_color)
    draw = ImageDraw.Draw(image)
    num_of_objects = np.random.randint(min_objects_in_image, max_objects_in_image + 1)
    bboxes = []
    objects_categories_names = []
    for index in range(num_of_objects):

        shape_entry = np.random.choice(shapes)
        try:
            axis_ratio = shape_entry['shape_aspect_ratio']
        except Exception as e:
            print(e)
            pass
        shape_width_choices = shape_entry['shape_width_choices'] if 'shape_width_choices' in shape_entry else 1
        try:
            bbox = create_bbox(image_size, bboxes, shape_width_choices, axis_ratio, iou_thresh, margin_from_edge,
                               size_fluctuation)
        except Exception as e:
            msg = str(e)
            raise Exception(
                f'Failed in placing the {index} object into image:\n{msg}.\nHere is the failed-to-be-placed shape entry: {shape_entry}')

        if len(bbox):
            bboxes.append(bbox.tolist())
        else:
            break
        objects_categories_names.append(shape_entry['category_name'])

        fill_color = tuple(shape_entry['fill_color'])
        outline_color = tuple(shape_entry['outline_color'])
        draw_shape(draw, shape_entry['shape'], bbox, fill_color, outline_color)

    bboxes = np.array(bboxes)
    # transfer bbox coordinate to:  [xmin, ymin, w, h]: (bbox_margin is added distance between shape and bbox)
    bboxes = [bboxes[:, 0] - bbox_margin,
              bboxes[:, 1] - bbox_margin,
              bboxes[:, 2] - bboxes[:, 0] + 2 * bbox_margin,
              bboxes[:, 3] - bboxes[:, 1] + 2 * bbox_margin]  # / np.tile(image_size,2)

    bboxes = np.stack(bboxes, axis=1)  # / np.tile(image_size, 2)

    return image, bboxes, objects_categories_names


def fill_categories_records(shapes):
    categories_records = []
    added_category_names = []
    map_categories_id = {}
    id = 0
    for shape in shapes:
        category_name = shape['category_name']
        if category_name not in added_category_names:
            categories_records.append({
                "supercategory": shape['super_category'],
                "id": id,
                "name": category_name,
            })
            added_category_names.append(category_name)

            map_categories_id.update({category_name: id})
            id += 1

    return categories_records, map_categories_id


def create_dataset(config_file, shapes_file):
    """
    :param config_file: Configuration file. Holds common configs, e.g. image size, num of object in image
    :type config_file: yaml
    :param shapes_file: Configuration file. Defines characteristics of shapes objects included - se.g. type, ize, color
    :type shapes_file: yaml
    :return:  Creates 3 output files: 1. An annotation json file, in the format of coco dataset. Data is arranged a a dict object with 5 elements:
        info, licenses, images, categories, annotations 2. class_names_file, which holds the class names table.
        This table is used by inference for category id decoding. 3. Images files.
    :rtype:
    """
    with open(shapes_file, 'r') as stream:
        shapes = yaml.safe_load(stream)

    with open(config_file, 'r') as stream:
        config = yaml.safe_load(stream)

    splits = config["splits"]
    output_dir = config["output_dir"]
    class_names_out_file = f'{output_dir}/{config["class_names_file"]}'

    categories_records, map_categories_id = fill_categories_records(shapes)

    with open(class_names_out_file, 'w') as f:
        for category in categories_records:
            f.write("%s\n" % category['name'])

    date_today = date.today()
    info = {
        "description": "Shapes Dataset",
        "url": '',
        "version": config.get('version', 1.0),
        "year": date_today.year,
        "contributor": config.get('contributor'),
        "date_created": str(date_today),
        "licenses": config.get('licenses', []),
        "categories": categories_records
    }
    from pathlib import Path

    anno_id = 0
    for split in splits:
        images_records = []
        annotatons_records = []

        split_output_dir = Path(f'{output_dir}/{split}')
        split_output_dir.mkdir(parents=True, exist_ok=True)
        print(f'Creating {split} split in {output_dir}/{split}: {int(splits[split])} examples.\n Running....')

        annotations_path = f'{output_dir}/{split}/annotations.json'
        for example_id in range(int(splits[split])):
            try:
                image, bboxes, objects_categories_names = make_image(shapes, config['image_size'],
                                                                     config['min_objects_in_image'],
                                                                     config['max_objects_in_image'],
                                                                     tuple(config['bg_color']),
                                                                     config['iou_thresh'],
                                                                     config['margin_from_edge'],
                                                                     config['bbox_margin'],
                                                                     config['size_fluctuation'],
                                                                     )
            except Exception as e:
                msg = str(e)
                raise Exception(f'Error: While creating the {example_id}th image: {msg}')
            image_filename = f'img_{example_id + 1:06d}.jpg'
            file_path = f'{output_dir}/{split}/{image_filename}'
            image.save(file_path)

            if len(bboxes) == 0:
                continue

            images_records.append({
                "license": '',
                "file_name": image_filename,
                "coco_url": "",
                'width': image.height,
                'height': image.height,
                "date_captured": str(datetime.now()),
                "flickr_url": "",
                "id": example_id
            })

            for bbox, category_name in zip(bboxes, objects_categories_names):
                annotatons_records.append({
                    "segmentation": [],
                    "area": [],
                    "iscrowd": 0,
                    "image_id": example_id,
                    "bbox": list(bbox),
                    "category_id": map_categories_id[category_name],
                    "id": anno_id
                }
                )
                anno_id += 1
        output_records = {
            "info": info,
            "licenses": [],
            "images": images_records,
            "categories": categories_records,
            "annotations": annotatons_records
        }
        print(f'Save annotation  in {annotations_path}')
        with open(annotations_path, 'w') as fp:
            json.dump(output_records, fp)

    print(f'Completed!')


if __name__ == '__main__':
    config_file = 'config/config.yaml'
    shapes_file = 'config/shapes.yaml'

    try:
        create_dataset(config_file=config_file, shapes_file=shapes_file)
    except Exception as e:
        print(e)
        exit(1)
