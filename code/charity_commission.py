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
# # Charity Commission register: exploratory analysis

# %% [markdown]
# ## Roadmap

# %% [markdown]
# This repo aims to be an exhaustive analysis of the data released by the Charity Commission at https://register-of-charities.charitycommission.gov.uk/register/full-register-download.
#
# Some of the questions we want to look at:
# - [x] most frequent transferors
# - [x] most frequent transferees
# - [x] evolution of number of mergers per year
# - [x] what are the annual returns of the transferee before/after the merger?
# - [x] what's the size of transferors/transferees in terms of annual return?
# - [ ] what is the median number of trustees per charity?
# - [ ] who are "repeat trustees"?

# %% [markdown]
# For starters, the analysis covers the [Register of merged charities](https://www.gov.uk/government/publications/register-of-merged-charities) data.

# %% [markdown]
# See the [notebook](https://github.com/dataactivists/charity_commission_register/blob/main/code/charity_commission.ipynb) for the charts.

# %% [markdown]
# ## Imports
# %%
import altair as alt
import dataframe_image as dfi
import json
import numpy as np
import pandas as pd
import seaborn as sns
# %% [markdown]
# ## Register of merged charities

# %% [markdown]
# ### Intro

# %% [markdown]
# The data can be found at https://www.gov.uk/government/publications/register-of-merged-charities.

# %% [markdown]
# - [Merging two or more Charitable Incorporated Organisations (CIOs)](https://www.gov.uk/government/publications/register-of-merged-charities/guidance-about-the-register-of-merged-charities#merging-two-or-more-charitable-incorporated-organisations-cios) does not require the merger to be registered. Consequently, the register of merged charities will be missing this data. Does this data need to be FOIA'd?

# %% [markdown]
# ### Cleaning `merger` data

# %% [markdown]
# #### Load data

# %%
df = pd.read_csv('../data/mergers_register_march_2024.csv', encoding='cp1252')

# %% [markdown]
# #### Cols

# %%
df.head()

# %%
# shorten col names
df.columns = [
    'transferor',
    'transferee',
    'date_vesting',
    'date_transferred',
    'date_registered',
]

# %%
df.info()

# %%
# drop column with null values
df = df.drop(columns='date_vesting')

# %% [markdown]
# #### `dtypes`

# %%
df.dtypes

# %%
df.convert_dtypes().dtypes

# %%
# strip whitespace
df['transferor'] = df['transferor'].apply(str.strip)
df['transferee'] = df['transferee'].apply(str.strip)

# %%
# convert date cols to datetime
date_cols = ['date_transferred', 'date_registered']

df[date_cols] = df[date_cols].apply(lambda x: pd.to_datetime(x, format='%d/%m/%Y'))

df.head()

# %% [markdown]
# #### Date cols

# %% [markdown]
# This dataset contains transfers dated from 1990, while registrations only start in 2007.

# %%
# calculate timespan between date of transfer and date of registration
df['registered-transfer'] = (
    df['date_registered'] - df['date_transferred']
).dt.days / 365

df.sort_values('registered-transfer')

# %%
# count of transfer and registration by year

chart = (
    alt.Chart(df[['date_registered', 'date_transferred']])
    .mark_line(point=alt.OverlayMarkDef(filled=False))
    .transform_calculate(year_registration='year(datum.date_registered)')
    .transform_calculate(year_transfer='year(datum.date_transferred)')
    .transform_fold(['year_registration', 'year_transfer'], as_=['type', 'year'])
    .encode(
        alt.X('year:O').title('Year'),
        alt.Y('count():Q').title(''),
        alt.Color('type:N').legend(title='Type'), 
    )
    .properties(title='Count of transfers and registrations by year')
)

chart.save('../charts/count_transfer_registration_year.png')

chart

# %%
# distribution of timespans between transfer and registration
chart_diff_line = (
    alt.Chart(df[['date_transferred', 'registered-transfer']])
    .mark_line(color='darkred')
    .encode(
        alt.X('year(date_transferred):T').title('year of transfer'),
        alt.Y('registered-transfer:Q').title('Timespan between transfer and registration'),
    )
)

