# Smart Access System - Startup Script
# Run from the project folder that contains this script

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

# Activate venv
& ".\.venv\Scripts\Activate.ps1"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Smart Access System - Quick Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Choose what to do:`n" -ForegroundColor Yellow
Write-Host "1. Test all packages and APIs" -ForegroundColor White
Write-Host "2. Start API only (for testing /logs endpoint)" -ForegroundColor White
Write-Host "3. Start Camera System only (requires webcam)" -ForegroundColor White
Write-Host "4. Start both API and Camera System" -ForegroundColor White
Write-Host "`nEnter choice (1-4): " -NoNewline -ForegroundColor Yellow

$choice = Read-Host

switch ($choice) {
    "1" {
        Write-Host "`n>>> Testing imports..." -ForegroundColor Cyan
        python -c "import cv2,fastapi,uvicorn,numpy,face_recognition; print('✓ All packages OK')"
        
        Write-Host "`n>>> Starting test API..." -ForegroundColor Cyan
        $proc = Start-Process -FilePath python -ArgumentList '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8000' -PassThru
        Write-Host "✓ API started (PID: $($proc.Id))" -ForegroundColor Green
        
        Write-Host "`n>>> Testing endpoints..." -ForegroundColor Cyan
        Start-Sleep -Milliseconds 2000
        $urls = @('http://127.0.0.1:8000/docs', 'http://127.0.0.1:8000/logs')
        foreach ($url in $urls) {
            try {
                $resp = Invoke-WebRequest -Uri $url -TimeoutSec 2
                Write-Host "✓ $url -> HTTP $($resp.StatusCode)" -ForegroundColor Green
            }
            catch {
                Write-Host "✗ $url -> Failed" -ForegroundColor Red
            }
        }
        
        Write-Host "`n>>> Testing webcam..." -ForegroundColor Cyan
        python -c "import cv2; cap=cv2.VideoCapture(0); ok=cap.isOpened(); cap.release(); print(f'✓ Webcam available: {ok}' if ok else '✗ Webcam NOT available')"
        
        Write-Host "`n>>> Stopping test API..." -ForegroundColor Cyan
        Stop-Process -Id $proc.Id -Force
        Write-Host "✓ API stopped" -ForegroundColor Green
    }
    
    "2" {
        Write-Host "`n>>> Starting API..." -ForegroundColor Cyan
        Write-Host "Open browser at: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow
        python -m uvicorn api:app --host 127.0.0.1 --port 8000
    }
    
    "3" {
        Write-Host "`n>>> Starting Camera System..." -ForegroundColor Cyan
        Write-Host "A webcam window will open." -ForegroundColor Yellow
        Write-Host "Press ESC to stop`n" -ForegroundColor Yellow
        python main.py
    }
    
    "4" {
        Write-Host "`n>>> Starting API in background..." -ForegroundColor Cyan
        $apiProc = Start-Process -FilePath python -ArgumentList '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8000' -PassThru
        Write-Host "✓ API started (PID: $($apiProc.Id))" -ForegroundColor Green
        Write-Host "✓ API docs at: http://127.0.0.1:8000/docs" -ForegroundColor Green
        Write-Host "✓ Logs endpoint at: http://127.0.0.1:8000/logs" -ForegroundColor Green
        
        Start-Sleep -Milliseconds 1000
        
        Write-Host "`n>>> Starting Camera System..." -ForegroundColor Cyan
        Write-Host "Webcam window will open. Press ESC to stop." -ForegroundColor Yellow
        Write-Host "API will keep running in background.`n" -ForegroundColor Yellow
        python main.py
        
        Write-Host "`n>>> Stopping API..." -ForegroundColor Cyan
        Stop-Process -Id $apiProc.Id -Force
        Write-Host "✓ API stopped" -ForegroundColor Green
    }
    
    default {
        Write-Host "`nInvalid choice. Exiting." -ForegroundColor Red
    }
}

Write-Host "`nDone!" -ForegroundColor Cyan
