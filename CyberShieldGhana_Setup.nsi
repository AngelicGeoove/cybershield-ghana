; CyberShield Ghana - NSIS Installer Script
; Compile with NSIS (https://nsis.sourceforge.io/)

!define APP_NAME "CyberShield Ghana"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "CyberShield Ghana Team"
!define APP_URL "https://csaghana.org"
!define APP_EXE "CyberShieldGhana.exe"
!define INSTALLER_NAME "CyberShieldGhana_Setup_v${APP_VERSION}.exe"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "${INSTALLER_NAME}"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
InstallDirRegKey HKLM "Software\${APP_NAME}" ""
RequestExecutionLevel admin
Icon "${APP_EXE}"
UninstallIcon "${APP_EXE}"

!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "${APP_EXE}"
!define MUI_UNICON "${APP_EXE}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  File "${APP_EXE}"
  
  WriteRegStr HKLM "Software\${APP_NAME}" "" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "URLInfoAbout" "${APP_URL}"
  
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR"
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR"
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${APP_NAME}.url" "InternetShortcut" "URL" "${APP_URL}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Website.lnk" "$INSTDIR\${APP_NAME}.url" "" "$INSTDIR"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR"
SectionEnd

Function .onInit
  ; Check for VC++ Redistributable
  ClearErrors
  RegOpenKey HKLM "SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" $0
  IfErrors 0 vcruntime_found
  MessageBox MB_ICONWARNING|MB_OK "Visual C++ Redistributable may be required.\n\nIf the application fails to start, please install it from:\nhttps://aka.ms/vs/17/release/vc_redist.x64.exe"
  vcruntime_found:
FunctionEnd

Function un.onUninstallConfirm
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to uninstall ${APP_NAME}?" IDYES +2
  Abort
FunctionEnd

Section "Uninstall"
  Delete "$INSTDIR\${APP_EXE}"
  Delete "$INSTDIR\cybershield.db"
  Delete "$INSTDIR\Uninstall.exe"
  
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Website.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.url"
  RMDir "$SMPROGRAMS\${APP_NAME}"
  
  Delete "$DESKTOP\${APP_NAME}.lnk"
  
  RMDir "$INSTDIR"
  
  DeleteRegKey HKLM "Software\${APP_NAME}"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd