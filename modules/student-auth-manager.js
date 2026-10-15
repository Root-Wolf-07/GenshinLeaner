/**
 * Student Authentication & Personal Dashboard Manager
 * Genshin Cognitive Academy • Comprehensive Identity & Account Controller
 *
 * Implements:
 * - Email and Phone number login switching
 * - Client-side validation & normalization
 * - Password policy verification & visibility toggle
 * - Email / SMS OTP code entry & resend cooldown timer
 * - Single-use password reset flow
 * - 1-Click Copy Student ID to clipboard with tooltip feedback
 * - Personal Student Dashboard loading & data isolation
 * - Seamless integration with 3D character tutor switching
 */

export class StudentAuthManager {
  constructor(options = {}) {
    this.apiBaseUrl = options.apiBaseUrl || '';
    this.currentUser = null;
    this.authToken = localStorage.getItem('student_auth_token') || null;
    this.resendTimer = null;
    this.resendCountdown = 60;
    this.pendingVerificationIdentifier = null;
    this.pendingVerificationChannel = 'email';

    this.initElements();
    this.attachEventListeners();
    this.checkInitialSession();
  }

  initElements() {
    // Top Nav Controls
    this.authBtn = document.getElementById('auth-account-btn');
    this.authPillAvatar = document.getElementById('auth-pill-avatar');
    this.authPillLabel = document.getElementById('auth-pill-label');
    this.authPillIdBadge = document.getElementById('auth-pill-id-badge');

    // Main Modal & Containers
    this.modal = document.getElementById('student-auth-modal');
    this.closeModalBtn = document.getElementById('close-auth-modal-btn');
    this.views = {
      login: document.getElementById('auth-view-login'),
      register: document.getElementById('auth-view-register'),
      verify: document.getElementById('auth-view-verify'),
      forgot: document.getElementById('auth-view-forgot'),
      reset: document.getElementById('auth-view-reset'),
      dashboard: document.getElementById('auth-view-dashboard'),
    };

    // Notification banners
    this.errorBanner = document.getElementById('auth-error-banner');
    this.successBanner = document.getElementById('auth-success-banner');

    // Login Form Elements
    this.loginForm = document.getElementById('auth-login-form');
    this.loginTypeEmailBtn = document.getElementById('login-type-email-btn');
    this.loginTypePhoneBtn = document.getElementById('login-type-phone-btn');
    this.loginIdentifierInput = document.getElementById('login-identifier-input');
    this.loginIdentifierLabel = document.getElementById('login-identifier-label');
    this.loginPasswordInput = document.getElementById('login-password-input');
    this.loginPasswordToggle = document.getElementById('login-password-toggle');
    this.loginRememberMe = document.getElementById('login-remember-me');
    this.loginSubmitBtn = document.getElementById('login-submit-btn');

    // Register Form Elements
    this.registerForm = document.getElementById('auth-register-form');
    this.regTypeEmailBtn = document.getElementById('reg-type-email-btn');
    this.regTypePhoneBtn = document.getElementById('reg-type-phone-btn');
    this.regFullNameInput = document.getElementById('reg-fullname-input');
    this.regIdentifierInput = document.getElementById('reg-identifier-input');
    this.regIdentifierLabel = document.getElementById('reg-identifier-label');
    this.regPasswordInput = document.getElementById('reg-password-input');
    this.regPasswordToggle = document.getElementById('reg-password-toggle');
    this.regConfirmPasswordInput = document.getElementById('reg-confirm-password-input');
    this.regConfirmPasswordToggle = document.getElementById('reg-confirm-password-toggle');
    this.regTermsCheckbox = document.getElementById('reg-terms-checkbox');
    this.regSubmitBtn = document.getElementById('reg-submit-btn');

    // Verification Elements
    this.verifyForm = document.getElementById('auth-verify-form');
    this.verifyTargetLabel = document.getElementById('verify-target-label');
    this.verifyCodeInput = document.getElementById('verify-code-input');
    this.verifySubmitBtn = document.getElementById('verify-submit-btn');
    this.verifyResendBtn = document.getElementById('verify-resend-btn');
    this.verifyDevHint = document.getElementById('verify-dev-hint');

    // Forgot Password Elements
    this.forgotForm = document.getElementById('auth-forgot-form');
    this.forgotIdentifierInput = document.getElementById('forgot-identifier-input');
    this.forgotSubmitBtn = document.getElementById('forgot-submit-btn');

    // Reset Password Elements
    this.resetForm = document.getElementById('auth-reset-form');
    this.resetIdentifierInput = document.getElementById('reset-identifier-input');
    this.resetCodeInput = document.getElementById('reset-code-input');
    this.resetPasswordInput = document.getElementById('reset-password-input');
    this.resetPasswordToggle = document.getElementById('reset-password-toggle');
    this.resetConfirmPasswordInput = document.getElementById('reset-confirm-password-input');
    this.resetSubmitBtn = document.getElementById('reset-submit-btn');

    // Dashboard Elements
    this.dashFullName = document.getElementById('dash-fullname');
    this.dashStudentId = document.getElementById('dash-studentid');
    this.dashCopyIdBtn = document.getElementById('dash-copy-id-btn');
    this.dashContact = document.getElementById('dash-contact');
    this.dashLevelBadge = document.getElementById('dash-level-badge');
    this.dashDocsCount = document.getElementById('dash-docs-count');
    this.dashMaterialsCount = document.getElementById('dash-materials-count');
    this.dashQuizzesCount = document.getElementById('dash-quizzes-count');
    this.dashAvgScore = document.getElementById('dash-avg-score');
    this.dashTutorsGrid = document.getElementById('dash-tutors-grid');
    this.dashWeakTopicsList = document.getElementById('dash-weak-topics-list');
    this.dashRecentActivitiesList = document.getElementById('dash-recent-activities-list');
    this.dashLogoutBtn = document.getElementById('dash-logout-btn');
  }

