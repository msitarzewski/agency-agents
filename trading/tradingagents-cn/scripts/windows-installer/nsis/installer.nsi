!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"

!define PRODUCT_NAME "TradingAgentsCN"
!ifndef PRODUCT_VERSION
  !define PRODUCT_VERSION "1.0.0"
!endif
!ifndef BACKEND_PORT
  !define BACKEND_PORT "8000"
!endif
!ifndef MONGO_PORT
  !define MONGO_PORT "27017"
!endif
!ifndef REDIS_PORT
  !define REDIS_PORT "6379"
!endif
!ifndef NGINX_PORT
  !define NGINX_PORT "80"
!endif
!ifndef PACKAGE_ZIP
  !define PACKAGE_ZIP "C:\\TradingAgentsCN\\release\\packages\\TradingAgentsCN-Portable-latest.zip"
!endif
!ifndef OUTPUT_DIR
  !define OUTPUT_DIR "C:\\TradingAgentsCN\\release\\packages"
!endif

Name "${PRODUCT_NAME}"
OutFile "${OUTPUT_DIR}\TradingAgentsCNSetup-${PRODUCT_VERSION}.exe"
InstallDir "C:\TradingAgentsCN"
RequestExecutionLevel admin
SetDatablockOptimize on
SetCompressor lzma

Var BackendPort
Var MongoPort
Var RedisPort
Var NginxPort
Var hBackendEdit
Var hMongoEdit
Var hRedisEdit
Var hNginxEdit
Var hDetectBtn
Var LaunchCheckbox
Var LaunchCheckboxState

Function .onInit
 StrCpy $BackendPort "${BACKEND_PORT}"
 StrCpy $MongoPort "${MONGO_PORT}"
 StrCpy $RedisPort "${REDIS_PORT}"
 StrCpy $NginxPort "${NGINX_PORT}"
 StrCpy $LaunchCheckboxState ${BST_CHECKED}
FunctionEnd

Function PortsPage
 nsDialogs::Create 1018
 Pop $0
 ${If} $0 == error
   Abort
${EndIf}

${NSD_CreateLabel} 0 0 100% 12u "Configure Ports for Installation"

${NSD_CreateLabel} 0 18u 45% 12u "Backend Port (default ${BACKEND_PORT})"
 ${NSD_CreateText} 50% 16u 35% 12u "$BackendPort"
 Pop $hBackendEdit

${NSD_CreateLabel} 0 36u 45% 12u "MongoDB Port (default ${MONGO_PORT})"
 ${NSD_CreateText} 50% 34u 35% 12u "$MongoPort"
 Pop $hMongoEdit

${NSD_CreateLabel} 0 54u 45% 12u "Redis Port (default ${REDIS_PORT})"
 ${NSD_CreateText} 50% 52u 35% 12u "$RedisPort"
 Pop $hRedisEdit

${NSD_CreateLabel} 0 72u 45% 12u "Nginx Port (default ${NGINX_PORT})"
 ${NSD_CreateText} 50% 70u 35% 12u "$NginxPort"
 Pop $hNginxEdit

 nsDialogs::Show
FunctionEnd


