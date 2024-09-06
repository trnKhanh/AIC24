import axios from "axios";

export async function search(q, offset, limit, nprob, model) {
  const res = await axios.get("http://127.0.0.1:5000/api/search", {
    params: {
      q: q,
      offset: offset,
      limit: limit,
      nprob: nprob,
      model: model,
    },
  });
  const data = res.data;
  return data;
}
export async function searchSimilar(id, offset, limit, nprob, model) {
  const res = await axios.get("http://127.0.0.1:5000/api/similar", {
    params: {
      id: id,
      offset: offset,
      limit: limit,
      nprob: nprob,
      model: model,
    },
  });
  const data = res.data;
  return data;
}
