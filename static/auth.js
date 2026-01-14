/**
 * iGet - Telegram Authorization
 * Минималистичный интерфейс авторизации
 */

class TelegramAuth {
    constructor() {
        this.authModal = null;
        this.init();
    }

    init() {
        this.checkAuthStatus();
    }

    async checkAuthStatus() {
        try {
            const response = await fetch('/api/auth/status');
            const data = await response.json();

            if (data.status && data.status.authorized) {
                this.onAuthSuccess(data.user);
            } else {
                this.showAuthModal();
            }
        } catch (error) {
            console.error('Auth status check error:', error);
            this.showAuthModal();
        }
    }

    showAuthModal() {
        if (this.authModal) return;

        this.authModal = document.createElement('div');
        this.authModal.id = 'auth-modal';
        this.authModal.className = 'auth-modal';
        this.authModal.innerHTML = `
            <div class="auth-modal-content">
                <div class="auth-card">
                    <!-- Header -->
                    <div class="auth-header">
                        <div class="auth-logo">iGet</div>
                        <div class="auth-subtitle">Войдите через Telegram</div>
                    </div>

                    <!-- Status Dots -->
                    <div class="auth-status-dots">
                        <div class="status-dot active" id="status-system"></div>
                        <div class="status-dot" id="status-network"></div>
                        <div class="status-dot" id="status-auth"></div>
                    </div>

                    <!-- Loading -->
                    <div class="boot-sequence" id="boot-sequence">
                        <div class="boot-loader"></div>
                        <div class="boot-text">Подключение...</div>
                    </div>

                    <!-- Auth Screen -->
                    <div class="auth-screen hidden" id="auth-screen">
                        <!-- Phone Form -->
                        <div class="auth-form" id="phone-form">
                            <div class="form-title">Номер телефона</div>
                            <div class="form-subtitle">Введите номер, привязанный к Telegram</div>

                            <div class="input-group">
                                <input
                                    type="tel"
                                    id="phone-input"
                                    class="auth-input"
                                    placeholder="+7 999 123 45 67"
                                    autocomplete="off"
                                >
                            </div>

                            <button class="auth-btn" id="send-code-btn">
                                Получить код
                            </button>

                            <div class="helper-text">Нажмите Enter для отправки</div>
                        </div>

                        <!-- Code Form -->
                        <div class="auth-form hidden" id="code-form">
                            <div class="form-title">Код подтверждения</div>
                            <div class="form-subtitle">Код отправлен в Telegram</div>

                            <div class="input-group">
                                <input
                                    type="text"
                                    id="code-input"
                                    class="auth-input"
                                    placeholder="12345"
                                    maxlength="5"
                                    autocomplete="off"
                                >
                            </div>

                            <button class="auth-btn" id="submit-code-btn">
                                Подтвердить
                            </button>

                            <div class="helper-text">Нажмите Enter для отправки</div>
                        </div>

                        <!-- Password Form -->
                        <div class="auth-form hidden" id="password-form">
                            <div class="form-title">Двухфакторная аутентификация</div>
                            <div class="form-subtitle">Введите пароль 2FA</div>

                            <div class="input-group">
                                <input
                                    type="password"
                                    id="password-input"
                                    class="auth-input"
                                    placeholder="Пароль"
                                    autocomplete="off"
                                >
                            </div>

                            <button class="auth-btn" id="submit-password-btn">
                                Войти
                            </button>

                            <div class="helper-text">Нажмите Enter для отправки</div>
                        </div>

                        <!-- Status -->
                        <div class="auth-status" id="auth-status-text"></div>

                        <!-- Error -->
                        <div class="auth-error hidden" id="auth-error"></div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(this.authModal);

        // Boot sequence
        setTimeout(() => {
            this.completeBoot();
        }, 1200);

        this.attachEventListeners();
    }

    completeBoot() {
        const bootSeq = document.getElementById('boot-sequence');
        const authScreen = document.getElementById('auth-screen');

        if (bootSeq && authScreen) {
            bootSeq.style.display = 'none';
            authScreen.classList.remove('hidden');

            // Focus first input
            document.getElementById('phone-input')?.focus();

            this.setStatusDot('network', 'active');
        }
    }

    setStatusDot(id, state) {
        const dot = document.getElementById(`status-${id}`);
        if (dot) {
            dot.className = `status-dot ${state}`;
        }
    }

    attachEventListeners() {
        // Phone auth
        const sendCodeBtn = document.getElementById('send-code-btn');
        const phoneInput = document.getElementById('phone-input');

        sendCodeBtn?.addEventListener('click', () => this.sendPhoneCode());
        phoneInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendPhoneCode();
        });

        // Code submit
        const submitCodeBtn = document.getElementById('submit-code-btn');
        const codeInput = document.getElementById('code-input');

        submitCodeBtn?.addEventListener('click', () => this.submitCode());
        codeInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitCode();
        });

        // Password submit
        const submitPasswordBtn = document.getElementById('submit-password-btn');
        const passwordInput = document.getElementById('password-input');

        submitPasswordBtn?.addEventListener('click', () => this.submitPassword());
        passwordInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.submitPassword();
        });
    }

    async sendPhoneCode() {
        const phone = document.getElementById('phone-input').value.trim();

        if (!phone) {
            this.showError('Введите номер телефона');
            return;
        }

        this.updateStatus('Отправка кода...');
        this.setStatusDot('network', 'waiting');

        try {
            const response = await fetch('/api/auth/phone', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone })
            });

            const data = await response.json();

            if (data.success) {
                document.getElementById('phone-form').classList.add('hidden');
                document.getElementById('code-form').classList.remove('hidden');
                this.updateStatus('Код отправлен в Telegram');
                document.getElementById('code-input')?.focus();
                this.setStatusDot('network', 'active');
            } else {
                this.showError(data.error || 'Не удалось отправить код');
                this.setStatusDot('network', 'error');
            }
        } catch (error) {
            this.showError('Ошибка подключения: ' + error.message);
            this.setStatusDot('network', 'error');
        }
    }

    async submitCode() {
        const code = document.getElementById('code-input').value.trim();

        if (!code) {
            this.showError('Введите код');
            return;
        }

        this.updateStatus('Проверка кода...');
        this.setStatusDot('auth', 'waiting');

        try {
            const response = await fetch('/api/auth/code', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });

            const data = await response.json();

            if (data.success) {
                this.onAuthSuccess(data.user);
            } else if (data.requires_password) {
                document.getElementById('code-form').classList.add('hidden');
                document.getElementById('password-form').classList.remove('hidden');
                this.updateStatus('Требуется пароль 2FA');
                document.getElementById('password-input')?.focus();
            } else {
                this.showError(data.error || 'Неверный код');
                this.setStatusDot('auth', 'error');
            }
        } catch (error) {
            this.showError('Ошибка подключения: ' + error.message);
            this.setStatusDot('auth', 'error');
        }
    }

    async submitPassword() {
        const password = document.getElementById('password-input').value;

        if (!password) {
            this.showError('Введите пароль');
            return;
        }

        this.updateStatus('Проверка пароля...');

        try {
            const response = await fetch('/api/auth/password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password })
            });

            const data = await response.json();

            if (data.success) {
                this.onAuthSuccess(data.user);
            } else {
                this.showError(data.error || 'Неверный пароль');
                this.setStatusDot('auth', 'error');
            }
        } catch (error) {
            this.showError('Ошибка подключения: ' + error.message);
            this.setStatusDot('auth', 'error');
        }
    }

    updateStatus(message) {
        const statusEl = document.getElementById('auth-status-text');
        if (statusEl) {
            statusEl.textContent = message;
        }
        document.getElementById('auth-error')?.classList.add('hidden');
    }

    showError(message) {
        const errorEl = document.getElementById('auth-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
        }
        this.updateStatus('');
    }

    onAuthSuccess(user) {
        this.updateStatus('✓ Авторизация успешна');
        this.setStatusDot('auth', 'active');

        setTimeout(() => {
            if (this.authModal) {
                this.authModal.remove();
                this.authModal = null;
            }
            this.displayUserInfo(user);
        }, 800);
    }

    displayUserInfo(user) {
        console.log('Authorized as:', user);
    }

    // WebSocket event handler
    handleAuthEvent(data) {
        if (data.type === 'auth_status') {
            if (data.status === 'success') {
                this.onAuthSuccess(data.data.user);
            } else if (data.status === 'error') {
                this.showError(data.data.error);
            } else {
                this.updateStatus(this.getStatusMessage(data.status));
            }
        }
    }

    getStatusMessage(status) {
        const messages = {
            'sending_code': 'Отправка кода...',
            'waiting_code': 'Ожидание кода...',
            'verifying_code': 'Проверка кода...',
            'waiting_password': 'Требуется пароль',
            'verifying_password': 'Проверка пароля...',
            'success': '✓ Успешно!'
        };
        return messages[status] || status;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.telegramAuth = new TelegramAuth();
});
