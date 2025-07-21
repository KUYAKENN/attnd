@echo off
:: Go to your Angular dist build folder (replace with your real path)
cd /d "C:\Users\YourName\Desktop\angular-app\dist\your-app-name"

:: Start http-server with Single Page App (SPA) support
start "" cmd /c "http-server -p 4200 --spa"

:: Wait a few seconds for the server to initialize
timeout /t 5 >nul

:: Launch Chrome in kiosk mode
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk http://localhost:4200
exit
