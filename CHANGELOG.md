# GoodWe SEC1000/S Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/jozef-moravcik-homeassistant/goodwe-sec1000s.svg)](https://github.com/jozef-moravcik-homeassistant/goodwe-sec1000s/releases)
[![License](https://img.shields.io/github/license/jozef-moravcik-homeassistant/goodwe-sec1000s.svg)](LICENSE)

Home Assistant integration for GoodWe Smart Energy Controller SEC1000/S

## v1.01.03

## 📋 Changes

- New service set_min_export_limit for setting up a configuration parameter "Minimum export limit (kW)"
**Example:**

```yaml
action: goodwe_sec1000.set_min_export_limit
data:
  limit: 0.7
```

- New service set_max_export_limit for setting up a configuration parameter "Maximum export limit (kW)"
**Example:**

```yaml
action: goodwe_sec1000.set_max_export_limit
data:
  limit: 10
```
