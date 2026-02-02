#### BatteryTool

Need to kill your MacBook battery? Throw on an HDR YouTube video and run this program until your desired Battery Health is reached. Simply keep your MacBook plugged in and run this program. It will automatically disable charging when the battery reaches or exceeds 95% and re-enable it once the charge drops to 5% or below. The tool continuously monitors battery health and will automatically exit when it reaches 79% or below. The charging state is managed to force the battery to drain and cycle without needing any interaction from you.

> Your Apple One Year Limited Warranty includes replacement coverage for a defective battery. If you purchased an AppleCare Protection Plan for your Mac laptop and your battery retains less than 80 percent of its original capacity, Apple will replace the battery at no charge. If you don't have coverage, you can have the battery replaced for a fee

Note: This tool has only been tested on Apple silicon Macbooks on MacOS 15

#### Usage

1. Plug in your MacBook
2. [Install UV](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) using the standalone installer if you don't have it installed
3. Clone the repository to get access to the SMC binary:
   ```bash
   git clone https://github.com/oresttokovenko/battery-tool.git
   cd battery-tool
   ```
4. Install the tool:
   ```bash
   uv tool install git+https://github.com/oresttokovenko/battery-tool
   ```
5. Run from the cloned directory (sudo is needed to access SMC):
   ```bash
   sudo uvx batterytool
   ```

#### Roadmap

- **Cython Integration for Direct SMC Access**: Replace subprocess calls with native Python extension that compiles C source during installation
- **CHTE Key Support**: Add detection and support for the CHTE SMC key on newer firmware for better hardware compatibility

#### Acknowledgements

I would like to express gratitude to the authors of the following files, which have been instrumental in the development of this project:

- **[battery.sh](https://github.com/actuallymentor/battery/blob/main/battery.sh)** by [Actually Mentor](https://github.com/actuallymentor):
  This script has been invaluable in providing the foundation for battery management functionality in this project

- **[smc-command](https://github.com/hholtmann/smcFanControl/tree/master/smc-command)** by [hholtmann](https://github.com/hholtmann):
  The `smc-command` tool has been a key resource for interacting with the SMC chip
