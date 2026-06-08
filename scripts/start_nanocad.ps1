#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Запускает nanoCAD с загруженным .NET плагином CadEngine.Plugin.

.DESCRIPTION
    Скрипт проверяет:
    1. Установлен ли nanoCAD
    2. Прописан ли плагин в nCad.ini (если нет — добавляет)
    3. Запущен ли процесс nanoCAD (если нет — запускает)
    4. Доступен ли HTTP API плагина (ждёт до 30 сек)

.PARAMETER NoWait
    Не ждать готовности HTTP API после запуска nanoCAD.

.PARAMETER NoInstall
    Не добавлять плагин в nCad.ini автоматически.

.PARAMETER PluginPath
    Путь к CadEngine.Plugin.dll. По умолчанию ищет в репозитории.

.EXAMPLE
    # Полный запуск с проверкой
    ./scripts/start_nanocad.ps1

.EXAMPLE
    # Только проверить и запустить nanoCAD, не ждать API
    ./scripts/start_nanocad.ps1 -NoWait

.NOTES
    Repo root: предполагается, что скрипт запускается из корня репозитория.
#>

param(
    [switch]$NoWait,
    [switch]$NoInstall,
    [string]$PluginPath = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path "$PSScriptRoot\.."

# ── 1. Найти nanoCAD ──────────────────────────────────────────
$ncadPaths = @(
    "$env:PROGRAMFILES\nanoCAD\nanoCAD 26\nCad.exe",
    "$env:LOCALAPPDATA\Programs\nanoCAD\nanoCAD 26\nCad.exe",
    "$repoRoot\nanoCAD\nCad.exe",
    "C:\nanoCAD\nanoCAD 26\nCad.exe"
)

$ncadExe = $null
foreach ($p in $ncadPaths) {
    if (Test-Path $p) { $ncadExe = $p; break }
}

if (-not $ncadExe) {
    Write-Warning "nanoCAD 26 не найден. Укажите путь вручную:"
    Write-Warning "  .\scripts\start_nanocad.ps1 -ncadExe C:\path\to\nCad.exe"
    exit 1
}
Write-Host "[1/4] nanoCAD найден: $ncadExe" -ForegroundColor Green

# ── 2. Найти .NET плагин ──────────────────────────────────────
if (-not $PluginPath) {
    $candidates = @(
        "$repoRoot\engine\dist\CadEngine.Plugin.dll",
        "$repoRoot\engine\CadEngine.Plugin\bin\Release\CadEngine.Plugin.dll",
        "$repoRoot\engine\CadEngine.Plugin\bin\Debug\CadEngine.Plugin.dll"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $PluginPath = (Resolve-Path $c).Path; break }
    }
}
if (-not (Test-Path $PluginPath)) {
    Write-Error "Плагин не найден. Соберите: dotnet build engine\CadEngine.Plugin"
    exit 1
}
Write-Host "[2/4] Плагин найден: $PluginPath" -ForegroundColor Green

# ── 3. Прописать в nCad.ini ───────────────────────────────────
$ncadDir = Split-Path $ncadExe -Parent
$iniPath = "$ncadDir\nCad.ini"

if (-not $NoInstall -and (Test-Path $iniPath)) {
    $iniContent = Get-Content $iniPath -Raw -Encoding UTF8
    $sectionName = '[\NetModules]'
    $dllEntry = "CadEngine.Plugin=$PluginPath"

    if ($iniContent -match [regex]::Escape($dllEntry)) {
        Write-Host "[3/4] Плагин уже прописан в nCad.ini" -ForegroundColor Green
    } else {
        if ($iniContent -match [regex]::Escape($sectionName)) {
            # Секция есть — добавляем после неё
            $iniContent = $iniContent -replace "($([regex]::Escape($sectionName))\r?\n)", "`$1$dllEntry`r`n"
        } else {
            # Секции нет — добавляем в конец
            $iniContent = "$iniContent`r`n$sectionName`r`n$dllEntry`r`n"
        }
        Set-Content $iniPath -Value $iniContent -Encoding UTF8
        Write-Host "[3/4] Плагин прописан в nCad.ini: $iniPath" -ForegroundColor Green
    }
} else {
    Write-Host "[3/4] Пропущено (NoInstall или нет nCad.ini)" -ForegroundColor Yellow
    Write-Host "  Добавьте в $iniPath вручную:"
    Write-Host "  [$([char]0x5C)NetModules]"
    Write-Host "  CadEngine.Plugin=$PluginPath"
}

# ── 4. Запустить nanoCAD ──────────────────────────────────────
$proc = Get-Process -Name "nCad" -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "[4/4] nanoCAD уже запущен (PID $($proc.Id))" -ForegroundColor Green
} else {
    Write-Host "[4/4] Запускаю nanoCAD..." -ForegroundColor Yellow
    Start-Process -FilePath $ncadExe -WorkingDirectory $ncadDir
    Start-Sleep -Seconds 8
}

# ── 5. Ждать HTTP API ─────────────────────────────────────────
if (-not $NoWait) {
    $apiUrl = "http://localhost:5080/api/system/health"
    $maxWait = 30
    Write-Host "  Ожидаю HTTP API ($apiUrl)... до ${maxWait}с" -ForegroundColor Yellow

    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    while ($timer.Elapsed.TotalSeconds -lt $maxWait) {
        try {
            $response = Invoke-RestMethod -Uri $apiUrl -TimeoutSec 2 -ErrorAction Stop
            Write-Host "  ✅ HTTP API готов: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
            exit 0
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    Write-Error "  ⛔ HTTP API не ответил за ${maxWait}с. Проверьте, что плагин загружен."
    exit 1
}
