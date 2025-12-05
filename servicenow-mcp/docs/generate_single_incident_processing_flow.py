import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse
import numpy as np

def create_single_incident_processing_flow():
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 14)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Colors matching the reference style
    start_end_purple = '#F3E5F5'
    process_yellow = '#FFF9C4'
    orange_border = '#FF6F00'
    blue_border = '#1565C0'
    teal_border = '#00897B'
    
    # Helper function to draw rounded rectangle with dashed border
    def draw_box(x, y, width, height, color='white', border_color='#333', linewidth=1.5, linestyle='-'):
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                             boxstyle="round,pad=0.03,rounding_size=0.1",
                             facecolor=color, edgecolor=border_color, 
                             linewidth=linewidth, linestyle=linestyle)
        ax.add_patch(box)
    
    # Helper function to draw oval (start/end)
    def draw_oval(x, y, width, height, text, color):
        oval = Ellipse((x, y), width, height, facecolor=color, 
                        edgecolor='#9C27B0', linewidth=2)
        ax.add_patch(oval)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Helper function to draw arrow
    def draw_arrow(start, end, color='#333'):
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    
    # ==================== TITLE ====================
    ax.text(8, 13.5, '5.1 Single Incident Processing Flow', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1565C0')
    
    # ==================== USER FLOW (Top) ====================
    ax.text(3, 12.5, 'User -> ServiceNow UI -> Create Incident', 
            ha='left', va='center', fontsize=10, fontweight='medium')
    
    # Arrow down
    draw_arrow((4.5, 12.2), (4.5, 11.6))
    
    # ==================== WEB UI DASHBOARD ====================
    draw_box(4.5, 10.5, 4.5, 1.5, 'white', orange_border, 2, '--')
    ax.text(4.5, 10.9, 'Web UI Dashboard', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(4.5, 10.2, '"Process Single Incident"', ha='center', va='center', fontsize=9, style='italic')
    
    # POST /api/process label
    ax.text(7, 9.5, 'POST /api/process', ha='left', va='center', fontsize=9, family='monospace', color='#1565C0')
    
    # Arrow down
    draw_arrow((4.5, 9.7), (4.5, 9.1))
    
    # ==================== INCIDENT PROCESSOR ====================
    draw_box(4.5, 7, 5.5, 3.5, 'white', orange_border, 2, '--')
    ax.text(4.5, 8.5, 'IncidentProcessor.process()', ha='center', va='center', fontsize=10, fontweight='bold', family='monospace')
    
    ax.text(2.2, 7.8, '1. Fetch incident from ServiceNow', ha='left', va='center', fontsize=9)
    ax.text(2.2, 7.3, '2. Check if already processed', ha='left', va='center', fontsize=9)
    ax.text(2.2, 6.8, '3. Parse description (regex)', ha='left', va='center', fontsize=9)
    ax.text(2.2, 6.3, '4. Execute Redshift operations', ha='left', va='center', fontsize=9)
    ax.text(2.2, 5.8, '5. Update incident with results', ha='left', va='center', fontsize=9)
    
    # Branching arrows down
    # Vertical line down from processor
    ax.plot([4.5, 4.5], [5.2, 4.5], color='#333', linewidth=1.5)
    
    # Horizontal split line
    ax.plot([3, 6], [4.5, 4.5], color='#333', linewidth=1.5)
    
    # Left arrow down
    draw_arrow((3, 4.5), (3, 3.8))
    
    # Right arrow down  
    draw_arrow((6, 4.5), (9, 3.8))
    
    # ==================== SERVICENOW BOX ====================
    draw_box(3, 2.3, 3, 2.5, 'white', blue_border, 2, '--')
    ax.text(3, 3.3, 'ServiceNow', ha='center', va='center', fontsize=10, fontweight='bold', color=blue_border)
    ax.text(1.8, 2.7, '* GET incident', ha='left', va='center', fontsize=9)
    ax.text(1.8, 2.2, '* PUT work_notes', ha='left', va='center', fontsize=9)
    ax.text(1.8, 1.7, '* PATCH state', ha='left', va='center', fontsize=9)
    
    # ==================== AWS REDSHIFT BOX ====================
    draw_box(9, 2.3, 3.5, 2.5, 'white', teal_border, 2, '--')
    ax.text(9, 3.3, 'AWS Redshift', ha='center', va='center', fontsize=10, fontweight='bold', color=teal_border)
    ax.text(7.5, 2.7, '* execute_statement', ha='left', va='center', fontsize=9)
    ax.text(7.5, 2.2, '* describe_statement', ha='left', va='center', fontsize=9)
    ax.text(7.5, 1.7, '* get_result', ha='left', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/single_incident_processing_flow.png', 
                dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/single_incident_processing_flow.pdf', 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("Single Incident Processing Flow diagram saved as:")
    print("   - docs/single_incident_processing_flow.png")
    print("   - docs/single_incident_processing_flow.pdf")

if __name__ == "__main__":
    create_single_incident_processing_flow()
