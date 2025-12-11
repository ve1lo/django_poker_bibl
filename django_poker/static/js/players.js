class PlayerManager {
    constructor(tournamentId, tournamentType) {
        this.tournamentId = tournamentId;
        this.tournamentType = tournamentType; // 'PAID' or 'FREE'
        this.currentEliminationId = null;
        this.currentPlayerName = null;
        this.currentBalanceSuggestion = null;

        this.elements = {
            playerList: document.getElementById('player-list-body'),
            searchInput: document.getElementById('player-search-input'),
            searchResults: document.getElementById('player-search-results'),
            btnAddPlayer: document.getElementById('btn-add-player'),
            totalPlayers: document.getElementById('total-players-count'),
            // Registration Modal elements
            modal: document.getElementById('registration-modal'),
            modalClose: document.getElementById('modal-close'),
            modalCancel: document.getElementById('modal-cancel'),
            modalRegister: document.getElementById('modal-register'),
            playerName: document.getElementById('player-name'),
            playerUsername: document.getElementById('player-username'),
            playerPhone: document.getElementById('player-phone'),
            // Elimination Modal elements
            eliminationModal: document.getElementById('elimination-modal'),
            eliminationModalClose: document.getElementById('elimination-modal-close'),
            eliminationModalCancel: document.getElementById('elimination-modal-cancel'),
            eliminationModalConfirm: document.getElementById('elimination-modal-confirm'),
            eliminationPlayerName: document.getElementById('elimination-player-name'),
            bountyCount: document.getElementById('bounty-count'),
        };

        this.init();
    }

    init() {
        this.fetchPlayers();

        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }

        if (this.elements.btnAddPlayer) {
            this.elements.btnAddPlayer.addEventListener('click', () => this.openModal());
        }

        // Modal event listeners
        if (this.elements.modalClose) {
            this.elements.modalClose.addEventListener('click', () => this.closeModal());
        }

        if (this.elements.modalCancel) {
            this.elements.modalCancel.addEventListener('click', () => this.closeModal());
        }

        if (this.elements.modalRegister) {
            this.elements.modalRegister.addEventListener('click', () => this.registerFromModal());
        }

        // Close modal on outside click
        if (this.elements.modal) {
            this.elements.modal.addEventListener('click', (e) => {
                if (e.target === this.elements.modal) {
                    this.closeModal();
                }
            });
        }

        // Close modal on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (!this.elements.modal.classList.contains('hidden')) {
                    this.closeModal();
                }
                if (!this.elements.eliminationModal.classList.contains('hidden')) {
                    this.closeEliminationModal();
                }
            }
        });

        // Elimination Modal event listeners
        if (this.elements.eliminationModalClose) {
            this.elements.eliminationModalClose.addEventListener('click', () => this.closeEliminationModal());
        }

        if (this.elements.eliminationModalCancel) {
            this.elements.eliminationModalCancel.addEventListener('click', () => this.closeEliminationModal());
        }

        if (this.elements.eliminationModalConfirm) {
            this.elements.eliminationModalConfirm.addEventListener('click', () => this.confirmElimination());
        }

        // Close elimination modal on outside click
        if (this.elements.eliminationModal) {
            this.elements.eliminationModal.addEventListener('click', (e) => {
                if (e.target === this.elements.eliminationModal) {
                    this.closeEliminationModal();
                }
            });
        }
    }

    openModal() {
        if (this.elements.modal) {
            this.elements.modal.classList.remove('hidden');
            this.elements.playerName.focus();
        }
    }

    closeModal() {
        if (this.elements.modal) {
            this.elements.modal.classList.add('hidden');
            // Clear inputs
            this.elements.playerName.value = '';
            this.elements.playerUsername.value = '';
            this.elements.playerPhone.value = '';
        }
    }

    async registerFromModal() {
        const name = this.elements.playerName.value.trim();
        const username = this.elements.playerUsername.value.trim();
        const phone = this.elements.playerPhone.value.trim();

        if (!name) {
            alert('Player name is required');
            return;
        }

        const data = { name };
        if (username) data.username = username;
        if (phone) data.phone = phone;

        await this.register(data);
        this.closeModal();
    }

    async fetchPlayers() {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/players/`);
            const data = await response.json();
            this.renderPlayers(data.players);
        } catch (error) {
            console.error('Error fetching players:', error);
        }
    }

    renderPlayers(players) {
        if (!this.elements.playerList) return;

        this.elements.playerList.innerHTML = '';

        if (this.elements.totalPlayers) {
            this.elements.totalPlayers.textContent = players.length;
        }

        players.forEach(player => {
            const row = document.createElement('tr');
            row.className = "border-b border-border/50 transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted";

            const statusClass = player.status === 'ELIMINATED' ? 'text-red-500' : 'text-green-500';
            const statusText = player.status === 'ELIMINATED' ? `Eliminated (${player.place})` : 'Active';

            // Build player info
            let playerInfo = `<span class="text-foreground font-medium">${player.name}</span>`;

            // Add username or phone if available
            const extraInfo = [];
            if (player.username) extraInfo.push(`@${player.username}`);
            if (player.phone) extraInfo.push(player.phone);

            if (extraInfo.length > 0) {
                playerInfo += `<span class="text-xs text-muted-foreground block">${extraInfo.join(' • ')}</span>`;
            }

            if (player.table) {
                playerInfo += `<span class="text-xs text-blue-400 block">Table ${player.table} / Seat ${player.seat_number}</span>`;
            }

            // Escape player name for safe use in onclick
            const escapedPlayerName = player.name.replace(/'/g, "\\'");

            row.innerHTML = `
                <td class="p-4 align-middle">
                    <div class="flex flex-col">
                        ${playerInfo}
                    </div>
                </td>
                <td class="p-4 align-middle text-center">
                    ${this.tournamentType === 'PAID' ? `
                        <div class="flex flex-col items-center gap-1">
                            <span class="text-xs font-mono bg-secondary px-1.5 rounded">${player.rebuys}</span>
                            <span class="text-xs font-mono bg-secondary px-1.5 rounded">${player.addons}</span>
                        </div>
                    ` : `
                        <div class="flex flex-col items-center gap-1">
                            ${player.status === 'ELIMINATED' && player.points > 0 ? `
                                <div class="text-center">
                                    <div class="text-lg font-bold text-primary">${player.points}</div>
                                    <div class="text-xs text-muted-foreground">points</div>
                                </div>
                            ` : `
                                <span class="text-xs text-muted-foreground">-</span>
                            `}
                            ${player.bounty_count > 0 ? `
                                <span class="text-xs font-mono bg-amber-500/20 text-amber-400 px-1.5 rounded mt-1" title="Bounties">🎯 ${player.bounty_count}</span>
                            ` : ''}
                        </div>
                    `}
                </td>
                <td class="p-4 align-middle text-right">
                    ${player.status !== 'ELIMINATED' ? `
                        <div class="flex justify-end gap-1">
                            ${this.tournamentType === 'PAID' ? `
                                <button onclick="playerManager.rebuy(${player.id})" class="h-8 w-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground" title="Rebuy">
                                    <span class="font-bold text-xs">R</span>
                                </button>
                                <button onclick="playerManager.addon(${player.id})" class="h-8 w-8 inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent hover:text-accent-foreground" title="Add-on">
                                    <span class="font-bold text-xs">A</span>
                                </button>
                            ` : ''}
                            <button onclick="playerManager.eliminate(${player.id}, '${escapedPlayerName}')" class="h-8 w-8 inline-flex items-center justify-center rounded-md bg-orange-500/10 text-orange-500 hover:bg-orange-500 hover:text-white transition-colors" title="Eliminate">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                            </button>
                            <button onclick="playerManager.unregister(${player.id})" class="h-8 w-8 inline-flex items-center justify-center rounded-md bg-destructive/10 text-destructive hover:bg-destructive hover:text-destructive-foreground transition-colors" title="Delete Player">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
                            </button>
                        </div>
                    ` : `
                        <div class="text-xs font-medium text-destructive text-right">
                            <div>Place: ${player.place}</div>
                            ${this.tournamentType === 'FREE' ? `
                                <div class="text-primary font-bold mt-1">${player.points || 0} pts</div>
                                ${player.bounty_count > 0 ? `
                                    <div class="text-amber-400 text-xs">+${player.bounty_count} 🎯</div>
                                ` : ''}
                            ` : ''}
                        </div>
                    `}
                </td>
            `;
            this.elements.playerList.appendChild(row);
        });
    }

    async handleSearch(query) {
        if (query.length < 2) {
            this.elements.searchResults.innerHTML = '';
            this.elements.searchResults.classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`/api/players/search/?q=${encodeURIComponent(query)}&tournament_id=${this.tournamentId}`);
            const data = await response.json();

            this.elements.searchResults.innerHTML = '';

            if (data.results.length > 0) {
                this.elements.searchResults.classList.remove('hidden');
                data.results.forEach(player => {
                    const div = document.createElement('div');
                    div.className = "p-2 hover:bg-muted cursor-pointer";
                    div.textContent = player.name;
                    div.onclick = () => this.registerExistingPlayer(player.id, player.name);
                    this.elements.searchResults.appendChild(div);
                });
            } else {
                this.elements.searchResults.classList.add('hidden');
            }
        } catch (error) {
            console.error('Error searching players:', error);
        }
    }

    async registerExistingPlayer(playerId, name) {
        await this.register({ player_id: playerId });
        this.elements.searchInput.value = '';
        this.elements.searchResults.classList.add('hidden');
    }

    async registerNewPlayer() {
        const name = this.elements.searchInput.value;
        if (!name) return;

        await this.register({ name: name });
        this.elements.searchInput.value = '';
    }

    async register(data) {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Player registered:', result);
                this.fetchPlayers();

                // Clear search input and results
                this.elements.searchInput.value = '';
                this.elements.searchResults.innerHTML = '';
                this.elements.searchResults.classList.add('hidden');

                // Show success message
                this.showNotification('Player registered successfully!', 'success');
            } else {
                const err = await response.json();
                alert(err.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Error registering:', error);
            alert('Error registering player. Please try again.');
        }
    }

    showNotification(message, type = 'success') {
        // Simple notification - можно улучшить позже
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 rounded-lg px-6 py-3 shadow-lg ${type === 'success' ? 'bg-green-600' : 'bg-red-600'} text-white`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    openEliminationModal(registrationId, playerName) {
        if (this.elements.eliminationModal) {
            this.currentEliminationId = registrationId;
            this.currentPlayerName = playerName;
            this.elements.eliminationPlayerName.textContent = playerName;
            this.elements.bountyCount.value = '0';
            this.elements.eliminationModal.classList.remove('hidden');
            this.elements.bountyCount.focus();
        }
    }

    closeEliminationModal() {
        if (this.elements.eliminationModal) {
            this.elements.eliminationModal.classList.add('hidden');
            this.currentEliminationId = null;
            this.currentPlayerName = null;
        }
    }

    async confirmElimination() {
        const bountyCount = parseInt(this.elements.bountyCount.value) || 0;

        if (bountyCount < 0) {
            alert('Bounty count cannot be negative');
            return;
        }

        await this.postAction('eliminate', {
            registration_id: this.currentEliminationId,
            bounty_count: bountyCount
        });

        this.closeEliminationModal();
    }

    async eliminate(registrationId, playerName) {
        // For FREE tournaments, show modal to enter bounty count
        if (this.tournamentType === 'FREE') {
            this.openEliminationModal(registrationId, playerName);
        } else {
            // For PAID tournaments, just confirm and eliminate
            if (!confirm('Eliminate this player from the tournament?')) return;
            await this.postAction('eliminate', { registration_id: registrationId });
        }
    }

    async rebuy(registrationId) {
        await this.postAction('rebuy', { registration_id: registrationId });
    }

    async addon(registrationId) {
        await this.postAction('addon', { registration_id: registrationId });
    }

    async unregister(registrationId) {
        if (!confirm('⚠️ Delete this player from the tournament?\n\nThis will permanently remove their registration and cannot be undone.')) return;

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/unregister/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ registration_id: registrationId })
            });

            if (response.ok) {
                const result = await response.json();
                this.showNotification(`Player ${result.player_name} removed successfully`, 'success');
                this.fetchPlayers();
            } else {
                const err = await response.json();
                alert(err.error || 'Failed to remove player');
            }
        } catch (error) {
            console.error('Error removing player:', error);
            alert('Error removing player. Please try again.');
        }
    }

    async postAction(action, data) {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/${action}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();

                console.log('DEBUG: Elimination result:', result);
                console.log('DEBUG: Payout amount:', result.payout_amount);
                console.log('DEBUG: payoutManager exists:', !!window.payoutManager);

                // Check if player won a prize
                if (result.payout_amount) {
                    this.showNotification(
                        `🏆 Place ${result.place}! Prize: $${result.payout_amount.toLocaleString()}`,
                        'success'
                    );

                    // Refresh payouts if payout manager exists
                    if (window.payoutManager) {
                        console.log('DEBUG: Refreshing payouts...');
                        window.payoutManager.fetchPayouts();
                    } else {
                        console.log('DEBUG: payoutManager not found!');
                    }
                }

                // Check if level was advanced (for FREE tournaments)
                if (result.level_advanced) {
                    this.showNotification(`Level advanced to ${result.new_level}!`, 'success');

                    // Trigger immediate status update for timer
                    if (window.timer) {
                        window.timer.fetchStatus();
                    }
                }

                this.fetchPlayers();

                // Update tables display after elimination (player leaves table)
                if (window.tableManager) {
                    window.tableManager.fetchTables();
                }

                // Show table balance suggestions
                if (result.balance_suggestion) {
                    this.showBalanceSuggestion(result.balance_suggestion);
                }
            }
        } catch (error) {
            console.error(`Error ${action}:`, error);
        }
    }

    showBalanceSuggestion(suggestion) {
        this.currentBalanceSuggestion = suggestion;

        const block = document.getElementById('balance-suggestion-block');
        const icon = document.getElementById('balance-suggestion-icon');
        const title = document.getElementById('balance-suggestion-title');
        const message = document.getElementById('balance-suggestion-message');
        const details = document.getElementById('balance-suggestion-details');
        const actions = document.getElementById('balance-suggestion-actions');

        if (!block) return;

        if (suggestion.type === 'balance') {
            // Simple balance - show which tables need rebalancing
            block.className = 'mb-4 rounded-lg border-2 border-amber-500/50 bg-amber-500/10 p-4';
            icon.textContent = '⚖️';
            title.textContent = 'Table Balance Suggestion';
            message.textContent = suggestion.message;

            details.innerHTML = `
                <div class="bg-background/50 rounded-md p-3 text-sm">
                    <div class="flex items-center justify-center gap-4 py-2">
                        <div class="text-center">
                            <div class="text-xs text-muted-foreground mb-1">From</div>
                            <div class="text-2xl font-bold text-primary">Table ${suggestion.from_table}</div>
                            <div class="text-xs text-muted-foreground mt-1">${suggestion.from_table_count} players</div>
                        </div>
                        <div class="flex flex-col items-center gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-500">
                                <path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>
                            </svg>
                            <div class="text-xs font-medium text-amber-600">${suggestion.players_count} player(s)</div>
                        </div>
                        <div class="text-center">
                            <div class="text-xs text-muted-foreground mb-1">To</div>
                            <div class="text-2xl font-bold text-green-500">Table ${suggestion.to_table}</div>
                            <div class="text-xs text-muted-foreground mt-1">${suggestion.to_table_count} players</div>
                        </div>
                    </div>
                </div>
                <div class="text-xs text-muted-foreground mt-2 text-center">
                    💡 Use the move player interface to manually move players between tables
                </div>
            `;

            actions.innerHTML = `
                <button onclick="playerManager.hideBalanceSuggestion()"
                    class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent h-9 px-4">
                    Got it
                </button>
            `;
        } else if (suggestion.type === 'break_table') {
            // Break table - show all movements
            block.className = 'mb-4 rounded-lg border-2 border-red-500/50 bg-red-500/10 p-4';
            icon.textContent = '🔴';
            title.textContent = 'Table Break Suggestion';
            message.textContent = suggestion.message;

            const movementsList = suggestion.movements.map(m => `
                <div class="flex items-center gap-2 text-sm">
                    <span class="font-medium">${m.player_name}</span>
                    <span class="text-muted-foreground">→</span>
                    <span class="text-xs">Table ${m.from_table}</span>
                    <span class="text-muted-foreground">→</span>
                    <span class="text-xs text-green-500 font-medium">Table ${m.to_table}</span>
                </div>
            `).join('');

            details.innerHTML = `
                <div class="bg-background/50 rounded-md p-3">
                    <div class="font-medium mb-2 text-sm">Suggested movements:</div>
                    <div class="space-y-1">
                        ${movementsList}
                    </div>
                </div>
                <div class="text-xs text-muted-foreground mt-2">
                    💡 This will help optimize table balance and reduce the number of active tables.
                </div>
            `;

            actions.innerHTML = `
                <button onclick="playerManager.applyTableBreak()"
                    class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors bg-red-500 text-white hover:bg-red-600 h-9 px-4">
                    Break Table & Move All Players
                </button>
                <button onclick="playerManager.hideBalanceSuggestion()"
                    class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors border border-input bg-background hover:bg-accent h-9 px-4">
                    I'll do it manually
                </button>
            `;
        }

        block.classList.remove('hidden');

        // Auto-scroll to the suggestion block
        setTimeout(() => {
            block.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }

    hideBalanceSuggestion() {
        const block = document.getElementById('balance-suggestion-block');
        if (block) {
            block.classList.add('hidden');
        }
        this.currentBalanceSuggestion = null;
    }

    applyBalanceSuggestion() {
        if (!this.currentBalanceSuggestion || this.currentBalanceSuggestion.type !== 'balance') {
            return;
        }

        const suggestion = this.currentBalanceSuggestion;

        // Open move player modal for this player
        if (window.tableManager) {
            // Find the player in tables and show modal
            const tables = window.tableManager.allTables;
            for (const table of tables) {
                const seat = table.seats.find(s => s.registration_id === suggestion.registration_id);
                if (seat) {
                    window.tableManager.showMovePlayerModal(
                        suggestion.registration_id,
                        suggestion.player_name,
                        suggestion.from_table,
                        seat.seat_number
                    );
                    this.hideBalanceSuggestion();
                    break;
                }
            }
        }
    }

    async applyTableBreak() {
        if (!this.currentBalanceSuggestion || this.currentBalanceSuggestion.type !== 'break_table') {
            return;
        }

        const suggestion = this.currentBalanceSuggestion;
        const movements = suggestion.movements;

        if (!movements || movements.length === 0) {
            alert('No movements to apply');
            return;
        }

        // Confirm action
        if (!confirm(`Break Table ${suggestion.table_number} and move ${movements.length} player(s)?\n\nThis action cannot be undone.`)) {
            return;
        }

        // Disable the button to prevent double-clicks
        const applyButton = document.querySelector('#balance-suggestion-actions button');
        if (applyButton) {
            applyButton.disabled = true;
            applyButton.textContent = 'Moving players...';
        }

        try {
            let successCount = 0;
            let failedMoves = [];

            // Move each player sequentially
            for (const movement of movements) {
                try {
                    // First, get available tables to find table_id
                    const tablesResponse = await fetch(`/api/tournament/${this.tournamentId}/tables/`);
                    const tablesData = await tablesResponse.json();

                    // Find the target table ID
                    const targetTable = tablesData.tables.find(t => t.number === movement.to_table);

                    if (!targetTable) {
                        failedMoves.push(`${movement.player_name}: Target table not found`);
                        continue;
                    }

                    // Find available seat at target table
                    const occupiedSeats = targetTable.seats.map(s => s.seat_number);
                    let availableSeat = null;
                    for (let i = 1; i <= targetTable.max_seats; i++) {
                        if (!occupiedSeats.includes(i)) {
                            availableSeat = i;
                            break;
                        }
                    }

                    if (!availableSeat) {
                        failedMoves.push(`${movement.player_name}: No available seats at Table ${movement.to_table}`);
                        continue;
                    }

                    // Move the player
                    const response = await fetch(`/api/tournament/${this.tournamentId}/tables/move/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            registration_id: movement.registration_id,
                            table_id: targetTable.id,
                            seat_number: availableSeat
                        })
                    });

                    const result = await response.json();

                    if (result.status === 'moved') {
                        successCount++;
                    } else {
                        failedMoves.push(`${movement.player_name}: ${result.error || 'Unknown error'}`);
                    }

                    // Small delay between moves to avoid race conditions
                    await new Promise(resolve => setTimeout(resolve, 200));

                } catch (error) {
                    console.error(`Error moving ${movement.player_name}:`, error);
                    failedMoves.push(`${movement.player_name}: Network error`);
                }
            }

            // Delete the empty table
            try {
                const deleteResponse = await fetch(`/api/tournament/${this.tournamentId}/tables/${suggestion.table_id}/delete/`, {
                    method: 'POST'
                });

                if (!deleteResponse.ok) {
                    console.warn('Could not delete empty table, but players were moved');
                }
            } catch (error) {
                console.error('Error deleting table:', error);
            }

            // Show results
            if (successCount === movements.length) {
                this.showNotification(
                    `✅ Table ${suggestion.table_number} broken successfully! ${successCount} player(s) moved.`,
                    'success'
                );
            } else if (successCount > 0) {
                this.showNotification(
                    `⚠️ Partially completed: ${successCount}/${movements.length} players moved.\n\nFailed:\n${failedMoves.join('\n')}`,
                    'warning'
                );
            } else {
                this.showNotification(
                    `❌ Failed to move players:\n${failedMoves.join('\n')}`,
                    'error'
                );
            }

            // Refresh displays
            this.fetchPlayers();
            if (window.tableManager) {
                window.tableManager.fetchTables();
            }

            // Hide the suggestion block
            this.hideBalanceSuggestion();

        } catch (error) {
            console.error('Error applying table break:', error);
            alert('Error applying table break. Check console for details.');
        } finally {
            // Re-enable button
            if (applyButton) {
                applyButton.disabled = false;
                applyButton.textContent = 'Break Table & Move All Players';
            }
        }
    }
}
