import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_flowchart():
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Define boxes [text, x, y, width, height, color]
    boxes = [
        ["Administrative Microdata\n(NEED 2024 - 50k Seed)", 0.3, 0.9, 0.4, 0.08, "#e1f5fe"],
        ["Deterministic\nStratified Expansion", 0.1, 0.75, 0.35, 0.08, "#fff9c4"],
        ["Census 2021 MSOA Marginals\n(Spatial Constraints)", 0.55, 0.75, 0.35, 0.08, "#e8f5e9"],
        ["Synthetic Population\n(684,000 Household Entities)", 0.3, 0.6, 0.4, 0.08, "#f3e5f5"],
        ["UBEM Archetype Mapping\n(Theoretical Need Th)", 0.3, 0.45, 0.4, 0.08, "#fff3e0"],
        ["MSOA-level Aggregation\n(Mean Need Tm)", 0.3, 0.3, 0.4, 0.08, "#e0f2f1"],
        ["Hierarchical Bayesian Model\n(Spatial ICAR Prior)", 0.3, 0.15, 0.4, 0.08, "#ffebee"],
        ["Behaviorally-Adjusted\nInventory (T*)", 0.3, 0.0, 0.4, 0.08, "#c8e6c9"]
    ]
    
    # Draw boxes
    for b in boxes:
        text, x, y, w, h, color = b
        rect = patches.Rectangle((x, y), w, h, linewidth=1, edgecolor='black', facecolor=color)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=11, fontweight='bold')
    
    # Draw arrows
    arrows = [
        ((0.5, 0.9), (0.275, 0.83)), # From Seed to Expansion
        ((0.275, 0.75), (0.5, 0.68)), # From Expansion to Synthetic
        ((0.5, 0.6), (0.5, 0.53)),
        ((0.5, 0.45), (0.5, 0.38)),
        ((0.5, 0.3), (0.5, 0.23)),
        ((0.5, 0.15), (0.5, 0.08)),
        # Side arrow from Census to Expansion
        ((0.55, 0.79), (0.45, 0.79))
    ]
    
    for start, end in arrows:
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8))
        
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.05, 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig("manuscript/figures/fig1.png", dpi=300, bbox_inches='tight')
    print("Saved regenerated Figure 1 flowchart.")

if __name__ == "__main__":
    draw_flowchart()
