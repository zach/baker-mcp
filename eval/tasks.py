"""The twelve tasks: a fault planted in a copy of a stack's data, and what a person would say.

Each task copies a stack, replaces one piece of text in its data (the fault), and asks the
agent to make the stack's objectives pass again by editing data/agent.dta only. Success is
judged by the stack itself: `check` exits 0, `sim --seeds 1-3` exits 0 over every scenario,
and the planted files are byte for byte as planted (default.dta and generated files are
never edited).
"""

TASKS = [
    dict(id="cube-spin", stack="cube", file="data/default.dta",
         old="(spin 45 ", new="(spin 400 ",
         ask="The cube is a blur when it spins and the turn scenario fails. Fix it."),
    dict(id="duel-infinite", stack="duel", file="data/default.dta",
         old="(damage 30)\n                    (hitstun 12)", new="(damage 30)\n                    (hitstun 40)",
         ask="Testers found a combo in Duel that never ends. Find it and fix the frame data."),
    dict(id="duel-block", stack="duel", file="data/default.dta",
         old="(hitstun 20) (blockstun 14)", new="(hitstun 20) (blockstun 26)",
         ask="In Duel a blocked attack no longer gives the turn back. Fix the frame data."),
    dict(id="duel-hard-cpu", stack="duel", file="data/default.dta",
         old="(hard   (reaction 12) (block 0.6)", new="(hard   (reaction 45) (block 0.05)",
         ask="Duel's hard CPU has become a pushover for players who know the combos. Retune the hard difficulty."),
    dict(id="duel-easy-reaction", stack="duel", file="data/default.dta",
         old="(easy   (reaction 30)", new="(easy   (reaction 4)",
         ask="Players say the easy CPU blocks things nobody could react to. Fix it."),
    dict(id="ledger-prices", stack="ledger", file="data/economy.dta",
         old="(bread (base_price 40)", new="(bread (base_price 4)",
         ask="Ledger's price table looks broken since the last sheet export: the economy is off pace. "
             "Find the bad value, fix it in your layer, and say which sheet cell to correct."),
    dict(id="ledger-mill", stack="ledger", file="data/economy.dta",
         old="(mill (cost 1500)", new="(mill (cost 15000)",
         ask="In Ledger the first mill comes far too late. Fix it in your layer and name the sheet cell."),
    dict(id="contraption-bounce", stack="contraption", file="data/default.dta",
         old="(friction 0.4) (bounce 0.2)", new="(friction 0.4) (bounce 0.95)",
         ask="Contraption's levels stopped solving: the ball will not stay in the bucket. Fix it."),
    dict(id="stuntline-gap", stack="stuntline", file="data/default.dta",
         old="(gap_8       (kind gap) (length 8)", new="(gap_8       (kind gap) (length 16)",
         ask="Stuntline's canyon jump fails its objectives. Fix the track kit."),
    dict(id="hearth-energy", stack="hearth", file="data/default.dta",
         old="(energy  (decay_per_hour 4.5)", new="(energy  (decay_per_hour 30)",
         ask="Hearth's villagers are exhausted and stuck all day. Fix the needs."),
    dict(id="wayfarer-glide", stack="wayfarer", file="data/default.dta",
         old="(glide_sink 2 ", new="(glide_sink 4 ",
         ask="In Wayfarer the glides no longer make it. Fix the traversal tuning."),
    dict(id="wayfarer-climb", stack="wayfarer", file="data/default.dta",
         old="(climb_max 8 ", new="(climb_max 4 ",
         ask="Wayfarer's world proof fails after a traversal change. Find the cause and fix it."),
]
