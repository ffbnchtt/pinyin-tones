const languageToggle = document.querySelector('#language-toggle');
const html = document.documentElement;

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
