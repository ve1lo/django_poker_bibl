class PayoutManager {
    constructor(tournamentId) {
        this.tournamentId = tournamentId;
        this.currentEditingId = null;

        this.elements = {
            btnGenerate: document.getElementById('btn-generate-payouts'),
            btnAdd: document.getElementById('btn-add-payout'),
            payoutsList: document.getElementById('payouts-list-body'),
            prizePool: document.getElementById('payout-prize-pool'),
            placesPaid: document.getElementById('payout-places-paid'),

            // Modal elements
            modal: document.getElementById('payout-modal'),
            modalTitle: document.getElementById('payout-modal-title'),
            modalClose: document.getElementById('payout-modal-close'),
            modalCancel: document.getElementById('payout-modal-cancel'),
            modalSave: document.getElementById('payout-modal-save'),
            inputPlace: document.getElementById('payout-place'),
            inputAmount: document.getElementById('payout-amount'),
        };

        this.init();
    }

    init() {
        this.fetchPayouts();

        if (this.elements.btnGenerate) {
            this.elements.btnGenerate.addEventListener('click', () => this.generatePayouts());
        }

        if (this.elements.btnAdd) {
            this.elements.btnAdd.addEventListener('click', () => this.openAddModal());
        }

        if (this.elements.modalClose) {
            this.elements.modalClose.addEventListener('click', () => this.closeModal());
        }

        if (this.elements.modalCancel) {
            this.elements.modalCancel.addEventListener('click', () => this.closeModal());
        }

        if (this.elements.modalSave) {
            this.elements.modalSave.addEventListener('click', () => this.savePayout());
        }

        // Close modal on outside click
        if (this.elements.modal) {
            this.elements.modal.addEventListener('click', (e) => {
                if (e.target === this.elements.modal) {
                    this.closeModal();
                }
            });
        }

        // Close modal on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.elements.modal.classList.contains('hidden')) {
                this.closeModal();
            }
        });
    }

    async fetchPayouts() {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/payouts/`);
            const data = await response.json();

            console.log('DEBUG: Fetched payouts data:', data);
            this.renderPayouts(data);
        } catch (error) {
            console.error('Error fetching payouts:', error);
        }
    }

    renderPayouts(data) {
        if (!this.elements.payoutsList) return;

        // Update stats
        if (this.elements.prizePool) {
            this.elements.prizePool.textContent = `$${data.prize_pool.toLocaleString()}`;
        }
        if (this.elements.placesPaid) {
            this.elements.placesPaid.textContent = data.places_paid;
        }

        // Render table
        this.elements.payoutsList.innerHTML = '';

        if (data.payouts.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td colspan="4" class="p-8 text-center text-muted-foreground">
                    No payouts configured yet. Click "Generate Payouts" to create prize structure.
                </td>
            `;
            this.elements.payoutsList.appendChild(row);
            return;
        }

        data.payouts.forEach(payout => {
            const row = document.createElement('tr');
            row.className = "border-b transition-colors hover:bg-muted/50";

            const playerDisplay = payout.player_name
                ? `<span class="text-green-500">${payout.player_name}</span>`
                : '<span class="text-muted-foreground text-xs">Not awarded yet</span>';

            row.innerHTML = `
                <td class="p-4 align-middle">
                    <div class="flex items-center gap-2">
                        <span class="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold">
                            ${payout.place}
                        </span>
                        <span class="text-sm text-muted-foreground">${this.getPlaceSuffix(payout.place)} Place</span>
                    </div>
                </td>
                <td class="p-4 align-middle">
                    ${playerDisplay}
                </td>
                <td class="p-4 align-middle text-right">
                    <span class="text-lg font-bold text-green-500">$${payout.amount.toLocaleString()}</span>
                </td>
                <td class="p-4 align-middle text-right">
                    <div class="flex justify-end gap-1">
                        <button onclick="payoutManager.openEditModal(${payout.id}, ${payout.place}, ${payout.amount})"
                            class="h-8 w-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground"
                            title="Edit">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
                                <path d="m15 5 4 4"/>
                            </svg>
                        </button>
                        <button onclick="payoutManager.deletePayout(${payout.id})"
                            class="h-8 w-8 inline-flex items-center justify-center rounded-md bg-destructive/10 text-destructive hover:bg-destructive hover:text-destructive-foreground transition-colors"
                            title="Delete">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                            </svg>
                        </button>
                    </div>
                </td>
            `;
            this.elements.payoutsList.appendChild(row);
        });
    }

    getPlaceSuffix(place) {
        const j = place % 10;
        const k = place % 100;
        if (j === 1 && k !== 11) return place + 'st';
        if (j === 2 && k !== 12) return place + 'nd';
        if (j === 3 && k !== 13) return place + 'rd';
        return place + 'th';
    }

    async generatePayouts() {
        if (!confirm('Generate payouts? This will replace any existing payout structure.')) {
            return;
        }

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/payouts/generate/`, {
                method: 'POST',
            });

            if (response.ok) {
                const result = await response.json();
                this.showNotification(
                    `Payouts generated! ${result.places_paid} places paid from $${result.prize_pool.toLocaleString()} prize pool`,
                    'success'
                );
                this.fetchPayouts();
            } else {
                const err = await response.json();
                alert(err.error || 'Failed to generate payouts');
            }
        } catch (error) {
            console.error('Error generating payouts:', error);
            alert('Error generating payouts. Please try again.');
        }
    }

    openAddModal() {
        this.currentEditingId = null;
        this.elements.modalTitle.textContent = 'Add Payout';
        this.elements.inputPlace.value = '';
        this.elements.inputAmount.value = '';
        this.elements.modal.classList.remove('hidden');
        this.elements.inputPlace.focus();
    }

    openEditModal(id, place, amount) {
        this.currentEditingId = id;
        this.elements.modalTitle.textContent = 'Edit Payout';
        this.elements.inputPlace.value = place;
        this.elements.inputAmount.value = amount;
        this.elements.modal.classList.remove('hidden');
        this.elements.inputPlace.focus();
    }

    closeModal() {
        this.elements.modal.classList.add('hidden');
        this.currentEditingId = null;
    }

    async savePayout() {
        const place = parseInt(this.elements.inputPlace.value);
        const amount = parseInt(this.elements.inputAmount.value);

        if (!place || !amount) {
            alert('Place and amount are required');
            return;
        }

        try {
            const url = this.currentEditingId
                ? `/api/tournament/${this.tournamentId}/payouts/${this.currentEditingId}/update/`
                : `/api/tournament/${this.tournamentId}/payouts/add/`;

            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ place, amount })
            });

            if (response.ok) {
                this.showNotification(
                    this.currentEditingId ? 'Payout updated!' : 'Payout added!',
                    'success'
                );
                this.closeModal();
                this.fetchPayouts();
            } else {
                const err = await response.json();
                alert(err.error || 'Failed to save payout');
            }
        } catch (error) {
            console.error('Error saving payout:', error);
            alert('Error saving payout. Please try again.');
        }
    }

    async deletePayout(id) {
        if (!confirm('Delete this payout?')) return;

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/payouts/${id}/delete/`, {
                method: 'POST'
            });

            if (response.ok) {
                this.showNotification('Payout deleted!', 'success');
                this.fetchPayouts();
            } else {
                alert('Failed to delete payout');
            }
        } catch (error) {
            console.error('Error deleting payout:', error);
            alert('Error deleting payout. Please try again.');
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 rounded-lg px-6 py-3 shadow-lg ${type === 'success' ? 'bg-green-600' : 'bg-red-600'} text-white`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}
