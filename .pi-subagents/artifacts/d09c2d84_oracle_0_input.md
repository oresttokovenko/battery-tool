# Task for oracle

You are a delegated subagent running from a fork of the parent session. Treat the inherited conversation as reference-only context, not a live thread to continue. Do not continue or answer prior messages as if they are waiting for a reply. Your sole job is to execute the task below and return a focused result for that task using your tools.

Task:
Investigate potential bugs in BatteryTool that could cause a discrepancy between the battery health percentage reported by the tool and the health percentage shown in macOS System Report.

The tool calculates health as `max_capacity / design_capacity * 100` where both values come from IOKit's AppleSmartBattery dictionary. The Python code is in src/batterytool/battery.py, src/batterytool/loop.py, src/batterytool/main.py, src/batterytool/constants.py. The C code is in c/power_sources.c, c/power_sources.h. The CFFI bridge is in c/build_iokit.py.

Key observation: the user says the tool reports health "x" but System Report shows "y" - suggesting a logic bug, a wrong IOKit key, a C type issue, or an integer/float division problem.

Please examine each of these files for bugs, focusing on:
1. Is `DesignCapacity` the right IOKit key for "original design capacity"?
2. Are there integer division or type issues in the C-to-Python path?
3. Could `AppleRawMaxCapacity` vs `AppleRawCurrentCapacity` be mixed up?
4. Is there any arithmetic error in the health or percentage calculations?
5. Any other subtle bugs in the battery info fetching or health calculation?

Files to examine:
- /Users/oresttokovenko/Development/BatteryTool/c/power_sources.c
- /Users/oresttokovenko/Development/BatteryTool/c/power_sources.h
- /Users/oresttokovenko/Development/BatteryTool/c/build_iokit.py
- /Users/oresttokovenko/Development/BatteryTool/src/batterytool/battery.py
- /Users/oresttokovenko/Development/BatteryTool/src/batterytool/loop.py
- /Users/oresttokovenko/Development/BatteryTool/src/batterytool/main.py
- /Users/oresttokovenko/Development/BatteryTool/src/batterytool/constants.py

## Acceptance Contract
Acceptance level: attested
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Return a concise result and residual risks when applicable

Required evidence: manual-notes, residual-risks

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```