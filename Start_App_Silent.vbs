Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Run Start_App.bat completely in the background (0 = hide window)
WshShell.Run "cmd /c cd /d """ & strDir & """ && Start_App.bat", 0, False
