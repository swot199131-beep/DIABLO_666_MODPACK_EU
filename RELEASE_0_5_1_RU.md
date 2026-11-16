# DIABLO_666 MODPACK EU 0.5.1

## Версии клиента
- Официальный EU micropatch: `2.4.1_4` (5 ноября 2026).
- Каталог совместимости модов и папка `mods`: `2.4.1.1`.
- В DIABLO это два разных идентификатора; `version.xml` определяет каталог совместимости, а не отображаемое название микропатча.
- Источник патча: https://worldoftanks.eu/en/news/updates/micro-patch-2-4-1_4/
- Подтверждение структуры папки клиента: SteamDB depot metadata показывает `mods/2.4.1.1`.

## Новые модули

### Gunner HUD 0.6.1
- WGMods: https://wgmods.net/8153/
- Dossier: https://wotmodsplanet.com/mods/gunner-hud/
- Файл: `maksforge.gunner_hud_0.6.1.wotmod`
- Aim timer, индикатор сведения, данные для автозарядчиков и Ares guns.
- Статус источника: Combat ready, WoT 2.4.1.1, обновлён 13.11.2026.

### BattleStats 1.5.4
- WGMods: https://wgmods.net/8133/
- Dossier: https://wotmodsplanet.com/mods/battlestats-wn8-wnx-wtr-player-statistics-world-of-tanks/
- Файл: `custix.battlestats_1.5.4_for_2.4.1.1.zip`
- WN8 / WNX / WTR в TAB и боковых панелях.
- Статус источника: Combat ready, WoT 2.4.1.1, обновлён 07.11.2026.
- Настройки: Aslain Mod Menu + OpenWG GameFace либо ModsSettingsAPI + ModsListAPI.

## Надёжность импорта
- Импорт сначала собирается во временную папку; прежняя рабочая копия не удаляется при ошибке.
- Проверяются количество записей и распакованный размер внешнего ZIP.
- Каждый `.wotmod` проверяется как ZIP-контейнер на целостность и небезопасные пути.
- Основной файл должен совпасть с шаблоном карточки.
- SHA-256 записывается в manifest.
- Каталог совместимости читается из `catalog.json`, а не дублируется магической строкой в коде.

## Статус релиза
Developer Preview. Реальный Windows build, чистый WoT EU test, цифровая подпись и финальная проверка всех модов всё ещё обязательны.
