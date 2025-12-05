import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

def create_workflow_processing_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(14, 28))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 30)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Colors
    main_border = '#333333'
    step_bg = '#F5F5F5'
    highlight_blue = '#E3F2FD'
    success_green = '#E8F5E9'
    
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
    ax.text(7, 29.3, '3.2 Workflow Processing Architecture', 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1565C0')
    
    # ==================== MAIN CONTAINER ====================
    draw_box(0.5, 0.5, 13, 28.3, 'white', main_border, 2, '--')
    ax.text(7, 28.4, 'INCIDENT PROCESSING WORKFLOW', 
            ha='center', va='center', fontsize=12, fontweight='bold')
    
    # ==================== USER BOX ====================
    draw_box(1, 26.5, 2, 1, 'white', main_border)
    ax.text(2, 27, 'User', ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(3.2, 26.5, 'Creates Incident', ha='left', va='center', fontsize=9)
    
    # Arrow down
    draw_arrow((2, 26.5), (2, 25.8))
    
    # ==================== SERVICENOW INCIDENT RECORD ====================
    draw_box(1, 23, 3.5, 2.5, 'white', main_border)
    ax.text(1.3, 25.2, 'ServiceNow', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.3, 24.7, 'Incident Record', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.3, 24.1, 'Description:', ha='left', va='center', fontsize=8)
    ax.text(1.3, 23.7, '"Create user', ha='left', va='center', fontsize=8, style='italic')
    ax.text(1.3, 23.3, '  user11 in', ha='left', va='center', fontsize=8, style='italic')
    ax.text(1.3, 22.9, '  redshift', ha='left', va='center', fontsize=8, style='italic')
    ax.text(1.3, 22.5, '  cluster 1"', ha='left', va='center', fontsize=8, style='italic')
    
    # Arrow down
    draw_arrow((2.75, 23), (2.75, 22.3))
    
    # ==================== INCIDENT PROCESSOR CONTAINER ====================
    draw_box(1, 4.5, 12, 17.5, 'white', main_border, 2)
    ax.text(7, 21.5, 'INCIDENT PROCESSOR', 
            ha='center', va='center', fontsize=11, fontweight='bold')
    
    # ==================== STEP 1: FETCH INCIDENT ====================
    draw_box(1.5, 18.8, 10, 2.2, step_bg, '#666')
    ax.text(1.8, 20.6, 'Step 1: FETCH INCIDENT', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.8, 20.1, 'ServiceNowClient.get_incident(incident_number)', ha='left', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 19.6, 'GET /api/now/table/incident?number=INC0010015', ha='left', va='center', fontsize=8, family='monospace', color='#1565C0')
    
    # Arrow down
    draw_arrow((6.5, 18.8), (6.5, 18.2))
    
    # ==================== STEP 2: CHECK IF PROCESSED ====================
    draw_box(1.5, 15.8, 10, 2, step_bg, '#666')
    ax.text(1.8, 17.4, 'Step 2: CHECK IF PROCESSED', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.8, 16.9, 'ServiceNowClient.is_already_processed(incident)', ha='left', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 16.4, 'Check work_notes for completion indicators', ha='left', va='center', fontsize=8, color='#666')
    
    # Arrow down
    draw_arrow((6.5, 15.8), (6.5, 15.2))
    
    # ==================== STEP 3: PARSE INCIDENT ====================
    draw_box(1.5, 11.8, 10, 3, step_bg, '#666')
    ax.text(1.8, 14.4, 'Step 3: PARSE INCIDENT', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.8, 13.9, 'IncidentParser.parse_incident(incident)', ha='left', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 13.3, 'Regex Patterns:', ha='left', va='center', fontsize=8, fontweight='bold')
    ax.text(1.8, 12.8, "• Username: r'user\\s+named\\s+(\\w+)'", ha='left', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 12.3, "• Cluster:  r'cluster[:\\s-]*(\\d+)'", ha='left', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 11.8, 'Result: {username: "user11", cluster: "redshift-cluster-1"}', ha='left', va='center', fontsize=8, family='monospace', color='#2E7D32')
    
    # Arrow down
    draw_arrow((6.5, 11.5), (6.5, 10.9))
    
    # ==================== STEP 4: EXECUTE REDSHIFT OPERATIONS ====================
    draw_box(1.5, 7, 10, 3.5, highlight_blue, '#1565C0')
    ax.text(1.8, 10.1, 'Step 4: EXECUTE REDSHIFT OPERATIONS', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.8, 9.5, 'RedshiftClient.user_exists(username)', ha='left', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 9.0, "→ SQL: SELECT usename FROM pg_user WHERE usename='user11'", ha='left', va='center', fontsize=8, family='monospace', color='#1565C0')
    ax.text(1.8, 8.4, 'RedshiftClient.create_user(username)', ha='left', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 7.9, '→ SQL: CREATE USER user11 PASSWORD DISABLE', ha='left', va='center', fontsize=8, family='monospace', color='#1565C0')
    ax.text(1.8, 7.3, 'RedshiftClient.verify_user(username)', ha='left', va='center', fontsize=8, family='monospace')
    
    # Arrow down
    draw_arrow((6.5, 7), (6.5, 6.4))
    
    # ==================== STEP 5: UPDATE INCIDENT ====================
    draw_box(1.5, 4.8, 10, 1.8, step_bg, '#666')
    ax.text(1.8, 6.2, 'Step 5: UPDATE INCIDENT', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.8, 5.7, 'ServiceNowClient.add_work_note(incident_number, result)', ha='left', va='center', fontsize=8, family='monospace')
    ax.text(1.8, 5.2, 'PUT /api/now/table/incident/{sys_id}', ha='left', va='center', fontsize=8, family='monospace', color='#1565C0')
    
    # Arrow down (outside processor box)
    draw_arrow((6.5, 4.5), (6.5, 3.8))
    
    # ==================== SERVICENOW UPDATED INCIDENT ====================
    draw_box(1, 1, 4, 2.5, success_green, '#2E7D32')
    ax.text(1.3, 3.2, 'ServiceNow', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.3, 2.8, 'Updated Incident', ha='left', va='center', fontsize=9, fontweight='bold')
    ax.text(1.3, 2.3, 'Work Notes:', ha='left', va='center', fontsize=8)
    ax.text(1.3, 1.9, '"✓ TASK', ha='left', va='center', fontsize=8, color='#2E7D32')
    ax.text(1.3, 1.5, '  COMPLETED..."', ha='left', va='center', fontsize=8, color='#2E7D32')
    ax.text(1.3, 1.1, 'State: Resolved', ha='left', va='center', fontsize=8, fontweight='bold', color='#2E7D32')
    
    plt.tight_layout()
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/workflow_processing_diagram.png', 
                dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('/workspaces/sample-workflow/servicenow-mcp/docs/workflow_processing_diagram.pdf', 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("✅ Workflow Processing diagram saved as:")
    print("   - docs/workflow_processing_diagram.png")
    print("   - docs/workflow_processing_diagram.pdf")

if __name__ == "__main__":
    create_workflow_processing_diagram()
