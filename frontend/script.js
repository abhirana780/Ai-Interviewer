const BACKEND = "http://localhost:7860";
let sessionId = null;

function addMsg(text, type) {
    const div = document.createElement("div");
    div.className = "msg " + type;
    div.textContent = text;
    document.getElementById("chat").appendChild(div);
}

document.getElementById("start").onclick = async () => {
    const role = document.getElementById("role").value;

    const res = await fetch(BACKEND + "/start", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({role})
    });

    const data = await res.json();
    sessionId = data.session_id;
    addMsg(data.question, "bot");
};

document.getElementById("send").onclick = async () => {
    const answer = document.getElementById("answer").value;
    addMsg(answer, "me");

    const res = await fetch(BACKEND + "/answer", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: sessionId, answer})
    });

    const data = await res.json();

    addMsg("Next: " + data.next_question, "bot");
    addMsg("Score: " + data.score + " — " + data.feedback, "bot");

    document.getElementById("answer").value = "";
};
