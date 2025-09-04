import { useState } from "react";
import { HiFolder, HiChevronDown, HiChevronRight } from "react-icons/hi2";
import FileEditor from './FileEditor';

const StructureEditor = ({ structure = {}, onChange, path = [] }) => {
  const [newFileName, setNewFileName] = useState("");
  const [newFolderName, setNewFolderName] = useState("");

  const handleAddFile = () => {
    if (newFileName.trim() === "") return;
    const newFileData = {
      description: "",
      source_files: [],
      namespace: "",
      file_type: ""
    };
    onChange([...path, "root"], newFileName, newFileData);
    setNewFileName("");
  };

  const handleAddFolder = () => {
    if (newFolderName.trim() === "") return;
    const newFolderData = {
      target_files: {},
      subfolders: {}
    };
    onChange([...path, "folders"], newFolderName, newFolderData);
    setNewFolderName("");
  };

  const FolderNode = ({ folderName, folderData, currentPath }) => {
    const [expanded, setExpanded] = useState(false);
    const [newChildFile, setNewChildFile] = useState("");
    const [newChildFolder, setNewChildFolder] = useState("");

    const toggleFolder = () => {
      setExpanded(!expanded);
    };

    const handleAddChildFile = () => {
      if (newChildFile.trim() === "") return;
      const newFileData = {
        description: "",
        source_files: [],
        namespace: "",
        file_type: ""
      };
      onChange([...currentPath, folderName, "target_files"], newChildFile, newFileData);
      setNewChildFile("");
    };

    const handleAddChildFolder = () => {
      if (newChildFolder.trim() === "") return;
      const newFolderData = {
        target_files: {},
        subfolders: {}
      };
      onChange([...currentPath, folderName, "subfolders"], newChildFolder, newFolderData);
      setNewChildFolder("");
    };

    const handleDeleteFolder = () => {
      onChange(currentPath, folderName, null);
    };

    // Function to determine if an object is likely a file rather than a folder structure
    const isFile = (obj) => {
      return obj && (
        Object.prototype.hasOwnProperty.call(obj, "description") || 
        Object.prototype.hasOwnProperty.call(obj, "file_type") || 
        Object.prototype.hasOwnProperty.call(obj, "namespace") ||
        Object.prototype.hasOwnProperty.call(obj, "source_files")
      );
    };

    return (
      <div className="mb-4">
        <div
          className="flex items-center cursor-pointer hover:bg-gray-50 p-2 rounded"
          onClick={toggleFolder}
        >
          {expanded ?
            <HiChevronDown className="w-4 h-4 mr-2 text-gray-500" /> :
            <HiChevronRight className="w-4 h-4 mr-2 text-gray-500" />
          }
          <HiFolder className="w-4 h-4 mr-2 text-gray-500" />
          <span className="font-medium">{folderName}</span>
          <button onClick={(e) => { e.stopPropagation(); handleDeleteFolder(); }} className="ml-2 text-red-500 text-xs">Delete</button>
        </div>

        {expanded && (
          <div className="ml-6">
            {/* Files in folder */}
            {Object.entries(folderData.target_files || {}).map(([fileName, fileData]) => (
              <FileEditor
                key={fileName}
                name={fileName}
                data={fileData}
                onChange={(key, value, updatedData) => {
                  onChange([...currentPath, folderName, "target_files"], fileName, updatedData || { ...fileData, [key]: value });
                }}
                onDelete={() =>
                  onChange([...currentPath, folderName, "target_files"], fileName, null)
                }
              />
            ))}

            {/* Handle files that might be directly in the folder object */}
            {Object.entries(folderData).filter(([key, value]) => 
              key !== "target_files" && key !== "subfolders" && isFile(value)
            ).map(([fileName, fileData]) => (
              <FileEditor
                key={fileName}
                name={fileName}
                data={fileData}
                onChange={(key, value, updatedData) => {
                  onChange([...currentPath, folderName], fileName, updatedData || { ...fileData, [key]: value });
                }}
                onDelete={() =>
                  onChange([...currentPath, folderName], fileName, null)
                }
              />
            ))}

            {/* Add new file in folder */}
            <div className="mt-2 flex items-center">
              <input
                type="text"
                value={newChildFile}
                onChange={(e) => setNewChildFile(e.target.value)}
                placeholder="New file name..."
                className="p-1 border rounded text-sm"
              />
              <button onClick={handleAddChildFile} className="ml-2 text-blue-600 text-sm">Add File</button>
            </div>

            {/* Add new subfolder in folder */}
            <div className="mt-2 flex items-center">
              <input
                type="text"
                value={newChildFolder}
                onChange={(e) => setNewChildFolder(e.target.value)}
                placeholder="New folder name..."
                className="p-1 border rounded text-sm"
              />
              <button onClick={handleAddChildFolder} className="ml-2 text-blue-600 text-sm">Add Folder</button>
            </div>

            {/* Render subfolders */}
            {Object.entries(folderData.subfolders || {}).map(([subFolderName, subFolderData]) => (
              <FolderNode
                key={subFolderName}
                folderName={subFolderName}
                folderData={subFolderData}
                currentPath={[...currentPath, folderName, "subfolders"]}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="ml-4 border-l-2 border-gray-100 pl-4">
      {/* Root Files */}
      {structure.root && (
        <div className="mb-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Root Files</h3>
          {Object.entries(structure.root).map(([fileName, fileData]) => (
            <FileEditor
              key={fileName}
              name={fileName}
              data={fileData}
              onChange={(key, value, updatedData) => {
                onChange([...path, "root"], fileName, updatedData || { ...fileData, [key]: value });
              }}
              onDelete={() =>
                onChange([...path, "root"], fileName, null)
              }
            />
          ))}
          <div className="mt-2 flex items-center">
            <input
              type="text"
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              placeholder="New root file name..."
              className="p-1 border rounded text-sm"
            />
            <button onClick={handleAddFile} className="ml-2 text-blue-600 text-sm">
              Add File
            </button>
          </div>
        </div>
      )}

      {/* Folders */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-2">Folders</h3>
        {Object.entries(structure.folders || {}).map(([folderName, folderData]) => (
          <FolderNode
            key={folderName}
            folderName={folderName}
            folderData={folderData}
            currentPath={[...path, "folders"]}
          />
        ))}
        <div className="mt-2 flex items-center">
          <input
            type="text"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="New folder name..."
            className="p-1 border rounded text-sm"
          />
          <button onClick={handleAddFolder} className="ml-2 text-blue-600 text-sm">
            Add Folder
          </button>
        </div>
      </div>
    </div>
  );
};

export default StructureEditor;