#!/usr/bin/env pwsh
# Financial Statement Transcription Tool - Local Startup Script
# Automatically handles port conflicts and starts fresh Streamlit instance

Write-Host "🚀 Starting Financial Statement Transcription Tool..." -ForegroundColor Green

# Function to kill processes using specific port
function Stop-ProcessOnPort {
    param([int]$Port)
    
    Write-Host "🔍 Checking for existing processes on port $Port..." -ForegroundColor Yellow
    
    $processes = netstat -ano | Select-String ":$Port\s" | ForEach-Object {
        $line = $_.Line.Trim()
        if ($line -match "\s+(\d+)$") {
            $matches[1]
        }
    }
    
    if ($processes) {
        foreach ($pid in $processes) {
            try {
                Write-Host "🔴 Killing process $pid using port $Port..." -ForegroundColor Red
                taskkill /PID $pid /F | Out-Null
                Write-Host "✅ Process $pid terminated successfully" -ForegroundColor Green
            }
            catch {
                Write-Host "⚠️  Could not kill process $pid" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "✅ Port $Port is free" -ForegroundColor Green
    }
}

# Kill any existing Streamlit processes
Write-Host "🧹 Cleaning up existing Streamlit processes..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 8560

# Also kill any remaining python processes that might be Streamlit
$pythonProcesses = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*streamlit*" } 2>$null
if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        try {
            Write-Host "🔴 Killing remaining Streamlit process $($proc.Id)..." -ForegroundColor Red
            Stop-Process -Id $proc.Id -Force
        }
        catch {
            Write-Host "⚠️  Could not kill process $($proc.Id)" -ForegroundColor Yellow
        }
    }
}

# Wait a moment for cleanup
Start-Sleep -Seconds 2

# Start Streamlit
Write-Host "🌟 Starting Streamlit on http://localhost:8560..." -ForegroundColor Cyan
Write-Host "📱 The app will open automatically in your browser" -ForegroundColor Cyan
Write-Host "🛑 Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host "" 

try {
    streamlit run app.py --server.port 8560 --server.headless false
}
catch {
    Write-Host "❌ Failed to start Streamlit. Make sure it's installed:" -ForegroundColor Red
    Write-Host "   pip install streamlit" -ForegroundColor White
    exit 1
} 