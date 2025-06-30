![image](https://github.com/user-attachments/assets/195f0cc4-f9cd-4308-abd5-28a59d05a540)

<h2>D&D Tools!</h2>

This project packages together a collection of software tools we use when playing D&D and building campaigns and such, with a browser-based interface for actually using the tools.

As of now, it includes the following tools:
- A die roller, which uses a carefully crafted parser to interpret arbitrary strings as die-notations and roll the corresponding numbers (`16d6+7d9 - 14d54+1708d64+ 123d2-76` will work, for instance)
- A character/npc backstory generator, which produces essential character information (species, occupation, background, etc.), life history information including family, home life, and upbringing, notable life events, and known people. The material form which the generator is drawn are tables in the 5e DMG and XGE, with a substantial amount of logic to ensure consistency.
- A minor magic item generator, with properties and quirks drawn from the DMG, minor magic items list, and cantrips, plus additional flavor based on the maker of the item and a list of item bases augmented by variable property tags (like color, material, style, and the like)
- A combat manager which tracks an arbitrary number of combatant cards containing hit points, armor class, attack damage, and turn-based conditions.
  -  Added cards include functions to take damage, heal, or add a duration-based condition based on a numeric input box.
  -  Turn-based execution advances by-card and keeps all cards in sorted initiative order, and updates condition timers. Conditions can be removed by clicking on the counters
  -  Cards are also marked when hp drops below 0.
  -  Further, when a card's attack rolls are clicked, those rolls are automatically made, and whenever any roll is made, the result is loaded into all cards' input box for easy and rapid application of damage and healing
- A history save feature which writes all the currently run generator and roll outputs to the local disk, so that roll sequences, made items, or backgrounds can be reviewed later, as well as a history clear function to remove clutter there
- A combat manager save and load function which saves the current combatant cards, turn order, and conditons to localStorage, so that an encounter can be paused and then re-loaded in-browser later, as well as a combat manager clear function
- Pleasant and fun header poster images and splash placeholders for before results are generated.

Features in progress include:
- A utility to run die roll experiments when including empowering, where a number of low rolls can be re-rolled and the new total used (examining the effects over a large number of trials)
- Setting the name of a generated character backstory to keep named NPCs around



