const loginForm = document.getElementById("login-form")
const emailInput = document.getElementById("login-email")
const passwordInput = document.getElementById("login-password")

loginForm.addEventListener("submit", function (event) {
    event.preventDefault()

    fetch(`${API_URL}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: emailInput.value,
            password: passwordInput.value
        })
    })
    .then(async response => {
        const data = await response.json()
        if (!response.ok) {
            throw new Error(data.detail || "Erro ao fazer login")
        }
        return data
    })
    .then(data => {
        // Guarda o token e dados da empresa no navegador
        localStorage.setItem("token", data.token)
        localStorage.setItem("businessName", data.business_name)
        localStorage.setItem("slug", data.slug)

        showToast("Login efetuado com sucesso!")

        // Redireciona para o painel de administração
        setTimeout(() => {
            window.location.href = "admin.html"
        }, 1000)
    })
    .catch(error => {
        console.error(error)
        showToast(error.message, true)
    })
})