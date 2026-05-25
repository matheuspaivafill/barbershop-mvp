const button = document.getElementById("register-button")
const name = document.getElementById("name")
const phone = document.getElementById("phone")
const clientsList = document.getElementById("clients-list")


console.log("Script carregou")

button.addEventListener("click", function (event) {

    event.preventDefault()

    console.log(name.value)

    console.log(phone.value)

    console.log("Botão clicado!")
    
    
    fetch("http://127.0.0.1:8000/client", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        name: name.value, 
        phone: phone.value})
        
    
})
    .then(response => response.json())

    .then(data => {

    console.log(data)

    alert("Cliente criado!")

    name.value = ""
    phone.value = ""

})

    .catch(error => {

    console.log(error)
})
}) 


function loadClients() {

    clientsList.innerHTML = ""

    fetch("http://127.0.0.1:8000/clients")

        .then(response => response.json())

        .then(data => {

            console.log("DEBUG:", data)

            data.forEach(function(client) {

                const clientCard = document.createElement("div")

                clientCard.classList.add("client-card")

                clientCard.innerText = `${client.name} - ${client.phone}`

                const deleteButton = document.createElement("button")

                deleteButton.innerText = "🗑"

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

                })

            })

        })

        .catch(error => {
            console.log(error)
        })
}
loadClients()
