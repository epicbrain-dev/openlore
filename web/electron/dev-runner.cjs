/**
 * dev-runner.cjs
 * Cross-platform runner for launching Electron against the active Vite dev server.
 */

const { spawn } = require('child_process');
const electron = require('electron');
const path = require('path');

process.env.VITE_DEV_SERVER_URL = 'http://localhost:5173';
process.env.NODE_ENV = 'development';

const projectRoot = path.resolve(__dirname, '..');
const child = spawn(electron, [projectRoot], {
  stdio: 'inherit',
  env: process.env,
});

child.on('close', (code) => {
  process.exit(code || 0);
});
