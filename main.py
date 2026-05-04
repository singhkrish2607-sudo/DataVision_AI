import asyncio
import os
import argparse
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from tkinter import Tk, filedialog
import pandas as pd
from power_bi_connector import PowerBIConnector, export_complete_analysis

load_dotenv()


from agents import CodeInterpreterTool, RunContextWrapper, Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel

# Tool definitions
code_interpreter = CodeInterpreterTool(tool_config={
  "type": "code_interpreter",
  "container": {
    "type": "auto",
    "file_ids": [

    ]
  }
})
class FileGeneratorAgentSchema(BaseModel):
  charts: str


class DataUnderstandingAgentContext:
  def __init__(self, workflow_input_as_text: str):
    self.workflow_input_as_text = workflow_input_as_text
def data_understanding_agent_instructions(run_context: RunContextWrapper[DataUnderstandingAgentContext], _agent: Agent[DataUnderstandingAgentContext]):
  workflow_input_as_text = run_context.context.workflow_input_as_text
  prompt = """You are a Data Analyst AI.

Be concise. Output only structured data, no explanations, no repeated input, no preamble. Maximum 50 words.

Your task is to analyze the given dataset (CSV or MySQL data) and generate a structured summary.
Instructions:
1. Identify all columns and their data types (numerical, categorical, date, etc.)
2. Provide total number of rows and columns
3. Detect missing/null values
4. Identify key features and important columns
5. Highlight possible relationships between columns
6. Detect basic patterns or trends
7. Suggest what kind of analysis or dashboard can be created


Analyze the following dataset:
Dataset:
 {workflow_input_as_text}


"""
  return prompt.replace("{workflow_input_as_text}", workflow_input_as_text)
