echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent\ntbin\win64\tell.exe" Jaswita 53157 CLEANUP_EXITING
timeout /t 1
"C:\PROGRA~1\ANSYSI~1\ANSYSS~1\v261\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="Jaswita" (%KILL_CMD% 4452) 
if /i "%LOCALHOST%"=="Jaswita" (%KILL_CMD% 17752) 
if /i "%LOCALHOST%"=="Jaswita" (%KILL_CMD% 1004) 
if /i "%LOCALHOST%"=="Jaswita" (%KILL_CMD% 11468)
del "C:\Users\jaswi\OneDrive\Desktop\ALL\SEM_7\project\jammalamadugu\new_obj\objective2_design_optimization\ansys\cleanup-fluent-Jaswita-1004.bat"
