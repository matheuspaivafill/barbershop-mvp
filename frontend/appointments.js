console.log("appointments.js carregou")

const button = document.getElementById("register-button")
const clientId = document.getElementById("client_id")
const date = document.getElementById("date")
const time = document.getElementById("time")
const appointmentsList = document.getElementById("appointments-list")


button.addEventListener("click", function (event) {

    event.preventDefault()

    fetch("http://127.0.0.1:8000/appointment", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        client_id: Number(clientId.value),
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

    loadAppointments()

    clientId.value = ""
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

            

            appointmentCard.innerText =
            `Cliente ID: ${appointment.client_id}
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
loadAppointments()