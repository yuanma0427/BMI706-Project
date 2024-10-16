import altair as alt
import pandas as pd
import streamlit as st
from vega_datasets import data

@st.cache
def load_data():
    df = pd.read_csv('https://raw.githubusercontent.com/yuanma0427/BMI706-Project/main/Cardiovascular_diseases.csv')
    df = df[['Region Name', 'Country Name', 'Year', 'Sex', 'Age Group', 'Number', 'Death rate per 100 000 population']]
    df["Number"] = df.groupby(["Region Name", "Country Name", "Sex", "Age Group"])["Number"].fillna(method="bfill")
    df["Death rate per 100 000 population"] = df.groupby(["Region Name", "Country Name", "Sex", "Age Group", "Number"])["Death rate per 100 000 population"].fillna(method="bfill")
    df.dropna(inplace=True)
    df.reset_index()
    df = df.rename(columns={"Country Name": "Country"})

    # to obtain the country code so that it can be mapped using the "id" in data.world_110m.url
    country_df = pd.read_csv('https://raw.githubusercontent.com/hms-dbmi/bmi706-2022/main/cancer_data/country_codes.csv', dtype = {'conuntry-code': str})
    country_df['country-code'] = country_df['country-code'].astype(str) 
    df = df.merge(country_df[['Country', 'country-code']], how="left", on="Country")
    return df

df = load_data()

st.write("# Visualizations for Cardiovascular Diseases Mortality")

# Sidebar for navigation
page = st.sidebar.radio("Select a Page", ["Plots 1-4", "Plot 5"])

# Page 1: Plots 1-4
if page == "Plots 1-4":

## plot 1
    st.write("## Plot1: World Map of cardiovascular disease mortality")
    # Aggregate data to get sums of total deaths per country, per year
    df2 = df.groupby(["Country", "Year", "country-code"]).agg(
        total_deaths=('Number', 'sum'),
        total_death_rate=('Death rate per 100 000 population', 'sum')
    ).reset_index()


    # Streamlit widget for selecting a single year
    year = st.sidebar.slider(
        'Select Year', 
        int(df2['Year'].min()), 
        int(df2['Year'].max()), 
        2000  # Default to 2000 year
    )

    df_filtered = df2[df2['Year'] == year]

    # Load world map geometry
    source = alt.topo_feature(data.world_110m.url, 'countries')

    # Visualization dimensions and projection
    width = 600
    height  = 300
    project = 'equirectangular'
    source = alt.topo_feature(data.world_110m.url, 'countries')

    # a gray map using as the visualization background
    background = alt.Chart(source
    ).mark_geoshape(
        fill='#aaa',
        stroke='white'
    ).properties(
        width=width,
        height=height
    ).project(project)

    selector = alt.selection_multi(
        fields = ['id'],
        on = 'click',
        )

    chart_base = alt.Chart(source
        ).properties(
            width=width,
            height=height
        ).project(project
        ).add_selection(selector
        ).transform_lookup(
            lookup="id",
            from_=alt.LookupData(df_filtered, "country-code", ['total_deaths', 'Country', 'total_death_rate']),
        )

    # fix the color schema so that it will not change upon user selection
    death_scale = alt.Scale(domain=[df_filtered['total_deaths'].min(), df_filtered['total_deaths'].max()], scheme='oranges')
    death_color = alt.Color(field="total_deaths", type="quantitative", scale=death_scale)

    chart_deaths = chart_base.mark_geoshape().encode(
        color = alt.condition(
            selector,
            death_color,
            alt.value('#ddd')
        ),
        tooltip = [alt.Tooltip('Country:N', title='Country'),
                alt.Tooltip('total_deaths:Q', title='Mortality'),
                alt.Tooltip('total_death_rate:Q', title='Total_Mortality')]
        ).transform_filter(
        selector
        )

    st.altair_chart(background + chart_deaths, use_container_width=True)

