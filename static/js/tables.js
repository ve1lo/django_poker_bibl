class TableManager {
    constructor(tournamentId) {
        this.tournamentId = tournamentId;
        this.container = document.getElementById('tables-container');
        this.autoSeatBtn = document.getElementById('btn-auto-seat');
        this.clearTablesBtn = document.getElementById('btn-clear-tables');
        this.addTableBtn = document.getElementById('btn-add-table');
        this.seatSelectedBtn = document.getElementById('btn-seat-selected');
        this.selectAllBtn = document.getElementById('btn-select-all-players');
        this.playersListContainer = document.getElementById('seating-players-list');

        // For move player functionality
        this.currentMovingPlayer = null;
        this.allTables = [];

        this.init();
    }

    init() {
        if (this.autoSeatBtn) {
            this.autoSeatBtn.addEventListener('click', () => this.generateTables());
        }
        if (this.clearTablesBtn) {
            this.clearTablesBtn.addEventListener('click', () => this.clearTables());
        }
        if (this.addTableBtn) {
            this.addTableBtn.addEventListener('click', () => this.showAddTableModal());
        }
        if (this.seatSelectedBtn) {
            this.seatSelectedBtn.addEventListener('click', () => this.seatSelectedPlayers());
        }
        if (this.selectAllBtn) {
            this.selectAllBtn.addEventListener('click', () => this.toggleSelectAll());
        }

        this.fetchTables();
        this.fetchPlayers();
    }

    async fetchTables() {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/tables/`);
            const data = await response.json();
            this.allTables = data.tables;  // Store tables data for move player functionality
            this.renderTables(data.tables);
        } catch (error) {
            console.error('Error fetching tables:', error);
        }
    }

    renderTables(tables) {
        this.container.innerHTML = '';

        if (tables.length === 0) {
            this.container.innerHTML = `
                <div class="col-span-full flex flex-col items-center justify-center py-12 text-center border border-dashed border-border/50 rounded-xl bg-card/30">
                    <div class="rounded-full bg-muted/50 p-4 mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-muted-foreground"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
                    </div>
                    <h3 class="text-lg font-semibold">No tables generated</h3>
                    <p class="text-muted-foreground max-w-sm mt-2">Click "Auto Seat" to generate tables and seat players.</p>
                </div>
            `;
            return;
        }

        tables.forEach(table => {
            const tableEl = document.createElement('div');
            tableEl.className = 'flex flex-col items-center p-4';

            const maxSeats = table.max_seats || 9;
            const seatsHtml = this.renderPokerTable(table.number, table.seats, maxSeats);

            tableEl.innerHTML = seatsHtml;
            this.container.appendChild(tableEl);
        });
    }

    renderPokerTable(tableNumber, seats, maxSeats) {
        // Positions for seats around the table (in degrees)
        const positions = this.getSeatPositions(maxSeats);

        let seatsHtml = '';

        for (let i = 1; i <= maxSeats; i++) {
            const player = seats.find(s => s.seat_number === i);
            const pos = positions[i - 1];

            const seatClass = player
                ? 'bg-primary/20 border-primary/40 text-primary cursor-pointer hover:bg-primary/30 transition-colors'
                : 'bg-muted/30 border-border/30 text-muted-foreground';

            const playerName = player ? player.player_name : 'Empty';
            const nameClass = player ? 'font-semibold text-foreground' : 'text-muted-foreground italic text-xs';

            const clickHandler = player
                ? `onclick="tableManager.showMovePlayerModal(${player.registration_id}, '${player.player_name.replace(/'/g, "\\'")}', ${tableNumber}, ${i})"`
                : '';

            seatsHtml += `
                <div class="absolute seat-${i}" style="left: ${pos.x}%; top: ${pos.y}%; transform: translate(-50%, -50%);">
                    <div class="flex flex-col items-center gap-1" ${clickHandler}>
                        <div class="w-12 h-12 rounded-full border-2 ${seatClass} flex items-center justify-center text-sm font-bold shadow-lg">
                            ${i}
                        </div>
                        <div class="text-center ${nameClass} text-xs max-w-[80px] truncate px-2 py-1 rounded bg-background/80 backdrop-blur-sm">
                            ${playerName}
                        </div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="w-full">
                <div class="text-center mb-4">
                    <h3 class="text-lg font-semibold">Table ${tableNumber}</h3>
                    <span class="text-xs text-muted-foreground">${seats.length} / ${maxSeats} Players</span>
                </div>
                <div class="relative mx-auto" style="width: 400px; height: 300px;">
                    <!-- Poker Table -->
                    <div class="absolute inset-0 rounded-full bg-gradient-to-br from-green-900 to-green-800 border-8 border-amber-900 shadow-2xl">
                        <div class="absolute inset-4 rounded-full border-4 border-amber-700/50"></div>
                        <div class="absolute inset-0 flex items-center justify-center">
                            <div class="text-center">
                                <div class="text-amber-200/40 font-bold text-2xl">TABLE</div>
                                <div class="text-amber-200/40 font-bold text-4xl">${tableNumber}</div>
                            </div>
                        </div>
                    </div>
                    <!-- Seats -->
                    ${seatsHtml}
                </div>
            </div>
        `;
    }

    getSeatPositions(maxSeats) {
        // Calculate positions around an ellipse
        const positions = [];
        const centerX = 50;
        const centerY = 50;
        const radiusX = 48; // horizontal radius
        const radiusY = 44; // vertical radius

        for (let i = 0; i < maxSeats; i++) {
            // Start from top and go clockwise
            const angle = (i * 360 / maxSeats - 90) * Math.PI / 180;
            const x = centerX + radiusX * Math.cos(angle);
            const y = centerY + radiusY * Math.sin(angle);
            positions.push({ x, y });
        }

        return positions;
    }

    async generateTables() {
        if (!confirm('This will clear current seating and regenerate tables. Continue?')) return;

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/tables/generate/`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.status === 'tables_generated') {
                this.fetchTables();
            } else if (data.status === 'no_players') {
                alert('No registered players to seat.');
            }
        } catch (error) {
            console.error('Error generating tables:', error);
        }
    }

    async clearTables() {
        if (!confirm('Are you sure you want to clear all tables?')) return;

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/tables/clear/`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.status === 'tables_cleared') {
                this.fetchTables();
            }
        } catch (error) {
            console.error('Error clearing tables:', error);
        }
    }

    showAddTableModal() {
        const modal = document.getElementById('add-table-modal');
        if (modal) {
            modal.classList.remove('hidden');
            document.getElementById('table-max-seats').value = 8;
        }
    }

    hideAddTableModal() {
        const modal = document.getElementById('add-table-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    async addTable() {
        const maxSeats = parseInt(document.getElementById('table-max-seats').value);

        if (!maxSeats || maxSeats < 2 || maxSeats > 10) {
            alert('Please enter a valid number of seats (2-10)');
            return;
        }

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/tables/add/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ max_seats: maxSeats })
            });

            const data = await response.json();

            if (data.status === 'table_added') {
                this.hideAddTableModal();
                this.fetchTables();
            }
        } catch (error) {
            console.error('Error adding table:', error);
        }
    }

    async fetchPlayers() {
        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/players/`);
            const data = await response.json();
            this.renderPlayersList(data.players);
        } catch (error) {
            console.error('Error fetching players:', error);
        }
    }

    renderPlayersList(players) {
        if (!this.playersListContainer) return;

        // Filter only registered players without seats
        const unseatedPlayers = players.filter(p => p.status === 'REGISTERED' && !p.seat_number);

        if (unseatedPlayers.length === 0) {
            this.playersListContainer.innerHTML = `
                <div class="text-center text-sm text-muted-foreground py-4">
                    All players are seated
                </div>
            `;
            return;
        }

        this.playersListContainer.innerHTML = unseatedPlayers.map(player => `
            <label class="flex items-center gap-2 p-2 rounded-lg hover:bg-secondary/30 cursor-pointer transition-colors">
                <input type="checkbox" class="player-checkbox w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                    data-player-id="${player.player_id}" data-registration-id="${player.id}">
                <span class="text-sm font-medium flex-1">${player.name}</span>
            </label>
        `).join('');
    }

    toggleSelectAll() {
        const checkboxes = this.playersListContainer.querySelectorAll('.player-checkbox');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);

        checkboxes.forEach(cb => {
            cb.checked = !allChecked;
        });

        this.selectAllBtn.textContent = allChecked ? 'Select All' : 'Deselect All';
    }

    async seatSelectedPlayers() {
        const checkboxes = this.playersListContainer.querySelectorAll('.player-checkbox:checked');
        const selectedPlayerIds = Array.from(checkboxes).map(cb => parseInt(cb.dataset.registrationId));

        console.log('Selected player IDs:', selectedPlayerIds);

        if (selectedPlayerIds.length === 0) {
            alert('Please select at least one player');
            return;
        }

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/tables/seat-selected/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ registration_ids: selectedPlayerIds })
            });

            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);

            if (data.status === 'players_seated') {
                this.fetchTables();
                this.fetchPlayers();
                if (data.seated_count > 0) {
                    alert(`Successfully seated ${data.seated_count} player(s)`);
                } else if (data.message) {
                    alert(data.message);
                }
            } else if (data.status === 'no_tables') {
                alert('No tables available. Please create tables first.');
            } else if (data.status === 'no_space') {
                let message = 'Not enough space in tables. Please add more tables.';
                if (data.debug) {
                    message += `\n\nDebug Info:\n` +
                        `Total capacity: ${data.debug.total_capacity}\n` +
                        `Currently seated: ${data.debug.currently_seated}\n` +
                        `Tables: ${data.debug.tables_count}\n` +
                        `Players to seat: ${data.debug.players_to_seat}`;
                }
                alert(message);
            } else {
                console.warn('Unknown status:', data.status);
                alert('Unknown response from server. Check console for details.');
            }
        } catch (error) {
            console.error('Error seating players:', error);
            alert('Error seating players. Check console for details.');
        }
    }

    // Move Player Modal Methods

    showMovePlayerModal(registrationId, playerName, currentTable, currentSeat) {
        this.currentMovingPlayer = {
            registrationId,
            playerName,
            currentTable,
            currentSeat
        };

        // Update modal content
        document.getElementById('moving-player-name').textContent = playerName;
        document.getElementById('moving-player-current').textContent =
            `Current: Table ${currentTable}, Seat ${currentSeat}`;

        // Load available positions
        this.loadAvailablePositions();

        // Show modal
        document.getElementById('move-player-modal').classList.remove('hidden');
    }

    hideMovePlayerModal() {
        document.getElementById('move-player-modal').classList.add('hidden');
        this.currentMovingPlayer = null;
    }

    loadAvailablePositions() {
        const positionsList = document.getElementById('available-positions-list');
        positionsList.innerHTML = '';

        // Group positions by table
        this.allTables.forEach(table => {
            // Find occupied seat numbers
            const occupiedSeats = table.seats.map(s => s.seat_number);
            const availableSeats = [];

            for (let i = 1; i <= table.max_seats; i++) {
                if (!occupiedSeats.includes(i)) {
                    availableSeats.push(i);
                }
            }

            if (availableSeats.length > 0) {
                const tableSection = document.createElement('div');
                tableSection.className = 'border border-border rounded-lg p-3';
                tableSection.innerHTML = `
                    <div class="font-medium mb-2">Table ${table.number} (${availableSeats.length} seats available)</div>
                    <div class="flex flex-wrap gap-2">
                        ${availableSeats.map(seat => `
                            <button onclick="tableManager.movePlayerToSeat(${table.id}, ${seat})"
                                class="px-3 py-1.5 rounded border border-primary/40 bg-primary/10 hover:bg-primary/20 transition-colors text-sm font-medium">
                                Seat ${seat}
                            </button>
                        `).join('')}
                    </div>
                `;
                positionsList.appendChild(tableSection);
            }
        });

        if (positionsList.children.length === 0) {
            positionsList.innerHTML = `
                <div class="text-center text-sm text-muted-foreground py-4">
                    No available seats at any table
                </div>
            `;
        }
    }

    async movePlayerToSeat(tableId, seatNumber) {
        if (!this.currentMovingPlayer) return;

        // Save player info before async operations
        const playerName = this.currentMovingPlayer.playerName;
        const registrationId = this.currentMovingPlayer.registrationId;

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/tables/move/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    registration_id: registrationId,
                    table_id: tableId,
                    seat_number: seatNumber
                })
            });

            const data = await response.json();

            if (data.status === 'moved') {
                this.hideMovePlayerModal();
                this.fetchTables();
                this.fetchPlayers();
                alert(`${playerName} moved successfully!`);
            } else if (data.error) {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error moving player:', error);
            alert('Error moving player. Check console for details.');
        }
    }

    async unseatPlayer() {
        if (!this.currentMovingPlayer) return;

        // Save player info before async operations
        const playerName = this.currentMovingPlayer.playerName;
        const registrationId = this.currentMovingPlayer.registrationId;

        if (!confirm(`Remove ${playerName} from the table?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/tournament/${this.tournamentId}/tables/move/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    registration_id: registrationId,
                    table_id: null,
                    seat_number: null
                })
            });

            const data = await response.json();

            if (data.status === 'moved') {
                this.hideMovePlayerModal();
                this.fetchTables();
                this.fetchPlayers();
                alert(`${playerName} removed from table.`);
            } else if (data.error) {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error unseating player:', error);
            alert('Error unseating player. Check console for details.');
        }
    }
}
