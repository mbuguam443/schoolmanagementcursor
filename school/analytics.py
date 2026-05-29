"""Dashboard chart data builders."""

from datetime import timedelta

from django.db.models import Avg, Count, Q
from .models import Attendance, Fee, GradeRecord, Student


def _fill_date_range(start, end, daily_map, value_keys):
    """Build aligned labels and series for each day in [start, end]."""
    labels = []
    series = {k: [] for k in value_keys}
    current = start
    while current <= end:
        labels.append(current.strftime('%b %d'))
        day_data = daily_map.get(current, {})
        for k in value_keys:
            series[k].append(day_data.get(k, 0))
        current += timedelta(days=1)
    return labels, series


def attendance_daily(today, days=14):
    start = today - timedelta(days=days - 1)
    rows = (
        Attendance.objects.filter(date__gte=start, date__lte=today)
        .values('date')
        .annotate(
            present=Count('id', filter=Q(status=Attendance.Status.PRESENT)),
            absent=Count('id', filter=Q(status=Attendance.Status.ABSENT)),
            late=Count('id', filter=Q(status=Attendance.Status.LATE)),
        )
        .order_by('date')
    )
    daily_map = {
        r['date']: {
            'present': r['present'],
            'absent': r['absent'],
            'late': r['late'],
        }
        for r in rows
    }
    labels, series = _fill_date_range(start, today, daily_map, ['present', 'absent', 'late'])
    return {'labels': labels, **series}


def attendance_today_breakdown(today):
    status_labels = {
        Attendance.Status.PRESENT: 'Present',
        Attendance.Status.ABSENT: 'Absent',
        Attendance.Status.LATE: 'Late',
        Attendance.Status.EXCUSED: 'Excused',
    }
    rows = (
        Attendance.objects.filter(date=today)
        .values('status')
        .annotate(count=Count('id'))
    )
    counts = {r['status']: r['count'] for r in rows}
    labels = []
    data = []
    colors = {
        Attendance.Status.PRESENT: '#10b981',
        Attendance.Status.ABSENT: '#ef4444',
        Attendance.Status.LATE: '#f59e0b',
        Attendance.Status.EXCUSED: '#6366f1',
    }
    chart_colors = []
    for code, label in status_labels.items():
        if counts.get(code, 0) > 0:
            labels.append(label)
            data.append(counts[code])
            chart_colors.append(colors[code])
    return {'labels': labels, 'data': data, 'colors': chart_colors}


def students_by_classroom(limit=8):
    rows = (
        Student.objects.filter(is_active=True, classroom__isnull=False)
        .values('classroom__grade__name', 'classroom__section')
        .annotate(count=Count('id'))
        .order_by('-count')[:limit]
    )
    labels = [f"{r['classroom__grade__name']} {r['classroom__section']}" for r in rows]
    data = [r['count'] for r in rows]
    return {'labels': labels, 'data': data}


def fee_status_breakdown():
    status_labels = dict(Fee.Status.choices)
    colors = {
        Fee.Status.PAID: '#10b981',
        Fee.Status.PENDING: '#f59e0b',
        Fee.Status.PARTIAL: '#6366f1',
        Fee.Status.OVERDUE: '#ef4444',
    }
    rows = Fee.objects.values('status').annotate(count=Count('id'))
    labels = []
    data = []
    chart_colors = []
    for r in rows:
        labels.append(status_labels.get(r['status'], r['status']))
        data.append(r['count'])
        chart_colors.append(colors.get(r['status'], '#94a3b8'))
    return {'labels': labels, 'data': data, 'colors': chart_colors}


def grade_letter_distribution():
    dist = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    for record in GradeRecord.objects.select_related('exam').iterator():
        letter = record.letter_grade
        if letter in dist:
            dist[letter] += 1
    labels = list(dist.keys())
    data = [dist[k] for k in labels]
    return {'labels': labels, 'data': data}


def average_score_by_subject(limit=6):
    rows = (
        GradeRecord.objects.values('exam__subject__name')
        .annotate(avg_score=Avg('score'))
        .order_by('-avg_score')[:limit]
    )
    labels = [r['exam__subject__name'] or 'Unknown' for r in rows]
    data = [round(float(r['avg_score']), 1) for r in rows if r['avg_score'] is not None]
    return {'labels': labels[: len(data)], 'data': data}


def build_dashboard_charts(today):
    return {
        'attendance_daily': attendance_daily(today),
        'attendance_today': attendance_today_breakdown(today),
        'students_by_class': students_by_classroom(),
        'fee_status': fee_status_breakdown(),
        'grade_distribution': grade_letter_distribution(),
        'scores_by_subject': average_score_by_subject(),
    }
