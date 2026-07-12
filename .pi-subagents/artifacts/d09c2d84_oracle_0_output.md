I now have complete, definitive evidence. Here is my analysis:

---

## Inherited decisions
- The tool calculates battery health as `max_capacity / design_capacity * 100`
- `max_capacity` is read from the IOKit key `AppleRawMaxCapacity`
- `design_capacity` is read from the IOKit key `DesignCapacity`
- The tool's primary purpose is to cycle the battery until health drops below 80% (the AppleCare warranty replacement threshold), defaulting to a 79% target

## Diagnosis

**There is a confirmed, critical bug.** The tool reads the wrong IOKit key for maximum capacity when calculating battery health.

On this machine (the actual development Mac), I verified the raw IOKit values via `ioreg` and compared against `system_profiler SPPowerDataType` (System Report):

| IOKit Key | Value (mAh) | What it represents |
|---|---|---|
| `AppleRawMaxCapacity` | 7961 | Raw hardware gauge reading (what the tool uses) |
| `NominalChargeCapacity` | 8205 | Adjusted/smoothed value (what System Report uses) |
| `DesignCapacity` | 8579 | Original design capacity |

- **Tool calculates**: `7961 / 8579 * 100 = 92.8%`
- **System Report shows**: `96%` (which is `8205 / 8579 * 100 = 95.6%`, rounded up)
- **Discrepancy: ~3 percentage points**

`AppleRawMaxCapacity` is the raw fuel-gauge reading from the battery's gas gauge IC. `NominalChargeCapacity` is the smoothed/adjusted value that Apple's own software uses for the "Maximum Capacity" percentage in System Report. They consistently differ because Apple applies its own filtering/adjustment on top of the raw reading.

**Why this is critical for the tool's purpose:**

When the tool reaches its default 79% target (using `AppleRawMaxCapacity`), System Report would still show approximately **81.4%** — *above* the 80% AppleCare warranty threshold. The user would stop cycling, take the Mac to Apple, and Apple would deny the replacement because their System Report still says the battery is healthy.

## Drift / contradiction check

No drift from inherited decisions — the bug is *in* the inherited design, not a deviation from it. The code correctly implements `max_capacity / design_capacity * 100`, but the choice of `AppleRawMaxCapacity` as the source for `max_capacity` is wrong for the health calculation. The same `max_capacity` field is also used for the `battery_percentage` calculation, where `AppleRawMaxCapacity` is actually the more appropriate denominator (since `AppleRawCurrentCapacity / AppleRawMaxCapacity` gives the raw state-of-charge that tracks the system's percentage display closely).

## Additional bugs found

1. **Unchecked `GetDictInt`/`GetDictBool` return values** (`c/power_sources.c`): If any IOKit key is missing, the corresponding struct field silently stays at 0. For `design_capacity = 0`, this causes a `ZeroDivisionError` crash in Python. For other fields, it produces silently wrong values.

2. **Version mismatch**: `meson.build` declares version `0.2.1` while `pyproject.toml` declares `0.2.3`.

## Recommendation

**Fix the health calculation to use `NominalChargeCapacity` instead of `AppleRawMaxCapacity`.**

The cleanest approach: add a separate `nominal_capacity` field to the `BatteryInfo` struct and the CFFI definition, read `NominalChargeCapacity` into it, and use it specifically for the health calculation while keeping `AppleRawMaxCapacity` for the percentage calculation. This requires changes to:
- `c/power_sources.h` — add `nominal_capacity` field
- `c/power_sources.c` — add `kNominalCapacityKey` and read it
- `c/build_iokit.py` — add the field to the CFFI `cdef`
- `src/batterytool/iokit_wrapper.pyi` — add the field to the stub
- `src/batterytool/loop.py` — change health calc to use `nominal_capacity`
- `src/batterytool/main.py` — change health calc to use `nominal_capacity`
- `tests/conftest.py` and `tests/test_main.py` — update fake data

A simpler alternative: change `kMaxCapacityKey` from `"AppleRawMaxCapacity"` to `"NominalChargeCapacity"`. This fixes the health calc (the critical bug) and only introduces a ~0.8% error in the percentage calculation (28.0% vs 27.2% vs system's 29%), which is negligible for the 5%/95% charge thresholds.

## Risks

- `NominalChargeCapacity` availability: confirmed present on this Apple Silicon MacBook. It is a standard `AppleSmartBattery` IOKit key, but should be verified across other Apple Silicon models.
- The ratio between `AppleRawMaxCapacity` and `NominalChargeCapacity` may vary across machines and over time. The ~3% gap observed here could be larger or smaller on other batteries.
- If the simple fix (swapping the key) is chosen, the percentage calculation becomes slightly less accurate, but this is acceptable given the wide 5%/95% thresholds.

## Need from main agent

None — the diagnosis is complete and conclusive.

## Suggested execution prompt

A worker handoff IS warranted to implement the fix:

```
Fix the battery health calculation bug in BatteryTool. The tool currently uses the IOKit key `AppleRawMaxCapacity` for the health calculation, but macOS System Report uses `NominalChargeCapacity`. These differ by ~3 percentage points, causing the tool to underreport health. This means the tool reaches its 79% target when System Report still shows ~81%, defeating the tool's purpose of getting below the 80% AppleCare warranty threshold.

Preferred approach (simplest): In `c/power_sources.c`, change `kMaxCapacityKey` from `"AppleRawMaxCapacity"` to `"NominalChargeCapacity"`. Update `tests/conftest.py` FAKE_BATTERY_INFO and `tests/test_main.py` expectations accordingly to reflect that `max_capacity` now comes from `NominalChargeCapacity`.

Also fix the secondary bug: check the return values of `GetDictInt()` and `GetDictBool()` in `FetchBatteryInfo()` and handle failures (e.g., log a warning or return an error indicator) instead of silently using 0.

Do NOT change the health formula itself (`max_capacity / design_capacity * 100`) — only change which IOKit key populates `max_capacity`.
```