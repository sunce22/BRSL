# RSL Skill Multipliers

Extracted: 2026-05-27 | Game version: 11.50.1 | 301 entries (27 named)

## Formula Notation

| Token | Meaning |
|-------|---------|
| `ATK` | caster's Attack stat |
| `DEF` | caster's Defence stat |
| `HP` | caster's max HP stat |
| `SPD` | caster's Speed stat |
| `TRG_HP` | target's current HP (damage scales with target HP) |
| `TRG_DEF` | target's Defence stat |
| `TRG_ATK` | target's Attack stat |
| `BUFF_COUNT` | number of active buffs on caster or target (damage increases per buff — these heroes become significantly stronger with buff stacking) |
| `TRG_HP_PERC` | conditional: applies only when target HP is below a threshold |

**Multi-component formulas** (e.g. `4.85*ATK+0.23*HP`) — damage adds all components. Each component is `coefficient * stat`. Sites like hellhades.com often show only the primary (first) component.

---

## Named Heroes (27)

| Hero | Skill | Index | Formula | Notes |
|------|-------|-------|---------|-------|
| Acrizia | Battlefield Domination | 2 | `2*HP+2*ATK` |  |
| Alsgor Crimsonhorn | Resounding Rally | 3 | `5.6*ATK+1.1*DEF` | buff-dependent |
| Angar | Bravado (Passive) | 3 | `0.12*HP+3*ATK` |  |
| Athel | SKILL_1 | 1 | `1.3*ATK + 30` | buff-dependent |
| Athel | SKILL_4 | 4 | `4.1*ATK+0.2*HP+0.3*HP` | buff-dependent |
| Bambus Fourleaf | Bamboo Splinter | 1 | `0.3*HP+3.9*ATK+3*DEF+1*SPD` |  |
| Bladechorister Caldor | Rythm’s Crescendo | 3 | `1.9*ATK+1.55*DEF` |  |
| Branch-arm Lasair | SKILL_3 | 3 | `0.13*HP+0.09*HP` |  |
| Cinda Forgeheart | Eruptive Blow | 1 | `2.9*ATK+3.3*DEF` | buff-dependent |
| Deliana | Magnificient (Passive, Cooldown: 4 turns) | 4 | `0.05*TRG_HP+0.5*HP+4.2*DEF+1.8*ATK` | target HP/stat, buff-dependent |
| Elder Skarg | Kingslayer (Passive) | 4 | `3.3*DEF+1.9*ATK` | buff-dependent |
| Iron Brago | Fearless Charge | 2 | `0.6*TRG_HP+2.5*ATK` | target HP/stat, buff-dependent |
| Korugar Death-Bell | Conduit of Agonies | 3 | `3*ATK` |  |
| Krisk the Ageless | Enter the Morass | 1 | `1.9*ATK` |  |
| Lugan the Steadfast | Crushing Blow | 1 | `0.26*HP` |  |
| Lugan the Steadfast | Stoic Solidarity (Passive) | 4 | `0.3*HP+3.8*ATK` |  |
| Marichka the Unbreakable | Nurtured Friendship | 3 | `0.5*TRG_HP+3*ATK+1.85*DEF` | target HP/stat |
| Necrohunter | SKILL_2 | 2 | `2*ATK+2.6*DEF+0.1*HP+2*HP` |  |
| Oella | Flutter Fluster | 1 | `3.6*ATK+1.9*DEF` |  |
| Quintus the Triumphant | Strip Away | 2 | `1.9*ATK` | buff-dependent |
| Renegade | SKILL_2 | 2 | `1.2*ATK+1.8*ATK+0.3*HP+4*DEF` | buff-dependent |
| Richtoff the Bold | Bloodletting | 2 | `1.9*ATK` |  |
| Roxam | Chroma Shift | 1 | `3.8*ATK` |  |
| Roxam | Chameleon (Passive) | 4 | `2.65*DEF` |  |
| Thea the Tomb Angel | Hexreaper | 2 | `3.5*ATK` |  |
| Vergumkaar | Crushing Trample | 3 | `4.85*ATK+0.23*HP` | buff-dependent |
| Аліка | SKILL_2 | 2 | `4.2*ATK+0.75*HP` |  |

---

## All Entries (301 total)

Unnamed heroes shown as `HERO_NNN` where NNN is the internal numeric ID.

