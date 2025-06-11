# CI Fix Loop for Windows PowerShell
# This script helps you quickly fix CI failures

Write-Host "🔧 CI Fix Loop - Push, Check, Fix, Repeat" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Yellow

# Check if gh CLI is installed
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "GitHub CLI (gh) is not installed" -ForegroundColor Red
    Write-Host "Install it using: winget install --id GitHub.cli"
    exit 1
}

# Function to push and check CI
function Push-AndCheck {
    Write-Host "`nPushing to GitHub..." -ForegroundColor Yellow
    git push origin HEAD
    
    Write-Host "`nWaiting for CI to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Get the latest workflow run
    Write-Host "`nChecking CI status..." -ForegroundColor Yellow
    gh run list --limit 1
    
    # Get run ID
    $runId = (gh run list --limit 1 --json databaseId | ConvertFrom-Json)[0].databaseId
    
    if ($runId) {
        Write-Host "`nWatching run #$runId..." -ForegroundColor Yellow
        gh run watch $runId
        
        # Get the status
        $status = (gh run view $runId --json conclusion | ConvertFrom-Json).conclusion
        
        if ($status -eq "success") {
            Write-Host "`n✅ All CI tests passed!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "`n❌ CI tests failed" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "Could not find workflow run" -ForegroundColor Red
        return $false
    }
}

# Function to view logs
function View-Logs {
    Write-Host "`nFetching failure logs..." -ForegroundColor Yellow
    
    # Get the latest run
    $runId = (gh run list --limit 1 --json databaseId | ConvertFrom-Json)[0].databaseId
    
    if ($runId) {
        # View failed jobs
        Write-Host "`nFailed jobs:" -ForegroundColor Yellow
        gh run view $runId --log-failed
        
        Write-Host "`nOptions:" -ForegroundColor Yellow
        Write-Host "1. View full logs in browser"
        Write-Host "2. Download all logs"
        Write-Host "3. Continue to fix"
        $choice = Read-Host "Choose (1-3)"
        
        switch ($choice) {
            1 { gh run view $runId --web }
            2 { 
                gh run download $runId
                Write-Host "Logs downloaded to current directory"
            }
        }
    }
}

# Function to get specific error details
function Get-ErrorDetails {
    $runId = (gh run list --limit 1 --json databaseId | ConvertFrom-Json)[0].databaseId
    
    if ($runId) {
        Write-Host "`nAnalyzing errors..." -ForegroundColor Yellow
        
        # Get job details
        $jobs = gh run view $runId --json jobs | ConvertFrom-Json | Select-Object -ExpandProperty jobs
        
        foreach ($job in $jobs) {
            if ($job.conclusion -eq "failure") {
                Write-Host "`nFailed Job: $($job.name)" -ForegroundColor Red
                
                # Try to get specific step that failed
                $steps = $job.steps | Where-Object { $_.conclusion -eq "failure" }
                foreach ($step in $steps) {
                    Write-Host "  Failed Step: $($step.name)" -ForegroundColor Red
                }
            }
        }
    }
}

# Main loop
while ($true) {
    Write-Host "`nWhat would you like to do?" -ForegroundColor Yellow
    Write-Host "1. Push and check CI"
    Write-Host "2. View last failure logs"
    Write-Host "3. Get error details"
    Write-Host "4. Amend last commit and push"
    Write-Host "5. Exit"
    $action = Read-Host "Choose (1-5)"
    
    switch ($action) {
        1 {
            if (Push-AndCheck) {
                Write-Host "Success! All tests are green." -ForegroundColor Green
                exit 0
            }
        }
        2 { View-Logs }
        3 { Get-ErrorDetails }
        4 {
            Write-Host "`nAmending commit and force pushing..." -ForegroundColor Yellow
            git add -A
            git commit --amend --no-edit
            git push --force-with-lease origin HEAD
        }
        5 {
            Write-Host "Exiting..."
            exit 0
        }
    }
}