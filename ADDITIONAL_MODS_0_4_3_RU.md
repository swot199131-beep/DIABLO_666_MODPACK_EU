# DIABLO 0.4.3 — подключённые кандидаты для локального импорта

## Battle Hits 2.4.2
- Upstream release: https://gitlab.com/wot-public-mods/battle-hits/-/releases/v2.4.2
- Описание/загрузка для 2.4.1.1: https://wotmods.net/world-of-tanks-mods/hangar/battle-hits-1-17-1-2/
- Показывает нанесённые и полученные выстрелы в ангаре, поддерживает реплеи.
- MIT license в репозитории: https://github.com/wot-public-mods/battle-hits
- В релизе v2.4.2 перечислены:
  - `me.poliroid.battlehits_2.4.2.wotmod`
  - `me.poliroid.modslistapi_1.8.0.wotmod`
  - `net.openwg.gameface_1.2.2.wotmod`
- Установить все три компонента из одного официального релиза. Не использовать архивы старых версий.

## Dynamic Armor Inspector Colours 0.1.3
- Источник/архив: https://wotmods.net/world-of-tanks-mods/tools/dynamic-armor-inspector-colours/
- Карточка: https://wotmodsplanet.com/mods/dynamic-armor-inspector-colours-2-4-1-1/
- Целевой клиент: 2.4.1.1.
- Настройка цветовых уровней нативного Armor Inspector и Vehicle Hub.
- Архив включает отдельные зависимости Aslain Mod Menu и OpenWG GameFace.
- Перед импортом выбрать именно архив 2.4.1.1.

## Как импортировать
1. Выбрать мод в каталоге DIABLO.
2. Нажать «ИМПОРТ WG MOD HUB» (кнопка теперь принимает также GitLab/WoTMods источники, если они указаны в карточке).
3. Скачать архив со страницы источника самостоятельно.
4. Выбрать архив в DIABLO.
5. Установщик оставит только файлы, совпадающие с разрешёнными шаблонами, проверит целостность `.wotmod`, создаст SHA-256 и локальный manifest.
6. Отметить компонент и нажать «УСТАНОВИТЬ ВЫБРАННОЕ».

Важно: DIABLO не включает эти бинарники в публичный ZIP. Battle Hits имеет MIT-лицензию с сохранением авторства/лицензии; для Dynamic Armor Inspector Colours право перепубликации не подтверждено, поэтому только локальный пользовательский импорт.
