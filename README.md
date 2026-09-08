[README.md — Blood Glucose Analytics Dashboard.md](https://github.com/user-attachments/files/31965937/README.md.Blood.Glucose.Analytics.Dashboard.md)
# Blood Glucose Analytics Dashboard

An end-to-end personal data analytics project for monitoring blood glucose trends following a physician-prescribed diabetes treatment plan.

The project collects daily blood glucose measurements through Google Forms, stores the responses in Google Sheets, processes the data using Python and Pandas, and presents the results through an interactive Streamlit dashboard.

## Overview

Monitoring blood glucose over time can be challenging when measurements are recorded repeatedly across different dates and meal periods.

This project transforms these daily measurements into structured and visual information to make glucose patterns easier to track and understand.

The dashboard provides an overview of glucose measurements, recent trends, weekly averages, and measurement history.

> **Note:** This project is intended for personal data monitoring and visualization. It is not a medical diagnostic tool and does not determine medication effectiveness or provide treatment recommendations.

---

## Objectives

- Collect blood glucose measurements in a structured format.
- Organize measurements by date and measurement period.
- Clean and transform raw data using Python.
- Analyze blood glucose trends over time.
- Compare measurements across different meal periods.
- Calculate weekly averages to identify longer-term trends.
- Build an interactive dashboard for easier data exploration.

---

## Data Pipeline

```text
Google Forms
     ↓
Google Sheets
     ↓
Python / Pandas
     ↓
Data Cleaning & Transformation
     ↓
Exploratory Data Analysis
     ↓
Plotly Visualizations
     ↓
Streamlit Dashboard
```

### 1. Data Collection

Daily measurements are recorded through a structured Google Form.

The form captures information such as:

- Date
- Blood glucose measurement
- Measurement period
- Meal information
- Physical activity
- Additional notes

### 2. Data Storage

Google Forms responses are automatically stored in Google Sheets, providing a centralized source for the collected data.

### 3. Data Processing

Python and Pandas are used to:

- Convert dates into standardized datetime formats.
- Convert glucose measurements into numeric values.
- Handle missing or invalid records.
- Standardize measurement-period labels.
- Sort measurements chronologically.
- Create weekly periods for aggregated analysis.

### 4. Data Analysis

The processed data is used to explore:

- Blood glucose trends over time.
- Differences between measurement periods.
- Weekly average glucose levels.
- Recent glucose patterns.
- Overall measurement statistics.

### 5. Visualization

Plotly is used to create interactive visualizations, while Streamlit provides the dashboard interface.

---

## Dashboard Features

### Key Metrics

The dashboard provides summary metrics including:

- Latest blood glucose measurement
- Overall average
- Recent 7-day average
- Number of measurements

### Blood Glucose Trend

An interactive time-series visualization shows how blood glucose measurements change over time.

### Measurement Period Analysis

Measurements can be explored according to their relationship with meals, allowing patterns across different measurement periods to be observed.

### Weekly Average

Weekly aggregation provides a higher-level view of glucose patterns and helps reduce the noise of individual measurements.

### Detailed History

A detailed table allows individual measurements to be reviewed alongside their recorded information.

### Interactive Filters

Users can filter the dashboard by:

- Date range
- Measurement period

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing and analysis |
| Pandas | Data cleaning and transformation |
| Plotly | Interactive data visualization |
| Streamlit | Dashboard development |
| Google Forms | Data collection |
| Google Sheets | Data storage |
| GitHub | Version control and project management |

---

## Analytical Approach

The project follows a simple analytical workflow:

**Collect → Clean → Transform → Analyze → Visualize → Monitor**

Rather than treating each glucose measurement as an isolated value, the project organizes measurements longitudinally to make trends and changes over time easier to identify.

---

## Key Questions

The dashboard is designed to help explore questions such as:

1. How does blood glucose change over time?
2. Are there noticeable differences between pre-meal and post-meal measurements?
3. How does the weekly average change over time?
4. How does the most recent period compare with previous measurements?
5. Are there noticeable patterns across different measurement periods?

---

## Limitations

This project has several limitations:

- The dataset represents observations from a single individual.
- The observation period is limited.
- Blood glucose can be affected by multiple factors, including food intake, physical activity, sleep, stress, and medication adherence.
- The project is observational and does not use a controlled experimental design.
- Changes in glucose levels cannot be interpreted as proof that medication caused the observed changes.

Therefore, the dashboard should be viewed as a **personal monitoring and data visualization tool**, rather than a medical decision-making system.

---

## Future Improvements

Potential improvements include:

- Automated data synchronization from Google Sheets.
- Additional statistical analysis.
- More detailed pre-meal vs. post-meal comparisons.
- Glucose variability analysis.
- Automated anomaly detection.
- Trend-based alerts.
- Additional contextual variables such as sleep, exercise, and meal composition.
- Deployment with automated data refresh.

---

## Project Structure

```text
PGDM-Bapa/
│
├── app.py
├── requirements.txt
├── README.md
│
└── ...
```

---

## Project Outcome

This project demonstrates an end-to-end data analytics workflow, from collecting real-world data to transforming, analyzing, and communicating insights through an interactive dashboard.

It combines **data collection, data cleaning, exploratory analysis, visualization, and dashboard development** into a single practical project.
