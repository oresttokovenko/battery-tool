### BatteryTool

AppleCare will replace your MacBook battery for free if it drops below 80% health. Mine was at 81% with two weeks of coverage left. So I wrote a tool to fix that.

BatteryTool cycles your battery on autopilot -- discharge to 5%, charge to 95%, check health, repeat -- until you cross the 80% threshold. Leave it plugged in, go about your life, come back to a warranty-eligible battery. I wrote about the whole process [here](https://oresttokovenko.com/blog/macbook-battery-replacement/).

> If you purchased an AppleCare Protection Plan for your Mac laptop and your battery retains less than 80 percent of its original capacity, Apple will replace the battery at no charge.

Only tested on Apple Silicon MacBooks running macOS 15.

#### Before you start

1. Turn off "Optimized Battery Charging" in System Settings > Battery (Apple will fight you otherwise)
2. Install [Caffeine](https://intelliscapesolutions.com/apps/caffeine) or something similar so your Mac doesn't fall asleep mid-cycle
3. Plug in your MacBook

#### Installation

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) if you don't have it
2. Clone and install:
   ```bash
   git clone https://github.com/oresttokovenko/battery-tool.git
   cd battery-tool
   uv tool install git+https://github.com/oresttokovenko/battery-tool
   ```

#### Usage

Needs root to talk to the SMC.

```bash
sudo uvx batterytool
```

#### Options

| Flag | What it does | Default |
|------|-------------|---------|
| `--target-health` | Stop when health drops to this % | `79` |
| `--max-charge` | Charge up to this % before discharging | `95` |
| `--min-charge` | Discharge down to this % before charging | `5` |
| `--interval` | How often to check battery, in seconds | `60` |
| `--log-file` | Write logs to a file | None |
| `--dry-run` | Print what would happen, don't touch the SMC | `False` |
| `--status` | Print current battery stats and exit | `False` |
| `--monitor-only` | Watch the battery without controlling it | `False` |
| `--force` | Skip the "is the charger plugged in?" check | `False` |

#### How it works

The SMC (System Management Controller) controls battery charging on Macs. Apple doesn't document its keys, but people have [reverse-engineered them](https://github.com/zackelia/bclm/issues/20). The tool writes to these keys to disable charging and force discharge while the laptop stays plugged in.

The cycle looks like this:
1. Write to `CH0B`/`CH0C`/`CH0I` (or `CHTE`/`CHIE` on macOS 15.7+) to block charging and force discharge
2. Wait for the battery to drain to `--min-charge`
3. Re-enable charging, wait until `--max-charge`
4. Check health (max capacity / design capacity)
5. If health is still above `--target-health`, go to 1
6. On any exit -- Ctrl+C, crash, target reached -- charging gets re-enabled. Your battery won't get stuck in a weird state.

In my case, it took about 85 cycles over 10 days to go from 81% to 79%.

#### Acknowledgements

- [battery.sh](https://github.com/actuallymentor/battery/blob/main/battery.sh) by [Actually Mentor](https://github.com/actuallymentor) -- the battery management logic started here
- [smc-command](https://github.com/hholtmann/smcFanControl/tree/master/smc-command) by [hholtmann](https://github.com/hholtmann) -- for talking to the SMC
- [bclm](https://github.com/zackelia/bclm) -- for figuring out which SMC keys control charging
