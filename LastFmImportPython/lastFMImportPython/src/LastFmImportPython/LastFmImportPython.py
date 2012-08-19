import win32com.client
import lastfm
#import cProfile
import sqlite3
import datetime
import shelve
import os
import codecs
from multiprocessing.pool import ThreadPool, TimeoutError
import time
import logging
import sys

# define IUNICODE collation function
def iUnicodeCollate(s1, s2):
    return cmp(s1.lower(), s2.lower())

def fromDelphiTDateTime(date):
    """
    Delphi datetimes int part is num days from 30 Dec 1899
    fractional part is part of a day??
    """
    delta = datetime.timedelta(date)
    dateZero = datetime.datetime(1899, 12, 30)
    return dateZero + delta

def toDelphiTDateTime(date):
    dateZero = datetime.datetime(1899, 12, 30)
    diff = date - dateZero
    return diff.days + (diff.seconds / 86400.0)

class playCollection(dict):
    
    def __init__(self, data=[]):
        '''
        :Parameters:
            `data` A list of trackDetails
        '''
        for track in data:
            self.addTrack(track)

    def addTrack(self, track):
        '''
        :Parameters:
            `track` A trackDetails object
        '''
        if track not in self:
            self[track] = {}
        try:
            album = getattr(track, 'album').lower()
        except AttributeError:
            album = None
        if album in self[track]:
            if track.played_on not in self[track][album]['played_on']:
                self[track][album]['played_on'].append(track.played_on)
        else:
            self[track][album] = {
                'played_on' : [track.played_on],
                'play_count' : getattr(track, 'play_count', 0)
                }
            trackId = getattr(track,'id',None)
            if trackId:
                self[track][album]['id'] = trackId
                
class trackDetails(object):
    properties = ["name", "artist"]
    non_eq_properties = ["played_on_uts", "played_on", "play_count", "album", "id"]
    both = properties + non_eq_properties
    
    def __init__(self, track):
        for field in self.both:
            try:
                attr = getattr(track, field, None) or track[field]
            except (IndexError, TypeError, KeyError):
                attr = None
            if attr is not None:
                setattr(self, field, attr)
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__hash__() == other.__hash__())
            
    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)
    
    def __hash__(self):
        tmp = 0
        for field in self.properties:
            tmp = tmp + hash(getattr(self, field).lower())
        return hash(tmp)

