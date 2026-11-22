(() => {
  "use strict";

  const script = document.currentScript;
  if (!script || document.querySelector("faq-rag-widget")) return;

  const apiBase = new URL(script.dataset.apiUrl || window.location.origin, document.baseURI);
  if (!apiBase.pathname.endsWith("/")) apiBase.pathname += "/";
  const title = script.dataset.title || "Assistant FAQ";
  const copy = {
    fr: { launcher: "Poser une question", close: "Fermer", welcome: "Bonjour ! Posez-moi une question sur nos produits et services.", question: "Votre question", placeholder: "Votre question…", send: "Envoyer", loading: "Réponse en cours…", askError: "Impossible de joindre l’assistant. Veuillez réessayer.", handoffIntro: "Notre équipe peut vous répondre. Laissez votre adresse courriel et votre message.", email: "Adresse courriel", message: "Votre message", handoffButton: "Contacter le support", sending: "Envoi du message…", sent: "Votre message a été transmis à l’équipe.", handoffError: "Le transfert a échoué. Veuillez réessayer plus tard.", language: "Langue" },
    en: { launcher: "Ask a question", close: "Close", welcome: "Hello! Ask me about our products and services.", question: "Your question", placeholder: "Your question…", send: "Send", loading: "Preparing an answer…", askError: "The assistant could not be reached. Please try again.", handoffIntro: "Our team can help. Leave your email address and a message.", email: "Email address", message: "Your message", handoffButton: "Contact support", sending: "Sending your message…", sent: "Your message was sent to our team.", handoffError: "The message could not be sent. Please try again later.", language: "Language" }
  };
  let language = (script.dataset.language || document.documentElement.lang || "fr").toLowerCase().startsWith("en") ? "en" : "fr";
  const requestedColor = script.dataset.primaryColor || "#a64d2d";
  const color = window.CSS?.supports("color", requestedColor) ? requestedColor : "#a64d2d";
  const sessionKey = `faq-rag-session:${apiBase.origin}`;
  let sessionId = null;
  try { sessionId = sessionStorage.getItem(sessionKey); } catch (_error) { /* Storage can be disabled by browser settings. */ }
  if (!sessionId) {
    sessionId = window.crypto?.randomUUID?.() || `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    try { sessionStorage.setItem(sessionKey, sessionId); } catch (_error) { /* Keep this page session usable without storage. */ }
  }

  const host = document.createElement("faq-rag-widget");
  const shadow = host.attachShadow({ mode: "open" });
  const style = document.createElement("style");
  style.textContent = `
    :host { --faq-primary: ${color}; color: #241d19; font: 15px/1.45 system-ui, sans-serif; }
    * { box-sizing: border-box; }
    .launcher { position: fixed; right: 22px; bottom: 22px; z-index: 2147483000; border: 0; border-radius: 999px; background: var(--faq-primary); color: white; padding: 14px 20px; font: inherit; font-weight: 650; cursor: pointer; box-shadow: 0 5px 22px #0003; }
    .panel { position: fixed; right: 22px; bottom: 82px; z-index: 2147483000; display: none; flex-direction: column; width: min(390px, calc(100vw - 28px)); height: min(590px, calc(100vh - 120px)); overflow: hidden; border: 1px solid #e5d9d2; border-radius: 16px; background: #fffdfb; box-shadow: 0 12px 40px #0003; }
    .panel.open { display: flex; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; color: white; background: var(--faq-primary); font-weight: 700; }
    header select { max-width: 112px; border: 1px solid #ffffff88; border-radius: 8px; padding: 6px 8px; color: #241d19; background: #fff; font: inherit; font-size: 13px; }
    button { font: inherit; cursor: pointer; }
    .close { border: 0; color: white; background: transparent; font-size: 22px; line-height: 1; }
    .messages { display: flex; flex: 1; flex-direction: column; gap: 10px; overflow-y: auto; padding: 14px; }
    .message { max-width: 90%; padding: 10px 12px; border-radius: 12px; white-space: pre-wrap; overflow-wrap: anywhere; }
    .assistant { align-self: flex-start; background: #f3ece7; }
    .user { align-self: flex-end; color: white; background: var(--faq-primary); }
    .sources { margin: -4px 0 4px 4px; padding-left: 18px; color: #51443d; font-size: 13px; }
    .sources a { color: #76391f; }
    .composer { display: flex; gap: 8px; border-top: 1px solid #eadfd9; padding: 12px; }
    input, textarea { width: 100%; min-width: 0; border: 1px solid #d5c9c2; border-radius: 9px; padding: 10px; font: inherit; }
    .composer input { flex: 1; }
    .send, .handoff-submit { border: 0; border-radius: 9px; padding: 9px 13px; color: white; background: var(--faq-primary); font-weight: 650; }
    .send:disabled, .handoff-submit:disabled { opacity: .55; cursor: wait; }
    .handoff { margin: 0 12px 12px; padding: 12px; border: 1px solid #eadfd9; border-radius: 12px; background: #fff; }
    .handoff[hidden] { display: none; }
    .handoff label { display: block; margin: 7px 0 4px; font-size: 13px; }
    .handoff textarea { min-height: 70px; resize: vertical; }
    .handoff-submit { margin-top: 8px; }
    .status { min-height: 20px; margin: 0; padding: 0 12px 8px; color: #5d514b; font-size: 13px; }
    @media (max-width: 480px) { .launcher { right: 14px; bottom: 14px; } .panel { right: 8px; bottom: 72px; height: min(620px, calc(100vh - 92px)); width: calc(100vw - 16px); } }
  `;
  const launcher = document.createElement("button");
  launcher.className = "launcher";
  launcher.type = "button";
  launcher.textContent = copy[language].launcher;
  launcher.setAttribute("aria-label", `Ouvrir ${title}`);
  const panel = document.createElement("section");
  panel.className = "panel";
  panel.setAttribute("aria-label", title);
  const header = document.createElement("header");
  const heading = document.createElement("span");
  heading.textContent = title;
  const languageSelect = document.createElement("select");
  languageSelect.setAttribute("aria-label", copy[language].language);
  for (const [value, label] of [["fr", "Français"], ["en", "English"]]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    languageSelect.append(option);
  }
  languageSelect.value = language;
  const close = document.createElement("button");
  close.className = "close";
  close.type = "button";
  close.textContent = "×";
  close.setAttribute("aria-label", copy[language].close);
  header.append(heading, languageSelect, close);
  const messages = document.createElement("div");
  messages.className = "messages";
  messages.setAttribute("aria-live", "polite");
  const welcome = document.createElement("div");
  welcome.className = "message assistant";
  welcome.textContent = copy[language].welcome;
  messages.append(welcome);
  const composer = document.createElement("form");
  composer.className = "composer";
  const questionInput = document.createElement("input");
  questionInput.type = "text";
  questionInput.maxLength = 500;
  questionInput.required = true;
  questionInput.placeholder = copy[language].placeholder;
  questionInput.setAttribute("aria-label", copy[language].question);
  const send = document.createElement("button");
  send.className = "send";
  send.type = "submit";
  send.textContent = copy[language].send;
  composer.append(questionInput, send);
  const status = document.createElement("p");
  status.className = "status";
  status.setAttribute("role", "status");
  const handoff = document.createElement("form");
  handoff.className = "handoff";
  handoff.hidden = true;
  const handoffIntro = document.createElement("p");
  handoffIntro.textContent = copy[language].handoffIntro;
  const emailLabel = document.createElement("label");
  emailLabel.append(document.createTextNode(copy[language].email));
  const emailInput = document.createElement("input");
  emailInput.type = "email";
  emailInput.required = true;
  emailInput.autocomplete = "email";
  emailLabel.append(emailInput);
  const messageLabel = document.createElement("label");
  messageLabel.append(document.createTextNode(copy[language].message));
  const messageInput = document.createElement("textarea");
  messageInput.required = true;
  messageInput.maxLength = 2000;
  messageLabel.append(messageInput);
  const handoffButton = document.createElement("button");
  handoffButton.className = "handoff-submit";
  handoffButton.type = "submit";
  handoffButton.textContent = copy[language].handoffButton;
  handoff.append(handoffIntro, emailLabel, messageLabel, handoffButton);
  panel.append(header, messages, composer, status, handoff);
  shadow.append(style, launcher, panel);
  document.body.append(host);

  function endpoint(path) {
    return new URL(path, apiBase).toString();
  }

  function setLanguage(nextLanguage, notifyPage = false) {
    language = nextLanguage === "en" ? "en" : "fr";
    const text = copy[language];
    languageSelect.value = language;
    languageSelect.setAttribute("aria-label", text.language);
    launcher.textContent = text.launcher;
    launcher.setAttribute("aria-label", `${language === "en" ? "Open" : "Ouvrir"} ${title}`);
    close.setAttribute("aria-label", text.close);
    welcome.textContent = text.welcome;
    questionInput.placeholder = text.placeholder;
    questionInput.setAttribute("aria-label", text.question);
    send.textContent = text.send;
    handoffIntro.textContent = text.handoffIntro;
    emailLabel.firstChild.textContent = text.email;
    messageLabel.firstChild.textContent = text.message;
    handoffButton.textContent = text.handoffButton;
    if (notifyPage) window.dispatchEvent(new CustomEvent("faq-rag-language", { detail: language }));
  }

  function addMessage(text, kind, sources = []) {
    const bubble = document.createElement("div");
    bubble.className = `message ${kind}`;
    bubble.textContent = text;
    messages.append(bubble);
    if (sources.length) {
      const list = document.createElement("ul");
      list.className = "sources";
      for (const source of sources) {
        const item = document.createElement("li");
        const link = document.createElement("a");
        const path = String(source.path || "");
        const safePath = path.split("/").filter(Boolean);
        link.textContent = `${source.title || path}${source.page ? ` — p. ${source.page}` : ""}`;
        if (safePath.length && safePath.every(part => part !== "." && part !== "..")) {
          const encoded = safePath.map(part => encodeURIComponent(part)).join("/");
          link.href = new URL(`demo-data/${encoded}`, apiBase).toString();
          link.target = "_blank";
          link.rel = "noopener noreferrer";
        } else {
          link.removeAttribute("href");
        }
        item.append(link);
        list.append(item);
      }
      messages.append(list);
    }
    messages.scrollTop = messages.scrollHeight;
  }

  launcher.addEventListener("click", () => {
    panel.classList.add("open");
    questionInput.focus();
  });
  close.addEventListener("click", () => panel.classList.remove("open"));
  languageSelect.addEventListener("change", () => setLanguage(languageSelect.value, true));
  window.addEventListener("faq-rag-language", event => {
    if (event.detail === "en" || event.detail === "fr") setLanguage(event.detail);
  });
  setLanguage(language);

  composer.addEventListener("submit", async event => {
    event.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;
    addMessage(question, "user");
    questionInput.value = "";
    send.disabled = true;
    status.textContent = copy[language].loading;
    try {
      const response = await fetch(endpoint("ask"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: sessionId, language })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      addMessage(result.answer, "assistant", result.sources || []);
      if (result.abstained) handoff.hidden = false;
      status.textContent = "";
    } catch (_error) {
      status.textContent = copy[language].askError;
    } finally {
      send.disabled = false;
      questionInput.focus();
    }
  });

  handoff.addEventListener("submit", async event => {
    event.preventDefault();
    handoffButton.disabled = true;
    status.textContent = copy[language].sending;
    try {
      const response = await fetch(endpoint("handoff"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, email: emailInput.value.trim(), message: messageInput.value.trim() })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      status.textContent = copy[language].sent;
      messageInput.value = "";
    } catch (_error) {
      status.textContent = copy[language].handoffError;
    } finally {
      handoffButton.disabled = false;
    }
  });
})();
