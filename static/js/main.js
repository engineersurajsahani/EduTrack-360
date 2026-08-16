// EduTrack 360 - Main JavaScript & Interactive Elements

document.addEventListener('DOMContentLoaded', () => {
    // Initialize Circular Progress Bars
    document.querySelectorAll('.progress-circle-fill').forEach(circle => {
        const percent = parseFloat(circle.getAttribute('data-percentage') || 0);
        const radius = circle.r.baseVal.value;
        const circumference = 2 * Math.PI * radius;
        
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        const offset = circumference - (percent / 100) * circumference;
        circle.style.strokeDashoffset = offset;
    });

    // Auto-dismiss Alerts after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});
