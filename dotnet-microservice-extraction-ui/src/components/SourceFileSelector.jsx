import { useState, useEffect } from 'react';

const flattenStructure = (structure, prefix = "") => {
  let files = [];
  Object.entries(structure).forEach(([key, value]) => {
    const currentPath = prefix ? `${prefix}/${key}` : key;
    if (value === "file") {
      const lower = key.toLowerCase();
      if (!(lower.endsWith(".css") || lower.endsWith(".js") || lower.endsWith(".map"))) {
        files.push(currentPath);
      }
    } else if (typeof value === "object") {
      files = files.concat(flattenStructure(value, currentPath));
    }
  });
  return files;
};

const SourceFileSelector = ({ selectedFiles = [], onChange }) => {
  const [options, setOptions] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [filteredOptions, setFilteredOptions] = useState([]);
  const [isFocused, setIsFocused] = useState(false);

  useEffect(() => {
    const storedResult = localStorage.getItem("analysis_result");
    if (storedResult) {
      const result = JSON.parse(storedResult);
      if (result.structure) {
        const flattened = flattenStructure(result.structure);
        setOptions(flattened);
        setFilteredOptions(flattened);
      }
    }
  }, []);

  const handleInputChange = (e) => {
    const text = e.target.value;
    setSearchText(text);
    const filtered = options.filter(opt =>
      opt.toLowerCase().includes(text.toLowerCase()) &&
      !selectedFiles.includes(opt)
    );
    setFilteredOptions(filtered);
  };

  const addFile = (file) => {
    const updated = [...selectedFiles, file];
    onChange(updated);
    // Retain the current searchText and update filtered options accordingly.
    setFilteredOptions(options.filter(opt =>
      opt.toLowerCase().includes(searchText.toLowerCase()) &&
      !updated.includes(opt)
    ));
  };

  const removeFile = (file) => {
    const updated = selectedFiles.filter(f => f !== file);
    onChange(updated);
    setFilteredOptions(options.filter(opt =>
      opt.toLowerCase().includes(searchText.toLowerCase()) &&
      !updated.includes(opt)
    ));
  };

  return (
    <div className="relative">
      <div className="flex flex-wrap gap-2 mb-2">
        {selectedFiles.map(file => (
          <div key={file} className="inline-flex items-center bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded-full">
            {file}
            <button 
              className="ml-1 text-blue-500 hover:text-blue-700" 
              onClick={() => removeFile(file)}
            >
              ×
            </button>
          </div>
        ))}
      </div>
      <input 
        type="text"
        value={searchText}
        onChange={handleInputChange}
        onFocus={() => setIsFocused(true)}
        onBlur={() =>
          setTimeout(() => {
            setIsFocused(false);
            setSearchText('');
            setFilteredOptions(options);
          }, 200)
        }
        placeholder="Search source files..."
        className="w-full p-2 border rounded-md text-sm"
      />
      {isFocused && filteredOptions.length > 0 && (
        <ul className="absolute z-10 w-full bg-white border border-gray-300 rounded-md mt-1 max-h-48 overflow-y-auto">
          {filteredOptions.map(opt => (
            <li 
              key={opt} 
              className="p-2 hover:bg-gray-100 cursor-pointer"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => addFile(opt)}
            >
              {opt}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SourceFileSelector;