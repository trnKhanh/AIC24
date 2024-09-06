export function Dropdown({ name, options }) {
  return (
    <div className="flex flex-row items-center bg-white border-2 rounded-xl p-1">
      <div className="p-2">
        <label className="font-bold" htmlFor={name}>
          {name + " "}
        </label>
      </div>
      <div className="border rounded-md border-gray-300 p-1 px-2">
        <select
          id={name}
          name={name}
          className="focus:outline-none"
        >
          {options.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
