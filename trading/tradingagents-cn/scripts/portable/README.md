# TradingAgents-CN Portable Scripts

This directory contains scripts for the TradingAgents-CN portable (green) version.

## Files

### Stop Services Scripts

- **stop_all.ps1** - PowerShell script to stop all services
- **stop_all_services.bat** - Batch file wrapper for easy execution

## Deployment

These scripts should be copied to the portable release directory during the build process:

```powershell
# Copy stop scripts
Copy-Item scripts/portable/stop_all.ps1 release/TradingAgentsCN-portable/stop_all.ps1
Copy-Item scripts/portable/stop_all_services.bat release/TradingAgentsCN-portable/停止所有服务.bat

# Copy documentation
Copy-Item docs/deployment/stop-services-guide.md release/TradingAgentsCN-portable/停止服务说明.md
```

## Usage in Portable Version

After deployment, users can stop all services by:

1. **Double-click** `停止所有服务.bat`
2. Or run in PowerShell: `.\stop_all.ps1`

## Features

### stop_all.ps1

- **Graceful Stop**: Uses PID file to stop services gracefully
- **Force Stop**: Can force stop all related processes
- **Cleanup**: Removes temporary files and PID files
- **Verification**: Checks if services are stopped successfully

### Parameters

- `-Force` - Force stop all related processes
- `-OnlyPid` - Only use PID file to stop
- `-Quiet` - Quiet mode, reduce output

### Examples

```powershell
# Normal stop (recommended)
.\stop_all.ps1

# Force stop all related processes
.\stop_all.ps1 -Force

# Only use PID file
.\stop_all.ps1 -OnlyPid

# Quiet mode
.\stop_all.ps1 -Quiet
```

## Service Stop Order

1. **Nginx** - Stop frontend service first
2. **Backend (FastAPI)** - Stop backend API service
3. **Redis** - Stop cache service
4. **MongoDB** - Stop database service

This order ensures:
- No new requests enter the system
- Ongoing requests have time to complete
- Data is saved correctly

## Processes Stopped

The script stops the following processes:

- `nginx.exe` - Nginx web server
- `python.exe` / `pythonw.exe` - Python backend processes
- `redis-server.exe` - Redis service
- `mongod.exe` - MongoDB service

## Cleanup

The script cleans up:

- `runtime\pids.json` - PID file
- `logs\nginx.pid` - Nginx PID file
- `temp\*` - Temporary directories

## Documentation

See [docs/deployment/stop-services-guide.md](../../docs/deployment/stop-services-guide.md) for detailed usage guide.

## Related Scripts

- [scripts/installer/start_all.ps1](../installer/start_all.ps1) - Start all services
- [start_portable.ps1](../../release/TradingAgentsCN-portable/start_portable.ps1) - Portable version startup script

## Notes

- These scripts are designed for Windows portable version only
- Requires PowerShell 5.0 or later
- May require administrator privileges to stop some processes
- Always backup data before stopping services

---

**Last Updated**: 2025-11-05

