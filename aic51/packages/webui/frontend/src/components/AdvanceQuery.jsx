import { useState, useEffect, useRef } from "react";
import classNames from "classnames";
import AddButton from "../assets/add-btn.svg";
import DeleteButton from "../assets/delete-btn.svg";
import XButton from "../assets/x-btn.svg";

export function AdvanceQueryContainer({ q, onChange }) {
  const temporalQueries = q.split(";");
  const handleOnChange = (id, newTemporalQuery) => {
    temporalQueries[id] = newTemporalQuery;
    onChange(temporalQueries.join(";"));
  };
  const handleOnDelete = (id) => {
    temporalQueries.splice(id, 1);
    onChange(temporalQueries.join(";"));
  };
  return (
    <div className="flex flex-row items-center flex-wrap">
      {temporalQueries.map((tq, id) => (
        <div className="basis-1/4 p-1">
          <TemporalQueryContainer
            key={id}
            temporalQuery={tq}
            onChange={(newTemporalQuery) => {
              handleOnChange(id, newTemporalQuery);
            }}
            onDelete={() => {
              handleOnDelete(id);
            }}
          />
        </div>
      ))}
      <div className="basis-1/4">
        <img
          className="hover:bg-gray-300 active:bg-gray-400 m-auto"
          src={AddButton}
          width="30em"
          draggable={false}
          onClick={() => {
            onChange(q + ";");
          }}
        />
      </div>
    </div>
  );
}

export function TemporalQueryContainer({ temporalQuery, onChange, onDelete }) {
  let q = temporalQuery;
  let ocrRegex = /OCR:((".*?")|\S+)\s?/g;
  const ocrMatches = q.matchAll(ocrRegex);
  const ocrs = [];
  for (const match of ocrMatches) {
    ocrs.push(
      match[0]
        .substring(4)
        .trim()
        .replace(/(^"|"$)/g, ""),
    );
    q = q.replace(match[0], "");
  }
  let objectbbRegex = /object:((".*?")|\S+)\s?/g;
  const objectbbMatches = q.matchAll(objectbbRegex);
  const objectbbs = [];
  for (const match of objectbbMatches) {
    objectbbs.push(
      match[0]
        .substring(7)
        .trim()
        .replace(/(^"|"$)/g, ""),
    );
    q = q.replace(match[0], "");
  }

  const handleOnChange = (e) => {
    const newQ = e.target.value;
    let selectorStr = [];
    for (const ocr of ocrs) {
      selectorStr.push(`OCR:"${ocr}"`);
    }
    for (const objectbb of objectbbs) {
      selectorStr.push(`object:"${objectbb}"`);
    }
    onChange(newQ + selectorStr.join(" "));
  };
  const handleOnOCRChange = (e) => {
    let selectorStr = [];
    if (e.target.value.length > 0) {
      let newocrs = e.target.value.split(",");
      for (const ocr of newocrs) {
        selectorStr.push(`OCR:"${ocr}"`);
      }
    }
    for (const objectbb of objectbbs) {
      selectorStr.push(`object:"${objectbb}"`);
    }

    onChange(q + selectorStr.join(" "));
  };
  const handleOnObjectbbChange = (newObjectbbs) => {
    console.log(newObjectbbs);
    let selectorStr = [];
    for (const ocr of ocrs) {
      selectorStr.push(`OCR:"${ocr}"`);
    }
    for (const objectbb of newObjectbbs) {
      selectorStr.push(`object:"${objectbb}"`);
    }

    onChange(q + selectorStr.join(" "));
  };
  return (
    <div className="text-sm bg-sky-300 flex flex-col p-1 space-y-1">
      <img
        className="mx-auto hover:bg-gray-300 active:bg-gray-400"
        src={DeleteButton}
        width="25em"
        draggable={false}
        onClick={() => {
          onDelete();
        }}
      />
      <textarea
        className="bg-slate-100 text-slate-400 focus:bg-white focus:text-black focus:outline-none"
        rows={2}
        value={q}
        onChange={handleOnChange}
      />
      <textarea
        className="bg-slate-100 text-slate-400 focus:bg-white focus:text-black focus:outline-none"
        rows={1}
        value={ocrs.join(",")}
        onKeyDown={(e) => {
          if (e.keyCode === 222) {
            e.preventDefault();
          }
        }}
        onChange={handleOnOCRChange}
      />
      <ObjectContainer
        objectbbs={objectbbs}
        onChange={handleOnObjectbbChange}
      />
    </div>
  );
}
const options = [
  "dog",
  "cat",
  "people",
  "car",
  "train",
  "box",
  "plane",
  "plain",
  "tv",
  "phone",
  "picture",
  "face",
  "girl",
  "lady",
  "men",
];

export function ObjectContainer({ objectbbs, onChange }) {
  const handleOnDelete = (id) => {
    objectbbs.splice(id, 1);
    onChange(objectbbs);
  };
  const handleOnCreate = (o) => {
    if (options.includes(o)) objectbbs.push(o);
    onChange(objectbbs);
  };
  return (
    <div className="flex flex-col space-y-1">
      <SearchabeDropdown
        name={"objectbb-selection"}
        options={options}
        onSelect={(opt) => handleOnCreate(opt)}
      />
      <div className="flex flex-row flex-wrap">
        {objectbbs.map((o, id) => (
          <div className="px-1">
            <ObjectBox
              key={id}
              objectbb={o}
              onDelete={() => handleOnDelete(id)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export function ObjectBox({ objectbb, onDelete }) {
  return (
    <div className="flex flex-row items-center space-x-1 bg-orange-100 w-fit">
      <div>{objectbb}</div>
      <img
        className="bg-red-100"
        src={XButton}
        width="15rem"
        onClick={onDelete}
      />
    </div>
  );
}

export function SearchabeDropdown({ name, options, onSelect }) {
  const [isFocus, setIsFocus] = useState(false);
  const [search, setSearch] = useState("");
  const dropdownElement = useRef(null);
  const visibleOptions = [];
  for (const opt of options) {
    if (opt.includes(search)) {
      visibleOptions.push(opt);
    }
  }

  const handleOnChange = (e) => {
    const text = e.target.value;
    setSearch(text);
  };

  useEffect(() => {
    const handleOnClick = (e) => {
      if (dropdownElement.current.contains(e.target)) {
        setIsFocus(true);
      } else {
        setIsFocus(false);
      }
    };
    document.addEventListener("click", handleOnClick);

    return () => {
      document.removeEventListener("click", handleOnClick);
    };
  }, []);

  return (
    <div className="relative group h-5">
      <div
        id={"searchable-dropdown-" + name}
        className={classNames("absolute flex flex-col w-full", {
          "z-10": isFocus,
        })}
        ref={dropdownElement}
      >
        <input
          className="bg-slate-100 text-slate-400 focus:bg-white focus:text-black focus:outline-none"
          type="text"
          value={search}
          onChange={handleOnChange}
          onKeyDown={(e) => {
            if (e.keyCode === 13) {
              e.preventDefault();
              e.stopPropagation();
            }
          }}
        />
        <div
          className={classNames(
            "top-full bg-gray-100 p-1 w-full max-h-52 overflow-scroll",
            {
              visible: isFocus,
              hidden: !isFocus,
            },
          )}
        >
          {visibleOptions.map((opt) => (
            <div
              key={opt}
              className="hover:bg-blue-200"
              onClick={(e) => {
                e.stopPropagation();
                setSearch("");
                setIsFocus(false);
                onSelect(opt);
              }}
            >
              {opt}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
