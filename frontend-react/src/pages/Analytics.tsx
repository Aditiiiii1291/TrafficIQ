import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ApiService } from '../services/apiService';
import { 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';
import { 
  BarChart3, 
  PieChart as PieIcon, 
  Activity, 
  TrendingUp, 
  ShieldAlert 
} from 'lucide-react';

const COLORS = ['#10b981', '#f59e0b', '#f43f5e', '#3b82f6', '#8b5cf6'];

const Analytics: React.FC = () => {
  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['analytics'],
    queryFn: ApiService.getAnalytics,
    refetchInterval: 10000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="relative">
          <div className="h-16 w-16 rounded-full border-4 border-slate-800 border-t-emerald-500 animate-spin"></div>
          <div className="mt-4 text-slate-400 text-sm font-medium animate-pulse">Assembling analytics charts...</div>
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="max-w-md mx-auto text-center py-12 border border-slate-800 bg-slate-900/30 rounded-2xl p-8 space-y-4">
        <ShieldAlert className="h-12 w-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold text-white">Analytics Unavailable</h2>
        <p className="text-slate-400 text-sm">
          Failed to load historical analytics database.
        </p>
      </div>
    );
  }

  const { trends, summary, event_statistics } = analytics;

  // Format line chart data
  const vehicleChartData = (trends.vehicle_count_over_time || []).map((item) => ({
    time: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    Count: item.total_vehicles,
  }));

  // Format pie chart distributions
  const congestionPieData = Object.entries(trends.congestion_distribution || {}).map(([key, value]) => ({
    name: key.replace('_', ' '),
    value,
  }));

  const recommendationPieData = Object.entries(trends.recommendation_distribution || {}).map(([key, value]) => ({
    name: key.replace('_', ' '),
    value,
  }));

  const densityBarData = Object.entries(trends.density_distribution || {}).map(([key, value]) => ({
    name: key,
    Count: value,
  }));

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-extrabold text-white">System Analytics</h1>
        <p className="text-slate-400 mt-1.5 text-sm font-medium">
          Timelines, distribution patterns, and priority performance metrics for TrafficIQ.
        </p>
      </div>

      {/* Analytics stats banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-md">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Total Videos Processed</span>
          <span className="text-3xl font-black text-white block mt-2">{summary.total_analyzed_records}</span>
        </div>
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-md">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Emergency Preemption Preempts</span>
          <span className="text-3xl font-black text-white block mt-2">{event_statistics.total_emergency_events}</span>
        </div>
        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur-md">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">Emergency Incidents preemption Preempt Rate</span>
          <span className="text-3xl font-black text-white block mt-2">{event_statistics.emergency_rate}</span>
        </div>
      </div>

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Vehicle Count Over Time */}
        <div className="lg:col-span-8 border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6">
          <h2 className="text-base font-bold text-white flex items-center mb-6">
            <TrendingUp className="mr-2 h-5 w-5 text-emerald-400" />
            Vehicle preemption Detection Timeline
          </h2>
          <div className="h-[300px]">
            {vehicleChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={vehicleChartData}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                    labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                  />
                  <Area type="monotone" dataKey="Count" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-600">
                <Activity className="h-8 w-8 mb-2" />
                <span className="text-sm font-semibold">No timeline data available</span>
              </div>
            )}
          </div>
        </div>

        {/* Traffic Density Distribution */}
        <div className="lg:col-span-4 border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6">
          <h2 className="text-base font-bold text-white flex items-center mb-6">
            <BarChart3 className="mr-2 h-5 w-5 text-emerald-400" />
            Density Classification
          </h2>
          <div className="h-[300px]">
            {densityBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={densityBarData}>
                  <XAxis dataKey="name" stroke="#475569" fontSize={11} tickLine={false} />
                  <YAxis stroke="#475569" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                    labelStyle={{ color: '#94a3b8', fontWeight: 'bold' }}
                  />
                  <Bar dataKey="Count" fill="#10b981" radius={[8, 8, 0, 0]}>
                    {densityBarData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-600">
                <Activity className="h-8 w-8 mb-2" />
                <span className="text-sm font-semibold">No density distribution data</span>
              </div>
            )}
          </div>
        </div>

        {/* Congestion Distribution */}
        <div className="lg:col-span-6 border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6">
          <h2 className="text-base font-bold text-white flex items-center mb-6">
            <PieIcon className="mr-2 h-5 w-5 text-emerald-400" />
            Congestion Level Share
          </h2>
          <div className="h-[250px] flex items-center justify-center">
            {congestionPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={congestionPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} (${percent ? (percent * 100).toFixed(0) : 0}%)`}
                  >
                    {congestionPieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <span className="text-sm font-semibold text-slate-600">No share metrics found</span>
            )}
          </div>
        </div>

        {/* Signal override actions share */}
        <div className="lg:col-span-6 border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-6">
          <h2 className="text-base font-bold text-white flex items-center mb-6">
            <PieIcon className="mr-2 h-5 w-5 text-emerald-400" />
            Signal Preemption Share
          </h2>
          <div className="h-[250px] flex items-center justify-center">
            {recommendationPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={recommendationPieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} (${percent ? (percent * 100).toFixed(0) : 0}%)`}
                  >
                    {recommendationPieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <span className="text-sm font-semibold text-slate-600">No preemption metrics found</span>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Analytics;
