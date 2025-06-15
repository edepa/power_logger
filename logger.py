import requests
import pandas as pd
import asyncio
from datetime import datetime
import urllib3
import warnings
import time
import shutil
import ipaddress
import os

class TimeoutException(Exception):
    """Custom exception to indicate a timeout."""

class PowerLogger:
    def __init__(self, target_ip: ipaddress.ip_address):
        self.target_base_url = "https://" + str(target_ip)
        self.target_power_meter_url = self.target_base_url + "/redfish/v1/Chassis/1/Power/FastPowerMeter"
        self.username = "Administrator"
        self.password = "MRTMW244"
        self.timestamp = datetime.now().strftime(f"%Y-%m-%d_%H_%M_%S")
        self.powerlogger_parent_dir = f"C:/powerlogger/{self.timestamp}"
        self.powerlogger_plot_subdir = f"{self.powerlogger_parent_dir}/plotdir"
        self.log_file_path = f"{self.powerlogger_parent_dir}/powerlog.csv"
        self.plot_file_path = f"{self.powerlogger_plot_subdir}/powerlog.csv"
        os.makedirs(self.powerlogger_parent_dir,exist_ok=True);
        os.makedirs(self.powerlogger_plot_subdir,exist_ok=True);
        warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)

    def get_log_directory(self) -> str:
        return self.powerlogger_parent_dir;

    def get_plot_directory(self) -> str:
        return self.powerlogger_plot_subdir;

    def read_target(self) -> pd.DataFrame:
        while True:
            try:
                response = requests.get(self.target_power_meter_url, auth=(self.username, self.password), verify=False)
                return pd.DataFrame(response.json()["PowerDetail"])
            except requests.ConnectionError:
                print("Data collection failed at", datetime.now(), "; retrying in 5 minutes ...")
                time.sleep(300)

    def write_to_file(self, power_from_target: pd.DataFrame):
        try:
            with open(self.log_file_path, 'r+') as log_file:
                num_rows = sum(1 for _ in log_file)
                column_names = pd.read_csv(self.log_file_path, nrows=0).to_dict()
                last_row_data = pd.read_csv(self.log_file_path, header=None, skiprows=num_rows - 1)
                column_values = {k: last_row_data[i].iloc[0] for i, k in enumerate(column_names)}
                try:
                    index = power_from_target.index[
                        (power_from_target["Time"] == column_values["Time"]).tolist()
                    ][0]
                except IndexError:
                    index = -1
                power_from_target = power_from_target.drop(range(index + 1))
                power_from_target.to_csv(self.log_file_path, mode='a', header=False, index=False)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            power_from_target.to_csv(self.log_file_path, index=False)

    async def update_log_file(self):
        print("Gathering data from target at", datetime.now())
        self.write_to_file(self.read_target())

    async def scheduler(self):
        try:
            while True:
                await asyncio.sleep(900)
                await self.update_log_file()
        except asyncio.CancelledError:
            raise

    async def run(self, timeout_duration):
        task = asyncio.create_task(self.scheduler())
        try:
            await asyncio.wait_for(task, timeout_duration)
        except asyncio.TimeoutError:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print("Scheduled logging was successfully cancelled after", timeout_duration, "seconds.")
            raise TimeoutException("")
        except KeyboardInterrupt:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                print("Scheduled logging was cleanly interrupted from the keyboard.")
            raise KeyboardInterrupt

    def copy_log_to_plot(self):
        try:
            shutil.copy(self.log_file_path, self.plot_file_path)
            print("\nCopied", self.log_file_path, "to", self.plot_file_path)
        except FileNotFoundError:
            print("No data had been logged at the time of interrupt.")
