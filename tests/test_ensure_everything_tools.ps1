$ErrorActionPreference = 'Stop'

function Assert-Equal {
    param($Actual, $Expected, [string]$Message)
    if ($Actual -ne $Expected) {
        throw "$Message Expected '$Expected', got '$Actual'."
    }
}

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw $Message
    }
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$helperPath = Join-Path $repositoryRoot 'scripts\ensure-everything-tools.ps1'
. $helperPath

Assert-Equal $script:SkillRoot $repositoryRoot 'Skill root must derive from $PSScriptRoot.'
Assert-Equal $script:EsPath (Join-Path $repositoryRoot 'bin\es.exe') 'ES path is not self-relative.'

$oldArchitecture = $env:PROCESSOR_ARCHITECTURE
$oldWowArchitecture = $env:PROCESSOR_ARCHITEW6432
try {
    $cases = @(
        @{ Native = 'AMD64'; Expected = 'x64' },
        @{ Native = 'x86'; Expected = 'x86' },
        @{ Native = 'ARM'; Expected = 'arm' },
        @{ Native = 'ARM64'; Expected = 'arm64' }
    )
    foreach ($case in $cases) {
        $env:PROCESSOR_ARCHITEW6432 = $null
        $env:PROCESSOR_ARCHITECTURE = $case.Native
        Assert-Equal (Get-NativeArchitecture) $case.Expected "Native mapping failed for $($case.Native)."
    }

    $env:PROCESSOR_ARCHITECTURE = 'x86'
    $env:PROCESSOR_ARCHITEW6432 = 'AMD64'
    Assert-Equal (Get-NativeArchitecture) 'x64' 'WoW64 native architecture detection failed.'
}
finally {
    $env:PROCESSOR_ARCHITECTURE = $oldArchitecture
    $env:PROCESSOR_ARCHITEW6432 = $oldWowArchitecture
}

Assert-Equal (Get-AssetPattern -Architecture 'x86') '^ES-[0-9.]+\.zip$' 'x86 asset pattern failed.'
Assert-Equal (Get-AssetPattern -Architecture 'x64') '^ES-[0-9.]+\.x64\.zip$' 'x64 asset pattern failed.'
Assert-Equal (Get-AssetPattern -Architecture 'arm') '^ES-[0-9.]+\.ARM\.zip$' 'ARM asset pattern failed.'
Assert-Equal (Get-AssetPattern -Architecture 'arm64') '^ES-[0-9.]+\.ARM64\.zip$' 'ARM64 asset pattern failed.'

$bundledEs = Join-Path $repositoryRoot 'bin\es.exe'
Assert-Equal (Get-PeArchitecture -Path $bundledEs) 'x64' 'Bundled PE architecture check failed.'
$metadata = Get-EsMetadata -Path $bundledEs -ExpectedArchitecture 'x64'
Assert-Equal $metadata.Version '1.1.0.37' 'Bundled ES version check failed.'
Assert-Equal $metadata.Architecture 'x64' 'Bundled ES metadata architecture failed.'

$helperText = Get-Content -LiteralPath $helperPath -Raw
Assert-True (-not $helperText.Contains('Program Files')) 'Helper must not infer IPC availability from an install path.'
Assert-True (-not $helperText.Contains('Find-Everything')) 'Helper must not search for Everything.exe.'
Assert-True ($helperText.Contains('backup-es.exe')) 'Helper must retain a rollback copy during replacement.'

$ipc = Test-EverythingIpc -Path $bundledEs
Assert-True ($ipc.ExitCode -is [int]) 'IPC check must return the native ES exit code.'

Write-Output 'PowerShell checks passed.'
exit 0
