; HAKON 安装包配置
; 使用 Inno Setup 编译此脚本生成安装包
; 下载 Inno Setup: https://jrsoftware.org/isdl.php
; 编译方法：用 Inno Setup Compiler 打开此文件，点击 Build

[Setup]
AppName=HAKON
AppVersion=1.0.0
AppPublisher=HAKON
AppPublisherURL=https://github.com/kahotsan-design/hakon-storyboard
AppSupportURL=https://github.com/kahotsan-design/hakon-storyboard
DefaultDirName={autopf}\HAKON
DefaultGroupName=HAKON
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=HAKON_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\HAKON.exe
UninstallDisplayName=HAKON
SetupIconFile=static\hakon_logo.ico
LicenseFile=
InfoBeforeFile=

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 把 dist\HAKON\ 下的所有文件打包进去
Source: "dist\HAKON\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\HAKON"; Filename: "{app}\HAKON.exe"; IconFilename: "{app}\HAKON.exe"
Name: "{group}\Uninstall HAKON"; Filename: "{uninstallexe}"
Name: "{autodesktop}\HAKON"; Filename: "{app}\HAKON.exe"; IconFilename: "{app}\HAKON.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\HAKON.exe"; Description: "{cm:LaunchProgram,HAKON}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
