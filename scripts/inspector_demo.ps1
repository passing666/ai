## Inspector demo PowerShell script
# Usage: run from repo root in PowerShell
# .\.venv\Scripts\Activate.ps1
# python -m pip install -e .
# .\scripts\inspector_demo.ps1

Write-Host "Running end-to-end demo (mock Deepseek)..."
python .\examples\end_to_end_demo.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "Demo succeeded. See out/demo_result.json"
} else {
    Write-Host "Demo failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
