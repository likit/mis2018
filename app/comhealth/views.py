# -*- coding: utf-8 -*-
import io
import json
import os
import datetime
from collections import OrderedDict, defaultdict
from io import BytesIO

import arrow
import pandas as pd
from flask_cors import cross_origin
from flask_mail import Message
from flask_wtf.csrf import generate_csrf
from pandas import read_excel, isna
from bahttext import bahttext
from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql import and_
from flask import (render_template, flash, redirect,
                   url_for, session, request, send_file,
                   send_from_directory, jsonify, make_response)
from flask_admin import BaseView, expose
from flask_login import login_required, current_user
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (SimpleDocTemplate, Table, Image,
                                Spacer, Paragraph, TableStyle, PageBreak, KeepTogether)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from . import comhealth
from .forms import (ServiceForm, TestProfileForm, TestListForm,
                    TestForm, TestGroupForm, CustomerForm, PasswordOfSignDigitalForm, SendMailToCustomerForm,
                    CustomerInfoForm)
from .models import *
from app.main import cors, mail
from ..e_sign_api import e_sign

bangkok = pytz.timezone('Asia/Bangkok')

ALLOWED_EXTENSIONS = ['xlsx', 'xls']


@comhealth.route('/api/v1/lineids/<lineid>')
@cross_origin()
def get_line_id(lineid):
    if (lineid):
        customer = ComHealthCustomer.query.filter_by(line_id=lineid).first()
        if customer:
            # serialization
            return jsonify({'status': True})
        else:
            return jsonify({'status': False})
    return 400


@comhealth.route('/')
@login_required
def landing():
    return render_template('comhealth/landing.html')


@comhealth.route('/finance', methods=('GET', 'POST'))
@login_required
def finance_landing():
    if request.method == 'POST':
        venue = request.form.get('venue')
        session['receipt_venue'] = venue
        return redirect(url_for('comhealth.finance_index'))
    return render_template('comhealth/finance_landing.html')


@comhealth.route('/services/finance')
@login_required
def finance_index():
    services = ComHealthService.query.all()
    services_data = []
    for sv in services:
        d = {
            'id': sv.id,
            'date': sv.date,
            'location': sv.location,
            'registered': sv.records.count(),
            'checkedin': sv.records.filter(ComHealthRecord.checkin_datetime != None).count()
        }
        services_data.append(d)
    services_data = sorted(services_data, key=lambda x: x['date'], reverse=True)
    return render_template('comhealth/finance_index.html', services=services_data)

@comhealth.route('/services/<int:service_id>/finance/download_receipts_all_summary/<summary_type>/<schedule_date_thaiform>')
@login_required
def download_receipts_all_summary(service_id,summary_type,schedule_date_thaiform):
    service = ComHealthService.query.get(service_id)
    receipts = []

    for rec in service.records:
        for receipt in rec.receipts:
            create_date = receipt.created_datetime.astimezone(bangkok).strftime("%Y-%m-%d")
            if summary_type == 'all' and create_date == schedule_date_thaiform:
                receipts.append({
                    "หมายเลข": receipt.code,
                    "วันที่ได้รับ": receipt.created_datetime.astimezone(bangkok).strftime("%Y-%m-%d %H:%M:%S"),
                    "ประเภทเงินที่จ่าย": receipt.payment_method,
                    "LabNo.": rec.labno,
                    "คำนำหน้า": rec.customer.title,
                    "ชื่อ": rec.customer.firstname,
                    "นามสกุล": rec.customer.lastname,
                    "ประเภทบุคลากร": rec.customer.emptype.name,
                    "เงินที่ได้": int(receipt.paid_amount),
                    "จ่ายเงิน": "จ่าย" if receipt.paid else "ยังไม่จ่าย",
                    "สถานะใบเสร็จ": "ปกติ" if not receipt.cancelled else "ยกเลิก",
                    "ผู้ออกใบเสร็จ": receipt.issuer.staff.fullname,
                    "หน่วยงาน": service.location,
                })
            elif summary_type == 'income':
                if receipt.cancelled == False and create_date == schedule_date_thaiform:
                    receipts.append({
                        "หมายเลข": receipt.code,
                        "วันที่ได้รับ": receipt.created_datetime.astimezone(bangkok).strftime("%Y-%m-%d %H:%M:%S"),
                        "ประเภทเงินที่จ่าย": receipt.payment_method,
                        "LabNo.": rec.labno,
                        "คำนำหน้า": rec.customer.title,
                        "ชื่อ": rec.customer.firstname,
                        "นามสกุล": rec.customer.lastname,
                        "ประเภทบุคลากร": rec.customer.emptype.name,
                        "เงินที่ได้": int(receipt.paid_amount),
                        "จ่ายเงิน": "จ่าย" if receipt.paid else "ยังไม่จ่าย",
                        "สถานะใบเสร็จ": "ปกติ" if not receipt.cancelled else "ยกเลิก",
                        "ผู้ออกใบเสร็จ": receipt.issuer.staff.fullname,
                        "หน่วยงาน": service.location,
                    })
            elif summary_type == 'cancel':
                if receipt.cancelled == True and create_date == schedule_date_thaiform:
                    receipts.append({
                        "หมายเลข": receipt.code,
                        "วันที่ได้รับ": receipt.created_datetime.astimezone(bangkok).strftime("%Y-%m-%d %H:%M:%S"),
                        "ประเภทเงินที่จ่าย": receipt.payment_method,
                        "LabNo.": rec.labno,
                        "คำนำหน้า": rec.customer.title,
                        "ชื่อ": rec.customer.firstname,
                        "นามสกุล": rec.customer.lastname,
                        "ประเภทบุคลากร": rec.customer.emptype.name,
                        "เงินที่ได้": int(receipt.paid_amount),
                        "จ่ายเงิน": "จ่าย" if receipt.paid else "ยังไม่จ่าย",
                        "สถานะใบเสร็จ": "ปกติ" if not receipt.cancelled else "ยกเลิก",
                        "ผู้ออกใบเสร็จ": receipt.issuer.staff.fullname,
                        "หน่วยงาน": service.location,
                    })
    receipts.sort(key=lambda k: (k['LabNo.'] is not None, k['LabNo.']))
    df = pd.DataFrame(receipts)
    output = io.BytesIO()
    df.to_excel(output,sheet_name='Sheet1', index=False)
    output.seek(0)
    return send_file(output,download_name='recepits_all.xlsx')

@comhealth.route('/services/<int:service_id>/finance/summary',methods=('GET', 'POST'))
@login_required
def finance_summary(service_id):
    schedule_date_thaiform = ''
    if request.method == 'POST':
        schedule_date = request.form.get('scheduledate')
        if schedule_date:
            schedule_date_string = schedule_date.split('/')
            schedule_date_thaiform = schedule_date_string[2] + '-' + f'{int(schedule_date_string[1]):02n}' + '-' + f'{int(schedule_date_string[0]):02n}'

    service = ComHealthService.query.get(service_id)
    totals_paid_cash = 0
    totals_paid_QR =  0
    totals_paid_amount = 0
    totals_paid_card = 0
    count_receipts = 0
    for rec in service.records:
        for receipt in rec.receipts:
            created_date_string = receipt.created_datetime.astimezone(bangkok).strftime("%Y-%m-%d")
            if receipt.paid and receipt.cancelled == False and created_date_string == schedule_date_thaiform:
                totals_paid_amount += receipt.paid_amount
                count_receipts += 1
                if receipt.payment_method=='cash':
                    totals_paid_cash += receipt.paid_amount
                if receipt.payment_method=='QR':
                    totals_paid_QR += receipt.paid_amount
                if receipt.payment_method=='card':
                    totals_paid_card += receipt.paid_amount
    return render_template('comhealth/finance_summary.html', service=service,totals_paid_amount=totals_paid_amount,
                           totals_paid_cash=totals_paid_cash,totals_paid_QR=totals_paid_QR,totals_paid_card=totals_paid_card,
                           count_receipts=count_receipts,schedule_date_thaiform=schedule_date_thaiform)


@comhealth.route('/api/services/<int:service_id>/records')
@login_required
def api_finance_record(service_id):
    service = ComHealthService.query.get(service_id)
    query = service.records.filter(ComHealthRecord.is_checked_in != None)
    query = query.filter(ComHealthRecord.checkin_datetime != None)
    #print(request.form.get('search'))
    records = [rec for rec in query if len(rec.receipts) > 0 or rec.finance_contact is not None]
    record_schema = ComHealthRecordSchema(many=True,
                                          only=('labno', 'customer', 'id',
                                                'checkin_datetime', 'finance_contact',
                                                'receipts', 'note'))
    return jsonify(record_schema.dump(records))

@comhealth.route('/api/records', methods=['GET'])
@login_required
def api_finance_record_tab():
    tab = request.args.get('tab')
    service_id = request.args.get('serviceid')
    service = ComHealthService.query.get(service_id)
    query = service.records.filter(ComHealthRecord.is_checked_in != None)
    query = query.filter(ComHealthRecord.checkin_datetime != None)
    if tab == 'pending':
        records = [rec for rec in query if rec.finance_contact_id == 1 or rec.finance_contact_id == 2]
    elif tab == 'paid':
        records = [rec for rec in query if len(rec.receipts) > 0 and rec.finance_contact is  None]
    elif tab == 'cancelled':
        #TODO แสดงใบเสร็จที่ถูกยกเลิก
        records = ComHealthRecord.query.filter_by(comment='ยกเลิก').all()
    else:
        records = []
    return jsonify([record.to_dict() for record in records])


@comhealth.route('/services/health-record')
@login_required
def health_record_landing():
    services = ComHealthService.query.all()
    services_data = []
    for sv in services:
        d = {
            'id': sv.id,
            'date': sv.date,
            'location': sv.location,
            'registered': sv.records.count(),
            'checkedin': len([r for r in sv.records if r.checkin_datetime is not None])
        }
        services_data.append(d)
    return render_template('comhealth/health_record_landing.html', services=services_data)


@comhealth.route('/services/<int:service_id>/health-record')
@login_required
def health_record_index(service_id):
    service = ComHealthService.query.get(service_id)
    employees = [r.customer for r in service.records]
    customer_schema = ComHealthCustomerSchema(many=True)
    if employees:
        org = employees[0].org
    else:
        org = None
    return render_template('comhealth/employees.html',
                           employees=customer_schema.dump(org.employees),
                           org=org)


@comhealth.route('/services/<int:service_id>/finance/records')
@login_required
def show_finance_records(service_id):
    service = ComHealthService.query.get(service_id)
    return render_template('comhealth/finance_records.html', service=service)


@comhealth.route('/customers')
@login_required
def index():
    services = ComHealthService.query.all()
    services_data = []
    for sv in services:
        d = {
            'id': sv.id,
            'date': sv.date,
            'location': sv.location,
            'registered': sv.records.count(),
            'checkedin': sv.records.filter(ComHealthRecord.checkin_datetime != None).count()
        }
        services_data.append(d)
    services_data = sorted(services_data, key=lambda x: x['date'], reverse=True)
    return render_template('comhealth/index.html', services=services_data)


@comhealth.route('/api/services/<int:service_id>/search')
def search_service_customer(service_id):
    # TODO: search should be done at the backend
    service = ComHealthService.query.get(service_id)
    record_schema = ComHealthRecordCustomerSchema(many=True,
                                                  only=("id", "labno", "checkin_datetime", "customer"))
    return jsonify(record_schema.dump(service.records))


@comhealth.route('/orgs/<int:org_id>/services/register')
@login_required
def register_service_to_org(org_id):
    services = ComHealthService.query.all()
    org = ComHealthOrg.query.get(org_id)
    service_schema = ComHealthServiceOnlySchema(many=True)
    return render_template('comhealth/service_register.html', services=service_schema.dump(services), org=org)


@comhealth.route('/orgs/<int:org_id>/services/<int:service_id>/register')
@login_required
def register_customer_to_service_org(service_id, org_id):
    org = ComHealthOrg.query.get(org_id)
    service = ComHealthService.query.get(service_id)
    num_customers = 0
    for employee in org.employees:
        previous_services = set([rec.service for rec in employee.records])
        if service not in previous_services:
            new_record = ComHealthRecord(date=service.date,
                                         service=service,
                                         customer=employee)
            db.session.add(new_record)
            num_customers += 1
        db.session.commit()
    flash('{} customers have been registered for this service.'.format(num_customers))
    return redirect(url_for('comhealth.index'))


@comhealth.route('/services/<int:service_id>')
@login_required
def display_service_customers(service_id):
    service = ComHealthService.query.get(service_id)
    return render_template('comhealth/service_customers.html', service_id=service_id, service=service)


@comhealth.route('api/services/<int:service_id>/customers')
@login_required
def get_services_customers(service_id):
    query = ComHealthRecord.query.filter_by(service_id=service_id)
    records_total = query.count()
    search = request.args.get('search[value]')
    col_idx = request.args.get('order[0][column]')
    direction = request.args.get('order[0][dir]')
    col_name = request.args.get('columns[{}][data]'.format(col_idx))
    query = query.join(ComHealthCustomer, aliased=True).filter(or_(
        ComHealthCustomer.firstname.contains(search),
        ComHealthCustomer.lastname.contains(search),
        ComHealthRecord.labno.contains(search)))
    try:
        column = getattr(ComHealthCustomer, col_name)
    except AttributeError:
        column = getattr(ComHealthRecord, col_name)
    if direction == 'desc':
        column = column.desc()
    query = query.order_by(column)
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []
    for item in query:
        item_data = item.to_dict()
        if item.checkin_datetime != None:
            item_data['checkin_datetime'] = item.checkin_datetime.astimezone(bangkok).strftime("%Y-%m-%d %H:%M")
            item_data[
                'check_in_time'] = '<a class="button is-rounded is-light" href="{}" <div><span class="icon"><i class="fas fa-user-check has-text-success"></i></span><span>Check in</span></div></a>'.format(
                url_for('comhealth.edit_record', record_id=item.id))
        else:
            item_data[
                'check_in_time'] = '<a class="button is-rounded is-light" href="{}" <div><span class="icon"><i class="fas fa-user"></i></span><span>Check in</span></div></a>'.format(
                url_for('comhealth.edit_record', record_id=item.id))
        item_data[
            'customer_info'] = '<a class="button is-rounded is-light" href="{}" <span class="icon"><i class="fas fa-pencil-alt"></i></span></a>'.format(
            url_for('comhealth.edit_customer_data', customer_id=item.customer_id, service_id=service_id))
        item_data[
            'note_info'] = '<a class="button is-rounded is-light" href="{}" <span class="icon"><i class="fas fa-book"></span></i></a>'.format(
            url_for('comhealth.edit_note_data', record_id=item.id))
        data.append(item_data)
    return jsonify({'data': data,
                    'recordsFiltered': total_filtered,
                    'recordsTotal': records_total,
                    'draw': request.args.get('draw', type=int),
                    })


