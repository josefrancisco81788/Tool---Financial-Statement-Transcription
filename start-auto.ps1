#!/usr/bin/env pwsh
# Auto-Port Streamlit Launcher
# Automatically finds an available port and starts the app

Write-Host "🚀 Auto-Port Streamlit Launcher" -ForegroundColor Green

function Test-Port {
    param([int]$Port)
    $result = netstat -an | Select-String ":$Port\s"
    return $result.Count -eq 0
}

function Find-AvailablePort {
    param([int]$StartPort = 8560)
    
    for ($port = $StartPort; $port -le ($StartPort + 50); $port++) {
        if (Test-Port -Port $port) {
            return $port
        }
    }
    return $null
}

# Find available port
$availablePort = Find-AvailablePort
if ($availablePort) {
    Write-Host "✅ Found available port: $availablePort" -ForegroundColor Green
    Write-Host "🌟 Starting Streamlit on http://localhost:$availablePort..." -ForegroundColor Cyan
    
    # Open browser automatically
    Start-Process "http://localhost:$availablePort"
    
    streamlit run app.py --server.port $availablePort
} else {
    Write-Host "❌ No available ports found in range 8560-8610" -ForegroundColor Red
    Write-Host "💡 Try manually killing processes or restart your computer" -ForegroundColor Yellow
} 