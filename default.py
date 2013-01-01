#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Team-XBMC
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#    This script is based on script.randomitems & script.wacthlist
#    Thanks to their original authors

import os
import sys
import xbmc
import xbmcgui
import xbmcaddon
import random
import datetime
import _strptime
import urllib

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__        = xbmcaddon.Addon()
__addonversion__ = __addon__.getAddonInfo('version')
__addonid__      = __addon__.getAddonInfo('id')
__addonname__    = __addon__.getAddonInfo('name')

def log(txt):
    message = '%s: %s' % (__addonname__, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

class Main:
    def __init__(self):
        self._parse_argv()
        # check how we were executed
        if self.MOVIEID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "movieid": %d }, "options":{ "resume": true } }, "id": 1 }' % int(self.MOVIEID))
        elif self.EPISODEID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "episodeid": %d }, "options":{ "resume": true }  }, "id": 1 }' % int(self.EPISODEID))
        elif self.MUSICVIDEOID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "musicvideoid": %d } }, "id": 1 }' % int(self.MUSICVIDEOID))
        elif self.ALBUMID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "albumid": %d } }, "id": 1 }' % int(self.ALBUMID))
        elif self.SONGID:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "songid": %d } }, "id": 1 }' % int(self.SONGID))
        else:
            self._init_vars()
            self._init_property()
            # clear our property, if another instance is already running it should stop now
            self.WINDOW.clearProperty('SkinWidgets_Running')
            a_total = datetime.datetime.now()
            #self._fetch_info_randomitems()
            #self._fetch_info_recommended()
            self._fetch_info_recentitems()
            self._fetch_info_inprogress()
            b_total = datetime.datetime.now()
            c_total = b_total - a_total
            log('Total time needed for all queries: %s' % c_total)
            # give a possible other instance some time to notice the empty property
            self.WINDOW.setProperty('SkinWidgets_Running', 'true')
            self._daemon()

    def _init_vars(self):
        self.WINDOW = xbmcgui.Window(10000)
        self.Player = Widgets_Player(action = self._update)
        self.Monitor = Widgets_Monitor(update_listitems = self._update, update_settings = self._init_property)
        self.LIMIT = 20
        self.inprogressvideos = []


    def _init_property(self):
        self.WINDOW.setProperty('SkinWidgets_Recommended', '%s' % __addon__.getSetting("recommended_enable"))
        self.WINDOW.setProperty('SkinWidgets_RandomItems', '%s' % __addon__.getSetting("randomitems_enable"))
        self.WINDOW.setProperty('SkinWidgets_RecentItems', '%s' % __addon__.getSetting("recentitems_enable"))
        self.WINDOW.setProperty('SkinWidgets_InProgressItems', '%s' % __addon__.getSetting("inprogressitems_enable"))
        self.WINDOW.setProperty('SkinWidgets_RandomItems_Update', 'false')
        self.RANDOMITEMS_UPDATE_METHOD = int(__addon__.getSetting("randomitems_method"))
        self.RECENTITEMS_HOME_UPDATE = __addon__.getSetting("recentitems_homeupdate")
        self.INPROGRESSITEMS_HOME_UPDATE = __addon__.getSetting("inprogressitems_homeupdate")
        # convert time to seconds, times 2 for 0,5 second sleep compensation
        self.RANDOMITEMS_TIME = int(__addon__.getSetting("randomitems_time").rstrip('0').rstrip('.')) * 60 * 2

    def _parse_argv( self ):
        try:
            params = dict( arg.split( "=" ) for arg in sys.argv[ 1 ].split( "&" ) )
        except:
            params = {}
        self.MOVIEID = params.get( "movieid", "" )
        self.EPISODEID = params.get( "episodeid", "" )
        self.MUSICVIDEOID = params.get( "musicvideoid", "" )
        self.ALBUMID = params.get( "albumid", "" )
        self.SONGID = params.get( "songid", "" )
        print self.EPISODEID

    def _fetch_info_recommended(self):
        a = datetime.datetime.now()
        if __addon__.getSetting("recommended_enable") == 'true':
            self._fetch_movies('RecommendedMovie')
            self._fetch_tvshows_recommended('RecommendedEpisode')
            self._fetch_albums('RecommendedAlbum')
            self._fetch_musicvideo('RecommendedMusicVideo')
            b = datetime.datetime.now()
            c = b - a
            log('Total time needed to request recommended queries: %s' % c)

    def _fetch_info_randomitems(self):
        a = datetime.datetime.now()
        if __addon__.getSetting("randomitems_enable") == 'true':
            self.RANDOMITEMS_UNPLAYED = __addon__.getSetting("randomitems_unplayed") == 'true'
            self._fetch_movies('RandomMovie')
            self._fetch_tvshows('RandomEpisode')
            self._fetch_musicvideo('RandomMusicVideo')
            self._fetch_albums('RandomAlbum')
            self._fetch_artist('RandomArtist')
            self._fetch_song('RandomSong')
            self._fetch_addon('RandomAddon')
            b = datetime.datetime.now()
            c = b - a
            log('Total time needed to request random queries: %s' % c)

    def _fetch_info_recentitems(self):
        a = datetime.datetime.now()
        if __addon__.getSetting("recentitems_enable") == 'true':
            self.RECENTITEMS_UNPLAYED = __addon__.getSetting("recentitems_unplayed") == 'true'
            self._fetch_movies('RecentMovie')
            self._fetch_tvshows('RecentEpisode')
            #self._fetch_musicvideo('RecentMusicVideo')
            #self._fetch_albums('RecentAlbum')
            b = datetime.datetime.now()
            c = b - a
            log('Total time needed to request recent items queries: %s' % c)
            
    def _fetch_info_inprogress(self):
        a = datetime.datetime.now()
        if __addon__.getSetting("inprogressitems_enable") == 'true':
            self.inprogressvideos = []
            self._clear_properties('InProgress')
            self._fetch_movies('InProgress')
            self._fetch_tvshows('InProgress')
            self._set_properties('InProgress')
            b = datetime.datetime.now()
            c = b - a
            log('Total time needed to request inprogress items queries: %s' % c)

    def _set_properties(self, request):
        from operator import itemgetter, attrgetter
        self.inprogressvideos.sort(key=itemgetter(0))
        
        count = 0
        for v in self.inprogressvideos:
            count += 1
            item = v[2]

            log('Adding inprogress video titled = "' + item['title'] + '" - ' + self._seconds_to_string(v[0],'long') + ' (' + str(v[0]) + ')')
            self.WINDOW.setProperty("%s.%d.Type"            % (request, count), v[1])
            self.WINDOW.setProperty("%s.%d.File"            % (request, count), item['file'])
            self.WINDOW.setProperty("%s.%d.Path"            % (request, count), media_path(item['file']))
            self.WINDOW.setProperty("%s.%d.RemainingTime"   % (request, count ), self._seconds_to_string(v[0],'long') )
          
            if v[1]=='movie':
                self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                self.WINDOW.setProperty("%s.%d.Title2"      % (request, count), item['tagline'])
                self.WINDOW.setProperty("%s.%d.Play"        % (request, count), 'XBMC.RunScript(' + __addonid__ + ',movieid=' + str(item.get('movieid')) + ')')
                self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['art'].get('fanart',''))
            else:
                self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['showtitle'])
                self.WINDOW.setProperty("%s.%d.Title2"      % (request, count), "s%.2de%.2d - %s" % ( float(item['season']), float(item['episode']), item['title']))
                self.WINDOW.setProperty("%s.%d.Play"        % (request, count), 'XBMC.RunScript(' + __addonid__ + ',episodeid=' + str(item.get('episodeid')) + ')')
                self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['art'].get('tvshow.fanart',''))

            if count == self.LIMIT:
                break
          
                

    def _fetch_movies(self, request):
        if not xbmc.abortRequested:
            json_string = '{"jsonrpc": "2.0",  "id": 1, "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "playcount", "year", "genre", "studio", "tagline", "plot", "runtime", "file", "plotoutline", "lastplayed", "trailer", "rating", "resume", "art", "streamdetails"], "limits": {"end": %d},' %self.LIMIT
            if request == 'RecommendedMovie':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "lastplayed"}, "filter": {"field": "inprogress", "operator": "true", "value": ""}}}' %json_string)
            elif request == 'RecentMovie' and self.RECENTITEMS_UNPLAYED:
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}, "filter": {"field": "playcount", "operator": "is", "value": "0"}}}' %json_string)
            elif request == 'RecentMovie':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}}}' %json_string)
            elif request == "RandomMovie" and self.RANDOMITEMS_UNPLAYED:
                json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" }, "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}}}' %json_string)
            elif request == 'InProgress':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}, "filter": {"field": "inprogress", "operator": "true", "value": ""}}}' %json_string)
            else:
                json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" } }}' %json_string)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            count2 = 0
            if json_query['result'].has_key('movies'):
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['movies']:
                  if item['resume']['position'] > 0 and ( (request == "RandomMovie" and self.RANDOMITEMS_UNPLAYED) or (request == 'RecentMovie' and self.RECENTITEMS_UNPLAYED) ):
                    pass
                  else:
                    count += 1
                    if (item['resume']['position'] and item['resume']['total'])> 0:
                        resume = "true"
                        played = '%s%%'%int((float(item['resume']['position']) / float(item['resume']['total'])) * 100)
                    else:
                        resume = "false"
                        played = '0%'
                    if item['playcount'] >= 1:
                        watched = "true"
                    else:
                        watched = "false"
                    art = item['art']
                    path = media_path(item['file'])
                    play = 'XBMC.RunScript(' + __addonid__ + ',movieid=' + str(item.get('movieid')) + ')'
                    streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                               item['streamdetails'])
                    # Temporary check if runtime is an int or str
                    if isinstance(item['runtime'],int):
                        runtime = str(item['runtime']/60)
                    else:
                        runtime = item['runtime']

                    if request == "InProgress":
                        if item['resume']['position'] > 0:
                            count2 += 1
                            self.inprogressvideos.append((float(item['resume']['total']) - float(item['resume']['position']),'movie',item))
                    else:
                        self.WINDOW.setProperty("%s.%d.Title"           % (request, count), item['title'])
                        self.WINDOW.setProperty("%s.%d.Year"            % (request, count), str(item['year']))
                        self.WINDOW.setProperty("%s.%d.Genre"           % (request, count), " / ".join(item['genre']))
                        self.WINDOW.setProperty("%s.%d.Studio"          % (request, count), item['studio'][0])
                        self.WINDOW.setProperty("%s.%d.Plot"            % (request, count), item['plot'])
                        self.WINDOW.setProperty("%s.%d.PlotOutline"     % (request, count), item['plotoutline'])
                        self.WINDOW.setProperty("%s.%d.Tagline"         % (request, count), item['tagline'])
                        self.WINDOW.setProperty("%s.%d.Runtime"         % (request, count), runtime)
                        self.WINDOW.setProperty("%s.%d.Rating"          % (request, count), str(round(float(item['rating']),1)))
                        self.WINDOW.setProperty("%s.%d.Trailer"         % (request, count), item['trailer'])
                        self.WINDOW.setProperty("%s.%d.Art(poster)"     % (request, count), art.get('poster',''))
                        self.WINDOW.setProperty("%s.%d.Art(fanart)"     % (request, count), art.get('fanart',''))
                        self.WINDOW.setProperty("%s.%d.Art(clearlogo)"  % (request, count), art.get('clearlogo',''))
                        self.WINDOW.setProperty("%s.%d.Art(clearart)"   % (request, count), art.get('clearart',''))
                        self.WINDOW.setProperty("%s.%d.Art(landscape)"  % (request, count), art.get('landscape',''))
                        self.WINDOW.setProperty("%s.%d.Art(banner)"     % (request, count), art.get('banner',''))
                        self.WINDOW.setProperty("%s.%d.Art(discart)"    % (request, count), art.get('discart',''))                
                        self.WINDOW.setProperty("%s.%d.Resume"          % (request, count), resume)
                        self.WINDOW.setProperty("%s.%d.PercentPlayed"   % (request, count), played)
                        self.WINDOW.setProperty("%s.%d.Watched"         % (request, count), watched)
                        self.WINDOW.setProperty("%s.%d.File"            % (request, count), item['file'])
                        self.WINDOW.setProperty("%s.%d.Path"            % (request, count), path)
                        self.WINDOW.setProperty("%s.%d.Play"            % (request, count), play)
                        self.WINDOW.setProperty("%s.%d.VideoCodec"      % (request, count), streaminfo['videocodec'])
                        self.WINDOW.setProperty("%s.%d.VideoResolution" % (request, count), streaminfo['videoresolution'])
                        self.WINDOW.setProperty("%s.%d.VideoAspect"     % (request, count), streaminfo['videoaspect'])
                        self.WINDOW.setProperty("%s.%d.AudioCodec"      % (request, count), streaminfo['audiocodec'])
                        self.WINDOW.setProperty("%s.%d.AudioChannels"   % (request, count), str(streaminfo['audiochannels']))

            if request == "InProgress":
                log('Found ' + str(count2) + ' movies inprogress')
            del json_query

    def _fetch_tvshows_recommended(self, request):
        if not xbmc.abortRequested:
            # First unplayed episode of recent played tvshows
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties": ["title", "studio", "file", "art"], "sort": {"order": "descending", "method": "lastplayed"}, "filter": {"field": "inprogress", "operator": "true", "value": ""}, "limits": {"end": %d}}, "id": 1}' %self.LIMIT)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            if json_query['result'].has_key('tvshows'):
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['tvshows']:
                    if xbmc.abortRequested:
                        break
                    count += 1
                    json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"tvshowid": %d, "properties": ["title", "playcount", "plot", "season", "episode", "showtitle", "file", "lastplayed", "rating", "resume", "art", "streamdetails"], "sort": {"method": "episode"}, "filter": {"field": "playcount", "operator": "is", "value": "0"}, "limits": {"end": 1}}, "id": 1}' %item['tvshowid'])
                    json_query2 = unicode(json_query2, 'utf-8', errors='ignore')
                    json_query2 = simplejson.loads(json_query2)
                    if json_query2.has_key('result') and json_query2['result'] != None and json_query2['result'].has_key('episodes'):
                        for item2 in json_query2['result']['episodes']:
                            episode = ("%.2d" % float(item2['episode']))
                            season = "%.2d" % float(item2['season'])
                            rating = str(round(float(item2['rating']),1))
                            episodeno = "s%se%s" %(season,episode)
                            art2 = item2['art']
                    #seasonthumb = ''
                    if (item2['resume']['position'] and item2['resume']['total']) > 0:
                        resume = "true"
                        played = '%s%%'%int((float(item2['resume']['position']) / float(item2['resume']['total'])) * 100)
                    else:
                        resume = "false"
                        played = '0%'
                    art = item['art']
                    path = media_path(item['file'])
                    play = 'XBMC.RunScript(' + __addonid__ + ',episodeid=' + str(item2.get('episodeid')) + ')'
                    streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                     item2['streamdetails'])
                    self.WINDOW.setProperty("%s.%d.Title"               % (request, count), item2['title'])
                    self.WINDOW.setProperty("%s.%d.Episode"             % (request, count), episode)
                    self.WINDOW.setProperty("%s.%d.EpisodeNo"           % (request, count), episodeno)
                    self.WINDOW.setProperty("%s.%d.Season"              % (request, count), season)
                    self.WINDOW.setProperty("%s.%d.Plot"                % (request, count), item2['plot'])
                    self.WINDOW.setProperty("%s.%d.TVshowTitle"         % (request, count), item2['showtitle'])
                    self.WINDOW.setProperty("%s.%d.Rating"              % (request, count), rating)
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"          % (request, count), art2.get('thumb',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.fanart)"  % (request, count), art2.get('tvshow.fanart',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.poster)"  % (request, count), art2.get('tvshow.poster',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.banner)"  % (request, count), art2.get('tvshow.banner',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.clearlogo)"% (request, count), art2.get('tvshow.clearlogo',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.clearart)" % (request, count), art2.get('tvshow.clearart',''))
                    self.WINDOW.setProperty("%s.%d.Art(tvshow.landscape)"% (request, count), art2.get('tvshow.landscape',''))
                    #self.WINDOW.setProperty("%s.%d.Art(season.poster)" % (request, count), seasonthumb)
                    self.WINDOW.setProperty("%s.%d.Studio"              % (request, count), item['studio'][0])
                    self.WINDOW.setProperty("%s.%d.Resume"              % (request, count), resume)
                    self.WINDOW.setProperty("%s.%d.PercentPlayed"       % (request, count), played)
                    self.WINDOW.setProperty("%s.%d.File"                % (request, count), item2['file'])
                    self.WINDOW.setProperty("%s.%d.Path"                % (request, count), path)
                    self.WINDOW.setProperty("%s.%d.Play"                % (request, count), play)
                    self.WINDOW.setProperty("%s.%d.VideoCodec"          % (request, count), streaminfo['videocodec'])
                    self.WINDOW.setProperty("%s.%d.VideoResolution"     % (request, count), streaminfo['videoresolution'])
                    self.WINDOW.setProperty("%s.%d.VideoAspect"         % (request, count), streaminfo['videoaspect'])
                    self.WINDOW.setProperty("%s.%d.AudioCodec"          % (request, count), streaminfo['audiocodec'])
                    self.WINDOW.setProperty("%s.%d.AudioChannels"       % (request, count), str(streaminfo['audiochannels']))
            del json_query

    def _fetch_tvshows(self, request):
        if not xbmc.abortRequested:
            season_folders = __addon__.getSetting("randomitems_seasonfolders")
            json_string = '{"jsonrpc": "2.0", "id": 1, "method": "VideoLibrary.GetEpisodes", "params": { "properties": ["title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails"], "limits": {"end": %d},' %self.LIMIT
            if request == 'RecentEpisode' and self.RECENTITEMS_UNPLAYED:
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}, "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}}}' %json_string)
            elif request == 'RecentEpisode':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}}}' %json_string)
            elif request == 'RandomEpisode' and self.RANDOMITEMS_UNPLAYED:
                json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" }, "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}}}' %json_string)
            elif request == 'InProgress':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}, "filter": {"field": "inprogress", "operator": "true", "value": ""}}}' %json_string)
            else:
                json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random" }}}' %json_string)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            count2 = 0
            if json_query['result'].has_key('episodes'):
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['episodes']:
                  if item['resume']['position'] > 0 and ( (request == 'RandomEpisode' and self.RANDOMITEMS_UNPLAYED) or (request == 'RecentEpisode' and self.RECENTITEMS_UNPLAYED) ):
                    pass
                  else:
                    count += 1
                    '''
                    # This part is commented out because it takes 1.5second extra on my system to request these which doubles the total time.
                    # Hence the ugly path hack that will require users to have season folders.
                    json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShowDetails", "params": {"properties": ["file", "studio"], "tvshowid":%s}, "id": 1}' %item['tvshowid'])
                    json_query2 = unicode(json_query2, 'utf-8', errors='ignore')
                    json_query2 = simplejson.loads(json_query2)
                    path = json_query2['result']['tvshowdetails']['file']
                    studio = json_query2['result']['tvshowdetails']['studio'][0]
                    '''
                    if season_folders == 'true':
                        path = os.path.split(media_path(item['file']))[0]
                    else:
                        path = media_path(item['file'])
                    episode = ("%.2d" % float(item['episode']))
                    season = "%.2d" % float(item['season'])
                    episodeno = "S%sE%s" %(season,episode)
                    #seasonthumb = ''
                    rating = str(round(float(item['rating']),1))
                    if (item['resume']['position'] and item['resume']['total']) > 0:
                        resume = "true"
                        played = '%s%%'%int((float(item['resume']['position']) / float(item['resume']['total'])) * 100)
                    else:
                        resume = "false"
                        played = '0%'
                    art = item['art']
                    path = media_path(item['file'])
                    play = 'XBMC.RunScript(' + __addonid__ + ',episodeid=' + str(item.get('episodeid')) + ')'
                    streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                     item['streamdetails'])

                    if request == "InProgress":
                        if item['resume']['position'] > 0:
                            count2 += 1
                            self.inprogressvideos.append((float(item['resume']['total']) - float(item['resume']['position']),'episode',item))
                    else:
                        self.WINDOW.setProperty("%s.%d.Title"               % (request, count), item['title'])
                        self.WINDOW.setProperty("%s.%d.Episode"             % (request, count), episode)
                        self.WINDOW.setProperty("%s.%d.EpisodeNo"           % (request, count), episodeno)
                        self.WINDOW.setProperty("%s.%d.Season"              % (request, count), season)
                        self.WINDOW.setProperty("%s.%d.Plot"                % (request, count), item['plot'])
                        self.WINDOW.setProperty("%s.%d.TVshowTitle"         % (request, count), item['showtitle'])
                        self.WINDOW.setProperty("%s.%d.Rating"              % (request, count), rating)
                        self.WINDOW.setProperty("%s.%d.Art(thumb)"          % (request, count), art.get('thumb',''))
                        self.WINDOW.setProperty("%s.%d.Art(tvshow.fanart)"  % (request, count), art.get('tvshow.fanart',''))
                        self.WINDOW.setProperty("%s.%d.Art(tvshow.poster)"  % (request, count), art.get('tvshow.poster',''))
                        self.WINDOW.setProperty("%s.%d.Art(tvshow.banner)"  % (request, count), art.get('tvshow.banner',''))
                        self.WINDOW.setProperty("%s.%d.Art(tvshow.clearlogo)"% (request, count), art.get('tvshow.clearlogo',''))
                        self.WINDOW.setProperty("%s.%d.Art(tvshow.clearart)" % (request, count), art.get('tvshow.clearart',''))
                        self.WINDOW.setProperty("%s.%d.Art(tvshow.landscape)"% (request, count), art.get('tvshow.landscape',''))
                        self.WINDOW.setProperty("%s.%d.Resume"              % (request, count), resume)
                        self.WINDOW.setProperty("%s.%d.PercentPlayed"       % (request, count), played)
                        self.WINDOW.setProperty("%s.%d.File"                % (request, count), item['file'])
                        self.WINDOW.setProperty("%s.%d.Path"                % (request, count), path)
                        self.WINDOW.setProperty("%s.%d.Play"                % (request, count), play)
                        self.WINDOW.setProperty("%s.%d.VideoCodec"          % (request, count), streaminfo['videocodec'])
                        self.WINDOW.setProperty("%s.%d.VideoResolution"     % (request, count), streaminfo['videoresolution'])
                        self.WINDOW.setProperty("%s.%d.VideoAspect"         % (request, count), streaminfo['videoaspect'])
                        self.WINDOW.setProperty("%s.%d.AudioCodec"          % (request, count), streaminfo['audiocodec'])
                        self.WINDOW.setProperty("%s.%d.AudioChannels"       % (request, count), str(streaminfo['audiochannels']))
            if request == "InProgress":
                log('Found ' + str(count2) + ' episodes inprogress')
            del json_query

    def _fetch_seasonthumb(self, tvshowid, seasonnumber):
        json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetSeasons", "params": {"properties": ["season", "thumbnail"], "tvshowid":%s }, "id": 1}' % tvshowid)
        json_query = unicode(json_query, 'utf-8', errors='ignore')
        json_query = simplejson.loads(json_query)
        if json_query['result'].has_key('seasons'):
            for item in json_query['result']['seasons']:
                season = "%.2d" % float(item['season'])
                if season == seasonnumber:
                    thumbnail = item['thumbnail']
                    return thumbnail

    def _fetch_musicvideo(self, request):
        if not xbmc.abortRequested:
            json_string = '{"jsonrpc": "2.0",  "id": 1, "method": "VideoLibrary.GetMusicVideos", "params": {"properties": ["title", "artist", "playcount", "year", "plot", "genre", "runtime", "fanart", "thumbnail", "file", "streamdetails"],  "limits": {"end": %d},' %self.LIMIT
            if request == 'RecommendedMusicVideo':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "playcount" }}}'  %json_string)
            elif request == 'RecentMusicVideo':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded"}}}'  %json_string)
            else:
                json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random"}}}' %json_string)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            if json_query['result'].has_key('musicvideos'):
                self._clear_properties(request)        
                count = 0
                for item in json_query['result']['musicvideos']:
                    count += 1
                    play = 'XBMC.RunScript(' + __addonid__ + ',musicvideoid=' + str(item.get('musicvideoid')) + ')'
                    path = media_path(item['file'])
                    streaminfo = media_streamdetails(item['file'].encode('utf-8').lower(),
                                                     item['streamdetails'])
                    # Temporary check if runtime is an int or str
                    if isinstance(item['runtime'],int):
                        runtime = str(item['runtime']/60)
                    else:
                        runtime = item['runtime']
                    self.WINDOW.setProperty("%s.%d.Title"           % (request, count), item['title'])
                    self.WINDOW.setProperty("%s.%d.Artist"          % (request, count), " / ".join(item['artist']))
                    self.WINDOW.setProperty("%s.%d.Year"            % (request, count), str(item['year']))
                    self.WINDOW.setProperty("%s.%d.Plot"            % (request, count), item['plot'])
                    self.WINDOW.setProperty("%s.%d.Genre"           % (request, count), " / ".join(item['genre']))
                    self.WINDOW.setProperty("%s.%d.Runtime"         % (request, count), runtime)
                    self.WINDOW.setProperty("%s.%d.Thumb"           % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"          % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"      % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)"     % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.File"            % (request, count), item['file'])
                    self.WINDOW.setProperty("%s.%d.Path"            % (request, count), path)
                    self.WINDOW.setProperty("%s.%d.Play"            % (request, count), play)
                    self.WINDOW.setProperty("%s.%d.VideoCodec"      % (request, count), streaminfo['videocodec'])
                    self.WINDOW.setProperty("%s.%d.VideoResolution" % (request, count), streaminfo['videoresolution'])
                    self.WINDOW.setProperty("%s.%d.VideoAspect"     % (request, count), streaminfo['videoaspect'])
                    self.WINDOW.setProperty("%s.%d.AudioCodec"      % (request, count), streaminfo['audiocodec'])
                    self.WINDOW.setProperty("%s.%d.AudioChannels"   % (request, count), str(streaminfo['audiochannels']))
            del json_query

    def _fetch_albums(self, request):
        if not xbmc.abortRequested:
            json_string = '{"jsonrpc": "2.0", "id": 1, "method": "AudioLibrary.GetAlbums", "params": {"properties": ["title", "description", "albumlabel", "artist", "genre", "year", "thumbnail", "fanart", "rating", "playcount"], "limits": {"end": %d},' %self.LIMIT
            if request == 'RecommendedAlbum':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "playcount" }}}' %json_string)
            elif request == 'RecentAlbum':
                json_query = xbmc.executeJSONRPC('%s "sort": {"order": "descending", "method": "dateadded" }}}' %json_string)
            else:
                json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random"}}}' %json_string)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            if json_query['result'].has_key('albums'):
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['albums']:
                    count += 1
                    rating = str(item['rating'])
                    if rating == '48':
                        rating = ''
                    play = 'XBMC.RunScript(' + __addonid__ + ',albumid=' + str(item.get('albumid')) + ')'
                    self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                    self.WINDOW.setProperty("%s.%d.Label"       % (request, count), item['title']) #needs to be removed
                    self.WINDOW.setProperty("%s.%d.Artist"      % (request, count), " / ".join(item['artist']))
                    self.WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                    self.WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                    self.WINDOW.setProperty("%s.%d.RecordLabel" % (request, count), item['albumlabel'])
                    self.WINDOW.setProperty("%s.%d.Description" % (request, count), item['description'])
                    self.WINDOW.setProperty("%s.%d.Rating"      % (request, count), rating)
                    self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.Play"        % (request, count), play)
            del json_query

    def _fetch_artist(self, request):
        if not xbmc.abortRequested:
            # Random artist
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "params": {"properties": ["genre", "description", "fanart", "thumbnail"], "sort": {"method": "random"}, "limits": {"end": %d}}, "id": 1}'  %self.LIMIT)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            if json_query['result'].has_key('artists'):
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['artists']:
                    count += 1
                    path = 'musicdb://2/' + str(item['artistid']) + '/'
                    self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['label'])
                    self.WINDOW.setProperty("%s.%d.Genre"       % (request, count), " / ".join(item['genre']))
                    self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.Description" % (request, count), item['description'])
                    self.WINDOW.setProperty("%s.%d.LibraryPath" % (request, count), path)

    def _fetch_song(self, request):
        if not xbmc.abortRequested:
            json_string = '{"jsonrpc": "2.0", "id": 1, "method": "AudioLibrary.GetSongs", "params": {"properties": ["title", "playcount", "artist", "album", "year", "file", "thumbnail", "fanart", "rating"], "filter": {"field": "playcount", "operator": "lessthan", "value": "1"}, "limits": {"end": %d},' %self.LIMIT
            if request == 'RandomSong' and self.RANDOMITEMS_UNPLAYED == "True":
                json_query = xbmc.executeJSONRPC('%s "sort": {"method": "random"}}}'  %json_string)
            else:
                json_query = xbmc.executeJSONRPC('%s  "sort": {"method": "random"}}}'  %json_string)
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            if json_query['result'].has_key('songs'):
                self._clear_properties(request)
                count = 0
                for item in json_query['result']['songs']:
                    count += 1
                    play = 'XBMC.RunScript(' + __addonid__ + ',songid=' + str(item.get('songid')) + ')'
                    path = media_path(item['file'])
                    self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['title'])
                    self.WINDOW.setProperty("%s.%d.Artist"      % (request, count), " / ".join(item['artist']))
                    self.WINDOW.setProperty("%s.%d.Year"        % (request, count), str(item['year']))
                    self.WINDOW.setProperty("%s.%d.Rating"      % (request, count), str(int(item['rating'])-48))
                    self.WINDOW.setProperty("%s.%d.Album"       % (request, count), item['album'])
                    self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.File"        % (request, count), item['file'])
                    self.WINDOW.setProperty("%s.%d.Path"        % (request, count), path)
                    self.WINDOW.setProperty("%s.%d.Play"        % (request, count), play)
            del json_query

    def _fetch_addon(self, request):
        if not xbmc.abortRequested:
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddons", "params": {"properties": ["name", "author", "summary", "version", "fanart", "thumbnail"]}, "id": 1}')
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = simplejson.loads(json_query)
            if json_query['result'].has_key('addons'):
                # find plugins and scripts
                addonlist = []
                for item in json_query['result']['addons']:
                    if item['type'] == 'xbmc.python.script' or item['type'] == 'xbmc.python.pluginsource':
                        addonlist.append(item)
                # randomize the list
                random.shuffle(addonlist)
                self._clear_properties(request)
                count = 0
                for item in addonlist:
                    count += 1
                    self.WINDOW.setProperty("%s.%d.Title"       % (request, count), item['name'])
                    self.WINDOW.setProperty("%s.%d.Author"      % (request, count), item['author'])
                    self.WINDOW.setProperty("%s.%d.Summary"     % (request, count), item['summary'])
                    self.WINDOW.setProperty("%s.%d.Version"     % (request, count), item['version'])
                    self.WINDOW.setProperty("%s.%d.Path"        % (request, count), item['addonid'])
                    self.WINDOW.setProperty("%s.%d.Thumb"       % (request, count), item['thumbnail']) #remove
                    self.WINDOW.setProperty("%s.%d.Fanart"      % (request, count), item['fanart']) #remove
                    self.WINDOW.setProperty("%s.%d.Art(thumb)"  % (request, count), item['thumbnail'])
                    self.WINDOW.setProperty("%s.%d.Art(fanart)" % (request, count), item['fanart'])
                    self.WINDOW.setProperty("%s.%d.Type"        % (request, count), item['type'])
                    # stop if we've reached the number of items we need
                    if count == self.LIMIT:
                        break
                self.WINDOW.setProperty("%s.Count" % (request), str(json_query['result']['limits']['total']))
            del json_query

    def _daemon(self):
        # deamon is meant to keep script running at all time
        count = 0
        home_update = False
        while (not xbmc.abortRequested) and self.WINDOW.getProperty('SkinWidgets_Running') == 'true':
            xbmc.sleep(1000)
            if self.RANDOMITEMS_UPDATE_METHOD == 0:
                count += 1
                if count == self.RANDOMITEMS_TIME:
                    #self._fetch_info_randomitems()
                    count = 0    # reset counter
            if self.WINDOW.getProperty('SkinWidgets_RandomItems_Update') == 'true':
                count = 0
                self.WINDOW.setProperty('SkinWidgets_RandomItems_Update','false')
                #self._fetch_info_randomitems()
            if  self.RECENTITEMS_HOME_UPDATE == 'true' and home_update and xbmcgui.getCurrentWindowId() == 10000:
                self._fetch_info_recentitems()
                home_update = False
            elif self.RECENTITEMS_HOME_UPDATE == 'true' and not home_update and xbmcgui.getCurrentWindowId() != 10000:
                home_update = True
            if  self.INPROGRESSITEMS_HOME_UPDATE == 'true' and home_update and xbmcgui.getCurrentWindowId() == 10000:
                log('updating through deamon')
                self._fetch_info_inprogress()
                home_update = False
            elif self.INPROGRESSITEMS_HOME_UPDATE == 'true' and not home_update and xbmcgui.getCurrentWindowId() != 10000:
                home_update = True

    def _clear_properties(self, request):
        count = 0
        for count in range(int(self.LIMIT)):
            count += 1
            self.WINDOW.clearProperty("%s.%d.Title" % (request, count))
            self.WINDOW.clearProperty("%s.%d.Type" % (request, count))

    def _update(self, type):
        xbmc.sleep(1000)
        if type == 'movie':
            #self._fetch_movies('RecommendedMovie')
            self._fetch_movies('RecentMovie')
        elif type == 'episode':
            #self._fetch_tvshows_recommended('RecommendedEpisode')
            self._fetch_tvshows('RecentEpisode')
        elif type == 'video':
            #only on db update
            #self._fetch_movies('RecommendedMovie')
            #self._fetch_tvshows_recommended('RecommendedEpisode')
            self._fetch_movies('RecentMovie')
            self._fetch_tvshows('RecentEpisode')
            #self._fetch_musicvideo('RecentMusicVideo')
        elif type == 'music':
            #self._fetch_albums('RecommendedAlbum')
            #self._fetch_albums('RecentAlbum')
            pass
        if self.RANDOMITEMS_UPDATE_METHOD == 1:
            # update random if db update is selected instead of timer
            if type == 'video':
                #self._fetch_movies('RandomMovie')
                #self._fetch_tvshows('RandomEpisode')
                #self._fetch_musicvideo('RandomMusicVideo')
                pass
            elif type == 'music':
                #self._fetch_albums('RandomAlbum')
                #self._fetch_artist('RandomArtist')
                #self._fetch_song('RandomSong')
                #self._fetch_addon('RandomAddon')
                pass

    def _seconds_to_string( self, time, format ):
        timestr = ''
        hh = mm = ss = 0
        try:
          if time > 0.0:
              hh = int(time / 3600)
              time = time % 3600
              mm = int(time / 60)
              ss = int(time % 60)
              log('time = %f, hh = %d, mm = %d, ss = %d' % (time,hh,mm,ss))
          if format == 'long':
              if hh == 1:
                  #timestr = ('%d ' + str(self.__language__(90001))) % hh
                  timestr = ('%d ' + 'hour') % hh
              if hh > 1:
                  timestr = ('%d ' + 'hours') % hh
              if mm > 0:
                  if mm == 1:
                      timestr = timestr + ((' %d ' + 'minute') % mm)
                  else:
                      timestr = timestr + ((' %d ' + 'minutes') % mm)
              if hh == 0 and mm == 0:
                  timestr = '0 ' + 'minutes'
              timestr = timestr + ' ' + 'left'
          if format == 'short':
              strm = ''
              if hh > 0:
                  timestr = '%dh' % hh
                  strm = ' '
              if mm > 0:
                  timestr = timestr + strm + ('%02dmin' % mm)
              if hh == 0 and mm == 0:
                  timestr = '0min'
        except:
          timestr = 'why here?'
  
        return timestr