chart_diff_hist = (
    alt.Chart(df['registered-transfer'].to_frame())
    .mark_bar(color='darkred')
    .encode(
        alt.X('count():Q').title('frequencies of specific timespans'),
        alt.Y('registered-transfer:Q').title('').axis(labels=False),
    )
)

chart = (
    alt.hconcat(chart_diff_line, chart_diff_hist).resolve_axis(y='shared')
    .properties(title='Patterns of number of years between transfer and registration')
)

chart.save('../charts/diff_transfer_registration_year.png')

chart

# %%
df.loc[df['registered-transfer'] > 10].sort_values(
    'registered-transfer', ascending=False
)

# %% [markdown]
# It seems that the *Register of merged charities* contains mergers from 1990, while the registrations start in late 2007.
#
# It seems unlikely that these very few ancient transfers and their late registrations represent reality. The repetitive seesaw pattern also seems to indicate errors, though it's not obvious what it's due to.
#
# We'll choose to drop any transfers from <2008 in our analysis, as they are few and represent the bulk of the long `registered-transfer` durations.

# %%
# drop transfers from <2008
df = df.loc[df['date_transferred'].dt.year >= 2008]

# %%
# count of transfer and registration by year

chart = (
    alt.Chart(df[['date_registered', 'date_transferred']])
    .mark_line(point=alt.OverlayMarkDef(filled=False))
    .transform_calculate(year_registration='year(datum.date_registered)')
    .transform_calculate(year_transfer='year(datum.date_transferred)')
    .transform_fold(['year_registration', 'year_transfer'], as_=['type', 'year'])
    .encode(
        alt.X('year:O').title('Year'),
        alt.Y('count():Q').title(''),
        alt.Color('type:N').legend(title='Type'), 
    )
    .properties(title='Count of transfers and registrations by year (after 2007)')
)

chart.save('../charts/count_transfer_registration_year_trimmed.png')

chart

# %%
# distribution of timespans between transfer and registration
chart_diff_line = (
    alt.Chart(df[['date_transferred', 'registered-transfer']])
    .mark_line(color='darkred')
    .encode(
        alt.X('year(date_transferred):T').title('year of transfer'),
        alt.Y('registered-transfer:Q').title('Timespan between transfer and registration'),
    )
)

chart_diff_hist = (
    alt.Chart(df['registered-transfer'].to_frame())
    .mark_bar(color='darkred')
    .encode(
        alt.X('count():Q').title('frequencies of specific timespans'),
        alt.Y('registered-transfer:Q').title('').axis(labels=False),
    )
)

chart = (
    alt.hconcat(chart_diff_line, chart_diff_hist).resolve_axis(y='shared')
    .properties(title='Patterns of number of years between transfer and registration (after 2007)')
)

chart.save('../charts/diff_transfer_registration_year_trimmed.png')

chart

# %% [markdown]
# #### Extract charity numbers

# %%
# check how charity numbers are indicated at end of string
df['transferor'].sample(10, random_state=42).str[-35:]

# %%
# separators in charity numbers
df['transferor'].str.extract(r'\(\d+(\D)\d+\)$').dropna()[0].unique()

# %%
# create charity number cols by extracting contents of last group in parentheses
# and filling any null values with any string of 5+ digits contained in the string
df['transferor_number'] = df['transferor'].str.lower().str.extract(
    pat=r'\(([^\(]+?)\)$'
)
df['transferor_number'] = df['transferor_number'].str.replace(pat=r'[\-\.\/]', repl='-')
df['transferor_number'] = df['transferor_number'].combine_first(
    df['transferor'].str.extract(pat=r'(\d{5,})')[0]
)

df['transferee_number'] = df['transferee'].str.lower().str.extract(
    pat=r'\(([^\(]+?)\)$'
)
df['transferee_number'] = df['transferee_number'].str.replace(pat=r'[\-\.\/]', repl='-')
df['transferee_number'] = df['transferee_number'].combine_first(
    df['transferee'].str.extract(pat=r'(\d{5,})')[0]
)

# %%
# list values that are not charity numbers
no_charity_number_transferors = df['transferor_number'].loc[
    df['transferor_number'].apply(str).str.contains(r'[a-zA-Z]')
].value_counts().to_frame()

