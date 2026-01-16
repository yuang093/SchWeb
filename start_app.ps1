<#
.SYNOPSIS
    Schwab AI Dashboard 通用啟動腳本
.DESCRIPTION
    自動偵測路徑與虛擬環境，適用於多台電腦與不同部署環境。
    無需修改即可在任何已安裝依賴的環境中執行。
#>

# 1. 取得腳本所在的「根目錄」 (這是通用化的關鍵)
$ScriptRoot = $PSScriptRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Schwab AI Dashboard - 通用啟動腳本" -ForegroundColor Cyan
Write-Host "=========================================="
Write-Host "工作目錄: $ScriptRoot" -ForegroundColor Gray

# ---------------------------------------------------------
# 2. 智慧偵測 Python 虛擬環境 (Venv)
# ---------------------------------------------------------
# 定義可能的虛擬環境路徑清單 (優先順序：backend內 -> 根目錄 -> 隱藏檔)
$VenvCandidates = @(
    "$ScriptRoot\backend\venv\Scripts\Activate.ps1",
    "$ScriptRoot\venv\Scripts\Activate.ps1",
    "$ScriptRoot\backend\.venv\Scripts\Activate.ps1",
    "$ScriptRoot\.venv\Scripts\Activate.ps1"
)

$VenvPath = $null
foreach ($Path in $VenvCandidates) {
    if (Test-Path $Path) {
        $VenvPath = $Path
        break
    }
}

# 準備後端啟動指令
if ($VenvPath) {
    Write-Host "✅ 偵測到虛擬環境: $VenvPath" -ForegroundColor Green
    # 組合指令：進入 backend -> 啟動 venv -> 跑 server
    $BackendCommand = "
        cd '$ScriptRoot\backend'; 
        . '$VenvPath'; 
        Write-Host '正在啟動後端 (Port 8000)...' -ForegroundColor Green;
        python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    "
} else {
    Write-Host "⚠️ 警告: 未偵測到虛擬環境 (venv)，將嘗試使用系統全域 Python..." -ForegroundColor Yellow
    $BackendCommand = "
        cd '$ScriptRoot\backend'; 
        Write-Host '正在使用系統 Python 啟動後端...' -ForegroundColor Yellow;
        python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
    "
}

# ---------------------------------------------------------
# 3. 啟動後端 (開新視窗)
# ---------------------------------------------------------
Start-Process powershell -ArgumentList "-NoExit", "-Command", $BackendCommand

# ---------------------------------------------------------
# 4. 啟動前端 (開新視窗)
# ---------------------------------------------------------
# 檢查 package.json 是否存在
if (Test-Path "$ScriptRoot\frontend\package.json") {
    $FrontendCommand = "
        cd '$ScriptRoot\frontend';
        Write-Host '正在啟動前端 (Port 5173)...' -ForegroundColor Green;
        npm run dev -- --port 5173
    "
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $FrontendCommand
} else {
    Write-Host "❌ 錯誤: 找不到 '$ScriptRoot\frontend\package.json'，無法啟動前端。" -ForegroundColor Red
}

# ---------------------------------------------------------
# 5. 顯示連線資訊
# ---------------------------------------------------------
# 獲取本機 IPv4 (過濾掉虛擬網卡與 Docker)
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.InterfaceAlias -match 'Wi-Fi|Ethernet|乙太網路' -and $_.IPAddress -notmatch '169.254' 
} | Select-Object -First 1).IPAddress

if (-not $localIP) {
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '127.0.0.1' } | Select-Object -First 1).IPAddress
}

Write-Host ""
Write-Host "🚀 服務已發送啟動指令！請檢查跳出的視窗是否運作正常。" -ForegroundColor White
Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "本機存取 (PC):     http://localhost:5173" -ForegroundColor Cyan
if ($localIP) {
    Write-Host "手機/區網存取 (LAN): http://$($localIP):5173" -ForegroundColor Yellow
    Write-Host "API 接口位置:      http://$($localIP):8000" -ForegroundColor Yellow
}
Write-Host "------------------------------------------------" -ForegroundColor Cyan
Write-Host "提示: 若要關閉服務，請直接關閉跳出的兩個 PowerShell 視窗。" -ForegroundColor Gray