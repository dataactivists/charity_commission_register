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
# and filling any null values with any string of 5+ numbers
df['transferor_number'] = df['transferor'].str.lower().str.extract(
    pat='\(([^\(]+?)\)$'
)
df['transferor_number'] = df['transferor_number'].str.replace(pat='[\-\.\/]', repl='-')
df['transferor_number'] = df['transferor_number'].combine_first(
    df['transferor'].str.extract(pat='(\d{5,})')
)

df['transferee_number'] = df['transferee'].str.lower().str.extract(
    pat='\(([^\(]+?)\)$'
)
df['transferee_number'] = df['transferee_number'].str.replace(pat='[\-\.\/]', repl='-')
df['transferee_number'] = df['transferee_number'].combine_first(
    df['transferee'].str.extract(pat='(\d{5,})')
)

# %%
# list values that are not charity numbers
df['transferor_number'].loc[
    ~df['transferor_number'].apply(str).str.contains(r'\d')
].value_counts()

# %%
# standardise values
df['transferor_number'] = df['transferor_number'].replace(
    to_replace={
        'unregistered .*': 'unregistered',
        'exempt .*': 'exempt',
        'excepted .*': 'excepted',
        'unincorporated .*': 'unincorporated',
        'not registered': 'unregistered',
    },
    regex=True
).replace(
    to_replace={
        value: 'other' for value in [
            'unrestricted assets only', 
            'formerly known as mount zion evangelical church',
            'all excepted',
            'herne bay branch',
            'bottley',
            'mrs m gee trust',
        ]
    }
)

df['transferor_number'].loc[
    ~df['transferor_number'].apply(str).str.contains(r'\d')
].value_counts()

# %%
# list values that are not charity numbers
df['transferee_number'].loc[
    ~df['transferee_number'].apply(str).str.contains(r'\d')
].value_counts()

# %%
# standardise values
df['transferee_number'] = df['transferee_number'].replace(
    to_replace={
        'exempt charity': 'exempt',
        'incorporating the merrett bequest': 'other',
        'cio': 'other',
        'picpus': 'other',
    }
)

df['transferee_number'].loc[
    ~df['transferee_number'].apply(str).str.contains(r'\d')
].value_counts()

# %% [markdown]
# ### Number of mergers over time

# %% [markdown]
# #### Most frequent transferors

# %%
df['transferor_number'].value_counts()[:10]

# %%
df['transferor_number'].value_counts().iloc[:100].plot(kind='bar').set_xticks([])

# %% [markdown]
# Most transferors are unregistered, exempt, or excepted. 
#
# Most registered transferors are only transferors once or twice (which makes sense, as they get merged into the transferee).

# %%
df[['transferor', 'transferee']].loc[df['transferor'].str.contains('1053467')]

# %%
df['transferor'].value_counts()[:10]

# %% [markdown]
# In one case, a number of hospital departments seem to have merged into one entity (*The County Durham and Darlington NHS Foundation Trust Charity*). 
#
# *The Parochial Church Council of the Ecclesiastical Parish of The A453 Churches of South Nottinghamshire* has managed to be the transferor 5 times. 


# %%
df['transferor_number'].str.extract('(\d{5,})').value_counts()
