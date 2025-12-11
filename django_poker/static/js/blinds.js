class BlindStructureManager {
    constructor(tournamentId) {
        this.tournamentId = tournamentId;
        this.levels = [];
        this.editingLevelId = null;

        this.elements = {
            blindStructureBody: document.getElementById('blind-structure-body'),
            btnAddLevel: document.getElementById('btn-add-level'),
        };

        this.init();
    }

    init() {
        this.fetchLevels();

        if (this.elements.btnAddLevel) {
            this.elements.btnAddLevel.addEventListener('click', () => this.addNewLevel());
        }
    }

    async fetchLevels() {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/levels/`);
            const data = await response.json();
            this.levels = data.levels;
            this.renderLevels();
        } catch (error) {
            console.error('Error fetching levels:', error);
        }
    }

    renderLevels() {
        if (!this.elements.blindStructureBody) return;

        this.elements.blindStructureBody.innerHTML = '';

        this.levels.forEach(level => {
            const row = document.createElement('tr');
            row.className = "border-b transition-colors hover:bg-muted/50";
            row.dataset.levelId = level.id;

            const typeLabel = level.is_break ? 'Break' : 'Level';
            const typeClass = level.is_break ? 'bg-blue-500/20 text-blue-400' : 'bg-secondary text-secondary-foreground';

            if (this.editingLevelId === level.id) {
                // Edit mode
                row.innerHTML = `
                    <td class="p-2 align-middle">
                        <input type="number" value="${level.level_number}" data-field="level_number"
                            class="w-full h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                    </td>
                    <td class="p-2 align-middle">
                        <input type="number" value="${level.small_blind}" data-field="small_blind" ${level.is_break ? 'disabled' : ''}
                            class="w-full h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50">
                    </td>
                    <td class="p-2 align-middle">
                        <input type="number" value="${level.big_blind}" data-field="big_blind" ${level.is_break ? 'disabled' : ''}
                            class="w-full h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50">
                    </td>
                    <td class="p-2 align-middle">
                        <input type="number" value="${level.ante}" data-field="ante" ${level.is_break ? 'disabled' : ''}
                            class="w-full h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50">
                    </td>
                    <td class="p-2 align-middle">
                        <input type="number" value="${level.duration}" data-field="duration"
                            class="w-full h-8 rounded border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring">
                    </td>
                    <td class="p-2 align-middle">
                        <label class="flex items-center gap-2 cursor-pointer">
                            <input type="checkbox" ${level.is_break ? 'checked' : ''} data-field="is_break"
                                class="rounded border-input">
                            <span class="text-xs">Break</span>
                        </label>
                    </td>
                    <td class="p-2 align-middle text-right">
                        <div class="flex justify-end gap-1">
                            <button onclick="blindStructureManager.saveLevel(${level.id})"
                                class="h-8 px-3 inline-flex items-center justify-center rounded-md text-xs font-medium bg-green-600 text-white hover:bg-green-700">
                                Save
                            </button>
                            <button onclick="blindStructureManager.cancelEdit()"
                                class="h-8 px-3 inline-flex items-center justify-center rounded-md text-xs font-medium border border-input bg-background hover:bg-accent">
                                Cancel
                            </button>
                        </div>
                    </td>
                `;
            } else {
                // View mode
                const blindsDisplay = level.is_break
                    ? '<span class="text-muted-foreground">—</span>'
                    : level.small_blind.toLocaleString();
                const bigBlindDisplay = level.is_break
                    ? '<span class="text-muted-foreground">—</span>'
                    : level.big_blind.toLocaleString();
                const anteDisplay = level.is_break
                    ? '<span class="text-muted-foreground">—</span>'
                    : level.ante.toLocaleString();

                row.innerHTML = `
                    <td class="p-2 align-middle">
                        <span class="font-mono font-semibold">${level.level_number}</span>
                    </td>
                    <td class="p-2 align-middle font-mono">${blindsDisplay}</td>
                    <td class="p-2 align-middle font-mono">${bigBlindDisplay}</td>
                    <td class="p-2 align-middle font-mono">${anteDisplay}</td>
                    <td class="p-2 align-middle font-mono">${level.duration} min</td>
                    <td class="p-2 align-middle">
                        <span class="text-xs font-medium px-2 py-1 rounded ${typeClass}">${typeLabel}</span>
                    </td>
                    <td class="p-2 align-middle text-right">
                        <div class="flex justify-end gap-1">
                            <button onclick="blindStructureManager.editLevel(${level.id})"
                                class="h-8 w-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent" title="Edit">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/>
                                </svg>
                            </button>
                            <button onclick="blindStructureManager.deleteLevel(${level.id})"
                                class="h-8 w-8 inline-flex items-center justify-center rounded-md bg-destructive/10 text-destructive hover:bg-destructive hover:text-destructive-foreground" title="Delete">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                                </svg>
                            </button>
                        </div>
                    </td>
                `;
            }

            this.elements.blindStructureBody.appendChild(row);
        });
    }

    editLevel(levelId) {
        this.editingLevelId = levelId;
        this.renderLevels();
    }

    cancelEdit() {
        this.editingLevelId = null;
        this.renderLevels();
    }

    async saveLevel(levelId) {
        const row = document.querySelector(`tr[data-level-id="${levelId}"]`);
        if (!row) return;

        const data = {
            level_number: parseInt(row.querySelector('[data-field="level_number"]').value),
            small_blind: parseInt(row.querySelector('[data-field="small_blind"]').value) || 0,
            big_blind: parseInt(row.querySelector('[data-field="big_blind"]').value) || 0,
            ante: parseInt(row.querySelector('[data-field="ante"]').value) || 0,
            duration: parseInt(row.querySelector('[data-field="duration"]').value),
            is_break: row.querySelector('[data-field="is_break"]').checked,
        };

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/level/${levelId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this.editingLevelId = null;
                this.fetchLevels();
                this.showNotification('Level updated successfully', 'success');
            } else {
                const err = await response.json();
                alert(err.error || 'Failed to update level');
            }
        } catch (error) {
            console.error('Error updating level:', error);
            alert('Error updating level. Please try again.');
        }
    }

    async deleteLevel(levelId) {
        if (!confirm('Delete this level? This cannot be undone.')) return;

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/level/${levelId}/delete/`, {
                method: 'POST',
            });

            if (response.ok) {
                this.fetchLevels();
                this.showNotification('Level deleted successfully', 'success');
            } else {
                const err = await response.json();
                alert(err.error || 'Failed to delete level');
            }
        } catch (error) {
            console.error('Error deleting level:', error);
            alert('Error deleting level. Please try again.');
        }
    }

    async addNewLevel() {
        // Get the highest level number
        const maxLevel = this.levels.length > 0
            ? Math.max(...this.levels.map(l => l.level_number))
            : 0;

        const data = {
            level_number: maxLevel + 1,
            small_blind: 100,
            big_blind: 200,
            ante: 0,
            duration: 15,
            is_break: false,
        };

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/level/add/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                this.fetchLevels();
                // Auto-edit the new level
                setTimeout(() => {
                    this.editLevel(result.level_id);
                }, 100);
                this.showNotification('New level added', 'success');
            } else {
                const err = await response.json();
                alert(err.error || 'Failed to add level');
            }
        } catch (error) {
            console.error('Error adding level:', error);
            alert('Error adding level. Please try again.');
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
