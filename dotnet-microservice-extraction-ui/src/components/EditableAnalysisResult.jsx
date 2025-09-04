import { useState, useEffect } from 'react';
import { HiPencil } from 'react-icons/hi2';
import StructureEditor from './StructureEditor';
import { useNavigate } from 'react-router-dom';

const STORAGE_KEY = "editedMicroservices";

const EditableAnalysisResult = ({ projects, onSave }) => {
  // Now projects prop is a microservices array
  const [editedMicroservices, setEditedMicroservices] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [...projects];
  });
  const [selectedMicroservice, setSelectedMicroservice] = useState(0);
  const [selectedProject, setSelectedProject] = useState(0);
  const navigate = useNavigate();

  const handleChange = (msIndex, projectIndex, path, key, value, updatedData) => {
    // Deep clone the editedMicroservices array
    const updated = JSON.parse(JSON.stringify(editedMicroservices));
    let current = updated[msIndex].projects[projectIndex].target_structure;
    if (path && path.length > 0) {
      for (const segment of path) {
        // Ensure the segment exists
        if (!current[segment]) current[segment] = {};
        current = current[segment];
      }
      if (value === null) {
        delete current[key];
      } else {
        current[key] = value;
      }
    } else {
      // Apply updatedData directly at the top-level target_structure
      Object.assign(current, updatedData);
    }
    setEditedMicroservices(updated);
  };

  const handleSave = () => {
    // Persist updated microservices into localStorage using the defined key
    localStorage.setItem(STORAGE_KEY, JSON.stringify(editedMicroservices));
    if (onSave) {
      onSave(editedMicroservices);
    }
    alert("Changes saved successfully.");
    navigate("/");
  };

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(editedMicroservices));
  }, [editedMicroservices]);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mt-6">
      <div className="flex flex-col border-b border-gray-200">
        {/* Microservices tabs */}
        <div className="flex space-x-4">
          {editedMicroservices.map((ms, msIndex) => (
            <button
              key={ms.name}
              onClick={() => { setSelectedMicroservice(msIndex); setSelectedProject(0); }}
              className={`px-4 py-2 text-sm font-medium ${
                selectedMicroservice === msIndex
                  ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                  : 'text-gray-500 hover:bg-gray-50'
              }`}
            >
              {ms.name}
            </button>
          ))}
        </div>
        {/* Projects tabs within selected microservice */}
        <div className="mt-4   flex space-x-4">
          {editedMicroservices[selectedMicroservice].projects.map((project, idx) => (
            <button
              key={project.project_name}
              onClick={() => setSelectedProject(idx)}
              className={`px-4 py-2 text-sm font-medium ${
                selectedProject === idx
                  ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                  : 'text-gray-500 hover:bg-gray-50'
              }`}
            >
              {project.project_name}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-6">
        {editedMicroservices[selectedMicroservice] &&
          editedMicroservices[selectedMicroservice].projects[selectedProject] && (
            <StructureEditor
              structure={
                editedMicroservices[selectedMicroservice].projects[selectedProject].target_structure
              }
              onChange={(path, key, value, updatedData) =>
                handleChange(selectedMicroservice, selectedProject, path, key, value, updatedData)
              }
              path={[]} // Top-level editing
            />
          )}
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={handleSave}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <HiPencil className="w-5 h-5 mr-2" />
          Save Changes
        </button>
      </div>
    </div>
  );
};

export default EditableAnalysisResult;