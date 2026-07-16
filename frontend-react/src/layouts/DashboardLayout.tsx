import React, { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { 
  LayoutDashboard, 
  Upload, 
  BarChart3, 
  History, 
  Menu, 
  X, 
  TrafficCone,
  User as UserIcon,
  Settings as SettingsIcon,
  LogOut
} from 'lucide-react';

const DashboardLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const { logout, user } = useAuth();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Upload Video', href: '/upload', icon: Upload },
    { name: 'Analytics', href: '/analytics', icon: BarChart3 },
    { name: 'History', href: '/history', icon: History },
    { name: 'Profile', href: '/profile', icon: UserIcon },
    { name: 'Settings', href: '/settings', icon: SettingsIcon },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col md:flex-row">
      {/* Sidebar for desktop */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 z-20 border-r border-slate-800/80 bg-slate-900/50 backdrop-blur-md">
        <div className="flex flex-col h-full pt-5 pb-4 overflow-y-auto px-4 justify-between">
          <div className="space-y-6">
            {/* Logo */}
            <div className="flex items-center px-2 gap-3">
              <div className="p-2 bg-gradient-to-tr from-emerald-500 to-teal-400 rounded-xl shadow-lg shadow-emerald-500/20">
                <TrafficCone className="h-6 w-6 text-slate-950" />
              </div>
              <div>
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">TrafficIQ</span>
                <p className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">AI Traffic Hub</p>
              </div>
            </div>

            {/* Navigation Links */}
            <nav className="space-y-1.5">
              {navigation.map((item) => {
                const active = location.pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`group flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-300 ${
                      active 
                        ? 'bg-gradient-to-r from-emerald-500/10 to-teal-500/5 text-emerald-400 border border-emerald-500/20 shadow-lg shadow-emerald-500/5' 
                        : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200 border border-transparent'
                    }`}
                  >
                    <Icon className={`mr-3 h-5 w-5 flex-shrink-0 transition-transform duration-300 group-hover:scale-110 ${active ? 'text-emerald-400' : 'text-slate-400'}`} />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="space-y-4 pt-4 border-t border-slate-800/80">
            {/* Logged in User Profile Info */}
            {user && (
              <div className="px-2 py-1 flex items-center space-x-3">
                <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-emerald-400">
                  {user.full_name.charAt(0)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-slate-200 truncate">{user.full_name}</p>
                  <p className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">{user.role}</p>
                </div>
              </div>
            )}
            
            {/* Logout Button */}
            <button
              onClick={logout}
              className="w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 border border-transparent transition-all duration-300"
            >
              <LogOut className="mr-3 h-5 w-5 flex-shrink-0" />
              Logout
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile top navigation bar */}
      <header className="md:hidden flex items-center justify-between px-6 py-4 bg-slate-900/80 backdrop-blur-md border-b border-slate-800/80 sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-gradient-to-tr from-emerald-500 to-teal-400 rounded-lg">
            <TrafficCone className="h-5 w-5 text-slate-950" />
          </div>
          <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">TrafficIQ</span>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
        >
          {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </header>

      {/* Mobile drawer overlay */}
      {sidebarOpen && (
        <div className="md:hidden fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <nav className="relative flex flex-col w-4/5 max-w-sm bg-slate-900 border-r border-slate-800 p-6 h-full shadow-2xl z-50 justify-between">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-1.5 bg-gradient-to-tr from-emerald-500 to-teal-400 rounded-lg">
                    <TrafficCone className="h-5 w-5 text-slate-950" />
                  </div>
                  <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">TrafficIQ</span>
                </div>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="space-y-2">
                {navigation.map((item) => {
                  const active = location.pathname === item.href;
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all ${
                        active 
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                          : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                      }`}
                    >
                      <Icon className="mr-3 h-5 w-5 text-emerald-400" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t border-slate-800">
              <button
                onClick={() => { setSidebarOpen(false); logout(); }}
                className="w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 border border-transparent transition-all duration-300"
              >
                <LogOut className="mr-3 h-5 w-5 flex-shrink-0" />
                Logout
              </button>
            </div>
          </nav>
        </div>
      )}

      {/* Main content viewport */}
      <main className="flex-1 md:pl-64 flex flex-col min-h-screen">
        <div className="flex-grow p-6 md:p-8 max-w-7xl w-full mx-auto space-y-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