class lastFmImport(object):

    def rlength(self, diction):
        if len(diction) == 0:
            return 0
        bottom = False
        total = 0
        for value in diction.itervalues():
            if type(value) != dict:
                bottom = True
                break
            total = total + self.rlength(value)
        if bottom:
            return len(diction)
        return total
    
    def displayError(self, exception):
        SDB = self.SDB
        logging.debug("Got exception: %s", exception)
        SDB.MessageBox("We encountered an error:\n%s" % exception, 1, [4])
    
    def displayResult(self, results):
        SDB = self.SDB
        SDB.MessageBox("Results:\n%s" % results, 2, [4])
        
    def setOptions(self):
        loggingPath = os.path.join(self.scriptPath, 'Log.txt')
        # TODO Look at this before rollout
        logging.basicConfig(filename=loggingPath, level=logging.DEBUG, 
                            format='%(asctime)s: %(message)s')
        optionsPath = os.path.join(self.scriptPath, 'Options')
        options = shelve.open(optionsPath)
        SDB = self.SDB
        form = SDB.UI.NewForm
        form.Caption = "LastFm Play Importer"
        form.BorderStyle = 3
        form.FormPosition = 4
        form.StayOnTop = True
        form.Common.SetRect(0,0,260,140)
        #iBorderWidth = frmDialog.Common.Width - frmDialog.Common.ClientWidth
        #iBorderHeight = frmDialog.Common.Height - frmDialog.Common.ClientHeight
        #frmDialog.Common.SetRect (100, 100, 570 + iBorderWidth, 524 + iBorderHeight)
        #frmDialog.Common.MinWidth = 570 + iBorderWidth
        #frmDialog.Common.MinHeight = 522 + iBorderHeight
        #frmDialog.FormPosition = mmFormScreenCenter
        label1 = SDB.UI.NewLabel(form)
        label1.Caption = "Username"
        label1.Common.SetRect(20,10,100,20)
        
        
        edit1 = SDB.UI.NewEdit(form)
        edit1.Text = options.get('username','')
        edit1.Common.SetRect(140,10,100,20)
        
        
        check1 = SDB.UI.NewCheckBox(form)
        check1.Caption = "Update played times?"
        check1.Checked = options.get('update_played_times', False)
        check1.Common.SetRect(20,40,200,20)
        
        
        button1 = SDB.UI.NewButton(form)
        button1.Caption = "&Go!"
        button1.Common.SetRect(50,80,60,20)
        button1.ModalResult = 1
        button1.Default = True
        
        button2 = SDB.UI.NewButton(form)
        button2.Caption = "&Cancel"
        button2.Common.SetRect(150,80,60,20)
        button2.ModalResult = 2
        button2.Cancel = True
        
        if form.ShowModal() != 1:
            return False
        # Get options
        options['username'] = edit1.Text
        options['update_played_times'] = check1.Checked
        self.username = options['username']
        self.update_played_times = options['update_played_times']
        options.close()
        return True
        
    def run(self):
        SDB = win32com.client.Dispatch("SongsDB.SDBApplication")
        
        self.SDB = SDB
        self.scriptPath = os.path.join(SDB.ScriptsPath, "LastFmImportPython")
        self.statusBar = SDB.Progress
        success = False
        
        # Set the username and update played times options, exit if cancel
        # was pressed
        if not self.setOptions():
            return
        
        try:
            # XXX Find a nice number....
            self.pool = ThreadPool(processes=10)
            self.pool2 =  ThreadPool(processes=2)
            while not success:
                try:
                    if self.statusBar.Terminate:
                        raise ManualCancel(None,None)
                    lastFmCollection = self.getLastFmDetails()
                except lastfm.error.InvalidParametersError as e:
                    self.displayError(e)
                    return
                except ManualCancel:
                    raise
                except PullError, e:
                    logging.warning("We got an exception: %s",  
                                    type(getattr(e, 'orig_exception','')))
                    pass
                else:
                    success = True
        finally:
            # I'd love to terminate but it seem to freeze if the child
            # raises an Exception in a funny way? (if the exception doesn't 
            # call __init__ of  Exception)
            self.statusBar.Text = "Closing last.fm threads, about to start updating."
            # Not strictly needed, but probably a good idea
            logging.debug("Closing threads.")
            self.pool.close()
            self.pool2.close()
            # No need to join as we don't *really* care about the data we get
            # back any more :P
            logging.debug("Threads Closed.")
