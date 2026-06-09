console.log("appointments.js carregou")

const button = document.getElementById("register-button")
const clientId = document.getElementById("client_id")
const date = document.getElementById("date")
const time = document.getElementById("time")


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

    alert("Agendamento criado!")

    clientId.value = ""
    date.value = ""
    time.value = ""

})

    .catch(error => {

    console.log(error)
})

})

