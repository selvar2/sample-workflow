import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import numpy as np

def create_flow_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(18, 8))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 8)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Colors matching your diagram
    start_end_color = '#F3E5F5'  # Light purple
    process_yellow = '#FFF9C4'   # Light yellow
    decision_blue = '#E3F2FD'    # Light blue
    success_green = '#E8F5E9'    # Light green
    action_pink = '#FCE4EC'      # Light pink
    
    # Helper function to draw rounded rectangle
    def draw_box(x, y, width, height, text, color, text_size=9, border_color='#333'):
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                             boxstyle="round,pad=0.05,rounding_size=0.2",
                             facecolor=color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=text_size, 
                fontweight='medium', wrap=True)
    
    # Helper function to draw oval (start/end)
    def draw_oval(x, y, width, height, text, color):
        oval = mpatches.Ellipse((x, y), width, height, facecolor=color, 
                                 edgecolor='#9C27B0', linewidth=2)
        ax.add_patch(oval)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Helper function to draw diamond (decision)
    def draw_diamond(x, y, size, text, color):
        diamond = Polygon([(x, y + size), (x + size, y), (x, y - size), (x - size, y)],
                         facecolor=color, edgecolor='#1976D2', linewidth=2)
        ax.add_patch(diamond)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, fontweight='medium')
    
    # Helper function to draw arrow
    def draw_arrow(start, end, color='#333', style='-', linewidth=1.5):
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color=color, lw=linewidth,
                                  linestyle=style, connectionstyle='arc3,rad=0'))
    
    # Y positions
    main_y = 4.5
    lower_y = 2.0
    
    # 1. Start (oval)
    draw_oval(1, main_y, 1.2, 0.8, 'Start', start_end_color)
    
    # 2. User Request in ServiceNow
    draw_box(3, main_y, 1.8, 1.2, 'User\nRequest in\nServiceNow', process_yellow)
    
    # 3. ServiceNow API/MCP
    draw_box(5.5, main_y, 1.6, 1.0, 'ServiceNow\nAPI/MCP', process_yellow)
    
    # 4. Agent Orchestrator/MCP Client
    draw_box(8, main_y, 1.8, 1.2, 'Agent\nOrchestrator/\nMCP Client', process_yellow)
    
    # 5. Decision: Checks new incident or not
    draw_diamond(10.5, main_y, 0.9, 'Checks\nnew incident\nor not', decision_blue)
    
    # 6. Incident already processed (No path)
    draw_box(13.5, main_y, 2.0, 1.0, 'Incident is already\nprocessed, no\nactions required', success_green)
    
    # 7. End (oval)
    draw_oval(16.5, main_y, 1.0, 0.7, 'End', start_end_color)
    
    # 8. Found New Incident (Yes path - goes down)
    draw_box(10.5, lower_y, 1.6, 1.0, 'Found New\nIncident', process_yellow)
    
    # 9. Process Required Redshift commands
    draw_box(13.5, lower_y, 2.2, 1.2, 'Process Required\nRedshift commands\nthrough Redshift MCP', action_pink)
    
    # 10. Update ServiceNow incident notes
    draw_box(16.5, lower_y, 1.8, 1.0, 'Update Service\nNow incident\nnotes', process_yellow)
    
    # Draw arrows
    # Start -> User Request
    draw_arrow((1.6, main_y), (2.1, main_y))
    
    # User Request -> ServiceNow API
    draw_arrow((3.9, main_y), (4.7, main_y))
    
    # ServiceNow API -> Agent Orchestrator
    draw_arrow((6.3, main_y), (7.1, main_y))
    
    # Agent Orchestrator -> Decision
    draw_arrow((8.9, main_y), (9.6, main_y))
    
    # Decision -> Already Processed (No)
    draw_arrow((11.4, main_y), (12.5, main_y), color='#E53935', style='--')
    ax.text(11.9, main_y + 0.3, 'No', fontsize=9, color='#E53935', fontweight='bold')
    
    # Already Processed -> End
    draw_arrow((14.5, main_y), (16.0, main_y))
    
    # Decision -> Found New Incident (Yes - goes down)
    draw_arrow((10.5, main_y - 0.9), (10.5, lower_y + 0.5), color='#4CAF50')
    ax.text(10.7, 3.2, 'Yes', fontsize=9, color='#4CAF50', fontweight='bold')
    
    # Found New Incident -> Process Redshift
    draw_arrow((11.3, lower_y), (12.4, lower_y))
    
    # Process Redshift -> Update ServiceNow
    draw_arrow((14.6, lower_y), (15.6, lower_y))
    
    # Update ServiceNow -> End (curves up)
    ax.annotate('', xy=(16.5, main_y - 0.35), xytext=(16.5, lower_y + 0.5),
               arrowprops=dict(arrowstyle='->', color='#333', lw=1.5,
                              connectionstyle='arc3,rad=0'))
    
    # Title
    ax.text(9, 7.3, 'ServiceNow-Redshift MCP Integration Flow', 
            ha='center', va='center', fontsize=16, fontweight='bold', color='#1565C0')
    
    ax.text(9, 6.7, 'Automated Incident Processing Workflow', 
            ha='center', va='center', fontsize=11, color='#666')
    
    plt.tight_layout()
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/flow_diagram.png', 
                dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/flow_diagram.pdf', 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("✅ Flow diagram saved as:")
    print("   - docs/flow_diagram.png")
    print("   - docs/flow_diagram.pdf")

if __name__ == "__main__":
    create_flow_diagram()
