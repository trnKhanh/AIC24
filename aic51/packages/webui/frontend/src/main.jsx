import * as React from "react";
import * as ReactDOM from "react-dom/client";

import {
  createRoutesFromElements,
  createBrowserRouter,
  Route,
  RouterProvider,
} from "react-router-dom";

import Root from "./routes/Root.jsx";
import Search, { loader as SearchLoader } from "./routes/Search.jsx";
import {loader as SearchSimilarLoader} from "./routes/SearchSimilar.jsx"
import "./index.css"

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route path="/" element={<Root />}>
      <Route path="search" element={<Search />} loader={SearchLoader} />
      <Route path="similar" element={<Search />} loader={SearchSimilarLoader} />
    </Route>,
  ),
);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
