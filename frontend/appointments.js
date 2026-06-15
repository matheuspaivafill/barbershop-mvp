console.log("appointments.js carregou")
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

    fetch("http://127.0.0.1:8000/appointment", {
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

    alert("Agendamento criado!")

    //loadAppointments()

    clientSelect.selectedIndex = 0
    date.value = ""
    time.value = ""

})

    .catch(error => {

    console.log(error)

    alert("Erro ao criar agendamento!")
})

})

function loadAppointments() {
    appointmentsList.innerHTML = ""

    fetch("http://127.0.0.1:8000/appointments")

        .then(response => response.json())

        .then(data => {

            console.log(data)

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

function loadClients() {

    fetch("http://127.0.0.1:8000/clients")

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

    fetch(`http://127.0.0.1:8000/available-times/${date.value}`)

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

