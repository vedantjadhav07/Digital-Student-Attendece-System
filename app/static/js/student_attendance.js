/**
 * Student Attendance Submission Handler
 */
function submitStudentAttendance(sessionId) {
    const markBtn = document.getElementById('markAttendanceBtn');
    const msgContainer = document.getElementById('attendanceFeedbackMsg');
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    if (markBtn) {
        markBtn.disabled = true;
        markBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Verifying Workstation...';
    }

    if (msgContainer) {
        msgContainer.innerHTML = '';
    }

    const formData = new FormData();
    if (sessionId) {
        formData.append('session_id', sessionId);
    }

    const headers = {};
    if (csrfToken) {
        headers['X-CSRFToken'] = csrfToken;
    }

    fetch('/attendance/submit', {
        method: 'POST',
        headers: headers,
        body: formData
    })
    .then(res => res.json().then(data => ({ status: res.status, ok: res.ok, body: data })))
    .then(result => {
        const data = result.body;
        if (result.ok && data.success) {
            if (markBtn) {
                markBtn.className = 'btn btn-success w-100 py-3 fw-bold fs-5 shadow';
                markBtn.innerHTML = `<i class="bi bi-check-circle-fill me-2"></i> ATTENDANCE RECORDED (Seat #${data.seat_number})`;
            }

            if (msgContainer) {
                msgContainer.innerHTML = `
                    <div class="alert alert-success d-flex align-items-center mt-3 shadow-sm border-0">
                        <i class="bi bi-shield-check fs-4 me-3"></i>
                        <div>
                            <div class="fw-bold">${data.message}</div>
                            <small class="text-muted">Recorded at ${data.timestamp || 'Just now'} | Workstation #${data.seat_number}</small>
                        </div>
                    </div>
                `;
            }
            showToast(data.message, 'success');
        } else {
            if (markBtn) {
                markBtn.disabled = false;
                markBtn.innerHTML = '<i class="bi bi-fingerprint me-2"></i> RETRY ATTENDANCE';
                markBtn.className = 'btn btn-primary w-100 py-3 fw-bold fs-5 shadow';
            }

            if (msgContainer) {
                msgContainer.innerHTML = `
                    <div class="alert alert-danger d-flex align-items-center mt-3 shadow-sm border-0">
                        <i class="bi bi-exclamation-triangle-fill fs-4 me-3"></i>
                        <div>
                            <div class="fw-bold">Verification Failed</div>
                            <small>${data.message || 'An error occurred. Please contact the lab faculty.'}</small>
                        </div>
                    </div>
                `;
            }
            showToast(data.message || 'Failed to mark attendance', 'danger');
        }
    })
    .catch(err => {
        console.error(err);
        if (markBtn) {
            markBtn.disabled = false;
            markBtn.innerHTML = '<i class="bi bi-fingerprint me-2"></i> RETRY ATTENDANCE';
        }
        if (msgContainer) {
            msgContainer.innerHTML = `
                <div class="alert alert-danger mt-3 shadow-sm">
                    <strong>Connection Error:</strong> Could not reach the attendance server. Please verify your lab connection.
                </div>
            `;
        }
    });
}

