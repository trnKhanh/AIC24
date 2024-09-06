import { searchSimilar } from "../services/search.js";

export async function loader({ request }) {
  const url = new URL(request.url);
  const searchParams = url.searchParams;

  const id = searchParams.get("id");
  const offset = searchParams.get("offset") || undefined;
  const limit = searchParams.get("limit") || undefined;
  const nprob = searchParams.get("nprob") || undefined;
  const model = searchParams.get("model") || undefined;

  const { frames } = await searchSimilar(id, offset, limit, nprob, model);

  return { id, offset, limit, nprob, model, frames: frames };
}
