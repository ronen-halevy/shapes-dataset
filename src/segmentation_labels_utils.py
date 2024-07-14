import numpy as np
def arrange_segmentation_entries(images_polygons, images_size, categories_lists):
    batch_entries = []
    for image_polygons, image_size, class_ids in zip(images_polygons, images_size,
                                                     categories_lists):
        # normalize sizes:
        image_polygons = [image_polygon / np.array(image_size) for image_polygon in image_polygons]

        image_entries = [
            f"{category_id} {' '.join(str(vertix) for vertix in list(image_polygon.reshape(-1)))}\n" for
            image_polygon, category_id in zip(image_polygons, class_ids)]
        batch_entries.append(image_entries)
    return batch_entries