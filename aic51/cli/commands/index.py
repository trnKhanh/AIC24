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
            "-u",
            "--update",
            dest="do_update",
            action="store_true",
            help="Update existing records",
        )

        parser.set_defaults(func=self)

    def __call__(self, collection_name, do_update, *args, **kwargs):
        # For some reasons, drop_collection works but very slow and
        # blocks IO process. Therefore, do not specify the overwrite
        # flag at the moment.
        database = MilvusDatabase(collection_name)
        features_dir = self._work_dir / "features"
        with (
            Progress(
                TextColumn("{task.fields[name]}"),
                TextColumn(":"),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
            ) as progress,
            ThreadPoolExecutor(os.cpu_count()) as executor,
        ):

            def update_progress(task_id):
                return lambda *args, **kwargs: progress.update(
                    task_id, *args, **kwargs
                )

            def index_one_video(video_id):
                task_id = progress.add_task(
                    description="Processing...", name=video_id
                )
                try:
                    self._index_features(
                        database,
                        video_id,
                        do_update,
                        update_progress(task_id),
                    )
                    progress.update(
                        task_id,
                        completed=1,
                        total=1,
                        description="Finished",
                    )
                except Exception as e:
                    progress.update(task_id, description=f"Error: {str(e)}")

            for video_path in features_dir.glob("*/"):
                video_id = video_path.stem
                executor.submit(index_one_video, video_id)

    def _index_features(
        self, database, video_id, do_update, update_progress
    ):
        update_progress(description="Indexing...")
        features_dir = self._work_dir / "features" / video_id
        for frame_path in features_dir.glob("*/"):
            frame_id = int(frame_path.stem)
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
            database.insert(data, do_update)
