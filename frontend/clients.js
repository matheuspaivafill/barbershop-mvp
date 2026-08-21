const clientForm = document.getElementById("client-form")
const clientName = document.getElementById("client-name")
const clientPhone = document.getElementById("client-phone")

if (clientForm) {
    clientForm.addEventListener("submit", function(event) {
        event.preventDefault()

        if (!window.currentBusinessId) {
            showToast("Por favor, selecione um estabelecimento primeiro.", true)
            return
        }

        fetch(`${API_URL}/client`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                business_id: window.currentBusinessId,
                name: clientName.value.trim(),
                phone: clientPhone.value.trim()
            })
        })
        .then(async response => {
            const data = await response.json()
            if (!response.ok) throw new Error(data.detail || "Erro ao salvar cliente")
            return data
        })
        .then(data => {
            showToast(data.message)

            clientName.value = ""
            clientPhone.value = ""

            // Recarrega a lista de clientes no dropdown
            if (typeof loadClients === "function") {
                loadClients()
            }
        })
        .catch(error => {
            console.error(error)
            showToast(error.message, true)
        })
    })
}