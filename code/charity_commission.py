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
# ## Roadmap

# %% [markdown]
# This repo aims to be an exhaustive analysis of the data released by the Charity Commission at https://register-of-charities.charitycommission.gov.uk/register/full-register-download. 
#
# Some of the questions we want to look at:
# - [x] most frequent transferors
# - [x] most frequent transferees
# - [x] evolution of number of mergers per year
# - [ ] the average time gap between each merger for repeat transferors/transferees?
# - [ ] what are the annual returns of the transferee before/after the merger?
# - [ ] what's the size of transferors/transferees in terms of annual return?
# - [ ] what is the median number of trustees per charity?
# - [ ] who are "repeat trustees"?

# %% [markdown]
# For starters, the analysis covers the [Register of merged charities](https://www.gov.uk/government/publications/register-of-merged-charities) data.

# %% [markdown]
# See the [notebook](https://github.com/harabat/charity_commission_register/blob/main/code/charity_commission.ipynb) for the charts.

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
import json
import pandas as pd
import seaborn as sns
from ydata_profiling import ProfileReport
# %% [markdown]
# ### Cleaning

# %% [markdown]
# #### Cleaning `merger` data

# %% [markdown]
# ##### Load data

# %%
df = pd.read_csv('../data/mergers_register_march_2024.csv', encoding='cp1252')

# %% [markdown]
# ##### Cols

# %%
df.head()

# %%
# shorten col names
df.columns = [
    'transferor', 'transferee', 'date_vesting', 'date_transferred', 'date_registered'
]

# %%
df.info()

# %%
# drop column with null values
df = df.drop(columns='date_vesting')

# %% [markdown]
# ##### `dtypes`

# %%
df.dtypes

# %%
# convert first 2 cols to str
df['transferor'] = df['transferor'].apply(str).apply(str.strip)
df['transferee'] = df['transferee'].apply(str).apply(str.strip)

# %%
# convert date cols to datetime
date_cols = ['date_transferred', 'date_registered']

df[date_cols] = df[date_cols].apply(lambda x: pd.to_datetime(x, format='%d/%m/%Y'))

df.head()

# %%

# %% [markdown]
# ##### Extract charity numbers

# %%
# check how charity numbers are indicated
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
# standardise values that are not charity numbers
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
# standardise values that are not charity numbers
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
# #### Joining with `annual returns` data

# %%
with open(
    '../data/publicextract.charity_annual_return_history.json', 'r', encoding='utf-8-sig'
) as file:
    data = json.load(file)

df_ar = pd.DataFrame(data)

# %%
df_ar.head()

# %%
df_ar = df_ar[[
    'date_of_extract',
    'registered_charity_number',
    'fin_period_start_date',
    'fin_period_end_date',
    'total_gross_income',
    'total_gross_expenditure',
]]

# %%
df_ar.dtypes

# %%
date_cols = [
    'date_of_extract',
    'fin_period_start_date',
    'fin_period_end_date',
]

df_ar[date_cols] = df_ar[date_cols].apply(pd.to_datetime)

df_ar.head()

# %%
df_ar.dtypes

# %%
df_ar['fin_start_year'] = df_ar['fin_period_start_date'].dt.year
df_ar['fin_end_year'] = df_ar['fin_period_end_date'].dt.year

# %%
df_ar.head()

# %%
df['merger_year'] = df['date_transferred'].dt.year

# %% [markdown]
# ### Number of mergers over time

# %% [markdown]
# #### Most frequent transferors

# %%
df['transferor_number'].value_counts()[:10].to_frame()

# %% [markdown]
# Most transferors are unregistered, exempt, or excepted.
#
# The [Guidance about the register of merged charities](https://www.gov.uk/government/publications/register-of-merged-charities/guidance-about-the-register-of-merged-charities#different-types-of-merger) states:
#
# > There are different types of merger:
# > 
# >   - merging with an existing charity
# >   - merging with a new charity you have set up for the purpose of merging
# >   - changing structure - usually a trust or unincorporated association that wants to change to a CIO or charitable company.
#
#
# The prevalence of unregistered/exempt/excepted transferors probably indicates one of two things:
#
# - Mergers of **very small charities (which are unregistered/exempt) officially joining bigger ones**. It's likely that these small charities are merging with larger ones to gain economies of scale, access to more resources, or to increase their impact. Alternatively, they might be facing hurdles due to funding constraints, regulatory burdens, or other challenges, and merging with a larger charity is a way to ensure their assets and mission continue.
# - Mergers of charities into **a new structure (CIO or charitable company)**.

