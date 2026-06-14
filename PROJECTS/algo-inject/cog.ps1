param(
    [string]$type = "thinking",
    [string]$message = "",
    [string]$tool = "",
    [string]$description = "",
    [string]$status = "",
    [string]$summary = "",
    [string]$tags = "",
    [string]$options = ""
)
$body = @{ type = $type; message = $message } | ConvertTo-Json -Compress
if ($tool) { $body = @{ type = $type; message = $message; tool = $tool; description = $description; status = $status; summary = $summary } | ConvertTo-Json -Compress }
try {
    Invoke-RestMethod -Uri "http://localhost:8001/api/cognition/event" -Method Post -Body $body -ContentType "application/json" -UseBasicParsing | Out-Null
} catch { }
