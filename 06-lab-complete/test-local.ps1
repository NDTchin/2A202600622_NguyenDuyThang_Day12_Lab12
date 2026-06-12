param(
    [string]$BaseUrl = "http://localhost:8080",
    [string]$ApiKey = "local-dev-key"
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "`n==> $Message"
}

Write-Step "Health check"
Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get

Write-Step "Readiness check"
Invoke-RestMethod -Uri "$BaseUrl/ready" -Method Get

Write-Step "Authentication should reject missing API key"
$body = @{ user_id = "auth-test"; question = "Hello" } | ConvertTo-Json -Compress
try {
    Invoke-RestMethod -Uri "$BaseUrl/ask" -Method Post -ContentType "application/json" -Body $body | Out-Null
    throw "Expected 401, got success"
} catch {
    if (-not $_.Exception.Response -or [int]$_.Exception.Response.StatusCode -ne 401) {
        throw
    }
    Write-Host "401 Unauthorized"
}

Write-Step "Authenticated request should work"
$body = @{ user_id = "local-test"; question = "What is deployment?" } | ConvertTo-Json -Compress
Invoke-RestMethod `
    -Uri "$BaseUrl/ask" `
    -Method Post `
    -Headers @{ "X-API-Key" = $ApiKey } `
    -ContentType "application/json" `
    -Body $body

Write-Step "Rate limit should allow 10 and block later requests"
$ok = 0
$limited = 0
$other = 0
$userId = "rate-test-$(Get-Date -Format yyyyMMddHHmmss)"

1..12 | ForEach-Object {
    $body = @{ user_id = $userId; question = "rate $_" } | ConvertTo-Json -Compress
    try {
        Invoke-RestMethod `
            -Uri "$BaseUrl/ask" `
            -Method Post `
            -Headers @{ "X-API-Key" = $ApiKey } `
            -ContentType "application/json" `
            -Body $body | Out-Null
        $script:ok++
    } catch {
        if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -eq 429) {
            $script:limited++
        } else {
            $script:other++
        }
    }
}

Write-Host "ok=$ok limited=$limited other=$other"
if ($ok -ne 10 -or $limited -lt 1 -or $other -ne 0) {
    throw "Rate limit test failed"
}

Write-Step "Local tests passed"
