# BatteryTool

Need to kill your MacBook battery? Throw on an HDR YouTube video and run this program until your desired Battery Health is reached. Simply keep your MacBook plugged in and run this program. It will automatically disable charging when the battery reaches or exceeds 95% and re-enable it once the charge drops to 5% or below. The tool continuously monitors and adjusts the charging state, forcing the battery to drain and cycle without needing any interaction from you. 

Note: This tool has only been tested on Apple silicon Macbooks on MacOS 15

# Usage

1. Plug in your MacBook 
2. `uv tool install git+https://github.com/oresttokovenko/batterytool`
3. `uvx batterytool`

## Acknowledgements

I would like to express gratitude to the authors of the following files, which have been instrumental in the development of this project:

- **[battery.sh](https://github.com/actuallymentor/battery/blob/main/battery.sh#L263)** by [Actually Mentor](https://github.com/actuallymentor):  
  This script has been invaluable in providing the foundation for battery management functionality in this project

- **[smc-command](https://github.com/hholtmann/smcFanControl/tree/master/smc-command)** by [hholtmann](https://github.com/hholtmann):  
  The `smc-command` tool has been a key resource for interacting with the SMC chip
