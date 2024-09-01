import os
import math
from pathlib import Path
import shutil

import numpy as np
import torch
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn

from .command import BaseCommand
from ...packages.analyse.features import CLIP


class AnalyseCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(AnalyseCommand, self).__init__(*args, **kwargs)

    def add_args(self, subparser):
        parser = subparser.add_parser(
            "analyse", help="Analyse extracted keyframes"
        )

        parser.add_argument(
            "-m",
            "--model",
            dest="model",
            type=str,
            default="openai/clip-vit-base-patch32",
            help="CLIP model used to extract features from keyframes",
        )
        parser.add_argument(
            "-b",
            "--batch-size",
            dest="batch_size",
            type=int,
            default=1,
        )
        parser.add_argument(
            "--no-gpu",
            dest="gpu",
            action="store_false",
            help="Do not use gpu",
        )
        parser.add_argument(
            "-o",
            "--overwrite",
            dest="do_overwrite",
            action="store_true",
            help="Overwrite existing features",
        )

        parser.set_defaults(func=self)

    def __call__(
        self, model, batch_size, gpu, do_overwrite, verbose, *args, **kwargs
    ):
        clip = CLIP(model)
        if gpu and torch.cuda.is_available():
            clip.to("cuda")
        elif verbose and gpu:
            clip.to("cpu")
            self._logger.warning("CUDA is not available, fallbacked to use CPU")

        keyframes_dir = self._work_dir / "keyframes"

        with Progress(
            TextColumn("{task.fields[name]}"),
            TextColumn(":"),
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
        ) as progress:

            def update_progress(task_id):
                return lambda *args, **kwargs: progress.update(
                    task_id, *args, **kwargs
                )

            for video in os.scandir(keyframes_dir):
                if not video.is_dir():
                    continue

                video_id = video.name
                task_id = progress.add_task(
                    description="Processing...",
                    name=video_id,
                )
                status_ok = self._extract_features(
                    clip,
                    video_id,
                    batch_size,
                    do_overwrite,
                    update_progress(task_id),
                )
                progress.update(
                    task_id,
                    completed=1,
                    total=1,
                    description=("Finished" if status_ok else "Skipped"),
                )

    def _get_keyframes_list(self, video_id):
        keyframes_path = self._work_dir / "keyframes" / video_id

        keyframes = []
        for keyframe in os.scandir(keyframes_path):
            keyframes.append(Path(keyframe.path))

        return keyframes

    def _extract_features(
        self, clip, video_id, batch_size, do_overwrite, update_progress
    ):
        update_progress(description="Extracting features...")
        keyframe_files = self._get_keyframes_list(video_id)
        features_dir = self._work_dir / "features" / video_id

        if features_dir.exists():
            if do_overwrite:
                shutil.rmtree(features_dir)
            else:
                return 0

        features_dir.mkdir(parents=True, exist_ok=True)

        features = clip.get_image_features(
            keyframe_files,
            batch_size,
            lambda finished_batches, total_batches, _: update_progress(
                completed=finished_batches, total=total_batches
            ),
        )
        update_progress(
            completed=0,
            total=features.size(0),
            description="Saving features...",
        )
        for i, path in enumerate(keyframe_files):
            feature_file = features_dir / f"{path.stem}.npy"
            np.save(feature_file, features[i])
            update_progress(advance=1)

        return 1
