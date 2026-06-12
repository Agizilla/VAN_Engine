# ScreenClipOCR

Windows-native screen capture utility with a global hotkey and clipboard-first workflow.

## Current MVP

- Global hotkey: `Ctrl + Shift + S`
- Drag-to-select capture across the virtual desktop
- Captured image is copied to the clipboard
- Optional save-to-disk support
- Dedicated `Extract Text` button for the most recent capture
- Capture history list with revisitable thumbnails
- `Save All` export for captured images and extracted text
- Minimize-to-tray behavior with tray reopen/exit
- Designer-backed WinForms form for visual editing in Visual Studio

## OCR

The app uses the local Tesseract installation already present on this machine:

- `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`

## Run

```powershell
dotnet run --project .\ScreenClipOCR.csproj
```

## Publish

Visual Studio:

- Open the project properties
- Go to `Publish`
- Use the included `FolderProfile`

CLI:

```powershell
dotnet publish .\ScreenClipOCR.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true
```

Default publish output:

- `bin\Publish\win-x64\`

## Next Good Step

- Persist capture history between launches
- Allow choosing the OCR executable path in settings
- Add an installer or portable release packaging
