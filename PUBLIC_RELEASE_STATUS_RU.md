# Публичный статус DIABLO_666 MODPACK EU 0.6.0

## Статус: DEVELOPER PREVIEW — НЕ ВЫДАВАТЬ ЗА ГОТОВЫЙ ПУБЛИЧНЫЙ EXE

### Готово
- 52 карточки в каталоге; 9 локально импортируемых карточек, 39 внешних ссылок, 12 заготовок, 2 заблокированных карточек.
- GUI: категории, поиск, галочки, карточка описания, предпросмотр, источник.
- Сохранение/загрузка локальных профилей выбора.
- Безопасная сверка предыдущего DIABLO набора с новым, восстановление оригиналов и защита чужих изменённых файлов.
- Проверка архива, SHA-256, зависимостей и конфликтов.
- PyInstaller onefile и Inno Setup 6 project.
- Windows GitHub Actions workflow с SHA-256 и опциональной Authenticode подписью.
- Каталог различает live EU 2.4.1_4 и Common Test 2.4.2; каталог модов остаётся 2.4.1.1 до подтверждения live-версии.
- Fair Play checklist обновлён по официальным публикациям января и октября 2026.

### Не завершено
- Реальный Windows EXE/Setup EXE ещё не собран (текущая среда Linux).
- Не проведён тест на чистой Windows 10/11 и в реальном WoT EU.
- Не задан публичный GitHub repository owner/name; автоматический updater приложения не активирован.
- Только часть каталога поддерживает локальный импорт; внешние карточки не означают встроенный установочный пакет.
- Не все моды проверены в бою на текущем клиенте.
- Цифровая подпись требует сертификата владельца проекта.

### Официальные источники
- Updates: https://worldoftanks.eu/en/news/updates/
- Live micropatch 2.4.1_4: https://worldoftanks.eu/en/news/updates/micro-patch-2-4-1_4/
- Common Test 2.4.2: https://worldoftanks.eu/en/news/updates/2-4-2-CT/
- Fair Play prohibited mods: https://worldoftanks.com/en/content/guide/fair-play/prohibited-mods/


## Подготовка публикации в репозитории
- [x] README, лицензия к собственному коду, credits и fair-play policy.
- [x] CONTRIBUTING, SECURITY, privacy notice.
- [x] GitHub issue templates для ошибок и предложений модов.
- [x] CI workflow для Windows build + checksum + release assets.
- [x] Инструкция по созданию репозитория и запуску сборки.
- [ ] Создать публичный GitHub repository в аккаунте владельца.
- [ ] Запустить Windows workflow и получить реальный Setup EXE.
- [ ] Пройти тесты на Windows 10/11 и реальном WoT EU.
