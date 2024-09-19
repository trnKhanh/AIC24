from math import ceil
import easyocr
import torch

from ....config import GlobalConfig
from .feature_extractor import FeatureExtractor, ImageDataset
from ....config import GlobalConfig


class TrOCR(FeatureExtractor):
    def __init__(self):
        self._reader = easyocr.Reader(["vi", "en"])

    def get_image_features(self, image_paths, batch_size, callback):
        image_features = []
        image_paths = [str(x) for x in image_paths]
        num_batches = ceil(len(image_paths) / batch_size)
        callback(0, num_batches, None)
        for i in range(num_batches):
            results = self._reader.readtext_batched(
                image_paths[i * batch_size : (i + 1) * batch_size],
                n_width=640,
                n_height=360,
            )
            for res in results:
                detected_texts = []
                for text in res:
                    detected_texts.append(text[-2])
                image_features.append(". ".join(detected_texts))
            callback(i + 1, num_batches, image_features)

        return image_features

    def get_text_features(self, texts):
        return texts

    def to(self, device):
        self._reader = easyocr.Reader(
            ["vi", "en"], gpu=(device in ["cuda", "mps"])
        )
