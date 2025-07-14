// static/script.js

const backendUrl = window.location.origin;
let attacks = []; // Array per memorizzare gli attacchi configurati
let lastResponseTimestamps = {}; // Per tenere traccia dell'ultimo timestamp di risposta per evitare duplicati
let attackResponsePollingInterval; // Dichiarazione globale per l'intervallo di polling

// --- Funzioni di Stato e Inizializzazione ---
async function checkBackendStatus() {
    try {
        const res = await fetch(`${backendUrl}/api/status`);
        const data = await res.json();
        document.getElementById('orchestratorStatus').textContent = data.orchestrator.status;

        const agentStatusesDiv = document.getElementById('agentStatuses');
        agentStatusesDiv.innerHTML = '';
        for (const agentName in data.agents) {
            const agentStatus = data.agents[agentName];
            // Se lo stato è "success" (come fornito dal backend nelle versioni precedenti), mostra "Running"
            // Altrimenti, usa il messaggio fornito o lo stato esatto.
            const statusText = agentStatus.status.includes('running') || agentStatus.status === 'OK' ? 'Running' : (agentStatus.message || agentStatus.status);
            const statusClass = agentStatus.status.includes('running') || agentStatus.status === 'OK' ? 'status-ok' : 'status-error';            
	    const div = document.createElement('div');
            div.className = `agent-status ${statusClass}`;
            div.textContent = `${agentName}: ${statusText}`;
            agentStatusesDiv.appendChild(div);
        }

    } catch (error) {
        document.getElementById('orchestratorStatus').textContent = 'Error: Backend Unreachable';
        document.getElementById('agentStatuses').innerHTML = '<div class="agent-status status-error">Could not fetch agent statuses.</div>';
        console.error('Error checking backend status:', error);
    }
}

// --- Gestione Attacchi Dinamici ---
function addAttack() {
    const newAttack = {
        type: 'port_scan',
        target: 'web-server',
        params: {}
    };
    attacks.push(newAttack);
    renderAttacks();
}

function removeAttack(index) {
    attacks.splice(index, 1);
    renderAttacks();
}

function renderAttacks() {
    const container = document.getElementById('attacksContainer');
    container.innerHTML = ''; 

    attacks.forEach((attack, index) => {
        const attackEntryDiv = document.createElement('div');
        attackEntryDiv.className = 'attack-entry';
        attackEntryDiv.innerHTML = `
            <button class="remove-button" onclick="removeAttack(${index})">Remove</button>
            <label>Attack Type:</label>
            <select id="attackType_${index}" onchange="updateAttack(${index}, 'type', this.value); toggleAttackParamsInEntry(${index})">
                <option value="port_scan" ${attack.type === 'port_scan' ? 'selected' : ''}>Port Scan</option>
                <option value="brute_force" ${attack.type === 'brute_force' ? 'selected' : ''}>Brute Force</option>
                <option value="lateral_movement_ssh" ${attack.type === 'lateral_movement_ssh' ? 'selected' : ''}>Lateral Movement (SSH)</option>
                <option value="malware_drop" ${attack.type === 'malware_drop' ? 'selected' : ''}>Malware Drop</option>
                <option value="dos_ip_flood" ${attack.type === 'dos_ip_flood' ? 'selected' : ''}>DoS IP Flood</option>
            </select>

            <label>Target VM:</label>
            <select id="targetName_${index}" onchange="updateAttack(${index}, 'target', this.value)">
                <option value="web-server" ${attack.target === 'web-server' ? 'selected' : ''}>Web Server</option>
                <option value="db-server" ${attack.target === 'db-server' ? 'selected' : ''}>DB Server</option>
                <option value="internal-client" ${attack.target === 'internal-client' ? 'selected' : ''}>Internal Client</option>
                <option value="dns-server" ${attack.target === 'dns-server' ? 'selected' : ''}>DNS Server</option>
            </select>

            <div id="attackParams_${index}" class="attack-params">
                </div>
        `;
        container.appendChild(attackEntryDiv);

        renderAttackSpecificParams(index, attack.type, attack.params);
    });
}

