$owner = 'jakelindsay87'
$repo = 'hoistscraper'
$branch = 'main'
$baseApiUrl = "https://api.github.com/repos/$owner/$repo/actions/runs"
$queryParams = "?branch=$branch&per_page=1"
$fullApiUrl = $baseApiUrl + $queryParams

# GitHub Token Handling
$GhToken = $env:GITHUB_TOKEN
if (-not $GhToken) {
    Write-Host "GITHUB_TOKEN environment variable not set."
    $UserInputToken = Read-Host -Prompt "If your repository is private or you require authentication, please enter a GitHub Personal Access Token (PAT) with 'repo' scope (or press Enter to skip)"
    if (-not [string]::IsNullOrWhiteSpace($UserInputToken)) {
        $GhToken = $UserInputToken
    }
}

$headers = @{
    'Accept'             = 'application/vnd.github.v3+json'
    'X-GitHub-Api-Version' = '2022-11-28'
}

if (-not [string]::IsNullOrWhiteSpace($GhToken)) {
    Write-Host "Using provided GitHub token for API calls."
    $headers['Authorization'] = "Bearer $GhToken"
} else {
    Write-Host "Proceeding without a GitHub token. This will likely fail if the repository is private or requires authentication for Actions details."
}

$noRunsCount = 0
$maxNoRunsRetries = 12 # Try for about 3 minutes if no runs are found initially (12 * 15s)
$apiErrorRetryCount = 0
$maxApiErrorRetries = 5

Write-Host 'Starting GitHub Actions CI poller script...'

while ($true) {
    Write-Host "$(Get-Date -Format 'HH:mm:ss'): Checking CI status for branch '$branch' on repo '$owner/$repo'..."
    $latestRun = $null
    $jobsCollection = $null

    try {
        $runsCollection = Invoke-RestMethod -Uri $fullApiUrl -Headers $headers -TimeoutSec 30 -ErrorAction Stop
        $apiErrorRetryCount = 0 # Reset API error count on successful call
    } catch {
        $apiErrorRetryCount++
        $ErrorRecord = $_ # Store the full error record
        $ActualMessage = $ErrorRecord.Exception.Message
        Write-Host ("Error fetching workflow runs: " + $ActualMessage) # Use string concatenation
        if ($apiErrorRetryCount -gt $maxApiErrorRetries) {
            Write-Host 'Max API error retries reached. Exiting.'
            exit 1 # General error exit code
        }
        Write-Host ("Will retry API call in 15 seconds (attempt " + $apiErrorRetryCount + "/" + $maxApiErrorRetries + ").")
        Start-Sleep -Seconds 15
        continue
    }

    if ($runsCollection.workflow_runs.Count -eq 0) {
        $noRunsCount++
        if ($noRunsCount -gt $maxNoRunsRetries) {
            Write-Host ("No workflow runs found for branch '" + $branch + "' after " + ($maxNoRunsRetries * 15) + " seconds. Please check GitHub Actions setup, branch name, or if a workflow was triggered.")
            exit 1 # General error exit code
        }
        Write-Host ("No workflow runs found yet for branch '" + $branch + "'. Attempt " + $noRunsCount + "/" + $maxNoRunsRetries + ". Checking again in 15 seconds.")
        Start-Sleep -Seconds 15
        continue 
    }

    $latestRun = $runsCollection.workflow_runs[0]
    $noRunsCount = 0 # Reset noRunsCount if a run is found

    $status = $latestRun.status
    $conclusion = $latestRun.conclusion
    $runId = $latestRun.id
    $runHtmlUrl = $latestRun.html_url

    Write-Host ("Latest run ID: " + $runId + " (URL: " + $runHtmlUrl + "), Status: " + $status + ", Conclusion: " + $conclusion)

    if ($status -eq 'completed') {
        if ($conclusion -eq 'success') {
            Write-Host 'CI GREEN'
            exit 0 # Success
        } else {
            Write-Host ("CI run " + $runId + " completed with status: '" + $conclusion + "'.")
            Write-Host ("Fetching jobs for run " + $runId + "...")
            $jobsApiUrl = $latestRun.jobs_url
            try {
                $jobsCollection = Invoke-RestMethod -Uri $jobsApiUrl -Headers $headers -TimeoutSec 30 -ErrorAction Stop
            } catch {
                $JobErrorRecord = $_ # Store the full error record
                $ActualJobMessage = $JobErrorRecord.Exception.Message
                Write-Host ("Error fetching jobs for run " + $runId + ": " + $ActualJobMessage) # Use string concatenation
                Write-Host ("Exiting due to error fetching job details. Overall status was '" + $conclusion + "'. Run URL: " + $runHtmlUrl)
                exit 1 # General error exit code to indicate CI failure
            }

            $failingJobs = $jobsCollection.jobs | Where-Object { $_.conclusion -ne 'success' -and $_.conclusion -ne 'skipped' -and $_.conclusion -ne $null }
            if ($failingJobs -and ($failingJobs | Measure-Object).Count -gt 0) {
                foreach ($job in $failingJobs) {
                    Write-Host ("Failing job: " + $job.name + ", Conclusion: " + $job.conclusion + ", Log URL: " + $job.html_url)
                }
            } else {
                Write-Host ("CI status was '" + $conclusion + "' but couldn't pinpoint specific failing job(s) from API, or all jobs surprisingly succeeded/skipped despite failed run. Check run URL: " + $runHtmlUrl)
            }
            exit 1 # General error exit code to indicate CI failure
        }
    } else { # Status is queued, in_progress, waiting, requested, etc.
        Write-Host ("CI run " + $runId + " is currently: '" + $status + "'. Checking again in 15 seconds.")
        Start-Sleep -Seconds 15
    }
} 