"""ЛР1. Мониторинг нагрузки с порогами и журналом в CSV."""
import csv
import time
from datetime import datetime
import psutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

INTERVAL = 3         # секунд между замерами (Вариант 12)
SAMPLES = 25         # количество замеров (Вариант 12)
THRESHOLDS = {"cpu": 85, "ram": 75, "disk": 90}  # Пороги по Варианту 12
LOG_FILE = "monitor_log.csv"


def take_sample():
    return {
        "time": datetime.now().strftime("%H:%M:%S"),
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "users": len(psutil.users()),  # Дополнительная метрика по Варианту 12
    }


def check_alerts(sample):
    alerts = []
    for metric, limit in THRESHOLDS.items():
        if sample[metric] >= limit:
            alerts.append(
                f"{metric.upper()} = {sample[metric]}% (порог {limit}%)")
    return alerts


def main():
    psutil.cpu_percent(interval=None)  # «прогреваем» первый вызов CPU

    # Списки для подсчета статистики (среднее и максимум)
    cpu_values = []
    ram_values = []
    disk_values = []
    users_values = []

    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["time", "cpu", "ram", "disk", "users", "alert"])
        writer.writeheader()

        for _ in range(SAMPLES):
            time.sleep(INTERVAL)
            s = take_sample()

            # Сохраняем значения для статистики
            cpu_values.append(s["cpu"])
            ram_values.append(s["ram"])
            disk_values.append(s["disk"])
            users_values.append(s["users"])

            alerts = check_alerts(s)
            s["alert"] = "; ".join(alerts)
            writer.writerow(s)

            mark = "  <-- ВНИМАНИЕ: " + s["alert"] if alerts else ""
            print(
                f"{s['time']}  CPU {s['cpu']:5.1f}%  RAM {s['ram']:5.1f}%  DISK {s['disk']:5.1f}%  USERS {s['users']}{mark}")

    print(f"\nЖурнал сохранён в {LOG_FILE}")

    # Вычисление и вывод средних и максимальных значений после цикла
    if SAMPLES > 0:
        print("\n--- ИТОГОВАЯ СТАТИСТИКА МОНИТОРИНГА ---")
        print(
            f"CPU   -> Среднее: {sum(cpu_values)/len(cpu_values):5.1f}% | Максимум: {max(cpu_values):5.1f}%")
        print(
            f"RAM   -> Среднее: {sum(ram_values)/len(ram_values):5.1f}% | Максимум: {max(ram_values):5.1f}%")
        print(
            f"DISK  -> Среднее: {sum(disk_values)/len(disk_values):5.1f}% | Максимум: {max(disk_values):5.1f}%")
        print(
            f"USERS -> Среднее: {sum(users_values)/len(users_values):5.1f}   | Максимум: {max(users_values)}")


if __name__ == "__main__":
    main()
