import { useLoaderData, Form, useSubmit } from "react-router-dom";
import { useEffect, useState } from "react";

import { search } from "../services/search.js";
import { FrameItem, FrameContainer } from "../components/Frame.jsx";
import { usePlayVideo } from "../components/VideoPlayer.jsx";
import { Dropdown } from "../components/Filter.jsx";
import PreviousButton from "../assets/previous-btn.svg";
import NextButton from "../assets/next-btn.svg";
import HomeButton from "../assets/home-btn.svg";

import {
  nlist,
  limitOptions,
  nprobeOption,
  modelOptions,
} from "../resources/options.js";

export async function loader({ request }) {
  const url = new URL(request.url);
  const searchParams = url.searchParams;

  const q = searchParams.get("q");
  const offset = searchParams.get("offset") || 0;
  const limit = searchParams.get("limit") || limitOptions[0];
  const nprobe = searchParams.get("nprobe") || nprobeOption[0];
  const model = searchParams.get("model") || modelOptions[0];

  const { total, frames } = await search(q, offset, limit, nprobe, model);

  return {
    query: { q },
    params: { limit, nprobe, model },
    offset,
    data: { total, frames },
  };
}

export default function Search() {
  const submit = useSubmit();
  const { query, params, offset, data } = useLoaderData();
  const playVideo = usePlayVideo();
  const [selectedFrame, setSelectedFrame] = useState(null);

  const { q = "", id = null } = query;
  const { limit, nprobe, model } = params;

  const { total, frames } = data;
  const empty = frames.length === 0;

  useEffect(() => {
    // Set correct values
    document.querySelector("#search-bar").value = q || "";
    document.querySelector("#search-bar").focus();
  }, [q]);

  for (const [k, v] of Object.entries(params)) {
    useEffect(() => {
      document.querySelector(`#${k}`).value = v;
    }, [v]);
  }

  // Add hotkeys
  useEffect(() => {
    const handleKeyDown = (e) => {
      switch (e.keyCode) {
        case 191:
          const filterBar = document.querySelector("#search-area");
          filterBar.scrollIntoView();
          const searchBar = document.querySelector("#search-bar");
          if (searchBar !== document.activeElement) {
            e.preventDefault();
            searchBar.focus();
            return false;
          }
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);
  useEffect(() => {
    const handleKeyDown = (e) => {
      switch (e.keyCode) {
        case 38:
          e.preventDefault();
          goToPreviousPage();
          return;
        case 40:
          e.preventDefault();
          goToNextPage();
          return;
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
      ...params,
      offset: 0,
    });
  };
  const goToPreviousPage = () => {
    submit({
      ...query,
      ...params,
      offset: Math.max(parseInt(offset) - parseInt(limit), 0),
    });
  };
  const goToNextPage = () => {
    if (!empty) {
      submit({
        ...query,
        ...params,
        offset: parseInt(offset) + parseInt(limit),
      });
    }
  };

  const handleOnPlay = (frame) => {
    playVideo(frame);
  };
  const handleOnSearchSimilar = (frame) => {
    submit({ id: frame.id, ...params }, { action: "/similar" });
  };

  const handleOnSelect = (frame) => {
    setSelectedFrame(frame.id);
  };
  const handleOnChangeParams = (e) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {};
    for (const [k, v] of formData.entries()) {
      data[k] = v;
    }
    submit({
      ...query,
      ...data,
    });
  };
  const handleOnSearch = (e) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {};
    for (const [k, v] of formData.entries()) {
      data[k] = v;
    }
    document.activeElement.blur();
    submit(
      {
        ...data,
        ...params,
      },
      { action: "/search" },
    );
  };

  return (
    <div id="search-area" className="flex flex-col w-full">
      <Form onSubmit={handleOnChangeParams}>
        <div className="py-2 px-5 self-stretch text-md justify-start items-center flex flex-row space-x-2">
          <Dropdown name="nprobe" options={nprobeOption} />
          <Dropdown name="limit" options={limitOptions} />
          <Dropdown name="model" options={modelOptions} />
          <input
            className="h-fit text-md px-4 py-2 border-2 border-gray-500 rounded-xl bg-gray-900 text-white hover:bg-gray-800 active:bg-gray-700"
            type="submit"
            value="Apply"
          />
        </div>
      </Form>

      <Form onSubmit={handleOnSearch}>
        <div className="flex flex-col p-1 px-5 space-y-2 bg-gray-100">
          <div className="flex flex-row space-x-5">
            <input
              autoComplete="off"
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
        </div>
      </Form>

      <div
        id="nav-bar"
        className="p-1 flex flex-row justify-center items-center text-xl font-bold"
      >
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
        <div className="w-10 text-center">{Math.floor(offset / limit) + 1}</div>
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
      {empty ? (
        <div className="w-full text-center p-2 bg-red-500 text-white text-xl text-bold">
          END
        </div>
      ) : (
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
      )}
    </div>
  );
}