#        lastFmCollection = playCollection(lastFmData)        
        dbData = self.getDbDetails()
        dbCollection = playCollection(dbData)
        
        self.updateDb(dbCollection, lastFmCollection)
    
    def getDbDetails(self):
        try:
            conn = sqlite3.connect(self.SDB.Database.Path)
            conn.create_collation('IUNICODE', iUnicodeCollate)
            conn.row_factory = sqlite3.Row
            
            query = """SELECT Artist as artist, Album as album, SongTitle as name,
                 PlayCounter as play_count, LastTimePlayed as played_on, ID as id 
                FROM Songs"""
            # Queries are slow, do them at artist level, and iterate lower
            results = []
            for track in conn.execute(query):
                trackDict = {}
                for key in track.keys():
                    trackDict[key] = track[key]
                # Update the time returned from the database
                # XXX Update this to pull all plays from MM
                trackDict['played_on'] = fromDelphiTDateTime(trackDict['played_on'])
                
                results.append(trackDetails(trackDict))
            return results 
        finally:
            conn.close()
        
        
    def updateDb(self, dbData, lastFmData):
        logging.debug("Starting matches")
        updated = 0
        updatedDate = 0
        updatedCount = 0
        matchedWithoutAlbum = 0
        matches = 0

        # Status bar stuff
        statusBar = self.statusBar
        statusBar.MaxValue = len(lastFmData)
        statusBar.Value = 0

        updateList = []
        nonMatchedList = []
        conn = sqlite3.connect(self.SDB.Database.Path)
        conn.create_collation('IUNICODE', iUnicodeCollate)
        for track, albums in lastFmData.iteritems():
            statusBar.Increase()
            statusBar.Text = "Matching tracks. %s/%s - %s Matches" %(statusBar.Value, statusBar.MaxValue, matches)
            if track in dbData:
                for album, details in albums.iteritems():
                    if album is None:
                        # Try just updating the first one...?
                        #if len(dbData[track]) > 1:
                        logging.debug('We are updating %s tracks on different albums', len(dbData[track]))
                        matchedWithoutAlbum = matchedWithoutAlbum + 1
                        album = next(dbData[track].iterkeys())
                        # We also need to see if this album existed in other lastFM Data and combine their data!
                        if album in albums:
                            albums[album]['played_on'].extend(details['played_on'])
                    album = album.lower()
                    if album in dbData[track]:
                        # Now we compare stuff
                        newTrack = {'id' : dbData[track][album]['id']}
                        thisUpdated = False
                        matches = matches + 1
                        query = []
                        if dbData[track][album]['play_count'] < len(details['played_on']):
                            newTrack['play_count'] = len(details['played_on'])
                            thisUpdated = True
                            updatedCount = updatedCount + 1
                            query.append('PlayCounter=:play_count')
                        # Update last played date if it's older
                        latest_played = max(details['played_on'])
                        latest_played_db = max(dbData[track][album]['played_on'])
                        if self.update_played_times and latest_played_db < latest_played:
                            newTrack['played_on'] = toDelphiTDateTime(latest_played)
                            thisUpdated = True
                            updatedDate = updatedDate + 1
                            query.append('LastTimePlayed=:played_on')                      
                        if thisUpdated:
                            updated = updated + 1
                            updateList.append((newTrack,track,album, dbData[track][album]))
                            query = "UPDATE Songs SET " + ','.join(query) + " WHERE ID=:id"
                            conn.execute(query, newTrack)
                    else:
                        nonMatchedList.append(('Match failed on: Album',track))
            else:
                nonMatchedList.append(('Match failed on: Artist/trackname',track))

        fileObj = open(os.path.join(self.scriptPath, 'updated.txt'),mode='w')
        fileObj.writelines([str(x)+'\n' for x in updateList])
        fileObj.close()
        
        fileObj = codecs.open(os.path.join(self.scriptPath, 'unMatched.txt'),mode='w')
        fileObj.writelines([str(x)+'\n' for x in nonMatchedList])
        fileObj.close()
    
        resultStr = ("Updated: %s\nUpdatedDates: %s\nUpdatedCounts: %s\nMatches: %s\n"
               "Matched without album: %s\nUnmatched: %s\nTotal rows changed: %s" 
               % (updated, updatedDate, updatedCount, matches,
                  matchedWithoutAlbum, len(nonMatchedList), conn.total_changes))
        conn.commit()
        conn.close()        
        logging.info(resultStr)
        self.displayResult(resultStr)
    
    def getLastFmDetails(self):
        ''' 
        Will also look at cached files and pull down stuff more recent
        saves result to a cache 
        '''
        path = os.path.join(self.scriptPath, 'Cache')
        # writeback is required as we are using mutable objects inside the 
        # dict
        logging.debug('Reading existing cache from %s', path)
        shelf = shelve.open(path, writeback=True)
        earliest_date = shelf.get('earliest_date')
        latest_date = shelf.get('latest_date')
        
        # We add some time on either side inwards to catch delayed scrobbles or 
        # missed tracks at the end.
        # For now, approx 1 week - 60seconds * 60*24*7
        #padding = 60*60*24*7
        padding = 60*60*24
        if earliest_date:
            earliest_date = str(int(earliest_date) + padding)
        if latest_date:
            latest_date = str(int(latest_date) - padding)
        logging.debug("Excluding between dates %s and %s", earliest_date, latest_date)
        tmp_earliest_date1 = tmp_latest_date1 = tmp_earliest_date2 = tmp_latest_date2 = None
        try:
            if earliest_date < latest_date:
                # If we have some dates, we only pull data from either side of them 
                tmp_earliest_date1, tmp_latest_date1 = self.pullLastFmDetails(
                                    shelf.setdefault('data', playCollection()),
                                    date_to=earliest_date)
                tmp_earliest_date2, tmp_latest_date2 = self.pullLastFmDetails(
                                    shelf.setdefault('data', playCollection()),
                                    date_from=latest_date)
                earliest_date = min(x for x in 
                    (earliest_date, tmp_earliest_date1, tmp_earliest_date2)
                    if x is not None)
                latest_date = max(latest_date, tmp_latest_date1, tmp_latest_date2)
            else:
                # Otherwise we grab everything!
                earliest_date, latest_date = self.pullLastFmDetails(
                                    shelf.setdefault('data', playCollection()),
                                    )
            # Now turn the data into something useable
            
            retVal = shelf['data']
        except ExceptionWithDates, e:
            # If we got an error we should still have updated our dict and
            # have some dates, so save these so re-running later doesn't 
            # need to pull as much.
            earliest_date = min(x for x in
                (earliest_date,
                 tmp_earliest_date1,
                 tmp_earliest_date2,
                 e.earliest_date)
                if x is not None)
            latest_date = max(latest_date, tmp_latest_date1, tmp_latest_date2,
                              e.latest_date)
            raise
        finally:
            shelf['earliest_date'] = earliest_date
            shelf['latest_date'] = latest_date
            shelf.close() 

        return retVal

                    
    def pullLastFmDetails(self, data, date_to=None, date_from=None):
        '''
        :Parameters:
            `data` - A playCollection Object
        
        :Keywords:
            `date_to` - Only pull tracks until this date
                            as an int unix time stamp
            `date_from` - Only pull tracks from this date
                            as an int unix time stamp
        
        :Returns:
            The date of the most recent play on last.fm
        '''
        # Max limit is 200, but we get quicker responses with smaller pages
        limit = 200
        timeout = limit
        api_key = 'daadfc9c6e9b2c549527ccef4af19adb'
        
        api = lastfm.Api(api_key)
        user = api.get_user(self.username)
        
        # Status bar stuff
        statusBar = self.statusBar
        statusBar.Text = "Loading Initial Recent Tracks"
        
        logging.debug("Pulling tracks between %s - %s", date_from, date_to)
        result = self.pool.apply_async(user.get_recent_tracks_pages, [limit], 
                        {'date_from':date_from, 'date_to':date_to})
        try:
            numPagesResult = self.pool.apply_async(result.get, [timeout])
            while not numPagesResult.ready():
                time.sleep(0.5)
                if self.statusBar.Terminate:
                    raise ManualCancel(None,None)
            numPages = numPagesResult.get()
        except Exception, e:
            raise PullError(None, None, e) 
        
        if numPages == 0:
            return date_to, date_from
        if statusBar.MaxValue != 9999:
            # This is a retry... make the current value = 
            statusBar.Value = statusBar.maxValue - numPages
        else:
            statusBar.MaxValue = numPages
            statusBar.Value = 0 
        
        statusBar.Text = "Loading pages: %s / %s " % (statusBar.Value, statusBar.MaxValue)
        
        def getPage(page):
            logging.debug("Getting page %s...", page)
            result = user.get_recent_tracks(limit=limit, date_from=date_from, 
                               date_to=date_to, page=page)
            logging.debug("... done with page %s", page)
            return result

        tracksIter = self.pool.imap(getPage, range(1,numPages+1))
        latest_date = earliest_date = None
        while True:
            tracksResult = self.pool2.apply_async(tracksIter.next, [timeout])
            while not tracksResult.ready():
                time.sleep(0.5)
                if self.statusBar.Terminate:
                    raise ManualCancel(None,None)
            try:
                tracks = tracksResult.get()
            except StopIteration:
                break
            except TimeoutError, e:
                raise PullError(earliest_date, latest_date, e) 
            statusBar.Increase()
            statusBar.Text = "Loading page: %s / %s " \
                % (statusBar.Value, statusBar.MaxValue)
            for track in tracks: 
                # Now append the details if this one isn't already in the list
                details = trackDetails(track)
                data.addTrack(details)
                # Cache the earliest and the latest result dates
                if latest_date is None or track.played_on_uts > latest_date:
                    latest_date = track.played_on_uts
                if earliest_date is None or track.played_on_uts < earliest_date:
                    earliest_date = track.played_on_uts
        # The dict is updated in place, return the last played date
        return earliest_date, latest_date

class ExceptionWithDates(Exception):
    def __init__(self, earliest_date, latest_date, orig_exception=None):
        self.earliest_date = earliest_date
        self.latest_date = latest_date
        self.orig_exception = orig_exception

        
class PullError(ExceptionWithDates):
    pass


class ManualCancel(ExceptionWithDates):
    pass

if __name__ == '__main__':
    importer = lastFmImport()
    try:
        #cProfile.run('importer.run()', sort='time')
        try:
            importer.run()
        finally:
            del(importer.statusBar)
    except ManualCancel, e:
        logging.debug("Script was cancelled manually")
        pass
    except Exception, e:
        logging.error("Exception encountered: %s", e)
    
    sys.exit(0)