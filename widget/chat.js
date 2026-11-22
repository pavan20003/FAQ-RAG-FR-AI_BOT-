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
    :host { --faq-primary: ${color}; --faq-ink: #252b25; --faq-muted: #697168; --faq-line: #e5e0d6; color: var(--faq-ink); font: 14px/1.5 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    * { box-sizing: border-box; }
    button, input, textarea, select { font: inherit; }
    button { cursor: pointer; }
    button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible { outline: 3px solid #d8ac69; outline-offset: 2px; }
    .launcher { position: fixed; right: 26px; bottom: 24px; z-index: 2147483000; display: inline-flex; align-items: center; gap: 11px; min-height: 54px; border: 1px solid #ffffff44; border-radius: 15px; padding: 0 20px 0 14px; color: #fff; background: var(--faq-primary); font: inherit; font-size: 13px; font-weight: 750; box-shadow: 0 10px 28px #1b2d2350; transition: transform .18s ease, box-shadow .18s ease, background .18s ease; }
    .launcher::before { width: 27px; height: 27px; display: grid; place-items: center; border-radius: 9px; content: "✳"; color: var(--faq-primary); background: #f3ead9; font-size: 15px; }
    .launcher:hover { transform: translateY(-2px); background: #273a2e; box-shadow: 0 13px 32px #1b2d235c; }
    .panel { position: fixed; right: 26px; bottom: 91px; z-index: 2147483000; display: none; flex-direction: column; width: min(410px, calc(100vw - 30px)); height: min(640px, calc(100vh - 120px)); overflow: hidden; border: 1px solid #ffffff; border-radius: 20px; background: #faf9f5; box-shadow: 0 22px 70px #1b2d2340, 0 3px 12px #1b2d231a; }
    .panel.open { display: flex; animation: rise-in .2s ease-out both; }
    @keyframes rise-in { from { opacity: 0; transform: translateY(8px) scale(.985); } to { opacity: 1; transform: translateY(0) scale(1); } }
    .chat-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 79px; padding: 13px 16px; color: #fff; background: var(--faq-primary); }
    .identity { min-width: 0; display: flex; align-items: center; gap: 11px; }
    .avatar { width: 42px; height: 42px; flex: 0 0 auto; display: grid; place-items: center; border: 1px solid #ffffff40; border-radius: 13px; color: #26392d; background: #f1e5cd; font-size: 21px; }
    .heading { display: block; max-width: 180px; overflow: hidden; font-size: 13px; font-weight: 750; text-overflow: ellipsis; white-space: nowrap; }
    .availability { display: flex; align-items: center; gap: 6px; margin-top: 4px; color: #dfe9df; font-size: 10px; font-weight: 550; }
    .availability::before { width: 6px; height: 6px; border-radius: 50%; content: ""; background: #a9d39b; box-shadow: 0 0 0 3px #a9d39b25; }
    .header-actions { display: flex; align-items: center; gap: 8px; }
    .header-actions select { max-width: 95px; min-height: 34px; border: 1px solid #ffffff55; border-radius: 8px; padding: 0 5px; color: #fff; background: #ffffff16; font-size: 11px; }
    .header-actions option { color: #252b25; background: #fff; }
    .close { width: 32px; height: 32px; border: 1px solid #ffffff3d; border-radius: 9px; color: white; background: transparent; font-size: 21px; line-height: 1; transition: background .18s ease; }
    .close:hover { background: #ffffff20; }
    .messages { display: flex; flex: 1; flex-direction: column; gap: 11px; overflow-y: auto; padding: 18px 15px; background: linear-gradient(#faf9f5, #f8f7f2); }
    .message { max-width: 88%; padding: 11px 13px; border-radius: 14px; white-space: pre-wrap; overflow-wrap: anywhere; }
    .assistant { align-self: flex-start; border: 1px solid #ebe7de; border-bottom-left-radius: 5px; color: #343b34; background: #fff; box-shadow: 0 2px 5px #19251a08; }
    .user { align-self: flex-end; border-bottom-right-radius: 5px; color: white; background: var(--faq-primary); box-shadow: 0 4px 10px #233c2b1c; }
    .sources { margin: -3px 0 5px 2px; padding-left: 18px; color: var(--faq-muted); font-size: 11px; }
    .sources a { color: var(--faq-primary); font-weight: 650; text-decoration-thickness: 1px; text-underline-offset: 2px; }
    .composer { display: flex; align-items: center; gap: 8px; border-top: 1px solid var(--faq-line); padding: 12px; background: #fff; }
    input, textarea { width: 100%; min-width: 0; border: 1px solid #deded5; border-radius: 10px; padding: 10px 12px; color: var(--faq-ink); background: #fbfbf8; font: inherit; }
    input::placeholder, textarea::placeholder { color: #858b82; }
    .composer input { min-height: 43px; flex: 1; }
    .send, .handoff-submit { min-height: 42px; border: 0; border-radius: 10px; padding: 0 14px; color: white; background: var(--faq-primary); font-weight: 700; transition: background .18s ease; }
    .send:hover, .handoff-submit:hover { background: #273a2e; }
    .send:disabled, .handoff-submit:disabled { opacity: .55; cursor: wait; }
    .handoff { margin: 0 12px 12px; padding: 13px; border: 1px solid var(--faq-line); border-radius: 13px; background: #fff; }
    .handoff[hidden] { display: none; }
    .handoff p { margin: 0 0 8px; color: #505950; font-size: 12px; }
    .handoff label { display: block; margin: 8px 0 4px; color: #4c554c; font-size: 11px; font-weight: 700; }
    .handoff textarea { min-height: 70px; resize: vertical; }
    .handoff-submit { margin-top: 9px; }
    .status { min-height: 19px; margin: 0; padding: 0 14px 7px; color: var(--faq-muted); background: #fff; font-size: 11px; }
    @media (max-width: 480px) {
      .launcher { right: 15px; bottom: 15px; min-height: 50px; }
      .panel { right: 8px; bottom: 76px; width: calc(100vw - 16px); height: min(660px, calc(100dvh - 88px)); border-radius: 17px; }
      .chat-header { min-height: 72px; padding: 11px 12px; }
      .avatar { width: 38px; height: 38px; }
      .header-actions { gap: 6px; }
      .header-actions select { max-width: 84px; }
    }
    @media (prefers-reduced-motion: reduce) { .panel.open { animation: none; } *, *::before, *::after { transition-duration: .01ms !important; } }
  `;
  const launcher = document.createElement("button");
  launcher.className = "launcher";
  launcher.type = "button";
  launcher.textContent = copy[language].launcher;
  launcher.setAttribute("aria-label", `Ouvrir ${title}`);
  launcher.setAttribute("aria-controls", "faq-rag-chat-panel");
  launcher.setAttribute("aria-expanded", "false");
  const panel = document.createElement("section");
  panel.className = "panel";
  panel.id = "faq-rag-chat-panel";
  panel.setAttribute("aria-label", title);
  panel.setAttribute("role", "dialog");
  const header = document.createElement("header");
  header.className = "chat-header";
  const identity = document.createElement("div");
  identity.className = "identity";
  const avatar = document.createElement("span");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "✳";
  const headerCopy = document.createElement("div");
  const heading = document.createElement("span");
  heading.className = "heading";
  heading.textContent = title;
  const availability = document.createElement("span");
  availability.className = "availability";
  availability.textContent = language === "en" ? "Here to help" : "À votre écoute";
  headerCopy.append(heading, availability);
  identity.append(avatar, headerCopy);
  const headerActions = document.createElement("div");
  headerActions.className = "header-actions";
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
  headerActions.append(languageSelect, close);
  header.append(identity, headerActions);
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
    availability.textContent = language === "en" ? "Here to help" : "À votre écoute";
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

  function openPanel() {
    panel.classList.add("open");
    launcher.setAttribute("aria-expanded", "true");
    questionInput.focus();
  }
  function closePanel() {
    panel.classList.remove("open");
    launcher.setAttribute("aria-expanded", "false");
    launcher.focus();
  }
  launcher.addEventListener("click", openPanel);
  close.addEventListener("click", closePanel);
  window.addEventListener("faq-rag-open", openPanel);
  window.addEventListener("faq-rag-suggestion", event => {
    if (typeof event.detail !== "string" || !event.detail.trim()) return;
    questionInput.value = event.detail;
    openPanel();
  });
  panel.addEventListener("keydown", event => {
    if (event.key === "Escape") closePanel();
  });
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
