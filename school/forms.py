from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import (
    AcademicYear,
    Attendance,
    Classroom,
    Exam,
    Fee,
    GradeLevel,
    GradeRecord,
    Student,
    Subject,
    Teacher,
    TimetableEntry,
)


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(widget, (forms.SelectMultiple, forms.Select)):
                widget.attrs.setdefault('class', 'form-select')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'form-control')
                widget.attrs.setdefault('rows', 3)
            else:
                widget.attrs.setdefault('class', 'form-control')


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })


class AcademicYearForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class GradeLevelForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = GradeLevel
        fields = ['name', 'order']


class SubjectForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description']


class ClassroomForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['grade', 'section', 'academic_year', 'class_teacher', 'capacity']


class TeacherForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'employee_id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'hire_date',
            'subjects',
            'is_active',
        ]
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'subjects': forms.CheckboxSelectMultiple(),
        }


class StudentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'admission_number',
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'email',
            'phone',
            'address',
            'guardian_name',
            'guardian_phone',
            'enrollment_date',
            'classroom',
            'is_active',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'enrollment_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TimetableForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = ['classroom', 'subject', 'teacher', 'day', 'start_time', 'end_time', 'room']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class ExamForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'subject', 'classroom', 'exam_date', 'max_score', 'academic_year']
        widgets = {'exam_date': forms.DateInput(attrs={'type': 'date'})}


def _student_choice_label(student):
    label = f'{student.admission_number} — {student.full_name}'
    if student.classroom:
        label += f' ({student.classroom.display_name})'
    return label


class GradeRecordForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = GradeRecord
        fields = ['exam', 'student', 'score', 'remarks']


class FeeForm(StyledFormMixin, forms.ModelForm):
    student = forms.ModelChoiceField(
        queryset=Student.objects.filter(is_active=True).select_related('classroom__grade').order_by(
            'last_name', 'first_name',
        ),
        widget=forms.Select(attrs={'class': 'form-select searchable-select'}),
        label='Student',
    )

    class Meta:
        model = Fee
        fields = ['student', 'title', 'amount', 'due_date', 'status', 'paid_amount', 'paid_on']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'paid_on': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].label_from_instance = _student_choice_label


class AttendanceBulkForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    classroom = forms.ModelChoiceField(
        queryset=Classroom.objects.select_related('grade', 'academic_year'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class AttendanceRowForm(forms.Form):
    student_id = forms.IntegerField(widget=forms.HiddenInput)
    status = forms.ChoiceField(
        choices=Attendance.Status.choices,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}),
    )
