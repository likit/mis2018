import datetime

from flask import render_template, make_response, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user

from app.main import db
from app.meeting_planner import meeting_planner
from app.meeting_planner.forms import MeetingEventForm
from app.meeting_planner.models import MeetingEvent, MeetingInvitation
from app.staff.models import StaffPersonalInfo
from app.main import mail
from pytz import timezone
from flask_mail import Message
import arrow

tz = timezone('Asia/Bangkok')


def send_mail(recp, title, message):
    message = Message(subject=title, body=message, recipients=recp)
    mail.send(message)


@meeting_planner.route('/')
@login_required
def index():
    return render_template('meeting_planner/index.html')


@meeting_planner.route('/meetings/new', methods=['GET', 'POST'])
@login_required
def create_meeting():
    form = MeetingEventForm()
    if form.validate_on_submit():
        form.start.data = form.start.data.astimezone(tz)
        form.end.data = form.end.data.astimezone(tz)
        for event_form in form.meeting_events:
            if event_form.room.data:
                event_form.start.data = form.start.data
                event_form.end.data = form.end.data
                event_form.title.data = f'ประชุม{form.title.data}'
        new_meeting = MeetingEvent()
        form.populate_obj(new_meeting)
        for staff_id in request.form.getlist('participants'):
            staff = StaffPersonalInfo.query.get(int(staff_id))
            invitation = MeetingInvitation(staff_id=staff.staff_account.id,
                                           created_at=new_meeting.start,
                                           meeting=new_meeting)
            db.session.add(invitation)
        new_meeting.creator = current_user
        db.session.commit()
        if form.notify_participants.data:
            meeting_invitation_link = url_for('meeting_planner.list_invitations', _external=True)
            message = f'''
            ขอเรียนเชิญเข้าร่วมประชุม{invitation.meeting.title}
            ในวันที่ {form.start.data.strftime('%d/%m/%Y %H:%M')} - {form.end.data.strftime('%d/%m/%Y %H:%M')}
            {invitation.meeting.rooms}
            
            กรุณาตอบรับการประชุมในลิงค์ด้านล่าง
            
            {meeting_invitation_link}
            '''
            if not current_app.debug:
                send_mail([invitation.staff.email+'@mahidol.ac.th' for invitation in new_meeting.invitations],
                          title=f'MUMT-MIS: เชิญเข้าร่วมประชุม{invitation.meeting.title}',
                          message=message)
            else:
                print(message)
        flash('บันทึกข้อมูลการประชุมแล้ว', 'success')
        return redirect(url_for('meeting_planner.index'))
    else:
        for field, error in form.errors.items():
            flash(f'{field}: {error}', 'danger')
    return render_template('meeting_planner/meeting_form.html', form=form)


@meeting_planner.route('/api/meeting_planner/add_event', methods=['POST'])
@login_required
def add_room_event():
    form = MeetingEventForm()
    form.meeting_events.append_entry()
    event_form = form.meeting_events[-1]
    template = u"""
    <div id="{}">
        <div class="field">
            <label class="label">{}</label>
            {}
            <span id="availability-{}"></span>
        </div>
        <div class="field">
            <label class="label">{}</label>
            <div class="control">
            {}
            </div>
        </div>
    <div>
    """
    resp = template.format(event_form.name,
                           event_form.room.label,
                           event_form.room(class_="js-example-basic-single"),
                           event_form.room.name,
                           event_form.request.label,
                           event_form.request(class_="input"),
                           )
    resp = make_response(resp)
    resp.headers['HX-Trigger-After-Swap'] = 'activateSelect2js'
    return resp


@meeting_planner.route('/api/meeting_planner/remove_event', methods=['DELETE'])
@login_required
def remove_room_event():
    form = MeetingEventForm()
    form.meeting_events.pop_entry()
    resp = ''
    for event_form in form.meeting_events:
        template = u"""
        <div id="{}" hx-preserve>
            <div class="field">
                <label class="label">{}</label>
                {}
                <span id="availability-{}"></span>
            </div>
            <div class="field">
                <label class="label">{}</label>
                <div class="control">
                {}
                </div>
            </div>
        </div>
        """.format(event_form.name,
                   event_form.room.label,
                   event_form.room(class_="js-example-basic-single"),
                   event_form.room.name,
                   event_form.request.label,
                   event_form.request(class_="input")
                   )
        resp += template
    if len(form.meeting_events.entries) == 0:
        resp = '<p>ไม่มีการใช้ห้องสำหรับกิจกรรม</p>'
    resp = make_response(resp)
    return resp


