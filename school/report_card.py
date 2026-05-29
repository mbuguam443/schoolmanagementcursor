"""Report card data for a student."""

from django.db.models import Count

from .models import AcademicYear, Attendance, GradeRecord, Student

SCHOOL_NAME = 'Kiambu Road School'


def build_report_card_context(student: Student, academic_year=None):
    student = (
        Student.objects.select_related('classroom__grade', 'classroom__academic_year')
        .get(pk=student.pk)
    )
    if academic_year is None:
        academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not academic_year and student.classroom:
            academic_year = student.classroom.academic_year

    grade_rows = []
    if academic_year:
        records = (
            GradeRecord.objects.filter(
                student=student,
                exam__academic_year=academic_year,
            )
            .select_related('exam', 'exam__subject')
            .order_by('exam__subject__name', '-exam__exam_date')
        )
        for record in records:
            grade_rows.append({
                'subject': record.exam.subject.name,
                'exam_name': record.exam.name,
                'exam_date': record.exam.exam_date,
                'score': record.score,
                'max_score': record.exam.max_score,
                'percentage': record.percentage,
                'letter_grade': record.letter_grade,
                'remarks': record.remarks,
            })

    attendance_stats = _attendance_stats(student, academic_year)
    overall_average = None
    if grade_rows:
        overall_average = round(
            sum(r['percentage'] for r in grade_rows) / len(grade_rows),
            1,
        )

    return {
        'school_name': SCHOOL_NAME,
        'student': student,
        'academic_year': academic_year,
        'grade_rows': grade_rows,
        'attendance_stats': attendance_stats,
        'overall_average': overall_average,
        'overall_letter': _letter_from_percentage(overall_average) if overall_average is not None else '—',
        'class_teacher': (
            student.classroom.class_teacher.full_name
            if student.classroom and student.classroom.class_teacher
            else '—'
        ),
    }


def _attendance_stats(student, academic_year):
    qs = Attendance.objects.filter(student=student)
    if academic_year:
        qs = qs.filter(
            date__gte=academic_year.start_date,
            date__lte=academic_year.end_date,
        )
    total = qs.count()
    if total == 0:
        return {
            'total_days': 0,
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0,
            'attendance_rate': None,
        }
    counts = qs.values('status').annotate(n=Count('id'))
    by_status = {r['status']: r['n'] for r in counts}
    present = by_status.get(Attendance.Status.PRESENT, 0)
    absent = by_status.get(Attendance.Status.ABSENT, 0)
    late = by_status.get(Attendance.Status.LATE, 0)
    excused = by_status.get(Attendance.Status.EXCUSED, 0)
    rate = round((present + late) / total * 100, 1)
    return {
        'total_days': total,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'attendance_rate': rate,
    }


def _letter_from_percentage(pct):
    if pct is None:
        return '—'
    if pct >= 90:
        return 'A'
    if pct >= 80:
        return 'B'
    if pct >= 70:
        return 'C'
    if pct >= 60:
        return 'D'
    return 'F'
