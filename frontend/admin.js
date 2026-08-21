// Verifica se o utilizador está logado. Se não estiver, envia para a página de login
const token = localStorage.getItem("token")
if (!token) {
    window.location.href = "login.html"
}

const clientsList = document.getElementById("clients-list")
const appointmentsList = document.getElementById("appointments-list")
const totalClients = document.getElementById("total-clients")
const totalAppointments = document.getElementById("total-appointments")
const searchClient = document.getElementById("search-client")
const searchAppointment = document.getElementById("search-appointment")
const clientsTitle = document.getElementById("clients-title")
const appointmentsTitle = document.getElementById("appointments-title")

let clients = []

// Função auxiliar com os cabeçalhos de autenticação
function getAuthHeaders() {
    return {
        "Authorization": `Bearer ${localStorage.getItem("token")}`,
        "Content-Type": "application/json"
    }
}

function loadClients() {
    fetch(`${API_URL}/clients`, {
        headers: getAuthHeaders()
    })
    .then(response => {
        if (response.status === 401) {
            localStorage.clear()
            window.location.href = "login.html"
            return
        }
        return response.json()
    })
    .then(data => {
        if (!data) return
        clients = data
        clientsTitle.innerText = `Clientes (${data.length})`
        totalClients.innerText = data.length
        clientsList.innerHTML = ""

        data.forEach(function(client) {
            const search = searchClient ? searchClient.value.toLowerCase() : ""
            if (!client.name.toLowerCase().includes(search)) return

            const clientCard = document.createElement("div")
            const deleteButton = document.createElement("button")
            deleteButton.innerText = "🗑"

            clientCard.classList.add("client-card")

            const info = document.createElement("div")
            info.classList.add("card-info")

            const nameEl = document.createElement("h3")
            nameEl.textContent = `👤 ${client.name}`

            const phoneEl = document.createElement("p")
            phoneEl.textContent = `📞 ${client.phone}`

            info.appendChild(nameEl)
            info.appendChild(phoneEl)
            clientCard.appendChild(info)
            clientCard.appendChild(deleteButton)
            clientsList.appendChild(clientCard)

            deleteButton.addEventListener("click", function() {
                if (!confirm("Deseja realmente excluir este cliente?")) return

                fetch(`${API_URL}/client/${client.id}`, {
                    method: "DELETE",
                    headers: getAuthHeaders()
                })
                .then(response => response.json())
                .then(() => loadClients())
                .catch(error => console.error(error))
            })
        })

        loadAppointments()
    })
    .catch(error => console.error(error))
}

function loadAppointments() {
    fetch(`${API_URL}/appointments`, {
        headers: getAuthHeaders()
    })
    .then(response => response.json())
    .then(data => {
        if (!data) return
        appointmentsTitle.innerText = `Agendamentos (${data.length})`
        totalAppointments.innerText = data.length
        appointmentsList.innerHTML = ""

        data.forEach(function(appointment) {
            const appointmentCard = document.createElement("div")
            const deleteButton = document.createElement("button")
            deleteButton.innerText = "🗑"
            appointmentCard.classList.add("client-card")

            const client = clients.find(c => c.id === appointment.client_id)
            const clientName = client ? client.name : `Cliente ${appointment.client_id}`

            const search = searchAppointment ? searchAppointment.value.toLowerCase() : ""
            if (!clientName.toLowerCase().includes(search)) return

            const info = document.createElement("div")
            info.classList.add("card-info")

            const nameEl = document.createElement("h3")
            nameEl.textContent = `📅 ${clientName}`
            const dateEl = document.createElement("p")
            dateEl.textContent = `🗓 ${appointment.date}`
            const timeEl = document.createElement("p")
            timeEl.textContent = `🕒 ${appointment.time}`

            info.appendChild(nameEl)
            info.appendChild(dateEl)
            info.appendChild(timeEl)
            appointmentCard.appendChild(info)
            appointmentCard.appendChild(deleteButton)

            deleteButton.addEventListener("click", function() {
                if (!confirm("Deseja realmente excluir este agendamento?")) return

                fetch(`${API_URL}/appointment/${appointment.id}`, {
                    method: "DELETE",
                    headers: getAuthHeaders()
                })
                .then(response => response.json())
                .then(() => loadAppointments())
                .catch(error => console.error(error))
            })

            appointmentsList.appendChild(appointmentCard)
        })
    })
    .catch(error => console.error(error))
}

loadClients()

if (searchClient) {
    searchClient.addEventListener("input", () => loadClients())
}

if (searchAppointment) {
    searchAppointment.addEventListener("input", () => loadAppointments())
}