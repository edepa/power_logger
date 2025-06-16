# Power Logger and Plotter

This project logs power consumption data from HPE iLO 4 interfaces via the RedFish API and optionally visualizes it alongside CPU frequency data collected using PowerTOP.

---

## ✨ Features

- 🔌 Logs power via RedFish FastPowerMeter endpoint
- 🧠 Supports PowerTOP dynamic power data with idle offset
- 📈 Plots power data with matplotlib
- 🎚️ Interactive range selection
- 🧠 CPU frequency plots (if frequency CSV present)

---

## 📦 Requirements

Install dependencies using:

```
pip install -r requirements.txt
```

Tested on **Python 3.10+** on **Windows 11**.

---

## 🚀 Usage

Run the main interface script:

```
python cli.py <ip_address> <True|False> <timeout_in_seconds> [idle_power]
```

### Arguments:

- `<ip_address>` – IP of the iLO 4 RedFish interface (e.g. `192.168.0.8`)
- `<True|False>` – whether to log an immediate 20-minute reading
- `<timeout_in_seconds>` – how long to keep logging (e.g. 3600 for 1 hour)
- `[idle_power]` *(optional)* – power offset (in watts) to add to PowerTOP values

### Example:

```
python cli.py 192.168.0.8 True 1800 24.0
```

---

## 📊 Plotting

After logging completes or is interrupted:
- All `.csv` files are listed
- You're prompted to choose which data to plot
- If a frequency CSV is found (e.g. `*_frequency.csv`), you'll be offered to include it
- You then define time ranges for the plots interactively

The plots use Matplotlib and appear in a GUI window.

---

## 📁 Directory Layout

```
power_logger/
├── cli.py               # CLI entry point
├── logger.py            # Power logging logic
├── plotter.py           # Power + frequency plotter
├── requirements.txt     # Dependencies
├── .gitignore           # Ignores virtual env and logs
├── README.md            # This file
└── powerlogger-env/     # Virtual environment (excluded from Git)
```

---

## 🔐 Authentication

Credentials for RedFish are hardcoded in `logger.py`:

```python
self.username = "Administrator"
self.password = "MRTMW244"
```

To improve security, replace this with environment variable lookups or a config file.

---

## 📎 Sample CSV Layouts

### Power log (`powerlog.csv`)
```
Time,Average
2025-06-14T13:00:00Z,42.5
2025-06-14T13:00:10Z,43.1
...
```

### CPU frequency (`*_frequency.csv`)
```
Time;CPU0;CPU1;...;CPU15
2025-06-14T13:00:00Z;1600;1600;...;1600
2025-06-14T13:00:10Z;2100;2100;...;2200
...
```

---

## 🧪 GitHub Actions (optional)

To lint your code automatically, create this file:  
`.github/workflows/lint.yml`

```yaml
name: Lint Python Code

on:
  push:
    paths: ["**.py"]
  pull_request:
    paths: ["**.py"]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v5
        with:
          python-version: 3.10
      - run: pip install flake8
      - run: flake8 .
```

---

## 📷 Plot Screenshot (optional)

You can capture your plot using:

```python
plt.savefig("docs/power_plot_example.png")
```

And reference it like this in your README:

```
![Power Plot Example](docs/power_plot_example.png)
```

---

## 🛠️ Credits

Created by [edepa](https://github.com/edepa)  
Logged and plotted on Windows 11 – June 2025

---

## 🧭 License

No license yet.
