import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ApiService } from '../services/apiService';
import { Link } from 'react-router-dom';
import { 
  Play, 
  Video, 
  AlertTriangle, 
  Gauge, 
  Activity, 
  TrendingUp, 
  ShieldAlert, 
  ExternalLink 
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['analytics'],
    queryFn: ApiService.getAnalytics,
    refetchInterval: 10000, // refresh every 10 seconds
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['history'],
    queryFn: () => ApiService.getHistory(),
    refetchInterval: 10000,
  });

  const isLoading = analyticsLoading || historyLoading;

  // Derive latest record
  const latestRecord = history?.records && history.records.length > 0 ? history.records[0] : null;
  const recentRuns = history?.records ? history.records.slice(0, 5) : [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="relative">
          <div className="h-16 w-16 rounded-full border-4 border-slate-800 border-t-emerald-500 animate-spin"></div>
          <div className="mt-4 text-slate-400 text-sm font-medium animate-pulse">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      title: 'Processed Runs',
      value: analytics?.summary.total_analyzed_records ?? 0,
      icon: Video,
      color: 'from-blue-500 to-indigo-600',
      shadow: 'shadow-blue-500/10',
    },
    {
      title: 'Emergency Incidents',
      value: analytics?.summary.total_emergency_events ?? 0,
      icon: ShieldAlert,
      color: 'from-rose-500 to-red-600',
      shadow: 'shadow-rose-500/10',
    },
    {
      title: 'Common Congestion',
      value: analytics?.summary.most_common_congestion_level?.replace('_', ' ') ?? 'N/A',
      icon: Gauge,
      color: 'from-amber-500 to-orange-600',
      shadow: 'shadow-amber-500/10',
    },
    {
      title: 'Active Recommendation',
      value: analytics?.summary.most_common_recommendation?.replace('_', ' ') ?? 'N/A',
      icon: AlertTriangle,
      color: 'from-emerald-500 to-teal-600',
      shadow: 'shadow-emerald-500/10',
    },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Heading */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            TrafficIQ Hub
          </h1>
          <p className="text-slate-400 mt-1.5 text-sm font-medium">
            AI-Powered Intelligent Traffic Management System
          </p>
        </div>
        <Link 
          to="/upload" 
          className="inline-flex items-center justify-center px-5 py-3 rounded-xl text-sm font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-all duration-300 transform hover:-translate-y-0.5 hover:shadow-lg hover:shadow-emerald-500/20"
        >
          <Play className="mr-2 h-4.5 w-4.5 fill-current" />
          Process New Video
        </Link>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div 
              key={i} 
              className={`p-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 backdrop-blur-md hover:border-slate-700/60 transition-all duration-300 hover:-translate-y-1 shadow-lg ${card.shadow}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-sm font-semibold">{card.title}</span>
                <div className={`p-2.5 rounded-xl bg-gradient-to-tr ${card.color} text-slate-950 shadow-md`}>
                  <Icon className="h-5 w-5 text-slate-100" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-2xl font-bold tracking-tight text-white block truncate">{card.value}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main split row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Latest Run Details */}
        <div className="lg:col-span-7 flex flex-col">
          <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6 flex flex-col h-full">
            <h2 className="text-lg font-bold text-white flex items-center mb-6">
              <TrendingUp className="mr-2 h-5 w-5 text-emerald-400" />
              Latest Processed Metrics
            </h2>

            {latestRecord ? (
              <div className="flex-1 flex flex-col justify-between space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Timestamp</span>
                    <span className="text-sm font-semibold text-slate-200 mt-1 block truncate">
                      {new Date(latestRecord.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Total Vehicles</span>
                    <span className="text-lg font-bold text-slate-100 mt-1 block">
                      {latestRecord.total_vehicles}
                    </span>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Congestion Status</span>
                    <span className={`inline-flex px-2 py-0.5 mt-2 rounded-md text-xs font-semibold uppercase ${
                      latestRecord.congestion === 'HIGH_CONGESTION' 
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                        : latestRecord.congestion === 'MEDIUM_CONGESTION' 
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' 
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {latestRecord.congestion.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Priority recommendation</span>
                    <span className={`inline-flex px-2 py-0.5 mt-2 rounded-md text-xs font-semibold uppercase ${
                      latestRecord.emergency_present 
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse' 
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {latestRecord.recommended_action.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-xs text-slate-400 font-medium">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span>Ready to query details</span>
                  </div>
                  <Link 
                    to={`/results?id=${encodeURIComponent(latestRecord.timestamp)}`}
                    className="inline-flex items-center text-xs font-semibold text-emerald-400 hover:text-emerald-300 gap-1 hover:underline"
                  >
                    View Processing Report
                    <ExternalLink className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            ) : (
              <div className="flex-grow flex flex-col items-center justify-center py-12 border-2 border-dashed border-slate-800 rounded-xl bg-slate-950/20">
                <Video className="h-10 w-10 text-slate-700 mb-3" />
                <span className="text-slate-500 text-sm font-semibold">No process runs documented yet</span>
                <Link to="/upload" className="text-emerald-400 hover:text-emerald-300 text-xs font-medium mt-1 underline">
                  Upload video to analyze
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activities */}
        <div className="lg:col-span-5 flex flex-col">
          <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6 flex flex-col h-full">
            <h2 className="text-lg font-bold text-white flex items-center mb-6">
              <Activity className="mr-2 h-5 w-5 text-emerald-400" />
              Recent Activities
            </h2>

            <div className="flex-1 space-y-4 overflow-y-auto max-h-[300px] pr-2">
              {recentRuns.length > 0 ? (
                recentRuns.map((run, index) => (
                  <div 
                    key={index} 
                    className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/60 hover:bg-slate-900 transition-colors"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-300">
                          {run.total_vehicles} Vehicles
                        </span>
                        {run.emergency_present && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase bg-red-500/10 text-red-400 border border-red-500/20 animate-pulse">
                            Emergency
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 block truncate mt-1">
                        {new Date(run.timestamp).toLocaleString()}
                      </span>
                    </div>

                    <Link 
                      to={`/results?id=${encodeURIComponent(run.timestamp)}`}
                      className="p-2 rounded-lg bg-slate-800/60 hover:bg-emerald-500 hover:text-slate-950 text-slate-400 transition-all"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Link>
                  </div>
                ))
              ) : (
                <div className="h-full flex flex-col items-center justify-center py-12 text-slate-600">
                  <Play className="h-8 w-8 mb-2" />
                  <span className="text-sm font-semibold">No recent activity</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
