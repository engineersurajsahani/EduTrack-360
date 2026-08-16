from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Subject, SubjectTask, Submission
from .forms import SubmissionForm, SubmissionReviewForm, SubjectTaskForm
from core.decorators import role_required, faculty_required, student_required

@login_required
def subject_list_view(request):
    user = request.user
    if user.is_student_user and hasattr(user, 'student_profile'):
        student = user.student_profile
        subjects_data = student.get_all_subjects_progress()
        academic_pct = student.get_academic_percentage()
        return render(request, 'academics/subject_list.html', {
            'subjects_data': subjects_data,
            'academic_pct': academic_pct,
            'student': student
        })
    elif user.is_faculty_user:
        faculty = getattr(user, 'faculty_profile', None)
        if faculty:
            subjects = Subject.objects.filter(assigned_faculty=faculty)
        else:
            subjects = Subject.objects.all()
        return render(request, 'academics/faculty_subject_list.html', {'subjects': subjects})
    else:
        # Admin
        subjects = Subject.objects.all().select_related('branch', 'semester', 'assigned_faculty__user')
        return render(request, 'academics/admin_subject_list.html', {'subjects': subjects})


@login_required
def subject_detail_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    user = request.user
    
    # Task collections
    assignments = subject.tasks.filter(task_type=SubjectTask.TaskType.ASSIGNMENT)
    microprojects = subject.tasks.filter(task_type__in=[SubjectTask.TaskType.MICROPROJECT, SubjectTask.TaskType.REPORT, SubjectTask.TaskType.VIVA])
    practicals = subject.tasks.filter(task_type=SubjectTask.TaskType.PRACTICAL)
    ppt_manuals = subject.tasks.filter(task_type__in=[SubjectTask.TaskType.PPT, SubjectTask.TaskType.MANUAL])

    student_stats = None
    submissions_dict = {}

    if user.is_student_user and hasattr(user, 'student_profile'):
        student = user.student_profile
        student_stats = student.get_subject_progress(subject)
        for sub in Submission.objects.filter(student=student, task__subject=subject):
            submissions_dict[sub.task_id] = sub

    return render(request, 'academics/subject_detail.html', {
        'subject': subject,
        'assignments': assignments,
        'microprojects': microprojects,
        'practicals': practicals,
        'ppt_manuals': ppt_manuals,
        'student_stats': student_stats,
        'submissions_dict': submissions_dict,
    })


@login_required
def task_detail_view(request, task_id):
    task = get_object_or_404(SubjectTask, id=task_id)
    user = request.user
    submission = None
    form = None
    review_form = None

    if user.is_student_user and hasattr(user, 'student_profile'):
        student = user.student_profile
        submission = Submission.objects.filter(task=task, student=student).first()
        if request.method == 'POST':
            form = SubmissionForm(request.POST, request.FILES, instance=submission)
            if form.is_valid():
                sub = form.save(commit=False)
                sub.task = task
                sub.student = student
                sub.status = Submission.Status.PENDING
                sub.save()
                messages.success(request, f"Submission for '{task.title}' uploaded successfully! Status is now Pending Approval.")
                return redirect('academics:task_detail', task_id=task.id)
        else:
            form = SubmissionForm(instance=submission)

    elif user.is_faculty_user or user.is_admin_user:
        # If student_id query param is present, load that submission
        student_id = request.GET.get('student_id')
        if student_id:
            submission = Submission.objects.filter(task=task, student_id=student_id).first()
            if submission:
                review_form = SubmissionReviewForm(instance=submission)

    return render(request, 'academics/task_detail.html', {
        'task': task,
        'submission': submission,
        'form': form,
        'review_form': review_form,
    })


@login_required
@faculty_required
def review_submission_view(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    if request.method == 'POST':
        form = SubmissionReviewForm(request.POST, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            if hasattr(request.user, 'faculty_profile'):
                sub.reviewed_by = request.user.faculty_profile
            sub.reviewed_at = timezone.now()
            sub.save()
            
            # Check milestone awards for student automatically!
            sub.student.check_and_award_milestones()
            
            messages.success(request, f"Submission by {sub.student.user.get_full_name() or sub.student.user.username} has been marked as {sub.get_status_display()}.")
            
            # Redirect back to where faculty came from
            next_url = request.POST.get('next_url')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:faculty_dashboard')
    
    return redirect('dashboard:faculty_dashboard')


@login_required
@student_required
def submission_history_view(request):
    student = request.user.student_profile
    submissions = Submission.objects.filter(student=student).select_related('task__subject', 'reviewed_by__user').order_by('-submitted_at')
    summary = student.get_submissions_summary()
    
    return render(request, 'academics/submission_history.html', {
        'submissions': submissions,
        'summary': summary,
        'student': student
    })
