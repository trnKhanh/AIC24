import re
from copy import deepcopy
import logging
import hashlib

from thefuzz import fuzz

from ..index import MilvusDatabase
from ...config import GlobalConfig
from ...packages.analyse.features import CLIP


class Searcher(object):
    cache = {}

    def __init__(self, collection_name):
        self._logger = logging.getLogger("searcher")
        self._database = MilvusDatabase(collection_name)
        self._models = {}
        for model in GlobalConfig.get("webui", "features") or []:
            model_name = model["name"].lower()
            if model_name == "clip":
                pretrained_model = model["pretrained_model"]
                self._models[model_name] = CLIP(pretrained_model)

        if len(self._models) == 0:
            self._logger.error(
                f'No models found in "{GlobalConfig.CONFIG_FILE}". Check your "{GlobalConfig.CONFIG_FILE}"'
            )

    def get_models(self):
        return list(self._models.keys())

    def _process_query(self, query):
        video_match = re.search('video:((".+?")|\\S+)\\s?', query)
        video_ids = (
            video_match.group().replace("video:", "", 1).strip('" ').split(",")
            if video_match is not None
            else []
        )
        if video_match is not None:
            query = query.replace(video_match.group(), "", 1)

        queries = query.split(";")
        processed = {
            "queries": [],
            "advance": [],
            "video_ids": video_ids,
        }
        for q in queries:
            q = q.strip()
            ocr = []
            while True:
                match = re.search('OCR:((".+?")|\\S+)\\s?', q)
                if match is None:
                    break
                ocr.append(
                    match.group().replace("OCR:", "", 1).strip('" ').lower()
                )
                q = q.replace(match.group(), "")

            processed["queries"].append(q)
            processed["advance"].append({})

            if len(ocr) > 0:
                processed["advance"][-1]["ocr"] = " ".join(ocr)
        return processed

    def _process_advance(self, advance_query, result, ocr_weight):
        if "ocr" not in advance_query:
            return result
        query_ocr = advance_query["ocr"]
        res = deepcopy(result)

        for i, record in enumerate(result):
            ocr = record["entity"]["ocr"] if "ocr" in record["entity"] else ""
            ocr_distance = fuzz.partial_ratio(query_ocr, ocr) / 100

            res[i]["distance"] = (
                record["distance"] + ocr_distance * ocr_weight
            ) / (1 + ocr_weight)
        res = sorted(res, key=lambda x: x["distance"], reverse=True)
        return res

    def _combine_temporal_results(self, results, temporal_k, max_interval):
        best = None
        for i in range(len(results)):
            res = results[i]
            for j in range(len(res)):
                video_id, frame_id = results[i][j]["entity"]["frame_id"].split(
                    "#"
                )
                video_id = video_id.replace("L", "").replace("_V", "")
                video_id = int(video_id)
                frame_id = int(frame_id)
                results[i][j]["_id"] = (video_id, frame_id)

        for res in results[::-1]:
            if best is None:
                best = res[:temporal_k]
                continue
            tmp = []
            res = sorted(res, key=lambda x: x["_id"])
            best = sorted(best, key=lambda x: x["_id"])
            l = 0
            r = 0
            for cur in res:
                cur_vid, cur_fid = cur["_id"]
                cur_fid = int(cur_fid)

                while l < len(best):
                    next_vid, next_fid = best[l]["_id"]
                    next_fid = int(next_fid)
                    if next_vid > cur_vid or (
                        next_vid == cur_vid and next_fid > cur_fid
                    ):
                        break
                    else:
                        l += 1

                while r < len(best):
                    next_vid, next_fid = best[r]["_id"]
                    next_fid = int(next_fid)
                    if next_vid > cur_vid or (
                        next_vid == cur_vid
                        and next_fid > cur_fid + max_interval
                    ):
                        break
                    else:
                        r += 1

                for i in range(l, r):
                    self._logger.debug(
                        f"{cur['_id']} ({cur['distance']}) -> {best[i]['_id']} ({best[i]['distance']})"
                    )
                    tmp.append(
                        {
                            **cur,
                            "distance": cur["distance"] + best[i]["distance"],
                        }
                    )
            highest = {}
            for cur in tmp:
                if (
                    cur["_id"] not in highest
                    or cur["distance"] > highest[cur["_id"]]["distance"]
                ):
                    highest[cur["_id"]] = cur
            tmp = list(highest.values())
            tmp = sorted(tmp, key=lambda x: x["distance"], reverse=True)
            best = tmp[:temporal_k]

        return best

    def search(
        self,
        q: str,
        filter: str = "",
        offset: int = 0,
        limit: int = 50,
        nprobe: int = 8,
        model: str = "clip",
        temporal_k: int = 10000,
        ocr_weight: float = 1,
        max_interval: int = 250,
        selected: str | None = None,
    ):
        query_hash = hashlib.sha256(
            (
                q
                + f"nprobe:{nprobe} model:{model} temporal_k:{temporal_k} ocr_weight:{ocr_weight} max_interval:{max_interval}"
            ).encode("utf-8")
        ).hexdigest()
        self._logger.debug(
            (
                q
                + f" nprobe:{nprobe} model:{model} temporal_k:{temporal_k} ocr_weight:{ocr_weight} max_interval:{max_interval}"
            )
        )
        if query_hash in self.cache:
            combined_results = self.cache[query_hash]
        else:
            processed = self._process_query(q)
            self._logger.debug(f"temporal_k: {temporal_k}")
            self._logger.debug(processed)
            if all([len(query) == 0 for query in processed["queries"]]) and all(
                [len(a) == 0 for a in processed["advance"]]
            ):
                combined_results = self.get_videos(processed["video_ids"])
            else:

                text_features = self._models[model].get_text_features(
                    processed["queries"]
                )
                text_features = text_features.tolist()

                video_ids_fitler = " || ".join(
                    [
                        f'frame_id like "{x.strip()}#%"'
                        for x in processed["video_ids"]
                    ]
                )
                filter_empty = len(filter) == 0
                if len(processed["video_ids"]) > 0:
                    video_ids_fitler = "(" + video_ids_fitler + ")"
                    if not filter_empty:
                        video_ids_fitler = " && " + video_ids_fitler
                import time

                st = time.time()

                results = self._database.search(
                    text_features,
                    filter + video_ids_fitler,
                    0,
                    temporal_k,
                    nprobe,
                    model,
                )
                en = time.time()
                self._logger.debug(f"{en-st} seconds to search results")
                for i in range(len(processed["queries"])):
                    results[i] = self._process_advance(
                        processed["advance"][i], results[i], ocr_weight
                    )

                st = time.time()
                combined_results = self._combine_temporal_results(
                    results, temporal_k, max_interval
                )
                en = time.time()
                self._logger.debug(f"{en-st} seconds to combine results")
            self.cache[query_hash] = combined_results

        if combined_results is None:
            res = {
                "results": [],
                "total": 0,
                "offset": 0,
            }
        else:
            if selected:
                print(selected)
                for i, res in enumerate(combined_results):
                    if selected == res["entity"]["frame_id"]:
                        offset = (i // limit) * limit
                        break
            res = {
                "results": combined_results[offset : offset + limit],
                "total": len(combined_results),
                "offset": offset,
            }
        return res

    def get_videos(self, video_ids):
        if len(video_ids) == 0:
            return []
        video_ids_fitler = " || ".join(
            [f'frame_id like "{x.strip()}#%"' for x in video_ids]
        )
        res = self._database.query(video_ids_fitler, 0, 10000)
        res = sorted(res, key=lambda x: x["frame_id"])
        res = [{"entity": x} for x in res]
        return res

    def search_similar(
        self,
        id: str,
        offset: int = 0,
        limit: int = 50,
        nprobe: int = 8,
        model: str = "clip",
    ):
        record = self._database.get(id)
        if len(record) == 0:
            return {"results": [], "total": 0, "offset": 0}

        image_features = [record[0][model]]

        results = self._database.search(
            image_features, "", offset, limit, nprobe, model
        )[0]
        res = {
            "results": results,
            "total": self._database.get_total(),
            "offset": offset,
        }
        return res
