// config.js
// Em desenvolvimento local (abrindo o front pelo 127.0.0.1/localhost), usa a API local.
// Em produção, aponta pro backend publicado no Render.
const API_URL = ["localhost", "127.0.0.1"].includes(window.location.hostname)
    ? "http://127.0.0.1:8000"
    : "https://agenda-pro-backend.onrender.com";
