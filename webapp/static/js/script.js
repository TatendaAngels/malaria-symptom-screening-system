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
    const heroTitle = document.querySelector(".hero-title");
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (context && heroTitle && !reducedMotion) {
        let width = 0;
        let height = 0;
        let animationFrame;
        let formationTargets = [];
        let formationMosquitoes = [];
        let formationStartedAt = 0;
        let titleRevealed = false;
        let hiddenAt = null;
        let titleIsInView = false;
        let formationIsActive = false;
        let nextFormationAt = 0;
        const formationDuration = 7600;
        const formationInterval = 20000;

        const ambientMosquitoes = Array.from({ length: 15 }, () => ({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            size: Math.random() * 2 + 1,
            speedX: Math.random() * 2 - 1,
            speedY: Math.random() * 2 - 1
        }));

        function resizeCanvas() {
            const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
            width = window.innerWidth;
            height = window.innerHeight;
            mosquitoCanvas.width = width * pixelRatio;
            mosquitoCanvas.height = height * pixelRatio;
            context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        }

        function collectTextTargets() {
            const targets = [];
            const titleStyle = window.getComputedStyle(heroTitle);
            const fontSize = parseFloat(titleStyle.fontSize);
            const scratchCanvas = document.createElement("canvas");
            const scratchContext = scratchCanvas.getContext("2d", { willReadFrequently: true });

            if (!scratchContext) return targets;

            scratchCanvas.width = Math.ceil(fontSize * 2);
            scratchCanvas.height = Math.ceil(fontSize * 1.6);
            scratchContext.font = titleStyle.font;
            scratchContext.textBaseline = "alphabetic";
            const baseline = fontSize * 1.2;
            const sampleStep = Math.max(2, Math.round(fontSize / 24));

            heroTitle.querySelectorAll(".hero-title-primary, .hero-title-highlight").forEach(block => {
                const textNode = block.firstChild;
                if (!textNode || textNode.nodeType !== Node.TEXT_NODE) return;

                const blockStyle = window.getComputedStyle(block);
                const range = document.createRange();

                for (let index = 0; index < textNode.textContent.length; index += 1) {
                    const character = textNode.textContent[index];
                    if (/\s/.test(character)) continue;

                    range.setStart(textNode, index);
                    range.setEnd(textNode, index + 1);
                    const characterBounds = range.getBoundingClientRect();
                    if (!characterBounds.width || !characterBounds.height) continue;

                    scratchContext.clearRect(0, 0, scratchCanvas.width, scratchCanvas.height);
                    scratchContext.fillText(character, 0, baseline);
                    const metrics = scratchContext.measureText(character);
                    if (!metrics.width) continue;

                    const pixels = scratchContext.getImageData(
                        0, 0, scratchCanvas.width, scratchCanvas.height
                    ).data;
                    const inkPixels = [];

                    for (let y = 0; y < scratchCanvas.height; y += sampleStep) {
                        for (let x = 0; x < scratchCanvas.width; x += sampleStep) {
                            if (pixels[(y * scratchCanvas.width + x) * 4 + 3] > 64) {
                                inkPixels.push({ x, y });
                            }
                        }
                    }

                    const targetCount = Math.min(12, Math.max(3, Math.round(inkPixels.length / 3)));
                    const ascent = metrics.actualBoundingBoxAscent || fontSize * 0.75;
                    const descent = metrics.actualBoundingBoxDescent || fontSize * 0.2;
                    const inkHeight = ascent + descent;
                    const lineOffset = Math.max(0, (characterBounds.height - inkHeight) / 2);
                    const inkTop = baseline - ascent;

                    for (let count = 0; count < targetCount && inkPixels.length; count += 1) {
                        const pixel = inkPixels.splice(
                            Math.floor(Math.random() * inkPixels.length), 1
                        )[0];
                        targets.push({
                            x: characterBounds.left + (pixel.x / metrics.width) * characterBounds.width,
                            y: characterBounds.top + lineOffset + pixel.y - inkTop,
                            color: blockStyle.color
                        });
                    }
                }
            });

            return targets;
        }

        function createFormationMosquitoes() {
            formationTargets = collectTextTargets();
            const titleBounds = heroTitle.getBoundingClientRect();

            formationMosquitoes = formationTargets.map(target => ({
                x: titleBounds.left - 100 + Math.random() * (titleBounds.width + 200),
                y: titleBounds.top - 100 + Math.random() * (titleBounds.height + 200),
                targetX: target.x,
                targetY: target.y,
                color: target.color,
                size: 1.7 + Math.random() * 0.7,
                delay: Math.random() * 700,
                phase: Math.random() * Math.PI * 2,
                curve: (Math.random() * 2 - 1) * Math.min(
                    Math.hypot(target.x - (titleBounds.left + titleBounds.width / 2),
                        target.y - (titleBounds.top + titleBounds.height / 2)) * 0.12,
                    52
                )
            }));

            return formationMosquitoes.length > 0;
        }

        function beginFormation(startedAt = performance.now()) {
            if (!createFormationMosquitoes()) return;

            formationStartedAt = startedAt;
            nextFormationAt = startedAt + formationInterval;
            titleRevealed = false;
            formationIsActive = true;
            heroTitle.classList.remove("is-revealed");
            heroTitle.classList.add("is-forming");
        }

        function endFormation() {
            formationIsActive = false;
            formationMosquitoes = [];
            heroTitle.classList.remove("is-forming", "is-revealed");
        }

        function drawAmbientMosquitoes() {
            ambientMosquitoes.forEach(mosquito => {
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
        }

        function drawFormationMosquito(mosquito, elapsed) {
            const progress = Math.max(0, Math.min(1, (elapsed - mosquito.delay) / 4900));
            const easedProgress = progress * progress * progress
                * (progress * (progress * 6 - 15) + 10);
            const distanceX = mosquito.targetX - mosquito.x;
            const distanceY = mosquito.targetY - mosquito.y;
            const distance = Math.hypot(distanceX, distanceY) || 1;
            const controlX = (mosquito.x + mosquito.targetX) / 2
                - (distanceY / distance) * mosquito.curve;
            const controlY = (mosquito.y + mosquito.targetY) / 2
                + (distanceX / distance) * mosquito.curve;
            const remaining = 1 - easedProgress;
            const x = remaining * remaining * mosquito.x
                + 2 * remaining * easedProgress * controlX
                + easedProgress * easedProgress * mosquito.targetX
                + Math.sin(elapsed / 220 + mosquito.phase) * remaining * 1.5;
            const y = remaining * remaining * mosquito.y
                + 2 * remaining * easedProgress * controlY
                + easedProgress * easedProgress * mosquito.targetY
                + Math.cos(elapsed / 240 + mosquito.phase) * remaining * 1.5;
            const fadeIn = Math.min(1, Math.max(0, (elapsed - mosquito.delay) / 500));
            const fadeOut = Math.max(0, 1 - Math.max(0, elapsed - 5600) / 1800);
            const fade = fadeIn * fadeOut;
            const tangentX = remaining * (controlX - mosquito.x)
                + easedProgress * (mosquito.targetX - controlX);
            const tangentY = remaining * (controlY - mosquito.y)
                + easedProgress * (mosquito.targetY - controlY);
            const heading = Math.atan2(tangentY, tangentX);
            const wingBeat = Math.sin(elapsed / 45 + mosquito.phase) * 0.35;

            context.save();
            context.translate(x, y);
            context.rotate(heading);
            context.globalAlpha = fade * 0.9;
            context.fillStyle = mosquito.color;
            context.strokeStyle = mosquito.color;
            context.lineWidth = 0.55;
            context.beginPath();
            context.ellipse(0, 0, mosquito.size, mosquito.size * 0.34, 0, 0, Math.PI * 2);
            context.fill();
            context.beginPath();
            context.ellipse(-mosquito.size * 0.25, -mosquito.size * 0.7,
                mosquito.size * 0.45, mosquito.size * 0.95, -0.5 + wingBeat, 0, Math.PI * 2);
            context.ellipse(mosquito.size * 0.25, -mosquito.size * 0.7,
                mosquito.size * 0.45, mosquito.size * 0.95, 0.5 - wingBeat, 0, Math.PI * 2);
            context.globalAlpha = fade * 0.38;
            context.fill();
            context.globalAlpha = fade * 0.9;
            context.beginPath();
            context.moveTo(mosquito.size * 0.65, 0);
            context.lineTo(mosquito.size * 1.6, 0);
            context.moveTo(mosquito.size * 0.7, 0);
            context.lineTo(mosquito.size * 2.2, mosquito.size * 1.2);
            context.stroke();
            context.restore();
        }

        function animateMosquitoes(timestamp) {
            context.clearRect(0, 0, width, height);
            drawAmbientMosquitoes();

            if (formationIsActive) {
                const elapsed = timestamp - formationStartedAt;
                formationMosquitoes.forEach(mosquito => drawFormationMosquito(mosquito, elapsed));

                if (!titleRevealed && elapsed >= 5200) {
                    heroTitle.classList.add("is-revealed");
                    titleRevealed = true;
                }

                if (elapsed >= formationDuration) {
                    endFormation();
                }
            } else if (titleIsInView && timestamp >= nextFormationAt) {
                beginFormation(timestamp);
            }

            animationFrame = window.requestAnimationFrame(animateMosquitoes);
        }

        resizeCanvas();
        window.addEventListener("resize", () => {
            resizeCanvas();
            if (formationIsActive) {
                beginFormation();
            }
        });
        if ("IntersectionObserver" in window) {
            const titleObserver = new IntersectionObserver(entries => {
                const isInView = entries[0].isIntersecting;
                if (isInView === titleIsInView) return;

                titleIsInView = isInView;
                if (isInView) {
                    beginFormation();
                } else {
                    endFormation();
                    nextFormationAt = 0;
                }
            }, { threshold: 0.12 });
            titleObserver.observe(heroTitle);
        } else {
            titleIsInView = true;
            beginFormation();
        }
        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                window.cancelAnimationFrame(animationFrame);
                hiddenAt = performance.now();
            } else {
                if (hiddenAt !== null) {
                    const pausedDuration = performance.now() - hiddenAt;
                    if (formationIsActive) formationStartedAt += pausedDuration;
                    if (nextFormationAt) nextFormationAt += pausedDuration;
                    hiddenAt = null;
                }
                animationFrame = window.requestAnimationFrame(animateMosquitoes);
            }
        });
        animationFrame = window.requestAnimationFrame(animateMosquitoes);
    }
}