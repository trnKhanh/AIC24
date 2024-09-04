import logging
import subprocess
from pathlib import Path

from pymilvus import DataType, MilvusClient
from ...config import GlobalConfig


class MilvusDatabase(object):
    DATATYPE_MAP = {
        "BOOL": DataType.BOOL,
        "INT8": DataType.INT8,
        "INT16": DataType.INT16,
        "INT32": DataType.INT32,
        "INT64": DataType.INT64,
        "FLOAT": DataType.FLOAT,
        "DOUBLE": DataType.DOUBLE,
        "BINARY_VECTOR": DataType.BINARY_VECTOR,
        "FLOAT_VECTOR": DataType.FLOAT_VECTOR,
        "FLOAT16_VECTOR": DataType.FLOAT16_VECTOR,
        "BFLOAT16_VECTOR": DataType.BFLOAT16_VECTOR,
        "VARCHAR": DataType.VARCHAR,
        "JSON": DataType.JSON,
        "ARRAY": DataType.ARRAY,
    }

    def __init__(self, collection_name, do_overwrite=False):
        self._collection_name = collection_name
        self._logger = logging.getLogger(__name__)
        self._start_server()
        self._client = MilvusClient("http://localhost:19530")

        collection_exists = self._client.has_collection(collection_name)

        if do_overwrite or not collection_exists:
            if collection_exists:
                self._client.drop_collection(self._collection_name)

            schema = MilvusClient.create_schema(
                auto_id=False, enable_dynamic_field=False
            )
            fields = GlobalConfig.get("milvus", "fields")
            if fields is not None:
                for field in fields:
                    if "datatype" in field:
                        field["datatype"] = self.DATATYPE_MAP[field["datatype"]]

                    schema.add_field(**field)

            index_params = self._client.prepare_index_params()
            indices = GlobalConfig.get("milvus", "indices")
            if indices is not None:
                for index in indices:
                    index_params.add_index(**index)

            self._client.create_collection(
                collection_name, schema=schema, index_params=index_params
            )

    def __del__(self):
        self._client.close()
        self._stop_server()

    def insert(self, data, do_update=False):
        if do_update:
            self._client.upsert(self._collection_name, data)
        else:
            self._client.insert(self._collection_name, data)

    def search(self, query, filter, offset, limit, nprob=8, feature="clip"):
        search_params = {
            "nprob": nprob,
        }
        res = self._client.search(
            self._collection_name,
            query,
            anns_field=f"{feature}_feature",
            filter=filter,
            offset=offset,
            limit=limit,
            search_params=search_params,
            output_fields=["video_id", "frame_id"],
        )
        return res

    def upsert(self):
        pass

    def delete(self):
        pass

    def _start_server(self):
        self._logger.info("Starting milvus-standalone server...")
        compose_file = (
            Path(__file__).parent
            / "../../milvus-standalone/milvus-standalone-docker-compose.yaml"
        )

        compose_cmd = [
            "docker",
            "compose",
            "--file",
            compose_file.resolve(),
            "up",
            "-d",
        ]
        subprocess.run(compose_cmd)

    def _stop_server(self):
        self._logger.info("Stopping milvus-standalone server...")
        compose_file = (
            Path(__file__).parent
            / "../../milvus-standalone/milvus-standalone-docker-compose.yaml"
        )
        compose_cmd = [
            "docker",
            "compose",
            "--file",
            compose_file.resolve(),
            "down",
        ]
        subprocess.run(compose_cmd)
