from pathlib import Path

SOURCE = Path('Алхимический_котел_рвотное_зелье_и_афродизиак.txt')
OUTPUT = Path('Алхимический_котел_рвотная_настойка_и_скриптовый_афродизиак.txt')

text = SOURCE.read_text(encoding='utf-8')

recipe_start_marker = "  // ============================================\n  // НОВОЕ: РВОТНАЯ НАСТОЙКА"
recipe_end_marker = "  // ============================================\n  // СЛАБЫЕ РЕЦЕПТЫ"
recipe_start = text.index(recipe_start_marker)
recipe_end = text.index(recipe_end_marker, recipe_start)

new_recipes = r'''  // ============================================
  // РВОТНАЯ НАСТОЙКА
  // Порядок: гнилая плоть -> ядовитый картофель -> ферментированный паучий глаз
  // Эффекты в подсказке предмета скрыты через HideFlags:32.
  // ============================================

  ctx.addRecipe(
    ctx.createCustomRecipe(
      'Рвотная настойка',
      [
        'minecraft:rotten_flesh',
        'minecraft:poisonous_potato',
        'minecraft:fermented_spider_eye',
      ],
      1,
      function (player, ctx) {
        var vomitPotionNbt =
          '{id:"minecraft:potion",Count:1b,tag:{' +
          'Potion:"minecraft:water",' +
          'CustomPotionColor:3555072,' +
          'HideFlags:32,' +
          'CustomPotionEffects:[' +
          '{Id:27b,Amplifier:31b,Duration:60,ShowParticles:0b,ShowIcon:0b}' +
          ']}}';

        return ctx.giveRecipeResult(
          player,
          vomitPotionNbt,
          'Рвотная настойка',
          'minecraft:item.bottle.fill',
          '§2'
        );
      },
      true
    )
  );

  // ============================================
  // АФРОДИЗИАК
  // Порядок: бутылочка мёда -> сладкие ягоды -> мак
  // Полностью скриптовый, Brewin' and Chewin' не требуется.
  // ============================================

  ctx.addRecipe(
    ctx.createCustomRecipe(
      'Афродизиак',
      [
        'minecraft:honey_bottle',
        'minecraft:sweet_berries',
        'minecraft:poppy',
      ],
      1,
      function (player, ctx) {
        var aphroPotionNbt =
          '{id:"minecraft:potion",Count:1b,tag:{' +
          'Potion:"minecraft:water",' +
          'CustomPotionColor:16733695,' +
          'HideFlags:32,' +
          'CustomPotionEffects:[' +
          '{Id:26b,Amplifier:31b,Duration:60,ShowParticles:0b,ShowIcon:0b}' +
          ']}}';

        return ctx.giveRecipeResult(
          player,
          aphroPotionNbt,
          'Афродизиак',
          'minecraft:item.bottle.fill',
          '§d'
        );
      },
      true
    )
  );

'''

text = text[:recipe_start] + new_recipes + text[recipe_end:]

# Исходник пользователя ещё не вызывает обработчик в tick/timer.
old_tick_tail = "  playerObject.loadWorldInfo();\n  playerObject.processPendingDrops();\n}"
new_tick_tail = "  playerObject.loadWorldInfo();\n  playerObject.processPendingDrops();\n  playerObject.processSpecialPotionEffects();\n}"

# Заменяем два первых подходящих хвоста после function tick и function timer отдельно.
def add_call_to_event_function(source, function_name):
    start = source.index('function ' + function_name + '(event)')
    end = source.index('\n}', start) + 2
    block = source[start:end]
    if 'playerObject.processSpecialPotionEffects();' not in block:
        block = block.replace(
            '  playerObject.processPendingDrops();\n}',
            '  playerObject.processPendingDrops();\n  playerObject.processSpecialPotionEffects();\n}',
        )
    return source[:start] + block + source[end:]

text = add_call_to_event_function(text, 'tick')
text = add_call_to_event_function(text, 'timer')

insert_marker = "  this.findMobEffectIdInServerRegistry = function (effectId, player) {"
insert_at = text.index(insert_marker)

