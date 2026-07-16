import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiService } from '../services/apiService';
import { 
  Upload, 
  FileVideo, 
  Settings, 
  Play, 
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';

const UploadVideo: React.FC = () => {
  const navigate = useNavigate();
  
  // File states
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  
  // Pipeline configuration
  const [maxFrames, setMaxFrames] = useState(150);
  const [skipFrames, setSkipFrames] = useState(5);
  const [vehicleConfidence, setVehicleConfidence] = useState(0.35);
  const [ambulanceConfidence, setAmbulanceConfidence] = useState(0.35);

  // Operation progress states
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'failed'>('idle');
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    const supportedExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
    const suffix = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
    
    if (!supportedExtensions.includes(suffix)) {
      setErrorMessage(`Unsupported format. Upload one of: ${supportedExtensions.join(', ')}`);
      setStatus('failed');
      setFile(null);
      setVideoPreviewUrl(null);
      return;
    }

    setFile(selectedFile);
    setErrorMessage('');
    setStatus('idle');
    setVideoPreviewUrl(URL.createObjectURL(selectedFile));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleProcess = async () => {
    if (!file) return;
    
    try {
      setStatus('uploading');
      setProgress(0);
      setErrorMessage('');

      // 1. Upload Video
      const uploadRes = await ApiService.uploadVideo(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setProgress(percentCompleted);
      });

      // 2. Process Video
      setStatus('processing');
      const processRes = await ApiService.processVideo({
        video_name: uploadRes.filename,
        max_frames: maxFrames,
        skip_frames: skipFrames,
        vehicle_confidence: vehicleConfidence,
        ambulance_confidence: ambulanceConfidence
      });

      setStatus('success');
      
      // Delay navigation slightly so they see the success indicator
      setTimeout(() => {
        // Query results for the created process result timestamp
        const recordTimestamp = processRes.timestamp || new Date().toISOString();
        navigate(`/results?id=${encodeURIComponent(recordTimestamp)}`);
      }, 1500);

    } catch (error: any) {
      console.error(error);
      const detail = error.response?.data?.detail || 'An error occurred during video analysis. Try again.';
      setErrorMessage(detail);
      setStatus('failed');
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold text-white">Process Video</h1>
        <p className="text-slate-400 mt-1.5 text-sm font-medium">
          Upload traffic feed segments to extract real-time vehicle counts, density, and lane priorities.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        {/* Left pane: File Dropzone or Video Preview */}
        <div className="md:col-span-7 space-y-4">
          {!videoPreviewUrl ? (
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={triggerFileInput}
              className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center min-h-[350px] ${
                dragActive 
                  ? 'border-emerald-400 bg-emerald-500/5' 
                  : 'border-slate-800 bg-slate-900/30 hover:border-slate-700/60'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept="video/*"
                onChange={handleChange}
              />
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl shadow-inner mb-4">
                <Upload className="h-8 w-8 text-emerald-400" />
              </div>
              <h3 className="text-white font-bold text-base">Drag and drop file</h3>
              <p className="text-slate-400 text-xs mt-1.5 font-medium">
                Supports MP4, AVI, MOV, MKV, or WEBM up to 200MB
              </p>
              <button 
                type="button" 
                className="mt-6 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-colors"
              >
                Browse Folders
              </button>
            </div>
          ) : (
            <div className="border border-slate-800/80 bg-slate-900/40 rounded-2xl p-4 overflow-hidden relative shadow-lg">
              <video 
                src={videoPreviewUrl} 
                controls 
                className="w-full max-h-[350px] rounded-xl bg-black object-contain border border-slate-800"
              />
              <div className="flex items-center justify-between mt-4">
                <div className="flex items-center space-x-2.5">
                  <FileVideo className="h-5 w-5 text-emerald-400" />
                  <span className="text-xs font-semibold text-slate-200 block truncate max-w-[200px]">
                    {file?.name}
                  </span>
                </div>
                <button 
                  onClick={() => {
                    setFile(null);
                    setVideoPreviewUrl(null);
                    setStatus('idle');
                    setErrorMessage('');
                  }}
                  className="text-xs font-bold text-rose-400 hover:text-rose-300 hover:underline"
                  disabled={status === 'uploading' || status === 'processing'}
                >
                  Clear Selection
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right pane: Pipeline Configurations */}
        <div className="md:col-span-5">
          <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6 space-y-6">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center border-b border-slate-800 pb-3">
              <Settings className="mr-2 h-4 w-4 text-emerald-400" />
              Analysis Configuration
            </h3>

            {/* Max Frames */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                <span>Max Frame Count</span>
                <span className="text-slate-200 font-bold">{maxFrames}</span>
              </div>
              <input
                type="range"
                min="50"
                max="500"
                step="25"
                value={maxFrames}
                onChange={(e) => setMaxFrames(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                disabled={status === 'uploading' || status === 'processing'}
              />
              <p className="text-[10px] text-slate-500 font-medium">Limits total frames analyzed per video</p>
            </div>

            {/* Skip Frames */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                <span>Skip Frame Rate</span>
                <span className="text-slate-200 font-bold">{skipFrames}</span>
              </div>
              <input
                type="range"
                min="1"
                max="15"
                step="1"
                value={skipFrames}
                onChange={(e) => setSkipFrames(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                disabled={status === 'uploading' || status === 'processing'}
              />
              <p className="text-[10px] text-slate-500 font-medium">Increases processing speed by skipping frames (1 = no skip)</p>
            </div>

            {/* Vehicle Confidence */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                <span>Vehicle Detection Threshold</span>
                <span className="text-slate-200 font-bold">{Math.round(vehicleConfidence * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={vehicleConfidence}
                onChange={(e) => setVehicleConfidence(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                disabled={status === 'uploading' || status === 'processing'}
              />
            </div>

            {/* Ambulance Confidence */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                <span>Ambulance Confidence Threshold</span>
                <span className="text-slate-200 font-bold">{Math.round(ambulanceConfidence * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={ambulanceConfidence}
                onChange={(e) => setAmbulanceConfidence(Number(e.target.value))}
                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                disabled={status === 'uploading' || status === 'processing'}
              />
            </div>

            {/* Operation Progress Status */}
            {status !== 'idle' && (
              <div className="pt-4 border-t border-slate-800 space-y-3">
                {status === 'uploading' && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-bold text-emerald-400">
                      <span>Uploading to Server</span>
                      <span>{progress}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2">
                      <div className="bg-emerald-500 h-2 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
                    </div>
                  </div>
                )}

                {status === 'processing' && (
                  <div className="flex items-center justify-center p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-emerald-400 animate-pulse gap-2">
                    <Loader2 className="h-4.5 w-4.5 animate-spin text-emerald-400" />
                    <span>Running AI Object Detection Loop...</span>
                  </div>
                )}

                {status === 'success' && (
                  <div className="flex items-center p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400 gap-2">
                    <CheckCircle className="h-4.5 w-4.5" />
                    <span>Analysis Complete! Generating Report...</span>
                  </div>
                )}

                {status === 'failed' && (
                  <div className="flex items-start p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-medium text-rose-400 gap-2.5">
                    <AlertCircle className="h-5 w-5 text-rose-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold block">Run Failed</span>
                      <span className="text-rose-500/90 block mt-0.5">{errorMessage}</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Action Trigger Button */}
            <button
              onClick={handleProcess}
              disabled={!file || status === 'uploading' || status === 'processing' || status === 'success'}
              className={`w-full py-3.5 rounded-xl text-sm font-bold flex items-center justify-center transition-all ${
                !file 
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-transparent'
                  : 'bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-lg shadow-emerald-500/15'
              }`}
            >
              {status === 'uploading' || status === 'processing' ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Please Wait
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4 fill-current" />
                  Analyze Video
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadVideo;