## Plot 2
    # Sidebar for region selection and year selection
    df2 = df.groupby(['Region Name', 'Country', 'Year']).agg({
        'Number': 'sum', 
    }).reset_index()

    st.sidebar.header("Controls")
    available_regions = df2['Region Name'].unique().tolist()
    selected_region = st.sidebar.selectbox('Select Region', sorted(available_regions))

    st.write(f"## Plot 2: Bar plot showing mortality comparison for each country in {selected_region} in {year}")

    df_region_filtered = df2[(df2['Region Name'] == selected_region) & (df2['Year'] == year)]

    available_country = df_region_filtered['Country'].unique().tolist()
    selected_country = st.sidebar.selectbox(f'Select Country in {selected_region}', sorted(available_country))
  

    bars = alt.Chart(df_region_filtered).mark_bar().encode(
        x=alt.X('Country:N', sort='-y', title='Country', axis=alt.Axis(labelAngle=-90, labelFontSize=10)),
        y=alt.Y('Number:Q', title='Total Mortality'),
        color=alt.condition(
            alt.datum['Country'] == selected_country,
            alt.value('red'),  # Red for selected bar
            alt.value('#1f77b4')  # Blue for non-selected bars
        ),
        tooltip=[alt.Tooltip('Country:N', title='Country'),
                 alt.Tooltip('Number:Q', title='Total Mortality')]
    ).properties(
        width=1200,
        height=600
    )

    st.altair_chart(bars, use_container_width=True)

## Plot 3

    st.write(f"## Plot 3: Trend Plot of Mortality for {selected_country} in {year}")

    trend_data_country = df[df['Country'] == selected_country]

    if not trend_data_country.empty:
        if 'All' in trend_data_country['Sex'].unique():
            total_mortality = trend_data_country[trend_data_country['Sex'] == 'All'].groupby(['Year']).agg({'Number': 'sum'}).reset_index()
            total_mortality['Mortality Type'] = 'All'
        else:
            total_mortality = pd.DataFrame(columns=['Year', 'Number', 'Mortality Type'])

        female_mortality = trend_data_country[trend_data_country['Sex'] == 'Female'].groupby(['Year']).agg({'Number': 'sum'}).reset_index()
        female_mortality['Mortality Type'] = 'Female'

        male_mortality = trend_data_country[trend_data_country['Sex'] == 'Male'].groupby(['Year']).agg({'Number': 'sum'}).reset_index()
        male_mortality['Mortality Type'] = 'Male'

        if 'Unknown' in trend_data_country['Sex'].unique():
            unknown_mortality = trend_data_country[trend_data_country['Sex'] == 'Unknown'].groupby(['Year']).agg({'Number': 'sum'}).reset_index()
            unknown_mortality['Mortality Type'] = 'Unknown'
        else:
            unknown_mortality = pd.DataFrame(columns=['Year', 'Number', 'Mortality Type'])

        country_total_mortality = df.groupby(['Country', 'Year']).agg({'Number': 'sum'}).reset_index()
        trend_data_all_countries = country_total_mortality.groupby('Year').agg({'Number': 'mean'}).reset_index()
        trend_data_all_countries['Mortality Type'] = 'Average'

        trend_data_combined = pd.concat([total_mortality, female_mortality, male_mortality, unknown_mortality, trend_data_all_countries], ignore_index=True)

        line_chart = alt.Chart(trend_data_combined).mark_line().encode(
            x=alt.X('Year:O', title='Year'),
            y=alt.Y('Number:Q', title='Mortality'),
            color=alt.Color('Mortality Type:N', scale=alt.Scale(
                domain=['All', 'Female', 'Male', 'Unknown', 'Average'],
                range=['blue', 'purple', 'green', 'pink', 'orange']
            )),
            tooltip=['Year:O', 'Mortality Type:N', 'Number:Q']
        ).properties(
            width=800,
            height=400,
        )

        st.altair_chart(line_chart, use_container_width=True)
    else:
        st.write("No data available for the selected country.")