  attachEventListeners() {
    // Open Modal
    if (this.authBtn) {
      this.authBtn.addEventListener('click', () => {
        if (this.currentUser) {
          this.showDashboard();
        } else {
          this.switchView('login');
        }
        this.openModal();
      });
    }

    // Close Modal
    if (this.closeModalBtn) {
      this.closeModalBtn.addEventListener('click', () => this.closeModal());
    }
    if (this.modal) {
      this.modal.addEventListener('click', (e) => {
        if (e.target === this.modal) this.closeModal();
      });
    }
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.modal && !this.modal.classList.contains('hidden')) {
        this.closeModal();
      }
    });

    // View Navigation Links
    document.querySelectorAll('[data-auth-target]').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const target = el.getAttribute('data-auth-target');
        this.switchView(target);
      });
    });

    // Login Form Switchers (Email vs Phone)
    if (this.loginTypeEmailBtn && this.loginTypePhoneBtn) {
      this.loginTypeEmailBtn.addEventListener('click', () => this.setLoginMethod('email'));
      this.loginTypePhoneBtn.addEventListener('click', () => this.setLoginMethod('phone'));
    }

    // Register Form Switchers (Email vs Phone)
    if (this.regTypeEmailBtn && this.regTypePhoneBtn) {
      this.regTypeEmailBtn.addEventListener('click', () => this.setRegisterMethod('email'));
      this.regTypePhoneBtn.addEventListener('click', () => this.setRegisterMethod('phone'));
    }

    // Password Visibility Toggles
    this.setupPasswordToggle(this.loginPasswordInput, this.loginPasswordToggle);
    this.setupPasswordToggle(this.regPasswordInput, this.regPasswordToggle);
    this.setupPasswordToggle(this.regConfirmPasswordInput, this.regConfirmPasswordToggle);
    this.setupPasswordToggle(this.resetPasswordInput, this.resetPasswordToggle);

    // Form Submissions
    if (this.loginForm) this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
    if (this.registerForm) this.registerForm.addEventListener('submit', (e) => this.handleRegister(e));
    if (this.verifyForm) this.verifyForm.addEventListener('submit', (e) => this.handleVerify(e));
    if (this.verifyResendBtn) this.verifyResendBtn.addEventListener('click', () => this.handleResendCode());
    if (this.forgotForm) this.forgotForm.addEventListener('submit', (e) => this.handleForgotPassword(e));
    if (this.resetForm) this.resetForm.addEventListener('submit', (e) => this.handleResetPassword(e));
    if (this.dashLogoutBtn) this.dashLogoutBtn.addEventListener('click', () => this.handleLogout());

    // 1-Click Copy Student ID
    if (this.dashCopyIdBtn) {
      this.dashCopyIdBtn.addEventListener('click', () => this.copyStudentId());
    }
  }

  setupPasswordToggle(input, btn) {
    if (!input || !btn) return;
    btn.addEventListener('click', () => {
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      btn.textContent = isPassword ? '👁️' : '🔒';
      btn.title = isPassword ? 'Hide password' : 'Show password';
    });
  }

  openModal() {
    if (this.modal) {
      this.modal.classList.remove('hidden');
      document.body.classList.add('overflow-hidden');
    }
    this.clearAlerts();
  }

  closeModal() {
    if (this.modal) {
      this.modal.classList.add('hidden');
      document.body.classList.remove('overflow-hidden');
    }
  }

  switchView(viewName) {
    this.clearAlerts();
    Object.keys(this.views).forEach(key => {
      const el = this.views[key];
      if (el) {
        if (key === viewName) {
          el.classList.remove('hidden');
        } else {
          el.classList.add('hidden');
        }
      }
    });

    if (viewName === 'dashboard') {
      this.loadDashboardData();
    }
  }

  setLoginMethod(type) {
    if (type === 'email') {
      this.loginTypeEmailBtn.classList.add('bg-amber-500/20', 'border-amber-400', 'text-amber-200');
      this.loginTypeEmailBtn.classList.remove('bg-slate-800/40', 'border-slate-700', 'text-slate-400');
      this.loginTypePhoneBtn.classList.remove('bg-amber-500/20', 'border-amber-400', 'text-amber-200');
      this.loginTypePhoneBtn.classList.add('bg-slate-800/40', 'border-slate-700', 'text-slate-400');
      this.loginIdentifierLabel.textContent = 'Student Email Address';
      this.loginIdentifierInput.placeholder = 'e.g. lumine@teyvat.org';
      this.loginIdentifierInput.type = 'email';
    } else {
      this.loginTypePhoneBtn.classList.add('bg-amber-500/20', 'border-amber-400', 'text-amber-200');
      this.loginTypePhoneBtn.classList.remove('bg-slate-800/40', 'border-slate-700', 'text-slate-400');
      this.loginTypeEmailBtn.classList.remove('bg-amber-500/20', 'border-amber-400', 'text-amber-200');
      this.loginTypeEmailBtn.classList.add('bg-slate-800/40', 'border-slate-700', 'text-slate-400');
      this.loginIdentifierLabel.textContent = 'Registered Phone Number';
      this.loginIdentifierInput.placeholder = 'e.g. +1 555-234-5678';
      this.loginIdentifierInput.type = 'tel';
    }
  }

  setRegisterMethod(type) {
    if (type === 'email') {
      this.regTypeEmailBtn.classList.add('bg-amber-500/20', 'border-amber-400', 'text-amber-200');
      this.regTypeEmailBtn.classList.remove('bg-slate-800/40', 'border-slate-700', 'text-slate-400');
      this.regTypePhoneBtn.classList.remove('bg-amber-500/20', 'border-amber-400', 'text-amber-200');
      this.regTypePhoneBtn.classList.add('bg-slate-800/40', 'border-slate-700', 'text-slate-400');
      this.regIdentifierLabel.textContent = 'Email Address (Verification required)';
      this.regIdentifierInput.placeholder = 'student@university.edu';
      this.regIdentifierInput.type = 'email';
    } else {
      this.regTypePhoneBtn.classList.add('bg-amber-500/20', 'border-amber-400', 'text-amber-200');
      this.regTypePhoneBtn.classList.remove('bg-slate-800/40', 'border-slate-700', 'text-slate-400');
      this.regTypeEmailBtn.classList.remove('bg-amber-500/20', 'border-amber-400', 'text-amber-200');
      this.regTypeEmailBtn.classList.add('bg-slate-800/40', 'border-slate-700', 'text-slate-400');
      this.regIdentifierLabel.textContent = 'Phone Number (SMS OTP required)';
      this.regIdentifierInput.placeholder = '+1 555-123-4567';
      this.regIdentifierInput.type = 'tel';
    }
  }

  showError(msg) {
    if (this.errorBanner) {
      this.errorBanner.textContent = msg;
      this.errorBanner.classList.remove('hidden');
    }
    if (this.successBanner) this.successBanner.classList.add('hidden');
  }

  showSuccess(msg) {
    if (this.successBanner) {
      this.successBanner.textContent = msg;
      this.successBanner.classList.remove('hidden');
    }
    if (this.errorBanner) this.errorBanner.classList.add('hidden');
  }

  clearAlerts() {
    if (this.errorBanner) this.errorBanner.classList.add('hidden');
    if (this.successBanner) this.successBanner.classList.add('hidden');
  }

  // --- Check Initial Authentication on Load ---
  async checkInitialSession() {
    if (!this.authToken) {
      this.updateTopBar(null);
      return;
    }

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/v1/auth/me`, {
        headers: { 'Authorization': `Bearer ${this.authToken}` },
        credentials: 'include'
      });
      if (res.ok) {
        const user = await res.json();
        this.setCurrentUser(user, this.authToken);
      } else {
        // Token expired or revoked
        this.clearSession();
      }
    } catch (e) {
      console.warn('Session verification error:', e);
    }
  }

  setCurrentUser(user, token) {
    this.currentUser = user;
    this.authToken = token;
    if (token) localStorage.setItem('student_auth_token', token);
    this.updateTopBar(user);
  }

  clearSession() {
    this.currentUser = null;
    this.authToken = null;
    localStorage.removeItem('student_auth_token');
    this.updateTopBar(null);
  }

  updateTopBar(user) {
    if (user && this.authBtn) {
      if (this.authPillAvatar) {
        const initials = (user.full_name || user.username || 'TR')
          .split(' ')
          .map(n => n[0])
          .join('')
          .toUpperCase()
          .slice(0, 2);
        this.authPillAvatar.textContent = initials;
      }
      if (this.authPillLabel) {
        this.authPillLabel.textContent = user.full_name || user.username;
      }
      if (this.authPillIdBadge) {
        this.authPillIdBadge.textContent = user.student_id;
        this.authPillIdBadge.classList.remove('hidden');
      }
    } else if (this.authBtn) {
      if (this.authPillAvatar) this.authPillAvatar.textContent = '✦';
      if (this.authPillLabel) this.authPillLabel.textContent = 'Sign In / Register';
      if (this.authPillIdBadge) this.authPillIdBadge.classList.add('hidden');
    }
  }

  // --- Registration Handler ---
  async handleRegister(e) {
    e.preventDefault();
    this.clearAlerts();

    const fullName = this.regFullNameInput.value.trim();
    const identifier = this.regIdentifierInput.value.trim();
    const channel = this.regIdentifierInput.type === 'email' ? 'email' : 'phone';
    const password = this.regPasswordInput.value;
    const confirmPassword = this.regConfirmPasswordInput.value;
    const termsAccepted = this.regTermsCheckbox.checked;

    if (!fullName) return this.showError('Please enter your full name.');
    if (!identifier) return this.showError('Please enter your email or phone number.');
    if (password.length < 8) return this.showError('Password must be at least 8 characters long.');
    if (password !== confirmPassword) return this.showError('Passwords do not match.');
    if (!termsAccepted) return this.showError('You must accept the Terms and Privacy Policy to create an account.');

    this.setButtonLoading(this.regSubmitBtn, true, 'Creating Account...');

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName,
          identifier: identifier,
          channel: channel,
          password: password,
          confirm_password: confirmPassword,
          terms_accepted: termsAccepted,
          student_level: 'undergraduate'
        })
      });

      const data = await res.json();
      if (!res.ok) {
        const errorMsg = data.error?.message || data.detail || 'Registration failed.';
        throw new Error(errorMsg);
      }

      // Transition to verification view
      this.pendingVerificationIdentifier = identifier;
      this.pendingVerificationChannel = channel;
      this.verifyTargetLabel.textContent = identifier;
      if (data.dev_code && this.verifyDevHint) {
        this.verifyDevHint.textContent = `[Dev Test Code: ${data.dev_code}]`;
        this.verifyDevHint.classList.remove('hidden');
      }

      this.switchView('verify');
      this.startResendCountdown();
      this.showSuccess('Account created! Please enter the 6-digit verification code dispatched to your contact.');
    } catch (err) {
      this.showError(err.message);
    } finally {
      this.setButtonLoading(this.regSubmitBtn, false, '✦ Create Student Account');
    }
  }

  // --- OTP Verification Handler ---
  async handleVerify(e) {
    e.preventDefault();
    this.clearAlerts();

    const code = this.verifyCodeInput.value.trim();
    const identifier = this.pendingVerificationIdentifier;

    if (!code || code.length < 4) {
      return this.showError('Please enter the 6-digit verification code.');
    }

    this.setButtonLoading(this.verifySubmitBtn, true, 'Verifying...');

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/v1/auth/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          identifier: identifier,
          code: code
        })
      });

      const data = await res.json();
      if (!res.ok) {
        const errorMsg = data.error?.message || data.detail || 'Verification failed.';
        throw new Error(errorMsg);
      }

      this.setCurrentUser(data.user, data.access_token);
      this.showSuccess(`Welcome to the Academy, ${data.user.full_name}! Your Student ID is ${data.user.student_id}.`);
      setTimeout(() => {
        this.switchView('dashboard');
      }, 1000);
    } catch (err) {
      this.showError(err.message);
    } finally {
      this.setButtonLoading(this.verifySubmitBtn, false, 'Verify & Enter Academy ✦');
    }
  }

  // --- Resend Verification Code ---
  async handleResendCode() {
    if (this.resendCountdown > 0) return;
    this.clearAlerts();

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/v1/auth/resend-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: this.pendingVerificationIdentifier })
      });
      const data = await res.json();
      if (res.ok) {
        if (data.dev_code && this.verifyDevHint) {
          this.verifyDevHint.textContent = `[Dev Test Code: ${data.dev_code}]`;
          this.verifyDevHint.classList.remove('hidden');
        }
        this.showSuccess('A fresh verification code has been dispatched.');
        this.startResendCountdown();
      } else {
        this.showError(data.error?.message || data.detail || 'Unable to resend code.');
      }
    } catch (err) {
      this.showError('Network error resending code.');
    }
  }

  startResendCountdown() {
    this.resendCountdown = 60;
    if (this.verifyResendBtn) {
      this.verifyResendBtn.disabled = true;
      this.verifyResendBtn.classList.add('opacity-50', 'cursor-not-allowed');
    }

    if (this.resendTimer) clearInterval(this.resendTimer);
    this.resendTimer = setInterval(() => {
      this.resendCountdown--;
      if (this.verifyResendBtn) {
        if (this.resendCountdown > 0) {
          this.verifyResendBtn.textContent = `Resend Code (${this.resendCountdown}s)`;
        } else {
          this.verifyResendBtn.textContent = 'Resend Code';
          this.verifyResendBtn.disabled = false;
          this.verifyResendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
          clearInterval(this.resendTimer);
        }
      }
    }, 1000);
  }

  // --- Login Handler ---
  async handleLogin(e) {
    e.preventDefault();
    this.clearAlerts();

    const identifier = this.loginIdentifierInput.value.trim();
    const password = this.loginPasswordInput.value;
    const rememberMe = this.loginRememberMe ? this.loginRememberMe.checked : false;

    if (!identifier) return this.showError('Please enter your email or phone number.');
    if (!password) return this.showError('Please enter your password.');

    this.setButtonLoading(this.loginSubmitBtn, true, 'Signing In...');

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          identifier: identifier,
          password: password,
          remember_me: rememberMe
        })
      });

      const data = await res.json();
      if (!res.ok) {
        // Check for unverified account redirect
        if (res.status === 403 && data.error?.message && typeof data.error.message === 'object' && data.error.message.code === 'UNVERIFIED_ACCOUNT') {
          const unverifiedDetails = data.error.message;
          this.pendingVerificationIdentifier = unverifiedDetails.identifier;
          this.pendingVerificationChannel = unverifiedDetails.channel || 'email';
          this.verifyTargetLabel.textContent = unverifiedDetails.identifier;
          this.switchView('verify');
          this.showError('Your account has not been verified yet. Enter the code sent to your contact.');
          return;
        }
        const errorMsg = data.error?.message || data.detail || 'Invalid login identifier or password.';
        throw new Error(typeof errorMsg === 'string' ? errorMsg : 'Authentication failed.');
      }

      this.setCurrentUser(data.user, data.access_token);
      this.showSuccess(`Welcome back, ${data.user.full_name || data.user.username}!`);
      setTimeout(() => {
        this.switchView('dashboard');
      }, 700);
    } catch (err) {
      this.showError(err.message);
    } finally {
      this.setButtonLoading(this.loginSubmitBtn, false, '✦ Sign In to Academy');
    }
  }

  // --- Forgot Password Handler ---
  async handleForgotPassword(e) {
    e.preventDefault();
    this.clearAlerts();

    const identifier = this.forgotIdentifierInput.value.trim();
    if (!identifier) return this.showError('Please enter your registered email or phone number.');

    this.setButtonLoading(this.forgotSubmitBtn, true, 'Sending Code...');

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/v1/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: identifier })
      });
      const data = await res.json();
      this.resetIdentifierInput.value = identifier;
      this.switchView('reset');
      this.showSuccess('A single-use password reset code has been sent. Please set your new password.');
    } catch (err) {
      this.showError('Failed to send reset code. Please try again.');
    } finally {
      this.setButtonLoading(this.forgotSubmitBtn, false, 'Send Password Reset Code');
    }
  }

  // --- Reset Password Handler ---
  async handleResetPassword(e) {
    e.preventDefault();
    this.clearAlerts();

    const identifier = this.resetIdentifierInput.value.trim();
    const code = this.resetCodeInput.value.trim();
    const newPassword = this.resetPasswordInput.value;
    const confirmPassword = this.resetConfirmPasswordInput.value;

    if (!code) return this.showError('Please enter the password reset code.');
    if (newPassword.length < 8) return this.showError('Password must be at least 8 characters long.');
    if (newPassword !== confirmPassword) return this.showError('Passwords do not match.');

    this.setButtonLoading(this.resetSubmitBtn, true, 'Updating Password...');

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/v1/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identifier: identifier,
          code: code,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error?.message || data.detail || 'Password reset failed.');
      }

      this.switchView('login');
      this.showSuccess('Password updated successfully! Please sign in with your new password.');
    } catch (err) {
      this.showError(err.message);
    } finally {
      this.setButtonLoading(this.resetSubmitBtn, false, 'Update Password & Sign In');
    }
  }

  // --- Load Personal Dashboard Data ---
  async loadDashboardData() {
    if (!this.authToken) {
      this.switchView('login');
      return;
    }

    try {
      const res = await fetch(`${this.apiBaseUrl}/api/v1/dashboard`, {
        headers: { 'Authorization': `Bearer ${this.authToken}` },
        credentials: 'include'
      });

      if (!res.ok) {
        if (res.status === 401) {
          this.clearSession();
          this.switchView('login');
          this.showError('Session expired. Please sign in again.');
        }
        return;
      }

      const data = await res.json();
      this.renderDashboard(data);
    } catch (err) {
      console.error('Error fetching dashboard:', err);
    }
  }

  renderDashboard(data) {
    if (this.dashFullName) this.dashFullName.textContent = data.student_name || 'Honored Student';
    if (this.dashStudentId) this.dashStudentId.textContent = data.student_id || 'STU-UNKNOWN';
    if (this.dashContact) {
      this.dashContact.textContent = data.email || data.phone || 'Verified Student';
    }
    if (this.dashLevelBadge) {
      this.dashLevelBadge.textContent = (data.student_level || 'undergraduate').toUpperCase();
    }
    if (this.dashDocsCount) this.dashDocsCount.textContent = data.total_documents || '0';
    if (this.dashMaterialsCount) this.dashMaterialsCount.textContent = data.total_study_materials || '0';
    if (this.dashQuizzesCount) this.dashQuizzesCount.textContent = data.total_quizzes_taken || '0';
    if (this.dashAvgScore) this.dashAvgScore.textContent = `${data.average_quiz_score || 0}%`;

    // Render Assigned Character Tutors Grid
    if (this.dashTutorsGrid && data.assigned_tutors) {
      this.dashTutorsGrid.innerHTML = data.assigned_tutors.map(t => `
        <div class="p-2.5 rounded-lg bg-slate-900/60 border border-[#d3bc8e]/20 flex items-center justify-between hover:border-amber-400/50 transition-all">
          <div>
            <div class="text-xs font-bold text-[#fae4b5]">${t.tutor_name}</div>
            <div class="text-[10px] text-slate-400">${t.subject} • ${t.element}</div>
          </div>
          <button class="dash-study-tutor-btn genshin-btn py-1 px-2.5 text-[10px] cursor-pointer" data-character-id="${t.character_id}">
            Study ✦
          </button>
        </div>
      `).join('');

      // Add click listener to switch tutor directly from dashboard
      this.dashTutorsGrid.querySelectorAll('.dash-study-tutor-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const charId = btn.getAttribute('data-character-id');
          if (window.switchTutor) {
            window.switchTutor(charId);
            this.closeModal();
          }
        });
      });
    }

    // Render Weak Topics / Recommendations
    if (this.dashWeakTopicsList) {
      const items = (data.weak_topics && data.weak_topics.length > 0)
        ? data.weak_topics.map(w => `
            <div class="p-2 rounded bg-amber-950/20 border border-amber-500/20 text-xs flex justify-between items-center">
              <span class="text-amber-200">${w.topic_name}</span>
              <span class="text-[10px] text-amber-400 font-bold">Mastery: ${Math.round(w.mastery_score * 100)}%</span>
            </div>
          `).join('')
        : '<div class="text-xs text-slate-400 py-1 italic">✦ Excellent comprehension! No critical weak topics detected.</div>';
      this.dashWeakTopicsList.innerHTML = items;
    }

    // Render Recent Activities
    if (this.dashRecentActivitiesList) {
      const items = (data.recent_activities && data.recent_activities.length > 0)
        ? data.recent_activities.map(act => `
            <div class="p-2 rounded bg-slate-900/40 border border-slate-800 text-xs flex justify-between items-center">
              <span class="text-slate-300 truncate max-w-[280px]">${act.title}</span>
              <span class="text-[10px] text-slate-500">${new Date(act.timestamp).toLocaleDateString()}</span>
            </div>
          `).join('')
        : '<div class="text-xs text-slate-400 py-1 italic">No recorded study sessions yet. Start a dialogue to begin!</div>';
      this.dashRecentActivitiesList.innerHTML = items;
    }
  }

  showDashboard() {
    this.switchView('dashboard');
    this.openModal();
  }

  // --- Copy Student ID ---
  copyStudentId() {
    const studentId = this.dashStudentId.textContent.trim();
    if (!studentId || studentId === 'STU-UNKNOWN') return;

    navigator.clipboard.writeText(studentId).then(() => {
      const originalText = this.dashCopyIdBtn.innerHTML;
      this.dashCopyIdBtn.innerHTML = '✓ Copied!';
      this.dashCopyIdBtn.classList.add('text-emerald-400', 'border-emerald-400');
      setTimeout(() => {
        this.dashCopyIdBtn.innerHTML = originalText;
        this.dashCopyIdBtn.classList.remove('text-emerald-400', 'border-emerald-400');
      }, 2000);
    }).catch(err => {
      console.warn('Clipboard write failed:', err);
    });
  }

  // --- Logout Handler ---
  async handleLogout() {
    try {
      await fetch(`${this.apiBaseUrl}/api/v1/auth/logout`, {
        method: 'POST',
        headers: this.authToken ? { 'Authorization': `Bearer ${this.authToken}` } : {},
        credentials: 'include'
      });
    } catch (e) {
      // Continue client cleanup regardless of network state
    }
    this.clearSession();
    this.closeModal();
    if (window.conversationPanel) {
      window.conversationPanel.clearMessages?.();
    }
  }

  setButtonLoading(btn, isLoading, label) {
    if (!btn) return;
    btn.disabled = isLoading;
    if (isLoading) {
      btn.innerHTML = `<span class="inline-block animate-spin mr-1">✦</span> ${label}`;
      btn.classList.add('opacity-75', 'cursor-wait');
    } else {
      btn.innerHTML = label;
      btn.classList.remove('opacity-75', 'cursor-wait');
    }
  }
}
