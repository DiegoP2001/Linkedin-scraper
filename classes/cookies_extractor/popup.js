const AUTHORIZED_EMAILS = [
    "email@domain.com",
    "email@domain.com",
    "email@domain.com",
    "email@domain.com",
    "email@domain.com",
]

document.getElementById("getCookies").addEventListener("click", function() {
    const email = document.querySelector("#email").value
    const emailRegex = /^[a-zA-Z0-9._%+-]+@domain\.com$/;
    if (!emailRegex.test(email)) {
        alert("El correo introducido debe pertenecer a DOMAIN. Ej:(abc@domain.com)")
        return
    }

    if (!AUTHORIZED_EMAILS.includes(email)) {
        alert("El correo introducido no está autorizado a para utilizar la extensión. Contacta con el administrador.")
        return
    }
    
    chrome.runtime.sendMessage({ action: "getCookies", email: email }, (response) => {
        document.getElementById("status").innerText = response.message;
    });
});
