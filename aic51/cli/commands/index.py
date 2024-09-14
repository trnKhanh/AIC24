from pathlib import Path
import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .command import BaseCommand
from ...packages.index import MilvusDatabase


class IndexCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super(IndexCommand, self).__init__(*args, **kwargs)

    def add_args(self, subparser):
        parser = subparser.add_parser("index", help="Index features")

        parser.add_argument(
            "-c",
            "--collection",
            dest="collection_name",
            type=str,
            default="milvus",
            help="Name of collection to index",
        )
        parser.add_argument(
            "-o",
            "--overwrite",
            dest="do_overwrite",
            action="store_true",
            help="Overwrite existing collection",
        )
        parser.add_argument(
            "-u",
            "--update",
            dest="do_update",
            action="store_true",
            help="Update existing records",
        )

        parser.set_defaults(func=self)

    def __call__(
        self, collection_name, do_overwrite, do_update, *args, **kwargs
    ):
        MilvusDatabase.start_server()
        database = MilvusDatabase(collection_name, do_overwrite)
        features_dir = self._work_dir / "features"
        with (
            Progress(
                TextColumn("{task.fields[name]}"),
                TextColumn(":"),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
            ) as progress,
        ):
            video_paths = sorted(
                [d for d in features_dir.glob("*/") if d.is_dir()],
                key=lambda path: path.stem,
            )
            task_id = progress.add_task(
                "Gathering features...",
                completed=0,
                total=len(video_paths),
                name="",
            )
            data_list = []
            for video_path in video_paths:
                progress.update(task_id, name=video_path.stem)
                video_id = video_path.stem
                data_list.extend(self._get_features(video_id))
                progress.update(task_id, advance=1)

            res = database.insert(data_list, do_update)
            self._logger.info(f"Successfully inserted {res['insert']} records")

    def _get_features(self, video_id):
        features_dir = self._work_dir / "features" / video_id
        data_list = []
        for frame_path in features_dir.glob("*/"):
            frame_id = frame_path.stem
            data = {
                "frame_id": f"{video_id}#{frame_id}",  # This is because Milvus does not allow composite primary key
                "cluster_id": 0,
            }
            for feature_path in frame_path.glob("*.npy"):
                feature = np.load(feature_path)
                data = {
                    **data,
                    f"feature_{feature_path.stem}": feature,
                }
            data_list.append(data)
        return data_list
