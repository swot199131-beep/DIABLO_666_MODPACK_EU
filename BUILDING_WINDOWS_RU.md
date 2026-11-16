# Сборка DIABLO_666 MODPACK EU 0.6.0 для Windows

## Требования
- Windows 10/11 x64
- Python 3.12 x64 с Python Launcher (`py`)
- Inno Setup 6: https://jrsoftware.org/isinfo.php

## Сборка
1. Распаковать исходный архив.
2. Запустить `BUILD_EXE.bat`.
3. Скрипт установит Python-зависимости, проверит каталог, выполнит 21 тест, соберёт приложение PyInstaller `--onefile` и затем Inno Setup.
4. Итоговый установщик:
   `dist\\installer\\DIABLO_666_MODPACK_EU_Setup_v0.6.0.exe`

## Что делает установщик
- Устанавливает программу в `%LOCALAPPDATA%\\Programs\\DIABLO_666_MODPACK_EU`.
- Не требует прав администратора.
- Создаёт ярлык в меню «Пуск».
- Предлагает ярлык на рабочем столе и запуск после установки.
- При удалении удаляет программу, но сохраняет `%LOCALAPPDATA%\\DIABLO_666_MODPACK_EU` с пакетами, логами и резервными копиями.

## GitHub Actions
Загрузите проект в GitHub и откройте Actions → `Build DIABLO Windows installer` → Run workflow. Скачайте artifact. При создании тега `v0.6.0` workflow автоматически создаст GitHub Release.

## Примечания
- Сборка unsigned, пока не настроен сертификат Authenticode.
- Сторонние модификации не перепаковываются и не распространяются вместе с установщиком.
- Перед публичным релизом необходимы тесты на чистой Windows и реальном WoT EU.
