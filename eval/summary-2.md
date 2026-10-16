| arm | success | calls (mean) | calls (median) | tokens, all (mean) | output tokens (mean) | wall (mean) | cost (total) |
|---|---|---|---|---|---|---|---|
| claude headless bridge_eval | 30/36 | 9.3 | 9 | 104k | 2.0k | 113 s | $2.60 |
| claude live bridge | 14/18 | 13.2 | 13 | 183k | 2.2k | 100 s | $1.76 |
| claude live cli | 15/18 | 4.4 | 4 | 70k | 1.6k | 51 s | $1.22 |
| opencode headless bridge | 33/36 | 11.9 | 10 | 225k | 2.7k | 116 s | $4.94 |
| opencode headless cli | 33/36 | 6.0 | 6 | 120k | 2.3k | 134 s | $3.18 |
| opencode live bridge | 18/18 | 17.4 | 16 | 254k | 2.9k | 176 s | $2.19 |
| opencode live cli | 17/18 | 8.0 | 6 | 162k | 3.3k | 148 s | $1.88 |

| task | arm | success | calls (mean) | calls (median) | tokens, all (mean) | output tokens (mean) | wall (mean) | cost (total) |
|---|---|---|---|---|---|---|---|---|
| contraption-bounce | claude headless bridge_eval | 3/3 | 12.0 | 13 | 119k | 1.8k | 219 s | $0.17 |
| contraption-bounce | opencode headless bridge | 3/3 | 19.0 | 21 | 306k | 3.6k | 225 s | $0.41 |
| contraption-bounce | opencode headless cli | 3/3 | 8.7 | 9 | 177k | 2.7k | 397 s | $0.30 |
| cube-spin | claude headless bridge_eval | 3/3 | 7.0 | 7 | 61k | 1.2k | 31 s | $0.14 |
| cube-spin | opencode headless bridge | 3/3 | 8.7 | 9 | 96k | 1.4k | 39 s | $0.23 |
| cube-spin | opencode headless cli | 3/3 | 3.7 | 4 | 59k | 1.1k | 34 s | $0.15 |
| duel-block | claude headless bridge_eval | 1/3 | 8.3 | 8 | 82k | 1.9k | 77 s | $0.25 |
| duel-block | opencode headless bridge | 3/3 | 9.7 | 9 | 197k | 2.8k | 94 s | $0.45 |
| duel-block | opencode headless cli | 2/3 | 4.7 | 5 | 90k | 2.1k | 64 s | $0.24 |
| duel-easy-reaction | claude headless bridge_eval | 3/3 | 7.3 | 7 | 96k | 1.7k | 93 s | $0.23 |
| duel-easy-reaction | opencode headless bridge | 2/3 | 14.7 | 15 | 367k | 3.2k | 92 s | $0.56 |
| duel-easy-reaction | opencode headless cli | 3/3 | 5.3 | 4 | 113k | 2.2k | 82 s | $0.26 |
| duel-hard-cpu | claude headless bridge_eval | 1/3 | 11.3 | 10 | 166k | 3.1k | 138 s | $0.37 |
| duel-hard-cpu | opencode headless bridge | 3/3 | 14.0 | 13 | 330k | 3.9k | 109 s | $0.59 |
| duel-hard-cpu | opencode headless cli | 3/3 | 7.3 | 8 | 172k | 3.2k | 90 s | $0.34 |
| duel-infinite | claude headless bridge_eval | 1/3 | 9.7 | 9 | 88k | 2.2k | 140 s | $0.17 |
| duel-infinite | opencode headless bridge | 1/3 | 11.0 | 11 | 269k | 3.1k | 154 s | $0.49 |
| duel-infinite | opencode headless cli | 1/3 | 7.7 | 6 | 157k | 2.7k | 139 s | $0.29 |
| hearth-energy | claude headless bridge_eval | 3/3 | 7.7 | 7 | 91k | 1.4k | 242 s | $0.15 |
| hearth-energy | opencode headless bridge | 3/3 | 16.3 | 16 | 378k | 2.8k | 309 s | $0.46 |
| hearth-energy | opencode headless cli | 3/3 | 6.0 | 6 | 114k | 1.8k | 473 s | $0.29 |
| ledger-mill | claude headless bridge_eval | 3/3 | 10.7 | 11 | 107k | 2.0k | 49 s | $0.21 |
| ledger-mill | opencode headless bridge | 3/3 | 10.3 | 10 | 175k | 2.3k | 54 s | $0.39 |
| ledger-mill | opencode headless cli | 3/3 | 6.3 | 5 | 127k | 2.2k | 42 s | $0.26 |
| ledger-prices | claude headless bridge_eval | 3/3 | 7.0 | 7 | 79k | 1.8k | 40 s | $0.17 |
| ledger-prices | opencode headless bridge | 3/3 | 8.7 | 9 | 100k | 2.3k | 46 s | $0.25 |
| ledger-prices | opencode headless cli | 3/3 | 6.7 | 6 | 127k | 2.4k | 46 s | $0.27 |
| live-cube-ab | claude live bridge | 3/3 | 10.7 | 11 | 73k | 1.6k | 32 s | $0.14 |
| live-cube-ab | claude live cli | 3/3 | 4.3 | 5 | 56k | 1.2k | 29 s | $0.15 |
| live-cube-ab | opencode live bridge | 3/3 | 13.7 | 15 | 105k | 1.9k | 64 s | $0.25 |
| live-cube-ab | opencode live cli | 3/3 | 3.7 | 4 | 57k | 1.3k | 57 s | $0.15 |
| live-cube-keep | claude live bridge | 3/3 | 7.0 | 7 | 62k | 1.0k | 28 s | $0.11 |
| live-cube-keep | claude live cli | 3/3 | 3.7 | 4 | 47k | 1.0k | 22 s | $0.13 |
| live-cube-keep | opencode live bridge | 3/3 | 11.3 | 11 | 75k | 1.7k | 71 s | $0.19 |
| live-cube-keep | opencode live cli | 3/3 | 4.7 | 5 | 64k | 1.4k | 64 s | $0.16 |
| live-duel-ab | claude live bridge | 2/3 | 16.0 | 16 | 200k | 2.9k | 146 s | $0.41 |
| live-duel-ab | claude live cli | 3/3 | 5.7 | 6 | 86k | 1.6k | 50 s | $0.22 |
| live-duel-ab | opencode live bridge | 3/3 | 23.3 | 25 | 258k | 4.2k | 191 s | $0.41 |
| live-duel-ab | opencode live cli | 3/3 | 6.7 | 7 | 133k | 2.9k | 125 s | $0.30 |
| live-duel-keep-some | claude live bridge | 0/3 | 15.3 | 18 | 299k | 2.8k | 190 s | $0.44 |
| live-duel-keep-some | claude live cli | 0/3 | 4.7 | 5 | 81k | 2.2k | 94 s | $0.25 |
| live-duel-keep-some | opencode live bridge | 3/3 | 23.7 | 24 | 553k | 4.4k | 406 s | $0.62 |
| live-duel-keep-some | opencode live cli | 2/3 | 19.3 | 16 | 455k | 8.5k | 435 s | $0.65 |
| live-ledger-keep-some | claude live bridge | 3/3 | 17.0 | 17 | 281k | 2.7k | 96 s | $0.38 |
| live-ledger-keep-some | claude live cli | 3/3 | 4.3 | 4 | 75k | 1.8k | 53 s | $0.24 |
| live-ledger-keep-some | opencode live bridge | 3/3 | 17.3 | 17 | 286k | 3.1k | 155 s | $0.38 |
| live-ledger-keep-some | opencode live cli | 3/3 | 6.7 | 7 | 134k | 2.5k | 95 s | $0.29 |
| live-wayfarer-keep-some | claude live bridge | 3/3 | 13.3 | 13 | 186k | 2.1k | 109 s | $0.29 |
| live-wayfarer-keep-some | claude live cli | 3/3 | 4.0 | 4 | 74k | 1.6k | 57 s | $0.23 |
| live-wayfarer-keep-some | opencode live bridge | 3/3 | 15.0 | 15 | 249k | 2.4k | 169 s | $0.35 |
| live-wayfarer-keep-some | opencode live cli | 3/3 | 7.0 | 6 | 128k | 3.1k | 109 s | $0.33 |
| stuntline-gap | claude headless bridge_eval | 3/3 | 9.3 | 9 | 86k | 1.8k | 127 s | $0.16 |
| stuntline-gap | opencode headless bridge | 3/3 | 9.3 | 9 | 147k | 2.1k | 112 s | $0.33 |
| stuntline-gap | opencode headless cli | 3/3 | 5.0 | 5 | 89k | 2.1k | 95 s | $0.24 |
| wayfarer-climb | claude headless bridge_eval | 3/3 | 11.7 | 11 | 131k | 2.6k | 102 s | $0.26 |
| wayfarer-climb | opencode headless bridge | 3/3 | 12.3 | 11 | 164k | 2.6k | 60 s | $0.36 |
| wayfarer-climb | opencode headless cli | 3/3 | 7.3 | 7 | 144k | 2.8k | 67 s | $0.30 |
| wayfarer-glide | claude headless bridge_eval | 3/3 | 10.0 | 11 | 145k | 2.2k | 95 s | $0.34 |
| wayfarer-glide | opencode headless bridge | 3/3 | 8.7 | 8 | 172k | 2.0k | 103 s | $0.42 |
| wayfarer-glide | opencode headless cli | 3/3 | 3.7 | 4 | 77k | 1.7k | 79 s | $0.23 |
