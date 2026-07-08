const clientsList = document.getElementById("clients-list")
let clients = []
const appointmentsList = document.getElementById("appointments-list")


function loadClients() {

    clientsList.innerHTML = ""

    fetch("http://127.0.0.1:8000/clients")

        .then(response => response.json())

        .then(data => {

            clients = data

            console.log(data)

            data.forEach(function(client) {

        const clientCard = document.createElement("div")
        const deleteButton = document.createElement("button")

            deleteButton.innerText = "🗑"

        clientCard.classList.add("client-card")

        clientCard.innerText =
            `${client.name} - ${client.phone}`

        clientCard.appendChild(deleteButton)

        clientsList.appendChild(clientCard)

        deleteButton.addEventListener("click", function() {

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

    })})
        loadAppointments()

})

        .catch(error => {

            console.log(error)

        })

}
loadClients()

function loadAppointments() {
    appointmentsList.innerHTML = ""

    fetch("http://127.0.0.1:8000/appointments")

        .then(response => response.json())

        .then(data => {

            console.log(data)

            data.forEach(function(appointment){

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
        .catch(error => {
            console.log(error)
        })
    })
}
loadClients()