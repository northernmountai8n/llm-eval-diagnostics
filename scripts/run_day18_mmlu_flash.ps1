param(
    [ValidateRange(1, 16)]
    [int]$Concurrency = 4
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo

& python .\src\report_day18_mmlu50.py
if ($LASTEXITCODE -ne 0) {
    throw 'The frozen MMLU sample or existing results did not pass validation.'
}

$keyWasAlreadySet = -not [string]::IsNullOrWhiteSpace($env:DEEPSEEK_API_KEY)
if (-not $keyWasAlreadySet) {
    $secret = Read-Host 'DeepSeek API Key (input hidden)' -AsSecureString
    $env:DEEPSEEK_API_KEY = [pscredential]::new('api', $secret).GetNetworkCredential().Password
    Remove-Variable secret
}

try {
    & python .\src\async_eval.py `
        --input '.\data\day18_mmlu_flash50.jsonl' `
        --model 'deepseek-flash' `
        --url 'https://api.deepseek.com/chat/completions' `
        --api-key-env 'DEEPSEEK_API_KEY' `
        --thinking disabled `
        --max-tokens 16 `
        --temperature 0 `
        --concurrency $Concurrency `
        --timeout 60 `
        --max-retries 2 `
        --backoff 0.5 `
        --out '.\runs\day18_deepseek_mmlu50.jsonl'
    $runExit = $LASTEXITCODE

    & python .\src\report_day18_mmlu50.py
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not generate the MMLU experiment report.'
    }
    if ($runExit -ne 0) {
        throw 'Some API requests failed. The report lists missing IDs; rerun this script to resume.'
    }
    Write-Host '[complete] DeepSeek Flash MMLU-50 results and report are ready.'
}
finally {
    if (-not $keyWasAlreadySet) {
        Remove-Item Env:DEEPSEEK_API_KEY -ErrorAction SilentlyContinue
    }
}
