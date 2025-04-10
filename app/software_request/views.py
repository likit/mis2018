import os
import arrow
import requests
from sqlalchemy import or_
from flask import render_template, redirect, flash, url_for, jsonify, request
from flask_login import login_required, current_user
from app.software_request import software_request
from app.software_request.forms import SoftwareRequestDetailForm
from app.software_request.models import *
from werkzeug.utils import secure_filename
from pydrive.auth import ServiceAccountCredentials, GoogleAuth
from pydrive.drive import GoogleDrive

from app.staff.models import StaffPersonalInfo

gauth = GoogleAuth()
keyfile_dict = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()
scopes = ['https://www.googleapis.com/auth/drive']
gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, scopes)
drive = GoogleDrive(gauth)

FOLDER_ID = '1832el0EAqQ6NVz2wB7Ade6wRe-PsHQsu'

json_keyfile = requests.get(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')).json()

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


def initialize_gdrive():
    gauth = GoogleAuth()
    scopes = ['https://www.googleapis.com/auth/drive']
    gauth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_keyfile, scopes)
    return GoogleDrive(gauth)


@software_request.route('/')
@login_required
def index():
    org = current_user.personal_info.org
    details = SoftwareRequestDetail.query.filter(or_(SoftwareRequestDetail.created_id == current_user.id,
                                                     SoftwareRequestDetail.created_by.has(StaffAccount.personal_info.has(org=org))))
    return render_template('software_request/index.html', details=details)


@software_request.route('/condition')
def condition_for_service_request():
    return render_template('software_request/condition_page.html')


@software_request.route('/request/add', methods=['GET', 'POST'])
@software_request.route('/request/edit/<int:detail_id>', methods=['GET', 'POST'])
def create_request(detail_id=None):
    if detail_id:
        detail = SoftwareRequestDetail.query.get(detail_id)
        form = SoftwareRequestDetailForm(obj=detail)
        if detail.type == 'ปรับปรุงระบบที่มีอยู่':
            system = SoftwareRequestSystem.query.filter_by(system=detail.title).first()
            form.system.data = system
    else:
        form = SoftwareRequestDetailForm()
    if form.validate_on_submit():
        if detail_id is None:
            detail = SoftwareRequestDetail()
        form.populate_obj(detail)
        file = form.file_upload.data
        drive = initialize_gdrive()
        if request.form.getlist('system'):
            system = SoftwareRequestSystem.query.get(request.form.getlist('system'))
            detail.title = system.system
        if file:
            file_name = secure_filename(file.filename)
            file.save(file_name)
            file_drive = drive.CreateFile({'title': file_name,
                                           'parents': [{'id': FOLDER_ID, "kind": "drive#fileLink"}]})
            file_drive.SetContentFile(file_name)
            file_drive.Upload()
            file_drive.InsertPermission({'type': 'anyone', 'value': 'anyone', 'role': 'reader'})
            detail.url = file_drive['id']
            detail.file_name = file_name
        if detail_id:
            detail.updated_date = arrow.now('Asia/Bangkok').datetime
        else:
            detail.created_date = arrow.now('Asia/Bangkok').datetime
            detail.created_id = current_user.id
        if 'draft' in request.form:
            detail.status = 'ร่าง'
        else:
            detail.status = 'ส่งคำขอแล้ว'
        db.session.add(detail)
        db.session.commit()
        if 'draft' in request.form:
            flash('บันทึกแบบร่างสำเร็จ', 'success')
        else:
            flash('ส่งคำขอสำเร็จ', 'success')
        return redirect(url_for('software_request.index'))
    else:
        for er in form.errors:
            flash(er, 'danger')
    return render_template('software_request/create_request.html', form=form, detail_id=detail_id)


@software_request.route('/api/system', methods=['GET'])
@login_required
def get_systems():
    search_term = request.args.get('term', '')
    key = request.args.get('key', 'id')
    results = []
    systems = SoftwareRequestSystem.query.all()
    for system in systems:
        if search_term in system.system:
            index_ = getattr(system, key) if hasattr(system, key) else getattr(system.system, key)
            results.append({
                "id": index_,
                "text": system.system
            })
    return jsonify({'results': results})