class TournamentTimer {
    constructor(tournamentId) {
        this.tournamentId = tournamentId;
        this.timerInterval = null;
        this.statusInterval = null;
        this.remainingSeconds = 0;
        this.status = 'PAUSED';
        this.isLevelChanging = false; // Flag to prevent multiple level changes

        this.elements = {
            timerDisplay: document.getElementById('timer-display'),
            blindsDisplay: document.getElementById('blinds-display'),
            anteDisplay: document.getElementById('ante-display'),
            statusBadge: document.getElementById('status-badge'),
            btnStart: document.getElementById('btn-start'),
            btnPause: document.getElementById('btn-pause'),
            btnNext: document.getElementById('btn-next'),
            btnPrev: document.getElementById('btn-prev'),
            btnBreak: document.getElementById('btn-break'),
            btnFinish: document.getElementById('btn-finish'),
            // Break Modal elements
            breakModal: document.getElementById('break-modal'),
            breakModalClose: document.getElementById('break-modal-close'),
            breakModalCancel: document.getElementById('break-modal-cancel'),
            breakModalConfirm: document.getElementById('break-modal-confirm'),
            breakDuration: document.getElementById('break-duration'),
        };

        this.init();
    }

    init() {
        this.fetchStatus();
        this.statusInterval = setInterval(() => this.fetchStatus(), 5000); // Sync every 5s
        this.startLocalTimer();

        if (this.elements.btnStart) {
            this.elements.btnStart.addEventListener('click', () => this.action('timer/start/'));
        }
        if (this.elements.btnPause) {
            this.elements.btnPause.addEventListener('click', () => this.action('timer/pause/'));
        }
        if (this.elements.btnNext) {
            this.elements.btnNext.addEventListener('click', () => this.action('level/next/'));
        }
        if (this.elements.btnPrev) {
            this.elements.btnPrev.addEventListener('click', () => this.action('level/prev/'));
        }
        if (this.elements.btnBreak) {
            this.elements.btnBreak.addEventListener('click', () => this.openBreakModal());
        }
        if (this.elements.btnFinish) {
            console.log('DEBUG: Finish button found, adding event listener');
            this.elements.btnFinish.addEventListener('click', () => {
                console.log('DEBUG: Finish button clicked');
                this.finishTournament();
            });
        } else {
            console.log('DEBUG: Finish button NOT found!');
        }

        // Break Modal event listeners
        if (this.elements.breakModalClose) {
            this.elements.breakModalClose.addEventListener('click', () => this.closeBreakModal());
        }
        if (this.elements.breakModalCancel) {
            this.elements.breakModalCancel.addEventListener('click', () => this.closeBreakModal());
        }
        if (this.elements.breakModalConfirm) {
            this.elements.breakModalConfirm.addEventListener('click', () => this.confirmBreak());
        }

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.elements.breakModal && !this.elements.breakModal.classList.contains('hidden')) {
                this.closeBreakModal();
            }
        });

        // Close modal on outside click
        if (this.elements.breakModal) {
            this.elements.breakModal.addEventListener('click', (e) => {
                if (e.target === this.elements.breakModal) {
                    this.closeBreakModal();
                }
            });
        }
    }

    async fetchStatus() {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/status/`);
            const data = await response.json();

            this.status = data.status;
            this.remainingSeconds = data.remaining_seconds;
            this.updateDisplay(data);
        } catch (error) {
            console.error('Error fetching status:', error);
        }
    }

    async action(endpoint) {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/${endpoint}`, {
                method: 'POST'
            });
            const data = await response.json();
            console.log('Action result:', data);
            this.fetchStatus(); // Immediate sync after action
        } catch (error) {
            console.error('Error performing action:', error);
        }
    }

    startLocalTimer() {
        if (this.timerInterval) clearInterval(this.timerInterval);

        this.timerInterval = setInterval(() => {
            if (this.status === 'RUNNING' && this.remainingSeconds > 0) {
                this.remainingSeconds--;
                this.updateTimerText();
                this.updateTimerColor();
                // Reset flag when timer is running normally
                this.isLevelChanging = false;
            } else if (this.status === 'RUNNING' && this.remainingSeconds <= 0 && !this.isLevelChanging) {
                // Timer reached 00:00, automatically go to next level
                this.isLevelChanging = true; // Set flag to prevent multiple calls
                this.autoNextLevel();
            }
        }, 1000);
    }

    updateTimerColor() {
        if (!this.elements.timerDisplay) return;

        // Remove existing color classes
        this.elements.timerDisplay.classList.remove('text-amber-500', 'text-red-500');

        // Add color based on remaining time
        if (this.remainingSeconds <= 60 && this.remainingSeconds > 30) {
            this.elements.timerDisplay.classList.add('text-amber-500');
        } else if (this.remainingSeconds <= 30) {
            this.elements.timerDisplay.classList.add('text-red-500');
        }
    }

    async autoNextLevel() {
        console.log('Timer reached 00:00, automatically advancing to next level...');

        // Show notification
        this.showLevelChangeNotification('Level Complete!', 'Moving to next level...');

        // Pause briefly to show the notification
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Go to next level
        await this.nextLevel();
    }

    async nextLevel() {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/level/next/`, {
                method: 'POST'
            });
            const data = await response.json();
            console.log('Next level result:', data);
            this.fetchStatus(); // Immediate sync after action
        } catch (error) {
            console.error('Error going to next level:', error);
        }
    }

    showLevelChangeNotification(title, message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[100] bg-primary text-primary-foreground rounded-xl px-8 py-6 shadow-2xl border-2 border-primary/50';
        notification.style.minWidth = '400px';
        notification.innerHTML = `
            <div class="text-center">
                <div class="text-3xl font-bold mb-2">${title}</div>
                <div class="text-lg opacity-90">${message}</div>
            </div>
        `;

        document.body.appendChild(notification);

        // Add entrance animation
        notification.style.opacity = '0';
        notification.style.transform = 'translate(-50%, -50%) scale(0.8)';
        setTimeout(() => {
            notification.style.transition = 'all 0.3s ease-out';
            notification.style.opacity = '1';
            notification.style.transform = 'translate(-50%, -50%) scale(1)';
        }, 10);

        // Remove after 2 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translate(-50%, -50%) scale(0.8)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 2000);
    }

    updateDisplay(data) {
        // Update Timer
        this.updateTimerText();

        // Update Blinds
        if (data.level) {
            if (this.elements.blindsDisplay) {
                this.elements.blindsDisplay.textContent = `${data.level.small_blind.toLocaleString()} / ${data.level.big_blind.toLocaleString()}`;
            }
            if (this.elements.anteDisplay) {
                this.elements.anteDisplay.textContent = data.level.ante.toLocaleString();
            }
        }

        // Update Status Badges
        this.updateStatusBadge(this.elements.statusBadge, data.status);

        // Update top status badge if exists
        const topBadge = document.getElementById('status-badge-top');
        if (topBadge) {
            this.updateStatusBadge(topBadge, data.status);
        }
    }

    updateStatusBadge(badge, status) {
        if (!badge) return;

        badge.textContent = status;

        // Remove all status classes
        badge.classList.remove('bg-green-600', 'bg-yellow-600', 'bg-gray-600', 'bg-blue-600', 'bg-red-600');
        badge.classList.remove('text-white');

        // Add appropriate color based on status
        switch(status) {
            case 'RUNNING':
                badge.classList.add('bg-green-600', 'text-white');
                break;
            case 'PAUSED':
                badge.classList.add('bg-yellow-600', 'text-white');
                break;
            case 'SCHEDULED':
                badge.classList.add('bg-gray-600', 'text-white');
                break;
            case 'BREAK':
                badge.classList.add('bg-blue-600', 'text-white');
                break;
            case 'FINISHED':
                badge.classList.add('bg-red-600', 'text-white');
                break;
        }
    }

    updateTimerText() {
        if (!this.elements.timerDisplay) return;

        const minutes = Math.floor(this.remainingSeconds / 60);
        const seconds = this.remainingSeconds % 60;
        this.elements.timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    openBreakModal() {
        if (this.elements.breakModal) {
            this.elements.breakModal.classList.remove('hidden');
            this.elements.breakDuration.focus();
        }
    }

    closeBreakModal() {
        if (this.elements.breakModal) {
            this.elements.breakModal.classList.add('hidden');
        }
    }

    async confirmBreak() {
        const duration = parseInt(this.elements.breakDuration.value) || 15;

        if (duration < 1 || duration > 120) {
            alert('Break duration must be between 1 and 120 minutes');
            return;
        }

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/break/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ duration: duration })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Break started:', data);
                this.fetchStatus();
                this.showLevelChangeNotification('Break Started', `${duration} minute break`);
                this.closeBreakModal();
            } else {
                const err = await response.json();
                alert(err.error || 'Failed to start break');
            }
        } catch (error) {
            console.error('Error starting break:', error);
            alert('Error starting break. Please try again.');
        }
    }

    async finishTournament() {
        console.log('DEBUG: finishTournament called');
        if (!confirm('⚠️ Finish this tournament?\n\nThis will mark the tournament as completed and cannot be undone.')) {
            console.log('DEBUG: User cancelled');
            return;
        }
        console.log('DEBUG: User confirmed, sending request...');

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/finish/`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Tournament finished:', data);
                alert('✅ Tournament has been marked as FINISHED!');
                this.fetchStatus();

                // Redirect to dashboard
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                const err = await response.json();
                alert(err.error || 'Failed to finish tournament');
            }
        } catch (error) {
            console.error('Error finishing tournament:', error);
            alert('Error finishing tournament. Please try again.');
        }
    }
}
