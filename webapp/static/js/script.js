// Smooth scrolling for homepage navigation

document.querySelectorAll('a[href^="#"]').forEach(link => {

    link.addEventListener("click", function(event) {

        const target = document.querySelector(this.getAttribute("href"));

        if (target) {
            event.preventDefault();

            target.scrollIntoView({
                behavior: "smooth"
            });
        }

    });

});

const assistantForm = document.getElementById("chat-form");

if (assistantForm) {
    const assistantModal = document.getElementById("assistant-modal");
    const assistantTrigger = document.querySelector(".assistant-trigger");
    const closeButton = assistantModal.querySelector(".close-btn");
    const dialog = assistantModal.querySelector('[role="dialog"]');
    const chatInput = document.getElementById("chat-input");
    const chatHistory = document.getElementById("chat-history");

    function setAssistantOpen(isOpen) {
        assistantModal.hidden = !isOpen;
        assistantModal.classList.toggle("active", isOpen);
        document.body.classList.toggle("modal-open", isOpen);

        if (isOpen) {
            chatInput.focus();
        } else {
            assistantTrigger.focus();
        }
    }

    assistantTrigger.addEventListener("click", () => setAssistantOpen(true));
    closeButton.addEventListener("click", () => setAssistantOpen(false));

    assistantModal.addEventListener("click", event => {
        if (event.target === assistantModal) {
            setAssistantOpen(false);
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !assistantModal.hidden) {
            setAssistantOpen(false);
        }

        if (event.key === "Tab" && !assistantModal.hidden) {
            const focusable = dialog.querySelectorAll("button, input");
            const first = focusable[0];
            const last = focusable[focusable.length - 1];

            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        }
    });

    chatInput.addEventListener("keydown", event => {
        if (event.key === "Enter" && !event.isComposing) {
            event.preventDefault();
            assistantForm.requestSubmit();
        }
    });

    assistantForm.addEventListener("submit", event => {
        event.preventDefault();

        const query = chatInput.value.trim();
        if (!query) return;

        appendChatMessage(query, "user-message");
        chatInput.value = "";

        window.setTimeout(() => {
            const response = getBotResponse(query);
            const botMessage = appendChatMessage(response.text, "bot-message");

            if (response.showScreeningLink) {
                const link = document.createElement("a");
                link.href = "/screening";
                link.textContent = "Open the screening tool";
                botMessage.append(document.createElement("br"), link);
            }

            chatHistory.scrollTop = chatHistory.scrollHeight;
        }, 600);

        chatHistory.scrollTop = chatHistory.scrollHeight;
    });

    function appendChatMessage(text, className) {
        const message = document.createElement("div");
        message.className = `chat-message ${className}`;
        message.textContent = text;
        chatHistory.appendChild(message);
        return message;
    }

    function getBotResponse(query) {
        const normalizedQuery = query.toLowerCase();

        if (/\b(danger|severe|emergency|convulsion|confusion|breathing)\b/.test(normalizedQuery)) {
            return {
                text: "Seek emergency medical care immediately for convulsions, confusion, difficulty breathing, unusual bleeding, yellow eyes or skin, or other severe or rapidly worsening symptoms."
            };
        }
        if (/\b(symptoms?|signs?)\b/.test(normalizedQuery)) {
            return {
                text: "Common malaria symptoms include fever, chills, headache, nausea, vomiting, and muscle aches. Symptoms need medical assessment.",
                showScreeningLink: true
            };
        }
        if (/\b(prevent(?:ion|ed|ing)?|avoid)\b/.test(normalizedQuery)) {
            return {
                text: "Reduce mosquito bites by using an insecticide-treated bed net, applying recommended insect repellent, and wearing covering clothing. Ask a healthcare professional about preventive medicine before travel."
            };
        }
        if (/\b(treat(?:ment|ed|ing)?|cure|medicines?|medications?)\b/.test(normalizedQuery)) {
            return {
                text: "Malaria requires prompt testing and treatment by a healthcare professional. The appropriate prescription depends on factors such as location and patient health; do not self-medicate."
            };
        }
        if (/\b(test|diagnos|diagnosis)\b/.test(normalizedQuery)) {
            return {
                text: "Malaria is diagnosed with a test, such as a rapid diagnostic test or blood smear. This chat and our screening tool cannot diagnose malaria."
            };
        }
        if (/\b(child|children|baby|babies|kid|kids)\b/.test(normalizedQuery)) {
            return {
                text: "Young children are at increased risk of severe malaria. If a child has a fever or may have malaria, seek prompt medical assessment and testing."
            };
        }
        if (/\b(hello|hi|hey)\b/.test(normalizedQuery)) {
            return {
                text: "Hello! I can share general information about malaria symptoms, prevention, testing, and treatment."
            };
        }

        return {
            text: "I can help with general information about malaria symptoms, prevention, testing, or treatment. For personal medical advice, please speak with a healthcare professional."
        };
    }
}