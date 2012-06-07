/*
Copyright 2009 Roman Nurik

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

/**
 * This function is triggered by the login/logout button.
 * If the user is logged in to the app, it logs them out.
 * If the user is logged out to the app, it logs them in.
 */
function loginOrLogout(){
  var token = google.accounts.user.checkLogin(EVENT_FEED_URL);
  if (token) {
    google.accounts.user.logout();
    init();
  } else {
    google.accounts.user.login(EVENT_FEED_URL);
  }
}
 
/**
 * Retrieves birthday reminders in the next 2 months,
 * and calls handleEventsFeed for the results.
 */
function getEvents() {
  var eventQuery = new google.gdata.calendar.CalendarEventQuery(EVENT_FEED_URL);
 
  // set minimum start time as today
  var today = new Date();
  var startTimeMin = new google.gdata.DateTime(today, true);
  eventQuery.setMinimumStartTime(google.gdata.DateTime.toIso8601(startTimeMin));
 
  // set maximum start time as 2 months from now
  var twoMonthsLater = new Date();
  var month = (today.getMonth() + 2) % 11;
  twoMonthsLater.setMonth(month);
  var startTimeMax = new google.gdata.DateTime(twoMonthsLater, true);
  eventQuery.setMaximumStartTime(google.gdata.DateTime.toIso8601(startTimeMax));
 
  eventQuery.setSortOrder('ascending');
  eventQuery.setSingleEvents(true);
  calendarService.getEventsFeed(eventQuery, handleEventsFeed, handleError);
}
 
 
/**
 * This function is called after the events query returns.
 * It parses through the entries, checking for Birthday Reminders.
 * It grabs the necessary information from the extended properties,
 * and displays each event in a table row.
 * @param {google.gdata.CalendarFeed} resultsFeedRoot The events feed
 */
function handleEventsFeed(resultsFeedRoot) {
  var eventList = document.getElementById('upcomingBirthdaysContent');
  eventList.innerHTML = '';
 
  eventsFeed = resultsFeedRoot.feed;
  events = eventsFeed.getEntries();
  var upcomingBirthdaysTable = document.createElement('table');
  var upcomingBirthdaysTbody = document.createElement('tbody');
  for (var i = 0; i < events.length; i++) {
    var eventTitle = events[i].getTitle().getText();
    if (eventTitle.match('Birthday Reminder')) {
      var eventRow = document.createElement('tr');
 
      var eventExtProperties = events[i].getExtendedProperties();
      var eventExtPropertiesHash = getExtPropertiesHash(eventExtProperties);
      var name = eventExtPropertiesHash.name;
      var image = eventExtPropertiesHash.image;
      var profile = eventExtPropertiesHash.profile;
      var birthmonth = eventExtPropertiesHash.birthmonth;
      var birthday = eventExtPropertiesHash.birthday;
 
      var nameCell = document.createElement('td');
      nameCell.appendChild(document.createTextNode(name));
      var dateCell = document.createElement('td');
      dateCell.appendChild(document.createTextNode(birthmonth + 
          '/' + birthday));
      var imgCell = document.createElement('td');
      var img = document.createElement('img');
      img.setAttribute('src', image);
      img.setAttribute('width', '30');
      img.setAttribute('height', '40');
      img.style.border = '1px solid #ff0000';
      imgCell.appendChild(img);
      var profileCell = document.createElement('td');
      var profileLink = document.createElement('a');
      profileLink.setAttribute('href', profile);
      profileLink.appendChild(document.createTextNode('Visit profile.'));
      profileCell.appendChild(profileLink);
      
      eventRow.appendChild(imgCell);
      eventRow.appendChild(nameCell);
      eventRow.appendChild(dateCell);
      eventRow.appendChild(profileCell);
      upcomingBirthdaysTbody.appendChild(eventRow);
    }
  }
  upcomingBirthdaysTable.appendChild(upcomingBirthdaysTbody);
  upcomingBirthdaysContent.appendChild(upcomingBirthdaysTable);
}
 
/**
 * Utility function for converting extended properties array
 *  into a hash function so it's easy to access named properties.
 *  @param {Array} extPropertiesArray Array of extended properties
 *  @return {Object} Hash of extended properties
 */
