# DataVision AI - Power BI Connector Integration

## Overview
DataVision AI now includes full Power BI integration with multiple export and connection options.

## Features

### 1. **Export to CSV**
- Export analysis results to CSV format
- Ideal for manual Power BI Desktop import
- Supports KPI data and chart information

### 2. **Export to Excel**
- Export analysis to Excel with multiple sheets
- Recommended format for best compatibility
- Automatically formats data for Power BI

### 3. **Export to JSON**
- Export analysis as structured JSON
- Includes configuration for Power BI Desktop
- Power BI config file with import instructions

### 4. **Power BI API Integration** (Advanced)
- Direct connection to Power BI Service
- Automatically push datasets to Power BI
- Requires authentication credentials

## Setup Instructions

### For CSV/Excel Export (Simple)
No additional setup required! Just run:
```bash
python main.py
# Select option 1, 2, or 4 to export
```

### For Power BI Service Integration (Advanced)

#### Step 1: Create Azure Service Principal

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Enter a name (e.g., "DataVision-AI-PowerBI")
5. Click "Register"

#### Step 2: Get Your Credentials

From the app registration page:
- Copy **Application (client) ID** → `POWER_BI_CLIENT_ID`
- Copy **Directory (tenant) ID** → `POWER_BI_TENANT_ID`

Create a client secret:
- Click "Certificates & secrets"
- Click "New client secret"
- Copy the secret value → `POWER_BI_CLIENT_SECRET`

#### Step 3: Add Permissions to Power BI Service

1. In app registration, click "API permissions"
2. Click "Add a permission"
3. Select "Power BI Service"
4. Select "Dataset.ReadWrite.All" and "Workspace.ReadWrite.All"
5. Click "Grant admin consent"

#### Step 4: Get Power BI Workspace and Dataset IDs

1. Go to [Power BI Service](https://app.powerbi.com)
2. Open your workspace
3. From the URL, copy the **Workspace ID**
4. Create a new dataset or select existing
5. From dataset settings, copy the **Dataset ID**

#### Step 5: Configure .env File

Create or update `.env` in your project folder:

```env
OPENAI_API_KEY=your_openai_api_key

# Power BI Service Integration
POWER_BI_TENANT_ID=your_tenant_id_here
POWER_BI_CLIENT_ID=your_client_id_here
POWER_BI_CLIENT_SECRET=your_client_secret_here
POWER_BI_WORKSPACE_ID=your_workspace_id_here
POWER_BI_DATASET_ID=your_dataset_id_here
```

## Usage

### Run the Tool
```bash
python main.py --file "path/to/your/data.csv"
# or
python main.py  # For interactive menu
```

### Choose Export Option
```
Choose export format:
1. Export to CSV
2. Export to Excel (recommended)
3. Export to JSON
4. Export all formats
5. Push to Power BI (requires credentials)
6. Skip export
```

## File Structure After Export

Exported files are saved in `power_bi_exports/` folder:

```
power_bi_exports/
├── analysis_20260502_123456.csv
├── analysis_20260502_123456.xlsx
├── analysis_20260502_123456.json
└── powerbi_config_20260502_123456.json
```

## Importing into Power BI Desktop

### Option 1: CSV Import
1. Open Power BI Desktop
2. Click "Get Data" → "Text/CSV"
3. Navigate to `power_bi_exports/` folder
4. Select `.csv` file
5. Load and create visualizations

### Option 2: Excel Import
1. Open Power BI Desktop
2. Click "Get Data" → "Excel"
3. Select `.xlsx` file from `power_bi_exports/`
4. Load data and create visualizations

### Option 3: JSON Import
1. Open Power BI Desktop
2. Click "Get Data" → "JSON"
3. Select `.json` file from `power_bi_exports/`
4. Follow transformation steps

## Power BI Connector Class Reference

### PowerBIConnector

#### Methods:

**`export_to_csv(dataframe, filename=None)`**
- Exports DataFrame to CSV file
- Returns: file path

**`export_to_excel(data_dict, filename=None)`**
- Exports multiple DataFrames to Excel sheets
- Returns: file path

**`export_to_json(analysis_data, filename=None)`**
- Exports analysis dictionary to JSON
- Returns: file path

**`authenticate()`**
- Authenticates with Power BI Service
- Requires: POWER_BI_TENANT_ID, CLIENT_ID, CLIENT_SECRET
- Returns: boolean

**`push_to_power_bi(dataframe, table_name)`**
- Pushes DataFrame to Power BI dataset
- Requires: workspace_id, dataset_id
- Returns: boolean

**`generate_power_bi_report_config(analysis_results, filename=None)`**
- Generates Power BI config JSON
- Returns: file path

## Troubleshooting

### "No module named requests"
```bash
pip install -r requirements.txt
```

### "Power BI authentication failed"
- Verify credentials in `.env`
- Check that Service Principal has Power BI permissions
- Ensure admin consent was granted

### "Power BI workspace/dataset ID not configured"
- Add `POWER_BI_WORKSPACE_ID` and `POWER_BI_DATASET_ID` to `.env`

### Cannot connect to Power BI Service
- Verify internet connection
- Check Azure app registration is active
- Verify Service Principal permissions in Power BI Admin Portal

## Example Workflow

```bash
# 1. Run analysis on CSV file
python main.py --file sales_data.csv

# 2. Choose export option (e.g., option 2 for Excel)
# 3. Files saved to power_bi_exports/

# 4. Open Power BI Desktop
# 5. Import Excel file from power_bi_exports/
# 6. Create interactive dashboards
# 7. Publish to Power BI Service
```

## Support

For issues or questions:
1. Check `.env` configuration
2. Review Power BI app registration permissions
3. Verify Azure credentials
4. Check Power BI Service workspace and dataset IDs

---

**Note:** Power BI Service integration requires Power BI Pro license or Premium capacity.
