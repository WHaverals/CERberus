from flask import Flask, request, render_template
from cer_module import cer
from plotting import plot_character_confusions
from dash import Dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px

default_unicode_ranges = {
    'Lowercase Latin alphabet': [(0x0061, 0x007A)],
    'Uppercase Latin alphabet': [(0x0041, 0x005A)],
    'Digits': [(0x0030, 0x0039), (0x2070, 0x2089)],
    'Punctuation': [(0x0021, 0x002E), (0x005B, 0x005F)],
    'MUFI Glyphs': [(0xf0, 0xf0), (0xf8, 0xf8), (0x100, 0x101), (0x112, 0x113), (0x127, 0x127), (0x12b, 0x12b), (0x14c, 0x14d), (0x16b, 0x16b), (0x1b6, 0x1b6), (0x223, 0x223), (0x233, 0x233), (0x2b3, 0x2b3), (0x2bc, 0x2bc), (0x2e2, 0x2e2), (0x304, 0x304), (0x3c9, 0x3c9), (0x1d43, 0x1d43), (0x1d48, 0x1d49), (0x1d50, 0x1d50), (0x1d52, 0x1d52), (0x1d57, 0x1d58), (0x1d5b, 0x1d5b), (0x1d9c, 0x1d9c), (0x1da6, 0x1da6), (0x1dd1, 0x1dd1), (0x1de3, 0x1de3), (0x1e9c, 0x1e9c), (0x2071, 0x2071), (0x207f, 0x207f), (0x2184, 0x2184), (0xa750, 0xa753), (0xa759, 0xa759), (0xa75c, 0xa75f), (0xa76b, 0xa76b), (0xa76e, 0xa770), (0xa78f, 0xa78f), (0xe154, 0xe154), (0xe1dc, 0xe1dc), (0xe554, 0xe554), (0xe5b8, 0xe5b8), (0xe5dc, 0xe5dc), (0xe665, 0xe665), (0xe681, 0xe681), (0xe74d, 0xe74d), (0xe8e5, 0xe8e5), (0xeed7, 0xeed7)]
}

app = Flask(__name__)

# define your Dash app inside your Flask app
app_dash = Dash(__name__, server=app, url_base_pathname='/dash/')

# layout for your Dash app
app_dash.layout = html.Div([
    html.H1("Character Confusion Plot"),
    dcc.Input(
        id='input-char',
        type='text',
        placeholder="Enter a character...",
        debounce=True
    ),
    dcc.Graph(id='char-confusion-plot')
])

@app_dash.callback(
    Output('char-confusion-plot', 'figure'),
    [Input('input-char', 'value')]
)
def update_output(value):
    confusion_stats_df = pd.read_csv('confusion_stats.csv')  # Load the DataFrame here
    if value is not None and len(value) == 1:
        fig = plot_character_confusions(confusion_stats_df, value, top_n=5)
        return fig
    else:
        return go.Figure()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cer', methods=['POST'])
def calculate_cer():
    reference = request.form.get('reference')
    hypothesis = request.form.get('hypothesis')

    # Boolean options
    options = ['ignore_punctuation', 'ignore_case', 'ignore_whitespace', 'ignore_numbers', 'ignore_newlines_and_returns']
    options_dict = {opt: opt in request.form for opt in options}

    # Parse unicode ranges
    unicode_ranges_names = request.form.getlist('unicode_ranges')
    unicode_ranges = {name: default_unicode_ranges[name] for name in unicode_ranges_names}

    # Parse custom range
    custom_range_name = request.form.get('custom_range_name')
    custom_range_start = request.form.get('custom_range_start')
    custom_range_end = request.form.get('custom_range_end')
    if custom_range_name and custom_range_start and custom_range_end:
        try:
            custom_range_start = int(custom_range_start, 16)  # Assuming the input is hexadecimal
            custom_range_end = int(custom_range_end, 16)    # Assuming the input is hexadecimal
            custom_range_dict = {custom_range_name: [(custom_range_start, custom_range_end)]}
            unicode_ranges.update(custom_range_dict)
        except ValueError:
            return "Error parsing custom range. Please check the input format."

    # Get ignore_chars
    ignore_chars = request.form.get('ignore_chars')

    # Get other inputs from the form
    discard_lines_with_chars = request.form.get('discard_lines_with_chars')
    replace_chars = request.form.get('replace_chars')
    replacement_chars = request.form.get('replacement_chars')

    result = cer(
        reference, 
        hypothesis, 
        discard_lines_with_chars=discard_lines_with_chars, 
        replace_chars=replace_chars, 
        replacement_chars=replacement_chars, 
        **options_dict, 
        unicode_ranges=unicode_ranges, 
        ignore_chars=ignore_chars
    )
        
    # New code: Save the DataFrame to a file
    confusion_stats_df = pd.DataFrame(result['confusionStats'])
    confusion_stats_df.to_csv('confusion_stats.csv', index=False)

    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)