function getExtPropertiesHash(extPropertiesArray) {
  var extPropertiesHash = {};
  for (var i = 0; i < extPropertiesArray.length; i++) {
   var extProperty = extPropertiesArray[i];
   extPropertiesHash[extProperty.name] =extProperty.value;
  }
  return extPropertiesHash;
}
 
/**
 * Adds birthday reminder event to calendar, based on form.
 */
function saveEvent() {
  // Get values from form
  var birthdateINPUT = document.getElementById('birthdate').value;
  var birthdateInputSplit = birthdateINPUT.split('/');
  if (birthdateInputSplit.length < 3) {
    alert('Birthdate should be in M/D/YYYY format, e.g. 6/24/1984.');
    return;
  }
  var birthday = birthdateInputSplit[1];
  var birthmonth = birthdateInputSplit[0];
  var birthyear = birthdateInputSplit[2];
  var name = document.getElementById('name').value;
  var image = document.getElementById('image').value;
  var profile = document.getElementById('profile').value;
  var inputs = { 'name': name, 'birthmonth': birthmonth, 
      'birthday': birthday, 'birthyear': birthyear, 'image': image, 
       'profile': profile};
 
  // Create event
  var event = new google.gdata.calendar.CalendarEventEntry();
 
  // Add title - this will be shown in agenda view, so it should be useful
  event.setTitle(google.gdata.atom.Text.create('Birthday Reminder for ' + name));
 
  // Add recurrence - birthday reminders should be repeated annually
  var today = new Date();
  var formattedStart =  today.getFullYear() + '' + formatNumber(birthmonth) + 
      '' + formatNumber(birthday);
  var recurrence = new google.gdata.Recurrence();
 
  // The recurrence value is in ICAL format. More info available here:
  // http://code.google.com/apis/calendar/developers_guide_protocol.html#CreatingRecurring
  recurrence.setValue('DTSTART;VALUE=DATE:' + formattedStart
       + 'DTEND;VALUE=DATE:' + formattedStart
       + '\r\nRRULE:FREQ=YEARLY;WKST=SU');
  event.setRecurrence(recurrence);
 
  // Add reminders - we have 3 checkboxes in the form.
  // Each number represents number of days. 
  // To add different options, change this array and checkbox HTML.
  // Options need to match options available in the calendar UI.
  var reminderDays = ['1', '2', '7'];
 
  for (var i = 0; i < reminderDays.length; i++) {
    if (document.getElementById('reminder_days' + reminderDays[i]).checked) {
      event.addReminder({days: reminderDays[i], method: google.gdata.Reminder.METHOD_EMAIL});
    }
  }
 
  // Add (empty) content
  event.setContent(google.gdata.atom.Text.create(''));
 
  // Add web content - this will place an icon on the calendar
  //  that opens a calendar gadget when clicked. 
  //  We set user preferences so the gadget knows the 
  //  name, birthday, and image to display.
  var webContent = new google.gdata.calendar.WebContent();
  webContent.setHeight(240);
  webContent.setWidth(280);
  webContent.setUrl('http://gdata-javascript-client.googlecode.com/svn/trunk/samples/calendar/birthday_manager/birthday_manager_gadget.xml');
  for (input in inputs) {
    var gadgetPref = new google.gdata.calendar.WebContentGadgetPref();
    gadgetPref.setName(input);
    gadgetPref.setValue(inputs[input]);
    webContent.addGadgetPref(gadgetPref);
  }
 
  var calendarLink = new google.gdata.calendar.CalendarLink();
  calendarLink.setWebContent(webContent);
  calendarLink.setRel('http://schemas.google.com/gCal/2005/webContent');
  calendarLink.setHref(
      'http://gdata-javascript-client.googlecode.com/svn/trunk/samples/calendar/birthday_manager/images/fingerreminder_favicon.png');
  calendarLink.setTitle('Birthday Reminder for ' + name);
  calendarLink.setType('application/x-google-gadgets+xml');
  
  event.setWebContentLink(calendarLink);
  
  // Add extended properties - This is a structured way 
  //  of storing additional information in a calendar entry. 
  //  They won't show up in the UI, but it will show up in the feed.
  for (input in inputs) {
    var extendedProperty = new google.gdata.ExtendedProperty();
    extendedProperty.setName(input);
    extendedProperty.setValue(inputs[input]);
    event.addExtendedProperty(extendedProperty);
  }
 
  // Insert entry into the default calendar for this service
  calendarService.insertEntry(EVENT_FEED_URL, event, entryCreated, handleError);
};
 
