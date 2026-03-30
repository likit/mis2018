from sqlalchemy import or_
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import TextAreaField, DateField, SelectField
from flask_login import current_user
from wtforms.validators import DataRequired, InputRequired

from app.software_request.models import *
from wtforms_alchemy import model_form_factory, QuerySelectField, QuerySelectMultipleField

BaseModelForm = model_form_factory(FlaskForm)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session


def create_request_form(detail_id):
    class SoftwareRequestDetailForm(ModelForm):
        class Meta:
            model = SoftwareRequestDetail

        if detail_id:
            room = QuerySelectField('ห้อง', query_factory=lambda: RoomResource.query.order_by(RoomResource.number.asc()),
                                allow_blank=True, blank_text='กรุณาเลือกห้อง')
            staffs = QuerySelectMultipleField('ผู้รับผิดชอบ', query_factory=lambda: StaffAccount.get_it_unit(),
                                              get_label='fullname')
        else:
            file_upload = FileField('File Upload')
            system = QuerySelectField('ระบบที่ต้องการปรับปรุง', query_factory=lambda: SoftwareRequestSystem.query.all(), allow_blank=True,
                                      blank_text='กรุณาเลือกระบบที่ต้องการปรับปรุง', get_label='system')
            work_process = QuerySelectField('กระบวนการทำงาน', allow_blank=True, get_label='name',
                                            query_factory=lambda: Process.query.filter(or_(Process.staff.contains(current_user),
                                                                                           Process.staff.any(StaffAccount.personal_info.has(org=current_user.personal_info.org)))),
                                            blank_text='กรุณาเลือกกระบวนการทำงาน')
            activity = QuerySelectField('โครงการที่เกี่ยวข้อง', query_factory=lambda: StrategyActivity.query.all(), allow_blank=True,
                                        blank_text='กรุณาเลือกโครงการที่เกี่ยวข้อง', get_label='content')
    return SoftwareRequestDetailForm


def create_timeline_form(detail_id):
    class SoftwareRequestTimelineForm(ModelForm):
        class Meta:
            model = SoftwareRequestTimeline

        task = TextAreaField('Task', validators=[DataRequired()])
        start = DateField('วันที่เริ่มต้น', validators=[DataRequired()])
        estimate = DateField('วันที่คาดว่าจะแล้วเสร็จ', validators=[DataRequired()])
        phase = SelectField('Phase', choices=[('1', '1'), ('2', '2'), ('3', '3')],validators=[DataRequired()])
        status = SelectField('status', choices=[('รอดำเนินการ', 'รอดำเนินการ'), ('เสร็จสิ้น', 'เสร็จสิ้น'), ('ยกเลิกการพัฒนา', 'ยกเลิกการพัฒนา')],
                             validators=[DataRequired()])
        issue = QuerySelectField('ปํญหาที่พบ', query_factory=lambda: SoftwareIssues.query.filter_by(software_request_detail_id=detail_id).all(), allow_blank=True,
                                 blank_text='', get_label='issue')
        admin = QuerySelectField('ผู้รับผิดชอบ', query_factory=lambda: StaffAccount.get_it_unit(), get_label='fullname')
    return SoftwareRequestTimelineForm


class SoftwareRequestIssueForm(ModelForm):
    class Meta:
        model = SoftwareIssues
        only = ['issue', 'label']

    status_ = SelectField('Status',
                          default='Draft',
                          choices=[(c,c) for c in ('Draft', 'Working', 'Cancelled', 'Closed')])
    staff = QuerySelectField('ผู้รับผิดชอบ', query_factory=lambda: StaffAccount.get_it_unit(), get_label='fullname')