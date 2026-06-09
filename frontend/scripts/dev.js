import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

const frontendRoot = process.cwd()
const projectRoot = resolve(frontendRoot, '..')
const viteBin = resolve(frontendRoot, 'node_modules', 'vite', 'bin', 'vite.js')
const statusUrl = 'http://127.0.0.1:8000/status'

// Resolve the Python interpreter to run `python -m uvicorn ...`.
// The venv interpreter is preferred because that is where the project deps
// (uvicorn, fastapi, face_recognition, ...) are installed.
function pickPython() {
  const candidates = [
    resolve(projectRoot, '.venv', 'Scripts', 'python.exe'), // Windows venv
    resolve(projectRoot, '.venv', 'bin', 'python'),          // POSIX venv
    resolve(projectRoot, '.venv311', 'Scripts', 'python.exe'),
    resolve(projectRoot, '.venv311', 'bin', 'python'),
    'python',
  ]
  return candidates.find(c => c === 'python' || existsSync(c)) ?? 'python'
}

async function isBackendReady() {
  try {
    const response = await fetch(statusUrl)
    return response.ok
  } catch {
    return false
  }
}

async function waitForBackend(timeoutMs = 30000) {
  const startedAt = Date.now()

  while (Date.now() - startedAt < timeoutMs) {
    if (await isBackendReady()) {
      return true
    }

    await new Promise((resolve) => setTimeout(resolve, 500))
  }

  return false
}

function spawnProcess(command, args, options = {}) {
  return spawn(command, args, {
    stdio: 'inherit',
    shell: false,
    ...options,
  })
}

// When this script runs inside an *activated* venv (e.g. VS Code's integrated
// terminal auto-activates it), the shell injects venv vars. On uv-managed venvs
// some of these carry a quoted interpreter path that the uv launcher trampoline
// misreads, producing: No Python at '"C:\...\python.exe'  (exit 103).
// Build a clean env that drops the activation vars and strips the venv's Scripts
// dir from PATH, so the interpreter resolves itself from pyvenv.cfg.
function cleanBackendEnv() {
  const env = { ...process.env }
  for (const key of ['VIRTUAL_ENV', 'VIRTUAL_ENV_PROMPT', 'PYTHONHOME', '__PYVENV_LAUNCHER__', 'PYVENV_LAUNCHER']) {
    delete env[key]
  }

  // Drop any venv Scripts/bin dir from PATH so it can't shadow or confuse resolution.
  const venvDirs = [
    resolve(projectRoot, '.venv', 'Scripts').toLowerCase(),
    resolve(projectRoot, '.venv', 'bin').toLowerCase(),
  ]
  const pathKey = Object.keys(env).find(k => k.toLowerCase() === 'path') ?? 'PATH'
  const sep = process.platform === 'win32' ? ';' : ':'
  if (env[pathKey]) {
    env[pathKey] = env[pathKey]
      .split(sep)
      .filter(p => !venvDirs.includes(p.replace(/[/\\]+$/, '').toLowerCase()))
      .join(sep)
  }

  env.SMART_ACCESS_DEBUG = process.env.SMART_ACCESS_DEBUG ?? '0'
  env.OPENBLAS_NUM_THREADS = process.env.OPENBLAS_NUM_THREADS ?? '1'
  env.OMP_NUM_THREADS = process.env.OMP_NUM_THREADS ?? '1'
  return env
}

const python = pickPython()
const backendAlreadyRunning = await isBackendReady()
let backendProcess = null

if (!backendAlreadyRunning) {
  console.log(`[dev] Starting backend on http://127.0.0.1:8000 ... (python: ${python})`)
  backendProcess = spawnProcess(python, [
    '-m', 'uvicorn', 'api:app',
    '--host', '127.0.0.1',
    '--port', '8000',
    '--log-level', 'warning',
    '--no-access-log',
  ], {
    cwd: projectRoot,
    env: cleanBackendEnv(),
  })

  backendProcess.on('exit', (code, signal) => {
    if (code !== 0 && signal !== 'SIGTERM' && signal !== 'SIGINT') {
      console.error(`[dev] Backend exited with code ${code ?? 'unknown'}`)
    }
  })

  const ready = await waitForBackend()
  if (!ready) {
    console.error('[dev] Backend did not become ready at http://127.0.0.1:8000/status')
    if (backendProcess) {
      backendProcess.kill('SIGTERM')
    }
    process.exit(1)
  }
  console.log('[dev] Backend is ready.')
} else {
  console.log('[dev] Backend already responding on http://127.0.0.1:8000')
}

const viteProcess = spawnProcess(process.execPath, [viteBin], {
  cwd: frontendRoot,
  env: process.env,
})

const shutdown = (signal) => {
  if (viteProcess && !viteProcess.killed) {
    viteProcess.kill(signal)
  }

  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill(signal)
  }
}

process.on('SIGINT', () => shutdown('SIGINT'))
process.on('SIGTERM', () => shutdown('SIGTERM'))
process.on('exit', () => shutdown('SIGTERM'))

viteProcess.on('exit', (code, signal) => {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill('SIGTERM')
  }

  if (code !== null) {
    process.exit(code)
  }

  if (signal) {
    process.kill(process.pid, signal)
  }
})