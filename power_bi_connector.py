"""
Power BI Connector for DataVision AI
Handles exporting data and connecting to Power BI
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class PowerBIConnector:
    """Connect DataVision AI analysis to Power BI"""
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None):
        """
        Initialize Power BI Connector
        
        Args:
            tenant_id: Azure Tenant ID (from .env)
            client_id: Azure Client ID (from .env)
            client_secret: Azure Client Secret (from .env)
        """
        self.tenant_id = tenant_id or os.getenv("POWER_BI_TENANT_ID")
        self.client_id = client_id or os.getenv("POWER_BI_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("POWER_BI_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWER_BI_WORKSPACE_ID")
        self.dataset_id = os.getenv("POWER_BI_DATASET_ID")
        
        self.access_token = None
        self.export_folder = Path("power_bi_exports")
        self.export_folder.mkdir(exist_ok=True)
        
    def export_to_csv(self, data: pd.DataFrame, filename: str = None) -> str:
        """
        Export DataFrame to CSV file
        
        Args:
            data: DataFrame to export
            filename: Output filename (default: timestamp-based)
            
        Returns:
            Path to exported CSV file
        """
        if filename is None:
            filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.export_folder / filename
        data.to_csv(filepath, index=False)
        print(f"✓ Exported to CSV: {filepath}")
        return str(filepath)
    
    def export_to_excel(self, data_dict: Dict[str, pd.DataFrame], filename: str = None) -> str:
        """
        Export multiple DataFrames to Excel (different sheets)
        
        Args:
            data_dict: Dictionary of sheet_name -> DataFrame
            filename: Output filename
            
        Returns:
            Path to exported Excel file
        """
        if filename is None:
            filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath = self.export_folder / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✓ Exported to Excel: {filepath}")
        return str(filepath)
    
    def export_to_json(self, analysis_data: Dict[str, Any], filename: str = None) -> str:
        """
        Export analysis results to JSON
        
        Args:
            analysis_data: Dictionary with analysis results
            filename: Output filename
            
        Returns:
            Path to exported JSON file
        """
        if filename is None:
            filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.export_folder / filename
        
        with open(filepath, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        print(f"✓ Exported to JSON: {filepath}")
        return str(filepath)
    
    def authenticate(self) -> bool:
        """
        Authenticate with Power BI using Service Principal
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            print("⚠ Power BI credentials not configured in .env file")
            print("  Add these to .env to enable Power BI integration:")
            print("  - POWER_BI_TENANT_ID")
            print("  - POWER_BI_CLIENT_ID")
            print("  - POWER_BI_CLIENT_SECRET")
            return False
        
        try:
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://analysis.windows.net/.default"
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            self.access_token = response.json()["access_token"]
            print("✓ Power BI authentication successful")
            return True
            
        except Exception as e:
            print(f"✗ Power BI authentication failed: {e}")
            return False
    
    def push_to_power_bi(self, dataframe: pd.DataFrame, table_name: str) -> bool:
        """
        Push DataFrame to Power BI dataset using REST API
        
        Args:
            dataframe: DataFrame to push
            table_name: Target table name in Power BI
            
        Returns:
            True if successful, False otherwise
        """
        if not self.authenticate():
            return False
        
        if not self.workspace_id or not self.dataset_id:
            print("⚠ Power BI workspace or dataset ID not configured")
            return False
        
        try:
            # Convert DataFrame to records
            records = dataframe.to_dict('records')
            
            # Prepare payload
            payload = {
                "rows": records
            }
            
            # Push to Power BI
            url = (f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/"
                   f"datasets/{self.dataset_id}/tables/{table_name}/rows")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            print(f"✓ Successfully pushed {len(records)} rows to Power BI table '{table_name}'")
            return True
            
        except Exception as e:
            print(f"✗ Failed to push to Power BI: {e}")
            return False
    
    def generate_power_bi_report_config(self, analysis_results: Dict[str, Any], 
                                       filename: str = None) -> str:
        """
        Generate a Power BI report configuration JSON
        Can be imported into Power BI Desktop
        
        Args:
            analysis_results: Analysis results from agents
            filename: Output filename
            
        Returns:
            Path to config file
        """
        if filename is None:
            filename = f"powerbi_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        config = {
            "report_name": analysis_results.get("dashboard_title", "DataVision AI Report"),
            "created_at": datetime.now().isoformat(),
            "data_analysis": analysis_results,
            "import_instructions": [
                "1. Open Power BI Desktop",
                "2. Create new blank report",
                "3. Get Data → CSV/JSON",
                f"4. Select exported data from: {self.export_folder}",
                "5. Load and configure visualizations",
                "6. Use the charts config below for quick setup"
            ]
        }
        
        filepath = self.export_folder / filename
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f"✓ Power BI config generated: {filepath}")
        return str(filepath)


