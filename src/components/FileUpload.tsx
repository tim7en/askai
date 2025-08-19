'use client';


import { useState, useRef } from 'react';
import { FileData, AnalysisResult } from '@/types';
import { processFiles, formatFileSize } from '@/lib/file-utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function FileUpload() {
  const [files, setFiles] = useState<FileData[]>([]);
  const [prompt, setPrompt] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState<number | null>(null);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    try {
      const fileData = await processFiles(selectedFiles);
      setFiles(fileData);
      setError('');
    } catch (err) {
      setError('Failed to process files');
      console.error(err);
    }
  };

  const handleAnalyze = async () => {
    if (files.length === 0) {
      setError('Please select files first');
      return;
    }
    if (!prompt.trim()) {
      setError('Please enter an analysis prompt');
      return;
    }
    setIsAnalyzing(true);
    setError('');
    setResults([]);
    setProgress(0);
    setCurrentFile(null);

    const delay = (ms: number) => new Promise(res => setTimeout(res, ms));
    const newResults: AnalysisResult[] = [];
    for (let i = 0; i < files.length; i++) {
      setCurrentFile(i);
      try {
        const response = await fetch('/api/analyze', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            files: [files[i]],
            prompt: prompt.trim()
          }),
        });
        const data = await response.json();
        if (data.success && data.results && data.results[0]) {
          newResults.push(data.results[0]);
        } else {
          newResults.push({
            fileName: files[i].name,
            filePath: files[i].path,
            analysis: data.error || 'Analysis failed',
            metadata: {
              size: files[i].size,
              type: files[i].type
            }
          });
        }
      } catch (err) {
        newResults.push({
          fileName: files[i].name,
          filePath: files[i].path,
          analysis: 'Failed to analyze file',
          metadata: {
            size: files[i].size,
            type: files[i].type
          }
        });
      }
      setResults([...newResults]);
      setProgress(Math.round(((i + 1) / files.length) * 100));
      await delay(1200); // 1.2s delay between requests
    }
    setCurrentFile(null);
    setIsAnalyzing(false);
  };

  const clearFiles = () => {
    setFiles([]);
    setResults([]);
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (folderInputRef.current) folderInputRef.current.value = '';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">File Upload</h2>
        
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Files
              </label>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={(e) => handleFileSelect(e.target.files)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Folder
              </label>
              <input
                ref={folderInputRef}
                type="file"
                /* @ts-expect-error - webkitdirectory is not in the standard TypeScript definitions */
                webkitdirectory=""
                directory=""
                onChange={(e) => handleFileSelect(e.target.files)}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-green-50 file:text-green-700 hover:file:bg-green-100"
              />
            </div>
          </div>

          {files.length > 0 && (
            <div className="border rounded-lg p-4 bg-gray-50">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">Selected Files ({files.length})</h3>
                <button
                  onClick={clearFiles}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Clear All
                </button>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {files.map((file, index) => (
                  <div key={index} className="flex justify-between items-center text-sm">
                    <span className="truncate flex-1" title={file.path}>
                      {file.path}
                    </span>
                    <span className="text-gray-500 ml-2">
                      {formatFileSize(file.size)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Analysis Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your analysis request (e.g., 'Analyze the code quality and suggest improvements', 'Summarize the main functions and their purposes', 'Find potential security issues')"
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={4}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing || files.length === 0 || !prompt.trim()}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium"
          >
            {isAnalyzing ? 'Analyzing Files...' : 'Analyze Files'}
          </button>

          {isAnalyzing && (
            <div className="w-full mt-4">
              <div className="flex justify-between mb-1">
                <span className="text-sm text-blue-700 font-medium">Processing files...</span>
                <span className="text-sm text-blue-700 font-medium">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              {currentFile !== null && files[currentFile] && (
                <div className="text-xs text-gray-500 mt-2">Analyzing: {files[currentFile].path}</div>
              )}
            </div>
          )}
        </div>
      </div>

      {results.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">Analysis Results</h2>
          <div className="space-y-6">
            {results.map((result, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-semibold text-gray-800">
                    {result.fileName}
                  </h3>
                  <span className="text-sm text-gray-500">
                    {formatFileSize(result.metadata.size)}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">{result.filePath}</p>
                <div className="bg-gray-50 rounded-md p-4">
                  <div className="prose prose-sm max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        img: ({node, ...props}) => (
                          <img {...props} style={{ maxWidth: '100%', height: 'auto' }} />
                        )
                      }}
                    >
                      {result.analysis}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