| Hero ID | Skill | Index | Formula | Notes |
|---------|-------|-------|---------|-------|
| HERO_2 | SKILL_1 | 1 | `2.3*ATK+0.15*HP` |  |
| HERO_6 | SKILL_2 | 2 | `3.9*ATK+3.2*DEF` | buff-dependent |
| Cinda Forgeheart | Eruptive Blow | 1 | `2.9*ATK+3.3*DEF` | buff-dependent |
| HERO_11 | SKILL_2 | 2 | `5.7*ATK+0.05*HP` |  |
| HERO_12 | SKILL_3 | 3 | `0.3*TRG_HP+2.8*ATK+3.5*DEF` | target HP/stat, buff-dependent |
| Lugan the Steadfast | Crushing Blow | 1 | `0.26*HP` |  |
| Lugan the Steadfast | Stoic Solidarity (Passive) | 4 | `0.3*HP+3.8*ATK` |  |
| HERO_27 | SKILL_4 | 4 | `4.4*ATK+0.2*TRG_HP` | target HP/stat |
| HERO_28 | SKILL_3 | 3 | `5.5*ATK+3.8*DEF` | buff-dependent |
| Renegade | SKILL_2 | 2 | `1.2*ATK+1.8*ATK+0.3*HP+4*DEF` | buff-dependent |
| HERO_59 | SKILL_3 | 3 | `1.8*ATK+0.1*HP` |  |
| HERO_60 | SKILL_1 | 1 | `2.7*ATK+2*DEF` | buff-dependent |
| Oella | Flutter Fluster | 1 | `3.6*ATK+1.9*DEF` |  |
| Alsgor Crimsonhorn | Resounding Rally | 3 | `5.6*ATK+1.1*DEF` | buff-dependent |
| HERO_81 | SKILL_2 | 2 | `0.12*HP+1.4*ATK+0.5*SPD+0.01*HP` | buff-dependent |
| Bambus Fourleaf | Bamboo Splinter | 1 | `0.3*HP+3.9*ATK+3*DEF+1*SPD` |  |
| HERO_94 | SKILL_1 | 1 | `1*DEF+0.03*HP+5*ATK` | buff-dependent |
| Bladechorister Caldor | Rythm’s Crescendo | 3 | `1.9*ATK+1.55*DEF` |  |
| HERO_100 | SKILL_2 | 2 | `3.2*ATK+0.1*HP` |  |
| HERO_103 | SKILL_1 | 1 | `1*ATK` |  |
| HERO_103 | SKILL_4 | 4 | `4.6*ATK` |  |
| HERO_110 | SKILL_2 | 2 | `3.1*ATK` |  |
| HERO_111 | SKILL_2 | 2 | `0.1*HP+1.1*ATK` |  |
| HERO_112 | SKILL_1 | 1 | `2.2*ATK+0.2*HP` |  |
| HERO_113 | SKILL_1 | 1 | `0.25*TRG_HP+2*ATK` | target HP/stat |
| HERO_127 | SKILL_1 | 1 | `1.9*ATK+2*HP+6*DEF+0.23*HP+2*ATK` |  |
| HERO_133 | SKILL_2 | 2 | `3.8*ATK+0.1*TRG_HP` | target HP/stat |
| HERO_134 | SKILL_1 | 1 | `2.8*ATK+0.1*HP` | buff-dependent |
| HERO_142 | SKILL_2 | 2 | `6.7*ATK` | buff-dependent |
| Athel | SKILL_1 | 1 | `1.3*ATK + 30` | buff-dependent |
| Athel | SKILL_4 | 4 | `4.1*ATK+0.2*HP+0.3*HP` | buff-dependent |
| HERO_158 | SKILL_1 | 1 | `2.1*ATK` |  |
| HERO_159 | SKILL_2 | 2 | `4.5*DEF+4.1*ATK+0.2*HP+0.5*TRG_HP` | target HP/stat, buff-dependent |
| HERO_165 | SKILL_2 | 2 | `1.4*ATK+0.1*HP` |  |
| HERO_166 | SKILL_3 | 3 | `0.15*HP+1.7*ATK` |  |
| HERO_175 | SKILL_1 | 1 | `4*ATK` |  |
| HERO_175 | SKILL_4 | 4 | `1.7*ATK+3.4*DEF` | buff-dependent |
| HERO_181 | SKILL_2 | 2 | `6.1*ATK` |  |
| HERO_182 | SKILL_1 | 1 | `2.2*ATK` |  |
| HERO_183 | SKILL_4 | 4 | `3.6*DEF+0.2*HP` |  |
| HERO_184 | SKILL_4 | 4 | `5.3*DEF+3.5*ATK` | buff-dependent |
| HERO_192 | SKILL_1 | 1 | `2*ATK+0.1*HP` |  |
| HERO_208 | SKILL_3 | 3 | `5.3*ATK` |  |
| HERO_209 | SKILL_2 | 2 | `2.3*ATK` |  |
| HERO_214 | SKILL_2 | 2 | `3.5*DEF+2.7*ATK+0.2*HP` | buff-dependent |
| Angar | Bravado (Passive) | 3 | `0.12*HP+3*ATK` |  |
| HERO_230 | SKILL_3 | 3 | `0.2*HP+3.6*ATK` |  |
| Richtoff the Bold | Bloodletting | 2 | `1.9*ATK` |  |
| HERO_234 | SKILL_1 | 1 | `2.9*ATK+3.6*DEF` | buff-dependent |
| HERO_240 | SKILL_1 | 1 | `0.2*TRG_HP+4.3*ATK` | target HP/stat |
| HERO_247 | SKILL_4 | 4 | `4.6*ATK+1*DEF` |  |
| HERO_249 | SKILL_2 | 2 | `5*DEF+0.3*TRG_HP+4.1*ATK` | target HP/stat |
| HERO_252 | SKILL_3 | 3 | `4.5*ATK` |  |
| HERO_253 | SKILL_1 | 1 | `1.9*ATK` |  |
| HERO_253 | SKILL_4 | 4 | `4.25*ATK+0.8*TRG_HP+3.5*DEF+2*HP` | target HP/stat |
| HERO_256 | SKILL_3 | 3 | `0.25*TRG_HP` | target HP/stat |
| HERO_257 | SKILL_1 | 1 | `4.4*ATK+0.2*TRG_HP+3.8*DEF+0.1*HP` | target HP/stat |
| HERO_261 | SKILL_1 | 1 | `4.6*ATK+0.25*HP` |  |
| HERO_264 | SKILL_4 | 4 | `0.3*HP+3*ATK+0.05*TRG_HP+10*ATK+1.78*DEF` | target HP/stat, buff-dependent |
| HERO_271 | SKILL_3 | 3 | `0.2*HP+0.15*HP+0.1*HP+3*ATK+5*ATK+1.7*DEF` | buff-dependent |
| HERO_279 | SKILL_1 | 1 | `3.4*ATK+0.3*HP` | buff-dependent |
| HERO_295 | SKILL_3 | 3 | `6.9*ATK+0.3*HP+1.6*DEF` | buff-dependent |
| HERO_302 | SKILL_1 | 1 | `1.7*ATK` |  |
| HERO_303 | SKILL_3 | 3 | `3.4*ATK` |  |
| HERO_305 | SKILL_1 | 1 | `0.3*HP+4.4*DEF+4*ATK+3*DEF+0.1*TRG_HP` | target HP/stat, buff-dependent |
| HERO_312 | SKILL_1 | 1 | `1.6*ATK` |  |
| HERO_320 | SKILL_1 | 1 | `1.7*ATK+0.25*TRG_HP+4*ATK+1.9*DEF` | target HP/stat |
| Аліка | SKILL_2 | 2 | `4.2*ATK+0.75*HP` |  |
| HERO_326 | SKILL_4 | 4 | `0.75*HP+4.3*ATK` |  |
| HERO_330 | SKILL_4 | 4 | `2.55*ATK` |  |
| HERO_332 | SKILL_2 | 2 | `0.1*HP+1.9*ATK` |  |
| HERO_335 | SKILL_4 | 4 | `3.5*ATK+2.4*DEF+0.25*TRG_HP` | target HP/stat |
| HERO_342 | SKILL_2 | 2 | `1.2*ATK+3.7*DEF` | buff-dependent |
| HERO_347 | SKILL_4 | 4 | `0.15*HP+1.1*ATK` | buff-dependent |
| HERO_351 | SKILL_3 | 3 | `4*ATK+0.08*HP` | buff-dependent |
| HERO_357 | SKILL_3 | 3 | `1.9*ATK+0.25*HP+3.1*DEF` | buff-dependent |
| HERO_362 | SKILL_1 | 1 | `3*ATK+0.3*TRG_HP+3.4*DEF` | target HP/stat |
| Krisk the Ageless | Enter the Morass | 1 | `1.9*ATK` |  |
| HERO_369 | SKILL_3 | 3 | `7.15*ATK+0.28*HP+2.3*DEF` | buff-dependent |
| HERO_379 | SKILL_4 | 4 | `2*ATK` | buff-dependent |
| Elder Skarg | Kingslayer (Passive) | 4 | `3.3*DEF+1.9*ATK` | buff-dependent |
| HERO_392 | SKILL_4 | 4 | `3.1*ATK+0.1*HP` |  |
| HERO_394 | SKILL_3 | 3 | `0.2*HP+3*ATK` | buff-dependent |
| HERO_405 | SKILL_1 | 1 | `4.5*ATK+0.1*HP` | buff-dependent |
| HERO_406 | SKILL_4 | 4 | `0.1*HP+2.3*ATK` |  |
| HERO_408 | SKILL_2 | 2 | `1.9*ATK+6*DEF` | buff-dependent |
| Necrohunter | SKILL_2 | 2 | `2*ATK+2.6*DEF+0.1*HP+2*HP` |  |
| HERO_438 | SKILL_1 | 1 | `3.5*ATK+0.1*TRG_HP` | target HP/stat |
| Thea the Tomb Angel | Hexreaper | 2 | `3.5*ATK` |  |
| HERO_445 | SKILL_1 | 1 | `6*ATK+1.9*DEF` | buff-dependent |
| HERO_446 | SKILL_4 | 4 | `0.06*HP+3*DEF+4*ATK` | buff-dependent |
| HERO_452 | SKILL_2 | 2 | `0.5*TRG_HP+2.2*ATK` | target HP/stat, buff-dependent |
| HERO_457 | SKILL_1 | 1 | `4.2*ATK+0.1*HP` | buff-dependent |
| HERO_461 | SKILL_3 | 3 | `0.2*HP+3.8*DEF+4*ATK` |  |
| HERO_466 | SKILL_2 | 2 | `3.8*DEF+2*ATK` |  |
| HERO_468 | SKILL_1 | 1 | `2*ATK+0.5*HP+2*HP` |  |
| Acrizia | Battlefield Domination | 2 | `2*HP+2*ATK` |  |
| HERO_474 | SKILL_3 | 3 | `3.9*DEF+5*ATK` |  |
| HERO_475 | SKILL_4 | 4 | `0.1*TRG_HP+5*ATK+0.5*HP+0.16*HP` | target HP/stat |
| HERO_479 | SKILL_1 | 1 | `0.2*HP+1.3*DEF+0.3*HP+3.1*ATK` | buff-dependent |
| HERO_485 | SKILL_2 | 2 | `3*ATK+0.15*HP+3*DEF` |  |
| HERO_489 | SKILL_2 | 2 | `3.8*ATK+3*DEF+0.12*HP` |  |
| HERO_495 | SKILL_3 | 3 | `2.3*ATK+0.3*HP` | buff-dependent |
| HERO_496 | SKILL_4 | 4 | `1.6*ATK` |  |
| HERO_502 | SKILL_4 | 4 | `4.8*ATK+4*DEF` |  |
| HERO_509 | SKILL_3 | 3 | `3.5*DEF+0.2*HP+4.35*ATK` | buff-dependent |
| HERO_516 | SKILL_3 | 3 | `0.5*HP+4.2*ATK+1.5*ATK` | buff-dependent |
| HERO_524 | SKILL_1 | 1 | `3.6*ATK` |  |
| HERO_526 | SKILL_2 | 2 | `3.26*DEF+0.22*HP+1.9*ATK+0.04*HP` | buff-dependent |
| HERO_531 | SKILL_3 | 3 | `0.18*HP+5*ATK` | buff-dependent |
| Vergumkaar | Crushing Trample | 3 | `4.85*ATK+0.23*HP` | buff-dependent |
| HERO_536 | SKILL_3 | 3 | `6*ATK+0.18*HP` | buff-dependent |
| HERO_544 | SKILL_2 | 2 | `3.3*ATK+4.3*DEF+0.2*HP` | buff-dependent |
| HERO_551 | SKILL_1 | 1 | `4.4*ATK` | buff-dependent |
| Roxam | Chroma Shift | 1 | `3.8*ATK` |  |
| Roxam | Chameleon (Passive) | 4 | `2.65*DEF` |  |
| HERO_557 | SKILL_4 | 4 | `1.8*ATK` | buff-dependent |
| HERO_563 | SKILL_3 | 3 | `3.4*ATK+0.24*HP+3.6*DEF` | buff-dependent |
| Iron Brago | Fearless Charge | 2 | `0.6*TRG_HP+2.5*ATK` | target HP/stat, buff-dependent |
| HERO_571 | SKILL_1 | 1 | `3.2*ATK+0.05*HP` |  |
| HERO_578 | SKILL_3 | 3 | `4*ATK+3.6*DEF` |  |
| HERO_579 | SKILL_4 | 4 | `1.6*ATK` |  |
| HERO_584 | SKILL_4 | 4 | `4.9*ATK+0.3*TRG_HP` | target HP/stat, buff-dependent |
| HERO_593 | SKILL_2 | 2 | `6.6*ATK+3.65*DEF` | buff-dependent |
| HERO_598 | SKILL_4 | 4 | `3.2*DEF` | buff-dependent |
| HERO_603 | SKILL_2 | 2 | `5.5*ATK` |  |
| HERO_604 | SKILL_3 | 3 | `3.1*DEF+3.8*ATK` |  |
| HERO_610 | SKILL_2 | 2 | `4.82*ATK+0.2*HP+0.3*HP` | buff-dependent |
| HERO_615 | SKILL_4 | 4 | `4.2*ATK` |  |
| HERO_617 | SKILL_4 | 4 | `4*DEF+0.2*HP+3.3*ATK` |  |
| HERO_622 | SKILL_4 | 4 | `3.5*ATK+4.1*DEF+0.24*HP` | buff-dependent |
| HERO_628 | SKILL_1 | 1 | `2.4*ATK` |  |
| HERO_629 | SKILL_2 | 2 | `2*ATK+0.2*HP` |  |
| HERO_630 | SKILL_4 | 4 | `1.9*ATK+3*DEF+1.35*ATK` | buff-dependent |
| HERO_635 | SKILL_6 | 6 | `0.5*TRG_HP+1.5*ATK` | target HP/stat, buff-dependent |
| HERO_642 | SKILL_3 | 3 | `3.85*ATK+1.6*DEF+0.15*TRG_HP` | target HP/stat, buff-dependent |
| HERO_647 | SKILL_4 | 4 | `4.4*ATK+0.15*TRG_HP` | target HP/stat, buff-dependent |
| HERO_650 | SKILL_1 | 1 | `3.9*ATK+3.7*DEF+0.1*HP+0.5*HP` |  |
| HERO_656 | SKILL_1 | 1 | `7*ATK+3.9*DEF` |  |
| HERO_657 | SKILL_4 | 4 | `1.2*ATK` |  |
| HERO_665 | SKILL_4 | 4 | `1*HP+3.6*ATK` | buff-dependent |
| HERO_671 | SKILL_2 | 2 | `4*ATK+2*DEF+0.3*HP` | buff-dependent |
| HERO_682 | SKILL_4 | 4 | `0.14*HP+1.7*ATK` |  |
| HERO_684 | SKILL_2 | 2 | `1.95*ATK+3.1*DEF+0.3*HP` |  |
| HERO_693 | SKILL_2 | 2 | `1.8*ATK+3*DEF` | buff-dependent |
| HERO_695 | SKILL_1 | 1 | `3.4*ATK+0.2*HP` |  |
| HERO_697 | SKILL_1 | 1 | `1.7*ATK` | buff-dependent |
| HERO_701 | SKILL_1 | 1 | `2.1*DEF+0.2*HP+7*ATK` |  |
| HERO_708 | SKILL_2 | 2 | `0.5*HP+0.05*HP+3.5*DEF` |  |
| HERO_709 | SKILL_3 | 3 | `2.5*DEF+0.22*HP` |  |
| Deliana | Magnificient (Passive, Cooldown: 4 turns) | 4 | `0.05*TRG_HP+0.5*HP+4.2*DEF+1.8*ATK` | target HP/stat, buff-dependent |
| HERO_718 | SKILL_2 | 2 | `4.6*ATK+3.6*DEF` | buff-dependent |
| HERO_720 | SKILL_1 | 1 | `1.8*DEF+5*ATK` |  |
| HERO_721 | SKILL_3 | 3 | `1.8*ATK+0.11*HP` | buff-dependent |
| HERO_722 | SKILL_4 | 4 | `0.35*HP+1.5*ATK` |  |
| HERO_724 | SKILL_2 | 2 | `2*ATK+0.1*HP+1.8*DEF` |  |
| HERO_725 | SKILL_2 | 2 | `3.7*DEF+4*ATK` | buff-dependent |
| HERO_731 | SKILL_3 | 3 | `0.15*HP+2.2*ATK+3.5*DEF` | buff-dependent |
| HERO_737 | SKILL_2 | 2 | `0.4*TRG_HP+2.5*DEF+3.75*ATK` | target HP/stat, buff-dependent |
| HERO_742 | SKILL_3 | 3 | `3*ATK` |  |
| HERO_744 | SKILL_3 | 3 | `2.5*DEF+0.4*TRG_HP+3.8*ATK` | target HP/stat |
| HERO_748 | SKILL_3 | 3 | `4.5*ATK` |  |
| HERO_749 | SKILL_4 | 4 | `0.4*HP` |  |
| Marichka the Unbreakable | Nurtured Friendship | 3 | `0.5*TRG_HP+3*ATK+1.85*DEF` | target HP/stat |
| HERO_756 | SKILL_2 | 2 | `3.9*DEF+0.2*HP` |  |
| Korugar Death-Bell | Conduit of Agonies | 3 | `3*ATK` |  |
| HERO_759 | SKILL_4 | 4 | `2.4*ATK` | buff-dependent |
| HERO_766 | SKILL_2 | 2 | `0.5*TRG_HP+4.5*ATK` | target HP/stat |
| HERO_769 | SKILL_1 | 1 | `1.6*ATK+0.2*HP` |  |
| HERO_769 | SKILL_4 | 4 | `2.4*ATK` |  |
| Quintus the Triumphant | Strip Away | 2 | `1.9*ATK` | buff-dependent |
| HERO_780 | SKILL_3 | 3 | `2.9*ATK+1*DEF+0.28*HP` |  |
| HERO_783 | SKILL_3 | 3 | `0.2*HP+0.45*SPD` |  |
| HERO_786 | SKILL_1 | 1 | `0.1*HP+2.2*ATK` |  |
| HERO_794 | SKILL_2 | 2 | `0.27*HP+1.2*ATK` | buff-dependent |
| HERO_806 | SKILL_3 | 3 | `2.9*ATK+0.15*TRG_HP` | target HP/stat |
| HERO_813 | SKILL_1 | 1 | `3*ATK+0.24*HP+1.8*DEF` |  |
| HERO_817 | SKILL_4 | 4 | `3*ATK+0.28*HP` |  |
| HERO_823 | SKILL_1 | 1 | `3.75*ATK` |  |
| HERO_824 | SKILL_3 | 3 | `3.9*ATK+0.1*HP` |  |
| HERO_829 | SKILL_2 | 2 | `3.8*ATK` |  |
| HERO_836 | SKILL_3 | 3 | `0.31*HP+2*ATK+0.18*HP` | buff-dependent |
| HERO_841 | SKILL_2 | 2 | `0.22*HP+1.1*ATK` |  |
| HERO_842 | SKILL_3 | 3 | `1.35*ATK+0.1*TRG_HP` | target HP/stat |
| HERO_844 | SKILL_1 | 1 | `3.7*ATK+0.5*TRG_HP` | target HP/stat, buff-dependent |
| HERO_849 | SKILL_3 | 3 | `4.1*ATK` | buff-dependent |
| HERO_850 | SKILL_3 | 3 | `0.1*TRG_HP+3.4*ATK+25+2.9*DEF` | target HP/stat, buff-dependent |
| HERO_855 | SKILL_3 | 3 | `1.1*ATK` | buff-dependent |
| HERO_858 | SKILL_1 | 1 | `3.2*ATK` |  |
| HERO_858 | SKILL_5 | 5 | `1.2*ATK+3*DEF` |  |
| HERO_862 | SKILL_5 | 5 | `0.25*HP+2*DEF+3.5*ATK` | buff-dependent |
| HERO_868 | SKILL_1 | 1 | `3.5*DEF+10*DEF+0.3*HP+2*ATK+2.1*ATK` |  |
| HERO_872 | SKILL_1 | 1 | `5.5*ATK` |  |
| HERO_872 | SKILL_4 | 4 | `2.5*DEF+0.03*TRG_HP` | target HP/stat |
| HERO_873 | SKILL_4 | 4 | `3.3*ATK+0.3*TRG_HP` | target HP/stat, buff-dependent |
| HERO_877 | SKILL_5 | 5 | `5.4*ATK` |  |
| HERO_878 | SKILL_4 | 4 | `2*TRG_HP+3.5*ATK+2.5*ATK` | target HP/stat, buff-dependent |
| HERO_882 | SKILL_4 | 4 | `3*ATK+0.3*TRG_HP` | target HP/stat, buff-dependent |
| HERO_886 | SKILL_5 | 5 | `0.18*HP` |  |
| HERO_891 | SKILL_2 | 2 | `0.26*HP+0.05*HP` |  |
| HERO_891 | SKILL_5 | 5 | `1.9*DEF+0.03*TRG_HP+3*ATK` | target HP/stat |
| HERO_895 | SKILL_2 | 2 | `2.65*ATK+0.29*HP+3*DEF+1*DEF` |  |
| HERO_897 | SKILL_4 | 4 | `0.3*HP` |  |
| HERO_899 | SKILL_2 | 2 | `0.05*HP+0.02*HP+4*ATK+0.23*HP` | buff-dependent |
| HERO_900 | SKILL_1 | 1 | `2.7*DEF+4.8*ATK` |  |
| HERO_911 | SKILL_2 | 2 | `3.8*ATK+0.2*HP` |  |
| HERO_912 | SKILL_3 | 3 | `0.10*TRG_HP` | target HP/stat |
| Branch-arm Lasair | SKILL_3 | 3 | `0.13*HP+0.09*HP` |  |
| HERO_917 | SKILL_3 | 3 | `4*ATK` |  |
| HERO_917 | SKILL_5 | 5 | `3.8*ATK+2.7*DEF` |  |
| HERO_918 | SKILL_3 | 3 | `2.5*DEF+0.1*TRG_HP+5*ATK` | target HP/stat |
| HERO_925 | SKILL_3 | 3 | `0.15*HP` |  |
| HERO_926 | SKILL_2 | 2 | `1.85*ATK+3.5*DEF` | buff-dependent |
| HERO_932 | SKILL_4 | 4 | `0.12*HP+3*ATK` | buff-dependent |
| HERO_935 | SKILL_5 | 5 | `3.5*DEF` |  |
| HERO_936 | SKILL_1 | 1 | `0.2*TRG_HP+2.8*ATK` | target HP/stat, buff-dependent |
| HERO_943 | SKILL_4 | 4 | `2*ATK+1.9*DEF+0.12*HP+0.25*HP` |  |
| HERO_949 | SKILL_2 | 2 | `4.2*ATK` |  |
| HERO_949 | SKILL_4 | 4 | `0.2*HP+3.2*ATK+0.1*HP` | buff-dependent |
| HERO_953 | SKILL_1 | 1 | `0.1*HP` |  |
| HERO_953 | SKILL_3 | 3 | `4.6*ATK` |  |
| HERO_954 | SKILL_2 | 2 | `0.1*HP` |  |
| HERO_962 | SKILL_3 | 3 | `5.5*ATK` |  |
| HERO_962 | SKILL_5 | 5 | `3.5*DEF+4.7*ATK+0.25*HP` | buff-dependent |
| HERO_967 | SKILL_2 | 2 | `0.2*TRG_HP+4*DEF+1.2*ATK` | target HP/stat, buff-dependent |
| HERO_968 | SKILL_2 | 2 | `1.8*DEF+1.2*ATK` |  |
| HERO_971 | SKILL_2 | 2 | `1.55*DEF` |  |
| HERO_971 | SKILL_4 | 4 | `4.1*ATK+0.4*HP` | buff-dependent |
| HERO_976 | SKILL_3 | 3 | `1*TRG_HP+3.7*ATK+4.1*DEF` | target HP/stat, buff-dependent |
| HERO_980 | SKILL_4 | 4 | `3.3*ATK` |  |
| HERO_984 | SKILL_5 | 5 | `1.7*DEF+4*ATK` |  |
| HERO_989 | SKILL_4 | 4 | `0.15*HP+0.03*HP+3.5*DEF` | buff-dependent |
| HERO_990 | SKILL_2 | 2 | `5.5*DEF` |  |
| HERO_990 | SKILL_3 | 3 | `4.8*ATK` | buff-dependent |
| HERO_994 | SKILL_2 | 2 | `6*ATK+1.7*DEF` | buff-dependent |
| HERO_1006 | SKILL_2 | 2 | `0.26*HP` |  |
| HERO_1006 | SKILL_3 | 3 | `0.38*HP` |  |
| HERO_1010 | SKILL_3 | 3 | `6*ATK+0.5*TRG_HP+7*DEF` | target HP/stat |
| HERO_1014 | SKILL_3 | 3 | `0.28*HP` |  |
| HERO_1019 | SKILL_3 | 3 | `4.4*DEF+2.6*ATK` | buff-dependent |
| HERO_1023 | SKILL_3 | 3 | `3.9*ATK+3.3*DEF` |  |
| HERO_1024 | SKILL_3 | 3 | `3.8*DEF+5*HP+1.35*ATK` | buff-dependent |
| HERO_1027 | SKILL_3 | 3 | `6*ATK+0.5*HP+3.5*DEF+0.1*TRG_HP` | target HP/stat |
| HERO_1031 | SKILL_3 | 3 | `0.5*TRG_HP` | target HP/stat |
| HERO_1035 | SKILL_1 | 1 | `4*ATK` |  |
| HERO_1035 | SKILL_4 | 4 | `0.21*HP` | buff-dependent |
| HERO_1036 | SKILL_2 | 2 | `0.15*HP+2.3*ATK` |  |
| HERO_1037 | SKILL_4 | 4 | `4.5*ATK` | buff-dependent |
| HERO_1040 | SKILL_4 | 4 | `3.5*DEF+4*ATK` | buff-dependent |
| HERO_1052 | SKILL_4 | 4 | `0.25*HP` |  |
| HERO_2100 | SKILL_1 | 1 | `1.7*ATK+0.1*HP+7.5*DEF` | buff-dependent |
| HERO_2106 | SKILL_3 | 3 | `3.4*ATK` |  |
| HERO_2107 | SKILL_2 | 2 | `2.1*ATK` |  |
| HERO_2108 | SKILL_3 | 3 | `2.8*ATK+0.1*HP+3.4*DEF` |  |
| HERO_2202 | SKILL_2 | 2 | `5.2*ATK` | buff-dependent |
| HERO_2214 | SKILL_1 | 1 | `4*ATK` |  |
| HERO_2222 | SKILL_4 | 4 | `1.8*ATK+1.2*DEF` | buff-dependent |
| HERO_2234 | SKILL_2 | 2 | `6*ATK` |  |
| HERO_2235 | SKILL_2 | 2 | `3*ATK` | buff-dependent |
| HERO_2239 | SKILL_1 | 1 | `0.5*HP+3*ATK` |  |
| HERO_2259 | SKILL_1 | 1 | `3*ATK` |  |
| HERO_2259 | SKILL_3 | 3 | `3*ATK+0.1*HP` | buff-dependent |
| HERO_2263 | SKILL_1 | 1 | `3*ATK+0.4*TRG_HP` | target HP/stat |
| HERO_2270 | SKILL_2 | 2 | `0.12*HP` |  |
| HERO_2275 | SKILL_4 | 4 | `3*ATK+4*ATK+0.15*HP+1*TRG_HP+0.4*HP` | target HP/stat |
| HERO_2281 | SKILL_8 | 8 | `0.01*TRG_HP+2.7*ATK` | target HP/stat |
| HERO_2282 | SKILL_3 | 3 | `2.7*ATK` |  |
| HERO_2290 | SKILL_1 | 1 | `3.1*ATK+2.1*DEF+0.5*HP` |  |
| HERO_2295 | SKILL_5 | 5 | `2.5*ATK` |  |
| HERO_2300 | SKILL_6 | 6 | `4*DEF` |  |
| HERO_2301 | SKILL_1 | 1 | `0.4*TRG_HP+4*ATK+0.15*HP` | target HP/stat |
| HERO_2307 | SKILL_2 | 2 | `4*ATK` |  |
| HERO_2311 | SKILL_1 | 1 | `3.1*ATK` | buff-dependent |
| HERO_2321 | SKILL_2 | 2 | `4*ATK+0.15*HP+1*TRG_HP` | target HP/stat |
| HERO_2327 | SKILL_5 | 5 | `3*ATK` |  |
| HERO_2560 | SKILL_2 | 2 | `3.1*ATK+0.03*TRG_HP` | target HP/stat |
| HERO_2565 | SKILL_1 | 1 | `0.1*TRG_HP+7*ATK` | target HP/stat, buff-dependent |
| HERO_2569 | SKILL_1 | 1 | `3*ATK` | buff-dependent |
| HERO_2612 | SKILL_1 | 1 | `4.9*ATK+0.1*HP+0.3*TRG_HP` | target HP/stat, buff-dependent |
| HERO_2624 | SKILL_3 | 3 | `0.1*HP+5*ATK+0.4*HP+0.03*TRG_HP+0.8*HP+0.2*HP` | target HP/stat |
| HERO_2652 | SKILL_4 | 4 | `0.45*HP+6*ATK+1*TRG_HP` | target HP/stat |
| HERO_2696 | SKILL_2 | 2 | `5*ATK+1*TRG_HP` | target HP/stat, buff-dependent |
| HERO_2702 | SKILL_6 | 6 | `0.05*HP+6.5*ATK` |  |
| HERO_2706 | SKILL_3 | 3 | `0.3*TRG_HP+2*ATK+5*DEF` | target HP/stat, buff-dependent |
| HERO_5001 | SKILL_31 | 31 | `0.15*HP+3*ATK+0*HP` | buff-dependent |
| HERO_5002 | SKILL_64 | 64 | `0.1*HP+3.5*DEF+2.7*ATK` | buff-dependent |
| HERO_6001 | SKILL_30 | 30 | `1.4*DEF` |  |
| HERO_7000 | SKILL_18 | 18 | `0.15*HP+1.9*ATK` | buff-dependent |
| HERO_7002 | SKILL_13 | 13 | `0.25*HP+1.3*ATK` |  |
| HERO_8822 | SKILL_3 | 3 | `2.7*ATK+0.12*HP` | buff-dependent |
| HERO_8823 | SKILL_2 | 2 | `0.25*HP+2.5*ATK` |  |
| HERO_8824 | SKILL_3 | 3 | `3.6*DEF+0.5*HP+6*HP` |  |
| HERO_8852 | SKILL_4 | 4 | `3.6*DEF` | buff-dependent |
| HERO_8857 | SKILL_4 | 4 | `3.6*DEF+0.2*HP` |  |
| HERO_8877 | SKILL_3 | 3 | `0.27*HP+0.7*ATK+3.4*DEF+63.7*DEF+0.13*HP` | buff-dependent |
| HERO_8927 | SKILL_4 | 4 | `1.8*DEF+0.28*HP+1.85*ATK` | buff-dependent |
| HERO_22140 | SKILL_13 | 13 | `5*ATK` |  |
| HERO_22668 | SKILL_4 | 4 | `3*ATK` |  |
| HERO_22669 | SKILL_2 | 2 | `7*ATK+5*ATK` | buff-dependent |
| HERO_22669 | SKILL_6 | 6 | `0.005*HP+3*ATK+1*TRG_HP` | target HP/stat |
| HERO_42669 | SKILL_1 | 1 | `3*ATK+0.25*TRG_HP+0.27*HP` | target HP/stat, buff-dependent |
