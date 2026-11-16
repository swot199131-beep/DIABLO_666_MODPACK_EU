#define MyAppName "DIABLO_666 MODPACK EU"
#define MyAppVersion "0.6.1"
#define MyAppPublisher "DIABLO Community"
#define MyAppExeName "DIABLO_666_MODPACK_EU.exe"

[Setup]
AppId={{C6E0A8F3-9B14-4D65-9F9A-666D1AB05252}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={localappdata}\Programs\DIABLO_666_MODPACK_EU
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=DIABLO_666_MODPACK_EU_Setup_v{#MyAppVersion}
SetupIconFile=..\assets\diablo_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes
RestartApplications=no
Uninstallable=yes
UsePreviousAppDir=yes
VersionInfoVersion=0.6.1.0
VersionInfoCompany=DIABLO Community
VersionInfoDescription=DIABLO_666 MODPACK EU Setup
VersionInfoProductName=DIABLO_666 MODPACK EU
VersionInfoProductVersion=0.6.1

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:"; Flags: unchecked

[Files]
Source: "..\dist\app\DIABLO_666_MODPACK_EU.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DIABLO_666 MODPACK EU"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\DIABLO_666 MODPACK EU"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить DIABLO_666 MODPACK EU"; Flags: postinstall nowait skipifsilent

; User data and backups in LocalAppData are intentionally preserved.
