<#
.SYNOPSIS
    Starts all microservices and the API Gateway in separate PowerShell windows.
#>

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " Starting FastAPI + gRPC Microservices Mesh      " -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Compile Protos
Write-Host "`n[1/5] Compiling protobuf definitions..." -ForegroundColor Yellow
& "$ROOT\venv\Scripts\python.exe" "$ROOT\scripts\generate_proto.py"

# 2. Start User Service (:8000 HTTP / :50050 gRPC)
Write-Host "`n[2/5] Starting User Service on port 8000 (gRPC 50050)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT'; & '.\venv\Scripts\python.exe' -m user_service.main"

Start-Sleep -Seconds 2

# 3. Start Product Service (:8001 HTTP / :50051 gRPC)
Write-Host "`n[3/5] Starting Product Service on port 8001 (gRPC 50051)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT'; & '.\venv\Scripts\python.exe' -m product_service.main"

Start-Sleep -Seconds 2

# 4. Start Order Service (:8002 HTTP)
Write-Host "`n[4/5] Starting Order Service on port 8002..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT'; & '.\venv\Scripts\python.exe' -m order_service.main"

Start-Sleep -Seconds 2

# 5. Start API Gateway (:8080 HTTP)
Write-Host "`n[5/5] Starting API Gateway on port 8080..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT'; & '.\venv\Scripts\python.exe' -m api_gateway.main"

Write-Host "`n=================================================" -ForegroundColor Cyan
Write-Host " All services started!                           " -ForegroundColor Cyan
Write-Host " - API Gateway Docs:     http://localhost:8080/docs" -ForegroundColor Yellow
Write-Host " - User Service Docs:    http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host " - Product Service Docs: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host " - Order Service Docs:   http://localhost:8002/docs" -ForegroundColor Yellow
Write-Host "=================================================" -ForegroundColor Cyan
