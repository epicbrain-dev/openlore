/**
 * backendManager.cjs
 * OpenLore Studio Desktop - Python Engine Supervisor
 * Handles discovery, lifecycle management, health monitoring, and graceful shutdown of the OpenLore daemon.
 */

const { spawn, spawnSync } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');
const os = require('os');

class BackendManager {
  constructor() {
    this.process = null;
    this.port = 8000;
    this.host = '127.0.0.1';
    this.isManaged = false;
    this.logs = [];
  }

  /**
   * Pings the OpenLore HTTP server to check if it's responsive.
   */
  async checkHealth(host = this.host, port = this.port, timeoutMs = 600) {
    return new Promise((resolve) => {
      const req = http.get(
        {
          host,
          port,
          path: '/api/catalog',
          timeout: timeoutMs,
        },
        (res) => {
          // Accept any 2xx or 4xx status as proof that the server is alive
          resolve(res.statusCode >= 200 && res.statusCode < 500);
        }
      );

      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  /**
   * Discovers the best Python executable or OpenLore shim available on the host machine.
   */
  findPythonShim() {
    if (process.env.OPENLORE_PYTHON && fs.existsSync(process.env.OPENLORE_PYTHON)) {
      return { cmd: process.env.OPENLORE_PYTHON, argsPrefix: [] };
    }

    const home = os.homedir();
    const isWin = process.platform === 'win32';

    // Check user ~/.openlore bin/openlore
    const userOpenloreBin = isWin
      ? path.join(home, '.openlore', 'bin', 'openlore.bat')
      : path.join(home, '.openlore', 'bin', 'openlore');
    if (fs.existsSync(userOpenloreBin)) {
      return { cmd: userOpenloreBin, argsPrefix: [] };
    }

    // 1. Check user ~/.openlore venv
    const userVenvPy = isWin
      ? path.join(home, '.openlore', 'venv', 'Scripts', 'python.exe')
      : path.join(home, '.openlore', 'venv', 'bin', 'python3');
    if (fs.existsSync(userVenvPy)) {
      return { cmd: userVenvPy, argsPrefix: ['-m', 'openlore.cli.main'] };
    }

    // 2. Check repo root venv (for development / studio checkout)
    const repoVenvPy = isWin
      ? path.resolve(__dirname, '..', '..', 'venv', 'Scripts', 'python.exe')
      : path.resolve(__dirname, '..', '..', 'venv', 'bin', 'python3');
    if (fs.existsSync(repoVenvPy)) {
      return { cmd: repoVenvPy, argsPrefix: ['-m', 'openlore.cli.main'] };
    }

    // 3. Check standard system locations
    const systemCandidates = isWin
      ? [
          'C:\\Python312\\python.exe',
          'C:\\Python311\\python.exe',
          'C:\\Program Files\\Python312\\python.exe',
          'py.exe',
          'python.exe',
        ]
      : [
          '/opt/homebrew/bin/python3',
          '/usr/local/bin/python3',
          '/usr/bin/python3',
          'python3',
        ];

    for (const cand of systemCandidates) {
      if (cand.includes(path.sep) && fs.existsSync(cand)) {
        return { cmd: cand, argsPrefix: ['-m', 'openlore.cli.main'] };
      }
    }

    // 4. Fallback to system command
    return { cmd: isWin ? 'python' : 'python3', argsPrefix: ['-m', 'openlore.cli.main'] };
  }

  /**
   * Starts or connects to the OpenLore backend daemon.
   */
  async start({ port = 8000, host = '127.0.0.1', onLog } = {}) {
    this.port = port;
    this.host = host;

    // Check if backend is already running
    const alreadyAlive = await this.checkHealth(host, port, 800);
    if (alreadyAlive) {
      this.isManaged = false;
      const msg = `[Desktop Engine] Found active OpenLore server already running at http://${host}:${port}`;
      if (onLog) onLog(msg);
      return { running: true, managed: false, host, port };
    }

    const shim = this.findPythonShim();
    const args = [...shim.argsPrefix, 'web', '--port', String(port), '--host', host];

    // Determine repository root or execution directory
    const home = os.homedir();
    let workingDir = path.resolve(__dirname, '..', '..');
    let pythonPath = path.join(workingDir, 'src');

    // If running inside app.asar or installed bundle where src/ does not exist:
    if (!fs.existsSync(pythonPath)) {
      if (fs.existsSync(path.join(process.cwd(), 'src'))) {
        workingDir = process.cwd();
        pythonPath = path.join(workingDir, 'src');
      } else {
        workingDir = path.join(home, '.openlore');
        pythonPath = '';
      }
    }

    // Ensure standard UNIX paths are present in GUI launcher environment
    const extraPaths = process.platform === 'win32'
      ? [path.join(home, '.openlore', 'bin'), path.join(home, '.openlore', 'venv', 'Scripts')]
      : [path.join(home, '.openlore', 'bin'), '/opt/homebrew/bin', '/usr/local/bin', path.join(home, '.openlore', 'venv', 'bin')];
    const augmentedPath = extraPaths.join(path.delimiter) + (process.env.PATH ? path.delimiter + process.env.PATH : '');

    const env = {
      ...process.env,
      PATH: augmentedPath,
      PYTHONUNBUFFERED: '1',
      ...(pythonPath ? { PYTHONPATH: pythonPath + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : '') } : {}),
    };

    const startMsg = `[Desktop Engine] Spawning OpenLore daemon: ${shim.cmd} ${args.join(' ')}`;
    if (onLog) onLog(startMsg);

    try {
      this.process = spawn(shim.cmd, args, {
        cwd: workingDir,
        env,
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      this.isManaged = true;

      const handleData = (chunk) => {
        const text = chunk.toString().trim();
        if (text) {
          this.logs.push(text);
          if (this.logs.length > 500) this.logs.shift();
          if (onLog) onLog(text);
        }
      };

      this.process.stdout.on('data', handleData);
      this.process.stderr.on('data', handleData);

      this.process.on('close', (code, signal) => {
        const exitMsg = `[Desktop Engine] Process exited with code: ${code}, signal: ${signal}`;
        if (onLog) onLog(exitMsg);
        this.process = null;
        this.isManaged = false;
      });

      // Poll until the server responds or timeout reached (10s)
      const maxRetries = 40;
      for (let i = 0; i < maxRetries; i++) {
        await new Promise((r) => setTimeout(r, 250));
        if (await this.checkHealth(host, port, 400)) {
          if (onLog) onLog(`[Desktop Engine] ✅ Backend successfully ready at http://${host}:${port}`);
          return { running: true, managed: true, host, port };
        }
        if (!this.process) {
          throw new Error('OpenLore backend terminated unexpectedly during startup.');
        }
      }

      throw new Error(`OpenLore backend did not become responsive on port ${port} within 10 seconds.`);
    } catch (err) {
      if (onLog) onLog(`[Desktop Engine] ⚠️ Failed to launch local backend: ${err.message}`);
      return { running: false, managed: false, error: err.message, host, port };
    }
  }

  /**
   * Gracefully shuts down the background Python process.
   */
  async stop() {
    if (!this.process || !this.isManaged) {
      return;
    }

    return new Promise((resolve) => {
      const proc = this.process;
      this.process = null;
      this.isManaged = false;

      let forceKillTimeout;

      const onExit = () => {
        clearTimeout(forceKillTimeout);
        resolve();
      };

      proc.once('exit', onExit);

      // Attempt graceful SIGINT first
      try {
        proc.kill('SIGINT');
      } catch (e) {
        // Ignored
      }

      // Force kill if it doesn't terminate within 2 seconds
      forceKillTimeout = setTimeout(() => {
        try {
          proc.kill('SIGKILL');
        } catch (e) {
          // Ignored
        }
        resolve();
      }, 2000);
    });
  }

  /**
   * Probes the system environment to determine whether Python is available,
   * whether the OpenLore engine is installed, and current daemon health.
   */
  async detectEnvironment() {
    const isWin = process.platform === 'win32';
    const home = os.homedir();
    const openloreDir = path.join(home, '.openlore');
    const venvPython = isWin
      ? path.join(openloreDir, 'venv', 'Scripts', 'python.exe')
      : path.join(openloreDir, 'venv', 'bin', 'python3');

    const isVenvInstalled = fs.existsSync(venvPython);
    const isDaemonRunning = await this.checkHealth(this.host, this.port, 400);

    // Find host Python 3 executable
    let systemPython = null;
    let pythonVersion = null;

    const candidates = isWin
      ? ['python.exe', 'py.exe', 'C:\\Python312\\python.exe', 'C:\\Python311\\python.exe', 'C:\\Program Files\\Python312\\python.exe']
      : ['python3', '/opt/homebrew/bin/python3', '/usr/local/bin/python3', '/usr/bin/python3'];

    for (const cand of candidates) {
      try {
        const check = spawnSync(cand, ['--version'], { encoding: 'utf-8', timeout: 3000 });
        if (check.status === 0 && (check.stdout || check.stderr)) {
          systemPython = cand;
          pythonVersion = (check.stdout || check.stderr).trim();
          break;
        }
      } catch (e) {
        // Continue
      }
    }

    return {
      os: process.platform,
      arch: process.arch,
      home,
      openloreDir,
      isVenvInstalled,
      isDaemonRunning,
      systemPython,
      pythonVersion,
      canBootstrap: Boolean(systemPython),
    };
  }

  /**
   * Bootstraps the OpenLore engine in ~/.openlore using installer.py.
   */
  async bootstrapEngine({ onLog, onProgress } = {}) {
    const env = await this.detectEnvironment();
    if (!env.systemPython) {
      throw new Error('Python 3.9+ was not found on your system. Please install Python to bootstrap OpenLore.');
    }

    // Locate installer.py (either bundled in web/electron/installer.py or root installer.py)
    let installerPath = path.join(__dirname, 'installer.py');
    if (!fs.existsSync(installerPath)) {
      installerPath = path.resolve(__dirname, '..', '..', 'installer.py');
    }
    if (!fs.existsSync(installerPath)) {
      throw new Error('Could not locate installer.py bundle.');
    }

    const home = os.homedir();
    const openloreDir = path.join(home, '.openlore');
    const args = [
      installerPath,
      '--yes',
      '--prefix',
      openloreDir,
      '--no-modify-path',
      '--with-dcc',
      'all',
    ];

    if (onLog) onLog(`[Bootstrapper] Executing: ${env.systemPython} ${args.join(' ')}`);
    if (onProgress) onProgress({ step: 1, totalSteps: 4, label: 'Initializing isolated Python runtime (~/.openlore/venv)...', percent: 15 });

    return new Promise((resolve, reject) => {
      const proc = spawn(env.systemPython, args, {
        cwd: home,
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1',
        },
      });

      proc.stdout.on('data', (chunk) => {
        const text = chunk.toString().trim();
        if (!text) return;
        if (onLog) onLog(text);

        if (text.includes('Creating virtual environment') || text.includes('Setting up isolated')) {
          if (onProgress) onProgress({ step: 1, totalSteps: 4, label: 'Creating isolated virtual environment...', percent: 25 });
        } else if (text.includes('Installing OpenLore') || text.includes('pip install')) {
          if (onProgress) onProgress({ step: 2, totalSteps: 4, label: 'Downloading & installing OpenLore v2.0.0 engine...', percent: 55 });
        } else if (text.includes('Exporting DCC') || text.includes('Scaffolding') || text.includes('Sidecars')) {
          if (onProgress) onProgress({ step: 3, totalSteps: 4, label: 'Configuring DCC Live Link connectors (Blender, Maya, Unreal)...', percent: 80 });
        }
      });

      proc.stderr.on('data', (chunk) => {
        const text = chunk.toString().trim();
        if (text && onLog) onLog(`[Error] ${text}`);
      });

      proc.on('close', async (code) => {
        if (code !== 0) {
          return reject(new Error(`Installer process exited with code ${code}`));
        }

        if (onProgress) onProgress({ step: 4, totalSteps: 4, label: 'Starting OpenLore engine daemon...', percent: 95 });
        if (onLog) onLog('[Bootstrapper] Installation complete. Launching local daemon...');

        try {
          const res = await this.start({ onLog });
          if (onProgress) onProgress({ step: 4, totalSteps: 4, label: 'Connected! Engine is online.', percent: 100 });
          resolve(res);
        } catch (e) {
          reject(e);
        }
      });
    });
  }

  getStatus() {
    return {
      running: this.isManaged ? (this.process !== null) : null,
      managed: this.isManaged,
      host: this.host,
      port: this.port,
      pid: this.process ? this.process.pid : null,
    };
  }
}

module.exports = new BackendManager();
