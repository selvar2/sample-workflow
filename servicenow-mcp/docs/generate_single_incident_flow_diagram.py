import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

def create_single_incident_flow_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(14, 16))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 18)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Colors
    main_border = '#333333'
    orange_border = '#FF6F00'
    blue_border = '#1565C0'
    teal_border = '#00897B'
    
    # Helper function to draw box
    def draw_box(x, y, width, height, color='white', border_color='#333', linewidth=1.5, linestyle='-'):
        rect = FancyBboxPatch((x, y), width, height,
                             boxstyle="round,pad=0.02,rounding_size=0.05",
                             facecolor=color, edgecolor=border_color, 
                             linewidth=linewidth, linestyle=linestyle)
        ax.add_patch(rect)
    
    # Helper function to draw arrow
    def draw_arrow(start, end, color='#333'):
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    
    # ==================== TITLE ====================
    ax.text(7, 17.3, '5.1 Single Incident Processing Flow', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1565C0')
    
    # ==================== USER FLOW ====================
    ax.text(1, 16, 'User → ServiceNow UI → Create Incident', 
            ha='left', va='center', fontsize=10, fontweight='medium')
    
    # Arrow down
    draw_arrow((3.5, 15.7), (3.5, 15))
    
    # ==================== WEB UI DASHBOARD ====================
    draw_box(1.5, 13.2, 5, 1.5, 'white', orange_border, 2, '--')
    ax.text(4, 14.3, 'Web UI Dashboard', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(4, 13.7, '"Process Single Incident"', ha='center', va='center', fontsize=9, style='italic')
    
    # POST /api/process label
    ax.text(6.8, 12.7, 'POST /api/process', ha='left', va='center', fontsize=9, family='monospace', color='#1565C0')
    
    # Arrow down
    draw_arrow((4, 13.2), (4, 12.5))
    
    # ==================== INCIDENT PROCESSOR ====================
    draw_box(1.5, 8.5, 6.5, 3.5, 'white', orange_border, 2, '--')
    ax.text(4.75, 11.5, 'IncidentProcessor.process()', ha='center', va='center', fontsize=10, fontweight='bold', family='monospace')
    
    ax.text(2, 10.8, '1. Fetch incident from ServiceNow', ha='left', va='center', fontsize=9)
    ax.text(2, 10.3, '2. Check if already processed', ha='left', va='center', fontsize=9)
    ax.text(2, 9.8, '3. Parse description (regex)', ha='left', va='center', fontsize=9)
    ax.text(2, 9.3, '4. Execute Redshift operations', ha='left', va='center', fontsize=9)
    ax.text(2, 8.8, '5. Update incident with results', ha='left', va='center', fontsize=9)
    
    # Branching arrows down
    # Left branch
    draw_arrow((3.5, 8.5), (3.5, 7.8))
    draw_arrow((3.5, 7.8), (3, 7.3))
    
    # Right branch
    draw_arrow((5.5, 8.5), (5.5, 7.8))
    draw_arrow((5.5, 7.8), (8, 7.3))
    
    # Horizontal connector line
    ax.plot([3.5, 5.5], [7.8, 7.8], color='#333', linewidth=1.5)
    
    # ==================== SERVICENOW BOX ====================
    draw_box(1, 4.5, 3.5, 2.5, 'white', blue_border, 2, '--')
    ax.text(2.75, 6.6, 'ServiceNow', ha='center', va='center', fontsize=10, fontweight='bold', color=blue_border)
    ax.text(1.3, 6.0, '• GET incident', ha='left', va='center', fontsize=9)
    ax.text(1.3, 5.5, '• PUT work_notes', ha='left', va='center', fontsize=9)
    ax.text(1.3, 5.0, '• PATCH state', ha='left', va='center', fontsize=9)
    
    # ==================== AWS REDSHIFT BOX ====================
    draw_box(6, 4.5, 4, 2.5, 'white', teal_border, 2, '--')
    ax.text(8, 6.6, 'AWS Redshift', ha='center', va='center', fontsize=10, fontweight='bold', color=teal_border)
    ax.text(6.3, 6.0, '• execute_statement', ha='left', va='center', fontsize=9)
    ax.text(6.3, 5.5, '• describe_statement', ha='left', va='center', fontsize=9)
    ax.text(6.3, 5.0, '• get_result', ha='left', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/single_incident_flow_diagram.png', 
                dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/single_incident_flow_diagram.pdf', 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("✅ Single Incident Processing Flow diagram saved as:")
    print("   - docs/single_incident_flow_diagram.png")
    print("   - docs/single_incident_flow_diagram.pdf")

if __name__ == "__main__":
    create_single_incident_flow_diagram()
