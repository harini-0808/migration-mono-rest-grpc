import { useState } from "react";
import { HiDocument, HiChevronDown, HiChevronRight } from "react-icons/hi2";
import { FaMagic } from "react-icons/fa";
import SourceFileSelector from "./SourceFileSelector";
import axios from "../api/axios";

const ALLOWED_FILE_TYPES = [
       'controller',
        'config',
        'view',
        'model',
        'repository',
        ' interface',
        'layout',
        'razor_component',
        'service',
        'middleware',
        'program',
        'program_cs_grpc',
        'csproj',
        'ocelot',
        'csproj_grpc',
        'proto',
        'grpc_service_cs'

];


  const FileEditor = ({ name, data, onChange, onDelete }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChange = (field, value) => {
    onChange(field, value);
  };

  const handleGenerate = async (e) => {
    e.stopPropagation();
    setLoading(true);
    try {
      const response = await axios.post("/recommend", { file_name: name });
      if (response.data.status === "success") {
        const { description, file_type } = response.data.data;
        handleChange("description", description);
        handleChange("file_type", file_type);

        // Persist changes to local storage after AI recommendation
        const updatedData = { ...data, description: description, file_type: file_type };
        onChange(null, null, updatedData); // Notify parent to update state and persist
      } else {
        alert(response.data.detail || "Error generating recommendation.");
      }
    } catch (error) {
      alert("Error: " + error.message);
    }
    setLoading(false);
  };

  return (
    <>
      <div className="bg-white rounded-md mb-2 border border-gray-200">
        <div 
          className="flex items-center p-3 cursor-pointer hover:bg-gray-50"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 
            <HiChevronDown className="w-4 h-4 mr-2 text-gray-500" /> : 
            <HiChevronRight className="w-4 h-4 mr-2 text-gray-500" />
          }
          <HiDocument className="w-4 h-4 mr-2 text-gray-500" />
          <span className="font-medium text-sm">{name}</span>
          <button 
            onClick={(e) => { e.stopPropagation(); onDelete(); }} 
            className="ml-2 text-red-500 text-xs"
          >
            Delete
          </button>
        </div>
  
        {isExpanded && (
          <div className="p-3 border-t border-gray-200 bg-gray-50 relative">
            <button 
              onClick={handleGenerate}
              className="absolute top-2 right-2 bg-[#008597] hover:bg-[#007b8a] text-white px-2 py-1 text-xs rounded transition-colors duration-200"
              title="Generate content for description and file type"
            >
              <FaMagic className="inline mr-1" />
              Generate with AI
            </button>
            <div className="space-y-4 py-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={data.description || ''}
                  onChange={(e) => handleChange('description', e.target.value)}
                  className={`w-full p-2 border rounded-md text-sm ${loading ? "ai-shimmer" : ""}`}
                  rows="3"
                  placeholder="Enter file description..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Source Files
                </label>
                <div onClick={(e) => e.stopPropagation()}>
                  <SourceFileSelector 
                    selectedFiles={data.source_files || []}
                    onChange={(files) => handleChange('source_files', files)}
                  />
              </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Namespace
                </label>
                <input
                  type="text"
                  value={data.namespace || ''}
                  onChange={(e) => handleChange('namespace', e.target.value)}
                  className="w-full p-2 border rounded-md text-sm"
                  placeholder="Enter namespace..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  File Type
                </label>
                <div className="relative">
                  <select
                    value={data.file_type || ''}
                    onChange={(e) => handleChange('file_type', e.target.value)}
                    className={`appearance-none w-full p-2 border rounded-md text-sm ${loading ? "ai-shimmer" : ""} bg-white focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    <option value="" disabled>Select file type</option>
                    {ALLOWED_FILE_TYPES.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
  
      <style>{`
        @keyframes aiShimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
        .ai-shimmer {
          background: linear-gradient(90deg, #f0f0f0, #e0e0e0, #f0f0f0);
          background-size: 200% 100%;
          animation: aiShimmer 1.5s ease-in-out infinite;
        }
      `}</style>
    </>
  );
};

export default FileEditor;