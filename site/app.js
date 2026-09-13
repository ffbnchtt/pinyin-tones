const languageToggle = document.querySelector('#language-toggle');
const html = document.documentElement;
const typingDemoText = document.querySelector('#typing-demo-text');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const typingFrames = [
  { text: '', delay: 450 },
  { text: 'n', delay: 140 },
  { text: 'ni', delay: 140 },
  { text: 'ni3', delay: 500 },
  { text: 'nǐ', delay: 450 },
  { text: 'nǐ ', delay: 140 },
  { text: 'nǐ h', delay: 140 },
  { text: 'nǐ ha', delay: 140 },
  { text: 'nǐ hao', delay: 140 },
  { text: 'nǐ hao3', delay: 700 },
  { text: 'nǐ hǎo', delay: 1800 },
];
let typingTimer;
let typingFrame = 0;

function runTypingDemo() {
  window.clearTimeout(typingTimer);
  if (reducedMotion.matches) {
    typingDemoText.textContent = 'nǐ hǎo';
    return;
  }

  const frame = typingFrames[typingFrame];
  typingDemoText.textContent = frame.text;
  typingFrame = (typingFrame + 1) % typingFrames.length;
  typingTimer = window.setTimeout(runTypingDemo, frame.delay);
}

function setLanguage(language) {
  html.lang = language;
  document.querySelectorAll('[data-es][data-en]').forEach((element) => {
    element.textContent = element.dataset[language];
  });
  languageToggle.textContent = language === 'es' ? 'EN' : 'ES';
  languageToggle.setAttribute('aria-label', language === 'es' ? 'Switch to English' : 'Cambiar a español');
  localStorage.setItem('pinyin-tones-language', language);
  updateRecommendation(language);
}

function updateRecommendation(language) {
  const userAgent = navigator.userAgent;
  const recommendation = document.querySelector('#os-recommendation');
  const button = document.querySelector('#recommended-download');
  const isMac = /Macintosh|Mac OS X/.test(userAgent);
  const isWindows = /Windows/.test(userAgent);
  const isLinux = /Linux/.test(userAgent);
  const messages = {
    windows: ['Detectamos Windows: descargá el ZIP portable.', 'Windows detected: download the portable ZIP.'],
    macos: ['Detectamos macOS: elegí Apple Silicon o Intel abajo.', 'macOS detected: choose Apple Silicon or Intel below.'],
    linux: ['Detectamos Linux: elegí DEB o AppImage abajo.', 'Linux detected: choose DEB or AppImage below.'],
    other: ['Elegí la descarga adecuada para tu sistema.', 'Choose the download for your operating system.'],
  };
  const platform = isWindows ? 'windows' : isMac ? 'macos' : isLinux ? 'linux' : 'other';
  recommendation.textContent = messages[platform][language === 'es' ? 0 : 1];
  if (platform !== 'other') {
    document.querySelector(`[data-platform="${platform}"]`).classList.add('detected');
  }
  button.href = '#descargar';
}

const storedLanguage = localStorage.getItem('pinyin-tones-language');
setLanguage(storedLanguage === 'en' ? 'en' : 'es');
languageToggle.addEventListener('click', () => setLanguage(html.lang === 'es' ? 'en' : 'es'));
reducedMotion.addEventListener?.('change', () => {
  typingFrame = 0;
  runTypingDemo();
});
runTypingDemo();
