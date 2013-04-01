# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'C:\\Users\\louisdl\\git\\LastFmImportPython\\LastFmImportPython\\lastFMImportPython\\src\\LastFmImport\\LastFmImport.py'],
             pathex=['C:\\Users\\louisdl\\git\\LastFmImportPython\\LastFmImportPython\\lastFMImportPython\\src\\LastFmImport'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'LastFmImport.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=False )
app = BUNDLE(exe,
             name=os.path.join('dist', 'LastFmImport.exe.app'))
