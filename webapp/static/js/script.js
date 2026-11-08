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

const contactForm = document.getElementById("contact-form");

if (contactForm) {
    const contactStatus = document.getElementById("contact-status");
    const submitButton = contactForm.querySelector('button[type="submit"]');

    contactForm.addEventListener("submit", async event => {
        event.preventDefault();
        contactStatus.textContent = "";
        submitButton.disabled = true;

        try {
            const response = await fetch(contactForm.action, {
                method: "POST",
                body: new FormData(contactForm)
            });
            const contentType = response.headers.get("content-type") || "";
            const result = contentType.includes("application/json")
                ? await response.json()
                : null;

            if (!response.ok) {
                throw new Error(
                    (result && result.message) ||
                    `Failed to send email (HTTP ${response.status}). Please try again later.`
                );
            }

            if (!result || result.status !== "success") {
                throw new Error("The server returned an invalid response. Please try again later.");
            }

            contactForm.reset();
            contactStatus.textContent = "Message sent successfully! We’ll get back to you soon.";
        } catch (error) {
            contactStatus.textContent = error instanceof TypeError
                ? "Network error. Please check your connection and try again."
                : error.message;
        } finally {
            submitButton.disabled = false;
        }
    });
}

const menuToggle = document.querySelector(".menu-toggle");
const navLinks = document.getElementById("nav-links");

if (menuToggle && navLinks) {
    function setMenuOpen(isOpen) {
        navLinks.classList.toggle("active", isOpen);
        menuToggle.setAttribute("aria-expanded", String(isOpen));
        menuToggle.setAttribute("aria-label", isOpen ? "Close navigation menu" : "Open navigation menu");
    }

    menuToggle.addEventListener("click", () => {
        setMenuOpen(menuToggle.getAttribute("aria-expanded") !== "true");
    });

    navLinks.addEventListener("click", event => {
        if (event.target.closest("a")) {
            setMenuOpen(false);
        }
    });

    document.addEventListener("click", event => {
        if (!event.target.closest(".navbar") && menuToggle.getAttribute("aria-expanded") === "true") {
            setMenuOpen(false);
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") {
            setMenuOpen(false);
            menuToggle.focus();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 768) {
            setMenuOpen(false);
        }
    });
}

const mosquitoCanvas = document.getElementById("mosquito-canvas");

if (mosquitoCanvas) {
    const context = mosquitoCanvas.getContext("2d");

    if (context) {
        let width = 0;
        let height = 0;
        let animationFrame;

        function resizeMosquitoCanvas() {
            const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
            width = window.innerWidth;
            height = window.innerHeight;
            mosquitoCanvas.width = width * pixelRatio;
            mosquitoCanvas.height = height * pixelRatio;
            context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        }

        const mosquitoes = Array.from({ length: 15 }, () => ({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            size: Math.random() * 2 + 1,
            speedX: Math.random() * 2 - 1,
            speedY: Math.random() * 2 - 1
        }));

        function animateMosquitoes() {
            context.clearRect(0, 0, width, height);

            mosquitoes.forEach(mosquito => {
                mosquito.x += mosquito.speedX;
                mosquito.y += mosquito.speedY;

                if (mosquito.x > width || mosquito.x < 0) mosquito.speedX *= -1;
                if (mosquito.y > height || mosquito.y < 0) mosquito.speedY *= -1;

                context.fillStyle = "rgba(209, 179, 255, 0.4)";
                context.beginPath();
                context.arc(mosquito.x, mosquito.y, mosquito.size, 0, Math.PI * 2);
                context.fill();

                context.beginPath();
                context.moveTo(mosquito.x, mosquito.y);
                context.lineTo(mosquito.x - mosquito.size * 2, mosquito.y - mosquito.size * 2);
                context.lineTo(mosquito.x + mosquito.size * 2, mosquito.y - mosquito.size * 2);
                context.fillStyle = "rgba(209, 179, 255, 0.2)";
                context.fill();
            });

            animationFrame = window.requestAnimationFrame(animateMosquitoes);
        }

        resizeMosquitoCanvas();
        window.addEventListener("resize", resizeMosquitoCanvas);
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                window.cancelAnimationFrame(animationFrame);
            } else {
                animationFrame = window.requestAnimationFrame(animateMosquitoes);
            }
        });
        animateMosquitoes();
    }
}