"""Six tasks with a person's game running: the agent needs what only the running game holds.

The harness starts the stack headless with a console on a loopback port, makes the
person's live edits there with `config.set` (they live only in the game, unsaved), and
then starts the agent. Four tasks ask the agent to keep the person's live tuning, or the
part of it that passes the objectives; two ask for an A/B in the game: a snapshot named
`before`, then the fix, left on in the game, with the person's own tuning kept.

Each live edit below was checked with `sim --seeds 1-3`, alone: "keep" passes, "drop"
fails. Success adds to the first run's judge (check 0, sim 0, planted files unchanged):
- `expect`: values the headless data must give afterwards (`eval "{config.get PATH}"`).
- `live_expect`: values the running game must give afterwards.
- `ab`: the running game shows the same value for the path as the headless data (the fix
  is on), and after `{config.restore before}` it shows the planted value again.
"""

TASKS_LIVE = [
    dict(id="live-cube-keep", stack="cube",
         live={"cube.spin": 120, "cube.tilt": 35},
         expect={"cube.spin": 120, "cube.tilt": 35},
         ask="I've been tuning the cube in the running game and I like where it is now. Make my "
             "live tuning stick, so it survives a restart, and check it still passes."),
    dict(id="live-duel-keep-some", stack="duel",
         live={"duel.hit_pause": 8, "fighters.kestrel.moves.heavy.blockstun": 16,
               "cpu.hard.reaction": 40, "fighters.kestrel.moves.jab.damage": 45},
         expect={"duel.hit_pause": 8, "fighters.kestrel.moves.heavy.blockstun": 16,
                 "cpu.hard.reaction": 12, "fighters.kestrel.moves.jab.damage": 30},
         ask="I tried some changes live in the running Duel. Keep the ones that don't break an "
             "objective, so they survive a restart, and drop the rest. Tell me which you kept and why."),
    dict(id="live-ledger-keep-some", stack="ledger",
         live={"econ.recovery": 0.3, "goods.bread.base_price": 60, "buildings.mill.cost": 4000,
               "econ.start_money": 1500},
         expect={"econ.recovery": 0.3, "goods.bread.base_price": 60, "buildings.mill.cost": 1500,
                 "econ.start_money": 1500},
         ask="I tried some changes live in the running Ledger. Keep the ones that don't break an "
             "objective, so they survive a restart, and drop the rest. Tell me which you kept, and "
             "the sheet cell for any economy value."),
    dict(id="live-wayfarer-keep-some", stack="wayfarer",
         live={"wayfarer.run_speed": 7, "wayfarer.glide_sink": 2.4, "wayfarer.climb_max": 6},
         expect={"wayfarer.run_speed": 7, "wayfarer.glide_sink": 2, "wayfarer.climb_max": 8},
         ask="I tried some traversal changes live in the running Wayfarer. Keep the ones that don't "
             "break an objective, so they survive a restart, and drop the rest. Tell me which and why."),
    dict(id="live-cube-ab", stack="cube", file="data/default.dta", old="(spin 45 ", new="(spin 400 ",
         live={"cube.tilt": 35}, live_expect={"cube.tilt": 35},
         ab=("cube.spin", 400),
         ask="The cube spins far too fast. Before you change anything, save a snapshot of the running "
             "game named `before` so I can compare. Then fix it, and leave the running game showing "
             "your fix, with my own live tuning still in place."),
    dict(id="live-duel-ab", stack="duel", file="data/default.dta", old="(easy   (reaction 30)",
         new="(easy   (reaction 4)", live={"duel.hit_pause": 8}, live_expect={"duel.hit_pause": 8},
         ab=("cpu.easy.reaction", 4),
         ask="Players say Duel's easy CPU blocks things nobody could react to. Before you change "
             "anything, save a snapshot of the running game named `before` so I can compare. Then fix "
             "it, and leave the running game showing your fix, with my own live tuning still in place."),
]
