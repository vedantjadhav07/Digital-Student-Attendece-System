/**
 * Live Workstation Monitoring Engine via WebSockets
 */
class LabMonitor {
    constructor(config) {
        this.sessionId = config.sessionId;
        this.capacity = config.capacity || 30;
        this.remainingSeconds = config.remainingSeconds || 0;
        this.isPaused = config.isPaused || false;
        this.socket = null;
        this.timerInterval = null;

        this.initElements();
        this.initSocket();
        this.startCountdown();
    }

    initElements() {
        this.timerDisplay = document.getElementById('sessionTimerDisplay');
        this.presentCounter = document.getElementById('livePresentCounter');
        this.capacityCounter = document.getElementById('liveCapacityCounter');
        this.completionProgressBar = document.getElementById('liveProgressBar');
        this.completionPercentageText = document.getElementById('livePercentageText');
        this.gridContainer = document.getElementById('workstationGrid');
    }

    initSocket() {
        if (typeof io === 'undefined') {
            console.warn('Socket.IO library not loaded.');
            return;
        }

        this.socket = io({
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000
        });

        this.socket.on('connect', () => {
            console.log('Connected to attendance monitor socket.');
            // Join isolated room
            this.socket.emit('join_session', { session_id: this.sessionId });
            showToast('Live monitoring connected.', 'success');
        });

        this.socket.on('disconnect', () => {
            console.warn('Disconnected from live socket.');
            showToast('Disconnected from live monitor. Attempting reconnect...', 'warning');
        });

        // Event: Student marked attendance
        this.socket.on('attendance_marked', (data) => {
            this.handleAttendanceMarked(data);
        });

        // Fallback global event
        this.socket.on('attendance_update', (data) => {
            if (data.pc_number) {
                this.updateSeatNode(parseInt(data.pc_number), data.student_name, null);
            }
        });

        // Event: Session extended
        this.socket.on('session_timer_extended', (data) => {
            this.remainingSeconds = data.remaining_seconds;
            showToast('Session extended by faculty!', 'info');
        });

        // Event: Status changed (pause/resume)
        this.socket.on('session_status_changed', (data) => {
            this.isPaused = data.is_paused;
            showToast(this.isPaused ? 'Attendance session PAUSED.' : 'Attendance session RESUMED.', 'warning');
        });

        // Event: Session ended
        this.socket.on('session_closed', () => {
            showToast('Attendance portal closed.', 'secondary');
            clearInterval(this.timerInterval);
            if (this.timerDisplay) {
                this.timerDisplay.textContent = 'SESSION ENDED';
                this.timerDisplay.className = 'badge bg-secondary fs-6 py-2 px-3';
            }
        });
    }

    handleAttendanceMarked(data) {
        const seatNum = parseInt(data.seat_number);
        this.updateSeatNode(seatNum, data.student_name, data.timestamp);

        // Update counts
        if (this.presentCounter && data.total_present !== undefined) {
            this.presentCounter.textContent = data.total_present;
        }

        if (this.completionProgressBar && data.completion_pct !== undefined) {
            this.completionProgressBar.style.width = `${data.completion_pct}%`;
            if (this.completionPercentageText) {
                this.completionPercentageText.textContent = `${data.completion_pct}%`;
            }
        }

        // Notification
        showToast(`Attendance marked: ${data.student_name} at Seat #${seatNum}`, 'success');
    }

    updateSeatNode(seatNum, studentName, timestamp) {
        const node = document.getElementById(`ws-seat-${seatNum}`);
        if (!node) return;

        node.className = 'ws-node status-attended just-marked';

        const iconEl = node.querySelector('.ws-icon i');
        if (iconEl) {
            iconEl.className = 'bi bi-person-check-fill';
        }

        const occupantEl = node.querySelector('.ws-occupant');
        if (occupantEl) {
            occupantEl.textContent = studentName || 'Attended';
            occupantEl.title = studentName || '';
        }

        const timeEl = node.querySelector('.ws-time');
        if (timeEl && timestamp) {
            timeEl.textContent = timestamp;
        }

        // Remove pulse class after 1.5s
        setTimeout(() => {
            node.classList.remove('just-marked');
        }, 1500);
    }

    startCountdown() {
        if (!this.timerDisplay) return;

        const updateDisplay = () => {
            if (this.isPaused) {
                this.timerDisplay.textContent = 'PAUSED';
                this.timerDisplay.className = 'badge bg-warning text-dark fs-6 py-2 px-3';
                return;
            }

            if (this.remainingSeconds <= 0) {
                this.timerDisplay.textContent = '00:00 (EXPIRED)';
                this.timerDisplay.className = 'badge bg-danger fs-6 py-2 px-3';
                return;
            }

            const m = Math.floor(this.remainingSeconds / 60);
            const s = this.remainingSeconds % 60;
            this.timerDisplay.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

            if (this.remainingSeconds <= 60) {
                this.timerDisplay.className = 'badge bg-danger fs-6 py-2 px-3 animate-pulse';
            } else if (this.remainingSeconds <= 180) {
                this.timerDisplay.className = 'badge bg-warning text-dark fs-6 py-2 px-3';
            } else {
                this.timerDisplay.className = 'badge bg-success fs-6 py-2 px-3';
            }

            this.remainingSeconds--;
        };

        updateDisplay();
        this.timerInterval = setInterval(updateDisplay, 1000);
    }
}

