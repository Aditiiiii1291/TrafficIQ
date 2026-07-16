import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

const NotFound: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center max-w-md mx-auto space-y-5 px-6">
      <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl shadow-lg shadow-rose-500/5">
        <ShieldAlert className="h-10 w-10 text-rose-500" />
      </div>
      
      <div className="space-y-2">
        <h1 className="text-3xl font-black text-white tracking-tight">404 - Page Not Found</h1>
        <p className="text-slate-400 text-sm font-medium">
          The requested interface route does not exist or has been relocated.
        </p>
      </div>

      <Link
        to="/"
        className="inline-flex items-center px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-all duration-300"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Return to Dashboard
      </Link>
    </div>
  );
};

export default NotFound;
