This script sync's last.fm playcounts and last played dates into MM.
It will find total playcounts of every track in your last.fm history, check if it is higher than the value in the database (for all tracks of that title/artist - even if multiples) and updates it if so.
It will also update the last played times for all tracks with a newer last played on last.fm than in your MM database. 

Get it from: [b][url]http://psykar.com/scripts[/url][/b]
Direct link: [size=150][b][url]http://psykar.com/script-files/LastFmImportPython-3.1.mmip[/url][/b][/size]

It's been extensively tested now, but if you run into issues, sending me the log file would be a great help! %appdata%\MediaMonkey\Scripts\LastFmImport\Log.txt

[b]Notes:[/b][list]
[*]Does [u]*not* update MM's internal play histories[/u]. Feel free to use other scripts to fix this up (unlikely to be added as a feature here) http://www.mediamonkey.com/forum/viewtopic.php?f=2&t=31809[/list]

Source code is up at [url]https://github.com/Psykar/MM-LastFmImportPython[/url]
The tree needs cleaning up but figured I'd shove it up anyway given I'm now distributing an exe so you can look at the source code. It's compiled with pyinstaller.

Version history is here:
[url]https://github.com/Psykar/MM-LastFmImportPython/commits/master[/url]

===================================================
Old version details... I recommend the python version above though. As the vbscript version is VERY slow for large libraries and playcount histories.
====================

Well here is a vbscript implimentation of a last.fm sync of playcounts / last played date.

It will find total playcounts of every track in your last.fm history, check if it is higher than the value in the database (for all tracks of that title/artist - even if multiples) and updates it if so.
It will also update the last played times for all tracks with a newer last played on last.fm than in your MM database. 
===============
Useful if you lose your play counts, or you have a portable player (such as iPhone) which will scrobble tracks to last.fm OK, but won't update playcounts in MM (very annoying bug that)
It is *not* worth running more than once a week, as it uses your weekly track charts for totals, and these are only updated weekly.
===============

A log file is created automatically containing all tracks which were updated in a tab delimited file in your %appdata%/mediamonkey/lastfmimport directory.

A first run over a database can a few hours, but interrupting the script is safe, and running it later will pickup where it left off.
To speed it up somewhat, turn *OFF* autorate accurate, otherwise every track updated will need to be written too as the script processes.


======

My first real scripting attempt for MM, thanks to:
Teknojnky - author of last.fmnode - for code for various functions, hacked a LOT.
Trixmoto - for mmip packaging of normal scripts, had me stumped for a while there :D

======================================================
Download:
[size=150][b][url]http://psykar.com/scripts/[/url][/b][/size]
======================================================

I [b]VERY STRONGLY[/b] recommend a database backup before you try this.

 =====
' Changes: 2.4
' - Fixed bad typo
'
' Changes: 2.3
' - Fixed log file directory creation
'
' Changes: 2.2
' - Fixed log file save path error
'
' Changes: 2.1
' - Caches XML files locally for faster re-runs
' - Added retry option for HTTP timeouts
'
' Changes: 2.0
' - Added support for updating last played times - these will be up to a week out though
'
' Changes: 1.12
' - Fix: More graceful xml checking, should catch ALL Invalid characters
'
' Changes: 1.11
' - Fix: More infalid xml characters checked
' - More graceful exits when errors occur
'
' Changes: 1.10
' - Fix: More invalid xml characters checked
'
' Changes: 1.9
' - Fix: Last.FM usernames not parsing correctly if containing special chars
'
' Changes: 1.8
' - Fix: Invalid ASCII characters stripped (hopefully - let me know if you find more!)
'  Thanks to SinDenial and AndréVonDrei for testing!
' - More graceful error messages (for some, let me know if you get anything cryptic)
' - Check for invalid characters when writing update file - some seem to cause errors
'	when the actual update went fine - needs improvment
'
' Changes: 1.7
' - Fix: Invalid apostrophes stripped, sadly this will make things less accurate
'	but will reduce error messages for the moment
'
' Changes: 1.6
' - Fix: No longer case sensitive for track names
' - Fix: Error messages on timeouts are more helpful
'
' Changes: 1.5
' Better logging - by default a log file will be created listing tracks updated
'	this file is LastFmImport.vbs.Updated.txt located in the scripts folder and is 
'	tab delimited.
' Better status bar messages as well I would like to think
'
' Changes: 1.4
' - HUGE speedup - no more .updateall() rather only update the track that needs it with
'   updateDB()
'
' Changes: 1.3
' - Database lookup optimizations (I hope!)
' - Added a few more stats to the process
' - Cleaned logging so enabling should only print essential stats about updated files
'
' Changes: 1.2
' - Status Bars!
' - Code Tidy Up
'
' Changes: 1.1
' - Abstracted username
' - Pretty error messages
'
'ToDo:
'* Better UI
'  o Checkbox for updating last played times
'* Retry HTTP a few times before timing out
'* Move all files modified into %appdata%
'* Possibly use  sdb.ScriptsPath instead ?

===Beta changelog===

' Changes: 3.0
' - Added support for last.fm's recent track history
'
