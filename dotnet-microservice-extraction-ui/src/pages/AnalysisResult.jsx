import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// Removed unused axios import
import EditableAnalysisResult from '../components/EditableAnalysisResult';

const AnalysisResult = () => {
  const navigate = useNavigate();
  // Removed error state if not needed
  const [result, setResult] = useState(null);

  const handleStartNew = () => {
    localStorage.clear();
    navigate('/');
  };

  useEffect(() => {
    const storedResult = localStorage.getItem('analysis_result');
    const repoUrl = localStorage.getItem('repo_url');
    const targetFramework = localStorage.getItem('target_version');

    if (!storedResult) {
      navigate('/');
      return;
    }

    setResult({
      ...JSON.parse(storedResult),
      repo_url: repoUrl,
      target_framework: targetFramework
    });
  }, [navigate]);

  // Updated handleSave: now update microservices within the target structure
  const handleSave = (updatedMicroservices) => {
    console.log("Updated microservices:", updatedMicroservices);
    const updatedResult = {
      ...result,
      target_structure: {
        microservices: updatedMicroservices
      }
    };
    setResult(updatedResult);
    localStorage.setItem("analysis_result", JSON.stringify(updatedResult));
    alert("Changes saved successfully.");
  };

  if (!result) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analysis Result</h1>
        <div className="flex space-x-4">
          <button
            onClick={handleStartNew}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            Start New Analysis
          </button>
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:text-blue-800"
          >
            ← Back to Analysis
          </button>
        </div>
      </div>

      {/* Repository Info */}
      <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
        <div className="space-y-2">
          <div className="flex items-center">
            <span className="text-sm font-medium text-gray-500 w-32">Repository URL:</span>
            <span className="text-sm text-gray-900">{result.repo_url}</span>
          </div>
          <div className="flex items-center">
            <span className="text-sm font-medium text-gray-500 w-32">Target Framework:</span>
            <span className="text-sm text-gray-900">{result.target_framework}</span>
          </div>
        </div>
      </div>

      {/* Editable Analysis Result */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <EditableAnalysisResult
          projects={result.target_structure.microservices}
          onSave={handleSave}
        />
      </div>
    </div>
  );
};

export default AnalysisResult;