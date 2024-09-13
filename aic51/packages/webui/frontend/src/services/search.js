import axios from "axios";

const PORT = import.meta.env.VITE_PORT || 5000;

export async function search(q, offset, limit, nprobe, model) {
  const res = await axios.get(`http://127.0.0.1:${PORT}/api/search`, {
    params: {
      q: q,
      offset: offset,
      limit: limit,
      nprobe: nprobe,
      model: model,
    },
  });
  const data = res.data;
  return data;
}
export async function searchSimilar(id, offset, limit, nprobe, model) {
  const res = await axios.get(`http://127.0.0.1:${PORT}/api/similar`, {
    params: {
      id: id,
      offset: offset,
      limit: limit,
      nprobe: nprobe,
      model: model,
    },
  });
  const data = res.data;
  return data;
}

export async function getFrameInfo(videoId, frameId) {
  const res = await axios.get(`http://127.0.0.1:${PORT}/api/frame_info`, {
    params: {
      video_id: videoId,
      frame_id: frameId,
    },
  });
  const data = res.data;
  return data;
}
export async function getAvailableModels() {
  const res = await axios.get(`http://127.0.0.1:${PORT}/api/models`);
  const data = res.data;
  return data;
}
