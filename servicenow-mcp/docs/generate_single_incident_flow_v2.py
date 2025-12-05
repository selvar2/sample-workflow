import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse
import numpy as np

def create_single_incident_processing_flow():
    fig, ax = plt.subplots(1, 1, figsize=(18, 10))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Colors matching the reference image
    start_end_purple = '#F3E5F5'
    process_yellow = '#FFF9C4'
    decision_blue = '#B3E5FC'
    success_green = '#C8E6C9'
    action_pink = '#FCE4EC'
    
    # Helper function to draw rounded rectangle
    def draw_box(x, y, width, height, text, color, border_color='#333', text_size=9):
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                             boxstyle="round,pad=0.03,rounding_size=0.15",
                             facecolor=color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=text_size, 
                fontweight='medium', wrap=True)
    
    # Helper function to draw oval (start/end)
    def draw_oval(x, y, width, height, text, color):
        oval = Ellipse((x, y), width, height, facecolor=color, 
                        edgecolor='#9C27B0', linewidth=2)
        ax.add_patch(oval)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Helper function to draw diamond (decision)
    def draw_diamond(x, y, size, text, color):
        diamond = Polygon([(x, y + size), (x + size*1.2, y), (x, y - size), (x - size*1.2, y)],
                         facecolor=color, edgecolor='#0288D1', linewidth=2)
        ax.add_patch(diamond)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='medium')
    
    # Helper function to draw arrow
    def draw_arrow(start, end, color='#333', curved=False):
        if curved:
            ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle='->', color=color, lw=1.5,
                                      connectionstyle='arc3,rad=0.2'))
        else:
            ax.annotate('', xy=end, xytext=start,
                       arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    
    # Y positions
    top_y = 7
    bottom_y = 3
    
    # ==================== TOP ROW ====================
    
    # 1. Start (oval)
    draw_oval(1.2, top_y, 1.3, 0.9, 'Start', start_end_purple)
    
    # 2. User Request in ServiceNow
    draw_box(3.5, top_y, 2.2, 1.3, 'User Request\nin ServiceNow', process_yellow)
    
    # 3. ServiceNow API/MCP
    draw_box(6.2, top_y, 2, 1.3, 'ServiceNow\nAPI/MCP', process_yellow)
    
    # 4. Agent Orchestrator/MCP Client
    draw_box(9, top_y, 2.2, 1.3, 'Agent\nOrchestrator/\nMCP Client', process_yellow)
    
    # 5. Decision: Checks new incident or not
    draw_diamond(12, top_y, 1.1, 'Checks\nnew incident\nor not', decision_blue)
    
    # 6. Incident already processed (No path) - green box
    draw_box(15.5, top_y, 2.2, 1.3, 'Incident already\nprocessed, no\nactions required', success_green, '#4CAF50')
    
    # 7. End (oval)
    draw_oval(17.5, 5, 1.0, 0.8, 'End', start_end_purple)
    
    # ==================== BOTTOM ROW (Yes path) ====================
    
    # 8. Found New Incident
    draw_box(12, bottom_y, 2, 1.2, 'Found New\nIncident', process_yellow)
    
    # 9. Process Required Redshift commands (pink box)
    draw_box(15, bottom_y, 2.5, 1.4, 'Process Required\nRedshift commands\nthrough Redshift MCP', action_pink, '#E91E63')
    
    # 10. Update ServiceNow incident notes
    draw_box(17.5, bottom_y, 2, 1.2, 'Update ServiceNow\nincident notes', process_yellow)
    
    # ==================== ARROWS ====================
    
    # Start -> User Request
    draw_arrow((1.85, top_y), (2.4, top_y))
    
    # User Request -> ServiceNow API
    draw_arrow((4.6, top_y), (5.2, top_y))
    
    # ServiceNow API -> Agent Orchestrator
    draw_arrow((7.2, top_y), (7.9, top_y))
    
    # Agent Orchestrator -> Decision
    draw_arrow((10.1, top_y), (10.8, top_y))
    
    # Decision -> Already Processed (No) - curved arrow
    ax.annotate('', xy=(14.4, top_y), xytext=(13.2, top_y),
               arrowprops=dict(arrowstyle='->', color='#666', lw=1.5,
                              connectionstyle='arc3,rad=-0.2'))
    ax.text(13.8, top_y + 0.7, 'No', fontsize=9, color='#666', fontweight='bold')
    
    # Already Processed -> End (curved down)
    ax.annotate('', xy=(17.5, 5.4), xytext=(16.6, top_y - 0.3),
               arrowprops=dict(arrowstyle='->', color='#333', lw=1.5,
                              connectionstyle='arc3,rad=0.3'))
    
    # Decision -> Found New Incident (Yes - goes down)
    draw_arrow((12, top_y - 1.1), (12, bottom_y + 0.6))
    ax.text(12.3, 5, 'Yes', fontsize=9, color='#4CAF50', fontweight='bold')
    
    # Found New Incident -> Process Redshift
    draw_arrow((13, bottom_y), (13.75, bottom_y))
    
    # Process Redshift -> Update ServiceNow
    draw_arrow((16.25, bottom_y), (16.5, bottom_y))
    
    # Update ServiceNow -> End (curves up)
    ax.annotate('', xy=(17.5, 4.6), xytext=(17.5, bottom_y + 0.6),
               arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
    
    # ==================== TITLE ====================
    ax.text(9, 9.3, '5.1 Single Incident Processing Flow', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1565C0')
    
    plt.tight_layout()
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/single_incident_flow_v2.png', 
                dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/single_incident_flow_v2.pdf', 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("Single Incident Processing Flow diagram saved as:")
    print("   - docs/single_incident_flow_v2.png")
    print("   - docs/single_incident_flow_v2.pdf")

if __name__ == "__main__":
    create_single_incident_processing_flow()