data_understanding_agent = Agent(
  name="Data Understanding Agent",
  instructions=data_understanding_agent_instructions,
  model="gpt-4o",
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


class AnalysisAgentContext:
  def __init__(self, state_data_summary: str):
    self.state_data_summary = state_data_summary
def analysis_agent_instructions(run_context: RunContextWrapper[AnalysisAgentContext], _agent: Agent[AnalysisAgentContext]):
  state_data_summary = run_context.context.state_data_summary
  prompt = """You are a data analyst.
Use Code Interpreter to calculate EXACT values.

Run this Python code:

import pandas as pd
import json
from io import StringIO

raw_data = \"\"\"<<<STATE_DATA_SUMMARY>>>\"\"\"
df = pd.read_csv(StringIO(raw_data))

output = {}

# Real KPIs
for col in df.select_dtypes(include='number').columns:
    output[f\"{col}_sum\"] = round(float(df[col].sum()), 2)
    output[f\"{col}_avg\"] = round(float(df[col].mean()), 2)
    output[f\"{col}_max\"] = round(float(df[col].max()), 2)
    output[f\"{col}_min\"] = round(float(df[col].min()), 2)

# Real category counts
for col in df.select_dtypes(include='object').columns:
    counts = df[col].value_counts().head(6).to_dict()
    output[f\"{col}_counts\"] = counts

# Real correlations
corr = df.select_dtypes(include='number').corr()
output[\"correlations\"] = corr.round(2).to_dict()

# Print real values
print(json.dumps(output, indent=2))"""
  return prompt.replace("<<<STATE_DATA_SUMMARY>>>", state_data_summary)
analysis_agent = Agent(
  name="Analysis Agent",
  instructions=analysis_agent_instructions,
  model="gpt-4o",
  tools=[
    code_interpreter
  ],
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


class VisualizationAgentContext:
  def __init__(self, state_analysis_output: str):
    self.state_analysis_output = state_analysis_output
def visualization_agent_instructions(run_context: RunContextWrapper[VisualizationAgentContext], _agent: Agent[VisualizationAgentContext]):
  state_analysis_output = run_context.context.state_analysis_output
  return f"""You are a data visualization expert.

Be concise. Output only structured data, no explanations, no repeated input, no preamble. Maximum 100 words.

Based on the analysis below, create a detailed visualization plan.

CHART TYPE SELECTION RULES:
- Categorical vs Numerical     → bar, grouped_bar, stacked_bar, donut, pie
- Time vs Numerical            → line, area
- Numerical vs Numerical       → scatter
- Part of a whole (≤6 slices)  → pie, donut
- Two-dimensional intensity    → heatmap
- Frequency distribution       → histogram
- Process / pipeline / stages  → flow, sankey

RULES:
1. Recommend at least 5 charts total
2. Use at least 5 DISTINCT chart types (no defaulting to all bar charts)
3. Do not repeat the same chart type more than twice
4. Every chart must have ALL fields below — no exceptions

FOR EACH CHART, DEFINE THESE FIELDS:
- chart_id       → unique ID, e.g. \"chart_001\", \"chart_002\"
- chart_type     → one of: bar | line | pie | donut | scatter | area | heatmap | histogram | flow | grouped_bar | stacked_bar
- title          → human-readable chart title
- x_axis         → exact column name for x-axis (write \"N/A\" if not applicable)
- y_axis         → exact column name for y-axis (write \"N/A\" if not applicable)
- columns_used   → list of all columns this chart uses
- description    → what insight this chart reveals
- section        → one of: top_kpi | middle_charts | bottom_details
- color_scheme   → suggested color palette (e.g. \"blue shades\", \"red-green diverging\")

SECTION PLACEMENT GUIDE:
- top_kpi        → KPI scorecards, single-number charts, summary donuts
- middle_charts  → main trend and comparison charts (bar, line, scatter, area)
- bottom_details → deep-dive charts (heatmap, histogram, flow, grouped/stacked bar)

OUTPUT FORMAT:
Write each chart as a clearly labeled block like this:

Chart 001:
- chart_id: chart_001
- chart_type: bar
- title: Revenue by product category
- x_axis: category
- y_axis: revenue
- columns_used: category, revenue
- description: Shows which product categories generate the most revenue
- section: middle_charts
- color_scheme: blue shades

Chart 002:
- chart_id: chart_002
- chart_type: line
...and so on for every chart.

Analysis:
 {state_analysis_output}"""
visualization_agent = Agent(
  name="visualization_agent",
  instructions=visualization_agent_instructions,
  model="gpt-4o-mini",
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=10000,
    store=True
  )
)


class DashboardAgentContext:
  def __init__(self, state_visualization_output: str):
    self.state_visualization_output = state_visualization_output
def dashboard_agent_instructions(run_context: RunContextWrapper[DashboardAgentContext], _agent: Agent[DashboardAgentContext]):
  state_visualization_output = run_context.context.state_visualization_output
  return f"""You are a Power BI dashboard designer.

Be concise. Output only structured data, no explanations, no repeated input, no preamble. Maximum 50 words.

Using the visualization plan below:

{state_visualization_output}

Create a complete dashboard structure:

1. Dashboard Title
2. Sections (Top KPIs, Charts, Filters)
3. Chart placements
4. Suggested filters/slicers
5. Final dashboard description

Make it professional and ready for implementation.

Dashboard:
 {state_visualization_output}"""
dashboard_agent = Agent(
  name="dashboard_agent",
  instructions=dashboard_agent_instructions,
  model="gpt-4o",
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


class FileGeneratorAgentContext:
  def __init__(self, state_visualization_output: str):
    self.state_visualization_output = state_visualization_output
def file_generator_agent_instructions(run_context: RunContextWrapper[FileGeneratorAgentContext], _agent: Agent[FileGeneratorAgentContext]):
  state_visualization_output = run_context.context.state_visualization_output
  prompt = """You are a JSON generator.
Output ONLY raw JSON. No explanation. No backticks.

Extract REAL values from conversation history.
Generate realistic values based on dataset context.

{
  \"dashboard_title\": \"string\",
  \"filters\": [\"column1\", \"column2\"],
  \"kpis\": [
    {
      \"label\": \"string\",
      \"value\": \"real number from data\",
      \"column\": \"real column name\",
      \"aggregation\": \"sum | avg | count\"
    }
  ],
  \"charts\": [
    {
      \"chart_id\": \"chart_001\",
      \"chart_type\": \"bar\",
      \"title\": \"string\",
      \"x_axis\": \"real column name\",
      \"y_axis\": \"real column name\",
      \"section\": \"middle_charts\",
      \"data\": {
        \"labels\": [\"real value 1\", \"real value 2\", \"real value 3\"],
        \"values\": [1234, 5678, 9012]
      }
    }
  ],
  \"insights\": [
    \"real insight 1\",
    \"real insight 2\",
    \"real insight 3\"
  ]
}

STRICT RULES:
- labels must be REAL values from dataset
- values must be REAL numbers from dataset
- KPI values must be REAL calculated numbers
- Maximum 6 charts
- Maximum 3 KPIs
- Maximum 3 insights
- Maximum 2 filters
- NO random numbers
- NO placeholder text

IMPORTANT: Use ONLY the exact numbers from the analysis_output state. Do NOT estimate or round numbers. Use exact values like 247832 not 250000. Copy labels exactly from category counts.

Input:
<<<STATE_VISUALIZATION_OUTPUT>>>"""
  return prompt.replace("<<<STATE_VISUALIZATION_OUTPUT>>>", state_visualization_output)
file_generator_agent = Agent(
  name="file_generator_agent",
  instructions=file_generator_agent_instructions,
  model="gpt-4o",
  output_type=FileGeneratorAgentSchema,
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


class HtmlDashboardAgentContext:
  def __init__(self, state_file_generator: str):
    self.state_file_generator = state_file_generator
def html_dashboard_agent_instructions(run_context: RunContextWrapper[HtmlDashboardAgentContext], _agent: Agent[HtmlDashboardAgentContext]):
  state_file_generator = run_context.context.state_file_generator
  prompt = """You are an HTML dashboard generator.
Use only the last message as input.
Output ONLY raw HTML. No explanation. No backticks.
Maximum output: 2000 tokens.

USE:
- Chart.js from https://cdn.jsdelivr.net/npm/chart.js

PAGE STRUCTURE:
1. Header → gradient blue/purple, dashboard title, badge
2. Filters → one dropdown per filter, first option \"All\"
3. KPI cards → colored top border, emoji, real value, label
4. Charts grid → 2 columns, white cards, Chart.js canvas
5. Insights → left colored border cards with emoji
6. Footer → \"Generated by DataVision AI\"

CHART MAPPING:
bar → 'bar'
line → 'line'
pie → 'pie'
donut → 'doughnut'
scatter → 'scatter'
area → 'line' fill:true
histogram → 'bar'
heatmap → 'bar' horizontal stacked
grouped_bar → 'bar' grouped
stacked_bar → 'bar' stacked:true

COLORS:
'#4361ee','#3a0ca3','#7209b7','#f72585',
'#4cc9f0','#06d6a0','#ffd166','#ef476f'

PLACEMENT:
top_kpi → KPI card only, no canvas
middle_charts → full width card (grid span 2)
bottom_details → half width card

DATA RULES (Most Important):
- Read labels from chart.data.labels array
- Read values from chart.data.values array
- NEVER use Math.random()
- NEVER generate fake numbers
- If data missing → show \"No data available\"
- KPI value → read from kpis[].value directly

CHART RULES:
- responsive: true on all charts
- legend position: bottom
- tension: 0.4 on line charts
- Canvas id must match chart_id exactly

CSS:
- background: #f0f2f8
- white cards with border-radius: 14px
- box-shadow: 0 2px 12px rgba(0,0,0,0.07)
- header gradient: linear-gradient(135deg, #4361ee, #3a0ca3)
- KPI border colors: #4361ee, #7209b7, #06d6a0, #f72585
- Hover: transform translateY(-3px)
- Responsive grid for mobile

Input JSON:
<<<STATE_FILE_GENERATOR>>>"""
  return prompt.replace("<<<STATE_FILE_GENERATOR>>>", state_file_generator)
html_dashboard_agent = Agent(
  name="html_dashboard_agent",
  instructions=html_dashboard_agent_instructions,
  model="gpt-4o",
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)


class ImageGeneratorAgentContext:
  def __init__(self, state_file_generator: str):
    self.state_file_generator = state_file_generator
def image_generator_agent_instructions(run_context: RunContextWrapper[ImageGeneratorAgentContext], _agent: Agent[ImageGeneratorAgentContext]):
  state_file_generator = run_context.context.state_file_generator
  prompt = """You are a chart image generator.
Use Code Interpreter to convert JSON into chart images.

Create Python code that loads the JSON input, uses matplotlib to create chart images, saves files named by chart_id, and prints the saved filenames.

Input JSON:
<<<STATE_FILE_GENERATOR>>>"""
  return prompt.replace("<<<STATE_FILE_GENERATOR>>>", state_file_generator)

image_generator_agent = Agent(
  name="image_generator_agent",
  instructions=image_generator_agent_instructions,
  model="gpt-4o",
  tools=[
    code_interpreter
  ],
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)
class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("DataVision_AI"):
    state = {
      "data_summary": None,
      "dashboard_output": None,
      "visualization_output": None,
      "analysis_output": None,
      "file_generator": None
    }
    workflow = workflow_input.model_dump()
    conversation_history: list[TResponseInputItem] = [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": workflow["input_as_text"]
          }
        ]
      }
    ]
    data_understanding_agent_result_temp = await Runner.run(
      data_understanding_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69f11018dea08190b945b2a8d4eb61330fb73fd57ecdc871"
      }),
      context=DataUnderstandingAgentContext(workflow_input_as_text=workflow["input_as_text"])
    )

    conversation_history.extend([item.to_input_item() for item in data_understanding_agent_result_temp.new_items])

    data_understanding_agent_result = {
      "output_text": data_understanding_agent_result_temp.final_output_as(str)
    }
    state["data_summary"] = data_understanding_agent_result["output_text"]
    analysis_agent_result_temp = await Runner.run(
      analysis_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69f11018dea08190b945b2a8d4eb61330fb73fd57ecdc871"
      }),
      context=AnalysisAgentContext(state_data_summary=state["data_summary"])
    )

    conversation_history.extend([item.to_input_item() for item in analysis_agent_result_temp.new_items])

    analysis_agent_result = {
      "output_text": analysis_agent_result_temp.final_output_as(str)
    }
    state["analysis_output"] = analysis_agent_result["output_text"]
    visualization_agent_result_temp = await Runner.run(
      visualization_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69f11018dea08190b945b2a8d4eb61330fb73fd57ecdc871"
      }),
      context=VisualizationAgentContext(state_analysis_output=state["analysis_output"])
    )

    conversation_history.extend([item.to_input_item() for item in visualization_agent_result_temp.new_items])

    visualization_agent_result = {
      "output_text": visualization_agent_result_temp.final_output_as(str)
    }
    state["visualization_output"] = visualization_agent_result["output_text"]
    dashboard_agent_result_temp = await Runner.run(
      dashboard_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69f11018dea08190b945b2a8d4eb61330fb73fd57ecdc871"
      }),
      context=DashboardAgentContext(state_visualization_output=state["visualization_output"])
    )

    conversation_history.extend([item.to_input_item() for item in dashboard_agent_result_temp.new_items])

    dashboard_agent_result = {
      "output_text": dashboard_agent_result_temp.final_output_as(str)
    }
    state["dashboard_output"] = dashboard_agent_result["output_text"]
    file_generator_agent_result_temp = await Runner.run(
      file_generator_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69f11018dea08190b945b2a8d4eb61330fb73fd57ecdc871"
      }),
      context=FileGeneratorAgentContext(state_visualization_output=state["visualization_output"])
    )

    conversation_history.extend([item.to_input_item() for item in file_generator_agent_result_temp.new_items])

    file_generator_agent_result = {
      "output_text": file_generator_agent_result_temp.final_output.json(),
      "output_parsed": file_generator_agent_result_temp.final_output.model_dump()
    }
    state["file_generator"] = file_generator_agent_result["output_text"]
    html_dashboard_agent_result_temp = await Runner.run(
      html_dashboard_agent,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69f11018dea08190b945b2a8d4eb61330fb73fd57ecdc871"
      }),
      context=HtmlDashboardAgentContext(state_file_generator=state["file_generator"])
    )

    conversation_history.extend([item.to_input_item() for item in html_dashboard_agent_result_temp.new_items])

    html_dashboard_agent_result = {
      "output_text": html_dashboard_agent_result_temp.final_output_as(str)
    }
    return {
      "html_output": html_dashboard_agent_result["output_text"],
      "analysis_output": state["analysis_output"],
      "visualization_output": state["visualization_output"],
      "dashboard_output": state["dashboard_output"],
      "file_generator_output": state["file_generator"]
    }



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DataVision AI workflow on a CSV file.")
    parser.add_argument("--file", type=str, help="Path to the CSV file to analyze. If not provided, prompts for selection.")
    args = parser.parse_args()

    input_data = None

    # If file argument provided, use it directly
    if args.file:
        try:
            df = pd.read_csv(args.file)
            input_data = df.to_csv(index=False)
            print(f"\n✓ Successfully loaded file: {args.file}")
            print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        except Exception as e:
            print(f"\n✗ Error reading file {args.file}: {e}")
            exit(1)
    else:
        # Interactive menu
        print("\n" + "="*50)
        print("📊 DataVision AI - Data Analysis Tool")
        print("="*50)
        print("\nChoose an option:")
        print("1. Load a CSV file")
        print("2. Use sample data")
        print("="*50)
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            # Open file picker dialog
            root = Tk()
            root.withdraw()  # Hide the root window
            root.attributes('-topmost', True)  # Bring dialog to front
            
            file_path = filedialog.askopenfilename(
                title="Select CSV file to analyze",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            root.destroy()
            
            if file_path:
                try:
                    df = pd.read_csv(file_path)
                    input_data = df.to_csv(index=False)
                    print(f"\n✓ Successfully loaded: {file_path}")
                    print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
                except Exception as e:
                    print(f"\n✗ Error reading file: {e}")
                    exit(1)
            else:
                print("\n✗ No file selected. Exiting.")
                exit(1)
        elif choice == "2":
            print("\n✓ Using sample data...")
            input_data = """order_id,amount,category,date
1,200,Electronics,2024-01-01
2,150,Clothing,2024-01-02
3,300,Electronics,2024-01-03
4,100,Food,2024-01-04
"""
        else:
            print("\n✗ Invalid choice. Please enter 1 or 2.")
            exit(1)

    print("\n⏳ Processing data with AI agents...")
    print("-"*50)
    
    result = asyncio.run(
        run_workflow(
            WorkflowInput(input_as_text=input_data)
        )
    )

    print("-"*50)
    print("\n✓ Analysis complete!\n")
    print(result["html_output"])

    output_folder = Path("dashboard_outputs")
    output_folder.mkdir(exist_ok=True)
    html_filename = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    html_path = output_folder / html_filename
    with open(html_path, "w", encoding="utf-8") as html_file:
        html_file.write(result["html_output"])
    print(f"\n✓ Dashboard HTML saved to: {html_path}")
    
    # Export Options
    print("\n" + "="*50)
    print("📊 Dashboard Export Options")
    print("="*50)
    print("\nChoose export format:")
    print("1. Export to JSON (for Power BI Desktop import)")
    print("2. Push to Power BI Service (requires credentials)")
    print("3. Export HTML Dashboard to folder")
    print("4. Skip export")
    print("="*50)
    
    export_choice = input("\nEnter your choice (1-4): ").strip()
    analysis_data = {
        "analysis_output": result.get("analysis_output", ""),
        "visualization_output": result.get("visualization_output", ""),
        "dashboard_output": result.get("dashboard_output", ""),
        "file_generator_output": result.get("file_generator_output", "")
    }
    
    if export_choice == "1":
        exported_files = export_complete_analysis(analysis_data, "json")
        
        print("\n" + "-"*50)
        print("✓ Files exported successfully!")
        for file_type, filepath in exported_files.items():
            print(f"  • {file_type}: {filepath}")
        
        print("\n📋 How to import into Power BI Desktop:")
        print("  1. Open Power BI Desktop")
        print("  2. Click 'Get Data' → 'JSON'")
        print("  3. Select the exported JSON file from power_bi_exports/ folder")
        print("  4. Load and create visualizations in Power BI Desktop")
        
    elif export_choice == "2":
        print("\n⏳ Authenticating with Power BI Service...")
        connector = PowerBIConnector()
        
        if connector.authenticate():
            print("\n📤 Preparing data for Power BI...")
            
            json_export = connector.export_to_json(analysis_data)
            config_export = connector.generate_power_bi_report_config(analysis_data)
            
            print("\n✓ Files prepared:")
            print(f"  • JSON Export: {json_export}")
            print(f"  • Power BI Config: {config_export}")
            
            if connector.workspace_id and connector.dataset_id:
                print("\n📊 Power BI workspace is configured.")
                print("  Note: This script currently exports analysis data for import into Power BI.")
                print("  To create dashboards automatically, you would need to:")
                print("    1. Create a Power BI Report using the exported JSON data")
                print("    2. Define page layouts and visualizations in Power BI")
                print("    3. Publish to the Power BI Service workspace")
            else:
                print("\n⚠ Power BI workspace/dataset ID not configured")
                print("  Add to .env:")
                print("  - POWER_BI_WORKSPACE_ID")
                print("  - POWER_BI_DATASET_ID")
        else:
            print("\n✗ Power BI authentication failed")
            print("  To enable Power BI integration, add to .env:")
            print("  - POWER_BI_TENANT_ID")
            print("  - POWER_BI_CLIENT_ID")
            print("  - POWER_BI_CLIENT_SECRET")
    
    elif export_choice == "3":
        print("\n✓ HTML Dashboard already saved!")
        print(f"  Location: {html_path}")
        print("  You can open this file in any web browser to view the interactive dashboard.")
        
    elif export_choice == "4":
        print("\n✓ Skipping export. Analysis complete!")
    else:
        print("\n✗ Invalid choice.")

    
    print("\n" + "="*50)