# Публикация DIABLO_666 MODPACK EU в GitHub

Публичный репозиторий нельзя создать от имени владельца без входа в его GitHub-аккаунт. Этот проект подготовлен к загрузке; ниже — короткая процедура.

## 1. Создать репозиторий
1. Войти на https://github.com/new
2. Repository name: `DIABLO_666_MODPACK_EU`
3. Visibility: Public.
4. Не ставить галочки Add README, .gitignore или license — они уже находятся в проекте.
5. Создать репозиторий.

## 2. Загрузить исходники
Установить Git for Windows, распаковать ZIP в отдельную папку, открыть PowerShell в этой папке и выполнить:

```powershell
git init
git branch -M main
git add .
git status
git commit -m "Prepare DIABLO_666 MODPACK EU 0.6.0"
git remote add origin https://github.com/YOUR_ACCOUNT/DIABLO_666_MODPACK_EU.git
git push -u origin main
```

Заменить `YOUR_ACCOUNT` на свой GitHub username. Перед `git add` убедиться, что в проект не попали личные ключи, резервные копии или скачанные сторонние бинарники.

## 3. Запустить сборку Windows
1. Открыть вкладку Actions в репозитории.
2. Выбрать `Build DIABLO Windows installer`.
3. Нажать Run workflow.
4. Дождаться зелёного статуса всех шагов.
5. Скачать artifact `DIABLO_666_MODPACK_EU_Setup_v0.6.0_Windows_x64`.
6. Проверить SHA-256 и протестировать установщик на чистой Windows 10/11.

## 4. Публикация релиза после тестов
Не публиковать как stable, пока не завершены тесты Windows и реального клиента WoT EU. Для создания GitHub Release workflow уже поддерживает теги `v*`; после успешного тестирования:

```powershell
git tag v0.6.0
git push origin v0.6.0
```

Workflow соберёт Setup EXE и приложит SHA-256 и RELEASE_INFO.txt к GitHub Release.

## 5. Подпись EXE
Для Authenticode нужна собственная организация/издательская подпись. Добавить в Settings → Secrets and variables → Actions:
- `WINDOWS_CERTIFICATE_BASE64`
- `WINDOWS_CERTIFICATE_PASSWORD`

Не отправлять PFX-файл, пароль или base64 сертификата в чат, issue или публичный репозиторий.

## Важно
- В GitHub Actions сейчас настроена unsigned-сборка, если секреты подписи не заданы.
- GitHub repository URL, username и credentials намеренно не придуманы и не зашиты в проект.
- Не активировать auto-updater до выбора официального репозитория и реализации проверки подписи/хеша обновления.
