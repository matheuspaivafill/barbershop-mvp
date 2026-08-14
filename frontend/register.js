const registerForm = document.getElementById("register-form")

registerForm.addEventListener("submit", function (event) {
    event.preventDefault()

    const name = document.getElementById("reg-name").value
    const slug = document.getElementById("reg-slug").value
    const email = document.getElementById("reg-email").value
    const password = document.getElementById("reg-password").value

    fetch(`${API_URL}/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ name, slug, email, password })
    })
    .then(async response => {
        const data = await response.json()
        if (!response.ok) {
            throw new Error(data.detail || "Erro ao criar conta")
        }
        return data
    })
    .then(data => {
        localStorage.setItem("token", data.token)
        localStorage.setItem("slug", data.slug)

        showToast("Conta criada com sucesso!")

        setTimeout(() => {
            window.location.href = "admin.html"
        }, 1000)
    })
    .catch(error => {
        console.error(error)
        showToast(error.message, true)
    })
})