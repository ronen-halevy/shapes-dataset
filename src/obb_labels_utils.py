import numpy as np
import math
from shapely.geometry import Polygon

def xywh2xyxy(obboxes):
    """
    Trans rbox format to poly format.
    Args:
        rboxes (array/tensor): (num_gts, [cx cy l s θ]) θ∈[-pi/2, pi/2)

    Returns:
        polys (array/tensor): (num_gts, [x1 y1 x2 y2 x3 y3 x4 y4])
    """

    cls,  center, w, h = np.split(obboxes, (1, 3, 4), axis=-1)

    point1 = center + np.concatenate([-w/2,-h/2], axis=1)
    point2 = center + np.concatenate([w/2,-h/2], axis=1)
    point3 = center + np.concatenate([w/2,h/2], axis=1)
    point4 = center + np.concatenate([-w/2,h/2], axis=1)

    # order = obboxes.shape[:-1]
    return np.concatenate(
            [point1, point2, point3, point4], axis=-1)

def rotate(hbboxes, theta0):
    rot_angle = np.array(theta0) / 180 * math.pi  # rot_tick*np.random.randint(0, 8)

    rotate_bbox = lambda xy: np.concatenate([np.sum(xy * np.concatenate([np.cos(rot_angle)[...,None, None], np.sin(rot_angle)[...,None, None]], axis=-1), axis=-1,keepdims=True),
                              np.sum(xy * np.concatenate([-np.sin(rot_angle)[...,None, None], np.cos(rot_angle)[...,None, None]], axis=-1), axis=-1,keepdims=True)], axis=-1)
    offset_xy = (np.max(hbboxes, axis=-2, keepdims=True) + np.min(hbboxes,axis=-2, keepdims=True)) / 2
    hbboxes_ = hbboxes - offset_xy # remove offset b4 rotation
    rbboxes =  rotate_bbox(hbboxes_)
    rbboxes=rbboxes+offset_xy # add offset back
    return rbboxes


def create_obb_entries(bbox_entries):
    """

    :param bbox_entries:
    :type bbox_entries:
    :return:
    :rtype:
    """
    bboxes = []
    for idx, bbox_entry in enumerate(bbox_entries):  # loop on images
        bbox_entries = [[float(idx) for idx in entry.split(' ')] for entry in bbox_entry] #  string rbbox entries to float
        bbox_entries = np.array(bbox_entries)
        bbox_entries = xywh2xyxy(bbox_entries)
        bboxes.append(bbox_entries)
    return bboxes


def arrange_obb_entries(images_polygons, images_size, categories_lists):
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


def calc_iou(polygon1, polygons):
    """
    Calc iou between polygon1 and polygons - a list of polygons
    :param polygon: polygon vertices, np.array, shape: [nvertices,2]
    :param polygons: a list of np,array polygons of shape [nvertices,2]
    :return: a list, iou of polygon1 and polygons
    """
    polygon1 = Polygon(polygon1)
    iou=[]
    for polygon2 in polygons:
        polygon2 = Polygon(polygon2)
        intersect = polygon1.intersection(polygon2).area
        union = polygon1.union(polygon2).area
        iou.append(intersect / union)
    return np.array(iou)


def remove_dropped_bboxes(batch_bbox_entries, dropped_ids):
    batch_bbox_entries_modified = []
    for img_idx, img_bbox_entry in enumerate(batch_bbox_entries,):  # loop on images
        bbox_del_ids = [did[1] for did in dropped_ids if did[0] == img_idx]
        img_bbox_entries = np.delete(np.array(img_bbox_entry), bbox_del_ids, axis=0)#.tolist()
        batch_bbox_entries_modified.append(img_bbox_entries)
    return batch_bbox_entries_modified

def remove_dropped_polygons(batch_polygons, dropped_ids):
    batch_polygons_modified = []
    for img_idx, img_polygons in enumerate(batch_polygons):  # loop on images
        img_polygons_modified=[]
        for poly_idx, polygon in enumerate(img_polygons ):  # loop on images
            if [img_idx, poly_idx] not in dropped_ids:
                img_polygons_modified.append(polygon)
        batch_polygons_modified.append(img_polygons_modified)
    return batch_polygons_modified

