import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, FileResponse
from django.contrib import messages
from django.utils import timezone
from .models import Certificate, DigitalNOC, Badge, StudentBadge
from .pdf_generator import generate_certificate_pdf, generate_certificate_qr, generate_noc_pdf, generate_noc_qr
from core.decorators import role_required, admin_required, student_required

@login_required
def my_certificates_view(request):
    user = request.user
    student = getattr(user, 'student_profile', None)
    if not student:
        # If faculty or admin, list all generated certificates
        certificates = Certificate.objects.all().select_related('student__user')
        badges = StudentBadge.objects.all().select_related('student__user', 'badge')
        return render(request, 'certificates/all_certificates.html', {
            'certificates': certificates,
            'badges': badges
        })

    # Ensure milestones are checked
    student.check_and_award_milestones()
    
    certificates = Certificate.objects.filter(student=student).order_by('-issue_date')
    badges = StudentBadge.objects.filter(student=student).select_related('badge')
    
    return render(request, 'certificates/my_certificates.html', {
        'student': student,
        'certificates': certificates,
        'badges': badges
    })


def public_verify_certificate_view(request, cert_uuid):
    certificate = get_object_or_404(Certificate, uuid=cert_uuid)
    return render(request, 'certificates/verify_certificate.html', {
        'certificate': certificate,
        'student': certificate.student
    })


@login_required
def download_certificate_pdf_view(request, cert_id):
    certificate = get_object_or_404(Certificate, certificate_id=cert_id)
    
    # Check permissions (student themselves or faculty/admin)
    if request.user.is_student_user and certificate.student.user != request.user:
        messages.error(request, "Permission denied.")
        return redirect('certificates:my_certificates')

    base_url = request.build_absolute_uri('/')[:-1]
    if not certificate.qr_code or not os.path.exists(certificate.qr_code.path):
        generate_certificate_qr(certificate, base_url)

    if not certificate.pdf_file or not os.path.exists(certificate.pdf_file.path):
        generate_certificate_pdf(certificate)

    return FileResponse(open(certificate.pdf_file.path, 'rb'), content_type='application/pdf', filename=f"{certificate.certificate_id}.pdf")


@login_required
@student_required
def request_noc_view(request):
    student = request.user.student_profile
    existing_noc = DigitalNOC.objects.filter(student=student).first()

    if request.method == 'POST':
        purpose = request.POST.get('purpose', 'Semester Exam & Academic Clearance')
        if existing_noc:
            existing_noc.purpose = purpose
            existing_noc.save()
            messages.info(request, "NOC clearance request updated.")
        else:
            noc_num = DigitalNOC.objects.count() + 101
            noc_id = f"NOC-{timezone.now().year}-{noc_num:05d}"
            
            # Check if student already has 100% academic completion
            summary = student.get_submissions_summary()
            acad_clear = (summary['total_tasks'] > 0 and summary['approved'] == summary['total_tasks'])
            
            noc = DigitalNOC.objects.create(
                noc_id=noc_id,
                student=student,
                purpose=purpose,
                library_clearance=True,
                academic_clearance=acad_clear,
                department_clearance=True,
                lab_clearance=True,
                fees_clearance=True,
                is_approved=acad_clear,
            )
            base_url = request.build_absolute_uri('/')[:-1]
            generate_noc_qr(noc, base_url)
            if noc.is_approved:
                generate_noc_pdf(noc)
            messages.success(request, f"Digital NOC request submitted (NOC ID: {noc_id})!")
            return redirect('certificates:request_noc')

    return render(request, 'certificates/noc_status.html', {
        'student': student,
        'noc': existing_noc
    })


@login_required
@role_required('ADMIN', 'FACULTY', 'HOD')
def admin_noc_list_view(request):
    noc_list = DigitalNOC.objects.all().select_related('student__user', 'student__branch')
    return render(request, 'certificates/admin_noc_list.html', {'noc_list': noc_list})


@login_required
@role_required('ADMIN', 'FACULTY', 'HOD')
def update_noc_clearance_view(request, noc_id):
    noc = get_object_or_404(DigitalNOC, id=noc_id)
    if request.method == 'POST':
        noc.library_clearance = 'library_clearance' in request.POST
        noc.academic_clearance = 'academic_clearance' in request.POST
        noc.department_clearance = 'department_clearance' in request.POST
        noc.lab_clearance = 'lab_clearance' in request.POST
        noc.fees_clearance = 'fees_clearance' in request.POST
        noc.is_approved = noc.is_all_cleared
        if noc.is_approved:
            noc.approved_by = request.user
        
        base_url = request.build_absolute_uri('/')[:-1]
        if not noc.qr_code or not os.path.exists(noc.qr_code.path):
            generate_noc_qr(noc, base_url)
        if noc.is_approved:
            generate_noc_pdf(noc)

        noc.save()
        messages.success(request, f"Clearance updated for NOC: {noc.noc_id}")
        return redirect('certificates:admin_noc_list')

    return redirect('certificates:admin_noc_list')


def public_verify_noc_view(request, noc_uuid):
    noc = get_object_or_404(DigitalNOC, uuid=noc_uuid)
    return render(request, 'certificates/verify_noc.html', {
        'noc': noc,
        'student': noc.student
    })


@login_required
def download_noc_pdf_view(request, noc_id):
    noc = get_object_or_404(DigitalNOC, noc_id=noc_id)
    if not noc.is_approved:
        messages.error(request, "NOC is pending clearances and has not been approved yet.")
        return redirect('certificates:request_noc')

    base_url = request.build_absolute_uri('/')[:-1]
    if not noc.qr_code or not os.path.exists(noc.qr_code.path):
        generate_noc_qr(noc, base_url)

    if not noc.pdf_file or not os.path.exists(noc.pdf_file.path):
        generate_noc_pdf(noc)

    return FileResponse(open(noc.pdf_file.path, 'rb'), content_type='application/pdf', filename=f"{noc.noc_id}.pdf")
