param(
    [string]$ImageName = "jarvis-app",
    [string]$ImageTag = "latest",
    [string]$Registry = "docker.io/your-username"
)

$FullImage = "$Registry/$ImageName`:$ImageTag"

Write-Host "Building image: $FullImage"
docker build -t $FullImage .
if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }

Write-Host "Pushing image: $FullImage"
docker push $FullImage
if ($LASTEXITCODE -ne 0) { throw "Docker push failed" }

Write-Host "Build and push completed"
