Option Explicit

' Launch the native PySide6 application without a console window.
Dim shell, fso, root, pythonw, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)

pythonw = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python313\pythonw.exe"
If Not fso.FileExists(pythonw) Then
    pythonw = "pythonw.exe"
End If

command = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & root & "\run_desktop.py" & Chr(34)
shell.CurrentDirectory = root
shell.Run command, 0, False
