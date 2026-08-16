from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import ActivityCategory, ActivityCertificate, ActivityScheme
from .forms import ActivityCertificateUploadForm, ActivityCertificateReviewForm
from core.decorators import role_required, faculty_required, student_required

@login_required
def activity_hub_view(request):
    user = request.user
    categories = ActivityCategory.objects.all()
    student = getattr(user, 'student_profile', None)
    
    if student:
        category_progress = student.get_all_activities_progress()
        recent_certificates = ActivityCertificate.objects.filter(student=student).order_by('-submitted_at')[:10]
        return render(request, 'activities/activity_hub.html', {
            'categories': categories,
            'category_progress': category_progress,
            'recent_certificates': recent_certificates,
            'student': student
        })
    else:
        # Faculty or Admin view
        pending_certs = ActivityCertificate.objects.filter(status=ActivityCertificate.Status.PENDING).select_related('student__user', 'category')
        all_certs = ActivityCertificate.objects.all().select_related('student__user', 'category', 'verified_by__user')[:20]
        return render(request, 'activities/faculty_activity_hub.html', {
            'categories': categories,
            'pending_certs': pending_certs,
            'all_certs': all_certs
        })


@login_required
@student_required
def upload_activity_certificate_view(request):
    student = request.user.student_profile
    category_id = request.GET.get('category')
    initial_data = {}
    if category_id:
        initial_data['category'] = category_id

    if request.method == 'POST':
        form = ActivityCertificateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.student = student
            cert.status = ActivityCertificate.Status.PENDING
            cert.save()
            messages.success(request, f"Certificate for '{cert.title}' uploaded successfully! It is currently pending faculty verification.")
            return redirect('activities:activity_hub')
    else:
        form = ActivityCertificateUploadForm(initial=initial_data)

    schemes = ActivityScheme.objects.all().select_related('category')
    return render(request, 'activities/upload_certificate.html', {
        'form': form,
        'schemes': schemes,
        'student': student
    })


@login_required
def category_detail_view(request, category_code):
    category = get_object_or_404(ActivityCategory, code=category_code)
    user = request.user
    student = getattr(user, 'student_profile', None)
    
    if student:
        certificates = ActivityCertificate.objects.filter(student=student, category=category)
        earned_points = student.get_category_activity_points(category.code)
        pct = student.get_specific_category_pct(category.code, category.target_points)
    else:
        certificates = ActivityCertificate.objects.filter(category=category).select_related('student__user')
        earned_points = 0
        pct = 0

    schemes = category.schemes.all()

    return render(request, 'activities/category_detail.html', {
        'category': category,
        'certificates': certificates,
        'earned_points': earned_points,
        'pct': pct,
        'schemes': schemes,
        'student': student
    })


@login_required
@faculty_required
def review_activity_cert_view(request, cert_id):
    cert = get_object_or_404(ActivityCertificate, id=cert_id)
    if request.method == 'POST':
        form = ActivityCertificateReviewForm(request.POST, instance=cert)
        if form.is_valid():
            reviewed_cert = form.save(commit=False)
            if hasattr(request.user, 'faculty_profile'):
                reviewed_cert.verified_by = request.user.faculty_profile
            reviewed_cert.verified_at = timezone.now()
            reviewed_cert.save()
            
            # Trigger milestone calculations
            reviewed_cert.student.check_and_award_milestones()
            
            messages.success(request, f"Activity certificate for {reviewed_cert.student.user.get_full_name() or reviewed_cert.student.user.username} has been verified and awarded {reviewed_cert.points_awarded} points.")
            
            next_url = request.POST.get('next_url')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:faculty_dashboard')
            
    return redirect('dashboard:faculty_dashboard')
