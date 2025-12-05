import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
import numpy as np

def create_architecture_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(16, 20))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 22)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Colors
    platform_border = '#1565C0'  # Blue
    web_ui_border = '#FF6F00'    # Orange
    processing_border = '#00897B' # Teal
    mcp_server_border = '#E53935' # Red
    box_fill = 'white'
    component_yellow = '#FFF9C4'
    component_orange = '#FFE0B2'
    
    # Helper function to draw dashed border box
    def draw_layer_box(x, y, width, height, title, border_color, title_color=None):
        rect = FancyBboxPatch((x, y), width, height,
                             boxstyle="round,pad=0.02,rounding_size=0.1",
                             facecolor='white', edgecolor=border_color, 
                             linewidth=2, linestyle='--')
        ax.add_patch(rect)
        if title:
            ax.text(x + width/2, y + height - 0.3, title, 
                   ha='center', va='top', fontsize=11, fontweight='bold', 
                   color=title_color or border_color)
    
    # Helper function to draw component box
    def draw_component(x, y, width, height, text, color='white', border_color='#333', fontsize=8):
        rect = FancyBboxPatch((x, y), width, height,
                             boxstyle="round,pad=0.02,rounding_size=0.05",
                             facecolor=color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + width/2, y + height/2, text, 
               ha='center', va='center', fontsize=fontsize, wrap=True)
    
    # Helper function to draw arrow
    def draw_arrow(start, end, color='#333'):
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    
    # ==================== PLATFORM LAYER ====================
    draw_layer_box(0.5, 0.5, 15, 21, 'SERVICENOW MCP PLATFORM', platform_border)
    
    # ==================== WEB UI LAYER ====================
    draw_layer_box(1, 15.5, 14, 5.5, 'WEB UI LAYER (Flask)', web_ui_border)
    
    # app.py and templates
    draw_component(1.5, 18.5, 2, 0.8, 'app.py', component_yellow, web_ui_border)
    
    # Template connections
    ax.plot([3.5, 4.5], [18.9, 19.3], color='#333', linewidth=1)
    ax.plot([3.5, 4.5], [18.9, 18.9], color='#333', linewidth=1)
    ax.plot([3.5, 4.5], [18.9, 18.5], color='#333', linewidth=1)
    
    ax.text(4.7, 19.3, 'templates/index.html (Dashboard)', fontsize=8, va='center')
    ax.text(4.7, 18.9, 'templates/login.html (Authentication)', fontsize=8, va='center')
    ax.text(4.7, 18.5, 'Static Assets (Bootstrap 5.3.2)', fontsize=8, va='center')
    
    # Features box
    draw_component(1.5, 16, 6, 2, '', 'white', web_ui_border)
    ax.text(1.8, 17.7, 'Features:', fontsize=9, fontweight='bold', va='top')
    ax.text(1.8, 17.3, '• Session-based authentication', fontsize=8, va='top')
    ax.text(1.8, 16.9, '• Real-time SSE event streaming', fontsize=8, va='top')
    ax.text(1.8, 16.5, '• REST API endpoints', fontsize=8, va='top')
    ax.text(1.8, 16.1, '• Processing history persistence', fontsize=8, va='top')
    
    # ==================== PROCESSING LAYER ====================
    draw_layer_box(1, 10, 14, 4.8, 'PROCESSING LAYER (Python)', processing_border)
    
    # Config, ServiceNowClient, RedshiftClient
    draw_component(1.5, 12.5, 2.5, 1.5, 'Config\n(Environment)', component_orange, '#FF6F00')
    draw_component(4.5, 12.5, 3, 1.5, 'ServiceNowClient\n(REST API)', component_orange, '#FF6F00')
    draw_component(8, 12.5, 2.8, 1.5, 'RedshiftClient\n(boto3 SDK)', component_orange, '#FF6F00')
    
    # IncidentParser, IncidentProcessor
    draw_component(1.5, 10.5, 2.8, 1.5, 'IncidentParser\n(Regex Patterns)', component_yellow, '#333')
    draw_component(5, 10.5, 3.5, 1.5, 'IncidentProcessor\n(Orchestrates full workflow)', component_yellow, '#333')
    
    # ==================== MCP SERVER LAYER ====================
    draw_layer_box(1, 0.8, 14, 8.5, 'MCP SERVER LAYER (src/)', mcp_server_border)
    
    # servicenow_mcp/ header
    ax.text(1.5, 8.7, 'servicenow_mcp/', fontsize=10, fontweight='bold', color='#333')
    
    # Main files
    ax.text(2, 8.2, '├── server.py', fontsize=9, family='monospace')
    ax.text(6.5, 8.2, 'MCP Protocol Implementation', fontsize=8, color='#666')
    
    ax.text(2, 7.7, '├── server_sse.py', fontsize=9, family='monospace')
    ax.text(6.5, 7.7, 'SSE Transport Layer', fontsize=8, color='#666')
    
    ax.text(2, 7.2, '└── cli.py', fontsize=9, family='monospace')
    ax.text(6.5, 7.2, 'Command Line Interface', fontsize=8, color='#666')
    
    # auth/ section
    ax.text(1.5, 6.5, 'auth/', fontsize=10, fontweight='bold', color='#333')
    ax.text(2, 6.0, '└── auth_manager.py', fontsize=9, family='monospace')
    ax.text(6.5, 6.0, 'Authentication (Basic/OAuth/API Key)', fontsize=8, color='#666')
    
    # utils/ section
    ax.text(1.5, 5.3, 'utils/', fontsize=10, fontweight='bold', color='#333')
    ax.text(2, 4.8, '├── config.py', fontsize=9, family='monospace')
    ax.text(6.5, 4.8, 'Configuration Models (Pydantic)', fontsize=8, color='#666')
    ax.text(2, 4.3, '└── tool_utils.py', fontsize=9, family='monospace')
    ax.text(6.5, 4.3, 'Tool Registration & Discovery', fontsize=8, color='#666')
    
    # tools/ section
    ax.text(1.5, 3.6, 'tools/', fontsize=10, fontweight='bold', color='#333')
    ax.text(6.5, 3.6, '80+ MCP Tool Implementations', fontsize=9, fontweight='bold', color='#E53935')
    
    ax.text(2, 3.1, '├── incident_tools.py', fontsize=9, family='monospace')
    ax.text(2, 2.7, '├── change_tools.py', fontsize=9, family='monospace')
    ax.text(2, 2.3, '├── catalog_tools.py', fontsize=9, family='monospace')
    ax.text(2, 1.9, '├── user_tools.py', fontsize=9, family='monospace')
    ax.text(2, 1.5, '├── workflow_tools.py', fontsize=9, family='monospace')
    ax.text(2, 1.1, '├── knowledge_base.py', fontsize=9, family='monospace')
    ax.text(2, 0.7, '└── ... (12 tool modules)', fontsize=9, family='monospace', color='#666')
    
    # ==================== ARROWS BETWEEN LAYERS ====================
    # Web UI -> Processing
    draw_arrow((8, 15.5), (8, 14.8), '#333')
    
    # Processing -> MCP Server
    draw_arrow((8, 10), (8, 9.3), '#333')
    
    # Title
    ax.text(8, 21.7, '3.1 Component Architecture', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1565C0')
    
    plt.tight_layout()
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/architecture_diagram.png', 
                dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/architecture_diagram.pdf', 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("✅ Architecture diagram saved as:")
    print("   - docs/architecture_diagram.png")
    print("   - docs/architecture_diagram.pdf")

if __name__ == "__main__":
    create_architecture_diagram()