function renderAttackSpecificParams(index, type, params) {
    const paramsDiv = document.getElementById(`attackParams_${index}`);
    paramsDiv.innerHTML = ''; 

    switch (type) {
        case 'port_scan':
            paramsDiv.innerHTML = `
                <label>Scan Type (Nmap):</label>
                <input type="text" id="scanType_${index}" value="${params.scan_type || '-sS'}" onchange="updateAttackParams(${index}, 'scan_type', this.value)">
                <label>Ports (e.g., 80,443,22 or 1-1000):</label>
                <input type="text" id="ports_${index}" value="${params.ports || '22,80,443,3306'}" onchange="updateAttackParams(${index}, 'ports', this.value)">
            `;
            break;
        case 'brute_force':
            paramsDiv.innerHTML = `
                <label>Service (e.g., ssh, ftp, mysql):</label>
                <input type="text" id="bfService_${index}" value="${params.service || 'ssh'}" onchange="updateAttackParams(${index}, 'service', this.value)">
                <label>Usernames (comma-separated):</label>
                <input type="text" id="usernameList_${index}" value="${(params.username_list || ['admin', 'user']).join(',')}" onchange="updateAttackParams(${index}, 'username_list', this.value.split(',').map(s => s.trim()))">
                <label>Passwords (comma-separated):</label>
                <input type="text" id="passwordList_${index}" value="${(params.password_list || ['password', '123456']).join(',')}" onchange="updateAttackParams(${index}, 'password_list', this.value.split(',').map(s => s.trim()))">
            `;
            break;
        case 'lateral_movement_ssh':
            paramsDiv.innerHTML = `
                <label>Username:</label>
                <input type="text" id="lmUsername_${index}" value="${params.username || 'user'}" onchange="updateAttackParams(${index}, 'username', this.value)">
                <label>Password:</label>
                <input type="password" id="lmPassword_${index}" value="${params.password || 'password'}" onchange="updateAttackParams(${index}, 'password', this.value)">
                <label>Command to execute:</label>
                <textarea id="lmCommand_${index}" onchange="updateAttackParams(${index}, 'command', this.value)">${params.command || 'ls -la /'}</textarea>
            `;
            break;
        case 'malware_drop':
            paramsDiv.innerHTML = `
                <label>Malware Server:</label>
                <input type="text" id="malwareUrl_${index}" value="${params.malware_url}" onchange="updateAttackParams(${index}, 'malware_url', this.value)">
                <label>SSH Username:</label>
                <input type="text" id="sshUsername_${index}" value="${params.ssh_username || 'user'}" onchange="updateAttackParams(${index}, 'ssh_username', this.value)">
                <label>SSH Password:</label>
                <input type="password" id="sshPassword_${index}" value="${params.ssh_password || 'password'}" onchange="updateAttackParams(${index}, 'ssh_password', this.value)">
            `;
            break;
	case 'dos_ip_flood':
            paramsDiv.innerHTML = `
                <label>Target Port (e.g., 80 per HTTP, 53 per DNS):</label>
                <input type="number" id="dosTargetPort_${index}" value="${params.target_port || 80}" onchange="updateAttackParams(${index}, 'target_port', parseInt(this.value))">
                <label>Duration (seconds):</label>
                <input type="number" id="dosDuration_${index}" value="${params.duration_seconds || 30}" onchange="updateAttackParams(${index}, 'duration_seconds', parseInt(this.value))">
                <label>Flood Type (e.g. SYN/UDP/ICMP):</label>
                <input type="text" id="dosFloodType_${index}" value="${params.flood_type || 'SYN'}" onchange="updateAttackParams(${index}, 'flood_type', this.value)">
            `;
            break;
    }
}

function updateAttack(index, field, value) {
    if (field === 'type') {
        attacks[index].type = value;
        attacks[index].params = {}; 
    } else if (field === 'target') {
        attacks[index].target = value;
    }
    renderAttackSpecificParams(index, attacks[index].type, attacks[index].params);
}

function updateAttackParams(attackIndex, paramKey, paramValue) {
    attacks[attackIndex].params[paramKey] = paramValue;
}

function toggleAttackParamsInEntry(index) {
    const attackType = document.getElementById(`attackType_${index}`).value;
    renderAttackSpecificParams(index, attackType, attacks[index].params);
}

// --- Funzione per Avviare la Simulazione Completa ---
async function startFullSimulation() {
    const simulationDuration = document.getElementById('simulationDuration').value;

    const payload = {
        simulation_duration_seconds: parseInt(simulationDuration),
        attacks: attacks.map(a => ({ 
            attack_type: a.type,
            target_name: a.target,
            params: a.params
        }))
    };

    const responseDiv = document.getElementById('response');
    responseDiv.textContent = 'Starting full simulation...';
    document.getElementById('attackResponseOutput').textContent = 'Nessuna risposta attacco ancora.'; // Clear previous attack responses
    lastResponseTimestamps = {}; // Reset timestamps for new simulation

    try {
        const res = await fetch(`${backendUrl}/api/start_simulation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        responseDiv.textContent = JSON.stringify(data, null, 2);
        startPollingAttackResponses(); // Inizia a interrogare le risposte degli attacchi
    } catch (error) {
        responseDiv.textContent = 'Error starting simulation: ' + error.message;
        console.error('Error:', error);
    }
}


// NUOVA FUNZIONE: Avvia il polling per le risposte degli attacchi
function startPollingAttackResponses() {
    if (attackResponsePollingInterval) {
        clearInterval(attackResponsePollingInterval);
    }
    attackResponsePollingInterval = setInterval(getAttackResponses, 5000); // Poll every 2 seconds
    console.log("Iniziato il polling delle risposte degli attacchi.");
}

// NUOVA FUNZIONE: Richiede le risposte degli attacchi al backend e le visualizza
async function getAttackResponses() {
    try {
        const response = await fetch(`${backendUrl}/api/attack_results`); 
        const data = await response.json();

        if (data.status === "success" && data.results.length > 0) {
            const outputDiv = document.getElementById('attackResponseOutput');
            data.results.forEach(res => {
                // Crea un identificatore unico per ogni risposta per evitare duplicati
                // Ho aggiunto l'intero `JSON.stringify(res)` all'ID per una robustezza massima contro duplicati
                const responseId = JSON.stringify(res); 
                if (!lastResponseTimestamps[responseId]) {
                    const message = `[${new Date(res.timestamp * 1000).toLocaleTimeString()}] Attacco ${res.attack_type} su ${res.target_ip}: Status: ${res.status.toUpperCase()}`;
                    const details = res.output || res.message;
                    outputDiv.textContent += `\n${message}\nDetails: ${details}\n---`;
                    outputDiv.scrollTop = outputDiv.scrollHeight; // Scroll to bottom
                    lastResponseTimestamps[responseId] = true; // Marca come visualizzato
                }
            });
        }
    } catch (error) {
        console.error("Errore durante il recupero delle risposte degli attacchi:", error);
        // Puoi aggiungere un messaggio visibile se l'errore è persistente
    }
}

// Inizializza la GUI all'avvio
document.addEventListener('DOMContentLoaded', () => {
    checkBackendStatus(); 
    setInterval(checkBackendStatus, 10000); 
    renderAttacks(); 
});
