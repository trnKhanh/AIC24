import { Form } from "react-router-dom";
import classNames from "classnames";
import { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";

export default function Root() {
  const [answers, setAnswers] = useState([]);
  const [playingVideo, setPlayingVideo] = useState(null);
  const [frameCounter, setFrameCounter] = useState(0);
  const createAnswer = () => {};
  const playVideo = (frame) => {
    setPlayingVideo(frame);
  };
  useEffect(() => {
    if (playingVideo !== null) {
      const handleKeyDown = (e) => {
        if (e.keyCode === 27) {
          setPlayingVideo(null);
        }
      };
      const videoElement = document.querySelector("#playing-video");
      videoElement.currentTime = parseInt(playingVideo.frame_id) / 25 - 0.25;
      document.addEventListener("keydown", handleKeyDown);
      let id = setInterval(() => {
        setFrameCounter(videoElement.currentTime * 25);
      }, 20);
      return () => {
        document.removeEventListener("keydown", handleKeyDown);
        clearInterval(id);
      };
    }
  }, [playingVideo]);

  return (
    <>
      {playingVideo !== null && (
        <div
          onClick={(e) => {
            e.stopPropagation();
            setPlayingVideo(null);
          }}
          className="fixed flex items-center justify-center z-10 w-screen h-screen bg-black bg-opacity-25"
        >
          <div
            className="p-2 bg-white rounded-xl"
            onClick={(e) => {
              e.stopPropagation();
            }}
          >
            <div className="">
              <span className="font-bold">Video id</span>
              {": "}
              {playingVideo.video_id}
            </div>
            <div className="">
              {" "}
              <span className="font-bold">Frame id</span>
              {": "}
              {parseInt(frameCounter)}
            </div>
            <video
              id="playing-video"
              key={playingVideo.video_uri}
              controls
              autoPlay
            >
              <source src={playingVideo.video_uri} type="video/mp4" />
            </video>
          </div>
        </div>
      )}
      <div className="flex flex-row">
        <Outlet context={{ createAnswer, playVideo }} />
      </div>
    </>
  );
}
