import React, { useState, useEffect, useRef } from 'react';
import { 
  Zap, 
  Terminal, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  ChevronDown, 
  ChevronUp, 
  Cpu, 
  HardDrive, 
  FolderCheck, 
  ExternalLink,
  Layers,
  X
} from 'lucide-react';

export default function EngineSetupModal({ isOpen, onClose, onInstalled }) {
  const [envData, setEnvData] = useState(null);
  const [isLoadingEnv, setIsLoadingEnv] = useState(true);
  const [isInstalling, setIsInstalling] = useState(false);
  const [installError, setInstallError] = useState(null);
  const [progress, setProgress] = useState({ step: 0, totalSteps: 4, label: 'Ready to install', percent: 0 });
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const logsEndRef = useRef(null);

  const isDesktop = typeof window !== 'undefined' && Boolean(window.openloreDesktop);

  useEffect(() => {
    if (!isOpen) return;

    let cleanupProgress = () => {};
    let cleanupLogs = () => {};

    if (isDesktop && window.openloreDesktop.detectEnvironment) {
      setIsLoadingEnv(true);
      window.openloreDesktop.detectEnvironment()
        .then((data) => {
          setEnvData(data);
          setIsLoadingEnv(false);
        })
        .catch((err) => {
          setEnvData({ canBootstrap: false, error: err.message });
          setIsLoadingEnv(false);
        });

      cleanupProgress = window.openloreDesktop.onInstallProgress((prog) => {
        setProgress(prog);
        if (prog.percent >= 100) {
          setIsComplete(true);
          setIsInstalling(false);
          if (onInstalled) onInstalled();
        }
      });

      cleanupLogs = window.openloreDesktop.onInstallLog((logMsg) => {
        setLogs((prev) => [...prev.slice(-300), logMsg]);
      });
    } else {
      setIsLoadingEnv(false);
      setEnvData({
        os: 'browser',
        arch: 'web',
        canBootstrap: false,
        openloreDir: '~/.openlore',
        pythonVersion: 'N/A (Web Mode)',
      });
    }

    return () => {
      cleanupProgress();
      cleanupLogs();
    };
  }, [isOpen]);

  useEffect(() => {
    if (showLogs && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, showLogs]);

  const handleStartInstall = async () => {
    if (!isDesktop || !window.openloreDesktop.bootstrapEngine) return;

    setIsInstalling(true);
    setInstallError(null);
    setLogs(['[Bootstrapper] Starting turnkey OpenLore engine setup...']);
    setProgress({ step: 1, totalSteps: 4, label: 'Preparing runtime environment...', percent: 10 });

    try {
      await window.openloreDesktop.bootstrapEngine();
      setIsComplete(true);
      setIsInstalling(false);
      if (onInstalled) onInstalled();
    } catch (err) {
      setIsInstalling(false);
      setInstallError(err.message || 'Failed to install OpenLore engine');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-neutral-900 border border-neutral-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-800/80 bg-neutral-950/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-neutral-100 flex items-center gap-2">
                OpenLore Engine Setup
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-mono border border-amber-500/30">
                  v2.0.0
                </span>
              </h2>
              <p className="text-xs text-neutral-400">Turnkey 1-Click Engine & DCC Sidecar Setup</p>
            </div>
          </div>
          {!isInstalling && (
            <button 
              onClick={onClose}
              className="text-neutral-400 hover:text-neutral-200 p-1.5 rounded-lg hover:bg-neutral-800/60 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Welcome Intro */}
          <div className="text-sm text-neutral-300 leading-relaxed">
            OpenLore Studio connects your 3D viewports with an isolated local background daemon for OpenUSD 24.11 composition, CRDT synchronization, and Live Link DCC bridges.
          </div>

          {/* System Diagnostics Probe Card */}
          <div className="bg-neutral-950/80 border border-neutral-800/80 rounded-xl p-4 space-y-3">
            <div className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              System Diagnostics
            </div>

            {isLoadingEnv ? (
              <div className="flex items-center gap-2 text-xs text-neutral-400 py-2">
                <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
                Probing host runtime and Python installations...
              </div>
            ) : envData ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="bg-neutral-900/60 p-2.5 rounded-lg border border-neutral-800/60">
                  <span className="text-neutral-400 block mb-0.5">Host Platform</span>
                  <span className="font-mono text-neutral-200 font-medium">
                    {envData.os || 'Unknown'} ({envData.arch || 'x64'})
                  </span>
                </div>

                <div className="bg-neutral-900/60 p-2.5 rounded-lg border border-neutral-800/60">
                  <span className="text-neutral-400 block mb-0.5">Python Runtime</span>
                  {envData.systemPython ? (
                    <span className="font-mono text-emerald-400 flex items-center gap-1.5 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                      {envData.pythonVersion || envData.systemPython}
                    </span>
                  ) : (
                    <span className="font-mono text-amber-400 flex items-center gap-1.5 font-medium">
                      <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                      Python 3.9+ Not Found
                    </span>
                  )}
                </div>

                <div className="bg-neutral-900/60 p-2.5 rounded-lg border border-neutral-800/60 sm:col-span-2">
                  <span className="text-neutral-400 block mb-0.5">Target Installation Path</span>
                  <span className="font-mono text-neutral-300 break-all">
                    {envData.openloreDir || '~/.openlore'}
                  </span>
                </div>
              </div>
            ) : null}

            {envData && !envData.canBootstrap && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-xs text-amber-200 flex items-start gap-2.5 mt-2">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="block text-amber-300 font-semibold mb-1">Python 3.9+ Required</strong>
                  To run the local background daemon, install Python 3 on your system.
                  <a 
                    href="https://www.python.org/downloads/" 
                    target="_blank" 
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-amber-400 underline font-semibold mt-1.5 hover:text-amber-300"
                  >
                    Download Python 3.12 from python.org <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* Installation Progress View */}
          {isInstalling && (
            <div className="bg-neutral-950/80 border border-indigo-500/30 rounded-xl p-4 space-y-3 animate-in fade-in">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-neutral-200 flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                  {progress.label}
                </span>
                <span className="font-mono text-indigo-400 font-bold">{progress.percent}%</span>
              </div>

              {/* Progress Track */}
              <div className="w-full bg-neutral-800 h-2 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-amber-500 to-indigo-500 transition-all duration-300 rounded-full"
                  style={{ width: `${progress.percent}%` }}
                />
              </div>

              {/* Step Checklist */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 text-[11px] font-mono">
                <div className={`flex items-center gap-2 ${progress.percent >= 25 ? 'text-emerald-400' : 'text-neutral-500'}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" /> 1. Isolated Virtualenv
                </div>
                <div className={`flex items-center gap-2 ${progress.percent >= 55 ? 'text-emerald-400' : 'text-neutral-500'}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" /> 2. Core Python Engine v2.0.0
                </div>
                <div className={`flex items-center gap-2 ${progress.percent >= 80 ? 'text-emerald-400' : 'text-neutral-500'}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" /> 3. DCC Connectors & Bridges
                </div>
                <div className={`flex items-center gap-2 ${progress.percent >= 100 ? 'text-emerald-400' : 'text-neutral-500'}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" /> 4. Local Daemon Port 8000
                </div>
              </div>
            </div>
          )}

          {/* Success Card */}
          {isComplete && (
            <div className="bg-emerald-950/20 border border-emerald-500/40 rounded-xl p-4 flex items-center gap-3 animate-in zoom-in-95">
              <div className="w-9 h-9 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <div className="text-xs">
                <strong className="block text-emerald-300 font-semibold text-sm">OpenLore Engine Ready!</strong>
                <p className="text-neutral-300 mt-0.5">
                  The local daemon is active at <code className="text-amber-300 font-mono">http://127.0.0.1:8000</code>. Studio viewports and live pipelines are now connected.
                </p>
              </div>
            </div>
          )}

          {/* Error Card */}
          {installError && (
            <div className="bg-red-950/30 border border-red-500/40 rounded-xl p-4 text-xs text-red-200 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <strong className="block text-red-300 font-semibold">Installation Failed</strong>
                <p>{installError}</p>
              </div>
            </div>
          )}

          {/* Collapsible Log Terminal */}
          {logs.length > 0 && (
            <div className="border border-neutral-800 rounded-xl overflow-hidden bg-black">
              <button
                type="button"
                onClick={() => setShowLogs(!showLogs)}
                className="w-full px-4 py-2 bg-neutral-950 hover:bg-neutral-900 text-neutral-400 hover:text-neutral-200 text-xs font-mono flex items-center justify-between transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Terminal className="w-3.5 h-3.5 text-amber-400" />
                  Terminal Log Output ({logs.length} lines)
                </span>
                {showLogs ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showLogs && (
                <div className="p-3 max-h-48 overflow-y-auto font-mono text-[11px] text-neutral-300 space-y-1 bg-black/90">
                  {logs.map((log, idx) => (
                    <div key={idx} className="whitespace-pre-wrap break-all leading-tight">
                      {log}
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-neutral-800/80 bg-neutral-950/80">
          <div className="text-[11px] text-neutral-500 font-mono">
            Zero terminal commands required
          </div>

          <div className="flex items-center gap-3">
            {!isComplete ? (
              <>
                <button
                  type="button"
                  disabled={isInstalling}
                  onClick={onClose}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800/60 transition-colors disabled:opacity-50"
                >
                  Use Mock / Offline Mode
                </button>

                <button
                  type="button"
                  disabled={isInstalling || !envData?.canBootstrap}
                  onClick={handleStartInstall}
                  className="px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-neutral-950 shadow-lg shadow-amber-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all cursor-pointer font-sans"
                >
                  {isInstalling ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Installing Engine...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 fill-neutral-950" />
                      1-Click Install Engine
                    </>
                  )}
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 flex items-center gap-2 transition-all cursor-pointer"
              >
                <CheckCircle2 className="w-4 h-4" />
                Launch Studio Cockpit
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
