import os
import json
import tensorflow as tf
import numpy as np
from matplotlib import pyplot as plt


class dataset_util:
    @staticmethod
    def image_feature(value):
        """Returns a bytes_list from a string / byte."""
        return tf.train.Feature(
            bytes_list=tf.train.BytesList(value=[tf.io.encode_jpeg(value).numpy()])
        )

    @staticmethod
    def bytes_feature(value):
        """Returns a bytes_list from a string / byte."""
        return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value.encode()]))

    @staticmethod
    def bytes_feature_list(value):
        """Returns a bytes_list from a string / byte."""
        return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))

    @staticmethod
    def float_feature(value):
        """Returns a float_list from a float / double."""
        return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))

    @staticmethod
    def int64_feature(value):
        """Returns an int64_list from a bool / enum / int / uint."""
        return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

    @staticmethod
    def int64_feature_list(value):
        """Returns an int64_list from a bool / enum / int / uint."""
        return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

    @staticmethod
    def float_feature_list(value):
        """Returns a list of float_list from a float / double."""
        return tf.train.Feature(float_list=tf.train.FloatList(value=value))


class CreateTfrecordsShapes:
    @staticmethod
    def create_example(image, path, example):
        boxes = np.reshape(example['bboxes'], -1)
        shapes_id = [shape['id'] for shape in example['shapes']]

        feature = {
            "image": dataset_util.image_feature(image),
            "path": dataset_util.bytes_feature(path),
            "xmin": dataset_util.float_feature_list(boxes[0::4].tolist()),
            "ymin": dataset_util.float_feature_list(boxes[1::4].tolist()),
            "xmax": dataset_util.float_feature_list(boxes[2::4].tolist()),
            "ymax": dataset_util.float_feature_list(boxes[3::4].tolist()),
            "category_id": dataset_util.int64_feature_list(shapes_id),
        }
        return tf.train.Example(features=tf.train.Features(feature=feature))

    def create_tfrecords(self, input_annotation_file, tfrecords_out_dir):
        with open(input_annotation_file, "r") as f:
            annotations = json.load(f)["annotations"]

        print(f"Number of images: {len(annotations)}")

        num_samples = min(4096, len(annotations))
        num_tfrecords = len(annotations) // num_samples
        if len(annotations) % num_samples:
            num_tfrecords += 1  # add one record if there are any remaining samples

        if not os.path.exists(tfrecords_out_dir):
            os.makedirs(tfrecords_out_dir)  # c

        for tfrec_num in range(num_tfrecords):
            samples = annotations[(tfrec_num * num_samples): ((tfrec_num + 1) * num_samples)]

            with tf.io.TFRecordWriter(
                    tfrecords_out_dir + "/file_%.2i-%i.tfrec" % (tfrec_num, len(samples))
            ) as writer:
                for sample in samples:
                    image_path = sample['image_path']  # f"{images_dir}/{sample['image_id']:012d}.jpg"
                    image = tf.io.decode_jpeg(tf.io.read_file(image_path))
                    example = CreateTfrecordsShapes.create_example(image, image_path, sample)
                    writer.write(example.SerializeToString())

    def read_example(self, tfrecords_file_path):
        raw_dataset = tf.data.TFRecordDataset(tfrecords_file_path)
        dataset_example = raw_dataset.map(self.parse_tfrecord_fn)
        return dataset_example




if __name__ == '__main__':
    tfrecords_out_dir = "dataset/tfrecords"
    # input_images_dir = os.path.join(root_dir, "dataset/annotations/annotations.json")
    input_annotation_file = "dataset/annotations/annotations.json"
    create = CreateTfrecordsShapes()
    create.create_tfrecords(input_annotation_file, tfrecords_out_dir)
