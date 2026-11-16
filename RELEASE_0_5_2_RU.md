# DIABLO_666 MODPACK EU 0.6.0 — Windows Setup EXE pipeline

## Что нового
- Добавлен Inno Setup 6 проект `installer/DIABLO_666_MODPACK_EU.iss`.
- Итоговый файл после Windows-сборки: `DIABLO_666_MODPACK_EU_Setup_v0.6.0.exe`.
- Установщик работает без прав администратора и ставится в `%LOCALAPPDATA%\\Programs`.
- Создаёт ярлык в меню «Пуск» и предлагает дополнительный ярлык на рабочем столе.
- Предлагает запустить приложение после установки.
- Деинсталлятор удаляет приложение, но сохраняет пользовательские пакеты, настройки и резервные копии в `%LOCALAPPDATA%\\DIABLO_666_MODPACK_EU`.
- В приложение и установщик добавлена иконка и версия файла.
- Подготовлен GitHub Actions workflow: Windows x64 → тесты → PyInstaller onefile → Inno Setup → SHA-256 → workflow artifact; при теге `v*` создаётся GitHub Release.

## Получение реального EXE на Windows
### Вариант A — локально
1. Установить Windows 10/11 x64.
2. Установить Python 3.12 x64.
3. Установить Inno Setup 6: https://jrsoftware.org/isinfo.php
4. Распаковать исходный архив.
5. Запустить `BUILD_EXE.bat`.
6. Готовый установщик появится здесь:
   `dist\\installer\\DIABLO_666_MODPACK_EU_Setup_v0.6.0.exe`

### Вариант B — GitHub Actions
1. Создать GitHub repository и загрузить в него содержимое этого проекта.
2. Открыть вкладку Actions.
3. Запустить workflow `Build DIABLO Windows installer` через Run workflow.
4. Скачать artifact `DIABLO_666_MODPACK_EU_Setup_v0.6.0_Windows_x64`.
5. Для публичного релиза создать тег `v0.6.0`; workflow соберёт EXE и опубликует GitHub Release.

## Честный статус текущего файла
В этом архиве находится проект настоящего Windows-установщика, но не сам готовый Setup EXE. Текущая среда исполнения — Linux; Windows PE-сборщик, PyInstaller и Inno Setup здесь недоступны. Создать Windows EXE в этой среде и выдать его за собранный было бы неправильно.

## Публикация
Сборка будет unsigned, пока владелец проекта не добавит сертификат подписи кода. Windows SmartScreen может показывать предупреждение. До распространения проверьте установщик на чистой Windows 10/11 и протестируйте установку/обновление/удаление с WoT EU.

## Подпись кода (необязательно, но желательно для публичного выпуска)
В настройках GitHub repository добавьте Actions secrets:
- `WINDOWS_CERTIFICATE_BASE64` — содержимое PFX, закодированное Base64.
- `WINDOWS_CERTIFICATE_PASSWORD` — пароль PFX.

Workflow подпишет Setup EXE через Authenticode и timestamp server. Если secrets не заданы, релиз останется unsigned; это будет явно указано в `RELEASE_INFO.txt`. Никогда не помещайте PFX или пароль в исходный архив/репозиторий.
