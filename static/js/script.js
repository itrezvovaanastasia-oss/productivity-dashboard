// Общие функции для сайта

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Анимация появления элементов
    animateElements();

    // Настройка tooltips Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Настройка popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Автоматическое обновление данных каждые 5 минут
    setInterval(refreshData, 300000);
});

// Анимация элементов при прокрутке
function animateElements() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.stat-card, .info-card, .chart-container').forEach(el => {
        observer.observe(el);
    });
}

// Обновление данных
function refreshData() {
    if (window.location.pathname === '/stats') {
        fetch('/api/global_averages')
            .then(response => response.json())
            .then(data => {
                // Здесь можно обновить данные на странице
                console.log('Данные обновлены', data);
            })
            .catch(error => console.error('Ошибка обновления:', error));
    }
}

// Экспорт данных
function exportData(format) {
    let url = '';

    switch(format) {
        case 'csv':
            url = '/api/export/csv';
            break;
        case 'json':
            url = '/api/export/json';
            break;
        case 'excel':
            url = '/api/export/excel';
            break;
        default:
            console.error('Неизвестный формат:', format);
            return;
    }

    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `productivity_data_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Ошибка экспорта:', error);
            alert('Ошибка при экспорте данных');
        });
}

// Поиск пользователей
function searchUsers(query) {
    fetch(`/api/search/users?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            // Обновление списка пользователей
            console.log('Результаты поиска:', data);
        })
        .catch(error => console.error('Ошибка поиска:', error));
}

// Отображение уведомлений
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Автоматическое скрытие через 5 секунд
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, 5000);
}

// Форматирование чисел
function formatNumber(num, decimals = 2) {
    return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Определение типа устройства
function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// Сохранение настроек в localStorage
function saveSetting(key, value) {
    try {
        localStorage.setItem(`productivity_${key}`, JSON.stringify(value));
    } catch (e) {
        console.error('Ошибка сохранения настроек:', e);
    }
}

// Загрузка настроек из localStorage
function loadSetting(key, defaultValue) {
    try {
        const value = localStorage.getItem(`productivity_${key}`);
        return value ? JSON.parse(value) : defaultValue;
    } catch (e) {
        console.error('Ошибка загрузки настроек:', e);
        return defaultValue;
    }
}

// Темная тема
function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-bs-theme') === 'dark';

    if (isDark) {
        html.removeAttribute('data-bs-theme');
        saveSetting('darkMode', false);
    } else {
        html.setAttribute('data-bs-theme', 'dark');
        saveSetting('darkMode', true);
    }
}

// Инициализация темной темы при загрузке
const darkMode = loadSetting('darkMode', false);
if (darkMode) {
    document.documentElement.setAttribute('data-bs-theme', 'dark');
}

// Обработчик для кнопки темной темы
document.addEventListener('DOMContentLoaded', function() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
});