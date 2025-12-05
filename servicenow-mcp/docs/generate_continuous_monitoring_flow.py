import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse
import numpy as np

def create_continuous_monitoring_flow():
    fig, ax = plt.subplots(1, 1, figsize=(14, 14))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 16)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Colors matching the reference style
    process_yellow = '#FFF9C4'
    orange_border = '#FF6F00'
    blue_border = '#1565C0'
    
    # Helper function to draw rounded rectangle with dashed border
    def draw_box(x, y, width, height, color='white', border_color='#333', linewidth=1.5, linestyle='-'):
        box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                             boxstyle="round,pad=0.03,rounding_size=0.1",
                             facecolor=color, edgecolor=border_color, 
                             linewidth=linewidth, linestyle=linestyle)
        ax.add_patch(box)
    
    # Helper function to draw arrow
    def draw_arrow(start, end, color='#333'):
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    
    # ==================== TITLE ====================
    ax.text(7, 15.3, '5.2 Continuous Monitoring Flow', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1565C0')
    
    # ==================== MAIN CONTAINER - MONITORING MODE ====================
    draw_box(7, 8.5, 12, 12, 'white', orange_border, 2, '--')
    ax.text(7, 14, 'MONITORING MODE', ha='center', va='center', fontsize=12, fontweight='bold')
    
    # ==================== START MONITOR BOX ====================
    draw_box(3, 12, 2.5, 1.2, process_yellow, '#333', 1.5)
    ax.text(3, 12.2, 'Start', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(3, 11.7, 'Monitor', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Arrow down from Start Monitor
    draw_arrow((3, 11.4), (3, 10.8))
    
    # ==================== POLL LOOP BOX ====================
    draw_box(7, 7.5, 10, 5.5, 'white', blue_border, 2, '--')
    ax.text(7, 10, 'Poll Loop', ha='center', va='center', fontsize=11, fontweight='bold')
    
    # Code content inside Poll Loop
    ax.text(2.5, 9.2, 'while monitoring:', ha='left', va='center', fontsize=10, family='monospace')
    ax.text(3, 8.6, 'incidents = ServiceNow.list_incidents(from_date)', ha='left', va='center', fontsize=9, family='monospace')
    ax.text(3, 8.0, 'for incident in incidents:', ha='left', va='center', fontsize=9, family='monospace')
    ax.text(3.5, 7.4, 'if not processed and is_redshift_related:', ha='left', va='center', fontsize=9, family='monospace')
    ax.text(4, 6.8, 'process_incident(incident)', ha='left', va='center', fontsize=9, family='monospace')
    ax.text(3, 6.2, 'sleep(POLL_INTERVAL)  # default: 10 seconds', ha='left', va='center', fontsize=9, family='monospace', color='#666')
    
    # Arrow down from Poll Loop
    draw_arrow((7, 4.7), (7, 4.1))
    
    # ==================== STOP MONITOR BOX ====================
    draw_box(3, 3, 2.5, 1.2, process_yellow, '#333', 1.5)
    ax.text(3, 3.2, 'Stop', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(3, 2.7, 'Monitor', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Connecting line from Poll Loop to Stop Monitor
    ax.plot([3, 3], [4.7, 3.6], color='#333', linewidth=1.5)
    ax.plot([3, 7], [4.7, 4.7], color='#333', linewidth=1.5)
    
    plt.tight_layout()
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/continuous_monitoring_flow.png', 
                dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/continuous_monitoring_flow.pdf', 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("Continuous Monitoring Flow diagram saved as:")
    print("   - docs/continuous_monitoring_flow.png")
    print("   - docs/continuous_monitoring_flow.pdf")

if __name__ == "__main__":
    create_continuous_monitoring_flow()