special_handler = r'''  // ============================================
  // РВОТНАЯ НАСТОЙКА И СКРИПТОВЫЙ АФРОДИЗИАК
  // ============================================

  this.readEffectAmplifier = function (entry) {
    if (!entry) return -1;
    try { return entry.getInt('Amplifier'); } catch (errInt) {}
    try { return entry.getByte('Amplifier'); } catch (errByte) {}
    try { return entry.getInt('amplifier'); } catch (errLowerInt) {}
    try { return entry.getByte('amplifier'); } catch (errLowerByte) {}
    return -1;
  };

  this.hasSpecialPotionMarker = function (effectId, numericId, amplifier) {
    try {
      var list = this.getEffectListFromEntityNbt(this.player.getEntityNbt());
      if (!list) return false;

      for (var i = 0; i < list.size(); i++) {
        var entry = list.get(i);
        var idMatches =
          this.effectEntryMatchesId(entry, effectId) ||
          this.readNumericIdFromEffectEntry(entry) === numericId;

        if (idMatches && this.readEffectAmplifier(entry) === amplifier) return true;
      }
    } catch (errMarker) {}
    return false;
  };

  this.startVomitPotion = function (now) {
    var playerName = String(this.player.getName());
    var temp = this.player.getTempdata();

    temp.put('RP_VomitUntil', now + 120000);
    temp.put('RP_VomitNext', now + 450);

    this.runWorldCommand(this.world, 'effect clear ' + playerName + ' minecraft:unluck');
    this.runWorldCommand(this.world, 'effect give ' + playerName + ' minecraft:nausea 120 4 true');
    this.runWorldCommand(this.world, 'effect give ' + playerName + ' herbalistmod:delirium 120 1 true');
    this.runWorldCommand(this.world, 'effect give ' + playerName + ' minecraft:hunger 120 1 true');

    this.player.message('§2Желудок резко сводит. Вас начинает выворачивать!');
    this.player.playSound('minecraft:entity.player.burp', 1, 0.45);
  };

  this.startAphrodisiacPotion = function (now) {
    var playerName = String(this.player.getName());
    var temp = this.player.getTempdata();

    temp.put('RP_AphroUntil', now + 90000);
    temp.put('RP_AphroNext', now);
    temp.put('RP_AphroMessageNext', now + 15000);

    this.runWorldCommand(this.world, 'effect clear ' + playerName + ' minecraft:luck');
    this.player.message('§dПо телу разливается непривычное тепло...');
    this.player.playSound('minecraft:block.amethyst_block.chime', 0.8, 1.3);

    this.runWorldCommand(
      this.world,
      'execute as ' + playerName +
        ' at @s run particle minecraft:heart ~ ~1.15 ~ 0.65 0.8 0.65 0.03 24 force'
    );
  };

  this.processVomitPotion = function (now) {
    var temp = this.player.getTempdata();
    var until = Number(temp.get('RP_VomitUntil'));
    if (isNaN(until) || until <= 0) return;

    if (now >= until) {
      try {
        temp.remove('RP_VomitUntil');
        temp.remove('RP_VomitNext');
      } catch (errClearVomit) {}
      this.player.message('§7Тошнота постепенно отступает.');
      return;
    }

    var next = Number(temp.get('RP_VomitNext'));
    if (isNaN(next)) next = 0;
    if (now < next) return;

    temp.put('RP_VomitNext', now + 800 + Math.floor(Math.random() * 1200));

    var playerName = String(this.player.getName());
    var yaw = Math.floor(Math.random() * 361) - 180;
    var pitch = Math.floor(Math.random() * 71) - 35;

    this.runWorldCommand(
      this.world,
      'execute as ' + playerName + ' at @s run tp @s ~ ~ ~ ' + yaw + ' ' + pitch
    );
    this.runWorldCommand(
      this.world,
      'execute as ' + playerName +
        ' at @s anchored eyes run particle minecraft:item minecraft:slime_ball ' +
        '^ ^-0.28 ^0.45 0.18 0.12 0.18 0.10 30 force'
    );
    this.runWorldCommand(
      this.world,
      'execute as ' + playerName +
        ' at @s anchored eyes run particle minecraft:spore_blossom_air ' +
        '^ ^-0.25 ^0.45 0.22 0.15 0.22 0.025 24 force'
    );
    this.runWorldCommand(
      this.world,
      'execute as ' + playerName +
        ' at @s run particle minecraft:sneeze ~ ~1.4 ~ 0.25 0.25 0.25 0.04 12 force'
    );
    this.runWorldCommand(
      this.world,
      'execute as ' + playerName +
        ' at @s run playsound minecraft:entity.player.burp master ' +
        '@a[distance=..18] ~ ~ ~ 1 0.45'
    );
    this.runWorldCommand(
      this.world,
      'execute as ' + playerName +
        ' at @s run playsound minecraft:entity.generic.drink master ' +
        '@a[distance=..18] ~ ~ ~ 0.65 0.35'
    );
  };

  this.processAphrodisiacPotion = function (now) {
    var temp = this.player.getTempdata();
    var until = Number(temp.get('RP_AphroUntil'));
    if (isNaN(until) || until <= 0) return;

    if (now >= until) {
      try {
        temp.remove('RP_AphroUntil');
        temp.remove('RP_AphroNext');
        temp.remove('RP_AphroMessageNext');
      } catch (errClearAphro) {}
      this.player.message('§7Непривычный жар постепенно проходит.');
      return;
    }

    var playerName = String(this.player.getName());
    var next = Number(temp.get('RP_AphroNext'));
    if (isNaN(next)) next = 0;

    if (now >= next) {
      temp.put('RP_AphroNext', now + 1200);

      this.runWorldCommand(
        this.world,
        'execute as ' + playerName +
          ' at @s run particle minecraft:heart ~ ~1.2 ~ 0.65 0.85 0.65 0.035 10 force'
      );
      this.runWorldCommand(
        this.world,
        'execute as ' + playerName +
          ' at @s run particle minecraft:cherry_leaves ~ ~1.1 ~ 0.8 0.9 0.8 0.025 12 force'
      );
      this.runWorldCommand(
        this.world,
        'execute as ' + playerName +
          ' at @s run particle minecraft:dust 1 0.15 0.45 1 ' +
          '~ ~1.05 ~ 0.55 0.75 0.55 0.01 10 force'
      );

      if (Math.random() < 0.2) {
        this.runWorldCommand(
          this.world,
          'execute as ' + playerName +
            ' at @s run playsound minecraft:block.amethyst_block.chime player ' +
            '@a[distance=..12] ~ ~ ~ 0.25 1.6'
        );
      }
    }

    var messageNext = Number(temp.get('RP_AphroMessageNext'));
    if (isNaN(messageNext)) messageNext = now + 15000;

    if (now >= messageNext) {
      temp.put('RP_AphroMessageNext', now + 18000 + Math.floor(Math.random() * 10000));
      var messages = [
        '§dСердце начинает биться заметно быстрее...',
        '§dВзгляд невольно задерживается на окружающих...',
        '§dПо коже вновь проходит тёплая волна...',
      ];
      this.player.message(messages[Math.floor(Math.random() * messages.length)]);
    }
  };

  this.processSpecialPotionEffects = function () {
    if (!this.player) return;
    var now = new Date().getTime();

    if (this.hasSpecialPotionMarker('minecraft:unluck', 27, 31)) {
      this.startVomitPotion(now);
    }
    if (this.hasSpecialPotionMarker('minecraft:luck', 26, 31)) {
      this.startAphrodisiacPotion(now);
    }

    this.processVomitPotion(now);
    this.processAphrodisiacPotion(now);
  };

'''

text = text[:insert_at] + special_handler + text[insert_at:]

required = [
    "'Рвотная настойка'",
    "'Афродизиак'",
    'HideFlags:32',
    'herbalistmod:delirium 120 1 true',
    'this.processSpecialPotionEffects();',
    'this.processAphrodisiacPotion = function',
]
for value in required:
    if value not in text:
        raise RuntimeError('Не найден обязательный фрагмент: ' + value)

OUTPUT.write_text(text, encoding='utf-8')
print(f'Создан {OUTPUT}; размер {OUTPUT.stat().st_size} байт')
