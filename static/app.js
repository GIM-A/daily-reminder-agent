console.log("app.js 已加载");

// ==================== 元素引用 ====================
const authSection = document.getElementById("auth-section");
const chatSection = document.getElementById("chat-section");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const emailInput = document.getElementById("email");
const btnLogin = document.getElementById("btn-login");
const btnRegister = document.getElementById("btn-register");
const btnLogout = document.getElementById("btn-logout");
const btnSend = document.getElementById("btn-send");
const chatInput = document.getElementById("chat-input");
const messagesEl = document.getElementById("messages");
const authMessage = document.getElementById("auth-message");
const verifyBanner = document.getElementById("verify-banner");
const btnSendVerify = document.getElementById("btn-send-verify");

// ==================== 工具函数 ====================
function showAuthMessage(text, type = "") {
    authMessage.textContent = text;
    authMessage.className = type;
}

function showChat() {
    authSection.style.display = "none";
    chatSection.style.display = "block";
    refreshVerifyBanner();
}

function showAuth() {
    authSection.style.display = "block";
    chatSection.style.display = "none";
    messagesEl.innerHTML = "";
}

function getToken() {
    return localStorage.getItem("token");
}

// 根据 localStorage 里的 email_verified 决定是否显示提示条
function refreshVerifyBanner() {
    const verified = localStorage.getItem("email_verified") === "true";
    verifyBanner.style.display = verified ? "none" : "block";
}

// ==================== 登录 ====================
btnLogin.addEventListener("click", async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
        showAuthMessage("请填写用户名和密码", "error");
        return;
    }

    showAuthMessage("登录中...");

    try {
        const res = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json();

        if (data.error) {
            showAuthMessage(data.error, "error");
            return;
        }

        localStorage.setItem("token", data.access_token);
        localStorage.setItem("email", data.email || "");
        localStorage.setItem("email_verified", data.email_verified ? "true" : "false");

        showAuthMessage("登录成功！", "success");
        showChat();
    } catch (e) {
        showAuthMessage("网络错误：" + e.message, "error");
    }
});

// ==================== 注册 ====================
btnRegister.addEventListener("click", async () => {
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    const email = emailInput.value.trim();

    if (!username || !password || !email) {
        showAuthMessage("注册需要用户名、密码、邮箱", "error");
        return;
    }

    showAuthMessage("注册中...");

    try {
        const res = await fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password }),
        });
        const data = await res.json();

        if (data.error) {
            showAuthMessage(data.error, "error");
            return;
        }

        showAuthMessage("注册成功！现在可以登录了。", "success");
    } catch (e) {
        showAuthMessage("网络错误：" + e.message, "error");
    }
});

// ==================== 退出登录 ====================
btnLogout.addEventListener("click", () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("email_verified");
    showAuth();
    showAuthMessage("已退出登录");
});

// ==================== 发送验证邮件 ====================
btnSendVerify.addEventListener("click", async (e) => {
    e.preventDefault();

    const email = localStorage.getItem("email");
    if (!email) {
        alert("找不到邮箱信息，请重新登录");
        return;
    }

    btnSendVerify.textContent = "发送中...";

    try {
        const res = await fetch("/send-verify-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });
        const data = await res.json();

        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message || "验证邮件已发送，请查收");
        }
    } catch (e) {
        alert("网络错误：" + e.message);
    }

    btnSendVerify.textContent = "点此发送验证邮件";
});

// ==================== 发送消息 ====================
btnSend.addEventListener("click", async () => {
    const message = chatInput.value.trim();
    if (!message) return;

    appendMessage("user", message);
    chatInput.value = "";

    const token = getToken();
    if (!token) {
        appendMessage("bot", "登录状态已失效，请重新登录");
        showAuth();
        return;
    }

    appendMessage("bot", "思考中...");

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
            },
            body: JSON.stringify({ message }),
        });

        if (res.status === 401) {
            appendMessage("bot", "登录已过期，请重新登录");
            localStorage.removeItem("token");
            showAuth();
            return;
        }

        const data = await res.json();
        messagesEl.removeChild(messagesEl.lastChild);
        appendMessage("bot", data.reply || "（无回复）");
    } catch (e) {
        messagesEl.removeChild(messagesEl.lastChild);
        appendMessage("bot", "网络错误：" + e.message);
    }
});

// 回车发送
chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") btnSend.click();
});

function appendMessage(role, text) {
    const div = document.createElement("div");
    div.className = "message " + role;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ==================== 启动时检查登录状态 ====================
if (getToken()) {
    showChat();
} else {
    showAuth();
}