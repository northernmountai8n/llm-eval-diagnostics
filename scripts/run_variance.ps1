param(
    [ValidateSet('arc_easy', 'hellaswag', 'custom_mmlu_all_random5')]
    [string]$Task = 'arc_easy',
    [int[]]$Limits = @(200, 500, 1000),
    [int[]]$Seeds = @(1, 2, 3, 4, 5),
    [switch]$PlanOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path -Parent $PSScriptRoot
$modelId = 'Qwen/Qwen2.5-1.5B'
$revision = '8faed761d45a263340a0528343f099c05c9a4323'
$modelArgs = "pretrained=$modelId,revision=$revision,dtype=bfloat16"
$modelDirName = 'Qwen__Qwen2.5-1.5B'
$lm = (Get-Command lm_eval -ErrorAction Stop).Source

function Test-CompletedRun {
    param(
        [string]$OutputDir,
        [int]$Limit,
        [int]$Seed,
        [string]$Task
    )

    $modelDir = Join-Path $OutputDir $modelDirName
    if (-not (Test-Path -LiteralPath $modelDir -PathType Container)) {
        return $false
    }

    $results = @(Get-ChildItem -LiteralPath $modelDir -File -Filter 'results_*.json')
    if ($results.Count -eq 0) {
        return $false
    }

    foreach ($result in $results) {
        $stamp = $result.BaseName.Substring('results_'.Length)
        $samplePath = Join-Path $modelDir "samples_${Task}_$stamp.jsonl"
        if (-not (Test-Path -LiteralPath $samplePath -PathType Leaf)) {
            continue
        }
        try {
            $data = Get-Content -LiteralPath $result.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            $valid = $data.config.model -eq 'hf' -and
                $data.config.model_args.pretrained -eq $modelId -and
                $data.config.model_args.revision -eq $revision -and
                $data.config.model_args.dtype -eq 'bfloat16' -and
                $data.config.device -eq 'cuda:0' -and
                [int]$data.config.limit -eq $Limit -and
                [int]$data.config.random_seed -eq 0 -and
                [int]$data.config.numpy_seed -eq 1234 -and
                [int]$data.config.torch_seed -eq 1234 -and
                [int]$data.config.fewshot_seed -eq $Seed -and
                [int]$data.'n-shot'.$Task -eq 5 -and
                [int]$data.'n-samples'.$Task.effective -eq $Limit -and
                [int]$data.results.$Task.sample_len -eq $Limit
            if ($valid) {
                $rowCount = (Get-Content -LiteralPath $samplePath | Measure-Object -Line).Lines
                if ($rowCount -eq $Limit) {
                    return $true
                }
            }
        }
        catch {
            continue
        }
    }
    return $false
}

Push-Location $repoRoot
try {
    foreach ($limit in $Limits) {
        $maxLimit = switch ($Task) {
            'arc_easy' { 2376 }
            'hellaswag' { 10042 }
            'custom_mmlu_all_random5' { 14042 }
        }
        if ($limit -lt 1 -or $limit -gt $maxLimit) {
            throw "$Task limit must be between 1 and ${maxLimit}: $limit"
        }
        foreach ($seed in $Seeds) {
            $out = Join-Path $repoRoot "runs\variance\$Task\seed${seed}_limit${limit}"
            if (Test-CompletedRun -OutputDir $out -Limit $limit -Seed $seed -Task $Task) {
                Write-Host "[skip] $Task limit=$limit seed=$seed (verified complete)"
                continue
            }
            if (Test-Path -LiteralPath $out) {
                throw "Incomplete or mismatched output: $out. Inspect this directory before retrying."
            }
            if ($PlanOnly) {
                Write-Host "[plan] $Task limit=$limit seed=$seed"
                continue
            }

            $runArgs = @(
                'run', '--model', 'hf', '--model_args', $modelArgs,
                '--tasks', $Task, '--num_fewshot', '5',
                '--limit', "$limit", '--batch_size', '1',
                '--device', 'cuda:0', '--seed', "0,1234,1234,$seed",
                '--output_path', $out, '--log_samples'
            )
            if ($Task -eq 'custom_mmlu_all_random5') {
                $runArgs += @('--include_path', (Join-Path $repoRoot 'configs\tasks'))
            }
            Write-Host "[run] $Task limit=$limit seed=$seed"
            & $lm @runArgs
            if ($LASTEXITCODE -ne 0) {
                throw "lm_eval failed for limit=$limit seed=$seed. Inspect $out"
            }
            if (-not (Test-CompletedRun -OutputDir $out -Limit $limit -Seed $seed -Task $Task)) {
                throw "lm_eval returned success but output verification failed: $out"
            }
            Write-Host "[done] $Task limit=$limit seed=$seed"
        }
    }
    if ($PlanOnly) {
        Write-Host "[complete] $Task plan checked; no evaluations started."
    }
    else {
        Write-Host "[complete] All requested $Task runs are verified."
    }
}
finally {
    Pop-Location
}
