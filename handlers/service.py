#!/usr/bin/python2.5
#
# Copyright 2009 Roman Nurik
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Service /s/* request handlers."""

__author__ = 'api.roman.public@gmail.com (Roman Nurik)'

import os
import sys
import wsgiref.handlers
from xml.dom import minidom

from django.utils import simplejson
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api import urlfetch


from geo import geotypes

from models import PublicSchool
from models import Game

#for evernote API
import sys
import hashlib
import binascii
import time
from time import strftime
#import pytz
import datetime
import csv
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.notestore.ttypes as NoteStoreTypes
import evernote.edam.error.ttypes as Errors

OAS_API_URL = "http://api.openapiservice.com/v1.0/location/getLocation?appkey=4214ca98ac65a0daf814002a&phoneNumber="
OAS_API_URL_1 = "&requestedAccuracy=20000&acceptableAccuracy=65000&maximumAge=80000&responseTime=100000&tolerance=DELAY_TOLERANT"
LBS_API_NS = "http://service.las.alu.com/xsd"

username = "lucaswestine"
password = "StanFord7"

import gdata.calendar.calendarExample

#
# NOTE: You must change the consumer key and consumer secret to the 
#       key and secret that you received from Evernote
#
consumerKey = "westine"
consumerSecret = "277e8b3a8cc49b2d"

evernoteHost = "www.evernote.com" #this is production service
userStoreUri = "https://" + evernoteHost + "/edam/user"
noteStoreUriBase = "https://" + evernoteHost + "/edam/note/"

userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
userStore = UserStore.Client(userStoreProtocol)

versionOK = userStore.checkVersion("Python EDAMTest",
                                   UserStoreConstants.EDAM_VERSION_MAJOR,
                                   UserStoreConstants.EDAM_VERSION_MINOR)

class getDone(webapp.RequestHandler):
    def _simple_error(message, code=400):
      self.error(code)
      self.response.out.write(simplejson.dumps({
        'status': 'error',
        'error': { 'message': message },
        'results': []
      }))
      return None
    def get(self):   
        try :
            authResult = userStore.authenticate(username, password,
                                                consumerKey, consumerSecret)
        except Errors.EDAMUserException,e:
            # See http://www.evernote.com/about/developer/api/ref/UserStore.html#Fn_UserStore_authenticate
            parameter = e.parameter
            errorCode = e.errorCode
            errorText = Errors.EDAMErrorCode._VALUES_TO_NAMES[errorCode]
            return _simple_error(errorText, code=500)
        try:               
            user = authResult.user
            authToken = authResult.authenticationToken
            noteStoreUri =  noteStoreUriBase + user.shardId
            noteStoreHttpClient = THttpClient.THttpClient(noteStoreUri)
            noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
            noteStore = NoteStore.Client(noteStoreProtocol)
            notebooks = noteStore.listNotebooks(authToken)
            results = [] 
            for notebook in notebooks:          
                if notebook.defaultNotebook:
                    defaultNotebook = notebook
                filter = NoteStoreTypes.NoteFilter()
                filter.notebookGuid = notebook.guid
                filter.order = 1
                if self.request.get('type') == 'Todo':
                    filter.words = "any: todo:false"
                else:
                    filter.words = "any: todo:true"     
                filter.ascending = False
               # filter.timeZone = "Asia/Shanghai"
                noteList = noteStore.findNotes(authToken, filter, 0, 51)
                results = noteList.notes + results            
            self.response.headers['Content-Type'] = 'application/json'
            results_obj = [
              _merge_dicts({
                'title': result.title,
                'created': result.created / 1000,
                },
                )
              for result in results]
            #print self.request.get('type')
            
            self.response.out.write(simplejson.dumps({
            'status': 'success',
            'results': results_obj
              }))
        except:
            return _simple_error(str(sys.exc_info()[1]), code=500)
         
class getTodo(webapp.RequestHandler):
    """
    Just test the call
    """
    def _simple_error(message, code=400):
      self.error(code)
      self.response.out.write(simplejson.dumps({
        'status': 'error',
        'error': { 'message': message },
        'results': []
      }))
      return None
    def get(self):     
      # Authenticate the user
        try :
            authResult = userStore.authenticate(username, password,
                                                consumerKey, consumerSecret)
        except Errors.EDAMUserException,e:
            # See http://www.evernote.com/about/developer/api/ref/UserStore.html#Fn_UserStore_authenticate
            parameter = e.parameter
            errorCode = e.errorCode
            errorText = Errors.EDAMErrorCode._VALUES_TO_NAMES[errorCode]
            return _simple_error(errorText, code=500)
            #print "Authentication failed (parameter: " + parameter + " errorCode: " + errorText + ")"
            
#            if errorCode == Errors.EDAMErrorCode.INVALID_AUTH:
#                if parameter == "consumerKey":
#                    if consumerKey == "en-edamtest":
#                        #print "You must replace the variables consumerKey and consumerSecret with the values you received from Evernote."
#                    #else:
#                        #print "Your consumer key was not accepted by", evernoteHost
#                        #print "This sample client application requires a client API key. If you requested a web service API key, you must authenticate using OAuth."
#                    #print "If you do not have an API Key from Evernote, you can request one from http://www.evernote.com/about/developer/api"
#                elif parameter == "username":
#                    #print "You must authenticate using a username and password from", evernoteHost
#                    if evernoteHost != "www.evernote.com":
#                        #print "Note that your production Evernote account will not work on", evernoteHost
#                        #print "You must register for a separate test account at https://" + evernoteHost + "/Registration.action"
#                elif parameter == "password":
#                    print "The password that you entered is incorrect"
        
            #print ""
           # exit(1)
        try:  
            user = authResult.user
            authToken = authResult.authenticationToken
            noteStoreUri =  noteStoreUriBase + user.shardId
            noteStoreHttpClient = THttpClient.THttpClient(noteStoreUri)
            noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
            noteStore = NoteStore.Client(noteStoreProtocol)
    
            notebooks = noteStore.listNotebooks(authToken)
            results = []
            for notebook in notebooks:
                #print "  * ", notebook.name
                
                if notebook.defaultNotebook:
                    defaultNotebook = notebook
              #  else :
              #      continue
                filter = NoteStoreTypes.NoteFilter()
                filter.notebookGuid = notebook.guid
                filter.order = 1
                filter.words = "any: tag:todo todo:*" 
                filter.ascending = False
               # filter.timeZone = "Asia/Shanghai"
                noteList = noteStore.findNotes(authToken, filter, 0, 51)
                results = noteList.notes + results
             
            
            self.response.headers['Content-Type'] = 'application/json'
            results_obj = [
              _merge_dicts({
                'title': result.title,
                'created': time.asctime(time.localtime(result.created / 1000)),
                },
                )
              for result in results]
            #for song in results:
            #print song.type
      #     for result in query:
      #                  resultsobj.push( "Title: " + result.address
            self.response.out.write(simplejson.dumps({
            'status': 'success',
            'results': results_obj
              }))
        except:
            return _simple_error(str(sys.exc_info()[1]), code=500)
# @end snippet

def _merge_dicts(*args):
  """Merges dictionaries right to left. Has side effects for each argument."""
  return reduce(lambda d, s: d.update(s) or d, args)
  	
def unicode_str(s):
  return s.decode('utf8', 'ignore')
  	
# @start snippet
def xml_response(handler, page, templatevalues=None):
    """
    Renders an XML response using a provided template page and values
    """
    path = os.path.join(os.path.dirname(__file__), page)
    handler.response.headers["Content-Type"] = "text/xml"
    handler.response.out.write(template.render(path, templatevalues))

class SaveService(webapp.RequestHandler):
    """
    Just test the call
    """
 
      
    def get(self):
        self.post()
    
    def post(self):
    	  
        self.response.headers['Content-Type'] = 'application/json';
        game_entity = Game()
        
       # print float(self.request.get("latitude"))
        game_entity.location = db.GeoPt(float(self.request.get("latitude")),float(self.request.get("longitude")))
        game_entity.name = unicode_str(self.request.get("name"))
        game_entity.game_type = int(self.request.get('type'))
       # game_entity.address = unicode_str(self.request.get('address'))
      #  print self.request.get('address')
      #  game_entity.game_id = self.request.get('id')
        game_entity.update_location()
        game_entity.put()
        
        self.response.out.write(simplejson.dumps({
        "status": "success",
        "name": self.request.get("name"),
        "type": int(self.request.get('type')),
        "latitude":game_entity.location.lat,
        "longitude": game_entity.location.lon,	
        #"address": game_entity.address,
        "savedSuccess":game_entity.is_saved(),
      }))
       #xml_response(self, 'call.xml')
# @end snippet

class ShowAll(webapp.RequestHandler):
    """
    Just test the call
    """
    def get(self):     
      # Can't provide an ordering here in case inequality filters are used.      
       base_query = Game.all()
       count = base_query.count()
       
       results = base_query.fetch(count)
       #db.delete(results)
   #    for game in results:
    #   	 		resultsobj = resultsobj + simplejson.dumps({"latitude":game.location.lat,"longitude":game.location.lon,"name":game.name,"type":game.game_type})
    #   objs = simplejson.dumps(resultsobj)
       
       public_attrs = Game.public_attributes()
      
       results_obj = [
          _merge_dicts({
            'lat': result.location.lat,
            'lng': result.location.lon,
            },
            dict([(attr, getattr(result, attr))
                  for attr in public_attrs]))
          for result in results]
		#for song in results:
    	#print song.type
  #     for result in query:
  # 				 resultsobj.push( "Title: " + result.address
       self.response.out.write(simplejson.dumps({
       'status': 'success',
       'count': count,
       'results': results_obj
     	}))
# @end snippet

#this class provide OAS LBS service
class SubscribeLBS(webapp.RequestHandler):
    """
    OAS LBS
    """
    def get(self):
        self.post()
        
    def _fetch(self, phonenumber):	
    	  
        url = OAS_API_URL + phonenumber + OAS_API_URL_1;
        print url
        result = urlfetch.fetch(url)
        if result.status_code != 200:
            return None
        return result.content
        
    def post(self):
        print "asdfdskfsdfdsfdfffff"
        phonenumber = self.request.get('phone_number');
        lbsxml = self._fetch(phonenumber)
        dom = minidom.parseString(lbsxml)
        
        domDoc = dom.documentElement;
        latElement = domDoc.getElementsByTagName('ns:latitude')
        lntElement = domDoc.getElementsByTagName('ns:longitude')
        latValue = latElement[0].firstChild.nodeValue;
        lntValue = lntElement[0].firstChild.nodeValue;
        
        try:
            self.response.out.write(simplejson.dumps({"status": "success","latitude": latValue,"longitude":lntValue}))
        except:
            self._error("Error parsing weather. Good Bye.")
# @end snippet

class SearchService(webapp.RequestHandler):
  """Handler for search requests."""
  def get(self):
    def _simple_error(message, code=400):
      self.error(code)
      self.response.out.write(simplejson.dumps({
        'status': 'error',
        'error': { 'message': message },
        'results': []
      }))
      return None
      
    
    self.response.headers['Content-Type'] = 'application/json'
    query_type = self.request.get('type')
   
    
    if not query_type in ['proximity', 'bounds']:
      return _simple_error('type parameter must be '
                           'one of "proximity", "bounds".',
                           code=400)
    
    if query_type == 'proximity':
      try:
        center = geotypes.Point(float(self.request.get('lat')),
                                float(self.request.get('lon')))
      except ValueError:
        return _simple_error('lat and lon parameters must be valid latitude '
                             'and longitude values.')
    elif query_type == 'bounds':
      try:
        bounds = geotypes.Box(float(self.request.get('north')),
                              float(self.request.get('east')),
                              float(self.request.get('south')),
                              float(self.request.get('west')))
      except ValueError:
        return _simple_error('north, south, east, and west parameters must be '
                             'valid latitude/longitude values.')
    
    max_results = 100
    if self.request.get('maxresults'):
      max_results = int(self.request.get('maxresults'))
    
    max_distance = 80000 # 80 km ~ 50 mi
    if self.request.get('maxdistance'):
      max_distance = float(self.request.get('maxdistance'))

    game_type = None
    if self.request.get('gametype'):
      try:
        school_type = int(self.request.get('type'))
      except ValueError:
        return _simple_error('If gametype is provided, '
                             'it must be a valid number, as defined in '
                             'http://nces.ed.gov/ccd/psadd.asp#type')

    grade_range = None
    if self.request.get('mingrade') or self.request.get('maxgrade'):
      try:
        grade_range = (int(self.request.get('mingrade')),
                       int(self.request.get('maxgrade')))
        if grade_range[0] > grade_range[1]:
          return _simple_error('mingrade cannot exceed maxgrade.')
      except ValueError:
        return _simple_error('If mingrade or maxgrade is provided, '
                             'both must be valid integers.')
      
    try:
      # Can't provide an ordering here in case inequality filters are used.
      base_query = Game.all()

     
      
      if game_type:
        base_query.filter('game_type =', game_type)
      
      # Perform proximity or bounds fetch.
      if query_type == 'proximity':
        results = Game.proximity_fetch(
            base_query,
            center, max_results=max_results, max_distance=max_distance)
      elif query_type == 'bounds':
        results = Game.bounding_box_fetch(
            base_query,
            bounds, max_results=max_results)
      
      public_attrs = Game.public_attributes()
      
      results_obj = [
          _merge_dicts({
            'lat': result.location.lat,
            'lng': result.location.lon,
            },
            dict([(attr, getattr(result, attr))
                  for attr in public_attrs]))
          for result in results]

      self.response.out.write(simplejson.dumps({
        'status': 'success',
        'results': results_obj
      }))
    except:
      return _simple_error(str(sys.exc_info()[1]), code=500)


def main():
  application = webapp.WSGIApplication([
      ('/s/search', SearchService),
      ('/s/save', SaveService),
      ('/s/showall', ShowAll),
      ('/s/lbs', SubscribeLBS),
      ('/s/getTodo', getTodo),
      ('/s/getDone', getDone)
      ],
      debug=('Development' in os.environ['SERVER_SOFTWARE']))
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
