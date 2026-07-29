const clientsList = document.getElementById("clients-list")
const appointmentsList = document.getElementById("appointments-list")
const totalClients = document.getElementById("total-clients")
const totalAppointments = document.getElementById("total-appointments")
const searchClient = document.getElementById("search-client")
const searchAppointment = document.getElementById("search-appointment")
const clientsTitle = document.getElementById("clients-title")
const appointmentsTitle = document.getElementById("appointments-title")


let clients = []

function loadClients() {

    console.log("loadClients executou")

    clientsList.innerHTML = ""

    fetch("http://127.0.0.1:8000/clients")

        .then(response => response.json())

        .then(data => {

            clients = data

            clientsTitle.innerText =
            `Clientes (${data.length})`

            totalClients.innerText = data.length

            console.log(data)

            clientsList.innerHTML = ""

            data.forEach(function(client) {

                const search = searchClient.value.toLowerCase()

                if (!client.name.toLowerCase().includes(search)){

                    return

                }

                const clientCard = document.createElement("div")
                const deleteButton = document.createElement("button")

                deleteButton.innerText = "🗑"

                clientCard.classList.add("client-card")
                clientCard.innerHTML = `
                    <div class="card-info">
                    <h3>👤 ${client.name}</h3>
                    <p>📞 ${client.phone}</p>
                    </div>
                `
                clientCard.appendChild(deleteButton)
                clientsList.appendChild(clientCard)

                deleteButton.addEventListener("click", function() {

                    if (!confirm("Deseja realmente excluir este cliente?")){

                        return

                    }

                    fetch(`http://127.0.0.1:8000/client/${client.id}`, {
                        method: "DELETE"
                    })

                    .then(response => response.json())

                    .then(data => {

                        console.log(data)

                        loadClients()

                    })

                    .catch(error => {

                        console.log(error)

                    })

                })

            })

            loadAppointments()

        })

        .catch(error => {

            console.log(error)

        })

}

function loadAppointments() {

    console.log("loadAppointments executou")

    appointmentsList.innerHTML = ""

    fetch("http://127.0.0.1:8000/appointments")

        .then(response => response.json())

        .then(data => {

            console.log(data)

            appointmentsTitle.innerText =
            `Agendamentos (${data.length})`

            totalAppointments.innerText = data.length

            appointmentsList.innerHTML = ""

            data.forEach(function(appointment) {

                const appointmentCard = document.createElement("div")
                const deleteButton = document.createElement("button")

                deleteButton.innerText = "🗑"

                appointmentCard.classList.add("client-card")

                const client = clients.find(
                    c => c.id === appointment.client_id
                )

                const clientName = client
                    ? client.name
                    : `Cliente ${appointment.client_id}`

                const search = searchAppointment.value.toLowerCase()

                if (!clientName.toLowerCase().includes(search)){

                    return

                }

                console.log(
                    "appointment:",
                    appointment.client_id,
                    "client:",
                    client
                )

                appointmentCard.innerHTML = `
                    <div class="card-info">
                        <h3>📅 ${clientName}</h3>
                        <p>🗓 ${appointment.date}</p>
                        <p>🕒 ${appointment.time}</p>
                    </div>
                `

                appointmentCard.appendChild(deleteButton)

                deleteButton.addEventListener("click", function() {

                    if (!confirm("Deseja realmente excluir este agendamento?")){

                        return

                    }
                    
                    fetch(
                        `http://127.0.0.1:8000/appointment/${appointment.id}`,
                        {
                            method: "DELETE"
                        }
                    )

                    .then(response => response.json())

                    .then(data => {

                        console.log(data)

                        loadAppointments()

                    })

                    .catch(error => {

                        console.log(error)

                    })

                })

                appointmentsList.appendChild(appointmentCard)

            })

        })

        .catch(error => {

            console.log(error)

        })

}

loadClients()

searchClient.addEventListener("input", function() {

    loadClients()
})

searchAppointment.addEventListener("input",function(){

    loadAppointments()

})