def media_path(path):
    # Check for stacked movies
    try:
        path = os.path.split(path)[0].rsplit(' , ', 1)[1].replace(",,",",")
    except:
        path = os.path.split(path)[0]
    # Fixes problems with rared movies and multipath
    if path.startswith("rar://"):
        path = [os.path.split(urllib.url2pathname(path.replace("rar://","")))[0]]
    elif path.startswith("multipath://"):
        temp_path = path.replace("multipath://","").split('%2f/')
        path = []
        for item in temp_path:
            path.append(urllib.url2pathname(item))
    else:
        path = [path]
    return path[0]

def media_streamdetails(filename, streamdetails):
    info = {}
    video = streamdetails['video']
    audio = streamdetails['audio']
    if '3d' in filename:
        info['videoresolution'] = '3d'
    elif video:
        videowidth = video[0]['width']
        videoheight = video[0]['height']
        if (video[0]['width'] <= 720 and video[0]['height'] <= 480):
            info['videoresolution'] = "480"
        elif (video[0]['width'] <= 768 and video[0]['height'] <= 576):
            info['videoresolution'] = "576"
        elif (video[0]['width'] <= 960 and video[0]['height'] <= 544):
            info['videoresolution'] = "540"
        elif (video[0]['width'] <= 1280 and video[0]['height'] <= 720):
            info['videoresolution'] = "720"
        else:
            info['videoresolution'] = "1080"
    elif (('dvd') in filename and not ('hddvd' or 'hd-dvd') in filename) or (filename.endswith('.vob' or '.ifo')):
        info['videoresolution'] = '576'
    elif (('bluray' or 'blu-ray' or 'brrip' or 'bdrip' or 'hddvd' or 'hd-dvd') in filename):
        info['videoresolution'] = '1080'
    else:
        info['videoresolution'] = '1080'
    if video:
        info['videocodec'] = video[0]['codec']
        if (video[0]['aspect'] < 1.4859):
            info['videoaspect'] = "1.33"
        elif (video[0]['aspect'] < 1.7190):
            info['videoaspect'] = "1.66"
        elif (video[0]['aspect'] < 1.8147):
            info['videoaspect'] = "1.78"
        elif (video[0]['aspect'] < 2.0174):
            info['videoaspect'] = "1.85"
        elif (video[0]['aspect'] < 2.2738):
            info['videoaspect'] = "2.20"
        else:
            info['videoaspect'] = "2.35"
    else:
        info['videocodec'] = ''
        info['videoaspect'] = ''
    if audio:
        info['audiocodec'] = audio[0]['codec']
        info['audiochannels'] = audio[0]['channels']
    else:
        info['audiocodec'] = ''
        info['audiochannels'] = ''
    return info

    
