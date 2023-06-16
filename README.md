# CERberus -- guardian against character errors

This Python script provides an implementation of Character Error Rate (CER) calculation between a reference string and a hypothesis string, with various customization options available for pre-processing the strings and detailed reporting of results. It allows you to set specific options such as ignoring case, punctuation, whitespaces, numbers, newlines and returns, and other specific characters.

## Installation & Setup

To clone and run this application, you'll need [Git](https://git-scm.com/), [Python](https://www.python.org/downloads/), and [Anaconda](https://www.anaconda.com/products/distribution) (or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)) installed on your computer. You will also need to install some Python packages to run this application. From your command line, run:

```bash
# Clone this repository
git clone https://github.com/WHaverals/CERberus.git

# Go into the repository
cd CERberus

# Create a dedicated Conda environment
conda create --name cerberus python=3.9.15

# Activate the Conda environment
conda activate cerberus

# Install dependencies
pip install -r requirements.txt
```
After this, you can run the application using the following command:

```bash
python app.py
```

Remember to make sure your `CERberus` Conda environment is activated when you run this app. If it's not, you can activate it with `conda activate CERberus`.

Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000/) (or, possibly, another address that is printed to your console) to view the application in your web browser.

## CERberus

![ CERberus showing off what it's packing!](cerberus.gif)