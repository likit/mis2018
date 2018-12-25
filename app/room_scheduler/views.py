# -*- coding: utf8 -*-

from . import roombp as room
from .models import RoomResource
from flask import render_template, jsonify, request, flash, redirect, url_for
from datetime import datetime
import pytz

import google.auth
import dateutil.parser
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from ..main import json_keyfile


@room.route('/api/rooms')
def get_rooms():
    rooms = RoomResource.query.all()
    resources = []
    for rm in rooms:
        resources.append({
            'id': rm.number,
            'location': rm.location,
            'title': rm.number,
            'occupancy': rm.occupancy,
            'businessHours': {
                'start': rm.business_hour_start.strftime('%H:%M'),
                'end': rm.business_hour_end.strftime('%H:%M'),
            }
        })
    return jsonify(resources)


@room.route('/api/events')
def get_events():
    tz = pytz.timezone('Asia/Bangkok')
    credentials, project_id = google.auth.default()
    scoped_credentials = credentials.with_scopes([
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ])
    calendar_service = build('calendar', 'v3', credentials=scoped_credentials)
    request = calendar_service.events().list(calendarId='9hur49up24fdcbicdbggvpu77k@group.calendar.google.com')
    # Loop until all pages have been processed.
    all_events = []
    while request != None:
        # Get the next page.
        response = request.execute()
        # returns a list of item objects (events).
        for event in response.get('items', []):
            # The event object is a dict object with a 'summary' key.
            start = event.get('start', None)
            end = event.get('end', None)
            extended_properties = event.get('extendedProperties', {}).get('private', {})
            room_no = extended_properties.get('room_no', '736')
            evt = {
                'location': event.get('location', None),
                'title': event.get('summary', 'NO SUMMARY'),
                'description': event.get('description', ''),
                'start': start['dateTime'],
                'end': end['dateTime'],
                'resourceId': room_no,
            }
            all_events.append(evt)
        # Get the next request object by passing the previous request object to
        # the list_next method.
        request = calendar_service.events().list_next(request, response)
    return jsonify(all_events)


@room.route('/')
def index():
    return render_template('scheduler/room_main.html')


@room.route('/events/<list_type>')
def event_list(list_type='timelineDay'):
    return render_template('scheduler/event_list.html', list_type=list_type)


@room.route('/events/new')
def new_event():
    return render_template('scheduler/new_event.html')


@room.route('/list', methods=['POST', 'GET'])
def room_list():
    if request.method=='GET':
        rooms = RoomResource.query.all()
    else:
        room_number = request.form.get('room_number', None)
        users = request.form.get('users', 0)
        if room_number:
            rooms = RoomResource.query.filter_by(number=room_number)
        elif users > 0:
            rooms = RoomResource.query.filter(RoomResource.occupancy>=users)
        else:
            rooms = []

    return render_template('scheduler/room_list.html', rooms=rooms)


@room.route('/reserve/<room_no>', methods=['GET', 'POST'])
def room_reserve(room_no):
    if request.method=='POST':
        room_no = request.form.get('number', None)
        location = request.form.get('location', None)
        desc = request.form.get('desc', None)
        startdate = request.form.get('startdate', None)
        starttime = request.form.get('starttime', None)
        enddate = request.form.get('enddate', None)
        endtime = request.form.get('endtime', None)
        title = request.form.get('title', '')
        room = RoomResource.query.filter_by(number=room_no).first()
        tz = pytz.timezone('Asia/Bangkok')
        if startdate and starttime:
            startdatetime = datetime.strptime(
                '{} {}'.format(startdate, starttime), '%Y-%m-%d %H:%M')
            startdatetime = tz.localize(startdatetime, is_dst=None)
        else:
            startdatetime = None
        if enddate and endtime:
            enddatetime = datetime.strptime(
                '{} {}'.format(enddate, endtime), '%Y-%m-%d %H:%M')
            enddatetime = tz.localize(enddatetime, is_dst=None)
        else:
            enddatetime = None

        if startdatetime and enddatetime:
            timedelta = enddatetime - startdatetime
            if timedelta.days < 0 or timedelta.seconds == 0:
                flash('Date or time is invalid.')
            else:
                event = {
                    'summary': title,
                    'location': room_no,
                    'sendUpdates': 'all',
                    'status': 'tentative',
                    'description': desc,
                    'start': {
                        'dateTime': startdatetime.isoformat(),
                        'timeZone': 'Asia/Bangkok',
                    },
                    'end': {
                        'dateTime': enddatetime.isoformat(),
                        'timeZone': 'Asia/Bangkok',
                    },
                    'extendedProperties': {
                        'private': {
                            'room_no': room_no,
                            'location': location,
                        }
                    }
                }
                credentials, project_id = google.auth.default()
                scoped_credentials = credentials.with_scopes([
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/calendar.events'
                ])
                calendar_service = build('calendar', 'v3', credentials=scoped_credentials)
                event = calendar_service.events().insert(
                    calendarId='9hur49up24fdcbicdbggvpu77k@group.calendar.google.com',
                    body=event).execute()
                flash('Reservation has been made. {}'.format(event.get('htmlLink')))
                return redirect(url_for('room.index'))
    if room_no:
        room = RoomResource.query.filter_by(number=room_no).first()
        if room:
            timeslots = []
            for i in range(8,19):
                for j in [0, 30]:
                    timeslots.append('{:02}:{:02}'.format(i,j))
            return render_template('scheduler/reserve_form.html',
                                room=room, timeslots=timeslots)