const socket = io();
let obstacles = new Set();
let robotX = 0;
let robotY = 0;

// Cria a grade 10x10
const grid = document.getElementById("grid-container");
for (let y = 0; y < 10; y++) {
    for (let x = 0; x < 10; x++) {
        const cell = document.createElement("div");
        cell.classList.add("cell");
        cell.id = `cell-${x}-${y}`;
        grid.appendChild(cell);
    }
}

// Atualiza posição e obstáculos
socket.on("robot_position", data => {
    robotX = data.x;
    robotY = data.y;
    updateGrid();
});

socket.on("obstacle_update", data => {
    obstacles = new Set(data.obstacles.map(pos => `${pos.x}-${pos.y}`));
    updateGrid();
});

function updateGrid() {
    for (let y = 0; y < 10; y++) {
        for (let x = 0; x < 10; x++) {
            const cell = document.getElementById(`cell-${x}-${y}`);
            cell.className = "cell";
            if (x === robotX && y === robotY) {
                cell.classList.add("robot");
            } else if (obstacles.has(`${x}-${y}`)) {
                cell.classList.add("obstacle");
            }
        }
    }
}

function sendCommand(cmd) {
    const next = { x: robotX, y: robotY };
    if (cmd === 'F') next.y -= 1;
    else if (cmd === 'T') next.y += 1;
    else if (cmd === 'E') next.x -= 1;
    else if (cmd === 'D') next.x += 1;

    const nextKey = `${next.x}-${next.y}`;
    if (obstacles.has(nextKey)) {
        alert("Obstáculo detectado! Comando bloqueado.");
        return;
    }

    fetch("/send_command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd })
    }).then(res => res.json()).then(data => {
        if (!data.success) alert("Erro ao enviar comando.");
    });
}

function checkBrokerStatus() {
    fetch("/broker_status")
        .then(res => res.json())
        .then(data => {
            document.getElementById("broker-status").textContent = data.mosquitto_running ? "Rodando" : "Parado";
            document.getElementById("mqtt-status").textContent = data.connected ? "Conectado" : "Desconectado";
        });
}

function sendCommand(command) {
    socket.emit('send_command', { command: command });
}

function sendWait() {
    const seconds = document.getElementById('waitTime').value;
    if (seconds && !isNaN(seconds)) {
        const command = seconds + 'W';
        sendCommand(command);
    }
}
function definirBase() {
    socket.emit('definir_base');
  }


  
setInterval(checkBrokerStatus, 3000);
