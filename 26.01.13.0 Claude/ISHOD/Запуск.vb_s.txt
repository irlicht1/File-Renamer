Set WshShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

On Error Resume Next
WshShell.Run "pythonw """ & strPath & "\renamer_gui_v13_unified.pyw""", 0, False
If Err.Number <> 0 Then
    WshShell.Run "python """ & strPath & "\renamer_gui_v13_unified.py""", 0, False
End If
