param(
    [string]$WorkspaceRoot = "C:\Users\SsuJo_\.openclaw\workspace",
    [switch]$ForceDownload
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$skillRoot = Join-Path $WorkspaceRoot 'skills\everything'
$binDir = Join-Path $skillRoot 'bin'
$esPath = Join-Path $binDir 'es.exe'
$tempDir = Join-Path $env:TEMP ('everything-skill-' + [guid]::NewGuid().ToString('N'))
$repoApi = 'https://api.github.com/repos/voidtools/Everything/releases/latest'

function Test-EsExecutable {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    try {
        $p = Start-Process -FilePath $Path -ArgumentList '-version' -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$env:TEMP\es-version-out.txt" -RedirectStandardError "$env:TEMP\es-version-err.txt"
        return $p.ExitCode -eq 0
    } catch {
        return $false
    }
}

function Get-AssetPattern {
    if ([Environment]::Is64BitOperatingSystem) {
        return 'es-.*x64.*\.zip$'
    }
    return 'es-.*\.zip$'
}

function Download-EsFromGithub {
    param([string]$TargetPath)

    New-Item -ItemType Directory -Force -Path $binDir | Out-Null
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

    $release = Invoke-RestMethod -Uri $repoApi -Headers @{ 'User-Agent' = 'OpenClaw-Everything-Skill' }
    $pattern = Get-AssetPattern
    $asset = $release.assets | Where-Object { $_.name -match $pattern } | Select-Object -First 1
    if (-not $asset) {
        throw "No compatible es.exe asset found in latest release."
    }

    $zipPath = Join-Path $tempDir $asset.name
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -Headers @{ 'User-Agent' = 'OpenClaw-Everything-Skill' }

    $extractDir = Join-Path $tempDir 'extract'
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $downloadedEs = Get-ChildItem -Path $extractDir -Recurse -File -Filter 'es.exe' | Select-Object -First 1
    if (-not $downloadedEs) {
        throw 'Downloaded archive does not contain es.exe'
    }

    Copy-Item -Path $downloadedEs.FullName -Destination $TargetPath -Force
}

function Convert-ToEscapedUnicode {
    param([string]$Text)
    if ($null -eq $Text) { return $null }
    $builder = New-Object System.Text.StringBuilder
    foreach ($ch in $Text.ToCharArray()) {
        $code = [int][char]$ch
        if ($code -ge 32 -and $code -le 126 -and $ch -ne '\\') {
            [void]$builder.Append($ch)
        } else {
            [void]$builder.Append(('\u{0:x4}' -f $code))
        }
    }
    return $builder.ToString()
}

function Find-EverythingExe {
    param([string]$EsExePath)

    $paths = @()
    if (Test-Path $EsExePath) {
        try {
            $paths = & $EsExePath 'Everything.exe' 2>$null
        } catch {
            $paths = @()
        }
    }

    $preferred = $paths | Where-Object {
        $_ -match '\\Everything\.exe$' -and ($_ -match '^([A-Za-z]:\\)')
    } | Select-Object -Unique

    if ($preferred) {
        return $preferred[0]
    }

    $fallbacks = @(
        'C:\Program Files\Everything\Everything.exe',
        'C:\Program Files (x86)\Everything\Everything.exe',
        (Join-Path $env:LOCALAPPDATA 'Everything\Everything.exe')
    )

    foreach ($candidate in $fallbacks) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

try {
    $esReady = $false
    if (-not $ForceDownload) {
        $esReady = Test-EsExecutable -Path $esPath
    }

    if (-not $esReady) {
        Download-EsFromGithub -TargetPath $esPath
        $esReady = Test-EsExecutable -Path $esPath
        if (-not $esReady) {
            throw 'es.exe still not runnable after download'
        }
    }

    $everythingExe = Find-EverythingExe -EsExePath $esPath

    [pscustomobject]@{
        esPath = $esPath
        esReady = $esReady
        everythingExe = $everythingExe
        esPathEscaped = (Convert-ToEscapedUnicode -Text $esPath)
        everythingExeEscaped = (Convert-ToEscapedUnicode -Text $everythingExe)
    } | ConvertTo-Json -Compress
}
finally {
    if (Test-Path $tempDir) {
        Remove-Item -Recurse -Force $tempDir -ErrorAction SilentlyContinue
    }
}
