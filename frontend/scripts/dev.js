import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

const frontendRoot = process.cwd()
const projectRoot = resolve(frontendRoot, '..')
const viteBin = resolve(frontendRoot, 'node_modules', 'vite', 'bin', 'vite.js')
const statusUrl = 'http://127.0.0.1:8000/status'

const pythonCandidates = [
  resolve(projectRoot, '.venv', 'Scripts', 'python.exe'),
  resolve(projectRoot, '.venv311', 'Scripts', 'python.exe'),
  'python',
]

function pickPython() {
  for (const candidate of pythonCandidates) {
    if (candidate === 'python' || existsSync(candidate)) {
      return candidate
    }
  }

  return 'python'
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

const python = pickPython()
const backendAlreadyRunning = await isBackendReady()
let backendProcess = null

if (!backendAlreadyRunning) {
  console.log('[dev] Starting backend on http://127.0.0.1:8000 ...')
  backendProcess = spawnProcess(python, [
    '-m',
    'uvicorn',
    'api:app',
    '--host',
    '127.0.0.1',
    '--port',
    '8000',
    '--log-level',
    'warning',
    '--no-access-log',
  ], {
    cwd: projectRoot,
    env: {
      ...process.env,
      SMART_ACCESS_DEBUG: process.env.SMART_ACCESS_DEBUG ?? '0',
      OPENBLAS_NUM_THREADS: process.env.OPENBLAS_NUM_THREADS ?? '1',
      OMP_NUM_THREADS: process.env.OMP_NUM_THREADS ?? '1',
    },
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