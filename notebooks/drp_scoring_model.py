#!/usr/bin/env python3
"""
DRP Rights Access Scoring Model
=====================================
Phana AI Innovation Challenge 2026
Decentralized Rights Protocol -- Nkrumah Joel, UCC

This script:
1. Generates synthetic PHC-structured data (replace with real GSS microdata)
2. Engineers the deprivation composite index
3. Trains Random Forest + XGBoost classifiers
4. Evaluates model + prints results
5. Exports trained model + scaler for FastAPI integration
6. Generates a feature importance chart

When you download the real 2021 PHC microdata from:
  https://microdata.statsghana.gov.gh (Catalog #110)
Replace the synthetic data block (Section 1) with:
  df = pd.read_csv("PHC_2021_household.csv")
  or
  df = pd.read_spss("PHC_2021_household.sav")
"""
