import os
import math
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import torch
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn

from .command import BaseCommand
from ...packages.analyse.features import CLIP
from ...config import GlobalConfig


class AnalyseCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(AnalyseCommand, self).__init__(*args, **kwargs)

    def add_args(self, subparser):
        parser = subparser.add_parser(
            "analyse", help="Analyse extracted keyframes"
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
            "-s",
            "--skip-overlapping",
            dest="do_overwrite",
            action="store_false",
            help="Skip overlapping videos",
        )

        parser.set_defaults(func=self)

    def __call__(self, batch_size, gpu, do_overwrite, verbose, *args, **kwargs):
        models = GlobalConfig.get("analyse", "features")
        if models is None:
            raise RuntimeError(
                f"Models for features extraction are not specified. Check your config file."
            )
        video_ids = self._init_features_dir(do_overwrite)

        for model in models:
            model_name = model["name"]
            pretrained_model = model["pretrained_model"]
            clip = CLIP(pretrained_model)
            self._logger.info(
                f"Start extracting features using {model_name} ({pretrained_model})"
            )
            if gpu and torch.cuda.is_available():
                clip.to("cuda")
            elif verbose and gpu:
                clip.to("cpu")
                self._logger.warning(
                    "CUDA is not available, fallbacked to use CPU"
                )

            with (
                Progress(
                    TextColumn("{task.fields[name]}"),
                    TextColumn(":"),
                    SpinnerColumn(),
                    *Progress.get_default_columns(),
                    TimeElapsedColumn(),
                ) as progress,
                ThreadPoolExecutor(int(os.cpu_count() or 0) // 2) as executor,
            ):

                def update_progress(task_id):
                    return lambda *args, **kwargs: progress.update(
                        task_id, *args, **kwargs
                    )

                def analyse_one_video(video_id):
                    task_id = progress.add_task(
                        description="Processing...",
                        name=video_id,
                    )
                    try:
                        status_ok = self._extract_features(
                            model_name,
                            clip,
                            video_id,
                            batch_size,
                            update_progress(task_id),
                        )
                        progress.update(
                            task_id,
                            completed=1,
                            total=1,
                            description=(
                                "Finished" if status_ok else "Skipped"
                            ),
                        )
                    except Exception as e:
                        progress.update(task_id, description=f"Error: {str(e)}")

                futures = []
                for video_id in video_ids:
                    futures.append(executor.submit(analyse_one_video, video_id))
                for future in futures:
                    future.result()

    def _init_features_dir(self, do_overwrite):
        keyframes_dir = self._work_dir / "keyframes"
        features_dir = self._work_dir / "features"
        video_paths = [d for d in keyframes_dir.glob("*/")]
        video_ids = []
        for video_path in video_paths:
            video_features_dir = features_dir / video_path.stem
            if video_features_dir.exists():
                if do_overwrite:
                    shutil.rmtree(video_features_dir)
                else:
                    continue
            video_ids.append(video_path.stem)
            video_features_dir.mkdir(parents=True, exist_ok=True)
        return video_ids

    def _get_keyframes_list(self, video_id):
        keyframes_path = self._work_dir / "keyframes" / video_id

        keyframes = []
        for keyframe in os.scandir(keyframes_path):
            keyframes.append(Path(keyframe.path))

        return keyframes

    def _extract_features(
        self,
        model_name,
        clip,
        video_id,
        batch_size,
        update_progress,
    ):
        update_progress(description="Extracting features...")
        keyframe_files = self._get_keyframes_list(video_id)
        features_dir = self._work_dir / f"features" / video_id

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
            feature_file = features_dir / path.stem / f"{model_name}.npy"
            feature_file.parent.mkdir(parents=True, exist_ok=True)

            np.save(feature_file, features[i])
            update_progress(advance=1)

        return 1
