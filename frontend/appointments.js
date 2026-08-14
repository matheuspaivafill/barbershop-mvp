console.log("appointments.js carregou", new Date())

let clients = []
const clientSelect = document.getElementById("client-select")
const appointmentButton =
    document.getElementById("create-appointment-button")
const date = document.getElementById("date")
const time = document.getElementById("time")
const appointmentsList = document.getElementById("appointments-list")


date.addEventListener("change", function() {

    loadAvailableTimes()
})

appointmentButton.addEventListener("click", function (event) {

    event.preventDefault()

    if (!clientSelect.value) {
        alert("Selecione um cliente")
        return
    }

    fetch(`${API_URL}/appointment`, {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        client_id: Number(clientSelect.value),
        date: date.value,
        time: time.value
    })
})
    .then(response => response.json())
    
    .then(data => {

        console.log(data)

        if (data.Error) {
            alert(data.Error)
            return
        }

        showToast("Agendamento criado com sucesso!")

    //loadAppointments()

    clientSelect.selectedIndex = 0
    date.value = ""
    time.value = ""

})

    .catch(error => {

    console.log(error)

    showToast("Erro ao criar agendamento!", true)
})

})

function loadAppointments() {
    appointmentsList.innerHTML = ""

    fetch(`${API_URL}/appointments`)

        .then(response => response.json())

        .then(data => {

            console.log(data)

            updateNextAppointment(data)

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

            console.log(
                "appointment:",
                appointment.client_id,
                "client:",
                client
            )

            appointmentCard.innerText =
            `${clientName}
            | Data: ${appointment.date}
            | Horário: ${appointment.time}`
            
            appointmentCard.appendChild(deleteButton)

            deleteButton.addEventListener("click", function() {

                fetch(
                    `${API_URL}/appointment/${appointment.id}`,
                    {
                    method: "DELETE"
                })

               .then(response => response.json())

               .then(data => {

                    console.log(data)

                    showToast("Agendamento excluído com sucesso!")

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

function loadClients() {

    fetch(`${API_URL}/clients`)

        .then(response => response.json())

        .then(data => {

            clients = data

            clientSelect.innerHTML = ""

            const defaultOption = document.createElement("option")

            defaultOption.value = ""
            defaultOption.innerText = "Selecione um cliente"
            
            clientSelect.appendChild(defaultOption)

            data.forEach(function(client) {

                const option = document.createElement("option")

                option.value = client.id
                option.innerText = client.name

                clientSelect.appendChild(option)

            })
            
            //loadAppointments()

        })

        .catch(error => {

            console.log(error)

        })

        
}

function loadAvailableTimes() {

    if (!date.value) {
        return
    }

    fetch(`${API_URL}/available-times/${date.value}`)

        .then(response => response.json())

        .then(data => {

            time.innerHTML = ""

            data.forEach(function(hour) {

                const option = document.createElement("option")

                option.value = hour
                option.innerText = hour

                time.appendChild(option)

            

            })

        })

        .catch(error => {

            console.log(error)

        })

}

if (clientSelect) {
    loadClients()
}

