param(
    [switch]$AllowDownload,
    [switch]$ForceDownload
)

$ErrorActionPreference = 'Stop'
$script:MinimumEsVersion = [version]'1.1.0.37'
$script:ReleaseApi = 'https://api.github.com/repos/voidtools/ES/releases/latest'
$script:SkillRoot = Split-Path -Parent $PSScriptRoot
$script:EsPath = Join-Path $script:SkillRoot 'bin\es.exe'

function Get-NativeArchitecture {
    $value = $env:PROCESSOR_ARCHITEW6432
    if (-not $value) {
        $value = $env:PROCESSOR_ARCHITECTURE
    }

    switch ($value.ToUpperInvariant()) {
        'AMD64' { return 'x64' }
        'X86' { return 'x86' }
        'ARM64' { return 'arm64' }
        'ARM' { return 'arm' }
        default { throw "Unsupported Windows architecture: $value" }
    }
}

function Get-AssetPattern {
    param([Parameter(Mandatory)][string]$Architecture)

    switch ($Architecture) {
        'x64' { return '^ES-[0-9.]+\.x64\.zip$' }
        'x86' { return '^ES-[0-9.]+\.zip$' }
        'arm64' { return '^ES-[0-9.]+\.ARM64\.zip$' }
        'arm' { return '^ES-[0-9.]+\.ARM\.zip$' }
        default { throw "Unsupported ES architecture: $Architecture" }
    }
}

function Get-PeArchitecture {
    param([Parameter(Mandatory)][string]$Path)

    $bytes = [IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 64 -or $bytes[0] -ne 0x4d -or $bytes[1] -ne 0x5a) {
        throw "Not a valid PE executable: $Path"
    }

    $peOffset = [BitConverter]::ToInt32($bytes, 0x3c)
    if ($peOffset -lt 0 -or $peOffset + 6 -gt $bytes.Length) {
        throw "Invalid PE header: $Path"
    }
    if ([BitConverter]::ToUInt32($bytes, $peOffset) -ne 0x00004550) {
        throw "Invalid PE signature: $Path"
    }

    switch ([BitConverter]::ToUInt16($bytes, $peOffset + 4)) {
        0x014c { return 'x86' }
        0x8664 { return 'x64' }
        0x01c4 { return 'arm' }
        0xaa64 { return 'arm64' }
        default { throw "Unsupported PE machine type in $Path" }
    }
}

function Get-EsMetadata {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$ExpectedArchitecture
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "es.exe not found: $Path"
    }

    $architecture = Get-PeArchitecture -Path $Path
    if ($architecture -ne $ExpectedArchitecture) {
        throw "es.exe architecture $architecture does not match host $ExpectedArchitecture"
    }

    $versionText = (Get-Item -LiteralPath $Path).VersionInfo.ProductVersion
    try {
        $version = [version]$versionText
    }
    catch {
        throw "Unable to read es.exe version: $versionText"
    }
    if ($version -lt $script:MinimumEsVersion) {
        throw "es.exe $version is older than required $script:MinimumEsVersion"
    }

    return [pscustomobject]@{
        Version = $version.ToString()
        Architecture = $architecture
    }
}

