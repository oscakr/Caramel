<#
.SYNOPSIS
    Respaldo automático diario del repositorio Caramel hacia GitHub (origin/main).
.DESCRIPTION
    Verifica cambios en código, base de datos (caramel.db) y carpeta uploads/,
    ejecuta checkpoint seguro en SQLite, omite archivos > 95 MB (límite GitHub),
    crea commit únicamente si hubo cambios reales y hace push a GitHub.
    Registra cada ejecución en auto_backup.log (ignorado por .gitignore).
#>

[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "never"
$RepoPath = "C:\Users\Admin\Downloads\Caramel\Caramel-main"
$LogFile  = Join-Path $RepoPath "auto_backup.log"
$Branch   = "main"
$Remote   = "origin"
$MaxFileBytes = 95MB

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    Write-Output $line
}

# Recortar log si supera 500 líneas
if (Test-Path $LogFile) {
    $lines = Get-Content -Path $LogFile -ErrorAction SilentlyContinue
    if ($lines -and $lines.Count -gt 500) {
        $lines | Select-Object -Last 300 | Set-Content -Path $LogFile -Encoding UTF8
    }
}

Write-Log "=== Inicio de respaldo automático Caramel (DryRun=$DryRun) ==="

if (-not (Test-Path $RepoPath)) {
    Write-Log "No se encontró el repositorio en $RepoPath" "ERROR"
    exit 1
}

Set-Location $RepoPath

# 1. Checkpoint seguro de SQLite si caramel.db existe (sin romper si no hay python)
$DbPath = Join-Path $RepoPath "caramel.db"
if (Test-Path $DbPath) {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) {
        try {
            & python -c "import sqlite3; c=sqlite3.connect(r'$DbPath', timeout=5); c.execute('PRAGMA wal_checkpoint(TRUNCATE)'); c.close()" 2>$null
            Write-Log "Checkpoint SQLite completado en caramel.db."
        } catch {
            Write-Log "No se pudo ejecutar checkpoint SQLite (posible bloqueo temporal): $($_.Exception.Message)" "WARN"
        }
    }
}

# 2. Revisar si existen archivos nuevos/modificados > 95 MB (límite duro de GitHub = 100 MB)
$oversized = Get-ChildItem -Path $RepoPath -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Length -gt $MaxFileBytes -and
        $_.FullName -notmatch "\\(\.git|venv|\.venv|__pycache__)\\"
    }

if ($oversized) {
    foreach ($f in $oversized) {
        $mb = [math]::Round($f.Length / 1MB, 2)
        Write-Log "ADVERTENCIA: Archivo supera 95 MB ($mb MB) y puede ser rechazado por GitHub: $($f.FullName)" "WARN"
    }
}

# 3. Verificar cambios en el árbol de trabajo
$statusBefore = & git status --porcelain 2>&1
if (-not $statusBefore) {
    # Aún si no hay cambios locales, revisar si quedaron commits pendientes de subir (ej. noche sin internet)
    $ahead = (& git rev-list --count "$Remote/$Branch..HEAD" 2>$null)
    if ($ahead -and [int]$ahead -gt 0) {
        Write-Log "Sin cambios nuevos, pero existen $ahead commit(s) locales pendientes de subir."
        if (-not $DryRun) {
            $pushPending = & git push $Remote $Branch 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Push diferido completado correctamente ($ahead commits subidos)."
                exit 0
            } else {
                Write-Log "Fallo en push diferido: $pushPending" "ERROR"
                exit 1
            }
        }
    } else {
        Write-Log "Sin cambios detectados en el repositorio. Nada que respaldar."
    }
    exit 0
}

# 4. Preparar archivos (respetando .gitignore: .env, venv, *.log, *token* quedan excluidos)
if ($DryRun) {
    Write-Log "[DryRun] Cambios detectados que se respaldarían:"
    $statusBefore | ForEach-Object { Write-Log "  $_" }
    exit 0
}

& git add -A 2>&1 | Out-Null

# Excluir archivos > 95 MB si alguno fue agregado al staging
if ($oversized) {
    foreach ($f in $oversized) {
        $rel = $f.FullName.Substring($RepoPath.Length + 1).Replace('\', '/')
        & git reset HEAD -- "$rel" 2>$null | Out-Null
        Write-Log "Descartado del commit por superar 95 MB: $rel" "WARN"
    }
}

# Confirmar que realmente hay algo en el índice (staging)
& git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Log "No quedaron cambios en staging tras filtrar exclusiones."
    exit 0
}

$stagedFiles = & git diff --cached --name-only
$fileCount = ($stagedFiles | Measure-Object).Count
$dbChanged = ($stagedFiles -contains "caramel.db")
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"

if ($dbChanged) {
    $commitMsg = "chore(auto-backup): respaldo diario $timestamp (caramel.db + $fileCount archivo(s))"
} else {
    $commitMsg = "chore(auto-backup): respaldo diario $timestamp ($fileCount archivo(s))"
}

# 5. Crear commit
$commitOut = & git commit -m "$commitMsg" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Log "Error al crear commit: $commitOut" "ERROR"
    exit 1
}
Write-Log "Commit creado: $commitMsg"

# 6. Subir a GitHub
$pushOut = & git push $Remote $Branch 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Log "Push exitoso hacia $Remote/$Branch."
    exit 0
} else {
    Write-Log "Primer intento de push falló: $pushOut. Intentando sincronización rebase..." "WARN"
    $pullOut = & git pull --rebase --autostash $Remote $Branch 2>&1
    if ($LASTEXITCODE -eq 0) {
        $pushRetry = & git push $Remote $Branch 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Push exitoso tras rebase hacia $Remote/$Branch."
            exit 0
        } else {
            Write-Log "Error en push tras rebase: $pushRetry" "ERROR"
            exit 1
        }
    } else {
        Write-Log "No se pudo sincronizar (posible falta de conexión a Internet). El commit quedó guardado localmente para el próximo respaldo. Detalle: $pullOut" "ERROR"
        exit 1
    }
}
