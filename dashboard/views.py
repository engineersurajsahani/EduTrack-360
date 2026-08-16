import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Avg
from accounts.models import User, Department, FacultyProfile
from academics.models import Subject, SubjectTask, Submission, Branch, Semester, Program
from activities.models import ActivityCategory, ActivityCertificate
from certificates.models import Certificate, Badge, StudentBadge, DigitalNOC
from students.models import StudentProfile
from core.decorators import role_required, admin_required, faculty_required, student_required
from .export_utils import export_students_to_excel

@login_required
def redirect_view(request):
    """Smart router directing users to their appropriate dashboard."""
    user = request.user
    if user.is_admin_user:
        return redirect('dashboard:admin_dashboard')
    elif user.is_faculty_user:
        return redirect('dashboard:faculty_dashboard')
    elif user.is_student_user:
        return redirect('dashboard:student_dashboard')
    return redirect('accounts:profile')


@login_required
@student_required
def student_dashboard_view(request):
    student = request.user.student_profile
    
    # Calculate fresh data & awards
    student.check_and_award_milestones()
    
    overall_progress = student.get_overall_progress()
    color_status = student.get_overall_color_status()
    academic_pct = student.get_academic_percentage()
    subjects_progress = student.get_all_subjects_progress()
    activities_progress = student.get_all_activities_progress()
    submissions_summary = student.get_submissions_summary()
    pending_tasks = student.get_pending_tasks_list()
    badges = StudentBadge.objects.filter(student=student).select_related('badge')
    certificates = Certificate.objects.filter(student=student).order_by('-created_at')[:5]
    noc = DigitalNOC.objects.filter(student=student).first()

    # Chart data for Radar and Bar charts
    subject_labels = [s['subject'].code for s in subjects_progress]
    subject_scores = [s['weighted_score'] for s in subjects_progress]
    
    activity_labels = [a['category'].name for a in activities_progress]
    activity_scores = [a['percentage'] for a in activities_progress]

    context = {
        'student': student,
        'overall_progress': overall_progress,
        'color_status': color_status,
        'academic_pct': academic_pct,
        'subjects_progress': subjects_progress,
        'activities_progress': activities_progress,
        'submissions_summary': submissions_summary,
        'pending_tasks': pending_tasks,
        'badges': badges,
        'certificates': certificates,
        'noc': noc,
        'subject_labels_json': json.dumps(subject_labels),
        'subject_scores_json': json.dumps(subject_scores),
        'activity_labels_json': json.dumps(activity_labels),
        'activity_scores_json': json.dumps(activity_scores),
    }
    return render(request, 'dashboard/student_dashboard.html', context)


@login_required
@faculty_required
def faculty_dashboard_view(request):
    user = request.user
    faculty = getattr(user, 'faculty_profile', None)
    
    if faculty:
        assigned_subjects = Subject.objects.filter(assigned_faculty=faculty).select_related('branch', 'semester')
        subject_ids = assigned_subjects.values_list('id', flat=True)
        pending_submissions = Submission.objects.filter(task__subject_id__in=subject_ids, status=Submission.Status.PENDING).select_related('student__user', 'task__subject').order_by('-submitted_at')
    else:
        assigned_subjects = Subject.objects.all().select_related('branch', 'semester')
        pending_submissions = Submission.objects.filter(status=Submission.Status.PENDING).select_related('student__user', 'task__subject').order_by('-submitted_at')

    pending_activity_certs = ActivityCertificate.objects.filter(status=ActivityCertificate.Status.PENDING).select_related('student__user', 'category').order_by('-submitted_at')
    
    total_students_count = StudentProfile.objects.count()
    recent_reviews = Submission.objects.filter(status__in=[Submission.Status.APPROVED, Submission.Status.REJECTED]).select_related('student__user', 'task__subject').order_by('-reviewed_at')[:10]

    context = {
        'faculty': faculty,
        'assigned_subjects': assigned_subjects,
        'pending_submissions': pending_submissions,
        'pending_activity_certs': pending_activity_certs,
        'total_students_count': total_students_count,
        'recent_reviews': recent_reviews,
    }
    return render(request, 'dashboard/faculty_dashboard.html', context)


@login_required
@admin_required
def admin_dashboard_view(request):
    total_students = StudentProfile.objects.count()
    total_faculty = FacultyProfile.objects.count()
    total_subjects = Subject.objects.count()
    total_programs = Program.objects.count()
    total_branches = Branch.objects.count()
    
    pending_submissions_count = Submission.objects.filter(status=Submission.Status.PENDING).count()
    pending_certs_count = ActivityCertificate.objects.filter(status=ActivityCertificate.Status.PENDING).count()
    total_certificates_issued = Certificate.objects.count()
    
    departments = Department.objects.annotate(
        faculty_count=Count('users', filter=Q(users__role__in=['FACULTY', 'HOD'])),
        branch_count=Count('branches')
    )

    recent_students = StudentProfile.objects.all().select_related('user', 'branch', 'semester').order_by('-created_at')[:8]

    # Department analytics
    branches = Branch.objects.all().annotate(student_count=Count('students'))
    branch_labels = [b.code for b in branches]
    branch_counts = [b.student_count for b in branches]

    context = {
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_subjects': total_subjects,
        'total_programs': total_programs,
        'total_branches': total_branches,
        'pending_submissions_count': pending_submissions_count,
        'pending_certs_count': pending_certs_count,
        'total_certificates_issued': total_certificates_issued,
        'departments': departments,
        'recent_students': recent_students,
        'branch_labels_json': json.dumps(branch_labels),
        'branch_counts_json': json.dumps(branch_counts),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
@faculty_required
def qr_scanner_view(request):
    """Interactive camera-based QR code scanner page."""
    return render(request, 'dashboard/qr_scanner.html')


@login_required
def leaderboard_view(request):
    """Semester & College-wide Leaderboard based on overall performance."""
    branch_id = request.GET.get('branch')
    semester_id = request.GET.get('semester')

    students = StudentProfile.objects.all().select_related('user', 'branch', 'semester')
    if branch_id:
        students = students.filter(branch_id=branch_id)
    if semester_id:
        students = students.filter(semester_id=semester_id)

    # Compute overall score for each student
    ranked_students = []
    for s in students:
        overall = s.get_overall_progress()
        acad = s.get_academic_percentage()
        badges_count = s.badges.count()
        ranked_students.append({
            'student': s,
            'overall_progress': overall,
            'academic_pct': acad,
            'color_status': s.get_overall_color_status(),
            'badges_count': badges_count,
            'attendance': s.attendance_percentage,
        })

    # Sort descending by overall progress, then academic, then attendance
    ranked_students.sort(key=lambda x: (x['overall_progress'], x['academic_pct'], float(x['attendance'])), reverse=True)

    # Add 1-based rank
    for idx, item in enumerate(ranked_students, start=1):
        item['rank'] = idx

    branches = Branch.objects.all()
    semesters = Semester.objects.all()

    return render(request, 'dashboard/leaderboard.html', {
        'ranked_students': ranked_students,
        'branches': branches,
        'semesters': semesters,
        'selected_branch': branch_id,
        'selected_semester': semester_id,
    })


@login_required
@role_required('ADMIN', 'FACULTY', 'HOD')
def export_excel_view(request):
    branch_id = request.GET.get('branch')
    semester_id = request.GET.get('semester')
    students = StudentProfile.objects.all().select_related('user', 'branch', 'semester', 'academic_year')
    if branch_id:
        students = students.filter(branch_id=branch_id)
    if semester_id:
        students = students.filter(semester_id=semester_id)
    return export_students_to_excel(students)
