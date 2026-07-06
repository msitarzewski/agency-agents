# Windows Installer Build Scripts

## Quick Start

Build complete installer (auto-read version from VERSION file):
```powershell
.\build\build_installer.ps1
```

Skip portable package build (use existing):
```powershell
.\build\build_installer.ps1 -SkipPortablePackage
```

Specify custom version:
```powershell
.\build\build_installer.ps1 -Version "1.0.1"
```

## Version Management

- **Default**: Automatically reads version from `C:\TradingAgentsCN\VERSION` file
- **Override**: Use `-Version` parameter to specify custom version
- **Output**: `TradingAgentsCNSetup-{VERSION}.exe`

## Architecture

Two-layer approach:
1. **Portable package** (green version) - tested standalone package built by `scripts/deployment/build_portable_package.ps1`
2. **NSIS installer wrapper** - adds installation UI, port configuration, shortcuts, registry integration

## Features

- ✅ Port configuration UI (Backend, MongoDB, Redis, Nginx)
- ✅ Automatic port conflict detection
- ✅ UTF-8 encoding support for configuration files
- ✅ Desktop and Start Menu shortcuts
- ✅ Uninstaller with registry integration

## Output

- **Installer**: `scripts\windows-installer\nsis\TradingAgentsCNSetup-{VERSION}.exe`
- **Size**: ~320 MB (compressed from ~1.3GB portable package)
- **Compression**: LZMA (94.5% compression ratio)

## Build Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-Version` | Auto-read from VERSION file | Version string for installer |
| `-BackendPort` | 8000 | Default backend port |
| `-MongoPort` | 27017 | Default MongoDB port |
| `-RedisPort` | 6379 | Default Redis port |
| `-NginxPort` | 80 | Default Nginx port |
| `-SkipPortablePackage` | false | Skip building portable package |
| `-NsisPath` | Auto-detect | Custom NSIS installation path |

## Requirements

- **NSIS**: Nullsoft Scriptable Install System (auto-detected from standard paths)
- **PowerShell**: 5.1 or later
- **Portable Package**: Pre-built package in `release/packages/` directory
