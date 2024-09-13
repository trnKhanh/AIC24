import { useLoaderData } from "react-router-dom";
import { useState } from "react";
import { Outlet } from "react-router-dom";

import VideoProvider, { usePlayVideo } from "../components/VideoPlayer.jsx";

import AnswerSidebar from "../components/Answer.jsx";

export default function Root() {
  return (
    <VideoProvider>
      <div className="flex flex-row">
        <div>
          <div className="w-96">
            <AnswerSidebar />
          </div>
        </div>
        <Outlet />
      </div>
    </VideoProvider>
  );
}
