# Cinemap

Cinemap is a Python movie discovery tool built with IMDb data and graph-based similarity scoring. It recommends movies based on shared actors, directors, writers, and genres, then explains and visualizes the relationships behind each recommendation.

## Features

- Generate up to 10 recommendations for a selected movie
- Search for movies using favourite actors, directors, writers, and genres
- Find actors, directors, and writers with similar filmographies
- View interactive movie graphs using Plotly and Dash Cytoscape
- Inspect shared features and similarity scores for each recommendation

## Technologies

- Python
- NetworkX
- Plotly
- Dash
- Dash Cytoscape
- IMDb datasets

## Installation

Clone the repository:

```bash
git clone https://github.com/ersun1234567/Cinemap.git
cd Cinemap
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## IMDb Data Setup

Download and extract the following files from the [IMDb datasets page](https://datasets.imdbws.com/):

```text
title.basics.tsv
title.ratings.tsv
name.basics.tsv
title.principals.tsv
```

Place them inside a folder named `data`:

```text
Cinemap/
├── data/
│   ├── title.basics.tsv
│   ├── title.ratings.tsv
│   ├── name.basics.tsv
│   └── title.principals.tsv
├── main.py
└── ...
```

## Running Cinemap

Run the command-line application:

```bash
python main.py
```

The menu allows you to:

1. Generate movie recommendations
2. Search using favourite people and genres
3. Find people with similar filmographies
4. View the movie and person graph
5. Exit the program

Selecting the visualization option launches an interactive graph in your browser.

## Project Structure

- `main.py` — command-line interface
- `data_loader.py` — loads and filters IMDb datasets
- `graph_models.py` — graph and vertex data structures
- `recommendation.py` — recommendation and similarity algorithms
- `visualization.py` — Plotly and Dash Cytoscape visualizations

## Acknowledgements

Cinemap was developed as a University of Toronto CSC project. Movie and contributor information comes from IMDb’s non-commercial datasets.
