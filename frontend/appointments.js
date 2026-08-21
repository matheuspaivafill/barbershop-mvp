window.currentBusinessId = null

const businessDisplayName = document.getElementById("business-display-name")
const selectBusinessSection = document.getElementById("select-business-section")
const searchBusinessInput = document.getElementById("search-business-input")
const businessSearchStatus = document.getElementById("business-search-status")

const appointmentForm = document.getElementById("appointment-form")
const clientSelect = document.getElementById("client-select")
const confirmPhone = document.getElementById("confirm-phone")
const appointmentDate = document.getElementById("appointment-date")
const timeSelect = document.getElementById("time-select")
const submitAppointmentBtn = document.getElementById("submit-appointment-btn")

function initBusinessContext() {
    const urlParams = new URLSearchParams(window.location.search)
    const slug = urlParams.get("slug")

    if (slug) {
        fetch(`${API_URL}/business/slug/${slug}`)
        .then(res => res.json())
        .then(data => {
            if (data.id) {
                setBusiness(data.id, data.name)
            } else {
                showBusinessSearch("Estabelecimento não encontrado.")
            }
        })
        .catch(() => showBusinessSearch("Erro ao carregar o estabelecimento."))
        return
    }

    // Sem slug na URL: tenta usar o último estabelecimento escolhido nesta aba,
    // pra não obrigar a pessoa a buscar de novo se ela já tinha selecionado.
    const savedId = sessionStorage.getItem("selectedBusinessId")
    const savedName = sessionStorage.getItem("selectedBusinessName")
    if (savedId && savedName) {
        setBusiness(parseInt(savedId), savedName)
    } else {
        showBusinessSearch()
    }
}

function setBusiness(id, name) {
    window.currentBusinessId = id
    sessionStorage.setItem("selectedBusinessId", id)
    sessionStorage.setItem("selectedBusinessName", name)
    businessDisplayName.innerText = `Agendando em: ${name}`
    selectBusinessSection.style.display = "none"
    loadClients()
    const submitClientBtn = document.getElementById("submit-client-btn")
    if (submitClientBtn) submitClientBtn.disabled = false
}

function showBusinessSearch(message = "") {
    businessDisplayName.innerText = "Agendamento Online"
    selectBusinessSection.style.display = "block"
    if (message) businessSearchStatus.innerText = message
}

// Busca a lista de clientes cadastrados no estabelecimento atual
function loadClients() {
    if (!window.currentBusinessId || !clientSelect) return

    fetch(`${API_URL}/clients/public/${window.currentBusinessId}`)
    .then(res => res.json())
    .then(clients => {
        clientSelect.innerHTML = '<option value="">Selecione seu nome</option>'
        clients.forEach(client => {
            const option = document.createElement("option")
            option.value = client.id
            option.innerText = client.name
            clientSelect.appendChild(option)
        })
    })
    .catch(err => console.error(err))
}

if (searchBusinessInput) {
    searchBusinessInput.addEventListener("change", function() {
        const slug = searchBusinessInput.value.trim().toLowerCase().replace(/\s+/g, "-")
        if (!slug) return

        fetch(`${API_URL}/business/slug/${slug}`)
        .then(res => res.json())
        .then(data => {
            if (data.id) {
                setBusiness(data.id, data.name)
                businessSearchStatus.innerText = `Encontrado: ${data.name}`
            } else {
                businessSearchStatus.innerText = "Estabelecimento não encontrado."
            }
        })
        .catch(() => {
            businessSearchStatus.innerText = "Estabelecimento não encontrado."
        })
    })
}

appointmentDate.addEventListener("change", function() {
    if (!window.currentBusinessId || !appointmentDate.value) return

    fetch(`${API_URL}/available-times/${window.currentBusinessId}/${appointmentDate.value}`)
    .then(res => res.json())
    .then(times => {
        timeSelect.innerHTML = ""
        
        if (times.length === 0) {
            timeSelect.innerHTML = '<option value="">Sem horários disponíveis para esta data</option>'
            timeSelect.disabled = true
            submitAppointmentBtn.disabled = true
            return
        }

        timeSelect.innerHTML = '<option value="">Selecione um horário</option>'
        times.forEach(time => {
            const option = document.createElement("option")
            option.value = time
            option.innerText = time
            timeSelect.appendChild(option)
        })

        timeSelect.disabled = false
        submitAppointmentBtn.disabled = false
    })
    .catch(error => console.error(error))
})

appointmentForm.addEventListener("submit", function(event) {
    event.preventDefault()

    if (!window.currentBusinessId || !clientSelect.value || !confirmPhone.value.trim() || !appointmentDate.value || !timeSelect.value) {
        showToast("Preencha todos os campos do agendamento.", true)
        return
    }

    fetch(`${API_URL}/appointment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            business_id: window.currentBusinessId,
            client_id: parseInt(clientSelect.value),
            phone: confirmPhone.value.trim(),
            date: appointmentDate.value,
            time: timeSelect.value
        })
    })
    .then(async response => {
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || "Erro ao agendar")
        return data
    })
    .then(data => {
        showToast("Agendamento realizado com sucesso!")
        appointmentForm.reset()
        confirmPhone.value = ""
        timeSelect.disabled = true
        submitAppointmentBtn.disabled = true
    })
    .catch(error => {
        console.error(error)
        showToast(error.message, true)
    })
})

initBusinessContext()