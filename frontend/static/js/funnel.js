(function(){
  const trackSel = document.getElementById("track");
  const startBtn = document.getElementById("funnelStart");

  const stepResume = document.getElementById("stepResume");
  const resumeFile = document.getElementById("resumeFile");
  const resumeText = document.getElementById("resumeText");
  const uploadResumeBtn = document.getElementById("uploadResume");
  const atsResult = document.getElementById("atsResult");

  const stepAssessment = document.getElementById("stepAssessment");
  const assessmentPrompt = document.getElementById("assessmentPrompt");
  const assessmentCode = document.getElementById("assessmentCode");
  const assessmentStartBtn = document.getElementById("assessmentStart");
  const assessmentSubmitBtn = document.getElementById("assessmentSubmit");
  const assessmentResult = document.getElementById("assessmentResult");

  const stepInterview = document.getElementById("stepInterview");

  const stepSchedule = document.getElementById("stepSchedule");
  const slotInput = document.getElementById("slot");
  const noteInput = document.getElementById("note");
  const bookSlotBtn = document.getElementById("bookSlot");
  const scheduleResult = document.getElementById("scheduleResult");

  const stepOffer = document.getElementById("stepOffer");
  const candidateNameInput = document.getElementById("candidateName");
  const offerTitleInput = document.getElementById("offerTitle");
  const generateOfferBtn = document.getElementById("generateOffer");
  const offerBody = document.getElementById("offerBody");

  const stepLMS = document.getElementById("stepLMS");
  const courseNameInput = document.getElementById("courseName");
  const enrollLMSBtn = document.getElementById("enrollLMS");
  const lmsResult = document.getElementById("lmsResult");

  const stepLabs = document.getElementById("stepLabs");
  const labPrompt = document.getElementById("labPrompt");
  const labCode = document.getElementById("labCode");
  const labStartBtn = document.getElementById("labStart");
  const labSubmitBtn = document.getElementById("labSubmit");
  const labResult = document.getElementById("labResult");

  const state = {
    funnelId: null,
    track: "General",
    thresholds: { ats: 60, assessment: 70 },
    problemKey: null,
    labKey: null
  };

  function show(el){ el && (el.style.display = "block"); }
  function hide(el){ el && (el.style.display = "none"); }
  function setEnabled(el, yes){ if(el) el.disabled = !yes; }
  function info(el, text){ if(el) el.textContent = text || ""; }

  function resetFlow(){
    hide(stepResume); hide(stepAssessment); hide(stepInterview); hide(stepSchedule);
    hide(stepOffer); hide(stepLMS); hide(stepLabs);
    info(atsResult, ""); info(assessmentResult, ""); info(scheduleResult, "");
    offerBody.textContent = ""; info(lmsResult, ""); info(labResult, "");
    assessmentPrompt.textContent = ""; labPrompt.textContent = "";
    assessmentCode.value = ""; labCode.value = ""; resumeText.value = "";
    resumeFile.value = "";
    setEnabled(assessmentSubmitBtn, false); setEnabled(labSubmitBtn, false);
  }

  async function postJSON(url, obj){
    const res = await fetch(url, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(obj||{}) });
    return res.json();
  }

  startBtn.onclick = async () => {
    resetFlow();
    state.track = trackSel.value || "General";
    const data = await postJSON("/funnel/start", { track: state.track });
    state.funnelId = data.funnel_id;
    state.thresholds = data.thresholds || state.thresholds;
    show(stepResume);
  };

  uploadResumeBtn.onclick = async () => {
    if(!state.funnelId){ alert("Start the funnel first."); return; }
    const fd = new FormData();
    fd.append("funnel_id", state.funnelId);
    const file = resumeFile.files && resumeFile.files[0];
    if(file) fd.append("resume", file, file.name);
    let uploaded = null;
    try{
      const res = await fetch("/resume/upload", { method: "POST", body: fd });
      uploaded = await res.json();
    }catch(e){ info(atsResult, "Upload failed."); return; }

    const text = (resumeText.value || "").trim();
    const ats = await postJSON("/ats/score", { funnel_id: state.funnelId, track: state.track, text });
    const b = ats.breakdown || {};
    const matched = (b.matched_keywords || []).join(", ");
    const missing = (b.missing_keywords || []).join(", ");
    const fmt = b.formatting || {};
    const sections = Array.isArray(fmt.sections) ? fmt.sections.join(", ") : "";
    const contact = [fmt.contact_email ? "email" : null, fmt.contact_phone ? "phone" : null].filter(Boolean).join(", ");
    const pass = !!ats.pass;
    info(atsResult, `ATS Score: ${ats.score} — ${pass ? "PASS" : "FAIL"}\n${ats.details}\nMatched: ${matched}\nMissing: ${missing}\nSections: ${sections}\nContact: ${contact || "none"}`);
    if(pass){ show(stepAssessment); setEnabled(assessmentStartBtn, true); }
  };

  assessmentStartBtn.onclick = async () => {
    if(!state.funnelId){ alert("Start the funnel first."); return; }
    const data = await postJSON("/assessment/start", { funnel_id: state.funnelId, track: state.track });
    state.problemKey = data.problem_key;
    assessmentPrompt.textContent = data.prompt || "";
    setEnabled(assessmentSubmitBtn, true);
  };

  assessmentSubmitBtn.onclick = async () => {
    if(!state.funnelId || !state.problemKey){ alert("Get the problem first."); return; }
    const code = assessmentCode.value || "";
    const res = await postJSON("/assessment/submit", { funnel_id: state.funnelId, problem_key: state.problemKey, code });
    const pass = !!res.pass;
    info(assessmentResult, `Assessment Score: ${res.score} — ${res.feedback} — ${pass ? "PASS" : "FAIL"}`);
    if(pass){ show(stepInterview); show(stepSchedule); }
  };

  bookSlotBtn.onclick = async () => {
    if(!state.funnelId){ alert("Start the funnel first."); return; }
    const slot = (slotInput.value || "").trim();
    const note = (noteInput.value || "").trim();
    const data = await postJSON("/schedule/book", { funnel_id: state.funnelId, slot, note });
    if(data.error){ info(scheduleResult, `Error: ${data.error}`); return; }
    info(scheduleResult, `Scheduled: ${data.slot}`);
    show(stepOffer);
  };

  generateOfferBtn.onclick = async () => {
    if(!state.funnelId){ alert("Start the funnel first."); return; }
    const title = offerTitleInput.value || "Offer";
    const name = (candidateNameInput.value || "").trim();
    const data = await postJSON("/offer/generate", { funnel_id: state.funnelId, title, name });
    offerBody.textContent = data.body || "";
    show(stepLMS);
  };

  enrollLMSBtn.onclick = async () => {
    if(!state.funnelId){ alert("Start the funnel first."); return; }
    const course_name = courseNameInput.value || "Onboarding";
    const data = await postJSON("/lms/enroll", { funnel_id: state.funnelId, course_name });
    info(lmsResult, data.message || "Enrolled.");
    show(stepLabs);
  };

  labStartBtn.onclick = async () => {
    if(!state.funnelId){ alert("Start the funnel first."); return; }
    const data = await postJSON("/lab/start", { funnel_id: state.funnelId });
    state.labKey = data.lab_key;
    labPrompt.textContent = data.prompt || "";
    setEnabled(labSubmitBtn, true);
  };

  labSubmitBtn.onclick = async () => {
    if(!state.funnelId || !state.labKey){ alert("Get the lab first."); return; }
    const code = labCode.value || "";
    const data = await postJSON("/lab/submit", { funnel_id: state.funnelId, lab_key: state.labKey, code });
    info(labResult, `Lab Score: ${data.score} — ${data.feedback} — ${data.pass ? "PASS" : "FAIL"}`);
  };
})();