Function PortsPageLeave
 ${NSD_GetText} $hBackendEdit $BackendPort
 ${NSD_GetText} $hMongoEdit $MongoPort
 ${NSD_GetText} $hRedisEdit $RedisPort
 ${NSD_GetText} $hNginxEdit $NginxPort

 ; Validate port number format
 ${If} $BackendPort == ""
  MessageBox MB_ICONSTOP "Backend port cannot be empty"
  Abort
 ${EndIf}
 ${If} $MongoPort == ""
  MessageBox MB_ICONSTOP "MongoDB port cannot be empty"
  Abort
 ${EndIf}
 ${If} $RedisPort == ""
  MessageBox MB_ICONSTOP "Redis port cannot be empty"
  Abort
 ${EndIf}
 ${If} $NginxPort == ""
  MessageBox MB_ICONSTOP "Nginx port cannot be empty"
  Abort
 ${EndIf}

 ; Validate port range
 ${If} $BackendPort < 1024
  MessageBox MB_ICONSTOP "Backend port must be >= 1024"
  Abort
 ${EndIf}
 ${If} $MongoPort < 1024
  MessageBox MB_ICONSTOP "MongoDB port must be >= 1024"
  Abort
 ${EndIf}
 ${If} $RedisPort < 1024
  MessageBox MB_ICONSTOP "Redis port must be >= 1024"
  Abort
 ${EndIf}
 ${If} $BackendPort > 65535
  MessageBox MB_ICONSTOP "Backend port must be <= 65535"
  Abort
 ${EndIf}
 ${If} $MongoPort > 65535
  MessageBox MB_ICONSTOP "MongoDB port must be <= 65535"
  Abort
 ${EndIf}
 ${If} $RedisPort > 65535
  MessageBox MB_ICONSTOP "Redis port must be <= 65535"
  Abort
 ${EndIf}
 ${If} $NginxPort > 65535
  MessageBox MB_ICONSTOP "Nginx port must be <= 65535"
  Abort
 ${EndIf}

 ; Validate no duplicate ports
 ${If} $BackendPort == $MongoPort
  MessageBox MB_ICONSTOP "Backend port duplicates MongoDB port"
  Abort
 ${EndIf}
 ${If} $BackendPort == $RedisPort
  MessageBox MB_ICONSTOP "Backend port duplicates Redis port"
  Abort
 ${EndIf}
 ${If} $BackendPort == $NginxPort
  MessageBox MB_ICONSTOP "Backend port duplicates Nginx port"
  Abort
 ${EndIf}
 ${If} $MongoPort == $RedisPort
  MessageBox MB_ICONSTOP "MongoDB port duplicates Redis port"
  Abort
 ${EndIf}
 ${If} $MongoPort == $NginxPort
  MessageBox MB_ICONSTOP "MongoDB port duplicates Nginx port"
  Abort
 ${EndIf}
 ${If} $RedisPort == $NginxPort
  MessageBox MB_ICONSTOP "Redis port duplicates Nginx port"
  Abort
 ${EndIf}

 
 FunctionEnd

!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Launch TradingAgentsCN"
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchApplication"

Page custom PortsPage PortsPageLeave
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Function LaunchApplication
 ; Launch with admin privileges
 ExecShell "runas" "powershell" '-ExecutionPolicy Bypass -NoExit -File "$INSTDIR\start_all.ps1"'
FunctionEnd

Section
SetOutPath "$INSTDIR"

; Extract the portable package ZIP file
DetailPrint "Extracting portable package..."
File "${PACKAGE_ZIP}"

; Extract ZIP using PowerShell
DetailPrint "Unpacking files..."
nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "Expand-Archive -Path \"$INSTDIR\TradingAgentsCN-Portable-latest.zip\" -DestinationPath \"$INSTDIR\" -Force"'
Pop $0

${If} $0 != 0
  MessageBox MB_ICONSTOP "Failed to extract package. Error code: $0"
  Abort
${EndIf}

; Remove the ZIP file after extraction
Delete "$INSTDIR\TradingAgentsCN-Portable-latest.zip"

; Update configuration files with user-selected ports
DetailPrint "Updating configuration..."

; Update .env file (use PORT for backend, not BACKEND_PORT)
nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "$$envFile = \"$INSTDIR\.env\"; if (Test-Path $$envFile) { $$content = Get-Content $$envFile -Raw -Encoding UTF8; $$content = $$content -replace \"PORT=.*\", \"PORT=$BackendPort\"; $$content = $$content -replace \"API_PORT=.*\", \"API_PORT=$BackendPort\"; $$content = $$content -replace \"MONGODB_PORT=.*\", \"MONGODB_PORT=$MongoPort\"; $$content = $$content -replace \"REDIS_PORT=.*\", \"REDIS_PORT=$RedisPort\"; $$content = $$content -replace \"NGINX_PORT=.*\", \"NGINX_PORT=$NginxPort\"; $$utf8 = New-Object System.Text.UTF8Encoding $$false; [System.IO.File]::WriteAllText($$envFile, $$content, $$utf8) }"'

; Update Redis configuration
DetailPrint "Updating Redis configuration..."
nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "$$redisConf = \"$INSTDIR\runtime\redis.conf\"; if (Test-Path $$redisConf) { $$content = Get-Content $$redisConf -Raw -Encoding UTF8; $$content = $$content -replace \"^port\\s+\\d+\", \"port $RedisPort\"; $$utf8 = New-Object System.Text.UTF8Encoding $$false; [System.IO.File]::WriteAllText($$redisConf, $$content, $$utf8) }"'

