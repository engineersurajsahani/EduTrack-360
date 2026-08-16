import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import timedelta, date

from accounts.models import User, Department, FacultyProfile
from academics.models import Program, Branch, AcademicYear, Semester, Division, Subject, SubjectTask, Submission
from activities.models import ActivityCategory, ActivityScheme, ActivityCertificate
from certificates.models import Badge, StudentBadge, Certificate, DigitalNOC
from students.models import StudentProfile
from certificates.pdf_generator import generate_certificate_pdf, generate_certificate_qr, generate_noc_pdf, generate_noc_qr

class Command(BaseCommand):
    help = 'Seeds complete realistic demo database for EduTrack 360.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Starting EduTrack 360 database seed..."))

        # 1. Admin User
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'System',
                'last_name': 'Administrator',
                'email': 'admin@edutrack360.ac.in',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Admin: admin / admin123"))

        # 2. Departments
        dept_comp, _ = Department.objects.get_or_create(
            code='COMP',
            defaults={'name': 'Computer Engineering', 'description': 'Department of Computer Engineering & Software Systems'}
        )
        dept_it, _ = Department.objects.get_or_create(
            code='IT',
            defaults={'name': 'Information Technology', 'description': 'Department of Information Technology'}
        )
        dept_mech, _ = Department.objects.get_or_create(
            code='MECH',
            defaults={'name': 'Mechanical Engineering', 'description': 'Department of Mechanical Engineering'}
        )

        # 3. Programs & Branches
        prog_be, _ = Program.objects.get_or_create(
            code='BE',
            defaults={'name': 'Bachelor of Engineering (B.E.)', 'duration_years': 4}
        )
        branch_ce, _ = Branch.objects.get_or_create(
            program=prog_be,
            code='CE',
            defaults={'name': 'Computer Engineering', 'department': dept_comp}
        )
        branch_it, _ = Branch.objects.get_or_create(
            program=prog_be,
            code='IT',
            defaults={'name': 'Information Technology', 'department': dept_it}
        )

        # 4. Academic Years & Semesters
        years_data = [
            (1, 'First Year (FE)', 'FE'),
            (2, 'Second Year (SE)', 'SE'),
            (3, 'Third Year (TE)', 'TE'),
            (4, 'Final Year (BE)', 'BE'),
        ]
        created_years = {}
        for y_num, y_name, y_code in years_data:
            ay, _ = AcademicYear.objects.get_or_create(
                year_number=y_num,
                defaults={'name': y_name, 'code': y_code}
            )
            created_years[y_num] = ay

        sem_map = [
            (1, 'I', 1), (2, 'II', 1),
            (3, 'III', 2), (4, 'IV', 2),
            (5, 'V', 3), (6, 'VI', 3),
            (7, 'VII', 4), (8, 'VIII', 4),
        ]
        created_sems = {}
        for s_num, s_roman, y_num in sem_map:
            sem, _ = Semester.objects.get_or_create(
                number=s_num,
                defaults={'roman_name': s_roman, 'academic_year': created_years[y_num]}
            )
            created_sems[s_num] = sem

        # Divisions
        div_a, _ = Division.objects.get_or_create(
            branch=branch_ce,
            semester=created_sems[3],
            name='A'
        )

        # 5. Faculty Members
        # Main Faculty (Prof. Anjali Deshmukh)
        fac1_user, created = User.objects.get_or_create(
            username='faculty',
            defaults={
                'first_name': 'Anjali',
                'last_name': 'Deshmukh',
                'email': 'anjali.deshmukh@edutrack360.ac.in',
                'role': User.Role.FACULTY,
                'department': dept_comp,
                'is_staff': True,
            }
        )
        if created:
            fac1_user.set_password('faculty123')
            fac1_user.save()
        fac1_profile, _ = FacultyProfile.objects.get_or_create(
            user=fac1_user,
            defaults={'employee_id': 'FAC-COMP-101', 'designation': 'Assistant Professor', 'qualification': 'M.Tech (Computer Science)'}
        )

        # HOD (Dr. S. K. Sharma)
        hod_user, created = User.objects.get_or_create(
            username='prof_sharma',
            defaults={
                'first_name': 'Suresh',
                'last_name': 'Sharma',
                'email': 'hod.comp@edutrack360.ac.in',
                'role': User.Role.HOD,
                'department': dept_comp,
                'is_staff': True,
            }
        )
        if created:
            hod_user.set_password('faculty123')
            hod_user.save()
        hod_profile, _ = FacultyProfile.objects.get_or_create(
            user=hod_user,
            defaults={'employee_id': 'HOD-COMP-001', 'designation': 'Professor & Head of Department', 'qualification': 'Ph.D. (AI & Systems)'}
        )

        # 6. Subjects (B.E. Computer Engineering - Semester III)
        subjects_spec = [
            ('DCN', 'Data Communication & Networks', 4, fac1_profile, 30, 30, 25, 15),
            ('JAVA', 'Java Programming', 4, fac1_profile, 30, 30, 25, 15),
            ('OOP', 'Object Oriented Programming', 4, hod_profile, 30, 30, 25, 15),
            ('DBMS', 'Database Management Systems', 4, fac1_profile, 30, 30, 25, 15),
            ('CG', 'Computer Graphics & Animation', 3, hod_profile, 30, 30, 25, 15),
        ]
        created_subjects = {}
        for code, name, credits, fac, w_a, w_m, w_p, w_ppt in subjects_spec:
            sub, _ = Subject.objects.get_or_create(
                branch=branch_ce,
                semester=created_sems[3],
                code=code,
                defaults={
                    'name': name,
                    'credits': credits,
                    'assigned_faculty': fac,
                    'assignment_weight': w_a,
                    'microproject_weight': w_m,
                    'practical_weight': w_p,
                    'ppt_manual_weight': w_ppt,
                    'syllabus_summary': f"Standard curriculum and industry practicals for {name}."
                }
            )
            created_subjects[code] = sub

        # 7. Create Standard Tasks for each Subject
        tasks_lookup = {}
        for code, sub in created_subjects.items():
            tasks_lookup[code] = []
            # 4 Assignments
            for i in range(1, 5):
                t, _ = SubjectTask.objects.get_or_create(
                    subject=sub,
                    task_type=SubjectTask.TaskType.ASSIGNMENT,
                    task_number=i,
                    defaults={
                        'title': f"{code} Assignment {i}",
                        'description': f"Comprehensive problem solving and conceptual assignment #{i} for {sub.name}.",
                        'max_marks': 25,
                        'due_date': date(2026, 9, 15) + timedelta(days=i*10),
                    }
                )
                tasks_lookup[code].append(t)

            # Microproject (Proposal, Report, PPT, Viva/Demo)
            for m_type, m_title, num in [
                (SubjectTask.TaskType.MICROPROJECT, f"{code} Microproject Proposal", 1),
                (SubjectTask.TaskType.REPORT, f"{code} Microproject Report", 2),
                (SubjectTask.TaskType.PPT, f"{code} Microproject PPT", 3),
                (SubjectTask.TaskType.VIVA, f"{code} Microproject Demo & Viva", 4),
            ]:
                t, _ = SubjectTask.objects.get_or_create(
                    subject=sub,
                    task_type=m_type,
                    task_number=num,
                    defaults={
                        'title': m_title,
                        'description': f"Milestone #{num} for {sub.name} Capstone/Microproject.",
                        'max_marks': 50,
                        'due_date': date(2026, 10, 20) + timedelta(days=num*7),
                    }
                )
                tasks_lookup[code].append(t)

            # 3 Practicals & 1 Manual
            for p_num in range(1, 4):
                t, _ = SubjectTask.objects.get_or_create(
                    subject=sub,
                    task_type=SubjectTask.TaskType.PRACTICAL,
                    task_number=p_num,
                    defaults={
                        'title': f"{code} Practical {p_num}",
                        'description': f"Hands-on lab experiment #{p_num} with code implementation.",
                        'max_marks': 25,
                        'due_date': date(2026, 9, 30) + timedelta(days=p_num*7),
                    }
                )
                tasks_lookup[code].append(t)

            t_man, _ = SubjectTask.objects.get_or_create(
                subject=sub,
                task_type=SubjectTask.TaskType.MANUAL,
                task_number=1,
                defaults={
                    'title': f"{code} Complete Lab Manual",
                    'description': f"Signed and verified laboratory journal / manual for {sub.name}.",
                    'max_marks': 25,
                    'due_date': date(2026, 11, 15),
                }
            )
            tasks_lookup[code].append(t_man)

        # 8. Activity Categories & Schemes
        act_categories_data = [
            ('NSS', 'NSS (National Service Scheme)', 'volunteer_activism', 'success', 25, 10),
            ('CULTURAL', 'Cultural Activities & Performing Arts', 'theater_comedy', 'danger', 25, 10),
            ('SPORTS', 'Sports & Physical Fitness', 'emoji_events', 'warning', 25, 10),
            ('INTERNSHIP', 'Internship & Industrial Training', 'work', 'primary', 25, 10),
            ('WORKSHOP', 'Workshops & Technical Bootcamps', 'build', 'info', 25, 10),
            ('HACKATHON', 'Hackathons & Project Competitions', 'code', 'dark', 25, 10),
            ('COURSES', 'Online Certifications (NPTEL/Coursera)', 'school', 'primary', 25, 10),
            ('RESEARCH', 'Research Papers & Patents', 'menu_book', 'secondary', 25, 10),
        ]
        created_cats = {}
        for code, name, icon, col, target_pts, weight in act_categories_data:
            cat, _ = ActivityCategory.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'icon': icon,
                    'color_class': col,
                    'target_points': target_pts,
                    'weight_percentage': weight,
                }
            )
            created_cats[code] = cat

        # Standard Schemes
        schemes_data = [
            ('NSS', 'Tree Plantation Drive', 5),
            ('NSS', 'Blood Donation Camp', 5),
            ('NSS', '7-Day Residential NSS Camp', 15),
            ('NSS', 'Swachh Bharat Cleanliness Rally', 5),
            ('CULTURAL', 'Dance / Singing Competition (Participant)', 5),
            ('CULTURAL', 'State Level Cultural Winner (1st Prize)', 15),
            ('CULTURAL', 'Drama / Skit / Anchoring Lead', 10),
            ('SPORTS', 'Inter-Collegiate Sports Participant', 5),
            ('SPORTS', 'Zonal / State Tournament Winner', 15),
            ('INTERNSHIP', '1-3 Months Industry Internship', 20),
            ('WORKSHOP', '2-Day Technical Hands-on Workshop', 5),
            ('HACKATHON', 'Hackathon 1st / 2nd Prize Winner', 20),
            ('COURSES', 'NPTEL / Coursera Elite Certificate', 10),
        ]
        for c_code, s_name, pts in schemes_data:
            ActivityScheme.objects.get_or_create(
                category=created_cats[c_code],
                activity_name=s_name,
                defaults={'default_points': pts}
            )

        # 9. Students
        # Main Demo Student (Sayali Virkar - from Plan 1 & Plan 2)
        s1_user, created = User.objects.get_or_create(
            username='sayali',
            defaults={
                'first_name': 'Sayali',
                'last_name': 'Virkar',
                'email': 'sayali.virkar@edutrack360.ac.in',
                'role': User.Role.STUDENT,
                'phone': '+91 98765 43210',
            }
        )
        if created:
            s1_user.set_password('student123')
            s1_user.save()

        s1_profile, _ = StudentProfile.objects.get_or_create(
            user=s1_user,
            defaults={
                'prn': '2026CE025',
                'roll_no': '25',
                'program': prog_be,
                'branch': branch_ce,
                'academic_year': created_years[2],
                'semester': created_sems[3],
                'division': div_a,
                'attendance_percentage': 92.0,
                'headline': 'Computer Engineering Student | Full Stack & Cloud Enthusiast',
                'skills': 'Python, Django, Java, SQL, React, IoT, AWS',
                'github_url': 'https://github.com/sayalivirkar',
                'linkedin_url': 'https://linkedin.com/in/sayalivirkar',
            }
        )
        s1_profile.generate_qr_code("http://127.0.0.1:8000")
        s1_profile.save()

        # Demo Student 2 (Rahul Patil)
        s2_user, created = User.objects.get_or_create(
            username='rahul',
            defaults={
                'first_name': 'Rahul',
                'last_name': 'Patil',
                'email': 'rahul.patil@edutrack360.ac.in',
                'role': User.Role.STUDENT,
                'phone': '+91 98765 43211',
            }
        )
        if created:
            s2_user.set_password('student123')
            s2_user.save()

        s2_profile, _ = StudentProfile.objects.get_or_create(
            user=s2_user,
            defaults={
                'prn': '2026CE018',
                'roll_no': '18',
                'program': prog_be,
                'branch': branch_ce,
                'academic_year': created_years[2],
                'semester': created_sems[3],
                'division': div_a,
                'attendance_percentage': 88.0,
            }
        )
        s2_profile.generate_qr_code("http://127.0.0.1:8000")
        s2_profile.save()

        # Demo Student 3 (Neha Kulkarni)
        s3_user, created = User.objects.get_or_create(
            username='neha',
            defaults={
                'first_name': 'Neha',
                'last_name': 'Kulkarni',
                'email': 'neha.kulkarni@edutrack360.ac.in',
                'role': User.Role.STUDENT,
                'phone': '+91 98765 43212',
            }
        )
        if created:
            s3_user.set_password('student123')
            s3_user.save()

        s3_profile, _ = StudentProfile.objects.get_or_create(
            user=s3_user,
            defaults={
                'prn': '2026CE042',
                'roll_no': '42',
                'program': prog_be,
                'branch': branch_ce,
                'academic_year': created_years[2],
                'semester': created_sems[3],
                'division': div_a,
                'attendance_percentage': 95.0,
            }
        )
        s3_profile.generate_qr_code("http://127.0.0.1:8000")
        s3_profile.save()

        # 10. Seed Realistic Submissions for Sayali Virkar (as outlined in plan)
        # Helper to create dummy sample file
        dummy_content = b"%PDF-1.4 EduTrack 360 Sample Submission Document"
        
        # DCN (100% complete)
        for task in tasks_lookup['DCN']:
            sub, _ = Submission.objects.get_or_create(
                task=task,
                student=s1_profile,
                defaults={
                    'status': Submission.Status.APPROVED,
                    'marks_obtained': 24.0,
                    'faculty_remark': 'Excellent work! Accurate network packet captures and explanations.',
                    'reviewed_by': fac1_profile,
                    'reviewed_at': timezone.now(),
                }
            )
            if not sub.submission_file:
                sub.submission_file.save(f"sub_{s1_profile.prn}_{task.id}.pdf", ContentFile(dummy_content))

        # Java (Assignments 1 & 2 Approved, Assignment 3 Pending, Assignment 4 Not submitted, Microproject Report Approved)
        java_tasks = tasks_lookup['JAVA']
        for i, task in enumerate(java_tasks):
            if i in [0, 1, 4, 5, 8, 9]: # Approved
                sub, _ = Submission.objects.get_or_create(
                    task=task,
                    student=s1_profile,
                    defaults={
                        'status': Submission.Status.APPROVED,
                        'marks_obtained': 23.5,
                        'faculty_remark': 'Well implemented OOP classes and proper exception handling.',
                        'reviewed_by': fac1_profile,
                        'reviewed_at': timezone.now(),
                    }
                )
                if not sub.submission_file:
                    sub.submission_file.save(f"sub_{s1_profile.prn}_{task.id}.pdf", ContentFile(dummy_content))
            elif i == 2: # Assignment 3 Pending
                sub, _ = Submission.objects.get_or_create(
                    task=task,
                    student=s1_profile,
                    defaults={
                        'status': Submission.Status.PENDING,
                        'student_notes': 'Implemented Java Collections & Multithreading modules.',
                    }
                )
                if not sub.submission_file:
                    sub.submission_file.save(f"sub_{s1_profile.prn}_{task.id}.pdf", ContentFile(dummy_content))

        # OOP (Manual Rejected with Remark from plan: "Please correct conclusion section", some approved)
        oop_tasks = tasks_lookup['OOP']
        for i, task in enumerate(oop_tasks):
            if task.task_type == SubjectTask.TaskType.MANUAL:
                sub, _ = Submission.objects.get_or_create(
                    task=task,
                    student=s1_profile,
                    defaults={
                        'status': Submission.Status.REJECTED,
                        'marks_obtained': 10.0,
                        'faculty_remark': 'Please correct the conclusion section and add code flowcharts.',
                        'reviewed_by': hod_profile,
                        'reviewed_at': timezone.now(),
                    }
                )
                if not sub.submission_file:
                    sub.submission_file.save(f"sub_{s1_profile.prn}_{task.id}.pdf", ContentFile(dummy_content))
            elif i in [0, 1, 4, 8]:
                sub, _ = Submission.objects.get_or_create(
                    task=task,
                    student=s1_profile,
                    defaults={
                        'status': Submission.Status.APPROVED,
                        'marks_obtained': 22.0,
                        'faculty_remark': 'Good C++ polymorphism examples.',
                        'reviewed_by': hod_profile,
                        'reviewed_at': timezone.now(),
                    }
                )
                if not sub.submission_file:
                    sub.submission_file.save(f"sub_{s1_profile.prn}_{task.id}.pdf", ContentFile(dummy_content))

        # DBMS (90% complete)
        for i, task in enumerate(tasks_lookup['DBMS']):
            if i != 3: # 1 task pending
                sub, _ = Submission.objects.get_or_create(
                    task=task,
                    student=s1_profile,
                    defaults={
                        'status': Submission.Status.APPROVED,
                        'marks_obtained': 24.5,
                        'faculty_remark': 'Normalized SQL schemas and clean ER diagrams.',
                        'reviewed_by': fac1_profile,
                        'reviewed_at': timezone.now(),
                    }
                )
                if not sub.submission_file:
                    sub.submission_file.save(f"sub_{s1_profile.prn}_{task.id}.pdf", ContentFile(dummy_content))

        # 11. Seed Activity Certificates for Sayali Virkar
        activity_entries = [
            ('NSS', 'Annual Tree Plantation Drive 2026', 'Rotary & MSBTE NSS Unit', date(2026, 7, 15), ActivityCertificate.Level.COLLEGE, ActivityCertificate.AchievementRole.PARTICIPANT, ActivityCertificate.Status.APPROVED, 10, 'Actively planted 20 saplings on campus.'),
            ('NSS', 'National Blood Donation Camp', 'Red Cross Society', date(2026, 6, 20), ActivityCertificate.Level.DISTRICT, ActivityCertificate.AchievementRole.VOLUNTEER, ActivityCertificate.Status.APPROVED, 10, 'Organized registration and donor certificates.'),
            ('CULTURAL', 'Inter-College Solo Classical Dance', 'University Youth Festival', date(2026, 5, 10), ActivityCertificate.Level.STATE, ActivityCertificate.AchievementRole.WINNER, ActivityCertificate.Status.APPROVED, 20, '1st Prize Winner representing college at State level.'),
            ('SPORTS', 'Inter-Department Badminton Championship', 'Sports Council', date(2026, 4, 18), ActivityCertificate.Level.COLLEGE, ActivityCertificate.AchievementRole.WINNER, ActivityCertificate.Status.APPROVED, 15, 'Champion in Women Singles Tournament.'),
            ('WORKSHOP', 'AWS Cloud Architect Bootcamp', 'AWS Educate & Dept of COMP', date(2026, 3, 25), ActivityCertificate.Level.STATE, ActivityCertificate.AchievementRole.COMPLETED, ActivityCertificate.Status.APPROVED, 10, 'Successfully completed hands-on cloud architecture workshop.'),
            ('INTERNSHIP', 'Software Developer Intern (Python/Django)', 'TechCorp Solutions Pvt Ltd', date(2026, 2, 28), ActivityCertificate.Level.STATE, ActivityCertificate.AchievementRole.COMPLETED, ActivityCertificate.Status.APPROVED, 20, 'Completed 8-week production web application development.'),
            ('COURSES', 'NPTEL: Joy of Computing using Python', 'IIT Madras & SWAYAM', date(2026, 1, 15), ActivityCertificate.Level.NATIONAL, ActivityCertificate.AchievementRole.WINNER, ActivityCertificate.Status.APPROVED, 15, 'Elite + Silver Medal (Score: 88%).'),
        ]

        for cat_code, title, org, ev_date, lvl, role, stat, pts, remark in activity_entries:
            cert, _ = ActivityCertificate.objects.get_or_create(
                student=s1_profile,
                title=title,
                defaults={
                    'category': created_cats[cat_code],
                    'organization': org,
                    'event_date': ev_date,
                    'level': lvl,
                    'achievement_role': role,
                    'status': stat,
                    'points_awarded': pts,
                    'faculty_remark': remark,
                    'verified_by': fac1_profile,
                    'verified_at': timezone.now(),
                }
            )
            if not cert.certificate_file:
                cert.certificate_file.save(f"act_cert_{s1_profile.prn}_{cert.id}.pdf", ContentFile(dummy_content))

        # 12. Evaluate Milestones, Badges & Automatic Appreciation Certificates
        s1_profile.check_and_award_milestones()
        self.stdout.write(self.style.SUCCESS("Checked and generated badges & appreciation certificates for Sayali Virkar."))

        # 13. Create Digital NOC for Sayali Virkar
        noc, created = DigitalNOC.objects.get_or_create(
            student=s1_profile,
            defaults={
                'noc_id': 'NOC-2026-00125',
                'purpose': 'Semester Exam Clearance & Technical Internship Permission',
                'library_clearance': True,
                'academic_clearance': True,
                'department_clearance': True,
                'lab_clearance': True,
                'fees_clearance': True,
                'is_approved': True,
                'approved_by': hod_user,
            }
        )
        generate_noc_qr(noc, "http://127.0.0.1:8000")
        generate_noc_pdf(noc)

        self.stdout.write(self.style.SUCCESS("=================================================="))
        self.stdout.write(self.style.SUCCESS(" EduTrack 360 Database Successfully Seeded!"))
        self.stdout.write(self.style.SUCCESS("=================================================="))
        self.stdout.write(self.style.SUCCESS("Accounts Created:"))
        self.stdout.write(self.style.SUCCESS("  Admin:   username: admin        password: admin123"))
        self.stdout.write(self.style.SUCCESS("  Faculty: username: faculty      password: faculty123"))
        self.stdout.write(self.style.SUCCESS("  HOD:     username: prof_sharma  password: faculty123"))
        self.stdout.write(self.style.SUCCESS("  Student: username: sayali       password: student123  (PRN: 2026CE025)"))
        self.stdout.write(self.style.SUCCESS("  Student: username: rahul        password: student123  (PRN: 2026CE018)"))
        self.stdout.write(self.style.SUCCESS("  Student: username: neha         password: student123  (PRN: 2026CE042)"))
        self.stdout.write(self.style.SUCCESS("=================================================="))
