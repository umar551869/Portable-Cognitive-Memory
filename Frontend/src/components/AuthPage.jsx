import React, { useState } from 'react';
import { login, registerAccount } from '../api';

export default function AuthPage({ onLoginSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      let result;
      if (isLogin) {
        result = await login({ email: formData.email, password: formData.password });
      } else {
        result = await registerAccount(formData);
      }
      
      const session = {
        token: result.access_token,
        user: { email: formData.email, name: formData.name || 'Explorer' }
      };
      
      localStorage.setItem('pcg_session', JSON.stringify(session));
      onLoginSuccess(session);
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-[90vh] items-center justify-center p-4">
      <div className="panel-backdrop w-full max-w-md overflow-hidden rounded-[2.5rem] border border-slate-800/80 bg-slate-950/40 p-8 shadow-2xl backdrop-blur-3xl lg:p-12">
        <div className="relative mb-10 text-center">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-cyan-500/10 shadow-glow">
            <div className="h-8 w-8 animate-pulse rounded-full bg-cyan-400" />
          </div>
          <h1 className="font-display text-4xl text-white">
            {isLogin ? 'Wake your Brain' : 'Create Identity'}
          </h1>
          <p className="mt-3 text-sm text-slate-400">
            {isLogin ? 'Access your private neural memory field' : 'Begin mapping your cognitive journey'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {!isLogin && (
            <div>
              <label className="mb-2 block text-[10px] uppercase tracking-widest text-slate-400">FullName</label>
              <input
                type="text"
                required
                className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-5 py-4 text-white outline-none ring-cyan-500/30 transition-all focus:border-cyan-500 focus:ring-4"
                placeholder="Sir Muhammad Umar"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
          )}

          <div>
            <label className="mb-2 block text-[10px] uppercase tracking-widest text-slate-400">Email Interface</label>
            <input
              type="email"
              required
              className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-5 py-4 text-white outline-none ring-cyan-500/30 transition-all focus:border-cyan-500 focus:ring-4"
              placeholder="umar@fast.edu"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div>
            <label className="mb-2 block text-[10px] uppercase tracking-widest text-slate-400">Access Cipher</label>
            <input
              type="password"
              required
              className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-5 py-4 text-white outline-none ring-cyan-500/30 transition-all focus:border-cyan-500 focus:ring-4"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            />
          </div>

          {error && (
            <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-center text-sm text-rose-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="relative w-full overflow-hidden rounded-xl bg-cyan-500 py-4 font-bold text-slate-950 transition-all hover:bg-cyan-400 disabled:opacity-50"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950 border-t-transparent" />
                Syncing...
              </span>
            ) : (
              isLogin ? 'Initiate Link' : 'Establish Connection'
            )}
          </button>
        </form>

        <div className="mt-10 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-xs uppercase tracking-widest text-slate-500 transition-colors hover:text-cyan-400"
          >
            {isLogin ? "New user? Create a neural id" : "Existing user? Link identity"}
          </button>
        </div>
      </div>
    </div>
  );
}
