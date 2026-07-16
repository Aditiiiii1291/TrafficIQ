import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Lock, Trash2, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

const Settings: React.FC = () => {
  const { changePassword, deleteAccount } = useAuth();

  // Password change states
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Account deletion states
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!oldPassword || !newPassword || !confirmPassword) return;

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSuccess(false);
      await changePassword({ old_password: oldPassword, new_password: newPassword });
      setSuccess(true);
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Incorrect old password credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true);
      return;
    }

    try {
      setDeleteLoading(true);
      await deleteAccount();
    } catch (err) {
      console.error(err);
      alert('Failed to delete account.');
      setDeleteConfirm(false);
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-2xl mx-auto">
      <div>
        <h1 className="text-3xl font-extrabold text-white">Account Settings</h1>
        <p className="text-slate-400 mt-1.5 text-sm font-medium">
          Manage your password credentials and account lifecycle.
        </p>
      </div>

      {/* Password Change Card */}
      <div className="border border-slate-800/80 bg-slate-900/30 backdrop-blur-md rounded-2xl p-8 space-y-6">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center border-b border-slate-800 pb-3">
          <Lock className="mr-2 h-4.5 w-4.5 text-emerald-400" />
          Change Password
        </h3>

        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs font-semibold text-rose-400 flex items-center gap-2">
            <AlertCircle className="h-4.5 w-4.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400 flex items-center gap-2">
            <CheckCircle className="h-4.5 w-4.5 flex-shrink-0" />
            <span>Password updated successfully!</span>
          </div>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Current Password</label>
            <input
              type="password"
              required
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none"
              placeholder="••••••••"
              disabled={loading}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">New Password</label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none"
              placeholder="••••••••"
              disabled={loading}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Confirm New Password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 focus:border-emerald-500 rounded-xl px-4 py-2.5 text-xs text-slate-200 outline-none"
              placeholder="••••••••"
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
                Updating Password...
              </>
            ) : (
              'Update Password'
            )}
          </button>
        </form>
      </div>

      {/* Account Deletion Card */}
      <div className="border border-red-900/40 bg-red-950/5 backdrop-blur-md rounded-2xl p-8 space-y-6">
        <h3 className="text-sm font-bold text-red-400 uppercase tracking-wider flex items-center border-b border-red-900/20 pb-3">
          <Trash2 className="mr-2 h-4.5 w-4.5 text-red-500" />
          Danger Zone
        </h3>

        <div className="space-y-4">
          <p className="text-xs text-slate-400 font-medium">
            Once you delete your account, all your processed videos, history files, and preemption settings will be permanently wiped out. This action is irreversible.
          </p>

          <button
            onClick={handleDeleteAccount}
            disabled={deleteLoading}
            className={`px-5 py-3 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center transition-all ${
              deleteConfirm 
                ? 'bg-rose-600 hover:bg-rose-500 text-white animate-bounce' 
                : 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20'
            }`}
          >
            {deleteLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : deleteConfirm ? (
              'Confirm Account Deletion!'
            ) : (
              'Delete Account'
            )}
          </button>

          {deleteConfirm && (
            <button 
              onClick={() => setDeleteConfirm(false)}
              className="text-xs font-semibold text-slate-400 hover:underline block"
            >
              Cancel Deletion
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;