def _extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract JSON object from a raw text string.
    """
    if not isinstance(text, str):
        return {}
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                return {}
    return {}


def create_analysis_dataframe(analysis_results: Dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Convert analysis output into export-ready DataFrames.
    """
    analysis_raw = analysis_results.get("analysis_output") if isinstance(analysis_results, dict) else analysis_results
    analysis = _extract_json_from_text(analysis_raw)

    kpis = []
    category_rows = []
    correlation_rows = []

    for key, value in analysis.items():
        if isinstance(value, (int, float)):
            kpis.append({"metric": key, "value": value})
        elif isinstance(value, dict):
            if key.endswith("_counts"):
                column_name = key[: -len("_counts")]
                for label, count in value.items():
                    category_rows.append({
                        "column": column_name,
                        "label": label,
                        "value": count
                    })
            elif key == "correlations":
                for row_key, row_value in value.items():
                    if isinstance(row_value, dict):
                        for col_key, corr_value in row_value.items():
                            correlation_rows.append({
                                "column_x": row_key,
                                "column_y": col_key,
                                "correlation": corr_value
                            })

    kpi_df = pd.DataFrame(kpis)
    category_df = pd.DataFrame(category_rows)
    correlation_df = pd.DataFrame(correlation_rows)

    return kpi_df, category_df, correlation_df


def export_complete_analysis(analysis_results: Dict[str, Any], 
                            export_format: str = "all") -> Dict[str, str]:

    """
    Export complete analysis in multiple formats
    
    Args:
        analysis_results: Analysis results from workflow
        export_format: "csv", "excel", "json", or "all"
        
    Returns:
        Dictionary of exported file paths
    """
    connector = PowerBIConnector()
    exported_files = {}
    
    try:
        kpi_df, category_df, correlation_df = create_analysis_dataframe(analysis_results)
        
        if export_format in ["csv", "all"]:
            if not kpi_df.empty:
                exported_files["kpi_csv"] = connector.export_to_csv(kpi_df, "kpis.csv")
            if not category_df.empty:
                exported_files["category_csv"] = connector.export_to_csv(category_df, "category_counts.csv")
            if not correlation_df.empty:
                exported_files["correlation_csv"] = connector.export_to_csv(correlation_df, "correlations.csv")
        
        if export_format in ["excel", "all"]:
            data_dict = {}
            if not kpi_df.empty:
                data_dict["KPIs"] = kpi_df
            if not category_df.empty:
                data_dict["CategoryCounts"] = category_df
            if not correlation_df.empty:
                data_dict["Correlations"] = correlation_df
            if data_dict:
                exported_files["excel"] = connector.export_to_excel(data_dict)
        
        if export_format in ["json", "all"]:
            exported_files["json"] = connector.export_to_json(analysis_results)
            exported_files["powerbi_config"] = connector.generate_power_bi_report_config(
                analysis_results
            )
        
        return exported_files
        
    except Exception as e:
        print(f"Error during export: {e}")
        return {}
