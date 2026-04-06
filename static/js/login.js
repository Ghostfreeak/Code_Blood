document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('loginForm');
  const input = document.getElementById('username');
  const btn = document.getElementById('loginBtn');

  // If already logged in, go to chat
  const saved = localStorage.getItem('ct_username');
  if (saved) {
    window.location.href = '/chat';
    return;
  }

  input.focus();

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const name = input.value.trim();
    if (!name) {
      input.classList.add('error');
      showError('Please enter your name to continue.');
      return;
    }

    if (name.length < 2) {
      input.classList.add('error');
      showError('Name must be at least 2 characters.');
      return;
    }

    // Animate button
    btn.classList.add('loading');
    btn.querySelector('.btn-text').textContent = 'Starting...';

    setTimeout(() => {
      localStorage.setItem('ct_username', name);
      window.location.href = '/chat';
    }, 400);
  });

  input.addEventListener('input', () => {
    input.classList.remove('error');
    removeError();
  });

  function showError(msg) {
    removeError();
    const el = document.createElement('span');
    el.className = 'error-msg visible';
    el.textContent = msg;
    input.parentElement.parentElement.appendChild(el);
  }

  function removeError() {
    const existing = form.querySelector('.error-msg');
    if (existing) existing.remove();
  }

  // Suggestion: hit Enter anywhere
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.activeElement !== input) {
      input.focus();
    }
  });
});
