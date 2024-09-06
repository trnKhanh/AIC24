import {
  useLoaderData,
  Form,
  useSubmit,
  useOutletContext,
} from "react-router-dom";
import { useEffect, useState } from "react";

import { search } from "../services/search.js";
import { FrameItem, FrameContainer } from "../components/Frame.jsx";
import VideoPlayer from "../components/VideoPlayer.jsx";
import { Dropdown } from "../components/Filter.jsx";
import PreviousButton from "../assets/previous-btn.svg";
import NextButton from "../assets/next-btn.svg";
import HomeButton from "../assets/home-btn.svg";

export async function loader({ request }) {
  const url = new URL(request.url);
  const searchParams = url.searchParams;

  const q = searchParams.get("q");
  const offset = searchParams.get("offset") || undefined;
  const limit = searchParams.get("limit") || undefined;
  const nprob = searchParams.get("nprob") || undefined;
  const model = searchParams.get("model") || undefined;

  const { frames } = await search(q, offset, limit, nprob, model);

  return { q, offset, limit, nprob, model, frames: frames };
}

const nprobOption = [8, 32, 128, 256];
const limitOptions = [10, 20, 50];
const modelOptions = ["clip_b_16", "clip_b_32"];

export default function Search() {
  const submit = useSubmit();
  const {
    id = null,
    q = "",
    offset = 0,
    limit = limitOptions[0],
    nprob = nprobOption[0],
    model = modelOptions[0],
    frames,
  } = useLoaderData();
  const [playing, setPlaying] = useState(false);
  const [selectedFrame, setSelectedFrame] = useState(null);
  const { createAnswer, playVideo } = useOutletContext();

  const query = id !== null ? { id: id } : { q: q || "" };

  const hyperParams = {
    limit: limit,
    nprob: nprob,
    model: model,
  };

  useEffect(() => {
    // Set correct values
    document.querySelector("#search-bar").value = q;
    document.querySelector("#search-bar").focus();

    for (const [k, v] of Object.entries(hyperParams)) {
      document.querySelector(`#${k}`).value = v;
    }
  }, [q, limit, nprob, model]);

  useEffect(() => {
    // Add hotkeys
    const handleKeyDown = (e) => {
      console.log(e.keyCode);
      switch (e.keyCode) {
        case 191:
          const searchBar = document.querySelector("#search-bar");
          if (searchBar !== document.activeElement) {
            e.preventDefault();
            searchBar.focus();
            return false;
          }
        case 37:
          goToPreviousPage();
          return true;
        case 39:
          goToNextPage();
          return true;
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [offset]);

  const goToFirstPage = () => {
    submit({
      ...query,
      ...hyperParams,
      offset: 0,
    });
  };
  const goToPreviousPage = () => {
    submit({
      ...query,
      ...hyperParams,
      offset: Math.max(parseInt(offset) - parseInt(limit), 0),
    });
  };
  const goToNextPage = () => {
    submit({
      ...query,
      ...hyperParams,
      offset: Math.max(parseInt(offset) + parseInt(limit), 0),
    });
  };

  const handleOnPlay = (frame) => {
    playVideo(frame);
  };
  const handleOnSearchSimilar = (frame) => {
    submit(
      { id: frame.id, ...hyperParams },
      { method: "GET", action: "/similar" },
    );
  };

  const handleOnSelect = (frame) => {
    setSelectedFrame(frame.id);
  };

  return (
    <div className="flex flex-col w-full">
      <Form action="/search">
        <div
          className="flex flex-col p-1 px-5 space-y-2 bg-gray-100"
          id="search-area"
        >
          <div className="flex flex-row space-x-5">
            <input
              className="flex-grow text-lg p-2 border-2 rounded-xl border-gray-700 bg-gray-200 text-gray-500 focus:border-black focus:bg-white focus:text-black focus:outline-none"
              id="search-bar"
              type="search"
              placeholder="Search"
              name="q"
            />
            <input
              className="text-lg py-1 px-4 border-2 rounded-xl bg-gray-700 text-white hover:bg-gray-500 active:bg-gray-400"
              type="submit"
              value="Search"
            />
          </div>
          <div className="self-stretch text-md justify-start flex flex-row space-x-2">
            <Dropdown name="nprob" options={nprobOption} />
            <Dropdown name="limit" options={limitOptions} />
            <Dropdown name="model" options={modelOptions} />
          </div>
        </div>
      </Form>

      <div id="nav-bar" className="flex flex-row justify-center">
        <img
          onClick={() => {
            goToFirstPage();
          }}
          className="hover:bg-gray-200 active:bg-gray-300"
          width="50em"
          src={HomeButton}
          draggable="false"
        />

        <img
          onClick={() => {
            goToPreviousPage();
          }}
          className="hover:bg-gray-200 active:bg-gray-300"
          width="50em"
          src={PreviousButton}
          draggable="false"
        />
        <img
          onClick={() => {
            goToNextPage();
          }}
          className="hover:bg-gray-200 active:bg-gray-300"
          width="50em"
          src={NextButton}
          draggable="false"
        />
      </div>

      <FrameContainer id="result">
        {frames.map((frame) => (
          <FrameItem
            key={frame.id}
            video_id={frame.video_id}
            frame_id={frame.frame_id}
            thumbnail={frame.frame_uri}
            onPlay={() => {
              handleOnPlay(frame);
            }}
            onSearchSimilar={() => {
              handleOnSearchSimilar(frame);
            }}
            onSelect={() => {
              handleOnSelect(frame);
            }}
            selected={selectedFrame === frame.id}
          />
        ))}
      </FrameContainer>
    </div>
  );
}
