'
' MediaMonkey Script Uninstaller
'
' NAME: LastFmImport
'
' AUTHOR: Psyker7 - (http://psykar.com)
'

Dim inip : inip = SDB.ApplicationPath&"Scripts\Scripts.ini"
Dim inif : Set inif = SDB.Tools.IniFileByPath(inip)
If Not (inif Is Nothing) Then
  inif.DeleteSection("LastFmImport")
  SDB.RefreshScriptItems
End If
