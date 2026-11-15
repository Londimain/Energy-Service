; Скрипт установщика для программы "Ежемесячные отчёты (Energy Report)"
; Создан для сборки, выполненной через PyInstaller (файл EnergyReport.exe в папке dist)

#define MyAppName "Energy Report"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ОАО ""Компания МогНат"""
#define MyAppExeName "EnergyReport.exe"
#define MyAppURL "https://github.com/Londimain/Energy-Service"

[Setup]
AppId={{B2C3D4E5-F6A7-8901-2345-6789ABCDEF01}
AppName={#MyAppName}
VersionInfoVersion={#MyAppVersion}.0
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
CloseApplications=force
RestartApplications=yes

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

OutputDir=installer_output
OutputBaseFilename=EnergyReport_Setup_v{#MyAppVersion}
SetupIconFile=ico\appEnergy.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

PrivilegesRequired=admin

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; --- ВЫДАЕМ ПРАВА НА ЗАПИСЬ В ПАПКУ ПРОГРАММЫ ---
; Это нужно, чтобы локальная база Energy.db могла создаваться и обновляться
[Dirs]
Name: "{app}"; Permissions: users-modify

[Icons]
; Ярлык в меню "Пуск"
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Ярлык на рабочем столе
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent