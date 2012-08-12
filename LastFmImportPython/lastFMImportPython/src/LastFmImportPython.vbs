' Thanks to trixmoto for this function
Sub Install()
	Dim inip : inip = SDB.ApplicationPath&"Scripts\Scripts.ini"
	Dim inif : Set inif = SDB.Tools.IniFileByPath(inip)
	If Not (inif Is Nothing) Then
		inif.StringValue("LastFmImport","Filename") = "LastFmImportPython.vbs"
		inif.StringValue("LastFmImport","Procname") = "LastFmImportPython"
		inif.StringValue("LastFmImport","Order") = "7"
		inif.StringValue("LastFmImport","DisplayName") = "Last FM Play Importer Python"
		inif.StringValue("LastFmImport","Description") = "Update plays from Last.fm"
		inif.StringValue("LastFmImport","Language") = "VBScript"
		inif.StringValue("LastFmImport","ScriptType") = "0"
		SDB.RefreshScriptItems
	End If
	
End Sub

Sub LastFmImportPython()
	Dim oShell : Set oShell = CreateObject( "WScript.Shell" )
	Dim file : file = """"&SDB.ScriptsPath&"LastFmImportPython\LastFmImportPython.exe"""
	oShell.Run(file)
End Sub