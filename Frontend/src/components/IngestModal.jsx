import React, { useState } from 'react';
import { ingestDirectory, ingestText } from '../api';

export default function IngestModal({ token, onClose, onIngestSuccess }) {
  const [mode, setMode] = useState('text'); // 'text' or 'path'
  const [text, setText] = useState('');
  const [path, setPath] = useState('');
  const [projectId, setProjectId] = useState('my-memory');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');
    
    try {
      if (mode === 'text') {
        await ingestText(text, 'web-input', projectId, token);
        setMessage('Memory recorded! It is being mapped in the background.');
        setText('');
      } else {
        await ingestDirectory(path, projectId, token);
        setMessage('Bulk ingestion started! Scanned files are being mapped.');
        setPath('');
      }
      if (onIngestSuccess) onIngestSuccess();
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="panel-backdrop w-full max-w-lg rounded-[2.5rem] border border-slate-800/80 bg-slate-950/90 p-8 shadow-2xl lg:p-10">
        <div className="mb-8 flex items-center justify-between">
          <h2 className="font-display text-2xl text-white">Neural Ingest</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-white">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-8 flex gap-4">
          <button
            onClick={() => setMode('text')}
            className={`flex-1 rounded-xl py-3 text-xs font-bold uppercase tracking-widest transition-all ${
              mode === 'text' ? 'bg-cyan-500 text-slate-950' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
            }`}
          >
            Direct Memory
          </button>
          <button
            onClick={() => setMode('path')}
            className={`flex-1 rounded-xl py-3 text-xs font-bold uppercase tracking-widest transition-all ${
              mode === 'path' ? 'bg-cyan-500 text-slate-950' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
            }`}
          >
            System Files
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {mode === 'text' ? (
            <div>
              <label className="mb-2 block text-[10px] uppercase tracking-widest text-slate-500">Cognitive Content</label>
              <textarea
                required
                rows={5}
                className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-4 text-sm text-white outline-none focus:border-cyan-500"
                placeholder="Describe a concept, project details, or life experience..."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </div>
          ) : (
            <div>
              <label className="mb-2 block text-[10px] uppercase tracking-widest text-slate-500">Directory Path</label>
              <input
                type="text"
                required
                className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-4 text-sm text-white outline-none focus:border-cyan-500"
                placeholder="C:\Users\Documents\MyProject"
                value={path}
                onChange={(e) => setPath(e.target.value)}
              />
              <p className="mt-2 text-[10px] text-slate-500 italic">
                Scanning for code, markdown, and text files.
              </p>
            </div>
          )}

          <div>
            <label className="mb-2 block text-[10px] uppercase tracking-widest text-slate-500">Target Project ID</label>
            <input
              type="text"
              className="w-full rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-4 text-sm text-white outline-none focus:border-cyan-500"
              placeholder="e.g. personal-bio"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
            />
          </div>

          {message && (
            <div className={`rounded-xl p-4 text-center text-xs ${message.includes('Error') ? 'bg-rose-500/10 text-rose-300' : 'bg-emerald-500/10 text-emerald-300'}`}>
              {message}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-white py-4 font-bold text-slate-950 transition-all hover:bg-cyan-400 disabled:opacity-50"
          >
            {isLoading ? 'Processing...' : 'Initiate Mapping'}
          </button>
        </form>
      </div>
    </div>
  );
}
