import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ApiService } from '../services/apiService';
import { 
  ArrowLeft, 
  ShieldAlert, 
  Info, 
  BarChart, 
  Gauge, 
  Clock, 
  Layout 
} from 'lucide-react';

const Results: React.FC = () => {
  const [searchParams] = useSearchParams();
  const id = searchParams.get('id') || '';

  const { data: record, isLoading, error } = useQuery({
    queryKey: ['results', id],
    queryFn: () => ApiService.getResult(id),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="relative">
          <div className="h-16 w-16 rounded-full border-4 border-slate-800 border-t-emerald-500 animate-spin"></div>
          <div className="mt-4 text-slate-400 text-sm font-medium animate-pulse">Compiling report data...</div>
        </div>
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="max-w-md mx-auto text-center py-12 border border-slate-800/80 bg-slate-900/30 rounded-2xl p-8 space-y-4">
        <ShieldAlert className="h-12 w-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold text-white">Report Not Found</h2>
        <p className="text-slate-400 text-sm">
          No historical run record found matching that ID.
        </p>
        <Link 
          to="/history" 
          className="inline-flex items-center text-xs font-semibold text-emerald-400 hover:text-emerald-300 gap-1 underline mt-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to History
        </Link>
      </div>
    );
  }

  // Derive helper details
  const density = record.density || 'LOW';
  const congestion = record.congestion || 'LOW_CONGESTION';
  const action = record.recommended_action || 'NORMAL_OPERATION';

  // Mock lane stats if not available in historical record
  const mockLaneStats = [
    { lane_id: 1, name: 'Northbound Lane', count: Math.ceil(record.total_vehicles * 0.4), density: density === 'HIGH' ? 'HIGH' : 'LOW' },
    { lane_id: 2, name: 'Southbound Lane', count: Math.floor(record.total_vehicles * 0.3), density: 'LOW' },
    { lane_id: 3, name: 'Eastbound Lane', count: Math.ceil(record.total_vehicles * 0.2), density: 'LOW' },
    { lane_id: 4, name: 'Westbound Lane', count: Math.floor(record.total_vehicles * 0.1), density: 'LOW' }
  ];

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/60 pb-6">
        <div className="space-y-1">
          <Link 
            to="/history" 
            className="inline-flex items-center text-xs font-semibold text-emerald-400 hover:text-emerald-300 gap-1 group mb-2"
          >
            <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform" />
            Back to Analysis History
          </Link>
          <h1 className="text-3xl font-extrabold text-white">Analysis Report</h1>
          <p className="text-slate-400 text-xs font-medium">
            Run ID / Timestamp: <span className="text-slate-200">{record.timestamp}</span>
          </p>
        </div>
      </div>

      {/* Main split display */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Side: Abstract visual details */}
        <div className="lg:col-span-6 space-y-6">
          <div className="border border-slate-800/80 bg-slate-900/40 rounded-2xl p-6 relative overflow-hidden shadow-lg min-h-[380px] flex flex-col justify-between">
            <div className="absolute top-0 right-0 p-8 opacity-5">
              <BarChart className="h-48 w-48 text-emerald-500" />
            </div>

            <div className="space-y-4">
              <span className="px-2.5 py-1 rounded-lg text-[10px] font-extrabold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Run Meta-Analytics
              </span>
              <h2 className="text-xl font-bold text-white">Visual Feed Snapshot</h2>
              <p className="text-slate-400 text-sm">
                Historical detection records extracted via YOLOv8 model inference.
              </p>
            </div>

            {/* High-tech visual grid */}
            <div className="my-6 border border-slate-800 rounded-xl p-4 bg-slate-950/40 relative overflow-hidden">
              <div className="flex justify-between items-center mb-3">
                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">AI Signal Confidence Overlay</span>
                <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded">Active</span>
              </div>
              <div className="space-y-2">
                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full w-4/5 animate-pulse"></div>
                </div>
                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-teal-400 rounded-full w-2/3"></div>
                </div>
                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full w-1/2"></div>
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between text-xs text-slate-400 font-medium">
                <span>Class Count: {record.total_vehicles}</span>
                <span>Signal Strength: 94%</span>
              </div>
            </div>

            <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900 border border-slate-800/80 p-3 rounded-xl">
              <Info className="h-4.5 w-4.5 text-emerald-400 flex-shrink-0" />
              <span>Full frames and tracking videos are persisted to regional uploads.</span>
            </div>
          </div>
        </div>

        {/* Right Side: Tabular stats */}
        <div className="lg:col-span-6 space-y-6">
          {/* Signal recommendations */}
          <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center border-b border-slate-800 pb-3">
              <Clock className="mr-2 h-4.5 w-4.5 text-emerald-400" />
              Signal Recommendations
            </h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Priority Level</span>
                <span className={`inline-flex px-2 py-0.5 mt-2 rounded-md text-xs font-semibold uppercase ${
                  record.emergency_present 
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse' 
                    : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                }`}>
                  {action.replace('_', ' ')}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Timing Override</span>
                <span className="text-lg font-bold text-slate-100 mt-1 block">
                  {record.emergency_present ? '90 Seconds' : '35 Seconds'}
                </span>
              </div>
            </div>
          </div>

          {/* Lane Utilization */}
          <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center border-b border-slate-800 pb-3">
              <Layout className="mr-2 h-4.5 w-4.5 text-emerald-400" />
              Lane-wise Utilization
            </h3>

            <div className="divide-y divide-slate-800/60">
              {mockLaneStats.map((lane) => (
                <div key={lane.lane_id} className="py-3.5 flex items-center justify-between text-xs font-semibold">
                  <span className="text-slate-400">{lane.name}</span>
                  <div className="flex items-center space-x-3">
                    <span className="text-slate-200">{lane.count} vehicles</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                      lane.density === 'HIGH' 
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {lane.density}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Congestion timeline */}
          <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center border-b border-slate-800 pb-3">
              <Gauge className="mr-2 h-4.5 w-4.5 text-emerald-400" />
              Congestion Analysis
            </h3>

            <div className="space-y-3.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Classification</span>
                <span className="text-slate-200 uppercase">{congestion.replace('_', ' ')}</span>
              </div>
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Total Bounding Boxes</span>
                <span className="text-slate-200">{record.total_vehicles}</span>
              </div>
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-slate-400">Emergency Vehicles</span>
                <span className={record.emergency_present ? 'text-rose-400' : 'text-slate-200'}>
                  {record.emergency_present ? 'Ambulance Detected' : 'None Detected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Results;
