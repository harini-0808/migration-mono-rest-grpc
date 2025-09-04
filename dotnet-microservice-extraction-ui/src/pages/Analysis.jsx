import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { FiChevronRight, FiChevronDown, FiX } from "react-icons/fi";
import { FaFolder, FaFile } from "react-icons/fa";
import axios from "../api/axios";

const ProjectStructureView = ({ structure }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [activeFile, setActiveFile] = useState(null);

  const toggleFolder = (path) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedNodes(newExpanded);
  };

  const toggleFileDetails = (path) => {
    if (activeFile === path) {
      setActiveFile(null);
    } else {
      setActiveFile(path);
    }
  };

  const renderStructure = (data, currentPath = "") => {
    if (!data) return null;

    const folders = data.folders || data.subfolders || {};
    const files =
      Object.keys(data.files || {}).length > 0
        ? data.files
        : data.target_files || {};
    const rootFiles = data.root || {};

    const isFile = (obj) => {
      return (
        obj &&
        (Object.prototype.hasOwnProperty.call(obj, "description") ||
          Object.prototype.hasOwnProperty.call(obj, "file_type") ||
          Object.prototype.hasOwnProperty.call(obj, "namespace") ||
          Object.prototype.hasOwnProperty.call(obj, "source_files"))
      );
    };

    const fileElements = Object.entries(files).map(([fileName]) => {
      const filePath = currentPath ? `${currentPath}/${fileName}` : fileName;
      const isActive = activeFile === filePath;
      return (
        <div
          key={filePath}
          className={`flex items-center py-1 px-2 ${currentPath ? "ml-4" : ""} hover:bg-blue-50 rounded cursor-pointer transition-colors duration-200 ${isActive ? "ring-2 ring-blue-200" : ""}`}
          onClick={() => toggleFileDetails(filePath)}
        >
          <span className="w-4" />
          <FaFile className="h-5 w-5 text-gray-400 mr-2" />
          <span className="text-sm text-gray-700">{fileName}</span>
        </div>
      );
    });

    const embeddedFileElements = Object.entries(data)
      .filter(
        ([key, value]) =>
          key !== "target_files" &&
          key !== "subfolders" &&
          key !== "folders" &&
          key !== "root" &&
          isFile(value)
      )
      .map(([fileName]) => {
        const filePath = currentPath ? `${currentPath}/${fileName}` : fileName;
        const isActive = activeFile === filePath;
        return (
          <div
            key={filePath}
            className={`flex items-center py-1 px-2 ${currentPath ? "ml-4" : ""} hover:bg-blue-50 rounded cursor-pointer transition-colors duration-200 ${isActive ? "ring-2 ring-blue-200" : ""}`}
            onClick={() => toggleFileDetails(filePath)}
          >
            <span className="w-4" />
            <FaFile className="h-5 w-5 text-gray-400 mr-2" />
            <span className="text-sm text-gray-700">{fileName}</span>
          </div>
        );
      });

    const rootFileElements = Object.entries(rootFiles).map(([fileName]) => {
      const filePath = currentPath ? `${currentPath}/${fileName}` : fileName;
      const isActive = activeFile === filePath;
      return (
        <div
          key={filePath}
          className={`flex items-center py-1 px-2 hover:bg-blue-50 rounded cursor-pointer transition-colors duration-200 ${isActive ? "ring-2 ring-blue-200" : ""}`}
          onClick={() => toggleFileDetails(filePath)}
        >
          <span className="w-4" />
          <FaFile className="h-5 w-5 text-gray-400 mr-2" />
          <span className="text-sm text-gray-700">{fileName}</span>
        </div>
      );
    });

    const folderElements = Object.entries(folders).map(
      ([folderName, folderData]) => {
        const folderPath = currentPath ? `${currentPath}/${folderName}` : folderName;
        const isExpanded = expandedNodes.has(folderPath);

        return (
          <div key={folderPath} className="ml-4">
            <div
              className="flex items-center py-1 px-2 hover:bg-blue-50 rounded cursor-pointer transition-colors duration-200"
              onClick={() => toggleFolder(folderPath)}
            >
              {isExpanded ? (
                <FiChevronDown className="h-4 w-4 text-blue-600 mr-1" />
              ) : (
                <FiChevronRight className="h-4 w-4 text-blue-600 mr-1" />
              )}
              <FaFolder className="h-5 w-5 text-blue-500 mr-2" />
              <span className="text-sm text-gray-700">{folderName}</span>
            </div>
            {isExpanded && (
              <div className="ml-4 border-l border-blue-100 pl-2">
                {renderStructure(folderData, folderPath)}
              </div>
            )}
          </div>
        );
      }
    );

    return (
      <>
        {rootFileElements}
        {fileElements}
        {embeddedFileElements}
        {folderElements}
      </>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
      <div className="divide-y divide-gray-100">{renderStructure(structure)}</div>

      {activeFile &&
        (() => {
          const pathSegments = activeFile.split("/");
          let fileDetails = null;
          let current = structure;

          const isFile = (obj) => {
            return (
              obj &&
              (Object.prototype.hasOwnProperty.call(obj, "description") ||
                Object.prototype.hasOwnProperty.call(obj, "file_type") ||
                Object.prototype.hasOwnProperty.call(obj, "namespace") ||
                Object.prototype.hasOwnProperty.call(obj, "source_files"))
            );
          };

          if (
            pathSegments.length === 1 &&
            structure.root &&
            structure.root[pathSegments[0]]
          ) {
            fileDetails = structure.root[pathSegments[0]];
          } else {
            for (let i = 0; i < pathSegments.length; i++) {
              const seg = pathSegments[i];
              if (!current) break;

              if (i === pathSegments.length - 1) {
                if (current.files && current.files[seg]) {
                  fileDetails = current.files[seg];
                } else if (current.target_files && current.target_files[seg]) {
                  fileDetails = current.target_files[seg];
                } else if (current[seg] && isFile(current[seg])) {
                  fileDetails = current[seg];
                }
              } else {
                if (current.folders && current.folders[seg]) {
                  current = current.folders[seg];
                } else if (current.subfolders && current.subfolders[seg]) {
                  current = current.subfolders[seg];
                } else {
                  current = null;
                  break;
                }
              }
            }
          }

          return fileDetails ? (
            <div className="ml-4 mt-4 mb-4 bg-blue-50 rounded-lg border border-blue-100 p-4 animate-fadeIn">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-blue-700">File Details</h3>
                  <button
                    onClick={() => setActiveFile(null)}
                    className="p-1 hover:bg-blue-100 rounded-full transition-colors duration-150"
                  >
                    <FiX className="h-4 w-4 text-blue-600" />
                  </button>
                </div>

                <div className="grid gap-2 text-sm">
                  {fileDetails.description && (
                    <div className="flex items-start">
                      <span className="text-gray-500 w-28 flex-shrink-0">
                        Description:
                      </span>
                      <span className="text-gray-700">
                        {fileDetails.description}
                      </span>
                    </div>
                  )}
                  {fileDetails.namespace && (
                    <div className="flex items-start">
                      <span className="text-gray-500 w-28 flex-shrink-0">
                        Namespace:
                      </span>
                      <span className="text-gray-700">
                        {fileDetails.namespace}
                      </span>
                    </div>
                  )}
                  {fileDetails.file_type && (
                    <div className="flex items-start">
                      <span className="text-gray-500 w-28 flex-shrink-0">
                        Type:
                      </span>
                      <span className="text-gray-700">
                        {fileDetails.file_type}
                      </span>
                    </div>
                  )}
                  {fileDetails.source_files &&
                    fileDetails.source_files.length > 0 && (
                      <div className="flex items-start">
                        <span className="text-gray-500 w-28 flex-shrink-0">
                          Source Files:
                        </span>
                        <ul className="text-gray-700 list-disc list-inside">
                          {fileDetails.source_files.map((src, index) => (
                            <li key={index}>{src}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                </div>
              </div>
            </div>
          ) : null;
        })()}
    </div>
  );
};

const Analysis = () => {
  const navigate = useNavigate();
  const [repoUrl, setRepoUrl] = useState("");
  const [zipFile, setZipFile] = useState(null);
  const [sourceType, setSourceType] = useState("git");
  const [targetVersion, setTargetVersion] = useState("net6.0");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasExistingAnalysis, setHasExistingAnalysis] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [activeProject, setActiveProject] = useState(0);
  const [isStructureVisible, setIsStructureVisible] = useState(false);
  const initialZipName = zipFile ? zipFile.name : "No file selected";
  const [zipName, setZipName] = useState(initialZipName);
  const [isMigrating, setIsMigrating] = useState(false);
  const [instruction, setInstruction] = useState("");
  const [activeMicroservice, setActiveMicroservice] = useState(0);
  const [apiType, setApiType] = useState("rest");

  useEffect(() => {
    const analysisId = localStorage.getItem("analysis_id");
    const savedResult = localStorage.getItem("analysis_result");
    setHasExistingAnalysis(!!analysisId);
    if (savedResult) {
      setAnalysisResult(JSON.parse(savedResult));
    }
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      if (e.target.tagName === "TEXTAREA" && e.shiftKey) return;
      e.preventDefault();
      if (analysisResult) {
        handleMigrate();
      } else {
        handleSubmit(e);
      }
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.zip')) {
      setZipFile(file);
      setZipName(file.name);
      setError("");
    } else {
      setZipFile(null);
      setZipName("No file selected");
      setError("Please select a valid ZIP file");
    }
  };

  const handleMigrate = async () => {
    setIsMigrating(true);
    try {
      const response = await axios.post(
        "/migrate",
        {
          analysis_id: analysisResult.analysis_id,
          target_structure: analysisResult.target_structure,
        },
        { responseType: "blob" }
      );

      const blob = new Blob([response.data], { type: "application/zip" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");

      const disposition = response.headers["content-disposition"];
      let fileName = "download.zip";
      if (disposition && disposition.indexOf("filename=") !== -1) {
        const fileNameMatch = disposition.match(/filename="?([^"]+)"?/);
        if (fileNameMatch && fileNameMatch.length === 2) {
          fileName = fileNameMatch[1];
        }
      }

      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      alert("Migration successful!");
    } catch (err) {
      alert(err.response?.data?.detail || err.message || "Migration failed");
    } finally {
      setIsMigrating(false);
    }
  };

  const handleStartNew = () => {
    localStorage.clear();
    setHasExistingAnalysis(false);
    setAnalysisResult(null);
    setRepoUrl("");
    setZipFile(null);
    setZipName("No file selected");
    setSourceType("git");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("target_version", targetVersion);
      formData.append("api_type", apiType);
      formData.append("instruction", instruction);
      formData.append("source_type", sourceType);
      if (sourceType === "git") {
        if (!repoUrl) {
          throw new Error("Repository URL is required for git source type");
        }
        formData.append("repo_url", repoUrl);
      } else if (sourceType === "zip") {
        if (!zipFile) {
          throw new Error("ZIP file is required for zip source type");
        }
        formData.append("zip_file", zipFile);
      }

      const response = await axios.post("/analyze", formData, {
        headers: {
        "Content-Type": sourceType === "zip" ? "multipart/form-data" : "application/x-www-form-urlencoded",
        },
      });

      const result = response.data.data;
      localStorage.setItem("analysis_id", result.analysis_id);
      localStorage.setItem("target_version", result.target_version);
      localStorage.setItem("repo_url", result.repo_url);
      localStorage.setItem("analysis_result", JSON.stringify(result));
      setIsStructureVisible(true);

      setAnalysisResult(result);
      setHasExistingAnalysis(true);
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          const errorMessages = detail
            .map((d) => `${d.loc.join(".")}: ${d.msg}`)
            .join(", ");
          setError(errorMessages);
        } else {
          setError(detail);
        }
      } else {
        setError(err.message || "Failed to analyze repository");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 ">
      {hasExistingAnalysis && (
        <div className="bg-blue-50 border border-blue-100 rounded-lg py-3 px-4 mb-8 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between">
            <div className="mb-4 sm:mb-0">
              <h2 className="text-lg font-semibold text-blue-800">
                Analysis Result Available
              </h2>
              <p className="text-sm text-blue-600">
                Review and edit the target structure if needed before migration.
              </p>
            </div>
            <div className="flex space-x-3 w-full sm:w-auto">
              <button
                onClick={() => navigate("/result")}
                className="flex-1 sm:flex-none inline-flex items-center justify-center px-3 py-1 rounded-lg text-white bg-blue-600 hover:bg-blue-700 transition-colors"
              >
                Edit Target Structure
              </button>
              <button
                onClick={() => {
                  const storedResult = localStorage.getItem("analysis_result");
                  if (storedResult) {
                    setAnalysisResult(JSON.parse(storedResult));
                  }
                  setIsStructureVisible(true);
                }}
                className="flex-1 sm:flex-none inline inline-flex items-center justify-center px-3 py-1 rounded-lg text-blue-700 bg-white border border-blue-200 hover:bg-blue-50 transition-colors"
              >
                Show Target Structure
              </button>
              <button
                onClick={handleStartNew}
                className="flex-1 sm:flex-none inline-flex items-center justify-center px-3 py-1 rounded-lg text-blue-700 bg-white border border-blue-200 hover:bg-blue-50 transition-colors"
              >
                Start New
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-lg p-8 space-y-8 border border-gray-100">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            Project Analysis
          </h1>
        </div>

        <form
          onSubmit={handleSubmit}
          onKeyDown={handleKeyDown}
          className="space-y-6"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Source Type
            </label>
            <div className="flex space-x-6">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="sourceType"
                  value="git"
                  checked={sourceType === "git"}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  disabled={hasExistingAnalysis}
                />
                <span className="ml-2 text-sm text-gray-700">Git Repository</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="sourceType"
                  value="zip"
                  checked={sourceType === "zip"}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  disabled={hasExistingAnalysis}
                />
                <span className="ml-2 text-sm text-gray-700">ZIP File</span>
              </label>
            </div>
          </div>

          {sourceType === "git" ? (
            <div>
              <label
                htmlFor="repoUrl"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Repository URL
              </label>
              <input
                id="repoUrl"
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/username/repository"
                className="block w-full px-4 py-3 border border-gray-200 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-150"
                disabled={hasExistingAnalysis}
              />
            </div>
          ) : (
            <div>
              <label
                htmlFor="zipFile"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                ZIP File
              </label>
              <div className="flex items-center">
                <input
                  id="zipFile"
                  type="file"
                  accept=".zip"
                  onChange={handleFileChange}
                  className="block w-full px-4 py-3 border border-gray-200 rounded-lg shadow-sm text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 transition duration-150"
                  disabled={hasExistingAnalysis}
                />
                <span className="ml-4 text-sm text-gray-500">{zipName}</span>
              </div>
            </div>
          )}

          <div>
            <label
              htmlFor="targetVersion"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Target .NET Version
            </label>
            <select
              id="targetVersion"
              value={targetVersion}
              onChange={(e) => setTargetVersion(e.target.value)}
              className="block w-full px-4 py-3 border border-gray-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-150"
              disabled={hasExistingAnalysis}
            >
              <option value="net6.0">.NET 6.0</option>
              <option value="net7.0">.NET 7.0</option>
              <option value="net8.0">.NET 8.0</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Type
            </label>
            <div className="flex space-x-6">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="apiType"
                  value="rest"
                  checked={apiType === "rest"}
                  onChange={(e) => setApiType(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  disabled={hasExistingAnalysis}
                />
                <span className="ml-2 text-sm text-gray-700">REST</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="apiType"
                  value="grpc"
                  checked={apiType === "grpc"}
                  onChange={(e) => setApiType(e.target.value)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  disabled={hasExistingAnalysis}
                />
                <span className="ml-2 text-sm text-gray-700">gRPC</span>
              </label>
            </div>
          </div>

          <div>
            <label
              htmlFor="instruction"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              Instructions
            </label>
            <textarea
              id="instruction"
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="Enter instructions..."
              className="block w-full px-4 py-3 border border-gray-200 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition duration-150"
              rows="4"
            />
          </div>

          <div className="space-y-4">
            <button
              type="submit"
              disabled={
                isLoading ||
                (sourceType === "git" && !repoUrl) ||
                (sourceType === "zip" && !zipFile) ||
                hasExistingAnalysis
              }
              className={`w-full flex items-center justify-center py-3 px-4 rounded-lg shadow-sm text-sm font-medium transition duration-150
                        ${
                          isLoading ||
                          (sourceType === "git" && !repoUrl) ||
                          (sourceType === "zip" && !zipFile) ||
                          hasExistingAnalysis
                            ? "bg-blue-300 cursor-not-allowed text-white/80"
                            : "bg-blue-600 hover:bg-blue-700 text-white hover:shadow-md"
                        }`}
            >
              {isLoading ? (
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/20 border-t-white"></div>
                  <span>Analyzing Repository...</span>
                </div>
              ) : (
                "Start Analysis"
              )}
            </button>

            {analysisResult && (
              <button
                type="button"
                onClick={handleMigrate}
                disabled={isMigrating}
                className={`w-full flex items-center justify-center py-3 px-4 rounded-lg shadow-sm text-sm font-medium transition duration-150
                  ${
                    isMigrating
                      ? "bg-[#82c9d2] cursor-not-allowed text-white/80"
                      : "bg-[#008597] hover:bg-[#007b8a] text-white hover:shadow-md"
                  }`}
              >
                {isMigrating ? (
                  <div className="flex items-center space-x-3">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/20 border-t-white"></div>
                    <span>Migrating...</span>
                  </div>
                ) : (
                  "Migrate Project"
                )}
              </button>
            )}
          </div>
        </form>

        {error && (
          <div className="rounded-lg bg-red-50 p-4 border border-red-100 shadow-sm">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {isStructureVisible && analysisResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-6">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-7xl max-h-[90vh] overflow-y-auto transform transition-all duration-300">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">
                Project Structure Analysis
              </h2>
              <button
                onClick={() => setIsStructureVisible(false)}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors duration-150"
              >
                <FiX className="h-6 w-6 text-gray-500" />
              </button>
            </div>
            <div className="flex h-[calc(90vh-80px)]">
              <div className="w-1/3 border-r border-gray-200 p-6 space-y-4 overflow-y-auto">
                {analysisResult.target_structure.microservices.map(
                  (ms, msIndex) => (
                    <div key={msIndex} className="space-y-2">
                      <div
                        onClick={() => {
                          setActiveMicroservice(msIndex);
                          setActiveProject(0);
                        }}
                        className={`cursor-pointer font-bold text-xl pb-1 border-b ${activeMicroservice === msIndex ? "text-blue-600 border-blue-600" : "text-gray-700 border-transparent"}`}
                      >
                        {ms.name}
                      </div>
                      {activeMicroservice === msIndex && (
                        <div className="ml-4 space-y-1">
                          {ms.projects.map((project, projIndex) => (
                            <div
                              key={projIndex}
                              onClick={() => setActiveProject(projIndex)}
                              className={`cursor-pointer p-2 rounded transition-colors duration-150 ${activeProject === projIndex ? "bg-blue-100 text-blue-600" : "hover:bg-gray-100 text-gray-700"}`}
                            >
                              {project.project_name}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                )}
              </div>
              <div className="w-2/3 p-6 overflow-y-auto">
                <ProjectStructureView
                  structure={
                    analysisResult.target_structure.microservices[
                      activeMicroservice
                    ].projects[activeProject].target_structure
                  }
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analysis;