Write-Host "=== Sistema ===" -ForegroundColor Cyan
$os = Get-CimInstance Win32_OperatingSystem
$cpu = Get-CimInstance Win32_Processor
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
Write-Host "CPU: $($cpu.Name)"
Write-Host "RAM total: $([math]::Round($os.TotalVisibleMemorySize/1MB,1)) GB"
Write-Host "RAM livre: $([math]::Round($os.FreePhysicalMemory/1MB,1)) GB"
Write-Host "Disco livre: $([math]::Round($disk.FreeSpace/1GB,1)) GB"
python --version
