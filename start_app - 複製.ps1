# Schwab AI Investment Dashboard - 一鍵啟動腳本

# 1. 啟動後端伺服器 (FastAPI)
# 修正為 --host 0.0.0.0 以支援區域網路存取
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Write-Host '正在啟動後端服務...';
    cd backend;
    if (Test-Path '../venv/Scripts/Activate.ps1') {
        . ../venv/Scripts/Activate.ps1
    }
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
"

# 2. 啟動前端開發伺服器 (Vite)
# Vite 已在 package.json 設定 --host
Start-Process powershell -ArgumentList "-NoExit", "-Command", "
    Write-Host '正在啟動前端服務...';
    cd frontend;
    npm run dev -- --port 5173
"

# 3. 獲取本機 IPv4 位址
$localIP = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias '乙太網路', 'Wi-Fi' | Select-Object -First 1).IPAddress
if (-not $localIP) {
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '127.0.0.1' } | Select-Object -First 1).IPAddress
}

Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "服務啟動中..." -ForegroundColor Cyan
Write-Host "後端位址 (Local): http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "前端位址 (Local): http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 手機測試區域網路位址:" -ForegroundColor Yellow
Write-Host "前端網址: http://$($localIP):5173" -ForegroundColor Yellow
Write-Host "後端 API : http://$($localIP):8000" -ForegroundColor Yellow
Write-Host "------------------------------------------------" -ForegroundColor Cyan
