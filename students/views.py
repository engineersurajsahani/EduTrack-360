import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import StudentProfile
from academics.models import Subject, SubjectTask, Submission
from activities.models import ActivityCertificate
from certificates.models import Certificate, StudentBadge
from core.decorators import role_required, faculty_required

@login_required
def student_profile_view(request):
    user = request.user
    if user.is_student_user and hasattr(user, 'student_profile'):
        student = user.student_profile
        if request.method == 'POST':
            student.headline = request.POST.get('headline', student.headline)
            student.bio = request.POST.get('bio', student.bio)
            student.github_url = request.POST.get('github_url', student.github_url)
            student.linkedin_url = request.POST.get('linkedin_url', student.linkedin_url)
            student.skills = request.POST.get('skills', student.skills)
            student.save()
            messages.success(request, "Student portfolio details updated!")
            return redirect('students:profile')

        return render(request, 'students/profile.html', {'student': student})
    else:
        messages.info(request, "Please use the staff profile view.")
        return redirect('accounts:profile')


@login_required
def digital_id_card_view(request, student_id=None):
    if student_id and (request.user.is_faculty_user or request.user.is_admin_user):
        student = get_object_or_404(StudentProfile, id=student_id)
    elif hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
    else:
        return redirect('accounts:profile')

    # Ensure QR code exists
    base_url = request.build_absolute_uri('/')[:-1]
    if not student.qr_code_image or not os.path.exists(student.qr_code_image.path):
        student.generate_qr_code(base_url)
        student.save()

    return render(request, 'students/digital_id_card.html', {
        'student': student,
        'overall_progress': student.get_overall_progress(),
        'color_status': student.get_overall_color_status()
    })


def digital_portfolio_view(request, student_id=None, prn=None):
    """Publicly viewable and verifiable Student Digital Portfolio."""
    if prn:
        student = get_object_or_404(StudentProfile, prn=prn)
    elif student_id:
        student = get_object_or_404(StudentProfile, id=student_id)
    elif request.user.is_authenticated and hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
    else:
        return redirect('accounts:login')

    subjects_progress = student.get_all_subjects_progress()
    academic_pct = student.get_academic_percentage()
    activity_progress = student.get_all_activities_progress()
    approved_submissions = Submission.objects.filter(student=student, status=Submission.Status.APPROVED).select_related('task__subject')
    approved_activity_certs = ActivityCertificate.objects.filter(student=student, status=ActivityCertificate.Status.APPROVED).select_related('category')
    certificates = Certificate.objects.filter(student=student)
    badges = StudentBadge.objects.filter(student=student).select_related('badge')
    overall_progress = student.get_overall_progress()

    return render(request, 'students/digital_portfolio.html', {
        'student': student,
        'subjects_progress': subjects_progress,
        'academic_pct': academic_pct,
        'activity_progress': activity_progress,
        'approved_submissions': approved_submissions,
        'approved_activity_certs': approved_activity_certs,
        'certificates': certificates,
        'badges': badges,
        'overall_progress': overall_progress,
        'color_status': student.get_overall_color_status()
    })


def qr_student_progress_view(request, qr_token):
    """
    Main Innovation: Instant Student Progress Profile opened when Faculty scans Student QR.
    Contains full academic, activity status, and pending tasks with instant review action!
    """
    student = get_object_or_404(StudentProfile, qr_token=qr_token)
    
    subjects_progress = student.get_all_subjects_progress()
    academic_pct = student.get_academic_percentage()
    activity_progress = student.get_all_activities_progress()
    submissions_summary = student.get_submissions_summary()
    pending_tasks = student.get_pending_tasks_list()
    overall_progress = student.get_overall_progress()
    badges = StudentBadge.objects.filter(student=student).select_related('badge')
    certificates = Certificate.objects.filter(student=student)

    # If faculty is logged in, they can directly review submissions from this view
    is_faculty = request.user.is_authenticated and (request.user.is_faculty_user or request.user.is_admin_user)

    return render(request, 'students/qr_progress_profile.html', {
        'student': student,
        'subjects_progress': subjects_progress,
        'academic_pct': academic_pct,
        'activity_progress': activity_progress,
        'submissions_summary': submissions_summary,
        'pending_tasks': pending_tasks,
        'overall_progress': overall_progress,
        'color_status': student.get_overall_color_status(),
        'badges': badges,
        'certificates': certificates,
        'is_faculty': is_faculty,
    })


@login_required
@role_required('ADMIN', 'FACULTY', 'HOD')
def student_search_view(request):
    query = request.GET.get('q', '').strip()
    branch_id = request.GET.get('branch')
    semester_id = request.GET.get('semester')

    students = StudentProfile.objects.all().select_related('user', 'branch', 'semester', 'academic_year')

    if query:
        students = students.filter(
            Q(prn__icontains=query) |
            Q(roll_no__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query)
        )

    if branch_id:
        students = students.filter(branch_id=branch_id)
    if semester_id:
        students = students.filter(semester_id=semester_id)

    from academics.models import Branch, Semester
    branches = Branch.objects.all()
    semesters = Semester.objects.all()

    return render(request, 'students/student_search.html', {
        'students': students,
        'query': query,
        'branches': branches,
        'semesters': semesters,
        'selected_branch': branch_id,
        'selected_semester': semester_id,
    })
