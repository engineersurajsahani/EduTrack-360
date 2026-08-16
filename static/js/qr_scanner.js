// EduTrack 360 - Interactive QR Code Scanner Engine

let html5QrCode = null;

function onScanSuccess(decodedText, decodedResult) {
    console.log(`Scan result: ${decodedText}`);
    // Stop scanning once detected
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            handleScannedUrl(decodedText);
        }).catch(err => {
            console.error("Failed to stop scanner", err);
            handleScannedUrl(decodedText);
        });
    } else {
        handleScannedUrl(decodedText);
    }
}

function handleScannedUrl(urlOrToken) {
    const feedbackBox = document.getElementById('qr-scanner-feedback');
    if (feedbackBox) {
        feedbackBox.innerHTML = `
            <div class="alert alert-success d-flex align-items-center gap-2">
                <span class="material-symbols-outlined">check_circle</span>
                <div><strong>QR Detected!</strong> Redirecting to student progress dashboard...</div>
            </div>
        `;
    }

    // Check if the decoded text is an absolute or relative URL
    if (urlOrToken.startsWith('http://') || urlOrToken.startsWith('https://') || urlOrToken.startsWith('/')) {
        window.location.href = urlOrToken;
    } else {
        // Assume it is a token or PRN
        window.location.href = `/student/qr/${encodeURIComponent(urlOrToken)}/`;
    }
}

function startCameraScanner() {
    const readerElement = document.getElementById('qr-reader');
    if (!readerElement) return;

    html5QrCode = new Html5Qrcode("qr-reader");
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };

    html5QrCode.start(
        { facingMode: "environment" },
        config,
        onScanSuccess
    ).catch(err => {
        console.warn("Camera start failed, showing fallback instructions.", err);
        const feedbackBox = document.getElementById('qr-scanner-feedback');
        if (feedbackBox) {
            feedbackBox.innerHTML = `
                <div class="alert alert-warning d-flex align-items-center gap-2">
                    <span class="material-symbols-outlined">videocam_off</span>
                    <div>Camera permission required or device unavailable. You can upload an image of the QR Code below, or search by student PRN directly!</div>
                </div>
            `;
        }
    });
}

function stopCameraScanner() {
    if (html5QrCode && html5QrCode.isScanning) {
        html5QrCode.stop().then(() => {
            console.log("Scanner stopped.");
        });
    }
}

function scanQrImageFile(fileInput) {
    if (!fileInput.files || fileInput.files.length === 0) return;
    const imageFile = fileInput.files[0];
    const html5QrCodeScanner = new Html5Qrcode("qr-reader");
    html5QrCodeScanner.scanFile(imageFile, true)
        .then(decodedText => {
            onScanSuccess(decodedText, null);
        })
        .catch(err => {
            alert("No valid EduTrack 360 QR Code detected in this image. Please try another image.");
        });
}