@comhealth.route('/services/<int:service_id>/pre-register')
def pre_register(service_id):
    service = ComHealthService.query.get(service_id)
    return render_template('comhealth/pre_register.html', service=service)


@comhealth.route('/services/<int:service_id>/employees_list')
def employees_list(service_id):
    list_employees = request.args.get('employees_list')
    if list_employees:
        query = ComHealthRecord.query.filter_by(service_id=service_id)
        query = query.join(ComHealthCustomer, aliased=True).filter(or_(
            ComHealthCustomer.firstname.contains(list_employees),
            ComHealthCustomer.lastname.contains(list_employees)))
        #print(query)
        template = '<table class="table is-fullwidth">'
        template += '<thead><th></th><th></th></thead>'
        template += '<tbody>'
        for record in query:
            template += '<tr><td>'
            template += record.customer.firstname + ' ' + record.customer.lastname
            template += '</td><td><a class="button is-light is-link" href="{}" <span>ลงทะเบียน</span></a>'.format(
                url_for('comhealth.pre_register_login', service_id=service_id, record_id=record.id))
            template += '</td></tr>'
        template += '</tbody></table>'
        return template
    return ''


@comhealth.route('api/services/<int:service_id>/pre-register')
@login_required
def get_services_pre_register(service_id):
    query = ComHealthRecord.query.filter_by(service_id=service_id)
    records_total = query.count()
    search = request.args.get('search[value]')
    query = query.join(ComHealthCustomer, aliased=True).filter(or_(
        ComHealthCustomer.firstname.contains(search),
        ComHealthCustomer.lastname.contains(search)))
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    total_filtered = query.count()
    query = query.offset(start).limit(length)
    data = []
    for item in query:
        item_data = item.to_dict()
        item_data[
            'customer_pre_register'] = '<a class="button is-light is-link" href="{}" <span>ลงทะเบียน</span></a>'.format(
            url_for('comhealth.pre_register_login', service_id=service_id, record_id=item.id))
        data.append(item_data)
    return jsonify({'data': data,
                    'recordsFiltered': total_filtered,
                    'recordsTotal': records_total,
                    'draw': request.args.get('draw', type=int),
                    })


@comhealth.route('/services/<int:service_id>/pre-register/<int:record_id>/login', methods=['GET', 'POST'])
def pre_register_login(service_id, record_id):
    service = ComHealthService.query.get(service_id)
    record = ComHealthRecord.query.get(record_id)
    if request.method == 'POST':
        dob = request.form.get('dob')
        if record.customer.check_login_dob(dob):
            return redirect(url_for('comhealth.pre_register_tests',
                                    record_id=record_id, service_id=service_id))
        else:
            flash(u'วันเดือนปีเกิดไม่ถูกต้องหรือไม่มีข้อมูล', 'danger')
    return render_template('comhealth/pre_register_login.html',
                           service=service, record=record)


@comhealth.route('/services/<int:service_id>/pre-register/<int:record_id>/tests', methods=['GET', 'POST'])
def pre_register_tests(service_id, record_id):
    service = ComHealthService.query.get(service_id)
    record = ComHealthRecord.query.get(record_id)

    if request.method == 'POST':
        record.ordered_tests = []
        for field in request.form:
            if field.startswith('test_'):
                _, test_id = field.split('_')  # name=test_34
                test_item = ComHealthTestItem.query.get(int(test_id))
                record.ordered_tests.append(test_item)

        record.updated_at = datetime.now(tz=bangkok)
        db.session.add(record)
        db.session.commit()

        special_item_cost = sum([item.price for item in set(record.ordered_tests)])
        return render_template('comhealth/pre_register_summary.html',
                               special_item_cost=special_item_cost, record=record)

    return render_template('comhealth/pre_register_edit_record.html', service=service, record=record)


