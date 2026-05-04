# 🤖 DataVision AI

> An AI-powered data analysis tool with seamless Power BI integration — analyze your data, generate insights, and export directly to Power BI in seconds.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Power BI Integration](#power-bi-integration)
- [Export Options](#export-options)
- [Contributing](#contributing)
- [License](#license)

---

## 🌟 Overview

DataVision AI is a Python-based data analysis platform that leverages OpenAI's models to provide intelligent insights from your data. It features a multi-agent architecture and full Power BI integration, allowing you to go from raw data to interactive dashboards with minimal effort.

---

## ✨ Features

- 🧠 **AI-Powered Analysis** — Uses OpenAI GPT models to analyze and interpret your data
- 👾 **Multi-Agent Architecture** — Modular agents handle different analysis tasks
- 📊 **Power BI Integration** — Export results directly to Power BI Service or desktop
- 📁 **Multiple Export Formats** — CSV, Excel, and JSON export support
- 🔌 **Azure Service Principal Auth** — Secure authentication for Power BI API
- 📈 **KPI & Chart Generation** — Automatically generates KPIs and visualizations

---

## 📁 Project Structure

```
DataVision_AI/
├── main.py                  # Main entry point and interactive menu
├── agents.py                # AI agent definitions and logic
├── power_bi_connector.py    # Power BI export and API integration
├── requirements.txt         # Python dependencies
├── POWER_BI_SETUP.md        # Detailed Power BI setup guide
├── .env.example             # Environment variable template
├── dashboard_outputs/       # Generated dashboard files
└── power_bi_exports/        # Power BI export files (CSV, Excel, JSON)
```

---

## ✅ Prerequisites

- Python 3.8+
- An [OpenAI API Key](https://platform.openai.com/account/api-keys)
- (Optional) Azure account for Power BI Service integration
- (Optional) Power BI Desktop for local visualization

---

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/DataVision_AI.git
   cd DataVision_AI
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

1. **Copy the example environment file**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials**
   ```env
   OPENAI_API_KEY=your_openai_api_key

   # Optional: Power BI Service Integration
   POWER_BI_TENANT_ID=your_tenant_id
   POWER_BI_CLIENT_ID=your_client_id
   POWER_BI_CLIENT_SECRET=your_client_secret
   POWER_BI_WORKSPACE_ID=your_workspace_id
   POWER_BI_DATASET_ID=your_dataset_id
   ```

> ⚠️ **Never commit your `.env` file to GitHub.** It is already listed in `.gitignore`.

---

## 🖥️ Usage

**Run with a data file:**
```bash
python main.py --file "path/to/your/data.csv"
```

**Run in interactive mode:**
```bash
python main.py
```

**Choose your export format from the menu:**
```
Choose export format:
1. Export to CSV
2. Export to Excel (recommended)
3. Export to JSON
4. Export all formats
5. Push to Power BI (requires credentials)
6. Skip export
```

---

## 📊 Power BI Integration

DataVision AI supports multiple ways to connect with Power BI:

| Method | Description | Setup Required |
|--------|-------------|----------------|
| CSV Export | Manual import into Power BI Desktop | None |
| Excel Export | Best compatibility, multi-sheet export | None |
| JSON Export | Structured data with Power BI config | None |
| Power BI API | Direct push to Power BI Service | Azure credentials |

For detailed Power BI Service setup, see [POWER_BI_SETUP.md](./POWER_BI_SETUP.md).

---

## 📤 Export Options

Exported files are saved in the `power_bi_exports/` folder:

```
power_bi_exports/
├── analysis_20260502_123456.csv
├── analysis_20260502_123456.xlsx
├── analysis_20260502_123456.json
└── powerbi_config_20260502_123456.json
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

---

<p align="center">Built with ❤️ using Python & OpenAI</p>
