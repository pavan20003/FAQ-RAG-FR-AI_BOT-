(() => {
  "use strict";

  const script = document.currentScript;
  if (!script || document.querySelector("faq-rag-widget")) return;

  const apiBase = new URL(script.dataset.apiUrl || window.location.origin, document.baseURI);
  if (!apiBase.pathname.endsWith("/")) apiBase.pathname += "/";
  const title = script.dataset.title || "Assistant FAQ";
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
  launcher.textContent = "Poser une question";
  launcher.setAttribute("aria-label", `Ouvrir ${title}`);
  const panel = document.createElement("section");
  panel.className = "panel";
  panel.setAttribute("aria-label", title);
  const header = document.createElement("header");
  const heading = document.createElement("span");
  heading.textContent = title;
  const close = document.createElement("button");
  close.className = "close";
  close.type = "button";
  close.textContent = "×";
  close.setAttribute("aria-label", "Fermer");
  header.append(heading, close);
  const messages = document.createElement("div");
  messages.className = "messages";
  messages.setAttribute("aria-live", "polite");
  const welcome = document.createElement("div");
  welcome.className = "message assistant";
  welcome.textContent = "Bonjour ! Posez-moi une question sur nos produits et services.";
  messages.append(welcome);
  const composer = document.createElement("form");
  composer.className = "composer";
  const questionInput = document.createElement("input");
  questionInput.type = "text";
  questionInput.maxLength = 500;
  questionInput.required = true;
  questionInput.placeholder = "Votre question…";
  questionInput.setAttribute("aria-label", "Votre question");
  const send = document.createElement("button");
  send.className = "send";
  send.type = "submit";
  send.textContent = "Envoyer";
  composer.append(questionInput, send);
  const status = document.createElement("p");
  status.className = "status";
  status.setAttribute("role", "status");
  const handoff = document.createElement("form");
  handoff.className = "handoff";
  handoff.hidden = true;
  const handoffIntro = document.createElement("p");
  handoffIntro.textContent = "Notre équipe peut vous répondre. Laissez votre adresse courriel et votre message.";
  const emailLabel = document.createElement("label");
  emailLabel.textContent = "Adresse courriel";
  const emailInput = document.createElement("input");
  emailInput.type = "email";
  emailInput.required = true;
  emailInput.autocomplete = "email";
  emailLabel.append(emailInput);
  const messageLabel = document.createElement("label");
  messageLabel.textContent = "Votre message";
  const messageInput = document.createElement("textarea");
  messageInput.required = true;
  messageInput.maxLength = 2000;
  messageLabel.append(messageInput);
  const handoffButton = document.createElement("button");
  handoffButton.className = "handoff-submit";
  handoffButton.type = "submit";
  handoffButton.textContent = "Contacter le support";
  handoff.append(handoffIntro, emailLabel, messageLabel, handoffButton);
  panel.append(header, messages, composer, status, handoff);
  shadow.append(style, launcher, panel);
  document.body.append(host);

  function endpoint(path) {
    return new URL(path, apiBase).toString();
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

  composer.addEventListener("submit", async event => {
    event.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;
    addMessage(question, "user");
    questionInput.value = "";
    send.disabled = true;
    status.textContent = "Réponse en cours…";
    try {
      const response = await fetch(endpoint("ask"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: sessionId })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      addMessage(result.answer, "assistant", result.sources || []);
      if (result.abstained) handoff.hidden = false;
      status.textContent = "";
    } catch (_error) {
      status.textContent = "Impossible de joindre l’assistant. Veuillez réessayer.";
    } finally {
      send.disabled = false;
      questionInput.focus();
    }
  });

  handoff.addEventListener("submit", async event => {
    event.preventDefault();
    handoffButton.disabled = true;
    status.textContent = "Envoi du message…";
    try {
      const response = await fetch(endpoint("handoff"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, email: emailInput.value.trim(), message: messageInput.value.trim() })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      status.textContent = "Votre message a été transmis à l’équipe.";
      messageInput.value = "";
    } catch (_error) {
      status.textContent = "Le transfert a échoué. Veuillez réessayer plus tard.";
    } finally {
      handoffButton.disabled = false;
    }
  });
})();
