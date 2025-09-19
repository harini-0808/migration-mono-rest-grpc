// src/components/TokenUsage.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiX } from 'react-icons/fi';

const TokenUsage = () => {
  const navigate = useNavigate();
  const [tokenUsage, setTokenUsage] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const storedTokenUsage = localStorage.getItem('token_usage');
    if (!storedTokenUsage) {
      setError('No token usage data found. Please run a migration.');
      return;
    }
    setTokenUsage(JSON.parse(storedTokenUsage));
  }, []);

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="rounded-lg bg-red-50 p-4 border border-red-100 shadow-sm">
          <div className="flex items-start">
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
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!tokenUsage) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-8">
        <p className="text-sm text-gray-700">No token usage data available.</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Token Usage</h1>
        <button
          onClick={() => navigate('/')}
          className="text-blue-600 hover:text-blue-800"
        >
          ← Back to Analysis
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-100">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Summary</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className="flex items-start">
            <span className="text-sm font-medium text-gray-500 w-40">Total Tokens:</span>
            <span className="text-sm text-gray-700">{tokenUsage.total_tokens.toLocaleString()}</span>
          </div>
          <div className="flex items-start">
            <span className="text-sm font-medium text-gray-500 w-40">Total Prompt Tokens:</span>
            <span className="text-sm text-gray-700">{tokenUsage.total_prompt_tokens.toLocaleString()}</span>
          </div>
          <div className="flex items-start">
            <span className="text-sm font-medium text-gray-500 w-40">Total Response Tokens:</span>
            <span className="text-sm text-gray-700">{tokenUsage.total_response_tokens.toLocaleString()}</span>
          </div>
          <div className="flex items-start">
            <span className="text-sm font-medium text-gray-500 w-40">Total Requests:</span>
            <span className="text-sm text-gray-700">{tokenUsage.total_requests}</span>
          </div>
          <div className="flex items-start">
            <span className="text-sm font-medium text-gray-500 w-40">Avg Prompt Tokens/Request:</span>
            <span className="text-sm text-gray-700">{tokenUsage.average_prompt_tokens_per_request.toFixed(2)}</span>
          </div>
          <div className="flex items-start">
            <span className="text-sm font-medium text-gray-500 w-40">Avg Response Tokens/Request:</span>
            <span className="text-sm text-gray-700">{tokenUsage.average_response_tokens_per_request.toFixed(2)}</span>
          </div>
        </div>

        <h2 className="text-xl font-semibold text-gray-800 mb-4">Microservice Breakdown</h2>
        <div className="space-y-4 mb-6">
          {Object.entries(tokenUsage.microservice_stats).map(([msName, stats]) => (
            <div key={msName} className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-700">{msName}</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <div className="flex items-start">
                  <span className="text-sm font-medium text-gray-500 w-40">Total Tokens:</span>
                  <span className="text-sm text-gray-700">{(stats.prompt_tokens + stats.response_tokens).toLocaleString()}</span>
                </div>
                <div className="flex items-start">
                  <span className="text-sm font-medium text-gray-500 w-40">Prompt Tokens:</span>
                  <span className="text-sm text-gray-700">{stats.prompt_tokens.toLocaleString()}</span>
                </div>
                <div className="flex items-start">
                  <span className="text-sm font-medium text-gray-500 w-40">Response Tokens:</span>
                  <span className="text-sm text-gray-700">{stats.response_tokens.toLocaleString()}</span>
                </div>
                <div className="flex items-start">
                  <span className="text-sm font-medium text-gray-500 w-40">Requests:</span>
                  <span className="text-sm text-gray-700">{stats.requests}</span>
                </div>
                <div className="flex items-start">
                  {/* <span className="text-sm font-medium text-gray-500 w-40">Files Processed:</span>
                  <span className="text-sm text-gray-700">{stats.files_processed}</span> */}
                </div>
              </div>
            </div>
          ))}
        </div>

        <h2 className="text-xl font-semibold text-gray-800 mb-4">Top Consuming Files</h2>
        <div className="space-y-2">
          {tokenUsage.top_consuming_files.map(([fileName, tokens], index) => (
            <div key={index} className="flex items-center justify-between border-b border-gray-100 py-2">
              <span className="text-sm text-gray-700">{fileName}</span>
              <span className="text-sm text-gray-500">{tokens.toLocaleString()} tokens</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TokenUsage;