function Install-LatestEs {
    param(
        [Parameter(Mandatory)][string]$TargetPath,
        [Parameter(Mandatory)][string]$ExpectedArchitecture
    )

    $tempDir = Join-Path ([IO.Path]::GetTempPath()) ('everything-skill-' + [guid]::NewGuid().ToString('N'))
    $backupPath = Join-Path $tempDir 'backup-es.exe'
    $hadOriginal = Test-Path -LiteralPath $TargetPath -PathType Leaf

    try {
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        $release = Invoke-RestMethod -Uri $script:ReleaseApi -Headers @{ 'User-Agent' = 'everything-skill' }
        $pattern = Get-AssetPattern -Architecture $ExpectedArchitecture
        $assets = @($release.assets | Where-Object { $_.name -match $pattern })
        if ($assets.Count -ne 1) {
            throw "Expected one compatible ES asset, found $($assets.Count)"
        }

        $zipPath = Join-Path $tempDir $assets[0].name
        Invoke-WebRequest -Uri $assets[0].browser_download_url -OutFile $zipPath -Headers @{ 'User-Agent' = 'everything-skill' }
        $extractDir = Join-Path $tempDir 'extract'
        Expand-Archive -LiteralPath $zipPath -DestinationPath $extractDir -Force
        $candidates = @(Get-ChildItem -LiteralPath $extractDir -Recurse -File -Filter 'es.exe')
        if ($candidates.Count -ne 1) {
            throw "Expected one es.exe in downloaded archive, found $($candidates.Count)"
        }

        $null = Get-EsMetadata -Path $candidates[0].FullName -ExpectedArchitecture $ExpectedArchitecture
        New-Item -ItemType Directory -Path (Split-Path -Parent $TargetPath) -Force | Out-Null
        if ($hadOriginal) {
            Copy-Item -LiteralPath $TargetPath -Destination $backupPath -Force
        }
        Copy-Item -LiteralPath $candidates[0].FullName -Destination $TargetPath -Force
        return Get-EsMetadata -Path $TargetPath -ExpectedArchitecture $ExpectedArchitecture
    }
    catch {
        if ($hadOriginal -and (Test-Path -LiteralPath $backupPath)) {
            Copy-Item -LiteralPath $backupPath -Destination $TargetPath -Force
        }
        elseif (-not $hadOriginal -and (Test-Path -LiteralPath $TargetPath)) {
            Remove-Item -LiteralPath $TargetPath -Force
        }
        throw
    }
    finally {
        if (Test-Path -LiteralPath $tempDir) {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Test-EverythingIpc {
    param([Parameter(Mandatory)][string]$Path)

    $output = @(& $Path '-argv' '-get-everything-version' 2>$null)
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Version = (($output -join "`n").Trim())
    }
}

function Write-HelperResult {
    param([Parameter(Mandatory)][hashtable]$Values)
    [Console]::Out.WriteLine(([pscustomobject]$Values | ConvertTo-Json -Compress))
}

function Invoke-EverythingToolsCheck {
    $hostArchitecture = $null
    $metadata = $null

    try {
        $hostArchitecture = Get-NativeArchitecture
        if (-not $ForceDownload) {
            try {
                $metadata = Get-EsMetadata -Path $script:EsPath -ExpectedArchitecture $hostArchitecture
            }
            catch {
                if (-not $AllowDownload) {
                    throw "$($_.Exception.Message) Re-run with -AllowDownload to repair from the official voidtools/ES release."
                }
            }
        }

        if ($ForceDownload -or -not $metadata) {
            $metadata = Install-LatestEs -TargetPath $script:EsPath -ExpectedArchitecture $hostArchitecture
        }

        $ipc = Test-EverythingIpc -Path $script:EsPath
        $reachable = $ipc.ExitCode -eq 0
        $message = if ($reachable) {
            'ES is ready and Everything IPC is reachable.'
        }
        else {
            "ES is ready, but Everything IPC is not reachable (ES exit code $($ipc.ExitCode))."
        }

        Write-HelperResult -Values @{
            es_path = $script:EsPath
            es_ready = $true
            es_version = $metadata.Version
            host_architecture = $hostArchitecture
            es_architecture = $metadata.Architecture
            ipc_reachable = $reachable
            everything_version = $(if ($reachable) { $ipc.Version } else { $null })
            message = $message
        }
        return [int]$ipc.ExitCode
    }
    catch {
        Write-HelperResult -Values @{
            es_path = $script:EsPath
            es_ready = $false
            es_version = $(if ($metadata) { $metadata.Version } else { $null })
            host_architecture = $hostArchitecture
            es_architecture = $(if ($metadata) { $metadata.Architecture } else { $null })
            ipc_reachable = $false
            everything_version = $null
            message = $_.Exception.Message
        }
        return 1
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    exit (Invoke-EverythingToolsCheck)
}
