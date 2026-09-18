/**
 * preload.cjs
 * OpenLore Studio Desktop - Secure IPC Bridge
 * Exposes native desktop capabilities safely to the React frontend.
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('openloreDesktop', {
  isDesktop: true,
  platform: process.platform,

  /**
   * Prompts the native OS file picker.
   * @param {Object} options - { title, filters, properties }
   */
  openFileDialog: (options = {}) => ipcRenderer.invoke('dialog:openFile', options),

  /**
   * Prompts the native OS directory picker.
   * @param {Object} options - { title }
   */
  openDirectoryDialog: (options = {}) => ipcRenderer.invoke('dialog:openDirectory', options),

  /**
   * Gets current backend daemon status & PID.
   */
  getBackendStatus: () => ipcRenderer.invoke('backend:getStatus'),

  /**
   * Restarts the local OpenLore backend daemon.
   */
  restartBackend: () => ipcRenderer.invoke('backend:restart'),

  /**
   * Listens for log lines emitted by the local backend process.
   */
  onBackendLog: (callback) => {
    const handler = (_event, message) => callback(message);
    ipcRenderer.on('backend:log', handler);
    return () => ipcRenderer.removeListener('backend:log', handler);
  },

  /**
   * Listens for stage file opened via OS menu shortcut (Cmd/Ctrl+O).
   */
  onStageOpened: (callback) => {
    const handler = (_event, path) => callback(path);
    ipcRenderer.on('stage:opened', handler);
    return () => ipcRenderer.removeListener('stage:opened', handler);
  },

  /**
   * Listens for studio repo opened via OS menu shortcut (Cmd/Ctrl+Shift+O).
   */
  onRepoOpened: (callback) => {
    const handler = (_event, path) => callback(path);
    ipcRenderer.on('repo:opened', handler);
    return () => ipcRenderer.removeListener('repo:opened', handler);
  },

  /**
   * Opens an external link safely in the user's default browser.
   */
  openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),
});
