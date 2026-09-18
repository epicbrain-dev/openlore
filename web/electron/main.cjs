/**
 * main.cjs
 * OpenLore Studio Desktop - Electron Main Entrypoint
 * Cross-platform desktop runtime for macOS, Windows, and Linux.
 */

const { app, BrowserWindow, Menu, dialog, shell, ipcMain, session } = require('electron');
const path = require('path');
const fs = require('fs');
const backendManager = require('./backendManager.cjs');

// Enforce single-instance lock so multiple studios don't conflict on ports
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
}

let mainWindow = null;
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function createMainWindow() {
  const iconPath = path.join(__dirname, '..', 'build', 'icon.png');

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1024,
    minHeight: 700,
    title: 'OpenLore Studio Cockpit',
    backgroundColor: '#09090b',
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    trafficLightPosition: { x: 14, y: 14 },
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
      devTools: true,
    },
  });

  // Enable graceful display once content is loaded
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Handle external links by opening them in the system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Automatically route /api/* requests to local Python daemon in production
  try {
    session.defaultSession.webRequest.onBeforeRequest(
      { urls: ['file:///api/*', 'file://*/api/*'] },
      (details, callback) => {
        try {
          const u = new URL(details.url);
          const redirectUrl = `http://127.0.0.1:8000${u.pathname}${u.search}`;
          callback({ redirectURL: redirectUrl });
        } catch (e) {
          callback({});
        }
      }
    );
  } catch (e) {
    // Non-fatal if session filter cannot attach
  }

  if (isDev && process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  setupMenu();
}

function setupMenu() {
  const isMac = process.platform === 'darwin';

  const template = [
    ...(isMac
      ? [
          {
            label: app.name,
            submenu: [
              { role: 'about', label: 'About OpenLore Studio' },
              { type: 'separator' },
              { role: 'services' },
              { type: 'separator' },
              { role: 'hide', label: 'Hide OpenLore' },
              { role: 'hideOthers' },
              { role: 'unhide' },
              { type: 'separator' },
              { role: 'quit', label: 'Quit OpenLore Studio' },
            ],
          },
        ]
      : []),
    {
      label: 'File',
      submenu: [
        {
          label: 'Open USD Stage...',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            if (!mainWindow) return;
            const result = await dialog.showOpenDialog(mainWindow, {
              title: 'Open OpenUSD Stage',
              properties: ['openFile'],
              filters: [
                { name: 'OpenUSD Stage', extensions: ['usda', 'usdc', 'usd'] },
                { name: 'All Files', extensions: ['*'] },
              ],
            });
            if (!result.canceled && result.filePaths.length > 0) {
              mainWindow.webContents.send('stage:opened', result.filePaths[0]);
            }
          },
        },
        {
          label: 'Open Studio Repository...',
          accelerator: 'CmdOrCtrl+Shift+O',
          click: async () => {
            if (!mainWindow) return;
            const result = await dialog.showOpenDialog(mainWindow, {
              title: 'Select OpenLore Repository Root',
              properties: ['openDirectory'],
            });
            if (!result.canceled && result.filePaths.length > 0) {
              mainWindow.webContents.send('repo:opened', result.filePaths[0]);
            }
          },
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' },
      ],
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Engine',
      submenu: [
        {
          label: 'Restart OpenLore Backend Daemon',
          click: async () => {
            if (mainWindow) {
              mainWindow.webContents.send('backend:log', '[Desktop] Restarting OpenLore backend...');
            }
            await backendManager.stop();
            await backendManager.start({
              onLog: (msg) => {
                if (mainWindow && !mainWindow.isDestroyed()) {
                  mainWindow.webContents.send('backend:log', msg);
                }
              },
            });
          },
        },
        {
          label: 'Engine Status...',
          click: async () => {
            const status = backendManager.getStatus();
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'OpenLore Engine Status',
              message: `Host: ${status.host}:${status.port}\nManaged: ${status.managed}\nPID: ${status.pid || 'N/A'}\nStatus: ${status.running ? 'Connected' : 'External/Inactive'}`,
            });
          },
        },
      ],
    },
    {
      role: 'help',
      submenu: [
        {
          label: 'OpenLore Documentation',
          click: async () => {
            await shell.openExternal('https://github.com/epicbrain-dev/openlore');
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC Handlers
ipcMain.handle('dialog:openFile', async (_event, options = {}) => {
  if (!mainWindow) return { canceled: true, filePaths: [] };
  return dialog.showOpenDialog(mainWindow, {
    title: options.title || 'Open File',
    properties: options.properties || ['openFile'],
    filters: options.filters || [
      { name: 'USD Files', extensions: ['usda', 'usdc', 'usd'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  });
});

ipcMain.handle('dialog:openDirectory', async (_event, options = {}) => {
  if (!mainWindow) return { canceled: true, filePaths: [] };
  return dialog.showOpenDialog(mainWindow, {
    title: options.title || 'Select Folder',
    properties: ['openDirectory'],
  });
});

ipcMain.handle('backend:getStatus', async () => {
  return backendManager.getStatus();
});

ipcMain.handle('backend:restart', async () => {
  await backendManager.stop();
  return backendManager.start({
    onLog: (msg) => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('backend:log', msg);
      }
    },
  });
});

ipcMain.handle('shell:openExternal', async (_event, url) => {
  return shell.openExternal(url);
});

// Second instance focus
app.on('second-instance', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

app.whenReady().then(async () => {
  createMainWindow();

  // Spin up Python backend supervisor asynchronously
  backendManager.start({
    onLog: (msg) => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('backend:log', msg);
      }
    },
  }).catch((err) => {
    console.error('Failed to initialize OpenLore backend manager:', err);
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

// Graceful cleanup on quit
let isCleaningUp = false;
app.on('before-quit', async (e) => {
  if (!isCleaningUp) {
    e.preventDefault();
    isCleaningUp = true;
    try {
      await backendManager.stop();
    } finally {
      app.quit();
    }
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