@comhealth.route('/checkin/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(record_id):
    record = ComHealthRecord.query.get(record_id)
    total_paid_already = 0
    for r in record.receipts:
        if r.paid and not r.cancelled:
            total_paid_already += r.paid_amount
    finance_contact_reasons = ComHealthFinanceContactReason.query.all()
    if not record.service.profiles and not record.service.groups:
        return redirect(url_for('comhealth.edit_service', service_id=record.service.id))

    emptypes = ComHealthCustomerEmploymentType.query.all()

    if request.method == 'GET':
        if not record.checkin_datetime:
            group_preregister = []
            for group in record.service.groups:
                for item in group.test_items:
                    if item in record.ordered_tests:
                        is_preregister = True
                        break
                    else:
                        is_preregister = False
                if is_preregister:
                    group_preregister.append(group.id)
            return render_template('comhealth/edit_record.html',
                                   finance_contact_reasons=finance_contact_reasons,
                                   record=record,
                                   emptypes=emptypes,
                                   group_preregister=group_preregister)
    containers = set()
    group_item_cost = Decimal(0.0)
    if request.method == 'POST':
        if not record.labno:
            labno = request.form.get('service_code', '')
            if len(labno) != 10 or not labno.isdigit():
                flash(u'กรุณาระบุหมายเลข lab number ให้ถูกต้องหรือแสกนบาร์โค้ด', 'warning')
                return redirect(request.referrer)
            else:
                existing_rec = ComHealthRecord.query.filter_by(labno=labno).first()
                if existing_rec:
                    flash(u'หมายเลข lab number นี้มีการลงทะเบียนแล้ว ไม่สามารถใช้ซ้ำได้', 'warning')
                    return redirect(request.referrer)

            record.labno = labno  # assign a valid and unique lab number

        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        title = request.form.get('title')
        finance_contact_reason_id = request.form.get('finance_contact', '0')

        if finance_contact_reason_id != '0':
            record.finance_contact_id = int(finance_contact_reason_id)

        if firstname:
            record.customer.firstname = firstname
        if lastname:
            record.customer.lastname = lastname
        if title:
            record.customer.title = title
        if request.form.get('phone'):
            record.customer.phone = request.form.get('phone')
        if request.form.get('dob'):
            try:
                day, month, year = request.form.get('dob', '').split('/')
                year = int(year) - 543
                month = int(month)
                day = int(day)
            except:
                flash(u'วันเดือนปีเกิดไม่ถูกต้อง', 'warning')
            else:
                record.customer.dob = date(year, month, day)

        if not record.checkin_datetime:
            record.checkin_datetime = datetime.now(tz=bangkok)

        if not record.labno:
            labno = request.form.get('service_code')
            existing_labno = ComHealthRecord.query.filter_by(labno=labno).first()
            if existing_labno:
                flash(u'หมายเลข Lab number มีในฐานข้อมูลแล้ว', 'warning')
                return redirect(url_for('comhealth.edit_record', record_id=record_id))
            if labno.isdigit() and len(labno) == 10:
                record.labno = labno
            else:
                flash(u'หมายเลข lab number ไม่ถูกต้อง', 'warning')
                return redirect(url_for('comhealth.edit_record', record_id=record_id))

        record.ordered_tests = []
        test_order_list = []
        for field in request.form:
            if field.startswith('test_'):
                _, test_id = field.split('_')
                test_item = ComHealthTestItem.query.get(int(test_id))
                if not test_item.test.code in test_order_list:
                    group_item_cost += test_item.price
                    containers.add(test_item.test.container)
                    record.ordered_tests.append(test_item)
                    test_order_list.append(test_item.test.code)
            elif field.startswith('profile_'):
                _, test_id, _ = field.split('_')
                test_item = ComHealthTestItem.query.get(int(test_id))
                if not test_item.test.code in test_order_list:
                    record.ordered_tests.append(test_item)
                    containers.add(test_item.test.container)
                    test_order_list.append(test_item.test.code)

        if len(record.ordered_tests) == 0:
            flash(u'กรุณาเลือกรายการทดสอบอย่างน้อยหนึ่งรายการ', 'warning')
            return redirect(request.referrer)

        record.comment = request.form.get('comment')
        emptype_id = int(request.form.get('emptype_id', 0))
        department_id = int(request.form.get('department_id', 0))
        record.customer.emptype_id = emptype_id
        record.note = request.form.get('note')

        if department_id > 0:
            record.customer.dept_id = department_id

        if group_item_cost > 0:
            record.finance_contact_id = 1
        else:
            record.finance_contact_id = None
        # ถ้าเลือก เหมาจ่าย จะเป็นชำระเองทั้งหมด
        for profile in record.service.profiles:
            ordered_profile_tests = set(profile.test_items).intersection(record.ordered_tests)
            if ordered_profile_tests:
                if profile.quote > 0:
                    record.finance_contact_id = 2

        record.updated_at = datetime.now(tz=bangkok)
        db.session.add(record)
        db.session.commit()

    special_tests = set(record.ordered_tests)

    profile_item_cost = Decimal(0.0)

    for profile in record.service.profiles:
        ordered_profile_tests = set(profile.test_items).intersection(record.ordered_tests)
        if ordered_profile_tests:
            if profile.quote > 0:
                # Profile รวมราคาเหมาจ่าย
                profile_item_cost += profile.quote
            else:
                profile_item_cost += sum([test_item.price for test_item in ordered_profile_tests])
        special_tests.difference_update(set(profile.test_items))
    #Profile จะไม่คิดเงินนอกจากจะป็น ชำระเองทั้งหมด
    if record.finance_contact_id != 2:
        profile_item_cost = 0
    group_item_cost = sum([item.price for item in record.ordered_tests if item.group])
    special_item_cost = sum([item.price for item in special_tests])
    containers = set([item.test.container for item in record.ordered_tests])
    all_order_profile = set([item.profile for item in record.ordered_tests if item.profile])
    all_order_group = set([item.group for item in record.ordered_tests if item.group])
    dic_con = {}
    for item in record.ordered_tests:
        dic_con[item.test.name] = item.test.container.id
    return render_template('comhealth/record_summary.html',
                           record=record,
                           containers=containers,
                           profile_item_cost=profile_item_cost,
                           group_item_cost=group_item_cost,
                           special_tests=special_tests,
                           finance_contact_reasons=finance_contact_reasons,
                           special_item_cost=special_item_cost,
                           total_paid_already=total_paid_already,
                           dic_con=dic_con,
                           all_order_profile=all_order_profile,
                           all_order_group=all_order_group)


@comhealth.route('/record/<int:record_id>/edit-info', methods=['GET', 'POST'])
@login_required
def edit_customer_info_modal(record_id):
    record = ComHealthRecord.query.get(record_id)
    form = CustomerInfoForm(obj=record.customer)
    if form.validate_on_submit():
        form.populate_obj(record.customer)
        db.session.add(record.customer)
        db.session.commit()
        resp = make_response()
        resp.headers['HX-Refresh'] = 'true'
        return resp
    else:
        print(form.errors)
    return render_template('comhealth/modals/edit_customer_info_modal.html',
                           form=form, record=record)


@comhealth.route('/record/update-finance-contact/', methods=['GET', 'POST'])
@login_required
def update_finance_contact():
    if request.method == 'POST':
        record_id = request.form.get('record_id')
        record = ComHealthRecord.query.get(int(record_id))
        contact_reason_id = request.form.get('finance_contact')
        if contact_reason_id == '0':
            record.finance_contact_id = None
        else:
            record.finance_contact_id = int(contact_reason_id)
        db.session.add(record)
        db.session.commit()
        flash(u'ข้อมูลการติดต่อการเงินได้รับการเปลี่ยนแปลงแล้ว', 'success')
    return redirect(request.referrer)


@comhealth.route('/record/order/add-comment', methods=['GET', 'POST'])
@login_required
def add_comment_to_order():
    if request.method == 'POST':
        record_id = request.form.get('record_id')
        record = ComHealthRecord.query.get(int(record_id))
        comment = request.form.get('comment')
        record.comment = comment
        db.session.add(record)
        db.session.commit()

        return redirect(url_for('comhealth.edit_record', record_id=record.id))


@comhealth.route('/record/<int:record_id>/order/add-test-item/<int:item_id>/<profile_item_cost>', methods=['POST'])
@login_required
def add_item_to_order(record_id, item_id, profile_item_cost):
    if record_id and item_id:
        record = ComHealthRecord.query.get(record_id)
        item = ComHealthTestItem.query.get(item_id)

        if item not in record.ordered_tests:
            total_price = float(record.total_group_item_cost) + float(profile_item_cost)
            record.ordered_tests.append(item)
            if total_price + float(item.price) <= 0:
                record.finance_contact_id = None
            record.updated_at = arrow.now('Asia/Bangkok').datetime
            db.session.add(record)
            db.session.commit()

            price = f'{item.price or item.test.default_price} บาท'
            total_paid_amount = 0

            for r in record.receipts:
                if r.paid and not r.cancelled:
                    total_paid_amount += r.paid_amount

            template = f'''
            <tr>
            <td class="has-text-info">{item.test.name} ({item.test.desc}) {price if item.group else ''}</td>
            <td>
            <a class="button is-rounded is-small is-danger"
                hx-target="closest tr"
                hx-confirm="คุณแน่ใจว่าจะยกเลิกรายการนี้"
                hx-swap="outerHTML"
                hx-headers='{{"X-CSRF-Token": "{ generate_csrf() }" }}'
                hx-delete="{ url_for('comhealth.remove_item_from_order', record_id = record.id, item_id = item.id, profile_item_cost=profile_item_cost)}">
                <span class="icon">
                    <i class="fa-solid fa-trash-can"></i>
                </span>
                <span>ยกเลิก</span>
            </a>
            </td>
            </tr>
            <td id="paid-total" hx-swap-oob="true">
                <h1 class="title has-text-success">{total_paid_amount:,.02f} บาท</h1>
            </td>
            <td id="grand-total" hx-swap-oob="true">
                <h1 class="title">{total_price + float(item.price):,.02f} บาท</h1>
            </td>
            '''
            if total_paid_amount < record.total_group_item_cost:
                template += f'''
                    <td id="unpaid-total" hx-swap-oob="true">
                        <h1 class="title has-text-danger">{(record.total_group_item_cost - total_paid_amount):,.02f} บาท</h1>
                    </td>
                '''
            else:
                template += f'''
                    <td id="unpaid-total" hx-swap-oob="true">
                        <h1 class="title has-text-success">ไม่มี</h1>
                    </td>
                '''
            return template


@comhealth.route('/record/<int:record_id>/order/remove-test-item/<int:item_id>/<profile_item_cost>', methods=['DELETE'])
@login_required
def remove_item_from_order(record_id, item_id, profile_item_cost):
    if record_id and item_id:
        record = ComHealthRecord.query.get(record_id)
        item = ComHealthTestItem.query.get(item_id)

        if item in record.ordered_tests:
            price = f'{item.price or item.test.default_price} บาท'
            total_paid_amount = 0
            for r in record.receipts:
                if r.paid and not r.cancelled:
                    total_paid_amount += r.paid_amount

            total_price = float(record.total_group_item_cost) + float(profile_item_cost)

            if total_price - float(item.price) <= 0:
                record.finance_contact_id = None

            record.ordered_tests.remove(item)
            record.updated_at = datetime.now(tz=bangkok)
            record.finance_contact_id = record.finance_contact_id if any(
                [item.group for item in record.ordered_tests]) else None
            db.session.add(record)
            db.session.commit()

            template = f'''
            <tr>
            <td><strong>{item.test.name} ({item.test.desc}) {price if item.group else ''}</strong></td>
            <td>
            <a class ="button is-rounded is-small is-success"
                hx-target="closest tr"
                hx-swap="outerHTML"
                hx-headers='{{"X-CSRF-Token": "{ generate_csrf() }" }}'
                hx-post="{ url_for('comhealth.add_item_to_order', record_id = record.id, item_id = item.id, profile_item_cost= profile_item_cost)}">
                <span class="icon">
                    <i class="fas fa-plus"></i>
                </span>
                <span>เพิ่ม</span>
            </a>
            </td>
            </tr>
            <td id="paid-total" hx-swap-oob="true">
                <h1 class="title has-text-success">{total_paid_amount:,} บาท</h1>
            </td>
            <td id="grand-total" hx-swap-oob="true">
                <h1 class="title">{total_price - float(item.price):,} บาท</h1>
            </td>
            '''
            if total_paid_amount < record.total_group_item_cost:
                template += f'''
                    <td id="unpaid-total" hx-swap-oob="true">
                        <h1 class="title has-text-danger">{record.total_group_item_cost - total_paid_amount:,} บาท</h1>
                    </td>
                '''
            else:
                template += f'''
                    <td id="unpaid-total" hx-swap-oob="true">
                        <h1 class="title has-text-success">ไม่มี</h1>
                    </td>
                '''
            return template


@comhealth.route('/record/<int:record_id>/update-delivery-status')
@login_required
def update_delivery_status(record_id):
    if record_id:
        record = ComHealthRecord.query.get(record_id)
        record.urgent = not record.urgent
        record.updated_at = datetime.now(tz=bangkok)
        db.session.add(record)
        db.session.commit()
        flash('Delivery request has been updated.')
        return redirect(url_for('comhealth.edit_record', record_id=record.id))


@comhealth.route('/record/<int:record_id>/cancel')
@login_required
def cancel_checkin_record(record_id):
    record = ComHealthRecord.query.get(record_id)
    if not record:
        flash('Record does not exist.', 'warning')
        return redirect(request.referrer)
    if request.args.get('confirm') == 'no':
        return render_template('comhealth/confirm_record_cancel.html',
                               next=request.referrer, record=record)
    elif request.args.get('confirm') == 'yes':
        service_id = record.service_id
        record.labno = None
        record.checkin_datetime = None
        record.ordered_tests = []
        record.updated_at = datetime.now(tz=bangkok)
        record.urgent = False
        record.comment = ''
        db.session.add(record)
        db.session.commit()
        flash('The record has been cancelled.', 'success')
        return redirect(url_for('comhealth.display_service_customers',
                                service_id=service_id))


@comhealth.route('/tests')
@login_required
def test_index():
    profiles = ComHealthTestProfile.query.all()
    pf_schema = ComHealthTestProfileSchema(many=True)
    return render_template('comhealth/test_profile.html',
                           profiles=pf_schema.dump(profiles))


@comhealth.route('/test/groups')
@comhealth.route('/test/groups/<int:group_id>')
@login_required
def test_group_index(group_id=None):
    if group_id:
        group = ComHealthTestGroup.query.get(group_id)
        return render_template('comhealth/test_group_edit.html', group=group)

    groups = ComHealthTestGroup.query.all()
    gr_schema = ComHealthTestGroupSchema(many=True)
    return render_template('comhealth/test_group.html',
                           groups=gr_schema.dump(groups))


@comhealth.route('/test/profiles/new', methods=['GET', 'POST'])
@login_required
def add_test_profile():
    form = TestProfileForm()
    if form.validate_on_submit():
        new_profile = ComHealthTestProfile(
            name=form.name.data,
            desc=form.desc.data,
            age_max=form.age_max.data,
            age_min=form.age_min.data,
            gender=form.gender.data,
            quote=form.quote.data,
        )
        db.session.add(new_profile)
        db.session.commit()
        flash('Profile {} has been added.')
        return redirect(url_for('comhealth.test_index'))
    else:
        for field_name, errors in form.errors.items():
            for error in errors:
                flash(u'{} {}'.format(field_name, error))

    return render_template('comhealth/new_profile.html', form=form)


@comhealth.route('/test/groups/new', methods=['GET', 'POST'])
@login_required
def add_test_group():
    form = TestGroupForm()
    if form.validate_on_submit():
        new_group = ComHealthTestGroup(
            name=form.name.data,
            desc=form.desc.data,
            age_max=form.age_max.data,
            age_min=form.age_min.data,
            gender=form.gender.data,
        )
        db.session.add(new_group)
        db.session.commit()
        flash('Group {} has been added.')
        return redirect(url_for('comhealth.test_index'))
    else:
        for field_name, errors in form.errors.items():
            for error in errors:
                flash(u'{} {}'.format(field_name, error))

    return render_template('comhealth/new_group.html', form=form)


@comhealth.route('/test/tests/profile/menu/<int:profile_id>')
@login_required
def profile_test_menu(profile_id=None):
    '''Shows a menu of tests to be added to the profile.

    :param profile_id:
    :return:
    '''
    if profile_id:
        tests = ComHealthTest.query.all()
        t_schema = ComHealthTestSchema(many=True)
        form = TestListForm()
        profile = ComHealthTestProfile.query.get(profile_id)
        action = url_for('comhealth.add_test_to_profile', profile_id=profile_id)
        return render_template('comhealth/test_menu.html',
                               tests=t_schema.dump(tests),
                               form=form,
                               action=action,
                               profile=profile)
    return redirect(url_for('comhealth.test_index'))


@comhealth.route('/test/profiles/<int:profile_id>/add-test', methods=['GET', 'POST'])
@login_required
def add_test_to_profile(profile_id):
    '''Add tests selected from the menu to be added to the profile.

    :param profile_id:
    :return:
    '''
    form = TestListForm()
    if form.validate_on_submit() and profile_id:
        data = form.test_list.data
        tests = json.loads(data)

        for test in tests:
            new_item = ComHealthTestItem(test_id=int(test['id']),
                                         price=float(test['default_price']), profile_id=profile_id)
            db.session.add(new_item)
        db.session.commit()
        flash('Test(s) have been added to the profile')
        return redirect(url_for('comhealth.test_profile', profile_id=profile_id))

    flash('Falied to add tests to the profile.')
    return redirect(url_for('comhealth.profile_test_menu', set_id=profile_id))


@comhealth.route('/test/profiles/<int:profile_id>')
@login_required
def test_profile(profile_id):
    '''Main Test Index with Profile, Group and Test tabs.

    :param profile_id:
    :return:
    '''
    profile = ComHealthTestProfile.query.get(profile_id)
    return render_template('comhealth/test_profile_edit.html', profile=profile)


@comhealth.route('/test/profiles/<int:profile_id>/save', methods=['GET', 'POST'])
@login_required
def save_test_profile(profile_id):
    '''Generates a form for editing the price of the test item.

    :param profile_id:
    :return:
    '''
    profile = ComHealthTestProfile.query.get(profile_id)
    if request.method == 'POST':
        for test in request.form:
            if test.startswith('test'):
                _, test_id = test.split('_')
                test_item = ComHealthTestItem.query.get(int(test_id))
                test_item.price = float(request.form.get(test))
                db.session.add(test_item)
                #print(test_item.test.name, test_item.price, request.form.get(test))
        if request.form.get('quote') == '':
            profile.quote = 0
        else:
            profile.quote = float(request.form.get('quote'))
        db.session.add(profile)
        db.session.commit()
    flash('Change has been saved.')
    return redirect(url_for('comhealth.test_profile', profile_id=profile_id))


@comhealth.route('/test/profiles/<int:profile_id>/tests/<int:item_id>/remove', methods=['GET', 'POST'])
@login_required
def remove_test_profile(profile_id, item_id):
    '''Delete the test item from the profile.

    :param profile_id:
    :return:
    '''
    profile = ComHealthTestProfile.query.get(profile_id)
    tests = [test for test in profile.test_items if test.id != item_id]
    profile.test_items = tests
    db.session.add(profile)
    db.session.commit()
    return redirect(url_for('comhealth.test_profile', profile_id=profile.id))


@comhealth.route('/test/tests/group/menu/<int:group_id>')
@login_required
def group_test_menu(group_id=None):
    '''Shows a menu of tests to be added to the profile.

    :param profile_id:
    :return:
    '''
    if group_id:
        tests = ComHealthTest.query.all()
        t_schema = ComHealthTestSchema(many=True)
        form = TestListForm()
        group = ComHealthTestGroup.query.get(group_id)
        action = url_for('comhealth.add_test_to_group', group_id=group_id)
        return render_template('comhealth/group_test_menu.html',
                               tests=t_schema.dump(tests),
                               form=form,
                               action=action,
                               group=group)
    return redirect(url_for('comhealth.test_index'))


@comhealth.route('/test/groups/<int:group_id>/add-test',
                 methods=['GET', 'POST'])
@login_required
def add_test_to_group(group_id):
    '''Add tests selected from the menu to be added to the group.

    :param group_id:
    :return:
    '''
    form = TestListForm()
    if form.validate_on_submit() and group_id:
        data = form.test_list.data
        tests = json.loads(data)

        for test in tests:
            new_item = ComHealthTestItem(test_id=int(test['id']),
                                         price=float(test['default_price']), group_id=group_id)
            db.session.add(new_item)
        db.session.commit()
        flash('Test(s) have been added to the group')
        return redirect(url_for('comhealth.test_group_index', group_id=group_id))

    flash('Falied to add tests to the group.')
    return redirect(url_for('comhealth.group_test_menu', set_id=group_id))


@comhealth.route('/test/groups/<int:group_id>/save', methods=['GET', 'POST'])
@login_required
def save_test_group(group_id):
    '''Generates a form for editing the price of the test item.

    :param group_id:
    :return:
    '''
    group = ComHealthTestProfile.query.get(group_id)
    for test in request.form:
        if test.startswith('test'):
            _, test_id = test.split('_')
            test_item = ComHealthTestItem.query.get(int(test_id))
            test_item.price = float(request.form.get(test))
            db.session.add(test_item)
    db.session.commit()
    flash('Change has been saved.')
    return redirect(url_for('comhealth.test_group_index', group_id=group_id))


@comhealth.route('/test/groups/<int:group_id>/tests/<int:item_id>/remove', methods=['GET', 'POST'])
@login_required
def remove_group_test_item(group_id, item_id):
    '''Delete the test item from the group.

    :param group_id:
    :return:
    '''
    group = ComHealthTestGroup.query.get(group_id)
    tests = [test for test in group.test_items if test.id != item_id]
    group.test_items = tests
    db.session.add(group)
    db.session.commit()
    return redirect(url_for('comhealth.test_group_index', group_id=group.id))


@comhealth.route('/test/tests')
@comhealth.route('/test/tests/<int:test_id>')
@login_required
def test_test_index(test_id=None):
    if test_id:
        test = ComHealthTest.query.get(test_id)
        # TODO: create the test_test_edit.html
        return render_template('comhealth/test_test_edit.html', test=test)

    tests = ComHealthTest.query.all()
    t_schema = ComHealthTestSchema(many=True)
    return render_template('comhealth/test_test.html',
                           tests=t_schema.dump(tests))


@comhealth.route('/test/tests/new', methods=['GET', 'POST'])
@login_required
def add_new_test():
    form = TestForm()
    containers = [(c.id, c.name) for c in ComHealthContainer.query.all()]
    form.container.choices = containers
    if form.validate_on_submit():
        new_test = ComHealthTest(
            code=form.code.data,
            name=form.name.data,
            desc=form.desc.data,
            default_price=form.default_price.data,
            container=form.container.data
        )
        db.session.add(new_test)
        db.session.commit()
        flash('New test added successfully.')
        return redirect(url_for('comhealth.test_test_index'))
    return render_template('comhealth/new_test.html',
                           form=form)


@comhealth.route('/test/tests/edit/<int:test_id>', methods=['GET', 'POST'])
@login_required
def edit_test(test_id):
    test = ComHealthTest.query.get(test_id)
    form = TestForm(obj=test)
    if form.validate_on_submit():
        form.populate_obj(test)
        db.session.add(test)
        db.session.commit()
        flash('แก้ไขข้อมูลเรียบร้อยแล้ว', 'success')
        return redirect(url_for('comhealth.test_test_index'))
    return render_template('comhealth/edit_test.html', form=form)


@comhealth.route('/services/new', methods=['GET', 'POST'])
@login_required
def add_service():
    form = ServiceForm()
    if form.validate_on_submit():
        new_service = ComHealthService(location=form.location.data, date=form.service_date.data)
        db.session.add(new_service)
        db.session.commit()
        flash('The schedule has been updated.')
        return redirect(url_for('comhealth.index'))

    return render_template('comhealth/new_schedule.html', form=form)


@comhealth.route('/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_service(service_id=None):
    if service_id:
        service = ComHealthService.query.get(service_id)
        return render_template('comhealth/edit_service.html', service=service)


@comhealth.route('/services/profiles/<int:service_id>')
@comhealth.route('/services/profiles/<int:service_id>/<int:profile_id>')
@login_required
def add_service_profile(service_id=None, profile_id=None):
    if not (service_id and profile_id):
        service = ComHealthService.query.get(service_id)
        profiles = [pf for pf in ComHealthTestProfile.query.all() if pf not in service.profiles]
        return render_template('comhealth/profile_list.html',
                               profiles=profiles,
                               service=service)

    service = ComHealthService.query.get(service_id)
    profile = ComHealthTestProfile.query.get(profile_id)
    service.profiles.append(profile)
    db.session.add(service)
    db.session.commit()
    flash(u'Profile {} has been added to the service.'.format(profile.name))
    return redirect(url_for('comhealth.edit_service', service_id=service.id))


@comhealth.route('/services/profiles/delete/<int:service_id>/<int:profile_id>')
@login_required
def delete_service_profile(service_id=None, profile_id=None):
    if service_id and profile_id:
        service = ComHealthService.query.get(service_id)
        kept_profiles = []
        for profile in service.profiles:
            if profile.id != profile_id:
                kept_profiles.append(profile)
            else:
                flash(u'Profile {} has been removed from the service.'.format(profile.name))

        service.profiles = kept_profiles
        db.session.add(service)
        db.session.commit()

    return redirect(url_for('comhealth.edit_service', service_id=service.id))


@comhealth.route('/services/groups/<int:service_id>')
@comhealth.route('/services/groups/<int:service_id>/<int:group_id>')
@login_required
def add_service_group(service_id=None, group_id=None):
    if not (service_id and group_id):
        service = ComHealthService.query.get(service_id)
        groups = [gr for gr in ComHealthTestGroup.query.all() if gr not in service.groups]
        return render_template('comhealth/group_list.html',
                               groups=groups,
                               service=service)

    service = ComHealthService.query.get(service_id)
    group = ComHealthTestGroup.query.get(group_id)
    service.groups.append(group)
    db.session.add(service)
    db.session.commit()
    flash(u'Group {} has been added to the service.'.format(group.name))
    return redirect(url_for('comhealth.edit_service', service_id=service.id))


@comhealth.route('/services/groups/delete/<int:service_id>/<int:group_id>')
@login_required
def delete_service_group(service_id=None, group_id=None):
    if service_id and group_id:
        service = ComHealthService.query.get(service_id)
        kept_groups = []
        for group in service.groups:
            if group.id != group_id:
                kept_groups.append(group)
            else:
                flash(u'Group {} has been removed to the service.'.format(group.name))
        service.groups = kept_groups
        db.session.add(service)
        db.session.commit()

    return redirect(url_for('comhealth.edit_service', service_id=service.id))


@comhealth.route('/services/<int:service_id>/specimens-summary')
@login_required
def summarize_specimens(service_id):
    containers = set()
    service = ComHealthService.query.get(service_id)

    valid_records = ComHealthRecord.query.filter(
        ComHealthRecord.service_id == service_id,
        ComHealthRecord.labno != ''
    ).all()

    for record in valid_records:
        for test_item in record.ordered_tests:
            if test_item.test and test_item.test.container:
                containers.add(test_item.test.container)

    columns = [{'data': 'labno', 'searchable': True}]
    headers = []
    for ct in sorted(containers, key=lambda x: x.name):
        columns.append({'data': ct.id})
        headers.append(ct)

    return render_template('comhealth/specimens_checklist.html',
                           summary_date=datetime.now(tz=bangkok),
                           columns=columns,
                           headers=headers,
                           service=service)


@comhealth.route('/api/services/<int:service_id>/specimens-summary')
@login_required
def get_specimens_summary_data(service_id):
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    service = ComHealthService.query.get(service_id)
    query = service.records.filter(ComHealthRecord.labno != '')
    total_count = query.count()
    search = request.args.get('search[value]')
    if search:
        query = query.filter(ComHealthRecord.labno.like('%{}%'.format(search)))

    containers = set()
    for profile in service.profiles:
        for test_item in profile.test_items:
            containers.add(test_item.test.container)
    for group in service.groups:
        for test_item in group.test_items:
            containers.add(test_item.test.container)

    data = []
    for rec in query.order_by('labno').offset(start).limit(length):
        if rec.labno:
            d = {'labno': rec.labno}
            for ct in containers:
                if ct.name in rec.container_set:
                    d[
                        str(ct.id)] = '''<td><span class="icon"><i class="fa-solid fa-circle-check has-text-success"></i></span></td>'''
                else:
                    d[str(ct.id)] = None
            data.append(d)
    return jsonify({'data': data,
                    'recordsFiltered': query.count(),
                    'recordsTotal': total_count,
                    'draw': request.args.get('draw', type=int),
                    })


@comhealth.route('/services/<int:service_id>/containers/<int:container_id>/check_multi_container', methods=['POST'])
@login_required
def check_multi_container(service_id, container_id):
    service = ComHealthService.query.get(service_id)
    labno_a = request.form.get('labno_a')
    labno_b = request.form.get('labno_b')
    if labno_a.isnumeric() and labno_b.isnumeric():
        if int(labno_a) < int(labno_b):
            for x in range(int(labno_a), int(labno_b) + 1):
                labno = u'{}{}{}2{}'.format(str(service.date.year)[-1], f'{int(service.date.month):02n}',
                                            f'{int(service.date.day):02n}', f'{x:04n}')
                record = ComHealthRecord.query.filter_by(labno=labno).first()
                if record:
                    containers = set([item.test.container for item in record.ordered_tests])
                    for cts in containers:
                        if cts.id == container_id:
                            checkin_record = ComHealthSpecimensCheckinRecord.query \
                                .filter_by(record_id=record.id, container_id=container_id).first()
                            if checkin_record:
                                checkin_record.checkin_datetime = datetime.now(tz=bangkok)
                                db.session.add(checkin_record)
                                db.session.commit()
                            else:
                                checkin_record = ComHealthSpecimensCheckinRecord(
                                    record.id, container_id, datetime.now(tz=bangkok))
                                record.container_checkins.append(checkin_record)
                                db.session.add(record)
                                db.session.commit()
    return redirect(url_for('comhealth.list_tests_in_container', service_id=service_id, container_id=container_id))


@comhealth.route('/services/<int:service_id>/containers/<int:container_id>',
                 methods=['GET', 'POST'])
@login_required
def list_tests_in_container(service_id, container_id):
    if request.method == 'POST':
        specimens_no = request.form.get('specimens_no')
        labno = u'{}{}'.format(str(datetime.today().year)[-1], specimens_no[3:])
        record = ComHealthRecord.query.filter_by(labno=labno).first()
        if record:
            checkin_record = ComHealthSpecimensCheckinRecord.query.filter_by(record_id=record.id,
                                                                             container_id=container_id).first()
            if checkin_record:
                checkin_record.checkin_datetime = datetime.now(tz=bangkok)
                db.session.add(checkin_record)
                db.session.commit()
                flash("The container's check in has been updated.", 'success')
            else:
                record.container_checkins.append(ComHealthSpecimensCheckinRecord(
                    record.id, container_id, datetime.now(tz=bangkok)))
                db.session.add(record)
                db.session.commit()
                flash('The container has been checked in.', 'success')
        else:
            flash('The lab number is not valid or it no longer exists.', 'danger')

    tests = defaultdict(list)
    service = ComHealthService.query.get(service_id)
    if service:
        # TODO: refactor the code to reduce load time
        container = ComHealthContainer.query.get(container_id)
        checked_in_records = ComHealthRecord.query.filter(
            and_(ComHealthRecord.service_id == service.id,
                 ComHealthRecord.checkin_datetime != None)).all()
        checked_in_records = set([c.id for c in checked_in_records])
        test_items = ComHealthTestItem.query.join(test_item_record_table) \
            .filter(and_(ComHealthTestItem.test.has(container_id=container_id),
                         test_item_record_table.c.record_id.in_(checked_in_records))).all()
        checkincount = 0
        for test_item in test_items:
            for rec in test_item.records:
                if rec.id in checked_in_records:
                    tests[rec].append(test_item.test.code)
        records = sorted(tests.keys(), key=lambda x: x.labno)
        for rec1 in records:
            if rec1.get_container_checkin(container.id):
                checkincount += 1
    else:
        flash('The service no longer exists.', 'danger')
    return render_template('comhealth/container_tests.html',
                           records=records, tests=tests,
                           service=service, container=container, labnocount=len(records), checkincount=checkincount)


@comhealth.route('/services/<int:service_id>/records/<int:record_id>/containers/<int:container_id>/check')
@login_required
def check_container(service_id, record_id, container_id):
    checkin_record = ComHealthSpecimensCheckinRecord.query \
        .filter_by(record_id=record_id, container_id=container_id).first()
    if checkin_record:
        checkin_record.checkin_datetime = datetime.now(tz=bangkok)
        db.session.add(checkin_record)
        db.session.commit()
    else:
        record = ComHealthRecord.query.get(record_id)
        if record:
            record.container_checkins.append(ComHealthSpecimensCheckinRecord(
                record.id, container_id, datetime.now(tz=bangkok)))
            db.session.add(record)
            db.session.commit()
            flash('The container has been checked in.', 'success')
        else:
            flash('The record no longer exists.', 'danger')
    return redirect(url_for('comhealth.list_tests_in_container',
                            service_id=service_id, container_id=container_id))


@comhealth.route('/services/<int:service_id>/records/<int:record_id>/containers/<int:container_id>/uncheck')
@login_required
def uncheck_container(service_id, record_id, container_id):
    checkin_record = ComHealthSpecimensCheckinRecord.query \
        .filter_by(record_id=record_id, container_id=container_id).first()
    if checkin_record:
        checkin_record.checkin_datetime = datetime.now(tz=bangkok)
        db.session.delete(checkin_record)
        db.session.commit()
        flash('The container has been unchecked.', 'success')
    else:
        flash('The record no longer exists.', 'warning')
    return redirect(url_for('comhealth.list_tests_in_container',
                            service_id=service_id, container_id=container_id))


@comhealth.route('/services/<int:service_id>/containers/<int:container_id>/scan', methods=['GET', 'POST'])
@login_required
def scan_container(service_id, container_id):
    container = ComHealthContainer.query.get(container_id)
    service = ComHealthService.query.get(service_id)
    recents = ComHealthSpecimensCheckinRecord.query \
        .filter(ComHealthSpecimensCheckinRecord.container.has(id=container_id)) \
        .filter(ComHealthSpecimensCheckinRecord.record.has(service_id=service_id)) \
        .order_by(ComHealthSpecimensCheckinRecord.checkin_datetime.desc())
    check_is_container = 0
    if request.method == 'POST':
        specimens_no = request.form.get('specimens_no')
        labno = u'{}{}'.format(str(datetime.today().year)[-1], specimens_no[-9:])
        record = ComHealthRecord.query.filter_by(labno=labno).first()
        if record:
            containers = set([item.test.container for item in record.ordered_tests])
            for cts in containers:
                if cts.id == container_id:
                    checkin_record = ComHealthSpecimensCheckinRecord.query \
                        .filter_by(record_id=record.id, container_id=container_id).first()
                    if checkin_record:
                        checkin_record.checkin_datetime = datetime.now(tz=bangkok)
                        db.session.add(checkin_record)
                        db.session.commit()
                    else:
                        checkin_record = ComHealthSpecimensCheckinRecord(
                            record.id, container_id, datetime.now(tz=bangkok))
                        record.container_checkins.append(checkin_record)
                        db.session.add(record)
                        db.session.commit()
                    return render_template('comhealth/scan_container.html', service=service,
                                           container=container, specimens_no=specimens_no,
                                           checkin_record=checkin_record, recents=recents[:5])
                    check_is_container = 1
                    break
            if check_is_container == 0:
                flash(specimens_no + ' The container no longer exists.', 'danger')
        else:
            flash(specimens_no + '  no register.', 'danger')

    return render_template('comhealth/scan_container.html', service=service, container=container, recents=recents[:5])


@comhealth.route('/organizations')
@login_required
def list_orgs():
    org_schema = ComHealthOrgSchema(many=True)
    orgs = ComHealthOrg.query.all()
    return render_template('comhealth/org_list.html',
                           orgs=org_schema.dump(orgs))


@comhealth.route('/services/add-to-org/<int:org_id>', methods=['GET', 'POST'])
@login_required
def add_service_to_org(org_id):
    form = ServiceForm()
    org = ComHealthOrg.query.get(org_id)
    if form.validate_on_submit():
        existing_service = ComHealthService.query \
            .filter_by(date=form.service_date.data, location=form.location.data).first()
        if not existing_service:
            new_service = ComHealthService(date=form.service_date.data,
                                           location=form.location.data)
            db.session.add(new_service)
            for employee in org.employees:
                new_record = ComHealthRecord(date=form.service_date.data,
                                             service=new_service,
                                             customer=employee)
                db.session.add(new_record)
            db.session.commit()
        else:
            for employee in org.employees:
                services = set([rec.service for rec in employee.records])
                if existing_service not in services:
                    new_record = ComHealthRecord(date=form.service_date.data,
                                                 service=existing_service,
                                                 customer=employee)
                    db.session.add(new_record)
                    db.session.commit()

        flash('New service has been added to the organization.')
        return redirect(url_for('comhealth.index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash('{} {}'.format(field, error))
    return render_template('comhealth/new_schedule.html',
                           form=form, org=org)


@comhealth.route('/services/<int:service_id>/add-new-customer/<int:org_id>', methods=['GET', 'POST'])
@login_required
def add_customer_to_service_org(service_id, org_id):
    form = CustomerForm()
    form.emptype.choices = [(e.id, e.name) for e in ComHealthCustomerEmploymentType.query.all()]
    if form.validate_on_submit():
        service_id = form.service_id.data
        org_id = form.org_id.data
        if form.dob.data:
            d, m, y = form.dob.data.split('/')
            dob = date(int(y) - 543, int(m), int(d))  # convert to Thai Buddhist year
        else:
            dob = None
        customer = ComHealthCustomer(title=form.title.data,
                                     firstname=form.firstname.data,
                                     lastname=form.lastname.data,
                                     gender=form.gender.data,
                                     emptype_id=form.emptype.data,
                                     phone=form.phone.data,
                                     dob=dob,
                                     emp_id=form.emp_id.data,
                                     email=form.email.data,
                                     dept=form.dept.data,
                                     division=form.division.data,
                                     unit=form.unit.data,
                                     org_id=org_id)
        new_record = ComHealthRecord(service_id=service_id, customer=customer)
        db.session.add(customer)
        db.session.add(new_record)
        db.session.commit()
        customer.generate_hn()
        db.session.add(customer)
        db.session.commit()
        flash('New customer has been added to the database and service.')
        return redirect(url_for('comhealth.display_service_customers', service_id=service_id))
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash('{} {}'.format(field, err))

    if service_id and org_id:
        form.service_id.default = service_id
        form.org_id.default = org_id
        form.process()
        return render_template('comhealth/new_customer_service_org.html', form=form)


@comhealth.route('/orgs/<int:org_id>/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee(org_id):
    form = CustomerForm()
    form.emptype.choices = [(e.id, e.name) for e in ComHealthCustomerEmploymentType.query.all()]
    if request.method == 'POST':
        if form.validate_on_submit():
            customer = ComHealthCustomer()
            customer.org_id = org_id
            customer.firstname = form.firstname.data
            customer.lastname = form.lastname.data
            customer.title = form.title.data
            customer.phone = form.phone.data
            customer.emptype_id = form.emptype.data
            try:
                day, month, year = form.dob.data.split('/')
            except ValueError:
                flash(u'รูปแบบวันที่ไม่ถูกต้อง', 'warning')
                return render_template('comhealth/edit_customer_data.html', form=form)

            year = int(year) - 543
            month = int(month)
            day = int(day)
            try:
                customer.dob = datetime(year, month, day)
            except ValueError:
                flash(u'วันที่ไม่ถูกต้อง', 'warning')
                return render_template('comhealth/edit_customer_data.html', form=form)
            customer.emp_id = form.emp_id.data
            customer.gender = form.gender.data
            customer.email = form.email.data
            customer.dept = form.dept.data
            customer.division = form.division.data
            customer.unit = form.unit.data
            db.session.add(customer)
            db.session.commit()
            return redirect(request.args.get('next'))
        else:
            flash(form.errors, 'warning')
    return render_template('comhealth/new_customer_service_org.html', form=form)


@comhealth.route('/note/<int:record_id>/edit', methods=['GET', 'POST'])
def edit_note_data(record_id):
    record = ComHealthRecord.query.get(record_id)
    if request.method == 'POST':
        record.note = request.form.get('note')
        db.session.add(record)
        db.session.commit()
        return redirect(
            request.args.get('next', url_for('comhealth.get_services_customers', service_id=record.service_id)))
    return render_template('comhealth/edit_note.html', record=record)


@comhealth.route('/customers/<int:customer_id>/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def edit_customer_data(customer_id, service_id):
    form = CustomerForm()
    customer = ComHealthCustomer.query.get(customer_id)
    form.emptype.choices = [(e.id, e.name) for e in ComHealthCustomerEmploymentType.query.all()]
    if customer:
        if request.method == 'POST':
            if form.validate_on_submit():
                customer.firstname = form.firstname.data
                customer.lastname = form.lastname.data
                customer.title = form.title.data
                customer.phone = form.phone.data
                customer.emptype_id = form.emptype.data
                try:
                    day, month, year = form.dob.data.split('/')
                except ValueError:
                    flash(u'รูปแบบวันที่ไม่ถูกต้อง', 'warning')
                    return render_template('comhealth/edit_customer_data.html', form=form)

                year = int(year) - 543
                month = int(month)
                day = int(day)
                try:
                    customer.dob = datetime(year, month, day)
                except ValueError:
                    flash(u'วันที่ไม่ถูกต้อง', 'warning')
                    return render_template('comhealth/edit_customer_data.html', form=form)
                customer.gender = form.gender.data
                customer.email = form.email.data
                customer.emp_id = form.emp_id.data

                customer.dept = form.dept.data
                customer.division = form.division.data
                customer.unit = form.unit.data
                db.session.add(customer)
                db.session.commit()
                return redirect(url_for('comhealth.display_service_customers', service_id=service_id))
        else:
            form.firstname.data = customer.firstname
            form.lastname.data = customer.lastname
            form.title.data = customer.title
            form.phone.data = customer.phone
            form.emptype.data = customer.emptype_id
            if customer.dob:
                buddhist_year = customer.dob.year + 543
                month = customer.dob.month
                day = customer.dob.day
                form.dob.data = datetime(buddhist_year, month, day).strftime('%d/%m/%Y')
            form.gender.data = customer.gender
            form.email.data = customer.email
            form.emp_id.data = customer.emp_id
            form.dept.data = customer.dept
            form.division.data = customer.division
            form.unit.data = customer.unit

    else:
        flash('Customer not found.', 'warning')
        return redirect(request.args.get('next'))
    return render_template('comhealth/edit_customer_data.html', form=form, customer=customer)


# TODO: export the price of tests

@comhealth.route('/services/<int:service_id>/to-csv')
@login_required
def export_csv(service_id):
    # TODO: add employment types (number)
    # TODO: add organization + dept + unit
    service = ComHealthService.query.get(service_id)
    rows = []
    for record in service.records:
        if not record.labno:
            continue
        tests = ','.join([item.test.code for item in record.ordered_tests])
        department = record.customer.dept.name if record.customer.dept else ''
        emptype = record.customer.emptype.name if record.customer.emptype else ''
        reason = record.finance_contact.reason if record.finance_contact else ''
        division = record.customer.division.name if record.customer.division else ''
        rows.append({'hn': u'{}'.format(record.customer.hn or ''),
                     'title': u'{}'.format(record.customer.title),
                     'firstname': u'{}'.format(record.customer.firstname),
                     'lastname': u'{}'.format(record.customer.lastname),
                     'employmentType': u'{}'.format(emptype),
                     'age': u'{}'.format(record.customer.age_years or ''),
                     'gender': u'{}'.format(record.customer.gender),
                     'phone': u'{}'.format(record.customer.phone),
                     'organization': u'{}'.format(record.customer.org.name),
                     'department': u'{}'.format(department),
                     'division': u'{}'.format(division),
                     'unit': u'{}'.format(record.customer.unit),
                     'labno': u'{}'.format(record.labno),
                     'tests': u'{}'.format(tests),
                     'urgent': record.urgent,
                     'note_to_lab': u'{}'.format(record.comment),
                     'employment_note': u'{}'.format(record.note),
                     'finance_contact': u'{}'.format(reason),
                     'checkin_datetime': u'{}'.format(record.checkin_datetime)})
    if rows:
        pd.DataFrame(rows).to_excel('export.xlsx',
                                    header=True,
                                    columns=['labno',
                                             'hn',
                                             'title',
                                             'firstname',
                                             'lastname',
                                             'age',
                                             'gender',
                                             'phone',
                                             'organization',
                                             'department',
                                             'division',
                                             'unit',
                                             'employmentType',
                                             'tests',
                                             'urgent',
                                             'note_to_lab',
                                             'employment_note',
                                             'finance_contact',
                                             'checkin_datetime'],
                                    index=False,
                                    encoding='utf-8')
        return send_from_directory(os.getcwd(), path='export.xlsx')
    else:
        return 'Data is empty.'


@comhealth.route('/organizations/add', methods=['GET', 'POST'])
@login_required
def add_org():
    name = request.form.get('name', '')
    if name:
        org_ = ComHealthOrg.query.filter_by(name=name).first()
        if org_:
            return 'Organization exists!'
        else:
            new_org = ComHealthOrg(name=name)
            db.session.add(new_org)
            db.session.commit()
            return redirect(url_for('comhealth.list_orgs'))
    return 'No name found.'


@comhealth.route('/organizations/<int:orgid>/employees', methods=['GET', 'POST'])
@login_required
def list_employees(orgid):
    if orgid:
        org = ComHealthOrg.query.get(orgid)
        customer_schema = ComHealthCustomerSchema(many=True)
        return render_template('comhealth/employees.html',
                               employees=customer_schema.dump(org.employees),
                               org=org)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@comhealth.route('/organizations/<int:orgid>/employees/info', methods=['POST', 'GET'])
@login_required
def add_employee_info(orgid):
    """Add employees info from a file.
    """

    org = ComHealthOrg.query.get(orgid)
    info_items = ComHealthCustomerInfoItem.query.all()
    info_items = set([item.text for item in info_items])

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file alert')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            df = read_excel(file)
            for idx, rec in df.iterrows():
                rec = rec.fillna('')
                data = {}
                for col in rec.keys():
                    if col in info_items:
                        data[col] = rec[col]

                customer = ComHealthCustomer.query \
                    .filter_by(firstname=rec['firstname'], lastname=rec['lastname']).first()
                if not customer:
                    dept = None
                    emptype = None
                    if rec['department']:
                        existing_dept = ComHealthDepartment.query.filter_by(name=rec['department']).first()
                        if existing_dept:
                            dept = existing_dept
                        else:
                            dept = ComHealthDepartment(name=rec['department'], parent_id=orgid)
                    if rec['employmentType']:
                        existing_emptype = ComHealthCustomerEmploymentType.query \
                            .filter_by(name=rec['employmentType']).first()
                        if existing_emptype:
                            emptype = existing_emptype
                        else:
                            emptype = ComHealthCustomerEmploymentType(name=rec['employmentType'])
                    customer = ComHealthCustomer(
                        title=rec['title'],
                        firstname=rec['firstname'],
                        lastname=rec['lastname'],
                        org_id=orgid,
                        dept=dept,
                        gender=rec['gender'],
                        phone=rec['phone'],
                        emptype=emptype,
                        unit=rec['unit'],
                    )
                    db.session.add(customer)
                    db.session.commit()
                    customer.generate_hn()

                if not customer.info:
                    info = ComHealthCustomerInfo(
                        customer=customer,
                        data=data,
                        updated_at=datetime.now(tz=bangkok)
                    )
                    db.session.add(info)
                else:
                    customer.info.data = data
                db.session.add(customer)
                db.session.commit()
        return redirect(url_for('comhealth.list_employees', orgid=org.id))

    return render_template('comhealth/employee_info_upload.html', org=org)


@comhealth.route('/organizations/employees/info/<int:custid>',
                 methods=["POST", "GET"])
@login_required
def show_employee_info(custid):
    info_items = ComHealthCustomerInfoItem.query.all()
    info_items = [(it.text, it) for it in info_items]
    info_items = OrderedDict(sorted(info_items, key=lambda x: x[1].order))

    if request.method == 'GET':
        if not custid:
            flash('No customer ID specified.')
            return redirect(request.referrer)

        customer = ComHealthCustomer.query.get(custid)
        if customer:
            if not customer.info:
                info = ComHealthCustomerInfo(customer=customer, data={})
                db.session.add(info)
                db.session.commit()
            return render_template('comhealth/employee_info_update.html',
                                   info_items=info_items,
                                   customer=customer)
        else:
            flash('Customer with ID={} does not exist.'.format(customer.id))
            return redirect(request.referrer)

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        email = request.form.get('email')
        if customer_id:
            customer = ComHealthCustomer.query.get(int(customer_id))
            customer.email = email
            for k, item in info_items.items():
                if not item.multiple_selection:
                    customer.info.data[k] = request.form.get(k)
                else:
                    values = ' '.join(request.form.getlist(k))
                    customer.info.data[k] = values
            customer.info.updated_at = datetime.now(tz=bangkok)
            flag_modified(customer.info, "data")
            db.session.add(customer)
            db.session.commit()
        else:
            flash('Customer ID not found.')
        kiosk_mode = request.args.get('kiosk_mode', 'no')
        if kiosk_mode == 'yes':
            return redirect(url_for('comhealth.employee_kiosk_mode'))
        return redirect(url_for('comhealth.list_employees', orgid=customer.org.id))

def convert_date(date_data):
    if isna(date_data):
        return None

    # ขั้นตอนที่ 1: ดึงส่วนประกอบของวันที่ (วัน, เดือน, ปี) ออกมา ไม่ว่าจะเป็น datetime object หรือ string
    if isinstance(date_data, datetime):
        parsed_day = date_data.day
        parsed_month = date_data.month
        parsed_year = date_data.year
    else:
        try:
            parts = str(date_data).split('/')
            if len(parts) == 3:
                parsed_day, parsed_month, parsed_year = map(int, parts)
            else:
                return None
        except (ValueError, TypeError):
            return None

    # ถ้าไม่สามารถแยกส่วนประกอบของวันที่ได้ (เช่น parsed_day ยังคงเป็น None)
    if parsed_day is None or parsed_month is None or parsed_year is None:
        return None

    # ขั้นตอนที่ 2: ตรวจสอบและแปลงปีพุทธศักราชเป็นคริสต์ศักราช
    if parsed_year > 2300:
        year_gregorian = parsed_year - 543
    else:
        year_gregorian = parsed_year # ถือว่าเป็นปีคริสต์ศักราชอยู่แล้ว

    # ขั้นตอนที่ 3: (Optional) ตรวจสอบความสมเหตุสมผลของปีคริสต์ศักราชที่ได้
    current_year = datetime.now().year
    if not (1900 <= year_gregorian <= current_year + 10):
        return None

    try:
        return date(year_gregorian, parsed_month, parsed_day)
    except ValueError:
        # กรณีวันที่ไม่ถูกต้อง เช่น 31 ก.พ. หรือ เดือนที่ไม่มีอยู่
        return None

@comhealth.route('/organizations/<int:orgid>/employees/addmany', methods=['GET', 'POST'])
@login_required
def add_many_employees(orgid):
    # TODO: All new customer needs to have their HN generated.
    """Add employees from Excel file.

    Note that the birthdate is in Thai year and in dd/mm/yyyy.
    The columns are title, first name, last name, dob, and gender
    A record with no first name and last name is skipped.
    :type orgid: int
    """
    org = ComHealthOrg.query.get(orgid)

    if request.method == 'POST':
        labno_included = request.form.get('labno_included')
        if 'file' not in request.files:
            flash('No file alert')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)

        messages = []  # สำหรับเก็บข้อความแจ้งเตือนทั้งหมด
        new_customer_count = 0
        updated_customer_count = 0
        skipped_row_count = 0

        if file and allowed_file(file.filename):
            df = read_excel(file, dtype='object')
            for idx, rec in df.iterrows():
                row_number = idx + 2  # แถวใน Excel (สมมติว่ามี Header)
                row_messages = []  # ข้อความสำหรับแถวปัจจุบัน

                try:
                    title, firstname, lastname, dob, gender, emp_id, department_name, division_name, unit, emptype_name, phone = rec
                except ValueError:
                    row_messages.append(f"แถวที่ {row_number}: จำนวนคอลัมน์ไม่ถูกต้อง (คาดว่ามี 11 คอลัมน์)")
                    messages.append({"type": "error", "message": "; ".join(row_messages)})
                    skipped_row_count += 1
                    continue

                if isna(firstname):
                    firstname = None
                if isna(lastname):
                    lastname = None
                if isna(firstname) and isna(lastname):
                    continue
                if isna(unit):
                    unit = None
                if isna(emp_id):
                    emp_id = None
                if isna(phone):
                    phone = None



                if not isna(department_name):
                    department = ComHealthDepartment.query.filter_by(parent_id=orgid, name=department_name).first()
                    if not department:
                        department = ComHealthDepartment(parent_id=orgid, name=department_name)
                        division = ComHealthDivision(parent=department, name=division_name)
                        db.session.add(department)
                        db.session.add(division)
                    else:
                        if not isna(division_name):
                            division = ComHealthDepartment.query.filter_by(parent=department,
                                                                           name=division_name).first()
                            if not division:
                                division = ComHealthDivision(parent_id=department.id, name=division_name)
                                db.session.add(division)
                        else:
                            division = None
                else:
                    department = None
                    division = None

                # emptype_name (ประเภทการจ้างงาน): ค้นหาเท่านั้น, แจ้งเตือนหากไม่พบ
                emptype = None
                if not isna(emptype_name) and str(emptype_name).strip():
                    emptype_name_str = str(emptype_name).strip()
                    emptype = ComHealthCustomerEmploymentType.query.filter_by(name=emptype_name_str).first()
                    if not emptype:
                        row_messages.append(f"ไม่พบประเภทการจ้างงาน '{emptype_name_str}' ในระบบ - จะไม่ถูกบันทึก")
                        # ไม่มีการ db.session.add(emptype) ที่นี่ตามคำขอ

                parsed_phone = None
                if not isna(phone):
                    parsed_phone = str(phone).strip()
                    if parsed_phone and not parsed_phone.startswith('0'):
                        parsed_phone = '0' + parsed_phone

                # dob (วันเกิด): แปลงและตรวจสอบรูปแบบ
                parsed_dob = convert_date(dob)
                if parsed_dob is None and not isna(dob):
                    row_messages.append(
                        f"วันเกิด '{dob}' มีรูปแบบไม่ถูกต้อง (คาดหวัง dd/mm/yyyy) - จะถูกตั้งค่าเป็นว่าง")

                parsed_gender = None
                if not isna(gender):
                    try:
                        parsed_gender = int(gender)
                    except ValueError:
                        row_messages.append(f"เพศ '{gender}' มีรูปแบบไม่ถูกต้อง (คาดหวังตัวเลข) - จะถูกตั้งค่าเป็นว่าง")


                customer_ = ComHealthCustomer.query.filter_by(firstname=firstname,
                                                              lastname=lastname,
                                                              org=org).first()

                if not customer_:
                    # สร้างผู้รับบริการใหม่
                    try:
                        new_customer = ComHealthCustomer(
                            title=title,
                            firstname=firstname,
                            lastname=lastname,
                            dob=parsed_dob,
                            org=org,
                            gender=parsed_gender,
                            emp_id=emp_id,
                            dept=department,
                            division=division,
                            unit=unit,
                            emptype=emptype,
                            phone=parsed_phone
                        )
                        db.session.add(new_customer)
                        db.session.commit()  # Commit ครั้งแรกเพื่อให้ได้ ID สำหรับ generate_hn
                        new_customer.generate_hn()  # สร้าง HN
                        db.session.add(new_customer)  # เพิ่มเข้า session อีกครั้งหลังจากแก้ไข HN
                        db.session.commit()
                        new_customer_count += 1
                        #row_messages.append(f"เพิ่มผู้รับบริการใหม่สำเร็จ")
                    except Exception as e:
                        db.session.rollback()  # หากเกิดข้อผิดพลาด ให้ Rollback การเปลี่ยนแปลง
                        row_messages.append(f"ไม่สามารถเพิ่มผู้รับบริการใหม่ได้: {e}")
                        skipped_row_count += 1
                else:
                    # อัปเดตผู้รับบริการที่มีอยู่
                    try:
                        print(parsed_phone)
                        customer_.title = title if title is not None else customer_.title
                        customer_.dob = parsed_dob if parsed_dob is not None else customer_.dob
                        customer_.gender = parsed_gender if parsed_gender is not None else customer_.gender
                        customer_.emp_id = emp_id if emp_id is not None else customer_.emp_id  # ใช้ emp_id ที่อ่านมาโดยไม่มีการตรวจสอบซ้ำซ้อน
                        customer_.dept = department if department is not None else customer_.dept
                        customer_.division = division if division is not None else customer_.division
                        customer_.unit = unit if unit is not None else customer_.unit
                        customer_.emptype = emptype if emptype is not None else customer_.emptype
                        customer_.phone = parsed_phone if parsed_phone is not None else customer_.phone
                        db.session.add(customer_)
                        db.session.commit()
                        updated_customer_count += 1
                        #row_messages.append(f"อัปเดตข้อมูลพนักงานที่มีอยู่สำเร็จ")
                    except Exception as e:
                        db.session.rollback()  # หากเกิดข้อผิดพลาด ให้ Rollback การเปลี่ยนแปลง
                        row_messages.append(f"ไม่สามารถอัปเดตข้อมูลผู้รับบริการได้: {e}")
                        skipped_row_count += 1

                # รวบรวมข้อความสำหรับแถวนี้
                if row_messages:
                    # กำหนด type ของ message หลักตามสถานะการประมวลผล
                    if any(msg_part in ";".join(row_messages) for msg_part in["ไม่สามารถบันทึก", "ไม่สามารถเพิ่ม", "ไม่สามารถอัปเดต"]):
                        msg_type = "error"
                    elif any(msg_part in ";".join(row_messages) for msg_part in["มีรูปแบบไม่ถูกต้อง", "ไม่พบประเภทการจ้างงาน", "จำนวนคอลัมน์ไม่ครบถ้วน"]):
                        msg_type = "warning"
                    elif "สร้าง" in ";".join(row_messages):
                        msg_type = "info"
                    else:
                        msg_type = "success"

                    messages.append({"type": msg_type, "message": f"แถวที่ {row_number}: {'; '.join(row_messages)}"})

                    # Flash ข้อความทั้งหมดหลังจากประมวลผลไฟล์เสร็จสิ้น
            for msg in messages:
                    flash(msg["message"], msg["type"])

            flash(f"--- สรุปผลการนำเข้าข้อมูล ---", 'info')
            flash(f"เพิ่มผู้รับบริการ: {new_customer_count} คน", 'success')
            flash(f"อัปเดตข้อมูลผู้รับบริการ: {updated_customer_count} คน", 'success')
            flash(f"ข้ามการประมวลผล: {skipped_row_count} แถว (โปรดดูรายละเอียดในข้อความแจ้งเตือนด้านบน)", 'warning')

            return render_template('comhealth/employee_upload.html', org=org)

    return render_template('comhealth/employee_upload.html', org=org)


@comhealth.route('/organizations/mudt/employees', methods=['GET', 'POST'])
@login_required
def search_employees():
    df = read_excel('app/static/data/mudt2019.xls')
    data = []
    for idx, rec in df.iterrows():
        item = {
            'id': idx,
            'no': rec[0],
            'firstname': rec.firstname,
            'lastname': rec.lastname,
            'dob': rec.dob
        }
        data.append(item)
    return render_template('comhealth/search_employees.html', employees=data, org=u'การเคหะแห่งชาติ')


@comhealth.route('/checkin/<int:record_id>/receipts', methods=['GET', 'POST'])
@login_required
def list_all_receipts(record_id):
    record = ComHealthRecord.query.get(record_id)
    return render_template('comhealth/receipts.html', record=record)


@comhealth.route('/checkin/records/<int:record_id>/receipts', methods=['POST', 'GET'])
@login_required
def create_receipt(record_id):
    if request.method == 'GET':
        record = ComHealthRecord.query.get(record_id)
        customer_age = record.customer.age.years if record.customer.age else 0

        ref_profile = ComHealthReferenceTestProfile.query. \
            filter(ComHealthReferenceTestProfile.profile. \
                   has(ComHealthTestProfile.age_min <= customer_age)).first()
        if ref_profile:
            ref_profile_test_ids = [ti.test.id for ti in ref_profile.profile.test_items]
        else:
            ref_profile_test_ids = []
        valid_receipts = [rcp for rcp in record.receipts if not rcp.cancelled]
        return render_template('comhealth/new_receipt.html', record=record,
                               valid_receipts=valid_receipts,
                               ref_profile=ref_profile,
                               ref_profile_test_ids=ref_profile_test_ids,
                               )
    if request.method == 'POST':
        receipt_code = ComHealthReceiptID.get_number('MTH', db)
        receipt_code.count += 1
        record_id = request.form.get('record_id')
        record = ComHealthRecord.query.get(record_id)
        print_profile = request.form.get('print_profile', '')
        address = request.form.get('receipt_address', None)
        issued_for = request.form.get('issued_for', None)
        issuer = ComHealthCashier.query.filter_by(staff=current_user).first()
        if not issuer:
            issuer = ComHealthCashier(staff=current_user,
                                      position=current_user.personal_info.position)
            db.session.add(issuer)
            db.session.commit()

        # TODO: new receipt only includes unpaid tests
        receipt = ComHealthReceipt(
            code=receipt_code.number,
            created_datetime=arrow.now('Asia/Bangkok').datetime,
            record=record,
            print_profile_note=(True if print_profile == 'consolidated' else False),
            issued_at=session.get('receipt_venue', ''),
            issuer=issuer
        )
        if address:
            receipt.address = address
        if issued_for:
            receipt.issued_for = issued_for
        receipt.print_profile_note = True if print_profile else False
        receipt.print_profile_how = print_profile

        receipt_code.updated_datetime = arrow.now('Asia/Bangkok').datetime

        all_tests = record.get_all_tests()
        for test_item in record.ordered_tests:
            if test_item.test in all_tests:
                continue
            if test_item.profile and print_profile == '':
                continue
            visible = test_item.test.code + '_visible'
            billed = test_item.test.code + '_billed'
            reimbursable = test_item.test.code + '_reimbursable'
            billed = True if request.form.getlist(billed) else False
            visible = True if request.form.getlist(visible) else False
            reimbursable = True if request.form.getlist(reimbursable) else False
            invoice = ComHealthInvoice(test_item=test_item,
                                       receipt=receipt,
                                       billed=billed,
                                       reimbursable=reimbursable,
                                       visible=visible)
            db.session.add(invoice)
        if receipt.invoices:
            record.finance_contact = None
            db.session.add(record)
            db.session.add(receipt)
            db.session.add(receipt_code)
            db.session.commit()
        return redirect(url_for('comhealth.list_all_receipts', record_id=record.id))


@comhealth.route('/checkin/receipts/cancel/confirm/<int:receipt_id>', methods=['GET', 'POST'])
@login_required
def confirm_cancel_receipt(receipt_id):
    receipt = ComHealthReceipt.query.get(receipt_id)
    if not receipt.cancelled:
        return render_template('/comhealth/confirm_cancel_receipt.html', receipt=receipt)


@comhealth.route('/checkin/receipts/cancel/<int:receipt_id>', methods=['POST'])
@login_required
def cancel_receipt(receipt_id):
    receipt = ComHealthReceipt.query.get(receipt_id)
    if receipt.pdf_file:
        buffer = generate_receipt_pdf(receipt, sign=True, cancel=True)
        try:
            sign_pdf = e_sign(buffer, request.form.get('password'),
                              include_image=False,
                              sig_field_name='cancel', message=f'ยกเลิก {receipt.code}')
        except (ValueError, AttributeError) as e:
            raise e
            flash("ไม่สามารถลงนามดิจิทัลได้ โปรดตรวจสอบรหัสผ่าน", "danger")
        else:
            receipt.pdf_file = sign_pdf.read()
            sign_pdf.seek(0)
            receipt.cancelled = True
            receipt.cancel_comment = request.form.get('comment')
    else:
        receipt.cancelled = True
        receipt.cancel_comment = request.form.get('comment')
    db.session.add(receipt)
    db.session.commit()
    return redirect(url_for('comhealth.list_all_receipts',
                            record_id=receipt.record.id))


@comhealth.route('/checkin/receipts/pay/<int:receipt_id>', methods=['POST'])
@login_required
def pay_receipt(receipt_id):
    pay_method = request.form.get('pay_method')
    if pay_method == 'card':
        card_number = request.form.get('card_number').replace(' ', '')
    paid_amount = request.form.get('totalcost_pay', 0.0)
    receipt = ComHealthReceipt.query.get(receipt_id)
    #print(receipt.paid)
    if not receipt.paid:
        receipt.paid = True
        receipt.payment_method = pay_method
        if pay_method == 'card':
            receipt.card_number = card_number
            receipt.paid_amount = paid_amount
        if pay_method == 'cash':
            receipt.paid_amount = paid_amount
        if pay_method == 'QR':
            receipt.paid_amount = paid_amount
        db.session.add(receipt)
        db.session.commit()
    return redirect(url_for('comhealth.show_receipt_detail',
                            receipt_id=receipt_id))


@comhealth.route('receipt/<int:receipt_id>/password/enter', methods=['GET', 'POST'])
@login_required
def enter_password_for_sign_digital(receipt_id):
    form = PasswordOfSignDigitalForm()
    return render_template('comhealth/password_modal.html', form=form, receipt_id=receipt_id)


def send_mail(recp, title, message, attached_file=None, filename=None):
    message = Message(subject=title, body=message, recipients=recp)
    if attached_file:
        message.attach(filename=filename, data=attached_file, content_type='application/pdf')
    mail.send(message)


@comhealth.route('receipt/<int:receipt_id>/email-modal', methods=['GET', 'POST'])
@login_required
def send_email_modal(receipt_id):
    form = SendMailToCustomerForm()
    return render_template('comhealth/email_modal.html', form=form, receipt_id=receipt_id)


@comhealth.route('receipt/<int:receipt_id>/email/send/', methods=['POST'])
@login_required
def send_email_to_customer(receipt_id):
    form = SendMailToCustomerForm()
    receipt_detail = ComHealthReceipt.query.get(receipt_id)
    title = u'ใบเสร็จรับเงินคณะเทคนิคการแพทย์ มหาวิทยาลัยมหิดล'
    message = u'เรียนท่านผู้รับบริการ ตามที่ท่านได้ทำการชำระค่าบริการยังคณะเทคนิคการแพทย์ ม.มหิดล' \
              u'ท่านสามารถดาวน์โหลดใบเสร็จรับเงินตามลิงค์ที่แนบมาพร้อมนี้\n\n ขอแนบใบเสร็จเลขที่ {}' \
        .format(receipt_detail.code)
    message += u'\n\n======================================================'
    message += u'\nอีเมลนี้ส่งโดยระบบอัตโนมัติ กรุณาอย่าตอบกลับ ' \
               u'หากมีข้อสงสัยโปรดติดต่อกลับเจ้าหน้าที่ผู้และโครงการฯ ติดต่องานการเงิน mumtfinance@gmail.com, ติดต่อโครงการประเมินคุณภาพ eqamtmu@gmail.com'
    message += u'\nThis email was sent by an automated system. Please do not reply. If you have any questions, please contact the financial unit: mumtfinance@gmail.com, contact the quality assessment project: eqamtmu@gmail.com at Faculty of Medical Technology Mahidol University.'
    send_mail([form.email.data], title, message, receipt_detail.pdf_file, f'{receipt_detail.code}.pdf')
    flash(u'ส่งข้อมูลสำเร็จ.', 'success')
    return redirect(url_for('comhealth.show_receipt_detail', receipt_id=receipt_id, form=form))


@comhealth.route('/checkin/receipts/<int:receipt_id>', methods=['GET', 'POST'])
@login_required
def show_receipt_detail(receipt_id):
    receipt = ComHealthReceipt.query.get(receipt_id)
    action = request.args.get('action', None)
    if action == 'pay':
        receipt.paid = True
        db.session.add(receipt)
        db.session.commit()

    total_cost = sum([t.test_item.price for t in receipt.invoices if t.billed])
    total_cost_float = float(total_cost)
    total_special_cost = sum([t.test_item.price for t in receipt.invoices
                              if t.billed and t.test_item.group])

    total_special_cost_reimbursable = sum([t.test_item.price for t in receipt.invoices
                                           if t.billed and t.reimbursable and t.test_item.group])

    total_profile_cost = sum([t.test_item.price for t in receipt.invoices
                              if t.billed and t.test_item.profile])

    total_profile_cost_reimbursable = sum([t.test_item.price for t in receipt.invoices
                                           if t.billed and t.reimbursable and t.test_item.profile])
    profile_quote = 0
    for s in receipt.invoices:
        try:
            if s.test_item.profile.quote > 0:
                profile_quote = s.test_item.profile.quote
                break
        except:
            profile_quote = 0

    if profile_quote > 0 and receipt.print_profile_how == 'consolidated':
        total_profile_cost_reimbursable = profile_quote
        total_cost = total_profile_cost_reimbursable + total_special_cost
        total_cost_float = float(total_cost)
    if profile_quote == 0 and receipt.print_profile_how == 'consolidated':
        total_profile_cost_reimbursable = total_profile_cost

    total_profile_cost_not_reimbursable = total_profile_cost - total_profile_cost_reimbursable
    total_special_cost_not_reimbursable = total_special_cost - total_special_cost_reimbursable

    total_cost_thai = bahttext(total_cost)

    visible_special_tests = [t for t in receipt.invoices if t.visible and t.test_item.group]
    visible_profile_tests = [t for t in receipt.invoices if t.visible and t.test_item.profile]

    return render_template('comhealth/receipt_detail.html',
                           receipt=receipt,
                           total_cost=total_cost,
                           total_cost_float=total_cost_float,
                           total_profile_cost=total_profile_cost,
                           total_profile_cost_reimbursable=total_profile_cost_reimbursable,
                           total_profile_cost_not_reimbursable=total_profile_cost_not_reimbursable,
                           total_special_cost=total_special_cost,
                           total_cost_thai=total_cost_thai,
                           total_special_cost_not_reimbursable=total_special_cost_not_reimbursable,
                           total_special_cost_reimbursable=total_special_cost_reimbursable,
                           visible_special_tests=visible_special_tests,
                           visible_profile_tests=visible_profile_tests)


sarabun_font = TTFont('Sarabun', 'app/static/fonts/THSarabunNew.ttf')
pdfmetrics.registerFont(sarabun_font)
style_sheet = getSampleStyleSheet()
style_sheet.add(ParagraphStyle(name='ThaiStyle', fontName='Sarabun'))
style_sheet.add(ParagraphStyle(name='ThaiStyleNumber', fontName='Sarabun', alignment=TA_RIGHT))
style_sheet.add(ParagraphStyle(name='ThaiStyleCenter', fontName='Sarabun', alignment=TA_CENTER))


def generate_receipt_pdf(receipt, sign=False, cancel=False):
    logo = Image('app/static/img/logo-MU_black-white-2-1.png', 60, 60)

    digi_name = Paragraph(
        '<font size=12>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;(ลายมือชื่อดิจิทัล/Digital Signature)<br/></font>',
        style=style_sheet['ThaiStyle']) if sign else ""

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer,
                            rightMargin=10,
                            leftMargin=10,
                            topMargin=180,
                            bottomMargin=10,
                            )
    receipt_number = receipt.code
    data = []
    affiliation = '''<para align=center><font size=10>
            คณะเทคนิคการแพทย์ มหาวิทยาลัยมหิดล<br/>
            FACULTY OF MEDICAL TECHNOLOGY, MAHIDOL UNIVERSITY
            </font></para>
            '''
    address = '''<br/><br/><font size=11>
            999 ถ.พุทธมณฑลสาย 4 ต.ศาลายา<br/>
            อ.พุทธมณฑล จ.นครปฐม 73170<br/>
            999 Phutthamonthon 4 Road<br/>
            Salaya, Nakhon Pathom 73170<br/>
            เลขประจำตัวผู้เสียภาษี / Tax ID Number<br/>
            0994000158378
            </font>
            '''

    receipt_info = '''<br/><br/><font size=10>
            เลขที่/No. {receipt_number}<br/>
            วันที่/Date {issued_date}
            </font>
            '''
    issued_date = arrow.get(receipt.created_datetime.astimezone(bangkok)).format(fmt='DD MMMM YYYY', locale='th-th')
    receipt_info_ori = receipt_info.format(receipt_number=receipt_number,
                                           issued_date=issued_date,
                                           )

    header_content_ori = [[Paragraph(address, style=style_sheet['ThaiStyle']),
                           [logo, Paragraph(affiliation, style=style_sheet['ThaiStyle'])],
                           [],
                           Paragraph(receipt_info_ori, style=style_sheet['ThaiStyle'])]]

    header_styles = TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ])

    header_ori = Table(header_content_ori, colWidths=[150, 200, 50, 100])

    header_ori.hAlign = 'CENTER'
    header_ori.setStyle(header_styles)

    origin_or_copy = ''
    if receipt.copy_number == 1:
        origin_or_copy = Paragraph('<para align=center><font size=20>ต้นฉบับ(Original)<br/><br/></font></para>',
                               style=style_sheet['ThaiStyle'])
    else:
        origin_or_copy = Paragraph('<para align=center><font size=20>สำเนา(Copy)<br/><br/></font></para>',
                                   style=style_sheet['ThaiStyle'])
    if cancel:
        origin_or_copy = Paragraph('<para align=center><font size=20>ยกเลิก(Cancel)<br/><br/></font></para>',
                                   style=style_sheet['ThaiStyle'])
    hight_customer_name = 5.5
    if receipt.issued_for:

        customer_name = '''<para><font size=12>
        ได้รับเงินจาก / RECEIVED FROM {issued_for} ({customer_name})<br/>
        ที่อยู่ / ADDRESS {address} <br/>
        </font></para>
        '''.format(issued_for=receipt.issued_for,
                   customer_name=receipt.record.customer.fullname,
                   address=receipt.address,
                   )
    else:
        customer_name = '''<para><font size=12>
        ได้รับเงินจาก / RECEIVED FROM {customer_name}
        </font></para>
        '''.format(customer_name=receipt.record.customer.fullname,
                   )
    customer_labno = '''<para><font size=11>
    หมายเลขรายการ / NUMBER {customer_labno}<br/><br/>
    </font></para>
    '''.format(customer_labno=receipt.record.labno,
               venue=receipt.issued_at)
    customer = Table([[Paragraph(customer_name, style=style_sheet['ThaiStyle']),
                       Paragraph(customer_labno, style=style_sheet['ThaiStyle'])]],
                     colWidths=[300, 200]
                     )
    customer.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    items = [[Paragraph('<font size=10>ลำดับ / No.</font>', style=style_sheet['ThaiStyleCenter']),
              Paragraph('<font size=10>รายการ / Description</font>', style=style_sheet['ThaiStyleCenter']),
              Paragraph('<font size=10>เบิกได้ (บาท)*<br/>Reimbursable (BAHT)</font>',
                        style=style_sheet['ThaiStyleCenter']),
              Paragraph('<font size=10>เบิกไม่ได้ (บาท)*<br/>Non-reimbursable (BAHT)</font>',
                        style=style_sheet['ThaiStyleCenter']),
              Paragraph('<font size=10>รวม / Total</font>', style=style_sheet['ThaiStyleCenter']),
              ]]
    total = 0
    number_test = 0
    total_profile_price = 0
    total_special_price = 0
    if receipt.print_profile_note:
        profile_tests = [t for t in receipt.record.ordered_tests if t.profile]
        if profile_tests:
            if receipt.print_profile_how == 'consolidated':
                number_test += 1
                profile_price = profile_tests[0].profile.quote
                if profile_price > 0:
                    item = [Paragraph('<font size=12>{}</font>'.format(number_test), style=style_sheet['ThaiStyleCenter']),
                            Paragraph('<font size=12>การตรวจสุขภาพทางห้องปฏิบัติการ / Laboratory Tests</font>',
                                      style=style_sheet['ThaiStyle']),
                            Paragraph('<font size=12>-</font>', style=style_sheet['ThaiStyleCenter']),
                            Paragraph('<font size=12>{:,.2f}</font>'.format(profile_price),
                                      style=style_sheet['ThaiStyleNumber']),
                            Paragraph('<font size=12>{:,.2f}</font>'.format(profile_price),
                                      style=style_sheet['ThaiStyleNumber']),
                            ]
                    items.append(item)
                    total_special_price += profile_price
                    total += profile_price
                else:
                    for t in receipt.record.ordered_tests:
                        if t.profile:
                            total_special_price += t.price
                            total += t.price
                    item = [Paragraph('<font size=12>{}</font>'.format(number_test),
                                      style=style_sheet['ThaiStyleCenter']),
                            Paragraph('<font size=12>การตรวจสุขภาพทางห้องปฏิบัติการ / Laboratory Tests</font>',
                                      style=style_sheet['ThaiStyle']),
                            Paragraph('<font size=12>-</font>', style=style_sheet['ThaiStyleCenter']),
                            Paragraph('<font size=12>{:,.2f}</font>'.format(total_special_price),
                                      style=style_sheet['ThaiStyleNumber']),
                            Paragraph('<font size=12>{:,.2f}</font>'.format(total_special_price),
                                      style=style_sheet['ThaiStyleNumber']),
                            ]
                    items.append(item)
    for t in receipt.invoices:
        if t.visible:
            if t.billed:
                if t.test_item.profile and receipt.print_profile_how == 'consolidated':
                    continue
                if t.test_item.price is None:
                    price = t.test_item.test.default_price
                else:
                    price = t.test_item.price
                if price == 0:
                    continue
                total += price
                number_test += 1
                item = [Paragraph('<font size=12>{}</font>'.format(number_test), style=style_sheet['ThaiStyleCenter']),
                        Paragraph('<font size=12>{} ({})</font>'
                                  .format(t.test_item.test.name,
                                          t.test_item.test.gov_code or '-'),
                                  style=style_sheet['ThaiStyle'])
                        ]
                if t.reimbursable:
                    total_profile_price += price
                    item.append(
                        Paragraph('<font size=12>{:,.2f}</font>'.format(price), style=style_sheet['ThaiStyleNumber']))
                    item.append(Paragraph('<font size=12>-</font>', style=style_sheet['ThaiStyleCenter']))
                    item.append(
                        Paragraph('<font size=12>{:,.2f}</font>'.format(price), style=style_sheet['ThaiStyleNumber']))
                else:
                    total_special_price += price
                    item.append(Paragraph('<font size=12>-</font>', style=style_sheet['ThaiStyleCenter']))
                    item.append(
                        Paragraph('<font size=12>{:,.2f}</font>'.format(price), style=style_sheet['ThaiStyleNumber']))
                    item.append(
                        Paragraph('<font size=12>{:,.2f}</font>'.format(price), style=style_sheet['ThaiStyleNumber']))
                items.append(item)

    total_thai = bahttext(total)
    total_text = "รวมเงินทั้งสิ้น {}".format(total_thai)

    summary_rows = [
        [
            Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
            Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
            Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
            Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
            Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
        ],
        [
            Paragraph('<font size=12>{}</font>'.format(total_text), style=style_sheet['ThaiStyle']),
            Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
            Paragraph('<font size=12>{:,.2f}</font>'.format(total_profile_price), style=style_sheet['ThaiStyleNumber']),
            Paragraph('<font size=12>{:,.2f}</font>'.format(total_special_price), style=style_sheet['ThaiStyleNumber']),
            Paragraph('<font size=12>{:,.2f}</font>'.format(total), style=style_sheet['ThaiStyleNumber'])
        ]
    ]
    #table style หน้าสุดท้าย
    table_style = TableStyle([
        ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
        ('BOX', (0, -1), (-1, -1), 0.25, colors.black),
        ('BOX', (0, 0), (0, -1), 0.25, colors.black),
        ('BOX', (1, 0), (1, -1), 0.25, colors.black),
        ('BOX', (2, 0), (2, -1), 0.25, colors.black),
        ('BOX', (3, 0), (3, -1), 0.25, colors.black),
        ('BOX', (4, 0), (4, -1), 0.25, colors.black),
        ('BOX', (0, 0), (4, 32), 0.25, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, -2), (-1, -2), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (0, -1), (1, -1)),
    ])
    # table style หน้าอื่นๆ
    table_style2 = TableStyle([
        ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
        ('BOX', (0, 0), (0, -1), 0.25, colors.black),
        ('BOX', (1, 0), (1, -1), 0.25, colors.black),
        ('BOX', (2, 0), (2, -1), 0.25, colors.black),
        ('BOX', (3, 0), (3, -1), 0.25, colors.black),
        ('BOX', (4, 0), (4, -1), 0.25, colors.black),
        ('BOX', (0, 0), (4, 32), 0.25, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])

    MAX_ROWS_PER_PAGE = 24  # รวม header
    COL_WIDTHS = [40, 258, 70, 70, 70]

    item_tables = []

    header_row = items[0]
    data_rows = items[1:]
    total_rows = len(data_rows)

    for i in range(0, total_rows, MAX_ROWS_PER_PAGE - 1):

        if len(data_rows) < (MAX_ROWS_PER_PAGE - 1):
            empty_row = [
                Paragraph('<font size=12>&nbsp;</font>', style=style_sheet['ThaiStyle']),
                Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
                Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
                Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
                Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
            ]
            for _ in range((MAX_ROWS_PER_PAGE - 1) - len(data_rows)):
                data_rows.append(empty_row)

        page_data = data_rows[i:i + (MAX_ROWS_PER_PAGE - 1)]
        page_items = [header_row] + page_data

        # เช็คว่าหน้านี้เป็นหน้าสุดท้ายหรือไม่
        is_last_page = (i + (MAX_ROWS_PER_PAGE - 1) >= total_rows)

        if is_last_page:
            page_items += summary_rows

        table = Table(page_items, colWidths=COL_WIDTHS, repeatRows=1)
        table.setStyle(table_style if is_last_page else table_style2)

        item_tables.append(KeepTogether(table))

        if not is_last_page:
            item_tables.append(PageBreak())

    if receipt.payment_method == 'cash':
        payment_info = Paragraph('<font size=14>ชำระเงินด้วย / PAYMENT METHOD เงินสด / CASH</font>',
                                 style=style_sheet['ThaiStyle'])
    elif receipt.payment_method == 'QR':
        payment_info = Paragraph('<font size=14>ชำระเงินด้วย / PAYMENT METHOD QR / QR</font>',
                                 style=style_sheet['ThaiStyle'])
    elif receipt.payment_method == 'card':
        payment_info = Paragraph(
            '<font size=14>ชำระเงินด้วย / PAYMENT METHOD บัตรเครดิต / CREDIT CARD หมายเลข / NUMBER {}-****-****-{}</font>'.format(
                receipt.card_number[:4], receipt.card_number[-4:]),
            style=style_sheet['ThaiStyle'])
    else:
        payment_info = Paragraph('<font size=11>ยังไม่ชำระเงิน / UNPAID</font>', style=style_sheet['ThaiStyle'])

    total_content = []
    total_content.append([
        payment_info,
        Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
        Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
    ])

    total_table = Table(total_content, colWidths=[300, 150, 50])

    sign_text = Paragraph(
        '<br/><font size=12>ผู้รับเงิน / Received by &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {}<br/></font>'.format(
            receipt.issuer.staff.fullname),
        style=style_sheet['ThaiStyle'])

    receive = [[sign_text,
                Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle']),
                Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle'])]]
    receive_officer = Table(receive, colWidths=[0, 80, 20])
    personal_info = [[digi_name,
                      Paragraph('<font size=12>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</font>',
                                style=style_sheet['ThaiStyle'])]]
    issuer_personal_info = Table(personal_info, colWidths=[0, 30, 20])

    position = Paragraph(
        '<font size=12>ตำแหน่ง / Position &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {}</font>'.format(
            receipt.issuer.staff.personal_info.position),
        style=style_sheet['ThaiStyle'])
    position_info = [[position,
                      Paragraph('<font size=12></font>', style=style_sheet['ThaiStyle'])]]
    issuer_position = Table(position_info, colWidths=[0, 80, 20])

    def all_page_setup(canvas, doc):
        canvas.saveState()

        # Head
        header = header_ori
        w, h = header.wrap(doc.width, doc.topMargin)
        header.drawOn(canvas, doc.leftMargin + 28, doc.height + doc.topMargin - h)

        isoriginal = origin_or_copy
        w, h = isoriginal.wrap(doc.width, doc.topMargin)
        isoriginal.drawOn(canvas, doc.leftMargin + 200, doc.height + doc.topMargin - h * 4.5)

        subheader1 = Paragraph('<para align=center><font size=16>ใบเสร็จรับเงิน / RECEIPT<br/><br/></font></para>',
                               style=style_sheet['ThaiStyle'])
        w, h = subheader1.wrap(doc.width, doc.topMargin)
        subheader1.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h * 5.5)

        subheader2 = customer
        w, h = subheader2.wrap(doc.width, doc.topMargin)
        subheader2.drawOn(canvas, doc.leftMargin + 28, doc.height + doc.topMargin - h * hight_customer_name)

        logo_image = ImageReader('app/static/img/mu-watermark.png')
        canvas.drawImage(logo_image, 140, 265, mask='auto')

        # --- Footer content ---
        footer_y = 20  # Y position for footer content
        current_y = footer_y

        footer_notice = Paragraph(
            '<para align="center">'
            'สิทธิตามระเบียบกระทรวงการคลัง / Reimbursement is in accordance with the regulation of the Ministry of Finance.'
            '<br/>เอกสารนี้จัดทำด้วยวิธีการทางอิเล็กทรอนิกส์'
            '</para>',
            style=style_sheet['ThaiStyle']
        )
        w, h = footer_notice.wrap(doc.width, doc.bottomMargin)
        footer_notice.drawOn(canvas, doc.leftMargin, current_y)
        current_y += h + 1  # เพิ่มระยะห่างแนวตั้งเล็กน้อย

        footer_qr = Paragraph(
            'สามารถสแกน QR Code ตรวจสอบสถานะใบเสร็จรับเงินได้ที่ '
            '<img src="app/static/img/receipt_comhealth_checking.jpg" width="30" height="30" />',
            style=style_sheet['ThaiStyle']
        )
        w, h = footer_qr.wrap(doc.width, doc.bottomMargin)
        footer_qr.drawOn(canvas, doc.leftMargin + 32 , current_y)
        current_y += h + 1

        footer_time = Paragraph(
            'Time {} น.'.format(receipt.created_datetime.astimezone(bangkok).strftime('%H:%M:%S')),
            style=style_sheet['ThaiStyle']
        )
        w, h = footer_time.wrap(doc.width, doc.bottomMargin)
        footer_time.drawOn(canvas, doc.leftMargin + 32, current_y)
        current_y += h + 1

        footer_docno = Paragraph(
            'เลขที่กำกับเอกสาร<br/>Regulatory Document No. {}'.format(receipt.code),
            style=style_sheet['ThaiStyle']
        )
        w, h = footer_docno.wrap(doc.width, doc.bottomMargin)
        footer_docno.drawOn(canvas, doc.leftMargin + 32, current_y)

        canvas.restoreState()

    data.extend(item_tables)
    data.append(KeepTogether(Spacer(1, 6)))
    data.append(KeepTogether(total_table))
    data.append(KeepTogether(receive_officer))
    data.append(KeepTogether(issuer_personal_info))
    data.append(KeepTogether(issuer_position))

    doc.build(data, onLaterPages=all_page_setup, onFirstPage=all_page_setup, canvasmaker=PageNumCanvas)
    buffer.seek(0)
    return buffer

class PageNumCanvas(canvas.Canvas):
    """
    http://code.activestate.com/recipes/546511-page-x-of-y-with-reportlab/
    http://code.activestate.com/recipes/576832/
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """Constructor"""
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    # ----------------------------------------------------------------------
    def showPage(self):
        """
        On a page break, add information to the list
        """
        self.pages.append(dict(self.__dict__))
        self._startPage()

    # ----------------------------------------------------------------------
    def save(self):
        """
        Add the page number to each page (page x of y)
        """
        page_count = len(self.pages)

        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    # ----------------------------------------------------------------------
    def draw_page_number(self, page_count):
        """
        Add the page number
        """
        page = "%s/%s" % (self._pageNumber, page_count)
        self.setFont("Sarabun", 12)
        self.drawRightString(195 * mm, 290 * mm, page)


@comhealth.route('/receipts/pdf/<int:receipt_id>/download')
@login_required
def download_receipt_pdf(receipt_id):
    if request.method == 'GET':
        receipt = ComHealthReceipt.query.get(receipt_id)
        if  receipt.pdf_file:
            receipt.copy_number += 1
            db.session.add(receipt)
            db.session.commit()
            return send_file(BytesIO(receipt.pdf_file), download_name=f'{receipt.code}.pdf', as_attachment=True)
        buffer = generate_receipt_pdf(receipt)
        return send_file(buffer, download_name=f'{receipt.code}.pdf', as_attachment=True)

@comhealth.route('/checkin/receipts/show_pdf/<int:receipt_id>', methods=['GET', 'POST'])
def show_receipt_pdf(receipt_id):
    receipt = ComHealthReceipt.query.get(receipt_id)
    return render_template('comhealth/preview_receipt_detail.html',
                           receipt=receipt)

@comhealth.route('/api/receipts/preview_pdf/<int:receipt_id>')
@login_required
def preview_pdf(receipt_id):
    receipt = ComHealthReceipt.query.get(receipt_id)
    if receipt.pdf_file:
        return send_file(BytesIO(receipt.pdf_file), download_name=f'{receipt.code}.pdf', as_attachment=True)
    buffer = generate_receipt_pdf(receipt)
    return send_file(buffer, download_name=f'{receipt.code}.pdf', as_attachment=True)

@comhealth.route('/receipts/pdf/<int:receipt_id>', methods=['POST', 'GET'])
@login_required
def export_receipt_pdf(receipt_id):
    if request.method == 'GET':
        receipt = ComHealthReceipt.query.get(receipt_id)
        download_url = url_for('comhealth.download_receipt_pdf',receipt_id=receipt_id)
        enter_password_url = url_for('comhealth.enter_password_for_sign_digital', receipt_id=receipt_id)
        if receipt.copy_number == 1:
            template = f'''
                        <button class="button is-primary" 
                        hx-get={enter_password_url}>
                        <span class="icon">
                        <i class="fas fa-download"></i>
                        </span>
                        <span>ขอสำเนา</span>
                        </button>
                        '''
            resp = make_response(template)
            resp.headers['HX-Trigger'] = json.dumps({'downloadReceiptEvent': download_url})
            return resp
        else:
            template = f'''
            <button class="button is-primary" 
            hx-get={download_url}>
            <span class="icon">
            <i class="fas fa-download"></i>
            </span>
            <span>Download Copy</span>
            </button>
            '''
            resp = make_response(template)
            resp.headers['HX-Trigger'] = json.dumps({'downloadReceiptEvent': download_url})
            return resp
    elif request.method == 'POST':
        password = request.form.get('password')
        receipt = ComHealthReceipt.query.get(receipt_id)
        if receipt.pdf_file is None:
            buffer = generate_receipt_pdf(receipt, sign=True)
            try:
                sign_pdf = e_sign(buffer, password, include_image=False, sig_field_name='original')
            except (ValueError, AttributeError):
                flash("ไม่สามารถลงนามดิจิทัลได้ โปรดตรวจสอบรหัสผ่าน", "danger")
            else:
                receipt.pdf_file = sign_pdf.read()
                sign_pdf.seek(0)
                db.session.add(receipt)
                db.session.commit()
        else:
            buffer = generate_receipt_pdf(receipt, sign=True)
            try:
                sign_pdf = e_sign(buffer, password,
                                  include_image=False,
                                  sig_field_name='copy')
            except (ValueError, AttributeError):
                flash("ไม่สามารถลงนามดิจิทัลได้ โปรดตรวจสอบรหัสผ่าน", "danger")
            else:
                receipt.pdf_file = sign_pdf.read()
                receipt.copy_number += 1
                sign_pdf.seek(0)
                db.session.add(receipt)
                db.session.commit()
        response = make_response()
        response.headers['HX-Refresh'] = 'true'
        return response


class CustomerEmploymentTypeUploadView(BaseView):
    @expose('/')
    def index(self):
        return self.render('comhealth/employment_type_upload.html')

    @expose('/upload', methods=('POST', 'GET'))
    def upload(self):
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file alert')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No file selected')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                df = read_excel(file, dtype=object)
                for idx, row in df.iterrows():
                    rec = ComHealthCustomerEmploymentType.query \
                        .filter_by(emptype_id=row[0]).first()
                    if rec:
                        if not isna(row[1]):
                            rec.name = row[1]
                            db.session.add(rec)
                    else:
                        if not isna(row[1]) and not isna(row[0]):
                            rec = ComHealthCustomerEmploymentType(emptype_id=row[0], name=row[1])
                            db.session.add(rec)
                db.session.commit()
        return request.method


@comhealth.route('/services/<int:service_id>/all-tests')
@login_required
def list_all_tests(service_id):
    service = ComHealthService.query.get(service_id)
    return render_template('/comhealth/all_tests.html', service=service)


@comhealth.route('/health-record/kiosk', methods=['GET', 'POST'])
@login_required
def employee_kiosk_mode():
    if request.method == 'POST':
        labno = request.form['labno']
        record = ComHealthRecord.query.filter_by(labno=labno).first()
        if record:
            return redirect(url_for('comhealth.show_employee_info',
                                    custid=record.customer.id, kiosk_mode='yes'))
        else:
            flash(u'ไม่พบหมายเลขบริการ กรุณาตรวจสอบใหม่อีกครั้ง', 'danger')
    return render_template('comhealth/employee_kiosk_mode.html')


@comhealth.route('/consent-details/services/<int:service_id>')
@login_required
def list_consent_details(service_id):
    consent_details = ComHealthConsentDetail.query.all()
    return render_template('comhealth/consent_details.html', consent_details=consent_details, service_id=service_id)


@comhealth.route('/consent-records/services/<int:service_id>/consent-details/<int:consent_detail_id>',
                 methods=['GET', 'POST'])
@login_required
def add_consent_records(service_id, consent_detail_id):
    all_records = ComHealthRecord.query.filter_by(service_id=service_id).all()
    if request.method == 'POST':
        for record in all_records:
            if record.consent_record:
                continue
            consent = request.form.get('consent_{}'.format(record.id))
            if consent:
                consent_given = True if consent == "yes" else False
                consent_record = ComHealthConsentRecord(
                    detail_id=consent_detail_id,
                    is_consent_given=consent_given,
                    creator=current_user.id,
                    consent_date=datetime.today().date()
                )
                record.consent_record = consent_record
                db.session.add(consent_record)
        db.session.commit()
        return redirect(url_for('comhealth.index'))
    return render_template('comhealth/add_consent_records.html', all_records=all_records)


@comhealth.route('/receipt/search')
def search_receipt():
    return render_template('comhealth/search_receipt.html')


@comhealth.route('/receipt/search/list', methods=['POST', 'GET'])
def receipt_list():
    code = request.form.get('code', None)
    if code:
        receipt_detail = ComHealthReceipt.query.filter(ComHealthReceipt.code.ilike('%{}%'.format(code)))
    else:
        receipt_detail = []
    if request.headers.get('HX-Request') == 'true':
        return render_template('comhealth/receipt_list.html', receipt_detail=receipt_detail)
    return render_template('comhealth/receipt_list.html', receipt_detail=receipt_detail)
