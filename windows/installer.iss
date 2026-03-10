; ──────────────────────────────────────────────────────────────────
; Spleet — Inno Setup Installer Script
;
; HOW TO USE:
;   1. Build with PyInstaller first:
;        pyinstaller Spleet.spec
;   2. Install Inno Setup  (https://jrsoftware.org/isinfo.php)
;   3. Open this .iss file in Inno Setup Compiler and click Build,
;      or run from the command line:
;        iscc installer.iss
;   4. The installer EXE is written to the "Output" folder.
; ──────────────────────────────────────────────────────────────────

#define MyAppName      "Spleet"
#define MyAppVersion   "0.2.0"
#define MyAppPublisher "Spleet"
#define MyAppURL       "https://github.com/spleet"
#define MyAppExeName   "Spleet.exe"

[Setup]
AppId={{B1F2D3E4-A5B6-C7D8-E9F0-1A2B3C4D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=Spleet_Setup_{#MyAppVersion}
SetupIconFile=..\shared\assets\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
; Minimum Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy everything PyInstaller produced in dist\Spleet\
Source: "dist\Spleet\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";         Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}";   Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
