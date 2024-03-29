import json
from datetime import date, datetime
import numpy as np
import os



def create_segmentation_label_files(images_paths, images_polygons, images_sizes, images_objects_categories_indices,
                                  output_dir):
    """
    Description: one *.txt file per image,  one row per object, row format: class polygon vertices (x0, y0.....xn,yn)
    normalized coordinates [0 to 1].
    zero-indexed class numbers - start from 0


    :param images_paths: list of dataset image filenames
    :param images_polygons: list of per image polygons arrays
    :param images_objects_categories_indices:  list of per image categories_indices arrays
    :param output_dir: output dir of labels text files
    :return:
    """
    print(f'create_segmentation_label_files. output_dir: {output_dir}')
    # create out dirs if needed - tbd never needed...
    try:
        os.makedirs(output_dir)
    except FileExistsError:
        # catch if directory already exists
        pass
    ## create label files
    for image_polygons, image_path, images_size, categories_indices in zip(images_polygons, images_paths, images_sizes,
                                                              images_objects_categories_indices):
        im_height = images_size[0]
        im_width = images_size[1]
        # related label file has same name with .txt ext - split filename, replace ext to txt:
        head, filename = os.path.split(image_path)
        labels_filename = f"{output_dir}/{filename.rsplit('.', 1)[0]}.txt"
        print(f'labels_filename: {labels_filename}')

        # normalize sizes:
        image_polygons=[image_polygon/np.array(images_size) for image_polygon in image_polygons]
        with open(labels_filename, 'w') as f:
            for image_polygon, category_id in zip(image_polygons, categories_indices):
                entry = f"{category_id} {' '.join(str(vertix) for vertix in list(image_polygon.reshape(-1)))}\n"
                f.write(entry) # fill label file with entries


def create_detection_labels_unified_file(images_paths, images_bboxes, images_objects_categories_indices,
                                labels_file_path):
    """
    :param images_paths: list of dataset image filenames
    :param images_bboxes: list of per image bboxes arrays in xyxy format.
    :param images_objects_categories_indices:  list of per image categories_indices arrays
    :param labels_file_path: path of output labels text files
    :return:
    """
    print('create_detection_labels_unified_file')

    entries = []
    for image_path, categories_indices, bboxes in zip(images_paths, images_objects_categories_indices, images_bboxes):

        entry = f'{image_path} '
        for bbox, category_id in zip(bboxes, categories_indices):
            bbox_arr = np.array(bbox, dtype=float)
            xyxy_bbox = [bbox_arr[0], bbox_arr[1], bbox_arr[0] + bbox_arr[2], bbox_arr[1] + bbox_arr[3]]
            for vertex in xyxy_bbox:
                entry = f'{entry}{vertex},'
            entry = f'{entry}{float(category_id)} '
        entries.append(entry)
        file = open(labels_file_path, 'w')
        for item in entries:
            file.write(item + "\n")
    file.close()


def create_detection_lable_files(images_paths, images_bboxes, images_sizes, images_objects_categories_indices,

                                  output_dir):
    """
    Description: one *.txt file per image,  one row per object, row format: class x_center y_center width height.
    normalized coordinates [0 to 1].
    zero-indexed class numbers - start from 0

    :param images_paths: list of dataset image filenames
    :param images_bboxes: list of per image bboxes arrays in xyxy format.
    :param images_sizes:
    :param images_objects_categories_indices:  list of per image categories_indices arrays
    :param output_dir: output dir of labels text files
    :return:
    """
    print(f'create_per_image_labels_files. labels_output_dir: {output_dir}')
    try:
        os.makedirs(output_dir)
    except FileExistsError:
        # catch exception - directory already exists
        pass
    for bboxes, image_path, images_size, categories_indices in zip(images_bboxes, images_paths, images_sizes,
                                                              images_objects_categories_indices):
        im_height = images_size[0]
        im_width = images_size[1]

        head, filename = os.path.split(image_path)
        labels_filename = f"{output_dir}/{filename.rsplit('.', 1)[0]}.txt"
        with open(labels_filename, 'w') as f:
            for bbox, category_id in zip(bboxes, categories_indices):
                bbox_arr = np.array(bbox, dtype=float)
                # [xmin, ymin, w,h] to [x_c, y_c, w, h]
                xywh_bbox = [(bbox_arr[0] + bbox_arr[2] / 2) , (bbox_arr[1] + bbox_arr[3] / 2) ,
                               bbox_arr[2], bbox_arr[3] ]
                # normalize size:
                xywh_bbox = [xywh_bbox[0] / im_width,xywh_bbox[1] / im_height,
                               xywh_bbox[2] / im_width, xywh_bbox[3] / im_height]
                entry = f"{category_id} {' '.join(str(e) for e in xywh_bbox)}\n"
                f.write(entry)




# Create a coco like format label file. format:
# a single json file with 4 tables:
#     "info":
#     "licenses":
#     "images": images_records,
#     "categories": categories_records,
#     "annotations": annotatons_records
def create_coco_json_lable_files(images_paths, images_sizes, images_bboxes, images_objects_categories_indices,
                   category_names,  category_ids, annotations_output_path):
    """
     :param images_paths: list of dataset image filenames
    :param images_sizes: list of per image [im.height, im.width] tuples
    :param images_bboxes: list of per image bboxes arrays in xyxy format.
    :param images_objects_categories_indices: list of per image categories_indices arrays
    :param category_names: list of all dataset's category names
    :param category_ids:  list of all dataset's category ids

    :param annotations_output_path: path for output file storage
    :return:
    """

    print('create_coco_labels_file')

    anno_id = 0
    # for example_id in range(nex):
    added_category_names = []
    categories_records = []
    # map_categories_id = {}

    # fill category
    for category_name, category_id in zip(category_names, category_ids):

        if category_name not in added_category_names:
            categories_records.append({
                "supercategory": category_names,
                "id": category_id,
                "name": category_name,
            })
            added_category_names.append(category_name)

    images_records = []
    annotatons_records = []
    for example_id, (image_path, image_size, bboxes, objects_categories_indices) in enumerate(
            zip(images_paths, images_sizes, images_bboxes, images_objects_categories_indices)):

        # images records:

        images_records.append({
            "license": '',
            "file_name": image_path,
            "coco_url": "",
            'width': image_size[1],
            'height': image_size[0],
            "date_captured": str(datetime.now()),
            "flickr_url": "",
            "id": example_id
        })

        # annotatons_records
        for bbox, category_id in zip(bboxes, objects_categories_indices):
            annotatons_records.append({
                "segmentation": [],
                "area": [],
                "iscrowd": 0,
                "image_id": example_id,
                "bbox": list(bbox),
                "category_id": category_id,
                "id": anno_id
            }
            )
            anno_id += 1
    date_today = date.today()
    info = {
        "description": " Dataset",
        "url": '',
        # "version": config.get('version', 1.0),
        "year": date_today.year,
        "contributor": '',
        "date_created": str(date_today),
        "licenses": '',
        "categories": categories_records
    }
    output_records = {
        "info": info,
        "licenses": [],
        "images": images_records,
        "categories": categories_records,
        "annotations": annotatons_records
    }
    print(f'Save annotation  in {annotations_output_path}')
    with open(annotations_output_path, 'w') as fp:
        json.dump(output_records, fp)