@meeting_planner.route('/invitations/<int:invitation_id>/rsvp')
@login_required
def respond(invitation_id):
    response = request.args.get('response')
    keep = request.args.get('keep', 'false')
    invitation = MeetingInvitation.query.get(invitation_id)
    if invitation.meeting.cancelled_at is None:
        invitation.response = response
        invitation.responded_at = arrow.now('Asia/Bangkok').datetime
        if invitation.response == 'เข้าร่วม':
            invitation.note = ''
            resp = '<i class="fa-sharp fa-regular fa-circle-check has-text-success"></i>'
            if keep == 'false':
                resp += f'<div id="target-{invitation.id}" hx-swap-oob="true"></div>'
        elif invitation.response == 'ไม่เข้าร่วม':
            add_note_to_response_url = url_for('meeting_planner.add_note_to_response', invitation_id=invitation.id, keep=keep)
            resp = '<i class="fa-solid fa-hand has-text-danger"></i>'
            resp += f'<div id="note-target-{invitation.id}" hx-swap-oob="true"><form hx-get="{add_note_to_response_url}"><input type="text" placeholder="โปรดระบุเหตุผล" value="{invitation.note}" name="note" class="input is-small"><input class="tag is-light" type="submit" value="Send"></form></div>'
            '''
            if keep == 'false':
                resp += f'<div id="target-{invitation.id}" hx-swap-oob="true"></div>'
            '''
        else:
            invitation.note = ''
            resp = '<i class="fa-solid fa-hourglass-start"></i>'
            if keep == 'false':
                resp += f'<div id="target-{invitation.id}" hx-swap-oob="true"></div>'
        db.session.add(invitation)
        db.session.commit()
        return resp
    return f'<div id="target-{invitation.id}" hx-swap-oob="true"></div>'


@meeting_planner.route('/api/invitations/<int:invitation_id>/note', methods=['GET'])
@login_required
def add_note_to_response(invitation_id):
    keep = request.args.get('keep', 'false')
    invitation = MeetingInvitation.query.get(invitation_id)
    invitation.note = request.args.get('note')
    print(request.args.get('note'))
    db.session.add(invitation)
    db.session.commit()
    if keep == 'true':
        return f'<div id="note-target-{invitation.id}" hx-swap-oob="true"></div>'
    else:
        return f'<div id="target-{invitation.id}" hx-swap-oob="true"></div>'


@meeting_planner.route('/api/invitations/<int:invitation_id>/detail')
@login_required
def invitation_detail(invitation_id):
    invite = MeetingInvitation.query.get(invitation_id)
    return f'''
    <nav class="level is-mobile">
        <div class="level-left">
            <a class="level-item" hx-target="#left-icon-{invite.id}" hx-get="{url_for('meeting_planner.respond', invitation_id=invite.id, response='เข้าร่วม')}">
                <span class="tag is-success">เข้าร่วม</span>
            </a>
            <a class="level-item" hx-target="#left-icon-{invite.id}" hx-get="{url_for('meeting_planner.respond', invitation_id=invite.id, response='ไม่เข้าร่วม')}">
                <span class="tag is-danger">ไม่เข้าร่วม</span>
            </a>
            <a class="level-item" hx-target="#left-icon-{invite.id}" hx-get="{url_for('meeting_planner.respond', invitation_id=invite.id, response='ไม่แน่ใจ')}">
                <span class="tag is-light">ไม่แน่ใจ</span>
            </a>
        </div>
    </nav>
    '''


@meeting_planner.route('/meetings')
@login_required
def list_meetings():
    return render_template('meeting_planner/meetings.html')


@meeting_planner.route('/invitations')
@login_required
def list_invitations():
    cat = request.args.get('cat', 'new')
    now = datetime.datetime.now(tz=tz)
    return render_template('meeting_planner/meeting_invitations.html', cat=cat, now=now)


@meeting_planner.route('/api/meetings')
@login_required
def get_meetings():
    data = []
    for meeting in MeetingEvent.query.filter_by(creator=current_user).order_by(MeetingEvent.created_at.desc()):
        d_ = meeting.to_dict()
        view_meeting_url = url_for('meeting_planner.detail_meeting', meeting_id=d_['id'])
        d_['action'] = f'<a class="tag" href={view_meeting_url}>view</a>'
        data.append(d_)
    return jsonify({'data': data})


@meeting_planner.route('/meetings/<int:meeting_id>/detail')
@login_required
def detail_meeting(meeting_id):
    meeting = MeetingEvent.query.get(meeting_id)
    return render_template('meeting_planner/meeting_detail.html', meeting=meeting)


@meeting_planner.route('/api/invitations/<int:invitation_id>/notify')
@login_required
def notify_participant(invitation_id):
    invitation = MeetingInvitation.query.get(invitation_id)
    meeting_invitation_link = url_for('meeting_planner.list_invitations',
                                      _external=True,
                                      meeting_id=invitation.meeting_event_id)
    start = invitation.meeting.start.astimezone(tz)
    end = invitation.meeting.end.astimezone(tz)
    message = f'''
    ขอเรียนเชิญเข้าร่วมประชุม{invitation.meeting.title}
    ในวันที่ {start.strftime('%d/%m/%Y %H:%M')} - {end.strftime('%d/%m/%Y %H:%M')}
    {invitation.meeting.rooms}
    
    กรุณาตอบรับการประชุมในลิงค์ด้านล่าง
    
    {meeting_invitation_link}
    '''
    if not current_app.debug:
        send_mail([invitation.staff.email+'@mahidol.ac.th'],
                  title=f'MUMT-MIS: เชิญเข้าร่วมประชุม{invitation.meeting.title}',
                  message=message)
    else:
        print(message)
    resp = make_response()
    resp.headers['HX-Trigger-After-Swap'] = 'notifyAlert'
    return resp