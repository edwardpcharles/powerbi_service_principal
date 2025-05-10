# Variables
$clientId = ""
$tenantId = ""
$clientSecret = ""
$groupId = ""
$datasetId = ""
$refreshUrl = "https://api.powerbi.com/v1.0/myorg/groups/$groupId/datasets/$datasetId/refreshes"

# Get an authentication token
$tokenUrl = "https://login.microsoftonline.com/$tenantId/oauth2/token"
$body = @{
    grant_type    = "client_credentials"
    client_id     = $clientId
    client_secret = $clientSecret
    resource      = "https://analysis.windows.net/powerbi/api"
}

$response = Invoke-RestMethod -Method Post -Uri $tokenUrl -ContentType "application/x-www-form-urlencoded" -Body $body
$accessToken = $response.access_token

# Set headers
$headers = @{
    Authorization = "Bearer $accessToken"
}

# Trigger refresh request
$refreshRequestTime = Get-Date
Invoke-RestMethod -Method Post -Uri $refreshUrl -Headers $headers
Write-Output "✅ Dataset refresh request sent successfully at: $refreshRequestTime"

# Monitor refresh status
$refreshLogged = $false
do {
    Start-Sleep -Seconds 1

    # Retrieve refresh history
    $statusResponse = Invoke-RestMethod -Method Get -Uri $refreshUrl -Headers $headers
    $latestRefresh = $statusResponse.value | Sort-Object -Property startTime -Descending | Select-Object -First 1

    # Confirm refresh started (only logs once)
    if (-not $refreshLogged -and $latestRefresh.startTime -gt $refreshRequestTime) {
        Write-Output "✅ Refresh started successfully at: $($latestRefresh.startTime)"
        $refreshLogged = $true
    }

    # Print meaningful status updates
    if ($latestRefresh.status -ne "Unknown") {
        Write-Output "Current Refresh Status: $($latestRefresh.status)"
    }

    # Exit loop if refresh is completed or failed
    if ($latestRefresh.status -eq "Completed") {
        Write-Output "✅ Dataset refresh completed successfully!"
        break
    } elseif ($latestRefresh.status -eq "Failed") {
        Write-Output "❌ Dataset refresh failed!"
        break
    }

    Write-Output "⏳ Refresh in progress... Checking again in 1 second."

} while ($true)