def rotate_polygon_entries(batch_polygons, images_sizes, batch_thetas, iou_thresh=0):
    """
    Rotate polygons by theta.
    If a rotated polygon crosses image boundaries, keep unrotated polygon.
    If iou between a rotated polygon and any polygon in list crosses iou_thresh, then leave unrotated (set theta to 0)
    If iou of unrotated polygon and any polygon in list still crosses iou_thresh, then drop polygon.
    :param batch_polygons: batches polygons list. list size: [bimgs, npolygons], np.array polygons shape: [nvertices,2]
    :param images_size: tuple, [img_w, img_h], used for rotated polygon boundary check
    :param theta: polygons rotation angle in degrees.
    :param iou_thresh: max permitted iou between any image's pair of polygons
    :return:
       batches rpolygons: rotated polygons list. size: [bimgs, npolygons], entry: np.array polygons shape: [nvertices,2]
       batch_result_thetas: actual thetas list. size: [bimgs, npolygons], entry: float/int
       dropped_ids: dropped polygons, (due to iou above thresh). ids list. size: [bimgs, npolygons], entry: int
    :rtype:
    """
    batch_rpolygons = []
    batch_result_thetas = []
    dropped_ids=[]
    # loop on batch images:
    for im_idx, (image_polygons, image_size, thetas) in enumerate(zip(batch_polygons, images_sizes, batch_thetas)):
        rpolygons=[]
        res_thetas=[]
        for idx, (polygon, theta) in enumerate(zip(image_polygons, thetas)): # loop on image's polygons
            unrotate = False # reset unrotate fkag
            rpolygon = rotate(polygon, theta)
            # check if rotated shape is inside image bounderies, otherwise leave unrotated:
            if np.any(rpolygon > image_size) or np.any(rpolygon < 0):
                rpolygon=polygon # replace rotated by original unrotated
                unrotate = True
                print(f'\n Rotated shape is outsode image  boundaries. Keep unrotate. img id: {im_idx} shape id: {idx}')
            # if of rotated with already rotated list: if above thresh, keep unrotated or drop if iou above thresh:
            if np.any(calc_iou(rpolygon, rpolygons) > iou_thresh):
                if np.any(calc_iou(polygon, rpolygons) > iou_thresh):# iou for unrotated: either drop or keep unrotated
                    dropped_ids.append([im_idx, idx])
                    print(f'IOU with rotated images exceeds treshs: Droppng  img_id: {im_idx} shape_id: {idx}')
                    continue
                else:
                    print(f'IOU of unrotated passed. Keep unrotated shape. img_id {im_idx} shape_id: {idx}')
                    unrotate = True
                    rpolygon=polygon

            rpolygons.append(rpolygon)
            if unrotate:
                res_thetas.append(0)
            else:
                print(f'Rotate shape by {theta} degrees. img_id: {im_idx} shape_id: {idx} ')
                res_thetas.append(theta)

        batch_result_thetas.append(res_thetas)
        batch_rpolygons.append(rpolygons)
    print(f'Batch rotations angles: {batch_result_thetas}')
    return batch_rpolygons, batch_result_thetas, dropped_ids


def rotate_obb_bbox_entries(bbox_entries, images_size, obb_thetas):
    batch_rbboxes = []
    batch_dropped_ids=[]
    for im_idx, (hbboxes, image_size, theta) in enumerate(zip(bbox_entries, images_size, obb_thetas)):
        dropped_ids = []
        rbboxes = rotate(hbboxes.reshape([-1, 4, 2]), theta).reshape(-1, 8)
        for bbox_id, rbbox in enumerate(rbboxes):

            if np.any(rbbox > image_size[0]) or np.any(rbbox < 0):
                batch_dropped_ids.append([im_idx, bbox_id])
            else:
                batch_rbboxes.append(rbboxes)
    return batch_rbboxes, batch_dropped_ids


def append_category_field(batch_rbboxes, batch_objects_categories_names):
    """
    append category name at the end of each entry (as in dota format for obb)

    :param batch_rbboxes: list size: [batch][nti][entry string] where an entry string holds 8 bbox normed coordinates.
    :param batch_objects_categories_names: list of objects' names. list size: [batch][nti], string
    :return: batch_rbboxes_update, each entry apendedd with a category name.  list size: [batch][nti][entry string]
    """
    batch_rbboxes_update = []
    for img_rbboxes, img_objects_categories_names in zip(batch_rbboxes, batch_objects_categories_names):
        img_rbboxes_update = []
        for rbbox, img_object_category_name in zip(img_rbboxes, img_objects_categories_names):
            entry=rbbox.tolist()
            entry.append(img_object_category_name)
            img_rbboxes_update.append(entry)
        batch_rbboxes_update.append(img_rbboxes_update)
    return batch_rbboxes_update