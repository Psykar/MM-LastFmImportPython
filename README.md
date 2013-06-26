Mediamonkey LastFMImporter
============================
At this stage I no longer have the time/interest in maintaining this - as I don't use Mediamonkey myself any longer.
If you need help in getting this running with python directly, or any help with dev'ing it further, feel free to open an issue.


This script sync's last.fm playcounts and last played dates into MM.
It will find total playcounts of every track in your last.fm history, check if it is higher than the value in the database (for all tracks of that title/artist - even if multiples) and updates it if so.
It will also update the last played times for all tracks with a newer last played on last.fm than in your MM database. 

Get it from: *http://psykar.com/scripts*

Direct link: *http://psykar.com/script-files/LastFmImportPython-3.1.mmip*

It's been extensively tested now, but if you run into issues, sending me the log file would be a great help! %appdata%\MediaMonkey\Scripts\LastFmImport\Log.txt

### Notes:
* Does *not* update MM's internal play histories. Feel free to use other scripts to fix this up (unlikely to be added as a feature here) http://www.mediamonkey.com/forum/viewtopic.php?f=2&t=31809

Source code is up at https://github.com/Psykar/MM-LastFmImportPython
The tree needs cleaning up but figured I'd shove it up anyway given I'm now distributing an exe so you can look at the source code. It's compiled with pyinstaller.

Version history is here:
https://github.com/Psykar/MM-LastFmImportPython/commits/master
