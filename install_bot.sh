#!/bin/bash

# Скрипт установки Telegram бота для студии маникюра
# Запуск: sudo ./install_bot.sh

set -e  # Завершить скрипт при любой ошибке

echo "=== Установка Telegram бота для студии маникюра ==="

# Функция для проверки прав суперпользователя
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Этот скрипт должен запускаться с правами sudo!"
        exit 1
    fi
}

# Функция для обновления системы
update_system() {
    echo "Обновление системы..."
    apt update
    apt upgrade -y
    echo "Система обновлена!"
}

# Функция для установки Python и pip
install_python() {
    echo "Установка Python и pip..."
    apt install -y python3 python3-pip python3-venv
    echo "Python и pip установлены!"
}

# Функция для создания виртуального окружения и установки зависимостей
setup_project() {
    echo "Настройка проекта..."
    
    # Определяем директорию проекта
    PROJECT_DIR=$(pwd)
    
    # Создаем виртуальное окружение
    python3 -m venv venv
    source venv/bin/activate
    
    # Устанавливаем зависимости
    pip install -r requirements.txt
    
    echo "Зависимости установлены!"
}

# Функция для настройки переменных окружения
setup_env() {
    echo "Настройка переменных окружения..."
    
    # Запрашиваем данные у пользователя
    read -p "Введите BOT_TOKEN: " BOT_TOKEN
    read -p "Введите ADMIN_IDS (через запятую): " ADMIN_IDS
    
    # Создаем файл .env
    cat > .env << EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
EOF
    
    echo "Файл .env создан!"
}

# Функция для настройки службы systemd
setup_service() {
    echo "Настройка службы systemd..."
    
    # Определяем директорию проекта
    PROJECT_DIR=$(pwd)
    USER_NAME=$(logname)
    
    # Создаем файл службы
    cat > /lib/systemd/system/tg_bot.service << EOF
[Unit]
Description=Telegram Bot for Nail Studio
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python3 main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    # Обновляем systemd и запускаем службу
    systemctl daemon-reload
    systemctl start tg_bot.service
    systemctl enable tg_bot.service
    
    echo "Служба systemd настроена и запущена!"
}

# Функция для проверки статуса службы
check_status() {
    echo "Проверка статуса службы..."
    sleep 3  # Даем службе время запуститься
    systemctl status tg_bot.service --no-pager -l
}

# Функция для установки шрифтов (для поддержки кириллицы в PDF)
install_fonts() {
    echo "Установка шрифтов для поддержки кириллицы..."
    apt install -y fonts-dejavu
    echo "Шрифты установлены!"
}

# Основная функция
main() {
    check_root
    update_system
    install_python
    install_fonts
    setup_project
    setup_env
    setup_service
    check_status
    
    echo "=== Установка завершена! ==="
    echo "Бот запущен как служба systemd."
    echo "Для просмотра логов: journalctl -u tg_bot.service -f"
    echo "Для перезапуска бота: systemctl restart tg_bot.service"
    echo "Для остановки бота: systemctl stop tg_bot.service"
}

# Запускаем основную функцию
main