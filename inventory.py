"""ЛР1. Автоматическая инвентаризация компьютера."""
import json
import platform
import socket
from datetime import datetime
import psutil
import sys
sys.stdout.reconfigure(encoding='utf-8')


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M"),
    }


def get_cpu_info():
    freq = psutil.cpu_freq()
    return {
        "model": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_freq_mhz": round(freq.max) if freq else None,
        "load_percent": psutil.cpu_percent(interval=1),
    }


def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / 1024**3, 1),
        "used_percent": mem.percent,
        "available_gb": round(mem.available / 1024**3, 1),
    }


def get_disk_info():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fs": part.fstype,
            "total_gb": round(usage.total / 1024**3, 1),
            "used_percent": usage.percent,
        })
    return disks


def get_network_info():
    networks = []
    for name, addrs in psutil.net_if_addrs().items():
        ipv4_address = None
        netmask = None
        mac_address = None

        for a in addrs:
            if a.family == socket.AF_INET:    # IPv4
                ipv4_address = a.address
                netmask = a.netmask
            elif a.family == psutil.AF_LINK:   # MAC-адрес
                mac_address = a.address

        # Пропускаем интерфейсы без IPv4-адреса
        if ipv4_address:
            networks.append({
                "interface": name,
                "ipv4": ipv4_address,
                "netmask": netmask,
                "mac": mac_address
            })
    return networks


def analyze(passport):
    recommendations = []

    # 1. Анализ оперативной памяти (RAM)
    total_ram = passport["memory"]["total_gb"]
    if total_ram < 8:
        recommendations.append(
            "Недостаточно памяти для виртуальных машин и Docker")
    elif total_ram >= 16 and passport["cpu"]["physical_cores"] >= 6:
        recommendations.append(
            "Подходит для одновременной работы нескольких VM")

    # 2. Анализ заполненности дисков (> 85%)
    for disk in passport["disks"]:
        if disk["used_percent"] > 85:
            recommendations.append(
                f"Освободить место на диске {disk['device']}")

    # 3. Анализ физических ядер процессора (< 4)
    if passport["cpu"]["physical_cores"] < 4:
        recommendations.append(
            "Процессор может стать узким местом (bottleneck)")

    # 4. Собственное правило: проверка текущей нагрузки на процессор (> 80%)
    if passport["cpu"]["load_percent"] > 80:
        recommendations.append(
            "Высокая текущая нагрузка на CPU: рекомендуется проверить фоновые процессы")

    return recommendations


def main():
    passport = {
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": get_system_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disks": get_disk_info(),
        "network": get_network_info(),
    }

    # Результаты автоматического анализа в структуру паспорта
    passport["recommendations"] = analyze(passport)

    filename = f"passport_{passport['system']['hostname']}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(passport, f, indent=2, ensure_ascii=False)
    print(json.dumps(passport, indent=2, ensure_ascii=False))
    print(f"\nПаспорт сохранён в файл {filename}")


if __name__ == "__main__":
    main()
