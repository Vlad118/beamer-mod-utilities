@echo off
set source=D:\Games\BeamNG.drive\BeamNG.driveMods\0.32\mods
set target=D:\Games\BeamNG.drive\KissMP Server\mods

for %%f in (%source%\*.zip) do (
    set "skip="
    for %%e in (%exclude%) do if %%~nxf==%%e set "skip=true"
    if not defined skip mklink "%target%\%%~nxf" "%%f"
)