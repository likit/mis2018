# -*- coding:utf-8 -*-

from . import data_bp
from app.main import db
from app.models import CoreService, Process, Data, KPI
from forms import *
from flask import url_for, render_template, redirect, flash, request
from flask_login import current_user, login_required


@data_bp.route('/')
def index():
    data = Data.query.all()
    core_services = CoreService.query.all()
    back_office_processes = Process.query.filter_by(category='back_office').all()
    crm_processes = Process.query.filter_by(category='crm').all()
    performance_processes = Process.query.filter_by(category='performance').all()
    regulation_processes = Process.query.filter_by(category='regulation').all()
    return render_template('data_blueprint/index.html',
                                core_services=core_services,
                                data=data,
                                back_office_processes=back_office_processes,
                                crm_processes=crm_processes,
                                performance_processes=performance_processes,
                                regulation_processes=regulation_processes,
                                )


@data_bp.route('/core-services/new', methods=['GET', 'POST'])
@data_bp.route('/core-services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
def core_service_form(service_id=None):
    if service_id:
        service_ = CoreService.query.get(service_id)
        form = CoreServiceForm(obj=service_)
    else:
        form = CoreServiceForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if not service_id:
                new_service = CoreService()
                form.populate_obj(new_service)
                new_service.creator_id = current_user.id
                db.session.add(new_service)
            else:
                form.populate_obj(service_)
                db.session.add(service_)
            db.session.commit()
            flash(u'บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
            return redirect(url_for('data_bp.index'))
    return render_template('data_blueprint/core_services.html', form=form, service_id=service_id)


@data_bp.route('/data/new', methods=['GET', 'POST'])
@data_bp.route('/data/<int:data_id>/edit', methods=['GET', 'POST'])
@login_required
def data_form(data_id=None):
    if data_id:
        data_ = Data.query.get(data_id)
        form = DataForm(obj=data_)
    else:
        form = DataForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if not data_id:
                new_data = Data()
                form.populate_obj(new_data)
                new_data.creator_id = current_user.id
                db.session.add(new_data)
            else:
                form.populate_obj(data_)
                db.session.add(data_)
            db.session.commit()
            flash(u'บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
            return redirect(url_for('data_bp.index'))
    return render_template('data_blueprint/data_form.html', form=form)


@data_bp.route('/process/new', methods=['GET', 'POST'])
@data_bp.route('/process/<int:process_id>/edit', methods=['GET', 'POST'])
@login_required
def process_form(process_id=None):
    if process_id:
        data_ = Process.query.get(process_id)
        form = ProcessForm(obj=data_)
    else:
        form = ProcessForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if not process_id:
                new_data = Process()
                form.populate_obj(new_data)
                new_data.creator_id = current_user.id
                db.session.add(new_data)
            else:
                form.populate_obj(data_)
                db.session.add(data_)
            db.session.commit()
            flash(u'บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
            return redirect(url_for('data_bp.index'))
    return render_template('data_blueprint/process_form.html', form=form)


@data_bp.route('/kpi/new', methods=['GET', 'POST'])
@data_bp.route('/kpi/<int:kpi_id>/edit', methods=['GET', 'POST'])
@login_required
def kpi_form(kpi_id=None):
    section = request.args.get('section', 'general')
    process_id = request.args.get('process_id', type=int)
    service_id = request.args.get('service_id', type=int)
    if section == 'general':
        Form = KPIForm
    elif section == 'target':
        Form = KPITargetForm
    else:
        Form = KPIReportForm
    if service_id:
        service = CoreService.query.get(service_id)
    if process_id:
        proc = Process.query.get(process_id)
    if kpi_id:
        data_ = KPI.query.get(kpi_id)
        form = Form(obj=data_)
    else:
        form = Form()
    if request.method == 'POST':
        if form.validate_on_submit():
            if not kpi_id:
                new_data = KPI()
                form.populate_obj(new_data)
                new_data.creator_id = current_user.id
                if service_id:
                    new_data.core_services.append(service)
                if process_id:
                    new_data.processes.append(proc)
                db.session.add(new_data)
            else:
                form.populate_obj(data_)
                db.session.add(data_)
            db.session.commit()
            flash(u'บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
            return redirect(url_for('data_bp.index'))
        else:
            flash(form.errors, 'danger')
    if section == 'general':
        return render_template('data_blueprint/kpi_form.html', form=form)
    elif section == 'target':
        return render_template('data_blueprint/kpi_form_target.html', form=form)
    else:
        return render_template('data_blueprint/kpi_form_report.html', form=form)


@data_bp.route('/datasets/<int:dataset_id>/kpis/add', methods=['POST'])
@login_required
def add_kpi_to_dataset(dataset_id):
    ds = Dataset.query.get(dataset_id)
    kpi = KPI.query.filter_by(refno=request.form['refno']).first()
    if kpi:
        ds.kpis.append(kpi)
        db.session.add(ds)
        db.session.commit()
        flash(u'บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
    else:
        flash(u'ไม่พบตัวชี้วัดดังกล่าว', 'warning')
    return redirect(url_for('data_bp.dataset_detail', dataset_id=dataset_id))


@data_bp.route('/datasets/<int:dataset_id>/kpis/<int:kpi_id>/remove', methods=['GET'])
@login_required
def remove_kpi_from_dataset(dataset_id, kpi_id):
    ds = Dataset.query.get(dataset_id)
    kpi = KPI.query.get(kpi_id)
    ds.kpis.remove(kpi)
    db.session.add(ds)
    db.session.commit()
    flash(u'ลบตัวชี้วัดออกจากชุดข้อมูลเรียบร้อย', 'success')
    return redirect(url_for('data_bp.dataset_detail', dataset_id=dataset_id))


@data_bp.route('/data/<int:data_id>', methods=['GET'])
@login_required
def data_detail(data_id):
    data = Data.query.get(data_id)
    return render_template('data_blueprint/data_detail.html', data=data)


@data_bp.route('/data/<int:data_id>/datasets/<int:dataset_id>/edit', methods=['GET', 'POST'])
@data_bp.route('/data/<int:data_id>/datasets/form', methods=['GET', 'POST'])
@login_required
def dataset_form(data_id, dataset_id=None):
    if dataset_id:
        dataset = Dataset.query.get(dataset_id)
        form = createDatasetForm(data_id=data_id)(obj=dataset)
    else:
        form = createDatasetForm(data_id=data_id)()
    if request.method == 'POST':
        if form.validate_on_submit():
            if not dataset_id:
                new_dataset = Dataset()
                form.populate_obj(new_dataset)
                new_dataset.creator_id = current_user.id
                new_dataset.data_id = data_id
                db.session.add(new_dataset)
                db.session.commit()
                flash(u'บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
                return redirect(url_for('data_bp.data_detail', data_id=data_id))
            else:
                form.populate_obj(dataset)
                db.session.add(dataset)
                db.session.commit()
                flash(u'บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
                return render_template('data_blueprint/dataset_detail.html', dataset=dataset)
    return render_template('data_blueprint/dataset_form.html', form=form)


@data_bp.route('/datasets/<int:dataset_id>', methods=['GET'])
@login_required
def dataset_detail(dataset_id):
    ds = Dataset.query.get(dataset_id)
    return render_template('data_blueprint/dataset_detail.html', dataset=ds)


@data_bp.route('/core_services/<int:service_id>/delete')
@login_required
def delete_core_service(service_id):
    sv = CoreService.query.get(service_id)
    db.session.delete(sv)
    db.session.commit()
    flash(u'ลบข้อมูลเรียบร้อยแล้ว', 'success')
    return redirect(url_for('data_bp.index'))


@data_bp.route('/core_services/<int:service_id>')
@login_required
def core_service_detail(service_id):
    cs = CoreService.query.get(service_id)
    data = []
    for d in cs.data:
        data.append([cs.service, d.name + '(data)', 1])
        kpis_from_datasets = set()
        for ds in d.datasets:
            if cs in ds.core_services:
                data.append([d.name + '(data)', (ds.name or ds.reference) + '(ds)', 1])
                for kpi in ds.kpis:
                    if kpi in cs.kpis:
                        data.append([ds.name + '(ds)', kpi.name + '(kpi)', 1])
                        kpis_from_datasets.add(kpi)
                if not ds.kpis:
                        data.append([(ds.name or ds.reference) + '(ds)', u'ไม่มีตัวชี้วัด', 1])
    for kpi in cs.kpis:
        if kpi not in kpis_from_datasets:
            data.append([cs.service, kpi.name + '(kpi)', 1])

    return render_template('data_blueprint/core_service_detail.html', core_service=cs, data=data)


@data_bp.route('/processes/<int:process_id>')
@data_bp.route('/processes/<int:process_id>/kpis/all')
@data_bp.route('/processes/<int:process_id>/kpis/<int:kpi_id>')
@login_required
def process_detail(process_id, kpi_id=None):
    proc = Process.query.get(process_id)
    data = []
    if kpi_id:
        kpi = KPI.query.get(kpi_id)
        all_kpis = [kpi]
    else:
        all_kpis = proc.kpis

    dataset_data_pairs = set()
    data_list = []
    for k in all_kpis:
        data.append([proc.name, k.name + '(kpi)', 1])
        for ds in k.datasets:
            data.append([k.name + '(kpi)', (ds.name or ds.reference) + '(ds)', 1])
            ds_dt_pair = ((ds.name or ds.reference), ds.data.name)
            if ds_dt_pair not in dataset_data_pairs:
                data.append([(ds.name or ds.reference) + '(ds)', ds.data.name + '(data)', 1])
                dataset_data_pairs.add(ds_dt_pair)
                data_list.append(ds.data.name)

    return render_template('data_blueprint/process_detail.html', process=proc, data=data, kpi_id=kpi_id)