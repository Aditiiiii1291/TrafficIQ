import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { User, Shield, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const Profile: React.FC = () => {
  const { user, updateProfile } = useAuth();
  
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email) return;
    
    try {
      setLoading(true);
      setError('');
      setSuccess(false);
      await updateProfile({ full_name: fullName, email });
      setSuccess(true);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to update profile details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-2xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold text-white">My Profile</h1>
        <p className="text-slate-400 mt-1.5 text-sm font-medium">
          View and modify your user profile details.
        </p>
      </div>

      <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-8 space-y-6">
        <div className="flex items-center space-x-4 pb-6 border-b border-slate-800">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-2xl">
            <User className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-white font-bold text-base">{user?.full_name}</h3>
            <span className="inline-flex items-center text-[10px] font-bold uppercase tracking-wider text-slate-400 mt-1 gap-1">
              <Shield className="h-3 w-3 text-emerald-400" />
              Role: {user?.role}
            </span>
          </div>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-semibold text-rose-400 flex items-center gap-2">
            <AlertCircle className="h-4.5 w-4.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400 flex items-center gap-2">
            <CheckCircle className="h-4.5 w-4.5 flex-shrink-0" />
            <span>Profile details updated successfully!</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Full Name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none"
              disabled={loading}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-955 font-bold text-xs uppercase tracking-wider flex items-center justify-center transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Updating Profile...
              </>
            ) : (
              'Save Profile'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Profile;
