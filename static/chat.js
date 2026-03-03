// Handle Enter key to send message
document.addEventListener('DOMContentLoaded', function() {
    const inputField = document.getElementById("user-input");
    inputField.addEventListener('keypress', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
});

async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const message = inputField.value;
    const loadingIndicator = document.getElementById("loading-indicator");
    const sendBtn = document.getElementById("send-btn");

    if (!message.trim()) return;

    addMessage("user", message);
    inputField.value = "";
    inputField.focus();
    
    // Show loading indicator and disable send button
    loadingIndicator.style.display = "flex";
    sendBtn.disabled = true;
    inputField.disabled = true;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        addMessage("bot", data.reply);
    } catch (error) {
        addMessage("bot", "Sorry, there was an error processing your request.");
    } finally {
        // Hide loading indicator and re-enable send button
        loadingIndicator.style.display = "none";
        sendBtn.disabled = false;
        inputField.disabled = false;
        inputField.focus();
    }
}

function addMessage(sender, text) {
    const chatBox = document.getElementById("chat-box");
    const msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "user-message" : "bot-message";
    msgDiv.textContent = text;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}