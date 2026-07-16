import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ApiService } from '../services/apiService';
import { Link } from 'react-router-dom';
import { 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  Video, 
  Eye, 
  ShieldAlert 
} from 'lucide-react';

const History: React.FC = () => {
  const [dateFilter, setDateFilter] = useState('');
  const [congestionFilter, setCongestionFilter] = useState('ALL');
  const [recommendationFilter, setRecommendationFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8;

  // React Query with dynamic cache keys dependent on filters!
  const { data, isLoading, error } = useQuery({
    queryKey: ['history', dateFilter, congestionFilter, recommendationFilter],
    queryFn: () => ApiService.getHistory({
      date_filter: dateFilter || undefined,
      congestion_level: congestionFilter,
      recommendation: recommendationFilter
    }),
    refetchInterval: 15000,
  });

  const records = data?.records || [];
  
  // Client-side pagination
  const totalItems = records.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage));
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedRecords = records.slice(startIndex, startIndex + itemsPerPage);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Analysis History</h1>
          <p className="text-slate-400 mt-1.5 text-sm font-medium">
            Search, filter, and review historical TrafficIQ analytics runs.
          </p>
        </div>
      </div>

      {/* Filters row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 p-5 rounded-2xl border border-slate-800 bg-slate-900/20 backdrop-blur-md">
        {/* Date Filter */}
        <div className="space-y-1.5 col-span-1 sm:col-span-2">
          <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Timestamp Date Filter</label>
          <div className="relative">
            <input
              type="text"
              placeholder="e.g. 2026-07-16"
              value={dateFilter}
              onChange={(e) => { setDateFilter(e.target.value); setCurrentPage(1); }}
              className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none pl-10"
            />
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
          </div>
        </div>

        {/* Congestion Level Filter */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Congestion Level</label>
          <select
            value={congestionFilter}
            onChange={(e) => { setCongestionFilter(e.target.value); setCurrentPage(1); }}
            className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none"
          >
            <option value="ALL">All Congestions</option>
            <option value="LOW_CONGESTION">Low Congestion</option>
            <option value="MEDIUM_CONGESTION">Medium Congestion</option>
            <option value="HIGH_CONGESTION">High Congestion</option>
          </select>
        </div>

        {/* Preemption Recommendation Filter */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Signal Priority Action</label>
          <select
            value={recommendationFilter}
            onChange={(e) => { setRecommendationFilter(e.target.value); setCurrentPage(1); }}
            className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none"
          >
            <option value="ALL">All Preempts</option>
            <option value="NORMAL_OPERATION">Normal Operation</option>
            <option value="EXTEND_GREEN">Extend Green</option>
            <option value="HIGH_TRAFFIC_WARNING">High Traffic Warning</option>
            <option value="EMERGENCY_PRIORITY">Emergency Priority</option>
          </select>
        </div>
      </div>

      {/* Main content split */}
      {isLoading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <LoaderSpinner />
        </div>
      ) : error ? (
        <div className="text-center py-12 border border-slate-800 bg-slate-900/30 rounded-2xl p-8 space-y-3">
          <ShieldAlert className="h-10 w-10 text-rose-500 mx-auto" />
          <h3 className="text-white font-bold">Query Error</h3>
          <p className="text-slate-400 text-xs">Failed to load run logs. Check FastAPI connection.</p>
        </div>
      ) : paginatedRecords.length > 0 ? (
        <div className="space-y-6">
          <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl overflow-hidden shadow-lg">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-800">
                <thead className="bg-slate-900/60">
                  <tr>
                    <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Timestamp</th>
                    <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Vehicle Count</th>
                    <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Density</th>
                    <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Congestion</th>
                    <th className="px-6 py-4 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider">Priority Signal</th>
                    <th className="px-6 py-4 text-right text-[10px] font-bold text-slate-400 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-950/20">
                  {paginatedRecords.map((run, i) => (
                    <tr key={i} className="hover:bg-slate-900/30 transition-colors">
                      <td className="px-6 py-4 text-xs font-semibold text-slate-200 whitespace-nowrap">
                        {new Date(run.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-xs font-bold text-slate-100 whitespace-nowrap">
                        {run.total_vehicles}
                      </td>
                      <td className="px-6 py-4 text-xs whitespace-nowrap">
                        <span className="text-slate-300">{run.density}</span>
                      </td>
                      <td className="px-6 py-4 text-xs whitespace-nowrap">
                        <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          run.congestion === 'HIGH_CONGESTION' 
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                            : run.congestion === 'MEDIUM_CONGESTION' 
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' 
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {run.congestion.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs whitespace-nowrap">
                        <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          run.emergency_present 
                            ? 'bg-red-500/10 text-red-400 border border-red-500/20 animate-pulse' 
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {run.recommended_action.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-xs whitespace-nowrap">
                        <Link
                          to={`/results?id=${encodeURIComponent(run.timestamp)}`}
                          className="inline-flex items-center justify-center p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-emerald-400 hover:border-emerald-500/30 transition-all"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination buttons */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">
              Showing page {currentPage} of {totalPages} ({totalItems} total logs)
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className={`p-2 rounded-xl border border-slate-800 transition-colors ${
                  currentPage === 1 
                    ? 'text-slate-600 cursor-not-allowed bg-slate-900/20' 
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <ChevronLeft className="h-4.5 w-4.5" />
              </button>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className={`p-2 rounded-xl border border-slate-800 transition-colors ${
                  currentPage === totalPages 
                    ? 'text-slate-600 cursor-not-allowed bg-slate-900/20' 
                    : 'text-slate-300 hover:bg-slate-800'
                }`}
              >
                <ChevronRight className="h-4.5 w-4.5" />
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-16 border-2 border-dashed border-slate-800 rounded-2xl bg-slate-950/20 space-y-4">
          <Video className="h-10 w-10 text-slate-700 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-white font-bold text-sm">No analysis runs match</h3>
            <p className="text-slate-500 text-xs max-w-xs mx-auto">
              Change the search timestamp or filters to retrieve historical runs.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

const LoaderSpinner: React.FC = () => (
  <div className="relative">
    <div className="h-12 w-12 rounded-full border-4 border-slate-800 border-t-emerald-500 animate-spin"></div>
  </div>
);

export default History;
