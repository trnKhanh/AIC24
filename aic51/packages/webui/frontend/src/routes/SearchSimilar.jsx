import { searchSimilar } from "../services/search.js";
import {
  nlist,
  limitOptions,
  nprobeOption,
} from "../resources/options.js";

export async function loader({ request }) {
  const url = new URL(request.url);
  const searchParams = url.searchParams;

  const id = searchParams.get("id");
  const offset = searchParams.get("offset") || 0;
  const limit = searchParams.get("limit") || limitOptions[0];
  const nprobe = searchParams.get("nprobe") || nprobeOption[0];
  const model = searchParams.get("model") || undefined;

  const { total, frames } = await searchSimilar(
    id,
    offset,
    limit,
    nprobe,
    model,
  );

  return {
    query: { id },
    params: { limit, nprobe, model },
    offset,
    data: { total, frames },
  };
}
