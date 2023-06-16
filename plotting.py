import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def plot_character_confusions(confusion_stats_df: pd.DataFrame, char: str, top_n: int = 5):
    char_confusions = confusion_stats_df[confusion_stats_df['correct'] == char]

    # If there are no confusions for this character, print a message and return
    if char_confusions.empty:
        print(f"No confusions found for character '{char}'.")
        return go.Figure()

    # Sort by count and select the top_n
    char_confusions = char_confusions.sort_values('ratio', ascending=False).head(top_n)

    # Generate a color map
    cmap = px.colors.sequential.Plasma

    # Plot a bar chart
    fig = go.Figure(data=[
        go.Bar(x=char_confusions['generated'], y=char_confusions['ratio'], 
               marker_color=cmap, name='Ratio')
    ])
    fig.update_layout(title_text=f"Top {top_n} Confusions for Character '{char}'",
                      xaxis_title="Generated Character",
                      yaxis_title="Ratio")

    return fig