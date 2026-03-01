# Create a simple favicon.ico file using base64
$faviconBase64 = 'AAABAAEAEBAQAAEABACoDAAATgAAACAgAAAEAACACgAAFgAAACAgAAABACCkDQAANwAAACAgAAABACCkAwAAjgAAACAgAAABACCkBQAAlQAA'
$faviconBytes = [Convert]::FromBase64String($faviconBase64)
[System.IO.File]::WriteAllBytes((Join-Path $PSScriptRoot 'favicon.ico'), $faviconBytes)
Write-Host "Favicon created successfully"
