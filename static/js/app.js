// SignBridge AI - shared front-end helpers

const SignBridge = {
  // Simple local identity for the demo (no login system needed for MVP)
  getStudentName() {
    let name = localStorage.getItem('sb_student_name');
    if (!name) {
      name = 'Guest';
      localStorage.setItem('sb_student_name', name);
    }
    return name;
  },
  setStudentName(name) {
    localStorage.setItem('sb_student_name', name || 'Guest');
  },

  async post(url, body) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return res.json();
  },

  async get(url) {
    const res = await fetch(url);
    return res.json();
  },

  // Renders a sign sequence (array of {type, word, gu, image, letters}) into a container
  renderSignSequence(sequence, container) {
    container.innerHTML = '';
    sequence.forEach(item => {
      const card = document.createElement('div');
      card.className = 'sign-card fade-in';
      if (item.type === 'sign') {
        card.innerHTML = `
          <img src="${item.image}" alt="ISL sign for ${item.word}" loading="lazy">
          <div class="word">${item.word}</div>
          <div class="gu">Gujarati: ${item.gu}</div>
        `;
      } else {
        card.classList.add('fingerspell');
        const letters = item.letters.map(l => `<span class="letter-chip">${l}</span>`).join('');
        card.innerHTML = `
          <div style="font-size:2rem; padding:20px 0 4px;">✋</div>
          <div class="word">${item.word}</div>
          <div class="letters">${letters}</div>
        `;
      }
      container.appendChild(card);
    });
  },
};

function speakWelcome() {
  if (!('speechSynthesis' in window)) return false;
  window.speechSynthesis.cancel();
  const welcome = new SpeechSynthesisUtterance('Hello, welcome to the classroom.');
  welcome.rate = 0.92;
  welcome.pitch = 1.05;
  window.speechSynthesis.speak(welcome);
  return true;
}

document.addEventListener('DOMContentLoaded', () => {
  const welcomeVoice = document.getElementById('welcomeVoice');
  const playWelcome = document.getElementById('playWelcome');
  const closeWelcome = document.getElementById('closeWelcome');
  if (!welcomeVoice || !playWelcome || !closeWelcome) return;
  playWelcome.addEventListener('click', () => {
    if (speakWelcome()) {
      playWelcome.textContent = 'Playing...';
      window.setTimeout(() => { playWelcome.textContent = 'Play welcome'; }, 1800);
    }
  });
  closeWelcome.addEventListener('click', () => welcomeVoice.remove());
  window.setTimeout(() => { speakWelcome(); }, 450);
});

