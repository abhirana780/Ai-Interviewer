(function(){
  const sessionsEl = document.getElementById("sessions");
  const detailsEl = document.getElementById("details");
  const refreshBtn = document.getElementById("refresh");

  async function getJSON(url){ const r = await fetch(url); return r.json(); }

  function fmtDate(ts){
    if(!ts) return "";
    try{ const d = new Date(ts*1000); return d.toLocaleString(); }catch(e){ return String(ts); }
  }

  function pill(text, kind){
    const span = document.createElement("span");
    span.className = `pill ${kind||""}`;
    span.textContent = text;
    return span;
  }

  function renderSessions(items){
    sessionsEl.innerHTML = "";
    const table = document.createElement("table");
    table.className = "sessions-table";
    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    ["Name","Email","Mobile","College","Track","Score","AI%","Actions"].forEach(h=>{ const th=document.createElement("th"); th.textContent=h; trh.appendChild(th); });
    thead.appendChild(trh);
    const tbody = document.createElement("tbody");
    (items||[]).forEach(s => {
      const tr = document.createElement("tr");
      
      const tdName = document.createElement("td");
      tdName.textContent = s.candidate_name || "N/A";
      
      const tdEmail = document.createElement("td");
      tdEmail.textContent = s.email || "N/A";
      
      const tdMobile = document.createElement("td");
      tdMobile.textContent = s.mobile_number || "N/A";
      
      const tdCollege = document.createElement("td");
      tdCollege.textContent = s.college_name || "N/A";
      
      const tdTrack = document.createElement("td");
      tdTrack.textContent = s.track || "N/A";
      
      const tdScore = document.createElement("td");
      const score = s.final_score || s.avg_score || 0;
      const scoreKind = score>=4?"good":(score>=3?"avg":"bad");
      tdScore.appendChild(pill(`${score}/5`, scoreKind));
      
      const tdOverall = document.createElement("td");
      const o = Number(s.overall||0);
      const kind = o>=75?"good":(o>=50?"avg":"bad");
      tdOverall.appendChild(pill(`${o}%`, kind));
      
      const tdAct = document.createElement("td");
      tdAct.style.display = "flex";
      tdAct.style.gap = "8px";
      
      const btnView = document.createElement("button");
      btnView.textContent = "View";
      btnView.style.fontSize = "12px";
      btnView.onclick = () => loadDetails(s.id);
      
      const btnEmail = document.createElement("button");
      btnEmail.textContent = "📧 Email";
      btnEmail.style.fontSize = "12px";
      btnEmail.style.background = "#0b5ed7";
      btnEmail.style.color = "white";
      btnEmail.onclick = () => sendEmail(s.id, s.email, s.candidate_name);
      
      tdAct.appendChild(btnView);
      tdAct.appendChild(btnEmail);
      
      tr.appendChild(tdName);
      tr.appendChild(tdEmail);
      tr.appendChild(tdMobile);
      tr.appendChild(tdCollege);
      tr.appendChild(tdTrack);
      tr.appendChild(tdScore);
      tr.appendChild(tdOverall);
      tr.appendChild(tdAct);
      tbody.appendChild(tr);
    });
    table.appendChild(thead);
    table.appendChild(tbody);
    sessionsEl.appendChild(table);
  }

  function renderDetails(data){
    const v = data.verification || {overall:0, pairs:[]};
    const ans = data.answers || [];
    const pairs = v.pairs || [];
    detailsEl.innerHTML = "";
    
    // Candidate Info Section
    const infoSection = document.createElement("div");
    infoSection.style.marginBottom = "20px";
    
    const infoHeader = document.createElement("div");
    infoHeader.style.display = "flex";
    infoHeader.style.justifyContent = "space-between";
    infoHeader.style.alignItems = "center";
    infoHeader.style.marginBottom = "10px";
    
    const infoTitle = document.createElement("h4");
    infoTitle.textContent = "Candidate Information";
    infoTitle.style.margin = "0";
    
    const emailBtn = document.createElement("button");
    emailBtn.textContent = "📧 Send Results Email";
    emailBtn.style.background = "#0b5ed7";
    emailBtn.style.color = "white";
    emailBtn.onclick = () => sendEmail(data.session_id, data.email, data.candidate_name);
    
    infoHeader.appendChild(infoTitle);
    infoHeader.appendChild(emailBtn);
    infoSection.appendChild(infoHeader);
    
    const infoGrid = document.createElement("div");
    infoGrid.className = "detail-grid";
    
    const fields = [
      ["Name", data.candidate_name || "N/A"],
      ["Email", data.email || "N/A"],
      ["Mobile", data.mobile_number || "N/A"],
      ["Qualification", data.qualification || "N/A"],
      ["College", data.college_name || "N/A"],
      ["Track", data.track || "N/A"],
      ["Interview Date", fmtDate(data.created_at)]
    ];
    
    fields.forEach(([label, value]) => {
      const labelDiv = document.createElement("div");
      labelDiv.className = "detail-label";
      labelDiv.textContent = label + ":";
      const valueDiv = document.createElement("div");
      valueDiv.className = "detail-value";
      valueDiv.textContent = value;
      infoGrid.appendChild(labelDiv);
      infoGrid.appendChild(valueDiv);
    });
    
    infoSection.appendChild(infoGrid);
    detailsEl.appendChild(infoSection);
    
    // Score Summary
    const head = document.createElement("div");
    head.className = "details-head";
    const title = document.createElement("div");
    title.className = "details-title";
    title.textContent = "Interview Performance";
    const o = Number(v.overall||0);
    const kind = o>=75?"good":(o>=50?"avg":"bad");
    const summary = pill(`AI Score: ${o}%`, kind);
    head.appendChild(title);
    head.appendChild(summary);
    detailsEl.appendChild(head);
    
    // Q&A Section with Videos
    const list = document.createElement("div");
    list.className = "pairs";
    for(let i=0;i<pairs.length;i++){
      const p = pairs[i];
      const a = ans[i]||{};
      const item = document.createElement("div");
      item.className = "pair";
      
      const qd = document.createElement("div");
      qd.className = "q";
      qd.textContent = `Q${i+1}: ${p.question||""}`;
      
      const ad = document.createElement("div");
      ad.className = "a";
      ad.textContent = `A${i+1}: ${p.answer||""}`;
      
      // Video player if media exists
      if (a.media_path) {
        const videoContainer = document.createElement("div");
        videoContainer.style.marginTop = "8px";
        
        const video = document.createElement("video");
        video.src = a.media_path;
        video.controls = true;
        video.style.width = "100%";
        video.style.maxWidth = "400px";
        video.style.borderRadius = "8px";
        video.style.border = "1px solid #e2e6ef";
        
        const videoLabel = document.createElement("div");
        videoLabel.textContent = "🎥 Video Answer:";
        videoLabel.style.fontSize = "12px";
        videoLabel.style.fontWeight = "600";
        videoLabel.style.marginBottom = "4px";
        videoLabel.style.color = "#666";
        
        videoContainer.appendChild(videoLabel);
        videoContainer.appendChild(video);
        ad.appendChild(videoContainer);
      }
      
      const kd = document.createElement("div");
      kd.className = "k";
      const ck = Number(p.correctness||0);
      const kk = ck>=75?"good":(ck>=50?"avg":"bad");
      kd.appendChild(pill(`${ck}%`, kk));
      
      const sd = document.createElement("div");
      sd.className = "s";
      sd.textContent = a.score!=null?`Score ${a.score}/5`:"";
      
      const fd = document.createElement("div");
      fd.className = "f";
      fd.textContent = a.feedback||"";
      
      item.appendChild(qd);
      item.appendChild(ad);
      item.appendChild(kd);
      item.appendChild(sd);
      item.appendChild(fd);
      list.appendChild(item);
    }
    detailsEl.appendChild(list);
  }

  async function sendEmail(sessionId, email, candidateName) {
    if (!email || email === "N/A") {
      alert("No email address for this candidate.");
      return;
    }
    
    if (!confirm(`Send results to ${candidateName}?\n${email}`)) {
      return;
    }
    
    // Show loading state
    const originalText = event.target.textContent;
    event.target.textContent = "Sending...";
    event.target.disabled = true;
    
    try {
      const res = await fetch("/admin/send-email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId })
      });
      
      const data = await res.json();
      
      if (data.email_sent) {
        alert(`✅ Email sent to ${email}!\nCheck inbox in 1-2 minutes.`);
      } else {
        // Concise error message with file path in console
        alert(`❌ Email not configured!

Quick fix:
1. Edit: .env file
2. Set: EMAIL_ENABLED=true
3. Add Gmail credentials
4. Restart server

See console for details.`);
        console.error("Email Setup Required:");
        console.log("1. Open: d:\\wipronix\\.env");
        console.log("2. Set: EMAIL_ENABLED=true");
        console.log("3. Add: SMTP_USERNAME, SMTP_PASSWORD");
        console.log("4. Restart: python run.py");
        console.log("\nFull guide: START_HERE_EMAIL_SETUP.txt");
        console.log("Error:", data.message);
        if (data.setup_instructions) {
          console.table(data.setup_instructions);
        }
      }
    } catch (e) {
      alert("❌ Error: " + e.message);
      console.error("Email error:", e);
    } finally {
      // Restore button state
      event.target.textContent = originalText;
      event.target.disabled = false;
    }
  }

  async function load(){
    const data = await getJSON("/admin/sessions");
    renderSessions(data.sessions || []);
  }

  async function loadDetails(id){
    const data = await getJSON(`/admin/session/${id}`);
    renderDetails(data);
  }

  refreshBtn.onclick = load;
  load();
})();