## Plot 4
    st.write(f"## Plot 4: Cardiovascular disease mortality by age group and sex for {selected_country} in {year}")
    if selected_country and year:
        df_age_sex = df[(df['Country'] == selected_country) & (df['Year'] == year) & (df['Age Group'] != '[Unknown]') & (df['Age Group'] != '[All]')]

        if df_age_sex.empty:
            st.write(f"No data available for {selected_country} in {year}.")
        else:
            df_age_sex['Age Group'] = df_age_sex['Age Group'].str.strip("[]")  # remove the bracket so that they can be ordered
            age_order = [
                '0', '1-4', '5-9', '10-14', '15-19', '20-24', '25-29', 
                '30-34', '35-39', '40-44', '45-49', '50-54', 
                '55-59', '60-64', '65-69', '70-74', '75-79', 
                '80-84', '85+'
                ]
            bars = alt.Chart(df_age_sex).mark_bar().encode(
                x=alt.X('Age Group:N', axis=alt.Axis(labelAngle=-90), sort=age_order,),
                xOffset='Sex',   # grouped side by side bar plot
                y=alt.Y('Number:Q', axis=alt.Axis(grid=False), title='Mortality'),
                color=alt.Color('Sex:N', scale=alt.Scale(domain=['All', 'Male', 'Female'])),
                tooltip=[alt.Tooltip('Sex:N', title='Sex'),
                        alt.Tooltip('Age Group:N', title='Age Group'),
                        alt.Tooltip('Number:Q', title='Total Mortality')]
            ).properties(
                width=800,
                height=400
            )
            st.altair_chart(bars, use_container_width=True)
    else:
        st.write("Please select a country and year from the previous plots.")


## Page 2: Plot 5
elif page == "Plot 5":
    st.write("## Comparison of Mortality Among Different Countries")

    year_for_comparison = st.sidebar.slider(
        'Select Year for Comparison',
        int(df['Year'].min()),
        int(df['Year'].max()),
        2000  # Default to 2000
    )

    available_countries = df['Country'].unique().tolist()
    selected_countries = st.sidebar.multiselect('Select Countries to Compare', sorted(available_countries), default=['Finland', 'Canada', 'United States of America'])

    df_countries_filtered = df[df['Country'].isin(selected_countries) & (df['Year'] == year_for_comparison)]

    if df_countries_filtered.empty:
        st.write(f"No data available for the selected countries. Please select different countries.")
    else:
        total_mortality = df_countries_filtered[df_countries_filtered['Sex'] == 'All'].groupby(['Country']).agg({
            'Number': 'sum'
        }).reset_index()
        total_mortality['Gender'] = 'All'

        female_mortality = df_countries_filtered[df_countries_filtered['Sex'] == 'Female'].groupby(['Country']).agg({
            'Number': 'sum'
        }).reset_index()
        female_mortality['Gender'] = 'Female'

        male_mortality = df_countries_filtered[df_countries_filtered['Sex'] == 'Male'].groupby(['Country']).agg({
            'Number': 'sum'
        }).reset_index()
        male_mortality['Gender'] = 'Male'

        combined_data = pd.concat([total_mortality, female_mortality, male_mortality], ignore_index=True)

        bar_chart = alt.Chart(combined_data).mark_bar().encode(
            x=alt.X('Country:N', axis=alt.Axis(labelAngle=0)),
            xOffset='Gender',
            y=alt.Y('Number:Q', axis=alt.Axis(grid=False), title='Mortality'),
            color=alt.Color('Gender:N', scale=alt.Scale(domain=['All', 'Female', 'Male'])),
            tooltip=[alt.Tooltip('Country:N', title='Country'), alt.Tooltip('Gender:N'), alt.Tooltip('Number:Q', title='Mortality')]
        ).properties(
            width=800,
            height=400
        )   

        st.altair_chart(bar_chart, use_container_width=True)