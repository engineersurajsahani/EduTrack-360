from django.conf import settings
from academics.models import Submission
from activities.models import ActivityCertificate

def global_context(request):
    """Provides global branding, user role flags, and pending notification counts."""
    context = {
        'APP_NAME': 'EduTrack 360',
        'TAGLINE': 'One QR Code, Complete Student Journey.',
        'COLLEGE_NAME': 'EduTrack 360 Institute of Technology',
    }
    
    if request.user.is_authenticated:
        user = request.user
        context['is_admin'] = user.is_admin_user
        context['is_faculty'] = user.is_faculty_user
        context['is_student'] = user.is_student_user
        context['is_hod'] = user.is_hod_user
        
        # Pending counts for faculty/admin badges
        if user.is_faculty_user or user.is_admin_user:
            context['pending_submissions_count'] = Submission.objects.filter(status=Submission.Status.PENDING).count()
            context['pending_activity_certs_count'] = ActivityCertificate.objects.filter(status=ActivityCertificate.Status.PENDING).count()
            context['total_pending_reviews'] = context['pending_submissions_count'] + context['pending_activity_certs_count']
            
        if user.is_student_user and hasattr(user, 'student_profile'):
            student = user.student_profile
            context['student_profile'] = student
            context['student_overall_progress'] = student.get_overall_progress()
            context['student_color_status'] = student.get_overall_color_status()
            
    return context
