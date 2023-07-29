#! /usr/bin/env python
# coding=utf-8
# ================================================================
#   Copyright (C) 2022 . All rights reserved.
#
#   File name   : main_create_shapes_dataset.py
#   Author      : ronen halevy
#   Created date:  4/16/22
#   Description :
#   main method for  shapes dataset creation.
#   1. reads splits sizes and destination output path from config.json
#   2. Creates an instance of  ShapesDataset and generates the dataset
#   3. Envokes formatters to save dataset labels in various formats e.g. coco, multi text file (yolov5 ultralics like),
#   single text file
# ================================================================
import os

import yaml
import argparse
from pathlib import Path
from src.output_formatters.labels_text_file_formatter import create_row_text_labels_file
from src.output_formatters.labels_coco_formatter import coco_formatter
from src.output_formatters.labels_per_image_text_file_formatter import raw_text_files_labels_formatter
from src.output_formatters.segmentation_labels_formatter import segmentation_labels_formatter

from src.shapes_dataset import ShapesDataset

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", type=str, default='config/dataset_config.yaml',
                        help='yaml config file')

    args = parser.parse_args()
    config_file = args.config_file

    with open(config_file, 'r') as stream:
        config = yaml.safe_load(stream)

    output_dir = config["output_dir"]
    labels_seg_dir=config['labels_seg_dir']
    labels_det_dir=config['labels_det_dir']

    splits = config["splits"]
    shapes_dataset = ShapesDataset()

    for split in splits:
        nentries = int(splits[split])
        # create dirs for output if missing:
        images_out_dir = Path(f'{output_dir}/{split}/images')
        images_out_dir.mkdir(parents=True, exist_ok=True)

        images_filenames, images_sizes, images_bboxes, images_objects_categories_indices, category_names, category_ids, images_polygons = \
            shapes_dataset.create_dataset(
                nentries,
                f'{output_dir}/{split}')

        annotations_output_path = f'{output_dir}/{split}/images/annotations.json'
        images_filenames = [f'dataset/{split}/images/{images_filename}' for images_filename in images_filenames]

        # coco format
        coco_formatter(images_filenames, images_sizes, images_bboxes, images_objects_categories_indices,
                       category_names, category_ids,
                       annotations_output_path)

        # 2. single text file:
        create_row_text_labels_file(images_filenames, images_bboxes, images_objects_categories_indices,
                                    f'{output_dir}/{split}')

        # 3. text file per image
        labels_out_dir = Path(f'{output_dir}/{split}/{labels_det_dir}')
        labels_out_dir.mkdir(parents=True, exist_ok=True)

        raw_text_files_labels_formatter(images_filenames, images_bboxes, images_sizes,
                                        images_objects_categories_indices
                                        , labels_out_dir)
     #  4. Ultralitics like segmentation
        labels_out_dir = f'{output_dir}/{split}/{labels_seg_dir}'
        Path(labels_out_dir).mkdir(parents=True, exist_ok=True)
        segmentation_labels_formatter(images_filenames, images_polygons, images_sizes,
                                      images_objects_categories_indices,
                                      labels_out_dir)


if __name__ == '__main__':
    main()
