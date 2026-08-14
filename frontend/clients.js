window.addEventListener("beforeunload", function () {
    console.log("A página vai recarregar!")
})
const button = document.getElementById("register-client-button")
const name = document.getElementById("name")
const phone = document.getElementById("phone")
const clientsList = document.getElementById("clients-list")


console.log("Script carregou", new Date())


button.addEventListener("click", function (event) {

    event.preventDefault()

    console.log(name.value)

    console.log(phone.value)

    console.log("Botão clicado!")
    
    
    fetch(`${API_URL}/client`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
        name: name.value, 
        phone: phone.value})
        
    
})
    .then(response => response.json())

    .then(data => {

        console.log(data)

        showToast("Cliente cadastrado com sucesso!");
        name.value = "";
        hone.value = "";

    })

    .catch(error => {

    console.log(error)

    showToast("Error ao cadastrar cliente!", true)
})
}) 


function loadClients() {

    if (!clientsList) {
        return
    }

    clientsList.innerHTML = ""

    fetch(`${API_URL}/clients`)

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

                    fetch(`${API_URL}/client/${client.id}`, {
                        method: "DELETE"
                    })
                    .then(response => response.json())
                    .then(data => {

                        console.log(data)

                        showToast("Cliente excluído com sucesso!")

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
