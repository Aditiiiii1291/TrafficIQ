import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

const ForgotPassword: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-slate-100">
      <div className="w-full max-w-md border border-slate-800 bg-slate-900/40 p-8 rounded-2xl shadow-xl text-center space-y-5">
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl w-fit mx-auto">
          <ShieldAlert className="h-10 w-10 text-emerald-400" />
        </div>
        
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-white">Reset Password</h2>
          <p className="text-slate-400 text-xs font-medium">
            Placeholder Password Reset Portal. Please contact your system administrator to recover credentials.
          </p>
        </div>

        <Link
          to="/login"
          className="inline-flex items-center text-xs font-semibold text-emerald-400 hover:text-emerald-300 gap-1 underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Login
        </Link>
      </div>
    </div>
  );
};

export default ForgotPassword;
