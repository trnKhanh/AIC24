import logging

from transformers import CLIPModel, CLIPProcessor
from torch.utils.data import Dataset, DataLoader
import torch
from PIL import Image

from ....config import GlobalConfig


class ImageDataset(Dataset):
    def __init__(self, image_paths, processor):
        self._image_paths = image_paths
        self._processor = processor

    def __len__(self):
        return len(self._image_paths)

    def __getitem__(self, index):
        path = self._image_paths[index]
        logging.getLogger("PIL").setLevel(logging.ERROR)
        image = Image.open(path)

        processed_data = self._processor(images=[image], return_tensors="pt")
        processed_data["pixel_values"] = processed_data["pixel_values"].squeeze(
            0
        )

        return processed_data


class CLIP(object):
    def __init__(self, pretrained_model):
        self._model = CLIPModel.from_pretrained(pretrained_model)
        self._processor = CLIPProcessor.from_pretrained(pretrained_model)

        self._model.eval()

    def get_image_features(self, image_paths, batch_size, callback):
        dataset = ImageDataset(image_paths, self._processor)

        dataloader = DataLoader(
            dataset=dataset,
            batch_size=batch_size,
            shuffle=False,
            drop_last=False,
            num_workers=GlobalConfig.get("features", "num_workers") or 0,
            pin_memory=(
                True if GlobalConfig.get("features", "pin_memory") else False
            ),
        )
        image_features = None
        num_batches = len(dataloader)
        with torch.no_grad():
            callback(0, num_batches, None)
            for i, data in enumerate(dataloader):
                data.to(self._model.device)
                batch_features = self._model.get_image_features(**data)
                image_features = (
                    torch.cat([image_features, batch_features])
                    if image_features is not None
                    else batch_features
                )
                callback(i + 1, num_batches, image_features)

        return image_features

    def get_text_features(self, texts):
        tokenized_input = self._processor(texts=texts, return_tensors="pt")

        text_features = self._model.get_text_features(**tokenized_input)

        return text_features

    def to(self, device):
        self._model.to(device)