; Update MongoDB configuration
DetailPrint "Updating MongoDB configuration..."
nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "$$mongoConf = \"$INSTDIR\runtime\mongodb.conf\"; if (Test-Path $$mongoConf) { $$content = Get-Content $$mongoConf -Raw -Encoding UTF8; $$content = $$content -replace \"port:\\s*\\d+\", \"port: $MongoPort\"; $$utf8 = New-Object System.Text.UTF8Encoding $$false; [System.IO.File]::WriteAllText($$mongoConf, $$content, $$utf8) }"'

; Update Nginx configuration
DetailPrint "Updating Nginx configuration..."
nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "$$nginxConf = \"$INSTDIR\runtime\nginx.conf\"; if (Test-Path $$nginxConf) { $$content = Get-Content $$nginxConf -Raw -Encoding UTF8; $$content = $$content -replace \"listen\\s+\\d+;\", \"listen       $NginxPort;\"; $$utf8 = New-Object System.Text.UTF8Encoding $$false; [System.IO.File]::WriteAllText($$nginxConf, $$content, $$utf8) }"'

; Create shortcuts with admin privileges
DetailPrint "Creating shortcuts..."
CreateDirectory "$SMPROGRAMS\TradingAgentsCN"

; Create shortcuts using PowerShell to set RunAsAdministrator flag
; Fix: Change directory first, then execute script (simulate manual startup)
nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(\"$SMPROGRAMS\TradingAgentsCN\Start TradingAgentsCN.lnk\"); $s.TargetPath = \"powershell.exe\"; $s.Arguments = \"-ExecutionPolicy Bypass -NoExit -Command `\"Set-Location -Path ''$INSTDIR''; & ''$INSTDIR\start_all.ps1''`\"\"; $s.WorkingDirectory = \"$INSTDIR\"; $s.Save(); $bytes = [System.IO.File]::ReadAllBytes($s.FullName); $bytes[0x15] = $bytes[0x15] -bor 0x20; [System.IO.File]::WriteAllBytes($s.FullName, $bytes)"'

nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(\"$SMPROGRAMS\TradingAgentsCN\Stop TradingAgentsCN.lnk\"); $s.TargetPath = \"powershell.exe\"; $s.Arguments = \"-ExecutionPolicy Bypass -NoExit -Command `\"Set-Location -Path ''$INSTDIR''; & ''$INSTDIR\stop_all.ps1''`\"\"; $s.WorkingDirectory = \"$INSTDIR\"; $s.Save(); $bytes = [System.IO.File]::ReadAllBytes($s.FullName); $bytes[0x15] = $bytes[0x15] -bor 0x20; [System.IO.File]::WriteAllBytes($s.FullName, $bytes)"'

nsExec::ExecToLog 'powershell -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut(\"$DESKTOP\TradingAgentsCN.lnk\"); $s.TargetPath = \"powershell.exe\"; $s.Arguments = \"-ExecutionPolicy Bypass -NoExit -Command `\"Set-Location -Path ''$INSTDIR''; & ''$INSTDIR\start_all.ps1''`\"\"; $s.WorkingDirectory = \"$INSTDIR\"; $s.Save(); $bytes = [System.IO.File]::ReadAllBytes($s.FullName); $bytes[0x15] = $bytes[0x15] -bor 0x20; [System.IO.File]::WriteAllBytes($s.FullName, $bytes)"'

; Write uninstaller
WriteUninstaller "$INSTDIR\Uninstall.exe"

; Registry entries for Control Panel uninstall
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradingAgentsCN" "DisplayName" "TradingAgentsCN"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradingAgentsCN" "UninstallString" "$INSTDIR\Uninstall.exe"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradingAgentsCN" "DisplayVersion" "${PRODUCT_VERSION}"
WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradingAgentsCN" "InstallLocation" "$INSTDIR"

DetailPrint "Installation completed!"
SectionEnd

Section "Uninstall"
 Delete "$SMPROGRAMS\TradingAgentsCN\Start TradingAgentsCN.lnk"
 Delete "$SMPROGRAMS\TradingAgentsCN\Stop TradingAgentsCN.lnk"
 RMDir  "$SMPROGRAMS\TradingAgentsCN"
 Delete "$DESKTOP\TradingAgentsCN.lnk"
 Delete "$INSTDIR\Uninstall.exe"
 DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TradingAgentsCN"
 RMDir /r "$INSTDIR"
SectionEnd