# %%
transferor_freqs = df['transferor_number'].value_counts().value_counts().reset_index(name='freqs')

transferor_freqs = transferor_freqs.sort_values(by='count')

transferor_freqs

# %% [markdown]
# Most registered transferors have only been in the position of transferring charity once or twice.
#
# This makes sense, since the transferor charity typically ceases to exist as a separate entity after the merger. 
#
# The outcomes of a merger, as stated by the [Guidance about the register of merged charities](https://www.gov.uk/government/publications/register-of-merged-charities/guidance-about-the-register-of-merged-charities#why-register):
#
# > - your charity has closed or will close as a result of transferring your assets or
# > - your charity has not closed only because it has permanent endowment which will not be transferred to the charity you are merging with
#
# These repeat transferors might be falling into this second case. 

# %%
df[['transferor', 'transferee']].loc[df['transferor'].str.contains('1053467')].head()

# %% [markdown]
# *The County Durham and Darlington NHS Foundation Trust Charity* seems to be a case of a large consolidation.
#
# A number of department-specific NHS charities have merged into one entity. The aim could be to consolidate funds/reduce administrative overhead/streamline operations. 

# %%
df['transferor'].value_counts()[:10]

# %%
df.loc[df['transferor_number'] == '1189059'].iloc[:,:2].values

# %% [markdown]
# *The Parochial Church Council of the Ecclesiastical Parish of The A453 Churches of South Nottinghamshire* seems to be an example of a "merged" charity splitting into separate entities. 
#
# It is the most frequent transferor among registered charities, having been in that position 5 times.
#
# While this seems to be a reverse merger, it could also be the parent charity distributing some assets to children charities. 

# %% [markdown]
# #### Most frequent transferees

# %%
df['transferee_number'].value_counts()[:10]

# %%
transferee_freqs = df['transferee_number'].value_counts().value_counts().reset_index(name='freqs')

transferee_freqs = transferee_freqs.sort_values(by='count')

transferee_freqs

# %%
chart = (
    alt.Chart(transferee_freqs)
    .mark_bar()
    .encode(
        alt.X('count:Q'),
        alt.Y('freqs:Q')
    )
)

chart

# %%
df['transferee_number'].value_counts().iloc[:100].plot(kind='bar').set_xticks([])

# %% [markdown]
# Without counting the outlier that merged 1200+ times, some transferees have gone through mergers >40 times. 
#
# Most transferees only go through a merger <5 times.

# %%
df['transferee'].value_counts()[:10]

# %%
df[['transferor', 'transferee']].loc[
    df['transferee'].str.contains('Kingdom Hall Trust')
].head()

# %%
df[['transferor', 'transferee']].loc[
    df['transferee'].str.contains('Victim Support')
].head()

# %%
df[['transferor', 'transferee']].loc[
    df['transferee'].str.contains('Mission to Seafarers')
].head()

# %% [markdown]
# Summary from a [Brave](https://search.brave.com/search?q=The+Kingdom+Hall+Trust+&summary=1) search:
#
# The Kingdom Hall Trust:
# - Previously known as the London Company of Kingdom Witnesses, it was established on 28th July 1939 and changed its name to The Kingdom Hall Trust on 20th June 1994.
# - It is a charity associated with Jehovah’s Witnesses, with the charity number GB-CHC-275946.
# - The charity has undergone a significant merger in 2022, incorporating 1,279 Jehovah’s Witness congregations into the national charity. This is considered one of the largest charity mergers ever.

# %% [markdown]
# #### Count of mergers per year

# %%
merger_counts = df.groupby(
    df['date_registered'].dt.year, as_index=True
)['date_registered'].count()

merger_counts = merger_counts.to_frame('count').reset_index()

merger_counts.T

# %%
chart = (
    alt.Chart(merger_counts)
    .mark_bar()
    .encode(
        alt.Y('date_registered:N', title=''),
        alt.X('count:Q', title=''),
        alt.Color('date_registered:N', legend=None, scale=alt.Scale(scheme='dark2')),
    )
    .properties(
        title='Mergers per year, 11/2007-03/2024',
        width=600
    )
)
chart
