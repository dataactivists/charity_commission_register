# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Charity Commission register

# %% [markdown]
# ## Register of merged charities

# %% [markdown]
# ### Intro

# %% [markdown]
# The data can be found at https://www.gov.uk/government/publications/register-of-merged-charities. 

# %% [markdown]
# ### Imports
# %%
import altair as alt

import pandas as pd
import seaborn as sns
from ydata_profiling import ProfileReport
# %% [markdown]
# ### Cleaning

# %%
df = pd.read_csv('../data/mergers_register_march_2024.csv', encoding='cp1252')

# %%
df.head()

# %%
df.dtypes

# %%
# shorten col names
df.columns = [
    'transferor', 'transferee', 'date_vesting', 'date_transferred', 'date_registered'
]

# %%
# convert first 2 cols to str
df['transferor'] = df['transferor'].apply(str).apply(str.strip)
df['transferee'] = df['transferee'].apply(str).apply(str.strip)

# %%
# convert date cols to datetime
date_cols = ['date_vesting', 'date_transferred', 'date_registered']

df[date_cols] = df[date_cols].apply(lambda x: pd.to_datetime(x, format='%d/%m/%Y'))

df.head()

# %%
df['transferor'].sample(50).str[-15:]

# %%
# create charity number cols by extracting contents of last group in parentheses
df['transferor_number'] = df['transferor'].str.lower().str.extract(
    pat='\(([^\(]+?)\)$'
)
df['transferor_number'] = df['transferor_number'].str.replace(pat='[\-\.\/]', repl='-')

df['transferee_number'] = df['transferee'].str.lower().str.extract(
    pat='\(([^\(]+?)\)$'
)
df['transferee_number'] = df['transferee_number'].str.replace(pat='[\-\.\/]', repl='-')

df.iloc[10:20]

# %% [markdown]
# ### Number of mergers over time

# %% [markdown]
# #### Most frequent transferors/transferees

# %%
df['transferor_number'].value_counts()

# %%
df['transferor_number'].str.extract('(\d{5,})').value_counts()