class Widgets_Monitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.update_listitems = kwargs['update_listitems']
        self.update_settings = kwargs['update_settings']

    def onDatabaseUpdated(self, database):
        self.update_listitems(database)
        
    def onSettingsChanged(self):
        self.update_settings()

class Widgets_Player(xbmc.Player):
    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)
        self.type = ""
        self.action = kwargs[ "action" ]
        self.substrings = [ '-trailer', 'http://' ]

    def onPlayBackStarted(self):
        xbmc.sleep(1000)
        # Set values based on the file content
        if (self.isPlayingAudio()):
            self.type = "music"  
        else:
            if xbmc.getCondVisibility('VideoPlayer.Content(movies)'):
                filename = ''
                isMovie = True
                try:
                    filename = self.getPlayingFile()
                except:
                    pass
                if filename != '':
                    for string in self.substrings:
                        if string in filename:
                            isMovie = False
                            break
                if isMovie:
                    self.type = "movie"
            elif xbmc.getCondVisibility('VideoPlayer.Content(episodes)'):
                # Check for tv show title and season to make sure it's really an episode
                if xbmc.getInfoLabel('VideoPlayer.Season') != "" and xbmc.getInfoLabel('VideoPlayer.TVShowTitle') != "":
                    self.type = "episode"

    def onPlayBackEnded(self):
        self.onPlayBackStopped()

    def onPlayBackStopped(self):
        if self.type == 'movie':
            self.action('movie')
        elif self.type == 'episode':
            self.action('episode')
        elif self.type == 'music':
            self.action('music')
        self.type = ""

if (__name__ == "__main__"):
    log('script version %s started' % __addonversion__)
    Main()
    del Widgets_Monitor
    del Widgets_Player
    del Main
    log('script version %s stopped' % __addonversion__)