/**
 * Utility function to format numbers so that
 *  single digits have a 0 in front.
 */
function formatNumber(num) {
  if (num.length == 1) {
    return '0' + num;
  }
  return num;
}
 
/**
 * This function is called when event is added.
 * It updates the upcoming birthdays table.
 * @param {google.gdata.calendar.CalendarEntry} entryRoot
 */
function entryCreated(entryRoot) {
  alert('Successfully added to calendar.');
  //getEvents();
};
 
 
/**
 * This function is called if an error is encountered
 *  while retrieving a feed or adding an event.
 */
function handleError(e) {
  alert(e.cause ? e.cause.statusText : e.message);
};
 
/** 
 * This function is filled on page load,
 *  and fills the form with values from the URL.
 * This makes it easy to work with greasemonkey script.
 */
function fillFormFromURL() {
  var name = unescape(getURLParam('name'));
  var birthdate = unescape(getURLParam('birthdate')); 
  var image = unescape(getURLParam('image'));
  var profile = unescape(getURLParam('profile'));
  
  document.getElementById('name').value = name;
  document.getElementById('birthdate').value = birthdate;
  document.getElementById('image').value = image;
  document.getElementById('profile').value = profile;
  refreshImage();
}
 
/**
 * This function updates the image based on the 
 *  new image url in the form. 
 */
function refreshImage() {
  document.getElementById('imagePreview').innerHTML = '';
  var image = document.getElementById('image').value;
  if (image != '') {
    var img = document.createElement('img');
    img.setAttribute('src', image);
    document.getElementById('imagePreview').appendChild(img);
  }
}
 
/**
* Utility function to extract parameters appended to URL.
* @param {String} name Name of parameter in URL
* @return {String} Value of parameter, or '' if not found
*/
function getURLParam(name) {
  var regexS = '[\\?&]' + name + '=([^&#]*)';
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.href);
  return (results === null ? '' : results[1]);
}

/*
 * Add a reminder to event
 */ 

// Create the calendar service object
var calendarService = new google.gdata.calendar.CalendarService('GoogleInc-jsguide-1.0');

// The default "private/full" feed is used to insert event to the 
// primary calendar of the authenticated user
var feedUri = 'http://www.google.com/calendar/feeds/default/private/full';

// Create an instance of CalendarEventEntry representing the new event
var entry = new google.gdata.calendar.CalendarEventEntry();

// Set the title of the event
entry.setTitle(google.gdata.Text.create('JS-Client: add event reminder'));

// Create a When object that will be attached to the event
var when = new google.gdata.When();

// Set the start and end time of the When object
var startTime = google.gdata.DateTime.fromIso8601("2008-02-10T09:00:00.000-08:00");
var endTime = google.gdata.DateTime.fromIso8601("2008-02-10T10:00:00.000-08:00")
when.setStartTime(startTime);
when.setEndTime(endTime);

// Create a Reminder object that will be attached to the When object
var reminder = new google.gdata.Reminder();

// Set the reminder to be 30 minutes prior the event start time
reminder.setMinutes(30);

// Set the reminder method to be 'alert', a pop up alert on the browser
reminder.setMethod(google.gdata.Reminder.METHOD_ALERT);

// Add the reminder with the When object
when.addReminder(reminder);

// Add the When object to the event 
entry.addTime(when);

// The callback method that will be called after a successful insertion from insertEntry()
var callback = function(result) {
  PRINT('event created with reminder!');
}

// Error handler will be invoked if there is an error from insertEntry()
var handleError = function(error) {
  PRINT(error);
}

// Submit the request using the calendar service object
calendarService.insertEntry(feedUri, entry, callback, 
    handleError, google.gdata.calendar.CalendarEventEntry);
