# DIABLO_666 MODPACK EU 0.5.0

## Новые модули для WoT EU 2.4.1.1

### Improved Standard Sight 1.3.0
- WGMods: https://wgmods.net/8117/
- Dossier: https://wotmodsplanet.com/mods/improved-standard-sight/
- Файл: `center_corners_1.3.0.wotmod`
- Combat ready для 2.4.1.1.
- Группа конфликтов: `primary_reticle`.

### Minimap Zoom
- WGMods: https://wgmods.net/8099/
- Dossier: https://wotmodsplanet.com/mods/minimap-zoom/
- Файл: `minimap_zoom_*.wotmod`
- Combat ready для 2.4.1.1; standalone, без зависимости.

### Tank Setup Exporter 0.2.0
- WGMods: https://wgmods.net/8115/
- Dossier: https://wotmodsplanet.com/mods/tank-setup-exporter/
- Экспорт сборки танка в PNG: оборудование, боекомплект, расходники, экипаж, полевые модернизации.
- Для выбора макета используется Aslain Mod Menu; если меню есть в архиве, импортируется только при отсутствии установленной копии.

### Wreck Colours 1.0.0
- WGMods: https://wgmods.net/8114/
- Dossier: https://wotmodsplanet.com/mods/wreck-colours/
- Пользовательский цвет уничтоженных танков; живые танки и их камуфляж не затрагиваются.
- Настройки через Aslain Mod Menu.

## Общие правила импорта
- DIABLO не перепубликует бинарники сторонних авторов.
- Пользователь сам скачивает архив с официальной страницы WGMods.
- Импортёр проверяет домен источника, ожидаемое имя файла, структуру ZIP/WOTMOD, целостность и безопасные пути.
- SHA-256 вычисляется для каждого файла.
- Версия игры проверяется по `version.xml`; эти новые карточки разрешены только на 2.4.1.1.
- Для известных конфликтующих групп установка блокируется до исправления выбора.

## Публичный релиз
Сборка остаётся Developer Preview до тестирования на чистой Windows 10/11 с реальным WoT EU 2.4.1.1. EXE ещё не подписан, а запуск игры из этой среды невозможен.


## Дополнительные кандидаты прицелов
- Better Reticle Size 1.3: каталог/агрегатор сообщает 2.4.1.1, но проверенная CDN-ссылка ведёт на старый файл v1.2.5 и возвращает 404. Импорт заблокирован.
- Reticle Size Limit Remover: исходный код доступен, но актуальный отдельный бинарник для 2.4.1.1 не подтверждён. Импорт заблокирован.
- См. `RETICLE_COMPATIBILITY_RU.md`.
