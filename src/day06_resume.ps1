# Dot-source this file after activating the lmeval Conda environment and
# changing to the repository root:
#   . .\src\day06_resume.ps1
# This file sets up the Day 6 matrix and defines Invoke-Day6Run. It does not
# start any evaluations by itself.

$modelFile = '.\results\day06_models.json'
if (-not (Test-Path -LiteralPath $modelFile)) {
    throw "Missing $modelFile. Restore the pinned model revisions before running."
}

$parsedModels = Get-Content -LiteralPath $modelFile -Raw -Encoding UTF8 | ConvertFrom-Json
$models = @($parsedModels)
if ($models.Count -ne 3 -or @($models | Where-Object { $_.Sha -notmatch '^[0-9a-f]{40}$' }).Count -ne 0) {
    throw "Expected three models with pinned 40-character revisions in $modelFile."
}

$tasks = @(
    [pscustomobject]@{ Name='arc_easy';       Shot=0; Limit=200 }
    [pscustomobject]@{ Name='hellaswag';      Shot=0; Limit=200 }
    [pscustomobject]@{ Name='mmlu';           Shot=5; Limit=10  }
    [pscustomobject]@{ Name='gsm8k';          Shot=5; Limit=200 }
    [pscustomobject]@{ Name='truthfulqa_mc2'; Shot=0; Limit=200 }
)

$lm = (Get-Command lm_eval -ErrorAction Stop).Source

function Invoke-Day6Run {
    param($Model, $Task)

    $out = ".\runs\day06_$($Model.Tag)_$($Task.Name)_s$($Task.Shot)_n$($Task.Limit)"
    if (Test-Path -LiteralPath $out) {
        throw "Output directory already exists: $out. Inspect it before retrying."
    }

    $modelArgs = "pretrained=$($Model.Id),revision=$($Model.Sha),dtype=bfloat16"
    $runArgs = @(
        'run',
        '--model', 'hf',
        '--model_args', $modelArgs,
        '--tasks', $Task.Name,
        '--num_fewshot', "$($Task.Shot)",
        '--limit', "$($Task.Limit)",
        '--batch_size', '1',
        '--device', 'cuda:0',
        '--seed', '0,1234,1234,1234',
        '--output_path', $out,
        '--log_samples'
    )
    $cmdForLog = "lm_eval run --model hf --model_args '$modelArgs' --tasks $($Task.Name) --num_fewshot $($Task.Shot) --limit $($Task.Limit) --batch_size 1 --device cuda:0 --seed '0,1234,1234,1234' --output_path '$out' --log_samples"

    Write-Host "Starting: $($Model.Id) / $($Task.Name)"
    & $lm @runArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Evaluation failed: $($Model.Id) / $($Task.Name). This run was not logged."
    }

    $files = @(Get-ChildItem -LiteralPath $out -Recurse -File -Filter 'results_*.json')
    if ($files.Count -ne 1) {
        throw "Expected one results JSON in $out; found $($files.Count)."
    }

    python src/run_logger.py add `
        --model $Model.Id `
        --revision $Model.Sha `
        --task $Task.Name `
        --num-fewshot $Task.Shot `
        --limit $Task.Limit `
        --batch-size 1 `
        --dtype bfloat16 `
        --result-file $files[0].FullName `
        --cmd $cmdForLog `
        --notes 'Day 6 main result table; limited-sample trial'
    if ($LASTEXITCODE -ne 0) {
        throw "Evaluation succeeded but logging failed. Results: $out"
    }

    Write-Host "Completed and logged: $($Model.Id) / $($Task.Name)"
}

Write-Host 'Day 6 setup loaded. Existing runs were not started or changed.'