dfi.export(
    no_charity_number_transferors,
    '../charts/no_charity_number_transferors.png',
    table_conversion='selenium'
)

no_charity_number_transferors

# %%
# standardise values that are not charity numbers
df['transferor_number'] = df['transferor_number'].replace(
    to_replace={
        'unregistered .*': 'unregistered',
        'exempt.*': 'exempt',
        '.*excepted.*': 'excepted',
        'unincorporated .*': 'unincorporated',
        'not registered': 'unregistered',
    },
    regex=True,
).replace(
    to_replace={
        value: 'other' for value in [
            'unrestricted assets only', 
            'formerly known as mount zion evangelical church',
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
no_charity_number_transferees = df['transferee_number'].loc[
    df['transferee_number'].apply(str).str.contains(r'[a-zA-Z]')
].value_counts().to_frame()

dfi.export(
    no_charity_number_transferees,
    '../charts/no_charity_number_transferees.png',
    table_conversion='selenium'
)

no_charity_number_transferees

# %%
# standardise values that are not charity numbers
df['transferee_number'] = df['transferee_number'].replace(
    to_replace={
        'exempt.*': 'exempt',
        'incorporating the merrett bequest': 'other',
        'cio': 'other',
        'picpus': 'other',
    },
    regex=True,
)

df['transferee_number'].loc[
    df['transferee_number'].apply(str).str.contains(r'[a-zA-Z]')
].value_counts()

# %% [markdown]
# Charity numbers are generally indicated in the data files as a series of digits between parentheses at the end of the charity name: for example, `Crisis UK (1082947)`.
#
# The charity numbers are sometimes not between parentheses, or contain varying separator characters (`1170369-1` vs `1053467.01`), or the parentheses contain some other information.
#
# Often, the charity is exempt from having a registration number, and the reason is often indicated, but it is not provided systematically, and the wording varies greatly.
#
# That **the charity numbers or their absence are not indicated in a standardised way** translates to a **need to identify and evaluate the discrepancies case by case**, as this is key information which cannot be discarded. For example, to find which charities are exempt from registration, one first needs to find the many ways that this information is conveyed ("exempt", "excepted", "all exempted", etc.).

# %% [markdown]
# #### Charity name spelling

# %%
duplicate_names = df.loc[
    ~(df['transferee_number'].apply(str).str.contains(r'[a-zA-Z]')),
    ['transferee_number', 'transferee']
].drop_duplicates().groupby(
    'transferee_number'
).count().sort_values('transferee')

duplicate_names = duplicate_names.loc[
    duplicate_names['transferee'] > 1
]

duplicate_names.head()

# %%
df.set_index('transferee_number').loc[
    duplicate_names.index,
    'transferee'
].drop_duplicates().sort_values().values

# %% [markdown]
# ### Number of mergers over time

# %% [markdown]
# #### Most frequent transferors

# %%
# registered vs unregistered
registered_vs_unregistered_transferors = df['transferor_number'].apply(
    lambda x: 'exempt/unregistered/similar' if str(x).isalpha() else 'registered'
).value_counts().to_frame()

dfi.export(
    registered_vs_unregistered_transferors,
    '../charts/registered_vs_unregistered_transferors.png',
    table_conversion='selenium',
)

registered_vs_unregistered_transferors

# %% [markdown]
# The unregistered, exempt, or excepted transferors are relatively few. 
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
# These unregistered/exempt/excepted transferors might fall into either of two categories:
#
# - Mergers of **very small charities (which are unregistered/exempt) officially joining bigger ones**. It's likely that these small charities are merging with larger ones to gain economies of scale, access to more resources, or to increase their impact. Alternatively, they might be facing hurdles due to funding constraints, regulatory burdens, or other challenges, and merging with a larger charity is a way to ensure their assets and mission continue.
# - Mergers of charities into **a new structure (CIO or charitable company)**.

# %%
# frequencies of merger events for individual transferors
transferor_freqs = (
    df['transferor_number']
    .value_counts()
    .value_counts()
    .reset_index(name='freqs')
)

transferor_freqs = transferor_freqs.sort_values(by='count')

transferor_freqs.columns = ['count_of_mergers', 'frequency']

transferor_freqs = transferor_freqs.set_index('count_of_mergers', drop=True)

dfi.export(
    transferor_freqs,
    '../charts/transferor_freqs.png',
    table_conversion='selenium',
)

transferor_freqs

# %% [markdown]
# Most registered transferors have only been in the position of the transferring charity once or twice.
#
# This makes sense, since the transferor charity typically ceases to exist as a separate entity after the merger.
#
# The outcomes of a merger, as stated by the [Guidance about the register of merged charities](https://www.gov.uk/government/publications/register-of-merged-charities/guidance-about-the-register-of-merged-charities#why-register):
#
# > - your charity has closed or will close as a result of transferring your assets or
# > - your charity has not closed only because it has permanent endowment which will not be transferred to the charity you are merging with

# %% [markdown]
# The repeat transferors from the following figure might be falling into this second case.

# %%
# most frequent transferors as indicated by charity number
most_frequent_transferors = df.loc[
    ~df['transferor_number'].apply(lambda x: str(x).isalpha()),
    'transferor_number'
].value_counts().to_frame()[:10]

dfi.export(
    most_frequent_transferors,
    '../charts/most_frequent_transferors.png',
    table_conversion='selenium',
)

most_frequent_transferors

# %% [markdown]
# Let's look at charities 1053467 (75 mergers) and 1189059 (5 mergers).

# %%
# mergers of most frequent transferor
consolidation_merger = df.loc[
    df['transferor'].str.contains('1053467'),
    ['transferor', 'transferee']
].head()

consolidation_merger = consolidation_merger.set_index('transferor', drop=True)

dfi.export(
    consolidation_merger,
    '../charts/consolidation_merger.png',
    table_conversion='selenium',
)

consolidation_merger

# %% [markdown]
# *The County Durham and Darlington NHS Foundation Trust Charity* seems to be a case of a large consolidation.
#
# A number of department-specific NHS charities have merged into one entity. The aim could be to consolidate funds/reduce administrative overhead/streamline operations.

# %%
# most frequent transferors by charity name
df['transferor'].value_counts()[:10].to_frame()

# %%
# mergers of second most frequent transferor
reverse_merger = df.loc[
    df['transferor_number'] == '1189059'
].set_index('transferee', drop=True)['transferor'].to_frame()

dfi.export(
    reverse_merger,
    '../charts/reverse_merger.png',
    table_conversion='selenium',
)

reverse_merger

# %% [markdown]
# *The Parochial Church Council of the Ecclesiastical Parish of The A453 Churches of South Nottinghamshire* seems to be an example of a "merged" charity splitting into separate entities.
#
# It is the most frequent transferor among registered charities, having been in that position 5 times.
#
# While this seems to be a reverse merger, it could also be the parent charity distributing some assets to children charities.

# %% [markdown]
# #### Most frequent transferees

# %%
# registered vs unregistered
registered_vs_unregistered_transferees = df['transferee_number'].apply(
    lambda x: 'exempt/unregistered/similar' if str(x).isalpha() else 'registered'
).value_counts().to_frame()

dfi.export(
    registered_vs_unregistered_transferees,
    '../charts/registered_vs_unregistered_transferees.png',
    table_conversion='selenium',
)

registered_vs_unregistered_transferees

# %% [markdown]
# Unregistered charities are not frequently in the position of the transferee, which is what we'd expect, as these charities would probably be larger and more established. 

# %%
# check that frequent transferees are all registered
df['transferee_number'].value_counts()[:10]

# %%
# most frequent transferees
most_frequent_transferees = df['transferee'].value_counts()[:10].to_frame()

dfi.export(
    most_frequent_transferees,
    '../charts/most_frequent_transferees.png',
    table_conversion='selenium',
)

most_frequent_transferees

# %% [markdown]
# Without counting the outlier that merged 1200+ times, some transferees have gone through mergers >40 times.

# %%
# frequencies of merger events for individual transferees
transferee_freqs = (
    df['transferee_number']
    .value_counts()
    .value_counts()
    .reset_index(name='freqs')
)

transferee_freqs = transferee_freqs.sort_values(by='count')

transferee_freqs.columns = ['count_of_mergers', 'frequency']

transferee_freqs = transferee_freqs.set_index('count_of_mergers', drop=True)

dfi.export(
    transferee_freqs,
    '../charts/transferee_freqs.png',
    table_conversion='selenium',
)

transferee_freqs

# %% [markdown]
# Most transferees only go through a merger <5 times.

# %%
# mergers of most frequent transferee
consolidation_merger_kingdom_hall_trust = df.loc[
    df['transferee'].str.contains('Kingdom Hall Trust'),
    ['transferor', 'transferee']
].head()

dfi.export(
    consolidation_merger_kingdom_hall_trust,
    '../charts/consolidation_merger_kingdom_hall_trust.png',
    table_conversion='selenium',
)

consolidation_merger_kingdom_hall_trust = consolidation_merger_kingdom_hall_trust.set_index(
    'transferor', drop=True
)

consolidation_merger_kingdom_hall_trust

# %%
# mergers of second most frequent transferee
consolidation_merger_victim_support = df.loc[
    df['transferee'].str.contains('Victim Support'),
    ['transferor', 'transferee']
].head()

dfi.export(
    consolidation_merger_victim_support,
    '../charts/consolidation_merger_victim_support.png',
    table_conversion='selenium',
)

consolidation_merger_victim_support = consolidation_merger_victim_support.set_index(
    'transferor', drop=True
)

consolidation_merger_victim_support

# %% [markdown]
# Both Kingdom Hall Trust and Victim Support (and other frequent transferees) seem to be consolidation mergers.

# %% [markdown]
# Summary from a [Brave](https://search.brave.com/search?q=The+Kingdom+Hall+Trust+&summary=1) search:
#
# > The Kingdom Hall Trust:
# > - Previously known as the London Company of Kingdom Witnesses, it was established on 28th July 1939 and changed its name to The Kingdom Hall Trust on 20th June 1994.
# > - It is a charity associated with Jehovah’s Witnesses, with the charity number GB-CHC-275946.
# > - The charity has undergone a significant merger in 2022, incorporating 1,279 Jehovah’s Witness congregations into the national charity. This is considered one of the largest charity mergers ever.

# %% [markdown]
# #### Count of mergers per year

# %%
# merger counts by year
merger_counts = df.groupby(
    df['date_registered'].dt.year, as_index=True
)['date_registered'].count()

merger_counts = merger_counts.to_frame('count').reset_index()

merger_counts.T

# %%
# merger counts by year
chart = (
    alt.Chart(merger_counts)
    .mark_bar()
    .encode(
        alt.Y('date_registered:N', title=''),
        alt.X('count:Q', title=''),
        alt.Color('date_registered:N', legend=None, scale=alt.Scale(scheme='dark2')),
    )
    .properties(
        title='Mergers per year, 2008-2024',
        width=600
    )
)

chart.save('../charts/merger_counts.png')

chart

# %% [markdown]
# ### Joining with `annual returns` data (draft)

# %% [markdown]
# #### Load data

# %%
# # load annual return data
# with open(
#     '../data/publicextract.charity_annual_return_history.json',
#     'r',
#     encoding='utf-8-sig',
# ) as file:
#     data = json.load(file)

# df_ar = pd.DataFrame(data)

# df_ar.to_parquet('../data/publicextract.charity_annual_return_history.parquet')

# %%
df_ar = pd.read_parquet('../data/publicextract.charity_annual_return_history.parquet')

# %% [markdown]
# #### Cols

# %%
df_ar.head()

# %%
# select cols
df_ar = df_ar[[
    'registered_charity_number',
    'fin_period_start_date',
    'fin_period_end_date',
    'total_gross_income',
    'total_gross_expenditure',
]]

# %% [markdown]
# #### `dtypes`

# %%
df_ar.dtypes

# %%
# convert date cols to datetime
date_cols = [
    'fin_period_start_date',
    'fin_period_end_date',
]

df_ar[date_cols] = df_ar[date_cols].apply(pd.to_datetime)

df_ar.head()

# %%
df_ar.dtypes

# %% [markdown]
# #### Date cols

# %%
# extract year from date cols
df_ar['fin_start_year'] = df_ar['fin_period_start_date'].dt.year
df_ar['fin_end_year'] = df_ar['fin_period_end_date'].dt.year

df_ar.head()

# %% [markdown]
# #### Merge

# %%
# extract merger years
df['merger_year'] = df['date_transferred'].dt.year
df['merger_year_next'] = df['merger_year'].apply(lambda x: x + 1)

df.head()

# %%
# convert charity number to string
df_ar['registered_charity_number'] = df_ar['registered_charity_number'].apply(str).apply(str.strip)

# %%
# drop cols
df_ar = df_ar.drop(columns=[
    'fin_period_start_date',
    'fin_period_end_date',
    'total_gross_expenditure',
])

# %%
# annual return of transferees
df_merged_transferee = df.drop(
    columns=['date_registered', 'registered-transfer']
).merge(
    df_ar,
    left_on=['transferee_number', 'merger_year'],
    right_on=['registered_charity_number', 'fin_start_year'],
    how='left'
).merge(
    df_ar,
    left_on=['transferee_number', 'merger_year_next'],
    right_on=['registered_charity_number', 'fin_start_year'],
    how='left',
    suffixes=['_current', '_next']    
)

df_merged_transferee.head()

# %%
# annual return of transferors
df_merged_transferor = df.drop(
    columns=['date_registered', 'registered-transfer']
).merge(
    df_ar,
    left_on=['transferor_number', 'merger_year'],
    right_on=['registered_charity_number', 'fin_start_year'],
    how='left'
).merge(
    df_ar,
    left_on=['transferor_number', 'merger_year_next'],
    right_on=['registered_charity_number', 'fin_start_year'],
    how='left',
    suffixes=['_current', '_next']
)

df_merged_transferor.head()

# %% [markdown]
# #### Effect

# %%
# drop null income values
df_merged_transferee = df_merged_transferee.dropna(
    subset=['total_gross_income_current', 'total_gross_income_next'],
    how='all'
)

# %%
# fill empty incomes with 0
df_merged_transferee[
    ['total_gross_income_current', 'total_gross_income_next']
] = df_merged_transferee[
    ['total_gross_income_current', 'total_gross_income_next']
].fillna(0)

# %%
# annual return change from year N to N+1
df_merged_transferee['effect'] = (
    (
        df_merged_transferee['total_gross_income_next']
        - df_merged_transferee['total_gross_income_current']
    )
    / df_merged_transferee['total_gross_income_current']
    * 100
)

# %%
# replace incomes appearing or disappearing by +/-100
df_merged_transferee['effect'] = df_merged_transferee['effect'].replace([-np.inf, np.inf], [-100, 100])

# %%
# drop null income values
df_merged_transferor = df_merged_transferor.dropna(
    subset=['total_gross_income_current', 'total_gross_income_next'],
    how='all'
)

# %%
# fill empty incomes with 0
df_merged_transferor[
    ['total_gross_income_current', 'total_gross_income_next']
] = df_merged_transferor[
    ['total_gross_income_current', 'total_gross_income_next']
].fillna(0)

# %%
# annual return change from year N to N+1
df_merged_transferor['effect'] = (
    (
        df_merged_transferor['total_gross_income_next']
        - df_merged_transferor['total_gross_income_current']
    )
    / df_merged_transferor['total_gross_income_current']
    * 100
)

# %%
# replace incomes appearing or disappearing by +/-100
df_merged_transferor['effect'] = df_merged_transferor['effect'].replace([-np.inf, np.inf], [-100, 100])

# %% [markdown]
# ### Effect of mergers on annual return (draft)

# %%
# mergers with no income before merger and income after
new_charities = df_merged_transferee.loc[
    (
        pd.isna(df_merged_transferee['total_gross_income_current'])
        | (df_merged_transferee['total_gross_income_current'] == 0)
    )
    & (df_merged_transferee['total_gross_income_next'] > 0)
]

# count consolidations as 1 merger
new_charities = new_charities.drop_duplicates(
    subset=['transferee', 'date_transferred']
)

# calculate percentage
new_charities = new_charities.shape[0] / df_merged_transferee.shape[0]

print(f'{new_charities:.0%} of mergers result in the creation of new charities')

# %% [markdown]
# 11% of mergers result in the creation of new charities.
#
# As indicated by the number of unregistered organisations or organisations with an annual return of 0 before merger, and >0 after merger.

# %%
# charities with an income before and after merger
existing_charities = df_merged_transferee.loc[
    ~(
        pd.isna(df_merged_transferee['total_gross_income_current'])
        | (df_merged_transferee['total_gross_income_current'] == 0)
    )
]

# %%
# frequent effect sizes
existing_charities[['transferee', 'effect']].value_counts()[:10]

# %%
# count consolidations as 1 merger
existing_charities = existing_charities[['transferee', 'date_transferred', 'effect']].drop_duplicates()

existing_charities.head()

# %%
# effect of mergers on annual return
chart = (
    alt.Chart(existing_charities['effect'].dropna().apply(round).to_frame())
    .mark_bar()
    .encode(
        alt.X('effect:Q').scale(domain=[-105, 105], clamp=True).title('effect (%)'),
        alt.Y('count():Q').scale(type='log').title('count (log scale)'),
    )
).properties(
    title='Effect of mergers on annual return of transferees'
)

chart.save('../charts/effect_transferees.png')

chart

# %% [markdown]
# After a merger, most transferee organisations either cease to exist or have a +/- 40% change to their annual return.

# %% [markdown]
# According to the data, most mergers (including consolidation mergers) are of the type:
#
# - the transferees do not declare an annual return, indicating either that they cease to exist within the financial period
# - the transferee have a +/- 40% change to their annual returns within the financial period that a merger happened in.
#
# The majority of transferees disappearing after a merger is suspicious and might indicate an issue in the analysis or a subsequent merger into a new structure within the financial period.

# %%
# count consolidations as 1 merger
df_merged_transferor[['transferor', 'date_transferred', 'effect']].value_counts(dropna=False)

# %%
# effect of mergers on annual return
chart = (
    alt.Chart(df_merged_transferor['effect'].dropna().apply(round).to_frame())
    .mark_bar()
    .encode(
        alt.X('effect:Q').title('effect (%)'),
        alt.Y('count():Q').scale(type='log').title('count (log scale)')
    )
).properties(
    title='Effect of mergers on annual return of transferors'
)

chart.save('../charts/effect_transferors.png')

chart

# %% [markdown]
# For most transferors, their annual return either went to 0 or remained the same.
#
# This indicates that most transferors either merge into the transferee and cease to exist as an entity (effect -100%), or their merger is largely inconsequential in terms of annual return. However, some transferors declare their first annual return after the merger (effect +100%), which raises questions about the analysis, but a domain expert might be able to explain this. 

# %% [markdown]
# ## Trustees

# %% [markdown]
# ### Intro

# %% [markdown]
# ### Cleaning `trustees` data

# %% [markdown]
# #### Load data

# %%
# # load trustee data
# with open(
#     '../data/publicextract.charity_trustee.json',
#     'r',
#     encoding='utf-8-sig',
# ) as file:
#     data = json.load(file)

# df = pd.DataFrame(data)

# df.to_parquet('../data/publicextract.charity_trustee.parquet')

# %%
df = pd.read_parquet('../data/publicextract.charity_trustee.parquet')

# %% [markdown]
# #### Cols

# %%
df.head()

# %%
# drop cols
df = df.drop(columns='date_of_extract')

# %% [markdown]
# #### `dtypes`

# %%
df.dtypes

# %%
# convert date cols to datetime
df['trustee_date_of_appointment'] = df['trustee_date_of_appointment'].apply(pd.to_datetime)

# %%
# convert str col to string
df['trustee_name'] = df['trustee_name'].apply(str)

# %%
df['individual_or_organisation'].unique()

# %%
# convert str col to string
df['individual_or_organisation'] = df['individual_or_organisation'].apply(str)

# %%
df.dtypes

# %%
df['trustee_id'].value_counts()[:15]

# %%
repeat_trustees_ids = df['trustee_id'].value_counts()[:15].index

df.loc[
    df['trustee_id'].isin(repeat_trustees_ids),
    ['trustee_id', 'trustee_name', 'individual_or_organisation']
].value_counts(sort=False)
